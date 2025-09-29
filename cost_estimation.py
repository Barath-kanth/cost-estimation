# Add these imports at the top
import requests
import time
from datetime import datetime
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor

# Add these constants after the imports
AWS_PRICE_LIST_BASE = "https://pricing.us-east-1.amazonaws.com"
PRICE_LIST_ENDPOINTS = {
    'AmazonEC2': '/offers/v1.0/aws/AmazonEC2/current/{region}/index.json',
    'AmazonRDS': '/offers/v1.0/aws/AmazonRDS/current/{region}/index.json',
    'AmazonS3': '/offers/v1.0/aws/AmazonS3/current/{region}/index.json',
    'AWSLambda': '/offers/v1.0/aws/AWSLambda/current/{region}/index.json',
    'AmazonDynamoDB': '/offers/v1.0/aws/AmazonDynamoDB/current/{region}/index.json',
    'AmazonCloudFront': '/offers/v1.0/aws/AmazonCloudFront/current/index.json'
}

# Replace the _get_service_pricing method in AWSMultiAgentPackager class
def _get_service_pricing(self, service_code: str, config: Dict, region: str) -> Dict:
    """Get real-time pricing for AWS services using Price List API"""
    try:
        if service_code not in PRICE_LIST_ENDPOINTS:
            return self._get_estimated_pricing(service_code)

        # Get pricing data from AWS Price List API
        url = AWS_PRICE_LIST_BASE + PRICE_LIST_ENDPOINTS[service_code].format(region=region)
        response = requests.get(url)
        
        if response.status_code != 200:
            st.warning(f"Could not fetch pricing for {service_code}. Using estimates.")
            return self._get_estimated_pricing(service_code)

        data = response.json()
        monthly_cost = 0.0
        
        # Process different service types
        if service_code == 'AmazonEC2':
            monthly_cost = self._calculate_ec2_cost(data, config, region)
        elif service_code == 'AmazonRDS':
            monthly_cost = self._calculate_rds_cost(data, config, region)
        elif service_code == 'AmazonS3':
            monthly_cost = self._calculate_s3_cost(data, config)
        elif service_code == 'AWSLambda':
            monthly_cost = self._calculate_lambda_cost(data, config)
        else:
            monthly_cost = self._get_estimated_pricing(service_code)['monthly_cost']

        return {
            'monthly_cost': monthly_cost,
            'alternatives': self._get_service_alternatives(service_code),
            'last_updated': datetime.now().isoformat()
        }

    except Exception as e:
        st.warning(f"Error fetching price for {service_code}: {str(e)}")
        return self._get_estimated_pricing(service_code)

def _calculate_ec2_cost(self, price_data: Dict, config: Dict, region: str) -> float:
    """Calculate EC2 instance cost"""
    instance_type = config.get('instance_type', 't3.medium')
    os = config.get('os', 'Linux')
    hours = 730  # Average hours per month
    
    for product in price_data.get('products', {}).values():
        attributes = product.get('attributes', {})
        if (attributes.get('instanceType') == instance_type and 
            attributes.get('operatingSystem') == os and
            attributes.get('tenancy') == 'Shared'):
            
            # Get pricing terms
            sku = product.get('sku')
            terms = price_data.get('terms', {}).get('OnDemand', {})
            
            for term in terms.values():
                if term.get('sku') == sku:
                    for price_dim in term.get('priceDimensions', {}).values():
                        price_per_hour = float(price_dim.get('pricePerUnit', {}).get('USD', 0))
                        return price_per_hour * hours
    
    return 0.0

def _calculate_rds_cost(self, price_data: Dict, config: Dict, region: str) -> float:
    """Calculate RDS instance cost"""
    instance_type = config.get('instance', 'db.t3.medium')
    engine = config.get('engine', 'PostgreSQL')
    hours = 730
    
    for product in price_data.get('products', {}).values():
        attributes = product.get('attributes', {})
        if (attributes.get('instanceType') == instance_type and 
            attributes.get('databaseEngine') == engine):
            
            sku = product.get('sku')
            terms = price_data.get('terms', {}).get('OnDemand', {})
            
            for term in terms.values():
                if term.get('sku') == sku:
                    for price_dim in term.get('priceDimensions', {}).values():
                        price_per_hour = float(price_dim.get('pricePerUnit', {}).get('USD', 0))
                        return price_per_hour * hours
    
    return 0.0

def _calculate_s3_cost(self, price_data: Dict, config: Dict) -> float:
    """Calculate S3 storage cost"""
    storage_class = config.get('storage_class', 'STANDARD')
    storage_gb = config.get('storage_gb', 100)
    
    for product in price_data.get('products', {}).values():
        attributes = product.get('attributes', {})
        if (attributes.get('storageClass') == storage_class and 
            attributes.get('volumeType') == 'Standard'):
            
            sku = product.get('sku')
            terms = price_data.get('terms', {}).get('OnDemand', {})
            
            for term in terms.values():
                if term.get('sku') == sku:
                    for price_dim in term.get('priceDimensions', {}).values():
                        price_per_gb = float(price_dim.get('pricePerUnit', {}).get('USD', 0))
                        return price_per_gb * storage_gb
    
    return 0.0

def _calculate_lambda_cost(self, price_data: Dict, config: Dict) -> float:
    """Calculate Lambda cost"""
    memory = config.get('memory', 512)
    invocations = config.get('invocations', 1000000)
    avg_duration_ms = config.get('duration_ms', 500)
    
    # Lambda pricing components
    request_price = 0.0000002  # $0.20 per 1M requests
    compute_price = 0.0000166667  # per GB-second
    
    # Calculate costs
    request_cost = (invocations * request_price)
    compute_gb_seconds = (invocations * avg_duration_ms * (memory / 1024) / 1000)
    compute_cost = compute_gb_seconds * compute_price
    
    return request_cost + compute_cost

def _get_service_alternatives(self, service_code: str) -> List[str]:
    """Get alternative services based on workload type"""
    alternatives = {
        'AmazonEC2': ['AWSLambda', 'AWSFargate', 'AmazonLightsail'],
        'AmazonRDS': ['AmazonDynamoDB', 'AmazonAurora', 'AmazonDocumentDB'],
        'AmazonS3': ['AmazonEFS', 'AmazonFSx', 'AWSStorageGateway'],
        'AWSLambda': ['AmazonEC2', 'AWSFargate', 'AmazonLightsail'],
        'AmazonDynamoDB': ['AmazonRDS', 'AmazonDocumentDB', 'AmazonElastiCache'],
        'AmazonCloudFront': ['AWSGlobalAccelerator', 'AmazonRoute53']
    }
    return alternatives.get(service_code, [])