"""
Batch Processing Worker
Handles bulk operations using parallel processing with ThreadPool and ProcessPool
"""

import boto3
import json
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import logging
import os
import multiprocessing

logger = logging.getLogger(__name__)

REGION = os.environ.get('AWS_REGION', 'eu-west-1')
dynamodb = boto3.resource('dynamodb', region_name=REGION)


class BatchProcessor:
    """
    Generic batch processor with parallel execution
    Supports both thread-based and process-based parallelism
    """
    
    def __init__(self, max_workers: int = None, use_processes: bool = False):
        """
        Initialize batch processor
        
        Args:
            max_workers: Number of parallel workers (default: CPU count)
            use_processes: Use ProcessPoolExecutor for CPU-bound tasks
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
    
    def process_batch(
        self,
        items: List[Any],
        processor_func: Callable,
        chunk_size: int = 100
    ) -> Dict[str, Any]:
        """
        Process items in parallel batches
        
        Args:
            items: List of items to process
            processor_func: Function to apply to each item
            chunk_size: Size of chunks for batching
        
        Returns:
            Dict with results, errors, and statistics
        """
        if not items:
            return {'results': [], 'errors': [], 'total': 0, 'successful': 0}
        
        start_time = datetime.now()
        results = []
        errors = []
        
        # Choose executor type
        ExecutorClass = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        with ExecutorClass(max_workers=self.max_workers) as executor:
            # Submit all items for processing
            future_to_item = {
                executor.submit(processor_func, item): item
                for item in items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result(timeout=60)
                    results.append({'item': item, 'result': result, 'status': 'success'})
                except concurrent.futures.TimeoutError:
                    errors.append({'item': item, 'error': 'Timeout', 'status': 'timeout'})
                except Exception as e:
                    errors.append({'item': item, 'error': str(e), 'status': 'error'})
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'results': results,
            'errors': errors,
            'total': len(items),
            'successful': len(results),
            'failed': len(errors),
            'duration_seconds': duration,
            'items_per_second': len(items) / duration if duration > 0 else 0
        }
    
    async def process_batch_async(
        self,
        items: List[Any],
        processor_func: Callable,
        max_concurrent: int = 50
    ) -> Dict[str, Any]:
        """
        Process items using asyncio for I/O-bound operations
        """
        if not items:
            return {'results': [], 'errors': [], 'total': 0}
        
        start_time = datetime.now()
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        errors = []
        
        async def process_with_semaphore(item):
            async with semaphore:
                try:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, processor_func, item)
                    return {'item': item, 'result': result, 'status': 'success'}
                except Exception as e:
                    return {'item': item, 'error': str(e), 'status': 'error'}
        
        # Process all items concurrently
        tasks = [process_with_semaphore(item) for item in items]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed:
            if isinstance(result, Exception):
                errors.append({'error': str(result), 'status': 'exception'})
            elif result.get('status') == 'success':
                results.append(result)
            else:
                errors.append(result)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'results': results,
            'errors': errors,
            'total': len(items),
            'successful': len(results),
            'failed': len(errors),
            'duration_seconds': duration
        }


# ============== Specialized Batch Processors ==============

class InventoryBatchProcessor:
    """
    Batch processor for inventory operations
    """
    
    def __init__(self):
        self.processor = BatchProcessor(max_workers=10)
        self.inventory_table = dynamodb.Table('InventoryTable')
    
    def bulk_stock_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update stock levels for multiple products in parallel
        
        Args:
            updates: List of {'product_id', 'warehouse_id', 'quantity_change'}
        """
        def update_single(update):
            product_id = update['product_id']
            warehouse_id = update['warehouse_id']
            quantity_change = update['quantity_change']
            
            try:
                response = self.inventory_table.update_item(
                    Key={'PK': f'INV#{product_id}', 'SK': f'WH#{warehouse_id}'},
                    UpdateExpression='ADD quantity :qty SET last_updated = :ts',
                    ExpressionAttributeValues={
                        ':qty': quantity_change,
                        ':ts': datetime.now().isoformat()
                    },
                    ReturnValues='UPDATED_NEW'
                )
                return {'updated': True, 'new_quantity': response.get('Attributes', {}).get('quantity')}
            except Exception as e:
                raise Exception(f"Failed to update {product_id}: {str(e)}")
        
        return self.processor.process_batch(updates, update_single)
    
    def bulk_low_stock_check(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check low stock status for multiple products in parallel
        Returns list of products below threshold
        """
        def check_single(product):
            product_id = product['product_id']
            threshold = product.get('reorder_threshold', 20)
            
            try:
                response = self.inventory_table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={':pk': f'INV#{product_id}'}
                )
                
                items = response.get('Items', [])
                total_quantity = sum(item.get('quantity', 0) for item in items)
                
                return {
                    'product_id': product_id,
                    'total_quantity': total_quantity,
                    'threshold': threshold,
                    'is_low': total_quantity < threshold
                }
            except Exception as e:
                raise Exception(f"Failed to check {product_id}: {str(e)}")
        
        return self.processor.process_batch(products, check_single)


class AnalyticsBatchProcessor:
    """
    Batch processor for analytics computations
    Uses ProcessPoolExecutor for CPU-intensive calculations
    """
    
    def __init__(self):
        self.processor = BatchProcessor(max_workers=4, use_processes=False)
        self.analytics_table = dynamodb.Table('AnalyticsTable')
    
    def compute_product_metrics(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Compute analytics metrics for multiple products in parallel
        """
        def compute_single(product_id):
            # Simulate metric computation
            import random
            return {
                'product_id': product_id,
                'avg_daily_sales': round(random.uniform(5, 50), 2),
                'turnover_rate': round(random.uniform(0.1, 2.0), 3),
                'demand_trend': random.choice(['increasing', 'stable', 'decreasing']),
                'computed_at': datetime.now().isoformat()
            }
        
        return self.processor.process_batch(product_ids, compute_single)
    
    def aggregate_daily_metrics(self, dates: List[str]) -> Dict[str, Any]:
        """
        Aggregate metrics for multiple dates in parallel
        """
        def aggregate_single(date):
            try:
                response = self.analytics_table.query(
                    KeyConditionExpression='PK = :pk AND SK = :date',
                    ExpressionAttributeValues={
                        ':pk': 'METRIC#DAILY',
                        ':date': date
                    }
                )
                
                items = response.get('Items', [])
                if items:
                    return {
                        'date': date,
                        'total_orders': sum(i.get('orders_processed', 0) for i in items),
                        'total_revenue': sum(float(i.get('revenue', 0)) for i in items),
                        'found': True
                    }
                return {'date': date, 'found': False}
            except Exception as e:
                raise Exception(f"Failed to aggregate {date}: {str(e)}")
        
        return self.processor.process_batch(dates, aggregate_single)


class TransactionBatchProcessor:
    """
    Batch processor for transaction operations
    """
    
    def __init__(self):
        self.processor = BatchProcessor(max_workers=10)
        self.transaction_table = dynamodb.Table('TransactionTable')
    
    def bulk_record_transactions(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Record multiple transactions in parallel
        """
        def record_single(txn):
            import uuid
            transaction_id = str(uuid.uuid4())
            
            try:
                self.transaction_table.put_item(Item={
                    'PK': f'TXN#{transaction_id}',
                    'SK': 'DETAILS',
                    'transaction_id': transaction_id,
                    'type': txn.get('type'),
                    'product_id': txn.get('product_id'),
                    'warehouse_id': txn.get('warehouse_id'),
                    'quantity': txn.get('quantity'),
                    'unit_price': str(txn.get('unit_price', 0)),
                    'total_price': str(txn.get('quantity', 0) * txn.get('unit_price', 0)),
                    'status': 'completed',
                    'created_at': datetime.now().isoformat()
                })
                return {'transaction_id': transaction_id, 'recorded': True}
            except Exception as e:
                raise Exception(f"Failed to record transaction: {str(e)}")
        
        return self.processor.process_batch(transactions, record_single)


# ============== Lambda Handler for Batch Operations ==============

def lambda_batch_handler(event, context):
    """
    Lambda handler for batch processing requests
    Supports: bulk_stock_update, bulk_analytics, bulk_transactions
    """
    operation = event.get('operation')
    items = event.get('items', [])
    
    if not operation or not items:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing operation or items'})
        }
    
    logger.info(f"Batch operation: {operation}, items: {len(items)}")
    
    try:
        if operation == 'bulk_stock_update':
            processor = InventoryBatchProcessor()
            result = processor.bulk_stock_update(items)
        
        elif operation == 'low_stock_check':
            processor = InventoryBatchProcessor()
            result = processor.bulk_low_stock_check(items)
        
        elif operation == 'compute_metrics':
            processor = AnalyticsBatchProcessor()
            result = processor.compute_product_metrics(items)
        
        elif operation == 'bulk_transactions':
            processor = TransactionBatchProcessor()
            result = processor.bulk_record_transactions(items)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown operation: {operation}'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'operation': operation,
                'total': result.get('total'),
                'successful': result.get('successful'),
                'failed': result.get('failed'),
                'duration_seconds': result.get('duration_seconds'),
                'items_per_second': result.get('items_per_second')
            })
        }
    
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# ============== Utility Functions ==============

def run_parallel_tasks(tasks: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Run multiple independent tasks in parallel
    
    Args:
        tasks: Dict of {task_name: callable}
    
    Returns:
        Dict of {task_name: result}
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_name = {
            executor.submit(task): name
            for name, task in tasks.items()
        }
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = {'status': 'success', 'result': future.result()}
            except Exception as e:
                results[name] = {'status': 'error', 'error': str(e)}
    
    return results
