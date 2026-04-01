import boto3
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

REGION = os.environ.get('AWS_REGION', 'eu-west-1')
STOCK_EVENTS_QUEUE = os.environ.get('STOCK_EVENTS_QUEUE_URL', '')
TRANSACTION_EVENTS_QUEUE = os.environ.get('TRANSACTION_EVENTS_QUEUE_URL', '')
NOTIFICATION_EVENTS_QUEUE = os.environ.get('NOTIFICATION_EVENTS_QUEUE_URL', '')

sqs = boto3.client('sqs', region_name=REGION)

class EventPublisher:
    def __init__(self):
        self.queues = {
            'stock': STOCK_EVENTS_QUEUE,
            'transaction': TRANSACTION_EVENTS_QUEUE,
            'notification': NOTIFICATION_EVENTS_QUEUE
        }
    
    def publish(self, queue_name: str, event: Dict[str, Any]) -> bool:
        queue_url = self.queues.get(queue_name)
        if not queue_url:
            logger.warning(f"Queue {queue_name} not configured")
            return False
        
        event['timestamp'] = event.get('timestamp', datetime.now().isoformat())
        event['published_at'] = datetime.now().isoformat()
        
        try:
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(event),
                MessageAttributes={
                    'EventType': {
                        'DataType': 'String',
                        'StringValue': event.get('event_type', 'UNKNOWN')
                    },
                    'Source': {
                        'DataType': 'String',
                        'StringValue': 'inventory-service'
                    }
                }
            )
            logger.info(f"Published to {queue_name}: {response.get('MessageId')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {queue_name}: {str(e)}")
            return False
    
    def publish_batch(self, queue_name: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        queue_url = self.queues.get(queue_name)
        if not queue_url:
            return {'successful': 0, 'failed': len(events)}
        
        successful = 0
        failed = 0

        for i in range(0, len(events), 10):
            batch = events[i:i+10]
            entries = []
            
            for idx, event in enumerate(batch):
                event['timestamp'] = event.get('timestamp', datetime.now().isoformat())
                event['published_at'] = datetime.now().isoformat()
                
                entries.append({
                    'Id': str(idx),
                    'MessageBody': json.dumps(event),
                    'MessageAttributes': {
                        'EventType': {
                            'DataType': 'String',
                            'StringValue': event.get('event_type', 'UNKNOWN')
                        }
                    }
                })
            
            try:
                response = sqs.send_message_batch(
                    QueueUrl=queue_url,
                    Entries=entries
                )
                successful += len(response.get('Successful', []))
                failed += len(response.get('Failed', []))
            except Exception as e:
                logger.error(f"Batch publish failed: {str(e)}")
                failed += len(batch)
        
        return {'successful': successful, 'failed': failed}
    
    def publish_parallel(self, events_by_queue: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.publish_batch, queue_name, events): queue_name
                for queue_name, events in events_by_queue.items()
                if events
            }
            
            for future in as_completed(futures):
                queue_name = futures[future]
                try:
                    result = future.result(timeout=30)
                    results[queue_name] = result
                except Exception as e:
                    logger.error(f"Parallel publish to {queue_name} failed: {str(e)}")
                    results[queue_name] = {'successful': 0, 'failed': -1, 'error': str(e)}
        
        return results

_publisher = None

def get_publisher() -> EventPublisher:
    
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher

def publish_stock_event(
    event_type: str,
    product_id: str,
    warehouse_id: str,
    quantity: int,
    **kwargs
) -> bool:
    
    event = {
        'event_type': event_type,
        'product_id': product_id,
        'warehouse_id': warehouse_id,
        'quantity': quantity,
        **kwargs
    }
    return get_publisher().publish('stock', event)

def publish_transaction_event(
    event_type: str,
    transaction_id: str,
    product_id: str,
    quantity: int,
    total_amount: float,
    **kwargs
) -> bool:
    
    event = {
        'event_type': event_type,
        'transaction_id': transaction_id,
        'product_id': product_id,
        'quantity': quantity,
        'total_amount': total_amount,
        **kwargs
    }
    return get_publisher().publish('transaction', event)

def publish_notification_event(
    notification_type: str,
    subject: str,
    message: str,
    recipient: str = None,
    **kwargs
) -> bool:
    
    event = {
        'event_type': 'NOTIFICATION',
        'notification_type': notification_type,
        'subject': subject,
        'message': message,
        'recipient': recipient,
        **kwargs
    }
    return get_publisher().publish('notification', event)

def publish_low_stock_alert(
    product_id: str,
    product_name: str,
    warehouse_id: str,
    current_quantity: int,
    threshold: int
) -> bool:
    
    publisher = get_publisher()

    stock_event = {
        'event_type': 'LOW_STOCK_TRIGGERED',
        'product_id': product_id,
        'product_name': product_name,
        'warehouse_id': warehouse_id,
        'current_quantity': current_quantity,
        'threshold': threshold
    }

    notification_event = {
        'event_type': 'NOTIFICATION',
        'notification_type': 'warning',
        'subject': f'Low stock alert: {product_name}',
        'message': f'Stock level ({current_quantity}) is below threshold ({threshold}) at warehouse {warehouse_id}',
        'product_id': product_id,
        'action_url': f'/inventory?product={product_id}'
    }

    results = publisher.publish_parallel({
        'stock': [stock_event],
        'notification': [notification_event]
    })
    
    return all(r.get('successful', 0) > 0 for r in results.values())
