import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor

@dataclass
class AWSPriceList:
    """AWS Price List API Handler"""
    BASE_URL = "https://pricing.us-east-1.amazonaws.com"
    
    @staticmethod
    def get_services() -> Dict:
        """Get list of all AWS services"""
        try:
            response = requests.get(f"{AWSPriceList.BASE_URL}/offers/v1.0/aws/index.json")
            if response.status_code == 200:
                return response.json().get('offers', {})
            return {}
        except Exception as e:
            st.error(f"Error fetching services: {str(e)}")
            return {}

    @staticmethod
    def get_service_pricing(service: str, region: str) -> Dict:
        """Get pricing data for a service"""
        try:
            url = f"{AWSPriceList.BASE_URL}/offers/v1.0/aws/{service}/current/{region}/index.json"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            st.error(f"Error fetching {service} pricing: {str(e)}")
            return {}

    @staticmethod
    def get_regions() -> List[str]:
        """Get list of AWS regions"""
        try:
            response = requests.get(f"{AWSPriceList.BASE_URL}/meta/regions.json")
            if response.status_code == 200:
                return list(response.json().keys())
            return []
        except Exception as e:
            st.error(f"Error fetching regions: {str(e)}")
            return []

class AWSPricingCalculator:
    """Dynamic AWS Service Pricing Calculator"""
    
    def __init__(self):
        self.price_list = AWSPriceList()
        self.services = self.price_list.get_services()
        self.regions = self.price_list.get_regions()

    def calculate_service_cost(self, service: str, config: Dict, region: str) -> Dict:
        """Calculate cost for any AWS service"""
        pricing_data = self.price_list.get_service_pricing(service, region)
        if not pricing_data:
            return {"error": f"No pricing data available for {service}"}

        monthly_cost = self._process_pricing_data(pricing_data, config)
        alternatives = self._find_alternatives(service, config)

        return {
            "monthly_cost": monthly_cost,
            "alternatives": alternatives,
            "last_updated": datetime.now().isoformat()
        }

    def _process_pricing_data(self, pricing_data: Dict, config: Dict) -> float:
        """Process pricing data based on service attributes"""
        total_cost = 0.0
        products = pricing_data.get('products', {})
        terms = pricing_data.get('terms', {}).get('OnDemand', {})

        for product in products.values():
            if self._matches_configuration(product.get('attributes', {}), config):
                sku = product.get('sku')
                for term in terms.values():
                    if term.get('sku') == sku:
                        total_cost += self._calculate_price_dimensions(
                            term.get('priceDimensions', {}),
                            config
                        )

        return total_cost

    def _matches_configuration(self, attributes: Dict, config: Dict) -> bool:
        """Check if product attributes match required configuration"""
        for key, value in config.items():
            if key in attributes and str(attributes[key]) != str(value):
                return False
        return True

    def _calculate_price_dimensions(self, dimensions: Dict, config: Dict) -> float:
        """Calculate cost across all price dimensions"""
        total_cost = 0.0
        usage_hours = config.get('hours', 730)  # Default to monthly hours

        for dimension in dimensions.values():
            unit = dimension.get('unit', '')
            price = float(dimension.get('pricePerUnit', {}).get('USD', 0))

            if 'Hour' in unit:
                total_cost += price * usage_hours
            elif 'GB' in unit:
                total_cost += price * config.get('size_gb', 0)
            elif 'Requests' in unit:
                total_cost += price * config.get('requests', 0) / 1000  # Price per 1000 requests
            else:
                # Handle other units based on config
                quantity = config.get(unit.lower(), 1)
                total_cost += price * quantity

        return total_cost

    def _find_alternatives(self, service: str, config: Dict) -> List[Dict]:
        """Find alternative services based on workload requirements"""
        alternatives = []
        service_category = self._get_service_category(service)
        
        for other_service in self.services:
            if (other_service != service and 
                self._get_service_category(other_service) == service_category):
                alternatives.append({
                    "service": other_service,
                    "estimated_savings": self._estimate_savings(service, other_service, config)
                })

        return sorted(alternatives, key=lambda x: x['estimated_savings'], reverse=True)[:3]

    def _get_service_category(self, service: str) -> str:
        """Get service category from AWS service metadata"""
        try:
            response = requests.get(
                f"{AWSPriceList.BASE_URL}/offers/v1.0/aws/{service}/current/metadata.json"
            )
            if response.status_code == 200:
                return response.json().get('serviceGroup', '')
            return ''
        except Exception:
            return ''

    def _estimate_savings(self, current_service: str, alternative: str, config: Dict) -> float:
        """Estimate potential cost savings for alternative service"""
        current_cost = self.calculate_service_cost(current_service, config, config.get('region'))
        alt_cost = self.calculate_service_cost(alternative, config, config.get('region'))
        
        return (current_cost.get('monthly_cost', 0) - alt_cost.get('monthly_cost', 0))

# Usage in your main application
def get_service_pricing_explorer():
    calculator = AWSPricingCalculator()
    
    # Dynamic service selection
    service = st.selectbox("Select AWS Service", calculator.services)
    region = st.selectbox("Select Region", calculator.regions)
    
    # Dynamic configuration based on service
    config = {}
    pricing_data = calculator.price_list.get_service_pricing(service, region)
    
    if pricing_data:
        # Extract available attributes for configuration
        sample_product = next(iter(pricing_data.get('products', {}).values()), {})
        attributes = sample_product.get('attributes', {})
        
        st.subheader("Configuration")
        for attr, value in attributes.items():
            if attr.lower() in ['instancetype', 'vcpu', 'memory', 'storage']:
                config[attr] = st.text_input(f"{attr}", value)
    
        # Calculate costs
        if st.button("Calculate Cost"):
            result = calculator.calculate_service_cost(service, config, region)
            
            st.subheader("Cost Breakdown")
            st.write(f"Monthly Cost: ${result['monthly_cost']:.2f}")
            
            st.subheader("Alternative Services")
            for alt in result['alternatives']:
                st.write(f"- {alt['service']}: Potential savings ${alt['estimated_savings']:.2f}/month")

# Add to your Streamlit UI
if __name__ == "__main__":
    st.title("AWS Service Pricing Calculator")
    get_service_pricing_explorer()