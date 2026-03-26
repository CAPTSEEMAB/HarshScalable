import boto3
import json
import os
import uuid
import hashlib
import random
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

# AWS Configuration
REGION = os.environ.get('AWS_REGION', 'eu-west-1')
STOCK_EVENTS_QUEUE = os.environ.get('STOCK_EVENTS_QUEUE_URL', '')
TRANSACTION_EVENTS_QUEUE = os.environ.get('TRANSACTION_EVENTS_QUEUE_URL', '')
NOTIFICATION_EVENTS_QUEUE = os.environ.get('NOTIFICATION_EVENTS_QUEUE_URL', '')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
sqs = boto3.client('sqs', region_name=REGION)
auth_table = dynamodb.Table('AuthTable')
analytics_table = dynamodb.Table('AnalyticsTable')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ============== Event Publishing (Async Processing) ==============

def publish_event(queue_url: str, event: dict) -> bool:
    """Publish event to SQS for async processing"""
    if not queue_url:
        return False
    try:
        event['timestamp'] = event.get('timestamp', now())
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event),
            MessageAttributes={
                'EventType': {'DataType': 'String', 'StringValue': event.get('event_type', 'UNKNOWN')}
            }
        )
        return True
    except Exception as e:
        print(f"Failed to publish event: {str(e)}")
        return False

def publish_stock_event(event_type: str, product_id: str, warehouse_id: str, quantity: int, **kwargs):
    """Publish stock event for parallel processing"""
    event = {'event_type': event_type, 'product_id': product_id, 'warehouse_id': warehouse_id, 'quantity': quantity, **kwargs}
    publish_event(STOCK_EVENTS_QUEUE, event)

def publish_transaction_event(event_type: str, transaction_id: str, product_id: str, quantity: int, total_amount: float, **kwargs):
    """Publish transaction event for parallel processing"""
    event = {'event_type': event_type, 'transaction_id': transaction_id, 'product_id': product_id, 'quantity': quantity, 'total_amount': total_amount, **kwargs}
    publish_event(TRANSACTION_EVENTS_QUEUE, event)

def lambda_handler(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    if method == 'OPTIONS':
        return cors_response()
    print(f"Request: {method} {path}")
    try:
        if '/auth/health' in path: return ok({'status':'healthy','service':'auth','timestamp':now()})
        elif '/auth/login' in path and method == 'POST': return handle_login(event)
        elif '/auth/register' in path and method == 'POST': return handle_register(event)
        elif '/auth/profile' in path and method == 'GET': return handle_get_profile(event)
        elif '/auth/profile' in path and method == 'PUT': return ok({'message':'Profile updated'})
        elif '/auth/refresh' in path and method == 'POST': return handle_refresh(event)
        elif '/products' in path and method == 'GET': return handle_list_products()
        elif '/products' in path and method == 'POST': return handle_create_product(event)
        elif '/categories' in path and method == 'GET': return handle_list_categories()
        elif '/inventory/stock-in' in path: return handle_stock_in(event)
        elif '/inventory/stock-out' in path: return handle_stock_out(event)
        elif '/inventory/transfer' in path: return handle_stock_transfer(event)
        elif '/inventory/batch' in path and method == 'POST': return handle_batch_inventory(event)
        elif '/inventory/history' in path: return ok({'history':[],'count':0})
        elif '/inventory' in path and method == 'GET': return handle_list_inventory()
        elif '/warehouses' in path and method == 'GET': return handle_list_warehouses()
        elif '/warehouses' in path and method == 'POST': return ok({'warehouse_id':str(uuid.uuid4()),'message':'Warehouse created'})
        elif '/transactions/history' in path: return handle_transaction_history()
        elif '/transactions/purchase' in path: return handle_purchase(event)
        elif '/transactions/sale' in path: return handle_sale(event)
        elif '/transactions/batch' in path and method == 'POST': return handle_batch_transactions(event)
        elif '/transactions' in path and method == 'GET': return handle_transaction_history()
        elif '/analytics/dashboard' in path: return handle_analytics_dashboard()
        elif '/analytics/low-stock' in path: return handle_low_stock()
        elif '/analytics/top-products' in path: return handle_top_products()
        elif '/analytics/slow-products' in path: return handle_slow_products()
        elif '/analytics/warehouse-performance' in path: return handle_warehouse_performance()
        elif '/analytics/reorder-recommendations' in path: return handle_reorder_recommendations()
        elif '/analytics/forecast' in path: return handle_forecast()
        elif '/analytics/metrics' in path: return handle_analytics_metrics()
        elif '/resources/suppliers' in path: return ok({'suppliers':[{'supplier_id':'SUP001','name':'TechParts Inc','categories':['Electronics','Components'],'rating':4.5,'lead_time_days':5,'region':'North America','contact_email':'sales@techparts.com'},{'supplier_id':'SUP002','name':'Global Supply Co','categories':['Accessories','Storage'],'rating':4.2,'lead_time_days':7,'region':'Europe','contact_email':'info@globalsupply.com'},{'supplier_id':'SUP003','name':'FastShip Ltd','categories':['Electronics','Accessories'],'rating':4.8,'lead_time_days':3,'region':'Asia Pacific','contact_email':'orders@fastship.com'}]})
        elif '/resources/recommendations' in path: return ok({'recommendations':[]})
        elif '/resources/restock-guides' in path: return ok({'guides':[]})
        elif '/resources/vendor-search' in path: return ok({'results':[]})
        elif '/notifications' in path and method == 'GET': return handle_list_notifications()
        elif '/notifications' in path and method == 'POST': return handle_create_notification(event)
        # External Public API Integrations
        elif '/external/weather' in path: return handle_weather(event)
        elif '/external/currency' in path: return handle_currency(event)
        elif '/external/countries' in path: return handle_countries(event)
        elif 'health' in path: return ok({'status':'healthy','timestamp':now(),'parallel_processing':'enabled','external_apis':['weather','currency','countries']})
        else: return ok({'message':f'Endpoint {path} received','method':method})
    except Exception as e:
        print(f"Error: {str(e)}")
        return err(str(e), 500)


# ============== External Public API Handlers ==============

def handle_weather(event):
    """Handle weather API requests - integrates with OpenWeatherMap (Public API)"""
    params = event.get('queryStringParameters', {}) or {}
    city = params.get('city', 'New York')
    warehouse_id = params.get('warehouse_id')
    
    # Warehouse locations mapping
    warehouse_locations = {
        'WH001': 'New York',
        'WH002': 'Boston'
    }
    
    if warehouse_id and warehouse_id in warehouse_locations:
        city = warehouse_locations[warehouse_id]
    
    # Try to fetch real weather data (requires API key)
    api_key = os.environ.get('OPENWEATHER_API_KEY', '')
    
    if api_key:
        try:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather",
                params={'q': city, 'appid': api_key, 'units': 'metric'},
                timeout=10
            )
            if response.ok:
                data = response.json()
                return ok({
                    'city': data.get('name'),
                    'country': data.get('sys', {}).get('country'),
                    'temperature': data.get('main', {}).get('temp'),
                    'humidity': data.get('main', {}).get('humidity'),
                    'description': data.get('weather', [{}])[0].get('description'),
                    'wind_speed': data.get('wind', {}).get('speed'),
                    'source': 'openweathermap',
                    'warehouse_id': warehouse_id
                })
        except Exception as e:
            print(f"Weather API error: {str(e)}")
    
    # Fallback to mock data for demo
    return ok({
        'city': city,
        'country': 'US',
        'temperature': round(random.uniform(15, 28), 1),
        'humidity': random.randint(40, 75),
        'description': random.choice(['clear sky', 'partly cloudy', 'overcast']),
        'wind_speed': round(random.uniform(2, 12), 1),
        'source': 'mock_data',
        'warehouse_id': warehouse_id,
        'note': 'Set OPENWEATHER_API_KEY for real data'
    })

def handle_currency(event):
    """Handle currency exchange API requests - integrates with exchangerate-api.com (Public API)"""
    params = event.get('queryStringParameters', {}) or {}
    base = params.get('base', 'USD')
    target = params.get('target', 'EUR')
    amount = float(params.get('amount', 100))
    
    try:
        # Free public API - no key required
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{base}",
            timeout=10
        )
        if response.ok:
            data = response.json()
            rate = data.get('rates', {}).get(target, 1.0)
            converted = round(amount * rate, 2)
            
            return ok({
                'from_currency': base,
                'to_currency': target,
                'original_amount': amount,
                'converted_amount': converted,
                'exchange_rate': rate,
                'rates_date': data.get('date'),
                'source': 'exchangerate-api.com'
            })
    except Exception as e:
        print(f"Currency API error: {str(e)}")
    
    # Fallback mock rates
    mock_rates = {'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5, 'CAD': 1.36, 'INR': 83.1}
    rate = mock_rates.get(target, 1.0)
    
    return ok({
        'from_currency': base,
        'to_currency': target,
        'original_amount': amount,
        'converted_amount': round(amount * rate, 2),
        'exchange_rate': rate,
        'source': 'mock_data'
    })

def handle_countries(event):
    """Handle countries API requests - integrates with restcountries.com (Public API)"""
    params = event.get('queryStringParameters', {}) or {}
    name = params.get('name')
    region = params.get('region')
    
    try:
        if name:
            response = requests.get(
                f"https://restcountries.com/v3.1/name/{name}",
                params={'fields': 'name,capital,region,currencies,population'},
                timeout=10
            )
            if response.ok:
                data = response.json()
                if data:
                    country = data[0]
                    return ok({
                        'name': country.get('name', {}).get('common'),
                        'capital': country.get('capital', [None])[0],
                        'region': country.get('region'),
                        'currencies': list(country.get('currencies', {}).keys()),
                        'population': country.get('population'),
                        'source': 'restcountries.com'
                    })
        elif region:
            response = requests.get(
                f"https://restcountries.com/v3.1/region/{region}",
                params={'fields': 'name,capital'},
                timeout=10
            )
            if response.ok:
                data = response.json()
                countries = [{'name': c.get('name', {}).get('common'), 'capital': c.get('capital', [None])[0]} for c in data[:10]]
                return ok({
                    'region': region,
                    'countries': countries,
                    'count': len(countries),
                    'source': 'restcountries.com'
                })
    except Exception as e:
        print(f"Countries API error: {str(e)}")
    
    return ok({
        'error': 'Please provide name or region parameter',
        'example': '/external/countries?name=Germany or /external/countries?region=europe'
    })


# ============== Transaction Operations with Async Event Publishing ==============

def handle_purchase(event):
    """Handle purchase transaction with async event publishing"""
    body = json.loads(event.get('body', '{}'))
    transaction_id = str(uuid.uuid4())
    product_id = body.get('product_id', 'PROD001')
    quantity = body.get('quantity', 1)
    unit_price = body.get('unit_price', 0)
    total_amount = quantity * unit_price
    
    # Publish event for async processing
    publish_transaction_event('PURCHASE_CREATED', transaction_id, product_id, quantity, total_amount,
                             supplier_id=body.get('supplier_id'), warehouse_id=body.get('warehouse_id'))
    
    return ok({
        'transaction_id': transaction_id,
        'type': 'purchase',
        'status': 'completed',
        'total_amount': total_amount,
        'async_processing': True
    })

def handle_sale(event):
    """Handle sale transaction with async event publishing"""
    body = json.loads(event.get('body', '{}'))
    transaction_id = str(uuid.uuid4())
    product_id = body.get('product_id', 'PROD001')
    quantity = body.get('quantity', 1)
    unit_price = body.get('unit_price', 0)
    total_amount = quantity * unit_price
    
    # Publish event for async processing
    publish_transaction_event('SALE_COMPLETED', transaction_id, product_id, quantity, total_amount,
                             customer_id=body.get('customer_id'), warehouse_id=body.get('warehouse_id'))
    
    return ok({
        'transaction_id': transaction_id,
        'type': 'sale',
        'status': 'completed',
        'total_amount': total_amount,
        'async_processing': True
    })

def handle_batch_transactions(event):
    """
    Handle batch transactions in parallel
    Process multiple transactions concurrently using ThreadPoolExecutor
    """
    body = json.loads(event.get('body', '{}'))
    transactions = body.get('transactions', [])
    
    if not transactions:
        return err('No transactions provided', 400)
    
    results = []
    
    def process_single_transaction(txn):
        txn_type = txn.get('type', 'sale')
        transaction_id = str(uuid.uuid4())
        product_id = txn.get('product_id')
        quantity = txn.get('quantity', 1)
        unit_price = txn.get('unit_price', 0)
        total_amount = quantity * unit_price
        
        event_type = 'SALE_COMPLETED' if txn_type == 'sale' else 'PURCHASE_CREATED'
        publish_transaction_event(event_type, transaction_id, product_id, quantity, total_amount)
        
        return {
            'transaction_id': transaction_id,
            'type': txn_type,
            'total_amount': total_amount,
            'status': 'queued'
        }
    
    # Process all transactions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_single_transaction, txn) for txn in transactions]
        for future in as_completed(futures):
            try:
                results.append(future.result(timeout=10))
            except Exception as e:
                results.append({'error': str(e), 'status': 'failed'})
    
    total_amount = sum(r.get('total_amount', 0) for r in results if 'total_amount' in r)
    
    return ok({
        'message': f'Batch processed: {len(results)} transactions',
        'total_transactions': len(results),
        'total_amount': total_amount,
        'results': results,
        'parallel_processing': True
    })


def handle_login(event):
    body = json.loads(event.get('body','{}'))
    email = body.get('email','')
    password = body.get('password','')
    if not email or not password:
        return err('Email and password required', 400)
    try:
        response = auth_table.scan(FilterExpression='email = :email AND SK = :sk',ExpressionAttributeValues={':email':email,':sk':'PROFILE'})
    except Exception as e:
        return err(f'Database error: {str(e)}', 500)
    items = response.get('Items',[])
    if not items:
        return err('Invalid email or password', 401)
    user = items[0]
    user_id = user.get('user_id', user.get('PK','').replace('USER#',''))
    access_token = hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()
    refresh_token = hashlib.sha256(f"refresh{email}{datetime.now().isoformat()}".encode()).hexdigest()
    return ok({'access_token':access_token,'refresh_token':refresh_token,'token_type':'bearer','user':{'user_id':user_id,'email':user.get('email'),'name':user.get('full_name',user.get('username','User')),'role':user.get('role','student'),'is_active':user.get('is_active',True)}})

def handle_register(event):
    body = json.loads(event.get('body','{}'))
    email = body.get('email','')
    name = body.get('name','')
    password = body.get('password','')
    role = body.get('role','student')
    if not email or not password:
        return err('Email and password required', 400)
    user_id = str(uuid.uuid4())
    now_str = datetime.now().isoformat()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        auth_table.put_item(Item={'PK':f'USER#{user_id}','SK':'PROFILE','GSI1PK':f'EMAIL#{email}','GSI1SK':'USER','user_id':user_id,'email':email,'full_name':name,'password_hash':password_hash,'role':role,'is_active':True,'preferences':{},'created_at':now_str,'updated_at':now_str})
    except Exception as e:
        return err(f'Registration failed: {str(e)}', 500)
    access_token = hashlib.sha256(f"{email}{now_str}".encode()).hexdigest()
    refresh_token = hashlib.sha256(f"refresh{email}{now_str}".encode()).hexdigest()
    return ok({'access_token':access_token,'refresh_token':refresh_token,'token_type':'bearer','user':{'user_id':user_id,'email':email,'name':name,'role':role,'is_active':True}})

def handle_get_profile(event):
    return ok({'user_id':'demo-user','email':'test@example.com','name':'Test User','role':'admin','is_active':True,'preferences':{}})

def handle_refresh(event):
    access_token = hashlib.sha256(f"refreshed{datetime.now().isoformat()}".encode()).hexdigest()
    refresh_token = hashlib.sha256(f"newrefresh{datetime.now().isoformat()}".encode()).hexdigest()
    return ok({'access_token':access_token,'refresh_token':refresh_token,'token_type':'bearer'})

def handle_list_products():
    return ok({'products':[
        {'product_id':'PROD001','name':'Laptop Pro 15','sku':'LP-15-001','unit_price':1299.99,'category':'Electronics','category_id':'CAT001','stock':125,'reorder_threshold':20,'status':'active','created_at':'2026-03-01T00:00:00'},
        {'product_id':'PROD002','name':'Wireless Mouse','sku':'WM-ERG-002','unit_price':29.99,'category':'Accessories','category_id':'CAT002','stock':450,'reorder_threshold':50,'status':'active','created_at':'2026-03-01T00:00:00'},
        {'product_id':'PROD003','name':'USB-C Cable','sku':'USB-C-003','unit_price':14.99,'category':'Accessories','category_id':'CAT002','stock':890,'reorder_threshold':100,'status':'active','created_at':'2026-03-01T00:00:00'},
        {'product_id':'PROD004','name':'Monitor 27"','sku':'MON-27-004','unit_price':449.99,'category':'Electronics','category_id':'CAT001','stock':75,'reorder_threshold':15,'status':'active','created_at':'2026-03-05T00:00:00'},
        {'product_id':'PROD005','name':'Keyboard Mechanical','sku':'KB-MEC-005','unit_price':89.99,'category':'Accessories','category_id':'CAT002','stock':200,'reorder_threshold':30,'status':'active','created_at':'2026-03-08T00:00:00'},
    ],'count':5})

def handle_create_product(event):
    body = json.loads(event.get('body','{}'))
    return ok({'product_id':str(uuid.uuid4())[:8],'message':'Product created successfully',**body})

def handle_list_categories():
    return ok({'categories':[
        {'category_id':'CAT001','name':'Electronics','description':'Electronic devices and gadgets','product_count':2},
        {'category_id':'CAT002','name':'Accessories','description':'Computer accessories and peripherals','product_count':3},
        {'category_id':'CAT003','name':'Storage','description':'Storage devices and media','product_count':0},
    ]})


# ============== Stock Operations with Async Event Publishing ==============

def handle_stock_in(event):
    """Handle stock-in with async event publishing"""
    body = json.loads(event.get('body', '{}'))
    transaction_id = str(uuid.uuid4())
    product_id = body.get('product_id', 'PROD001')
    warehouse_id = body.get('warehouse_id', 'WH001')
    quantity = body.get('quantity', 0)
    
    # Publish event for async processing by SQS consumer
    publish_stock_event('STOCK_IN', product_id, warehouse_id, quantity, transaction_id=transaction_id)
    
    return ok({
        'message': 'Stock added',
        'transaction_id': transaction_id,
        'async_processing': True,
        'event_queued': 'STOCK_IN'
    })

def handle_stock_out(event):
    """Handle stock-out with async event publishing and low stock check"""
    body = json.loads(event.get('body', '{}'))
    transaction_id = str(uuid.uuid4())
    product_id = body.get('product_id', 'PROD001')
    warehouse_id = body.get('warehouse_id', 'WH001')
    quantity = body.get('quantity', 0)
    
    # Publish event for async processing
    publish_stock_event('STOCK_OUT', product_id, warehouse_id, quantity, transaction_id=transaction_id)
    
    # Simulate low stock check - in production this would query actual inventory
    current_stock = 125 - quantity  # Simulated
    reorder_threshold = 20
    if current_stock < reorder_threshold:
        publish_stock_event('LOW_STOCK_TRIGGERED', product_id, warehouse_id, current_stock, 
                           threshold=reorder_threshold)
    
    return ok({
        'message': 'Stock removed',
        'transaction_id': transaction_id,
        'async_processing': True,
        'event_queued': 'STOCK_OUT'
    })

def handle_stock_transfer(event):
    """Handle stock transfer between warehouses"""
    body = json.loads(event.get('body', '{}'))
    transaction_id = str(uuid.uuid4())
    product_id = body.get('product_id', 'PROD001')
    from_warehouse = body.get('from_warehouse_id', 'WH001')
    to_warehouse = body.get('to_warehouse_id', 'WH002')
    quantity = body.get('quantity', 0)
    
    # Publish event for async processing
    publish_stock_event('STOCK_TRANSFER', product_id, from_warehouse, quantity,
                       transaction_id=transaction_id, to_warehouse_id=to_warehouse)
    
    return ok({
        'message': 'Stock transferred',
        'transaction_id': transaction_id,
        'from_warehouse': from_warehouse,
        'to_warehouse': to_warehouse,
        'async_processing': True,
        'event_queued': 'STOCK_TRANSFER'
    })

def handle_batch_inventory(event):
    """
    Handle batch inventory operations in parallel
    Processes multiple stock updates concurrently using ThreadPoolExecutor
    """
    body = json.loads(event.get('body', '{}'))
    operations = body.get('operations', [])
    
    if not operations:
        return err('No operations provided', 400)
    
    results = []
    errors = []
    
    def process_single_operation(op):
        op_type = op.get('type', 'stock_in')
        product_id = op.get('product_id')
        warehouse_id = op.get('warehouse_id')
        quantity = op.get('quantity', 0)
        transaction_id = str(uuid.uuid4())
        
        event_type = {
            'stock_in': 'STOCK_IN',
            'stock_out': 'STOCK_OUT',
            'transfer': 'STOCK_TRANSFER'
        }.get(op_type, 'STOCK_IN')
        
        publish_stock_event(event_type, product_id, warehouse_id, quantity, transaction_id=transaction_id)
        
        return {
            'transaction_id': transaction_id,
            'type': op_type,
            'product_id': product_id,
            'status': 'queued'
        }
    
    # Process all operations in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_single_operation, op): op for op in operations}
        
        for future in as_completed(futures):
            try:
                result = future.result(timeout=10)
                results.append(result)
            except Exception as e:
                errors.append({'operation': futures[future], 'error': str(e)})
    
    return ok({
        'message': f'Batch processed: {len(results)} operations queued',
        'processed': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors,
        'parallel_processing': True
    })


def handle_list_inventory():
    return ok({'inventory':[
        {'inventory_id':'INV001','product_id':'PROD001','product_name':'Laptop Pro 15','warehouse_id':'WH001','warehouse_name':'Main Warehouse','quantity':125,'reorder_level':20,'location':'Shelf A-15','last_updated':'2026-03-24T10:00:00'},
        {'inventory_id':'INV002','product_id':'PROD002','product_name':'Wireless Mouse','warehouse_id':'WH001','warehouse_name':'Main Warehouse','quantity':450,'reorder_level':50,'location':'Shelf B-8','last_updated':'2026-03-24T10:00:00'},
        {'inventory_id':'INV003','product_id':'PROD003','product_name':'USB-C Cable','warehouse_id':'WH001','warehouse_name':'Main Warehouse','quantity':890,'reorder_level':100,'location':'Shelf C-3','last_updated':'2026-03-24T10:00:00'},
        {'inventory_id':'INV004','product_id':'PROD004','product_name':'Monitor 27"','warehouse_id':'WH002','warehouse_name':'East Distribution','quantity':75,'reorder_level':15,'location':'Bay D-2','last_updated':'2026-03-24T10:00:00'},
        {'inventory_id':'INV005','product_id':'PROD005','product_name':'Keyboard Mechanical','warehouse_id':'WH002','warehouse_name':'East Distribution','quantity':200,'reorder_level':30,'location':'Bay E-1','last_updated':'2026-03-24T10:00:00'},
    ]})

def handle_list_warehouses():
    return ok({'warehouses':[
        {'warehouse_id':'WH001','name':'Main Warehouse','location':'New York, NY','capacity':10000,'current_stock':1465,'utilization':14.65},
        {'warehouse_id':'WH002','name':'East Distribution','location':'Boston, MA','capacity':5000,'current_stock':275,'utilization':5.5},
    ]})

def handle_transaction_history():
    return ok({'transactions':[
        {'transaction_id':'TXN001','type':'PURCHASE','product_id':'PROD001','product_name':'Laptop Pro 15','warehouse_id':'WH001','quantity':50,'unit_price':1100.00,'total_price':55000.00,'status':'completed','timestamp':'2026-03-20T14:30:00','user':'admin'},
        {'transaction_id':'TXN002','type':'SALE','product_id':'PROD002','product_name':'Wireless Mouse','warehouse_id':'WH001','quantity':100,'unit_price':29.99,'total_price':2999.00,'status':'completed','timestamp':'2026-03-21T09:15:00','user':'manager'},
        {'transaction_id':'TXN003','type':'PURCHASE','product_id':'PROD003','product_name':'USB-C Cable','warehouse_id':'WH001','quantity':200,'unit_price':8.50,'total_price':1700.00,'status':'completed','timestamp':'2026-03-22T11:00:00','user':'admin'},
        {'transaction_id':'TXN004','type':'SALE','product_id':'PROD004','product_name':'Monitor 27"','warehouse_id':'WH002','quantity':25,'unit_price':449.99,'total_price':11249.75,'status':'completed','timestamp':'2026-03-23T16:45:00','user':'staff'},
        {'transaction_id':'TXN005','type':'RETURN','product_id':'PROD001','product_name':'Laptop Pro 15','warehouse_id':'WH001','quantity':2,'unit_price':1299.99,'total_price':2599.98,'status':'completed','timestamp':'2026-03-24T08:30:00','user':'manager'},
    ],'count':5})

def handle_analytics_dashboard():
    return ok({'total_products':5,'total_warehouses':2,'total_stock_units':1740,'total_transactions':5,'total_sales_value':14248.75,'total_purchase_value':56700.00,'low_stock_alerts':1,'recent_transactions':[{'id':'TXN005','type':'return','product':'Laptop Pro 15','amount':2599.98,'date':'2026-03-24'},{'id':'TXN004','type':'sale','product':'Monitor 27"','amount':11249.75,'date':'2026-03-23'},{'id':'TXN003','type':'purchase','product':'USB-C Cable','amount':1700.00,'date':'2026-03-22'}],'chart_data':{'daily_revenue':[{'date':'2026-03-18','revenue':12450.00},{'date':'2026-03-19','revenue':14200.00},{'date':'2026-03-20','revenue':9800.00},{'date':'2026-03-21','revenue':16300.00},{'date':'2026-03-22','revenue':11700.00},{'date':'2026-03-23','revenue':13200.75},{'date':'2026-03-24','revenue':15230.50}],'inventory_by_category':[{'category':'Electronics','count':200},{'category':'Accessories','count':1540}]}})

def handle_analytics_metrics():
    try:
        response = analytics_table.scan(FilterExpression='begins_with(PK, :pk)',ExpressionAttributeValues={':pk':'METRIC#'})
        items = []
        for item in response.get('Items',[]):
            items.append({'metric_type':item.get('PK','').split('#')[1] if '#' in item.get('PK','') else 'unknown','date':item.get('SK','unknown'),'inventory_count':int(item.get('inventory_count',0)),'orders_processed':int(item.get('orders_processed',0)),'revenue':float(item.get('revenue',0))})
        return ok({'metrics':items,'count':len(items)})
    except Exception as e:
        return err(f'Failed to fetch metrics: {str(e)}', 500)

def handle_low_stock():
    return ok({'low_stock_items':[{'product_id':'PROD004','product_name':'Monitor 27"','warehouse_id':'WH002','current_quantity':75,'reorder_threshold':100,'deficit':25}]})

def handle_top_products():
    return ok({'top_products':[{'product_id':'PROD002','product_name':'Wireless Mouse','total_sold':320,'revenue':9596.80},{'product_id':'PROD001','product_name':'Laptop Pro 15','total_sold':85,'revenue':110499.15},{'product_id':'PROD003','product_name':'USB-C Cable','total_sold':540,'revenue':8094.60},{'product_id':'PROD005','product_name':'Keyboard Mechanical','total_sold':150,'revenue':13498.50},{'product_id':'PROD004','product_name':'Monitor 27"','total_sold':45,'revenue':20249.55}]})

def handle_slow_products():
    return ok([{'product_id':'PROD004','name':'Monitor 27"','units_sold':5,'days_in_stock':45,'turnover_rate':0.11}])

def handle_warehouse_performance():
    return ok([{'warehouse_id':'WH001','name':'Main Warehouse','throughput':450,'avg_processing_time':2.1,'accuracy_rate':99.2,'utilization':14.65},{'warehouse_id':'WH002','name':'East Distribution','throughput':180,'avg_processing_time':1.8,'accuracy_rate':99.5,'utilization':5.5}])

def handle_reorder_recommendations():
    return ok({'recommendations':[{'product_id':'PROD004','product_name':'Monitor 27"','warehouse_id':'WH002','current_quantity':75,'recommended_order_qty':50,'urgency':'moderate','days_until_stockout':12}]})

def handle_forecast():
    today = datetime.now()
    daily = [{'date':(today+timedelta(days=i)).strftime('%Y-%m-%d'),'predicted_demand':max(5,15-i%7)} for i in range(1,31)]
    return ok({'product_id':'PROD001','product_name':'Laptop Pro 15','forecast':{'daily_forecast':daily,'confidence':'high','method':'moving_average','total_predicted_demand':sum(d['predicted_demand'] for d in daily)}})

def handle_list_notifications():
    """List notifications for current user"""
    notifications = [
        {'notification_id':str(uuid.uuid4()),'type':'warning','subject':'Low stock alert: Laptop Pro 15','message':'Stock level is below threshold (20 units)','status':'unread','timestamp':'2026-03-25T12:00:00','product_id':'PROD001','action_url':'/products'},
        {'notification_id':str(uuid.uuid4()),'type':'info','subject':'Reorder recommendation','message':'Monitor 27" needs reorder: 50 units recommended','status':'unread','timestamp':'2026-03-25T11:30:00','product_id':'PROD004','action_url':'/inventory'},
        {'notification_id':str(uuid.uuid4()),'type':'success','subject':'Purchase order received','message':'PO-00001 from TechParts Inc completed','status':'read','timestamp':'2026-03-25T10:15:00','order_id':'PO-00001','action_url':'/transactions'},
        {'notification_id':str(uuid.uuid4()),'type':'warning','subject':'Warehouse capacity warning','message':'East Distribution warehouse is 85% full','status':'read','timestamp':'2026-03-25T09:00:00','warehouse_id':'WH002','action_url':'/warehouses'},
        {'notification_id':str(uuid.uuid4()),'type':'info','subject':'Daily analytics ready','message':'Your daily inventory analytics report is available','status':'read','timestamp':'2026-03-25T06:00:00','action_url':'/analytics'},
    ]
    return ok({'notifications':notifications,'count':len(notifications)})

def handle_create_notification(event):
    """Create a new notification"""
    body = json.loads(event.get('body','{}'))
    notification = {
        'notification_id':str(uuid.uuid4()),
        'type':body.get('type','info'),
        'subject':body.get('subject','New notification'),
        'message':body.get('message',''),
        'status':'unread',
        'timestamp':now(),
        'action_url':body.get('action_url','')
    }
    return ok({'notification':notification,'message':'Notification created'})

def now():
    return datetime.now().isoformat()

def ok(data):
    return {'statusCode':200,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, PUT, DELETE, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token'},'body':json.dumps(data, cls=DecimalEncoder)}

def err(message, code=400):
    return {'statusCode':code,'headers':{'Content-Type':'application/json','Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, PUT, DELETE, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization'},'body':json.dumps({'detail':message})}

def cors_response():
    return {'statusCode':200,'headers':{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, PUT, DELETE, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token','Access-Control-Max-Age':'86400'},'body':''}
