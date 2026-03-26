"""
External Public API Integrations
Integrates publicly available web services to satisfy assignment requirements
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# API Keys (should be in environment variables or AWS Secrets Manager)
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')
EXCHANGE_RATE_API_KEY = os.environ.get('EXCHANGE_RATE_API_KEY', '')


class WeatherService:
    """
    Integration with OpenWeatherMap API
    Provides weather data for warehouse locations
    https://openweathermap.org/api
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENWEATHER_API_KEY
    
    def get_weather_by_city(self, city: str) -> Dict[str, Any]:
        """Get current weather for a city"""
        if not self.api_key:
            # Return mock data if no API key
            return self._mock_weather(city)
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/weather",
                params={
                    'q': city,
                    'appid': self.api_key,
                    'units': 'metric'
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'city': data.get('name'),
                'country': data.get('sys', {}).get('country'),
                'temperature': data.get('main', {}).get('temp'),
                'feels_like': data.get('main', {}).get('feels_like'),
                'humidity': data.get('main', {}).get('humidity'),
                'description': data.get('weather', [{}])[0].get('description'),
                'wind_speed': data.get('wind', {}).get('speed'),
                'timestamp': datetime.now().isoformat(),
                'source': 'openweathermap'
            }
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return self._mock_weather(city)
    
    def get_weather_for_warehouses(self, warehouses: list) -> Dict[str, Any]:
        """Get weather for multiple warehouse locations in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.get_weather_by_city, wh.get('location', wh.get('city', 'Unknown'))): wh
                for wh in warehouses
            }
            
            for future in as_completed(futures):
                warehouse = futures[future]
                try:
                    weather = future.result(timeout=15)
                    results[warehouse.get('warehouse_id', 'unknown')] = weather
                except Exception as e:
                    results[warehouse.get('warehouse_id', 'unknown')] = {'error': str(e)}
        
        return results
    
    def _mock_weather(self, city: str) -> Dict[str, Any]:
        """Return mock weather data for demo purposes"""
        import random
        return {
            'city': city,
            'country': 'US',
            'temperature': round(random.uniform(15, 30), 1),
            'feels_like': round(random.uniform(14, 32), 1),
            'humidity': random.randint(40, 80),
            'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'light rain']),
            'wind_speed': round(random.uniform(1, 10), 1),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_data'
        }


class CurrencyExchangeService:
    """
    Integration with Exchange Rate API
    Provides currency conversion for international pricing
    https://exchangerate-api.com/
    """
    
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or EXCHANGE_RATE_API_KEY
    
    def get_exchange_rates(self, base_currency: str = 'USD') -> Dict[str, Any]:
        """Get exchange rates for a base currency"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/{base_currency}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'base': data.get('base'),
                'date': data.get('date'),
                'rates': data.get('rates', {}),
                'timestamp': datetime.now().isoformat(),
                'source': 'exchangerate-api'
            }
        except Exception as e:
            logger.error(f"Exchange rate API error: {str(e)}")
            return self._mock_exchange_rates(base_currency)
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Convert amount from one currency to another"""
        rates = self.get_exchange_rates(from_currency)
        
        if 'error' in rates:
            return rates
        
        rate = rates.get('rates', {}).get(to_currency)
        if rate is None:
            return {'error': f'Currency {to_currency} not found'}
        
        converted = round(amount * rate, 2)
        
        return {
            'original_amount': amount,
            'original_currency': from_currency,
            'converted_amount': converted,
            'target_currency': to_currency,
            'exchange_rate': rate,
            'timestamp': datetime.now().isoformat()
        }
    
    def convert_product_prices(self, products: list, target_currency: str) -> list:
        """Convert prices for multiple products in parallel"""
        rates = self.get_exchange_rates('USD')
        rate = rates.get('rates', {}).get(target_currency, 1.0)
        
        converted_products = []
        for product in products:
            converted = product.copy()
            if 'unit_price' in converted:
                converted['unit_price_original'] = converted['unit_price']
                converted['unit_price'] = round(converted['unit_price'] * rate, 2)
                converted['currency'] = target_currency
            converted_products.append(converted)
        
        return converted_products
    
    def _mock_exchange_rates(self, base_currency: str) -> Dict[str, Any]:
        """Return mock exchange rates for demo purposes"""
        return {
            'base': base_currency,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'rates': {
                'EUR': 0.92,
                'GBP': 0.79,
                'JPY': 149.50,
                'CAD': 1.36,
                'AUD': 1.53,
                'INR': 83.12,
                'CNY': 7.24,
                'CHF': 0.88
            },
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_data'
        }


class RESTCountriesService:
    """
    Integration with REST Countries API
    Provides country information for supplier regions
    https://restcountries.com/
    """
    
    BASE_URL = "https://restcountries.com/v3.1"
    
    def get_country_by_name(self, name: str) -> Dict[str, Any]:
        """Get country information by name"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/name/{name}",
                params={'fields': 'name,capital,region,currencies,languages,population,flags'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                country = data[0]
                currencies = country.get('currencies', {})
                currency_codes = list(currencies.keys()) if currencies else []
                
                return {
                    'name': country.get('name', {}).get('common'),
                    'official_name': country.get('name', {}).get('official'),
                    'capital': country.get('capital', [None])[0],
                    'region': country.get('region'),
                    'currencies': currency_codes,
                    'languages': list(country.get('languages', {}).values()),
                    'population': country.get('population'),
                    'flag': country.get('flags', {}).get('svg'),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'restcountries'
                }
            return {'error': 'Country not found'}
        except Exception as e:
            logger.error(f"REST Countries API error: {str(e)}")
            return {'error': str(e)}
    
    def get_countries_by_region(self, region: str) -> list:
        """Get all countries in a region"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/region/{region}",
                params={'fields': 'name,capital,currencies'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [{
                'name': c.get('name', {}).get('common'),
                'capital': c.get('capital', [None])[0],
                'currencies': list(c.get('currencies', {}).keys())
            } for c in data]
        except Exception as e:
            logger.error(f"REST Countries API error: {str(e)}")
            return []


# ============== Singleton Instances ==============

_weather_service = None
_currency_service = None
_countries_service = None

def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service

def get_currency_service() -> CurrencyExchangeService:
    global _currency_service
    if _currency_service is None:
        _currency_service = CurrencyExchangeService()
    return _currency_service

def get_countries_service() -> RESTCountriesService:
    global _countries_service
    if _countries_service is None:
        _countries_service = RESTCountriesService()
    return _countries_service


# ============== Lambda Handler Integration ==============

def handle_weather_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle weather API requests"""
    path = event.get('path', '')
    
    if '/weather/warehouse' in path:
        # Get weather for all warehouses
        warehouses = [
            {'warehouse_id': 'WH001', 'location': 'New York'},
            {'warehouse_id': 'WH002', 'location': 'Boston'}
        ]
        weather_data = get_weather_service().get_weather_for_warehouses(warehouses)
        return {
            'warehouses': weather_data,
            'parallel_fetched': True,
            'count': len(weather_data)
        }
    else:
        # Get weather for a specific city
        city = event.get('queryStringParameters', {}).get('city', 'New York')
        return get_weather_service().get_weather_by_city(city)


def handle_currency_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle currency API requests"""
    params = event.get('queryStringParameters', {}) or {}
    
    amount = float(params.get('amount', 100))
    from_currency = params.get('from', 'USD')
    to_currency = params.get('to', 'EUR')
    
    if params.get('rates_only'):
        return get_currency_service().get_exchange_rates(from_currency)
    
    return get_currency_service().convert_currency(amount, from_currency, to_currency)


def handle_countries_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle countries API requests"""
    params = event.get('queryStringParameters', {}) or {}
    
    country_name = params.get('name')
    region = params.get('region')
    
    if country_name:
        return get_countries_service().get_country_by_name(country_name)
    elif region:
        countries = get_countries_service().get_countries_by_region(region)
        return {'region': region, 'countries': countries, 'count': len(countries)}
    
    return {'error': 'Please provide name or region parameter'}
