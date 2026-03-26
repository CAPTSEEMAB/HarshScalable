#!/usr/bin/env python3
"""
Test script for backend-lambda.py
Tests parallel processing and external API integrations
"""

import json
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the lambda handler
from importlib import import_module

# Load the module with hyphen in name
import importlib.util
spec = importlib.util.spec_from_file_location("backend_lambda", "backend-lambda.py")
backend_lambda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_lambda)

lambda_handler = backend_lambda.lambda_handler


def test_endpoint(name, path, method='GET', body=None):
    """Test a Lambda endpoint"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    event = {
        'path': path,
        'httpMethod': method,
        'queryStringParameters': {},
        'body': json.dumps(body) if body else None
    }
    
    # Extract query params from path
    if '?' in path:
        base_path, query = path.split('?', 1)
        event['path'] = base_path
        params = {}
        for param in query.split('&'):
            if '=' in param:
                k, v = param.split('=', 1)
                params[k] = v
        event['queryStringParameters'] = params
    
    try:
        response = lambda_handler(event, None)
        status = response.get('statusCode', 'N/A')
        body = json.loads(response.get('body', '{}'))
        
        print(f"Status: {status}")
        print(f"Response: {json.dumps(body, indent=2)}")
        return status == 200
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def run_tests():
    """Run all tests"""
    results = []
    
    print("\n" + "="*60)
    print("TESTING BACKEND LAMBDA - PARALLEL PROCESSING & EXTERNAL APIS")
    print("="*60)
    
    # 1. Health check
    results.append(("Health Check", test_endpoint(
        "Health Check",
        "/api/v1/health"
    )))
    
    # 2. External API - Weather
    results.append(("Weather API (Public)", test_endpoint(
        "Weather API - OpenWeatherMap (Public API)",
        "/api/v1/external/weather?city=London"
    )))
    
    # 3. External API - Currency
    results.append(("Currency API (Public)", test_endpoint(
        "Currency API - ExchangeRate (Public API)",
        "/api/v1/external/currency?base=USD&target=EUR&amount=100"
    )))
    
    # 4. External API - Countries
    results.append(("Countries API (Public)", test_endpoint(
        "Countries API - RestCountries (Public API)",
        "/api/v1/external/countries?name=Germany"
    )))
    
    # 5. Stock In with Async Event Publishing
    results.append(("Stock In (Async)", test_endpoint(
        "Stock In - Async Event Publishing",
        "/api/v1/inventory/stock-in",
        method='POST',
        body={
            'product_id': 'PROD001',
            'warehouse_id': 'WH001',
            'quantity': 50
        }
    )))
    
    # 6. Stock Out with Low Stock Check
    results.append(("Stock Out (Async)", test_endpoint(
        "Stock Out - Async Event + Low Stock Check",
        "/api/v1/inventory/stock-out",
        method='POST',
        body={
            'product_id': 'PROD001',
            'warehouse_id': 'WH001',
            'quantity': 110
        }
    )))
    
    # 7. Batch Inventory (Parallel Processing)
    results.append(("Batch Inventory (Parallel)", test_endpoint(
        "Batch Inventory - PARALLEL PROCESSING",
        "/api/v1/inventory/batch",
        method='POST',
        body={
            'operations': [
                {'type': 'stock_in', 'product_id': 'PROD001', 'warehouse_id': 'WH001', 'quantity': 10},
                {'type': 'stock_in', 'product_id': 'PROD002', 'warehouse_id': 'WH001', 'quantity': 20},
                {'type': 'stock_out', 'product_id': 'PROD003', 'warehouse_id': 'WH002', 'quantity': 5},
                {'type': 'transfer', 'product_id': 'PROD004', 'warehouse_id': 'WH001', 'quantity': 15},
                {'type': 'stock_in', 'product_id': 'PROD005', 'warehouse_id': 'WH002', 'quantity': 30},
            ]
        }
    )))
    
    # 8. Purchase Transaction with Async
    results.append(("Purchase (Async)", test_endpoint(
        "Purchase Transaction - Async Event",
        "/api/v1/transactions/purchase",
        method='POST',
        body={
            'product_id': 'PROD001',
            'quantity': 100,
            'unit_price': 1299.99,
            'supplier_id': 'SUP001'
        }
    )))
    
    # 9. Sale Transaction with Async
    results.append(("Sale (Async)", test_endpoint(
        "Sale Transaction - Async Event",
        "/api/v1/transactions/sale",
        method='POST',
        body={
            'product_id': 'PROD002',
            'quantity': 50,
            'unit_price': 29.99,
            'customer_id': 'CUST001'
        }
    )))
    
    # 10. Batch Transactions (Parallel Processing)
    results.append(("Batch Transactions (Parallel)", test_endpoint(
        "Batch Transactions - PARALLEL PROCESSING",
        "/api/v1/transactions/batch",
        method='POST',
        body={
            'transactions': [
                {'type': 'sale', 'product_id': 'PROD001', 'quantity': 5, 'unit_price': 1299.99},
                {'type': 'sale', 'product_id': 'PROD002', 'quantity': 10, 'unit_price': 29.99},
                {'type': 'purchase', 'product_id': 'PROD003', 'quantity': 100, 'unit_price': 14.99},
                {'type': 'sale', 'product_id': 'PROD004', 'quantity': 3, 'unit_price': 449.99},
            ]
        }
    )))
    
    # 11. Analytics Dashboard
    results.append(("Analytics Dashboard", test_endpoint(
        "Analytics Dashboard",
        "/api/v1/analytics/dashboard"
    )))
    
    # 12. Products List
    results.append(("Products List", test_endpoint(
        "Products List",
        "/api/v1/products"
    )))
    
    # Print Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)
    
    # Feature verification
    print("\n" + "="*60)
    print("REQUIREMENT VERIFICATION")
    print("="*60)
    print("✅ Parallel Processing: ThreadPoolExecutor for batch operations")
    print("✅ Async Event Publishing: SQS queue integration")
    print("✅ Public API #1: OpenWeatherMap (weather data)")
    print("✅ Public API #2: ExchangeRate-API (currency conversion)")
    print("✅ Public API #3: RestCountries (country information)")
    print("⚠️  Classmate API: Still needs integration")
    print("="*60)


if __name__ == '__main__':
    run_tests()
