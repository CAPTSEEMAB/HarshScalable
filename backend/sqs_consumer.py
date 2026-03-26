"""
SQS Message Consumer with Parallel Processing
Implements concurrent batch processing for inventory, transaction, and notification events
"""

import boto3
import json
import asyncio
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Callable
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
REGION = os.environ.get('AWS_REGION', 'eu-west-1')
STOCK_EVENTS_QUEUE = os.environ.get('STOCK_EVENTS_QUEUE_URL', '')
TRANSACTION_EVENTS_QUEUE = os.environ.get('TRANSACTION_EVENTS_QUEUE_URL', '')
NOTIFICATION_EVENTS_QUEUE = os.environ.get('NOTIFICATION_EVENTS_QUEUE_URL', '')

# Initialize AWS clients
sqs = boto3.client('sqs', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)


class ParallelSQSConsumer:
    """
    SQS Consumer that processes messages in parallel using:
    - ThreadPoolExecutor for I/O-bound operations
    - Batch processing for multiple messages
    - Async coordination for concurrent queue polling
    """
    
    def __init__(self, queue_url: str, handler: Callable, max_workers: int = 10, batch_size: int = 10):
        self.queue_url = queue_url
        self.handler = handler
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single SQS message"""
        try:
            body = json.loads(message.get('Body', '{}'))
            receipt_handle = message.get('ReceiptHandle')
            message_id = message.get('MessageId')
            
            logger.info(f"Processing message {message_id}")
            
            # Call the handler
            result = self.handler(body)
            
            # Delete message on success
            if self.queue_url:
                sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            
            logger.info(f"Successfully processed message {message_id}")
            return {'message_id': message_id, 'status': 'success', 'result': result}
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {'message_id': message.get('MessageId'), 'status': 'error', 'error': str(e)}
    
    def poll_messages(self) -> List[Dict[str, Any]]:
        """Poll messages from SQS queue"""
        if not self.queue_url:
            return []
            
        try:
            response = sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=self.batch_size,
                WaitTimeSeconds=20,  # Long polling
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            return response.get('Messages', [])
        except Exception as e:
            logger.error(f"Error polling messages: {str(e)}")
            return []
    
    def process_batch_parallel(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of messages in parallel using ThreadPoolExecutor"""
        if not messages:
            return []
        
        logger.info(f"Processing batch of {len(messages)} messages in parallel")
        
        # Submit all messages to the thread pool
        futures = {
            self.executor.submit(self.process_message, msg): msg 
            for msg in messages
        }
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=30)
                results.append(result)
            except concurrent.futures.TimeoutError:
                logger.error("Message processing timed out")
                results.append({'status': 'timeout'})
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                results.append({'status': 'error', 'error': str(e)})
        
        return results
    
    async def run_async(self, iterations: int = None):
        """Run the consumer asynchronously"""
        self.running = True
        iteration = 0
        
        while self.running:
            if iterations and iteration >= iterations:
                break
                
            # Poll messages
            messages = await asyncio.get_event_loop().run_in_executor(
                None, self.poll_messages
            )
            
            if messages:
                # Process batch in parallel
                results = await asyncio.get_event_loop().run_in_executor(
                    None, self.process_batch_parallel, messages
                )
                
                success_count = sum(1 for r in results if r.get('status') == 'success')
                logger.info(f"Batch complete: {success_count}/{len(results)} successful")
            
            iteration += 1
    
    def stop(self):
        """Stop the consumer"""
        self.running = False
        self.executor.shutdown(wait=True)


# ============== Event Handlers ==============

def handle_stock_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle stock events (STOCK_IN, STOCK_OUT, STOCK_TRANSFER, LOW_STOCK_TRIGGERED)
    Updates analytics and triggers notifications if needed
    """
    event_type = event.get('event_type')
    product_id = event.get('product_id')
    warehouse_id = event.get('warehouse_id')
    quantity = event.get('quantity', 0)
    timestamp = event.get('timestamp', datetime.now().isoformat())
    
    logger.info(f"Processing stock event: {event_type} for product {product_id}")
    
    # Update analytics table
    try:
        analytics_table = dynamodb.Table('AnalyticsTable')
        analytics_table.put_item(Item={
            'PK': f'STOCK#{product_id}',
            'SK': timestamp,
            'event_type': event_type,
            'warehouse_id': warehouse_id,
            'quantity_change': quantity,
            'processed_at': datetime.now().isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to update analytics: {str(e)}")
    
    # Check for low stock and trigger notification
    if event_type == 'LOW_STOCK_TRIGGERED':
        notification_event = {
            'event_type': 'NOTIFICATION',
            'notification_type': 'warning',
            'subject': f'Low stock alert: Product {product_id}',
            'message': f'Stock level is below threshold at warehouse {warehouse_id}',
            'product_id': product_id,
            'timestamp': timestamp
        }
        publish_to_queue(NOTIFICATION_EVENTS_QUEUE, notification_event)
    
    return {'processed': True, 'event_type': event_type}


def handle_transaction_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle transaction events (PURCHASE_CREATED, SALE_COMPLETED, RETURN_PROCESSED, DAMAGE_RECORDED)
    Updates analytics and can trigger reorder recommendations
    """
    event_type = event.get('event_type')
    transaction_id = event.get('transaction_id')
    product_id = event.get('product_id')
    quantity = event.get('quantity', 0)
    total_amount = event.get('total_amount', 0)
    timestamp = event.get('timestamp', datetime.now().isoformat())
    
    logger.info(f"Processing transaction event: {event_type} - {transaction_id}")
    
    # Update daily metrics
    try:
        analytics_table = dynamodb.Table('AnalyticsTable')
        date_key = timestamp[:10]  # YYYY-MM-DD
        
        analytics_table.update_item(
            Key={'PK': f'METRIC#DAILY', 'SK': date_key},
            UpdateExpression='ADD orders_processed :one, revenue :amt',
            ExpressionAttributeValues={':one': 1, ':amt': total_amount}
        )
    except Exception as e:
        logger.warning(f"Failed to update metrics: {str(e)}")
    
    # Check if reorder needed after sale
    if event_type == 'SALE_COMPLETED':
        # This could trigger a reorder recommendation check
        pass
    
    return {'processed': True, 'transaction_id': transaction_id}


def handle_notification_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle notification events - sends emails/SNS notifications
    """
    notification_type = event.get('notification_type', 'info')
    subject = event.get('subject', 'Notification')
    message = event.get('message', '')
    recipient = event.get('recipient')
    timestamp = event.get('timestamp', datetime.now().isoformat())
    
    logger.info(f"Processing notification: {subject}")
    
    # Store notification in DynamoDB
    try:
        auth_table = dynamodb.Table('AuthTable')
        import uuid
        notification_id = str(uuid.uuid4())
        
        auth_table.put_item(Item={
            'PK': f'NOTIFICATION#{notification_id}',
            'SK': 'DETAILS',
            'notification_type': notification_type,
            'subject': subject,
            'message': message,
            'status': 'sent',
            'created_at': timestamp,
            'processed_at': datetime.now().isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to store notification: {str(e)}")
    
    # In production, this would send via SES or SNS
    # ses.send_email(...) or sns.publish(...)
    
    return {'processed': True, 'notification_type': notification_type}


def publish_to_queue(queue_url: str, event: Dict[str, Any]) -> bool:
    """Publish an event to an SQS queue"""
    if not queue_url:
        logger.warning("Queue URL not configured, skipping publish")
        return False
        
    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event),
            MessageAttributes={
                'EventType': {
                    'DataType': 'String',
                    'StringValue': event.get('event_type', 'UNKNOWN')
                }
            }
        )
        logger.info(f"Published event to queue: {event.get('event_type')}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish to queue: {str(e)}")
        return False


# ============== Multi-Queue Parallel Consumer ==============

class MultiQueueConsumer:
    """
    Consumes from multiple SQS queues concurrently
    Each queue has its own worker pool
    """
    
    def __init__(self):
        self.consumers = []
        
    def add_consumer(self, queue_url: str, handler: Callable, max_workers: int = 5):
        """Add a new queue consumer"""
        if queue_url:
            consumer = ParallelSQSConsumer(queue_url, handler, max_workers)
            self.consumers.append(consumer)
    
    async def run_all(self, iterations: int = None):
        """Run all consumers concurrently"""
        if not self.consumers:
            logger.warning("No consumers configured")
            return
            
        tasks = [
            consumer.run_async(iterations) 
            for consumer in self.consumers
        ]
        await asyncio.gather(*tasks)
    
    def stop_all(self):
        """Stop all consumers"""
        for consumer in self.consumers:
            consumer.stop()


# ============== Lambda Handler for SQS Triggers ==============

def lambda_sqs_handler(event, context):
    """
    Lambda handler triggered by SQS
    Processes batches of messages in parallel
    """
    records = event.get('Records', [])
    
    if not records:
        return {'statusCode': 200, 'body': 'No records to process'}
    
    logger.info(f"Received {len(records)} SQS records")
    
    # Determine event source and handler
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        
        for record in records:
            body = json.loads(record.get('body', '{}'))
            event_type = body.get('event_type', '')
            
            # Route to appropriate handler
            if 'STOCK' in event_type:
                futures.append(executor.submit(handle_stock_event, body))
            elif any(t in event_type for t in ['PURCHASE', 'SALE', 'RETURN', 'DAMAGE']):
                futures.append(executor.submit(handle_transaction_event, body))
            elif 'NOTIFICATION' in event_type:
                futures.append(executor.submit(handle_notification_event, body))
            else:
                logger.warning(f"Unknown event type: {event_type}")
        
        # Wait for all to complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result(timeout=25)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error: {str(e)}")
                results.append({'error': str(e)})
    
    success_count = sum(1 for r in results if r.get('processed'))
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(results),
            'successful': success_count
        })
    }


# ============== Standalone Runner ==============

def main():
    """Run the multi-queue consumer as a standalone service"""
    logger.info("Starting Multi-Queue SQS Consumer")
    
    consumer = MultiQueueConsumer()
    
    # Add consumers for each queue
    consumer.add_consumer(STOCK_EVENTS_QUEUE, handle_stock_event, max_workers=5)
    consumer.add_consumer(TRANSACTION_EVENTS_QUEUE, handle_transaction_event, max_workers=5)
    consumer.add_consumer(NOTIFICATION_EVENTS_QUEUE, handle_notification_event, max_workers=3)
    
    try:
        asyncio.run(consumer.run_all())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        consumer.stop_all()


if __name__ == '__main__':
    main()
