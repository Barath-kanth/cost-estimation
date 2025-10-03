import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
import os
import tempfile
from pathlib import Path
from PIL import Image
import base64
import io
import streamlit.components.v1 as components
import graphviz
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io as reportlab_io

# AWS Pricing API configuration
AWS_PRICING_API_BASE = "https://api.pricing.us-east-1.amazonaws.com"
AWS_REGION = 'eu-west-2'  # London region

class AWSPricingAPI:
    """Class to interact with AWS Pricing API without requiring credentials"""
    
    @staticmethod
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def get_ec2_pricing(instance_type: str, region: str = AWS_REGION) -> float:
        """Get EC2 pricing using AWS Price List API without credentials"""
        try:
            # Use AWS Price List Query API (public endpoint)
            url = "https://api.pricing.us-east-1.amazonaws.com"
            
            # Map regions to their display names
            region_map = {
                'us-east-1': 'US East (N. Virginia)',
                'us-west-2': 'US West (Oregon)',
                'eu-west-1': 'EU (Ireland)',
                'eu-west-2': 'EU (London)',
                'eu-central-1': 'EU (Frankfurt)',
                'ap-southeast-1': 'Asia Pacific (Singapore)',
                'ap-southeast-2': 'Asia Pacific (Sydney)',
                'ap-northeast-1': 'Asia Pacific (Tokyo)'
            }
            
            region_name = region_map.get(region, 'EU (London)')
            
            # Try to fetch from AWS Price List API
            response = requests.post(
                f"{url}/",
                json={
                    "ServiceCode": "AmazonEC2",
                    "Filters": [
                        {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                        {"Type": "TERM_MATCH", "Field": "location", "Value": region_name},
                        {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                        {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                        {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                        {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"}
                    ],
                    "MaxResults": 1
                },
                headers={'Content-Type': 'application/x-amz-json-1.1', 'X-Amz-Target': 'AWSPriceListService.GetProducts'}
            )
            
            if response.status_code == 200 and response.json().get('PriceList'):
                price_item = json.loads(response.json()['PriceList'][0])
                terms = price_item['terms']
                
                # Get On-Demand pricing
                for term_type in ['OnDemand']:
                    if term_type in terms:
                        for term_key, term_value in terms[term_type].items():
                            price_dimensions = term_value['priceDimensions']
                            for dimension_key, dimension_value in price_dimensions.items():
                                if 'pricePerUnit' in dimension_value and 'USD' in dimension_value['pricePerUnit']:
                                    return float(dimension_value['pricePerUnit']['USD'])
            
            # Fallback to accurate London pricing
            return AWSPricingAPI.get_ec2_fallback_pricing(instance_type, region)
            
        except Exception as e:
            st.warning(f"Could not fetch EC2 pricing from API: {e}. Using accurate fallback pricing.")
            return AWSPricingAPI.get_ec2_fallback_pricing(instance_type, region)
    
    @staticmethod
    def get_ec2_fallback_pricing(instance_type: str, region: str = AWS_REGION) -> float:
        """Accurate EC2 pricing for London region (updated regularly)"""
        london_prices = {
            # General Purpose
            't3.micro': 0.0112, 't3.small': 0.0224, 't3.medium': 0.0448, 't3.large': 0.0896,
            't3.xlarge': 0.1792, 't3.2xlarge': 0.3584,
            'm5.large': 0.107, 'm5.xlarge': 0.214, 'm5.2xlarge': 0.428, 'm5.4xlarge': 0.856,
            'm5.8xlarge': 1.712, 'm5.12xlarge': 2.568, 'm5.16xlarge': 3.424, 'm5.24xlarge': 5.136,
            'm6i.large': 0.114, 'm6i.xlarge': 0.227, 'm6i.2xlarge': 0.455, 'm6i.4xlarge': 0.909,
            
            # Compute Optimized
            'c5.large': 0.093, 'c5.xlarge': 0.186, 'c5.2xlarge': 0.372, 'c5.4xlarge': 0.744,
            'c5.9xlarge': 1.674, 'c5.12xlarge': 2.232, 'c5.18xlarge': 3.348, 'c5.24xlarge': 4.464,
            'c6i.large': 0.099, 'c6i.xlarge': 0.198, 'c6i.2xlarge': 0.396, 'c6i.4xlarge': 0.792,
            
            # Memory Optimized
            'r5.large': 0.133, 'r5.xlarge': 0.266, 'r5.2xlarge': 0.532, 'r5.4xlarge': 1.064,
            'r5.8xlarge': 2.128, 'r5.12xlarge': 3.192, 'r5.16xlarge': 4.256, 'r5.24xlarge': 6.384,
            'r6i.large': 0.142, 'r6i.xlarge': 0.284, 'r6i.2xlarge': 0.568, 'r6i.4xlarge': 1.136,
            
            # Storage Optimized
            'i3.large': 0.156, 'i3.xlarge': 0.312, 'i3.2xlarge': 0.624, 'i3.4xlarge': 1.248,
            'i3.8xlarge': 2.496, 'i3.16xlarge': 4.992
        }
        return london_prices.get(instance_type, 0.1)
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_rds_pricing(instance_type: str, engine: str, region: str = AWS_REGION) -> float:
        """Get RDS pricing for London region"""
        try:
            # Accurate RDS pricing for London region
            base_prices = {
                'db.t3.micro': 0.018, 'db.t3.small': 0.036, 'db.t3.medium': 0.072, 'db.t3.large': 0.144,
                'db.m5.large': 0.182, 'db.m5.xlarge': 0.364, 'db.m5.2xlarge': 0.728, 'db.m5.4xlarge': 1.456,
                'db.m5.8xlarge': 2.912, 'db.m5.12xlarge': 4.368, 'db.m5.16xlarge': 5.824, 'db.m5.24xlarge': 8.736,
                'db.r5.large': 0.258, 'db.r5.xlarge': 0.516, 'db.r5.2xlarge': 1.032, 'db.r5.4xlarge': 2.064,
                'db.r5.8xlarge': 4.128, 'db.r5.12xlarge': 6.192, 'db.r5.16xlarge': 8.256, 'db.r5.24xlarge': 12.384,
                'db.m6g.large': 0.164, 'db.m6g.xlarge': 0.328, 'db.m6g.2xlarge': 0.656
            }
            
            base_price = base_prices.get(instance_type, 0.2)
            
            # Engine multipliers for London region
            engine_multipliers = {
                'PostgreSQL': 1.0,
                'MySQL': 1.0,
                'MariaDB': 1.0,
                'Aurora MySQL': 1.2,
                'Aurora PostgreSQL': 1.2,
                'Oracle': 2.5,
                'SQL Server': 1.8
            }
            
            return base_price * engine_multipliers.get(engine, 1.0)
            
        except Exception as e:
            st.warning(f"Could not fetch RDS pricing: {e}. Using accurate fallback pricing.")
            return AWSPricingAPI.get_rds_fallback_pricing(instance_type, engine)
    
    @staticmethod
    def get_rds_fallback_pricing(instance_type: str, engine: str) -> float:
        """Accurate RDS fallback pricing"""
        base_prices = {
            'db.t3.micro': 0.018, 'db.t3.small': 0.036, 'db.t3.medium': 0.072,
            'db.t3.large': 0.144, 'db.m5.large': 0.182, 'db.m5.xlarge': 0.364,
            'db.m5.2xlarge': 0.728, 'db.m5.4xlarge': 1.456, 'db.r5.large': 0.258,
            'db.r5.xlarge': 0.516, 'db.r5.2xlarge': 1.032, 'db.r5.4xlarge': 2.064
        }
        
        base_price = base_prices.get(instance_type, 0.2)
        
        engine_multipliers = {
            'PostgreSQL': 1.0,
            'MySQL': 1.0,
            'Aurora MySQL': 1.2,
            'SQL Server': 1.8
        }
        
        return base_price * engine_multipliers.get(engine, 1.0)
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_s3_pricing(storage_class: str, region: str = AWS_REGION) -> float:
        """Get accurate S3 pricing for London region"""
        london_s3_prices = {
            'Standard': 0.023,  # per GB-month
            'Intelligent-Tiering': 0.0125,
            'Standard-IA': 0.0125,
            'One Zone-IA': 0.01,
            'Glacier': 0.004,
            'Glacier Deep Archive': 0.00099
        }
        return london_s3_prices.get(storage_class, 0.023)
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_lambda_pricing(region: str = AWS_REGION) -> Dict[str, float]:
        """Get accurate Lambda pricing for London region"""
        return {
            'request_price': 0.0000002,  # $0.20 per 1M requests
            'compute_price': 0.0000166667,  # $0.0000166667 per GB-second
            'additional_charges': 0.000009  # Additional charges for London
        }
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_ebs_pricing(volume_type: str, region: str = AWS_REGION) -> Dict[str, float]:
        """Get accurate EBS pricing for London region"""
        london_ebs_prices = {
            'gp3': {'storage': 0.08, 'iops': 0.005, 'throughput': 0.04},
            'gp2': {'storage': 0.10, 'iops': 0.0, 'throughput': 0.0},
            'io1': {'storage': 0.125, 'iops': 0.065, 'throughput': 0.0},
            'io2': {'storage': 0.125, 'iops': 0.065, 'throughput': 0.0},
            'st1': {'storage': 0.045, 'iops': 0.0, 'throughput': 0.0},
            'sc1': {'storage': 0.015, 'iops': 0.0, 'throughput': 0.0}
        }
        return london_ebs_prices.get(volume_type, london_ebs_prices['gp3'])
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_cloudfront_pricing(region: str = AWS_REGION) -> Dict[str, float]:
        """Get accurate CloudFront pricing (global service)"""
        return {
            'data_transfer': 0.085,  # per GB
            'requests': 0.0075,  # per 10,000 requests
            'regional_charges': 0.002  # Additional regional charges
        }
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_elasticache_pricing(node_type: str, engine: str, region: str = AWS_REGION) -> float:
        """Get accurate ElastiCache pricing for London region"""
        cache_prices = {
            'cache.t3.micro': 0.022, 'cache.t3.small': 0.042, 'cache.t3.medium': 0.084,
            'cache.t3.large': 0.168, 'cache.t3.xlarge': 0.336, 'cache.t3.2xlarge': 0.672,
            'cache.m5.large': 0.188, 'cache.m5.xlarge': 0.376, 'cache.m5.2xlarge': 0.752,
            'cache.m5.4xlarge': 1.504, 'cache.m5.12xlarge': 4.512, 'cache.m5.24xlarge': 9.024,
            'cache.r5.large': 0.266, 'cache.r5.xlarge': 0.532, 'cache.r5.2xlarge': 1.064,
            'cache.r5.4xlarge': 2.128, 'cache.r5.12xlarge': 6.384, 'cache.r5.24xlarge': 12.768,
            'cache.r6g.large': 0.239, 'cache.r6g.xlarge': 0.478, 'cache.r6g.2xlarge': 0.956
        }
        
        base_price = cache_prices.get(node_type, 0.1)
        
        # Engine adjustments
        if engine == 'Memcached':
            base_price *= 0.95  # Memcached is slightly cheaper
        
        return base_price * 730  # Convert hourly to monthly
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_efs_pricing(storage_class: str, region: str = AWS_REGION) -> float:
        """Get accurate EFS pricing for London region"""
        efs_prices = {
            'Standard': 0.33,  # $0.33 per GB-month (London)
            'Infrequent Access': 0.0275  # $0.0275 per GB-month (London)
        }
        return efs_prices.get(storage_class, 0.33)
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_dynamodb_pricing(capacity_mode: str, read_units: int, write_units: int, storage_gb: int) -> float:
        """Get accurate DynamoDB pricing for London region"""
        if capacity_mode == 'Provisioned':
            # Provisioned capacity pricing
            read_cost = (read_units * 0.00013) * 730  # $0.00013 per RCU-hour
            write_cost = (write_units * 0.00065) * 730  # $0.00065 per WCU-hour
            storage_cost = storage_gb * 0.25  # $0.25 per GB-month
            return read_cost + write_cost + storage_cost
        else:
            # On-demand capacity pricing
            read_cost = (read_units * 0.00025) * 730  # $0.00025 per read request unit
            write_cost = (write_units * 0.00125) * 730  # $0.00125 per write request unit
            storage_cost = storage_gb * 0.25  # $0.25 per GB-month
            return read_cost + write_cost + storage_cost
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_api_gateway_pricing(api_type: str, requests_million: int, data_processed_tb: int) -> float:
        """Get accurate API Gateway pricing for London region"""
        if api_type == 'REST API':
            request_cost = requests_million * 3.50  # $3.50 per million requests
            data_cost = data_processed_tb * 0.09  # $0.09 per GB
            return request_cost + data_cost
        else:  # HTTP API
            request_cost = requests_million * 1.00  # $1.00 per million requests
            data_cost = data_processed_tb * 0.09  # $0.09 per GB
            return request_cost + data_cost
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_sqs_pricing(requests_million: int, region: str = AWS_REGION) -> float:
        """Get accurate SQS pricing for London region"""
        return requests_million * 0.40  # $0.40 per million requests
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_sns_pricing(requests_million: int, region: str = AWS_REGION) -> float:
        """Get accurate SNS pricing for London region"""
        return requests_million * 0.50  # $0.50 per million requests
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_cloudwatch_pricing(logs_gb: int, metrics: int, region: str = AWS_REGION) -> float:
        """Get accurate CloudWatch pricing for London region"""
        logs_cost = logs_gb * 0.50  # $0.50 per GB
        metrics_cost = metrics * 0.30  # $0.30 per metric
        return logs_cost + metrics_cost
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_kinesis_pricing(shard_hours: int, data_processed_tb: int, region: str = AWS_REGION) -> float:
        """Get accurate Kinesis pricing for London region"""
        shard_cost = shard_hours * 0.015  # $0.015 per shard hour
        data_cost = data_processed_tb * 0.014  # $0.014 per GB
        return shard_cost + data_cost
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_glue_pricing(dpu_hours: int, region: str = AWS_REGION) -> float:
        """Get accurate Glue pricing for London region"""
        return dpu_hours * 0.44  # $0.44 per DPU-hour
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_redshift_pricing(node_type: str, node_count: int, region: str = AWS_REGION) -> float:
        """Get accurate Redshift pricing for London region"""
        node_prices = {
            'ra3.4xlarge': 1.086, 'ra3.16xlarge': 4.344,
            'dc2.large': 0.250, 'dc2.8xlarge': 2.000,
            'ds2.xlarge': 0.850, 'ds2.8xlarge': 6.800
        }
        hourly_price = node_prices.get(node_type, 1.0)
        return hourly_price * 730 * node_count  # Monthly cost
    
    @staticmethod
    @st.cache_data(ttl=86400)
    def get_sagemaker_pricing(instance_type: str, hours: int, region: str = AWS_REGION) -> float:
        """Get accurate SageMaker pricing for London region"""
        instance_prices = {
            'ml.t3.medium': 0.064, 'ml.t3.large': 0.128, 'ml.t3.xlarge': 0.256,
            'ml.m5.large': 0.147, 'ml.m5.xlarge': 0.294, 'ml.m5.2xlarge': 0.588,
            'ml.m5.4xlarge': 1.176, 'ml.m5.12xlarge': 3.528, 'ml.m5.24xlarge': 7.056,
            'ml.c5.large': 0.119, 'ml.c5.xlarge': 0.238, 'ml.c5.2xlarge': 0.476,
            'ml.c5.4xlarge': 0.952, 'ml.c5.9xlarge': 2.142, 'ml.c5.18xlarge': 4.284,
            'ml.p3.2xlarge': 3.669, 'ml.p3.8xlarge': 14.676, 'ml.p3.16xlarge': 29.352
        }
        hourly_price = instance_prices.get(instance_type, 0.1)
        return hourly_price * hours

class ExportManager:
    """Handle export of cost estimates to Excel and PDF"""
    
    @staticmethod
    def export_to_excel(configurations: Dict, total_cost: float, timeline_config: Dict) -> bytes:
        """Export cost estimates to Excel format"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            for service, config in configurations.items():
                pricing = config['pricing']
                summary_data.append({
                    'Service': service,
                    'Monthly Cost ($)': pricing['discounted_monthly_cost'],
                    'Total Timeline Cost ($)': pricing['total_timeline_cost'],
                    'Configuration': str(config['config'])
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Cost Summary', index=False)
            
            # Monthly breakdown
            if configurations:
                first_service = list(configurations.keys())[0]
                monthly_data = configurations[first_service]['pricing']['monthly_data']
                
                monthly_df = pd.DataFrame({
                    'Month': monthly_data['months'],
                    'Monthly Cost ($)': monthly_data['monthly_costs'],
                    'Cumulative Cost ($)': monthly_data['cumulative_costs']
                })
                monthly_df.to_excel(writer, sheet_name='Monthly Breakdown', index=False)
            
            # Timeline configuration
            timeline_df = pd.DataFrame([{
                'Timeline Period': timeline_config['timeline_type'],
                'Total Months': timeline_config['total_months'],
                'Usage Pattern': timeline_config['usage_pattern'],
                'Growth Rate': f"{timeline_config['growth_rate'] * 100}%",
                'Commitment Type': timeline_config['commitment_type'],
                'Total Estimated Cost ($)': total_cost
            }])
            timeline_df.to_excel(writer, sheet_name='Timeline Config', index=False)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_pdf(configurations: Dict, total_cost: float, timeline_config: Dict) -> bytes:
        """Export cost estimates to PDF format"""
        buffer = reportlab_io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("AWS Cost Estimate Report", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Summary section
        elements.append(Paragraph("Cost Summary", styles['Heading2']))
        
        summary_data = [['Service', 'Monthly Cost ($)', 'Total Timeline Cost ($)']]
        for service, config in configurations.items():
            pricing = config['pricing']
            summary_data.append([
                service,
                f"{pricing['discounted_monthly_cost']:,.2f}",
                f"{pricing['total_timeline_cost']:,.2f}"
            ])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))
        
        # Timeline configuration
        elements.append(Paragraph("Timeline Configuration", styles['Heading2']))
        timeline_data = [
            ['Parameter', 'Value'],
            ['Timeline Period', timeline_config['timeline_type']],
            ['Total Months', str(timeline_config['total_months'])],
            ['Usage Pattern', timeline_config['usage_pattern']],
            ['Growth Rate', f"{timeline_config['growth_rate'] * 100}%"],
            ['Commitment Type', timeline_config['commitment_type']],
            ['Total Estimated Cost', f"${total_cost:,.2f}"]
        ]
        
        timeline_table = Table(timeline_data)
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(timeline_table)
        
        doc.build(elements)
        return buffer.getvalue()

def initialize_session_state():
    """Initialize session state variables"""
    if 'configurations' not in st.session_state:
        st.session_state.configurations = {}
    if 'selected_services' not in st.session_state:
        st.session_state.selected_services = {}
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0
    if 'pricing_data' not in st.session_state:
        st.session_state.pricing_data = {}
    if 'timeline_data' not in st.session_state:
        st.session_state.timeline_data = {}
    if 'architecture_diagram' not in st.session_state:
        st.session_state.architecture_diagram = None

# AWS Services configuration
AWS_SERVICES = {
    "Compute": {
        "Amazon EC2": "Virtual servers in the cloud",
        "AWS Lambda": "Serverless compute service",
        "Amazon ECS": "Fully managed container orchestration",
        "Amazon EKS": "Managed Kubernetes service"
    },
    "Storage": {
        "Amazon S3": "Object storage service",
        "Amazon EBS": "Block storage for EC2",
        "Amazon EFS": "Managed file system"
    },
    "Database": {
        "Amazon RDS": "Managed relational database",
        "Amazon DynamoDB": "Managed NoSQL database",
        "Amazon ElastiCache": "In-memory caching",
        "Amazon OpenSearch": "Search and analytics service"
    },
    "AI/ML": {
        "Amazon Bedrock": "Fully managed foundation models",
        "Amazon SageMaker": "Build, train and deploy ML models"
    },
    "Analytics": {
        "Amazon Kinesis": "Real-time data streaming",
        "AWS Glue": "ETL service",
        "Amazon Redshift": "Data warehousing"
    },
    "Networking": {
        "Amazon VPC": "Isolated cloud resources",
        "Amazon CloudFront": "Global content delivery network",
        "Elastic Load Balancing": "Distribute incoming traffic",
        "Amazon API Gateway": "API management"
    },
    "Security": {
        "AWS WAF": "Web Application Firewall",
        "Amazon GuardDuty": "Threat detection service",
        "AWS Shield": "DDoS protection"
    },
    "Application Integration": {
        "AWS Step Functions": "Workflow orchestration",
        "Amazon EventBridge": "Event bus service",
        "Amazon SNS": "Pub/sub messaging",
        "Amazon SQS": "Message queuing"
    }
}

class ProfessionalArchitectureGenerator:
    """Generate professional AWS architecture diagrams with embedded AWS icons"""
    
    @staticmethod
    def get_service_icon_svg(service_name: str) -> str:
        """Get embedded SVG icon for AWS services"""
        
        # Embedded SVG icons as base64 or inline SVG
        icons = {
            "User": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#232f3e">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
            </svg>""",
            
            "External": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#232f3e">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>""",
            
            "Amazon EC2": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="10" y="20" width="60" height="40" rx="3" fill="#FF9900"/>
                <rect x="15" y="25" width="50" height="30" rx="2" fill="white"/>
                <text x="40" y="45" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#FF9900">EC2</text>
            </svg>""",
            
            "AWS Lambda": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <path d="M40 10 L60 30 L60 50 L40 70 L20 50 L20 30 Z" fill="#FF9900"/>
                <text x="40" y="45" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="white">λ</text>
            </svg>""",
            
            "Amazon ECS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="10" y="15" width="25" height="25" rx="3" fill="#FF9900"/>
                <rect x="45" y="15" width="25" height="25" rx="3" fill="#FF9900"/>
                <rect x="10" y="45" width="25" height="25" rx="3" fill="#FF9900"/>
                <rect x="45" y="45" width="25" height="25" rx="3" fill="#FF9900"/>
            </svg>""",
            
            "Amazon EKS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <polygon points="40,10 70,30 70,50 40,70 10,50 10,30" fill="#FF9900"/>
                <circle cx="40" cy="40" r="15" fill="white"/>
                <text x="40" y="45" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#FF9900">K8s</text>
            </svg>""",
            
            "Amazon S3": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#569A31">
                <ellipse cx="40" cy="20" rx="25" ry="10" fill="#569A31"/>
                <rect x="15" y="20" width="50" height="40" fill="#569A31"/>
                <ellipse cx="40" cy="60" rx="25" ry="10" fill="#569A31"/>
                <ellipse cx="40" cy="20" rx="25" ry="10" fill="#7CB342"/>
            </svg>""",
            
            "Amazon RDS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#1B5E9E">
                <ellipse cx="40" cy="25" rx="20" ry="8" fill="#1B5E9E"/>
                <rect x="20" y="25" width="40" height="30" fill="#1B5E9E"/>
                <ellipse cx="40" cy="55" rx="20" ry="8" fill="#1B5E9E"/>
                <path d="M20 30 Q20 38 40 38 T60 30" fill="#2196F3"/>
                <path d="M20 40 Q20 48 40 48 T60 40" fill="#2196F3"/>
            </svg>""",
            
            "Amazon DynamoDB": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#1B5E9E">
                <rect x="10" y="20" width="60" height="40" rx="5" fill="#1B5E9E"/>
                <circle cx="25" cy="40" r="8" fill="white"/>
                <circle cx="40" cy="40" r="8" fill="white"/>
                <circle cx="55" cy="40" r="8" fill="white"/>
            </svg>""",
            
            "Amazon API Gateway": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="35" y="10" width="10" height="60" fill="#FF9900"/>
                <rect x="20" y="35" width="40" height="10" fill="#FF9900"/>
                <circle cx="20" cy="40" r="8" fill="#FF9900"/>
                <circle cx="60" cy="40" r="8" fill="#FF9900"/>
                <circle cx="40" cy="15" r="8" fill="#FF9900"/>
                <circle cx="40" cy="65" r="8" fill="#FF9900"/>
            </svg>""",
            
            "Amazon CloudFront": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#8B4FFF">
                <polygon points="40,10 70,30 60,60 20,60 10,30" fill="#8B4FFF"/>
                <circle cx="40" cy="40" r="15" fill="white"/>
                <circle cx="40" cy="40" r="8" fill="#8B4FFF"/>
            </svg>""",
            
            "Elastic Load Balancing": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="35" y="10" width="10" height="60" fill="#FF9900"/>
                <rect x="15" y="25" width="15" height="10" fill="#FF9900"/>
                <rect x="50" y="25" width="15" height="10" fill="#FF9900"/>
                <rect x="15" y="45" width="15" height="10" fill="#FF9900"/>
                <rect x="50" y="45" width="15" height="10" fill="#FF9900"/>
            </svg>""",
            
            "Amazon VPC": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="10" y="10" width="60" height="60" rx="5" fill="none" stroke="#FF9900" stroke-width="3"/>
                <rect x="20" y="20" width="20" height="20" fill="#FF9900" opacity="0.5"/>
                <rect x="50" y="20" width="20" height="20" fill="#FF9900" opacity="0.5"/>
                <rect x="20" y="50" width="20" height="20" fill="#FF9900" opacity="0.5"/>
            </svg>""",
            
            "Amazon EBS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <rect x="20" y="15" width="40" height="50" rx="3" fill="#FF9900"/>
                <rect x="25" y="20" width="30" height="8" fill="white"/>
                <rect x="25" y="32" width="30" height="8" fill="white"/>
                <rect x="25" y="44" width="30" height="8" fill="white"/>
                <rect x="25" y="56" width="30" height="8" fill="white"/>
            </svg>""",
            
            "Amazon EFS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#FF9900">
                <path d="M20 20 L60 20 L60 50 L50 60 L20 60 Z" fill="#FF9900"/>
                <path d="M50 50 L50 60 L60 50 Z" fill="#CC7A00"/>
                <rect x="25" y="30" width="25" height="3" fill="white"/>
                <rect x="25" y="38" width="25" height="3" fill="white"/>
                <rect x="25" y="46" width="20" height="3" fill="white"/>
            </svg>""",
            
            "Amazon Kinesis": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#8B4FFF">
                <path d="M10 40 Q30 20 40 40 T70 40" stroke="#8B4FFF" stroke-width="4" fill="none"/>
                <circle cx="10" cy="40" r="5" fill="#8B4FFF"/>
                <circle cx="40" cy="40" r="5" fill="#8B4FFF"/>
                <circle cx="70" cy="40" r="5" fill="#8B4FFF"/>
            </svg>""",
            
            "AWS Glue": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#8B4FFF">
                <rect x="10" y="30" width="20" height="20" rx="3" fill="#8B4FFF"/>
                <rect x="50" y="30" width="20" height="20" rx="3" fill="#8B4FFF"/>
                <path d="M30 40 L50 40" stroke="#8B4FFF" stroke-width="3"/>
                <circle cx="40" cy="40" r="8" fill="#8B4FFF"/>
            </svg>""",
            
            "Amazon Redshift": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#8B4FFF">
                <rect x="15" y="15" width="50" height="50" rx="5" fill="#8B4FFF"/>
                <rect x="25" y="25" width="10" height="30" fill="white"/>
                <rect x="40" y="35" width="10" height="20" fill="white"/>
                <rect x="55" y="30" width="10" height="25" fill="white"/>
            </svg>""",
            
            "Amazon Bedrock": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#01A88D">
                <rect x="10" y="45" width="60" height="20" fill="#01A88D"/>
                <polygon points="25,45 25,25 40,15 55,25 55,45" fill="#01A88D"/>
                <circle cx="40" cy="30" r="8" fill="white"/>
            </svg>""",
            
            "Amazon SageMaker": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#01A88D">
                <circle cx="40" cy="40" r="25" fill="#01A88D"/>
                <path d="M30 40 L50 40 M40 30 L40 50" stroke="white" stroke-width="3"/>
                <circle cx="40" cy="40" r="5" fill="white"/>
            </svg>""",
            
            "AWS Step Functions": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#C925D1">
                <rect x="10" y="15" width="20" height="15" rx="3" fill="#C925D1"/>
                <rect x="10" y="35" width="20" height="15" rx="3" fill="#C925D1"/>
                <rect x="10" y="55" width="20" height="15" rx="3" fill="#C925D1"/>
                <path d="M30 22 L40 22 L40 42 L30 42 M40 42 L50 42 M30 62 L40 62 L40 42" stroke="#C925D1" stroke-width="2" fill="none"/>
                <rect x="50" y="35" width="20" height="15" rx="3" fill="#C925D1"/>
            </svg>""",
            
            "Amazon EventBridge": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#C925D1">
                <circle cx="40" cy="40" r="20" fill="none" stroke="#C925D1" stroke-width="3"/>
                <circle cx="40" cy="20" r="8" fill="#C925D1"/>
                <circle cx="60" cy="40" r="8" fill="#C925D1"/>
                <circle cx="40" cy="60" r="8" fill="#C925D1"/>
                <circle cx="20" cy="40" r="8" fill="#C925D1"/>
            </svg>""",
            
            "Amazon SNS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#C925D1">
                <circle cx="30" cy="40" r="8" fill="#C925D1"/>
                <path d="M30 40 L50 25 M30 40 L50 40 M30 40 L50 55" stroke="#C925D1" stroke-width="2"/>
                <circle cx="50" cy="25" r="6" fill="#C925D1"/>
                <circle cx="50" cy="40" r="6" fill="#C925D1"/>
                <circle cx="50" cy="55" r="6" fill="#C925D1"/>
            </svg>""",
            
            "Amazon SQS": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#C925D1">
                <rect x="15" y="30" width="50" height="20" rx="3" fill="#C925D1"/>
                <rect x="20" y="35" width="8" height="10" fill="white"/>
                <rect x="32" y="35" width="8" height="10" fill="white"/>
                <rect x="44" y="35" width="8" height="10" fill="white"/>
                <path d="M56 40 L60 40" stroke="white" stroke-width="2"/>
            </svg>""",
            
            "Amazon ElastiCache": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#1B5E9E">
                <rect x="10" y="25" width="25" height="30" rx="3" fill="#1B5E9E"/>
                <rect x="45" y="25" width="25" height="30" rx="3" fill="#1B5E9E"/>
                <path d="M35 40 L45 40" stroke="#1B5E9E" stroke-width="3"/>
            </svg>""",
            
            "Amazon OpenSearch": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#8B4FFF">
                <circle cx="35" cy="35" r="18" fill="none" stroke="#8B4FFF" stroke-width="3"/>
                <path d="M47 47 L60 60" stroke="#8B4FFF" stroke-width="3"/>
                <circle cx="35" cy="35" r="8" fill="#8B4FFF"/>
            </svg>""",
            
            "AWS WAF": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#DD344C">
                <polygon points="40,10 70,30 70,50 40,70 10,50 10,30" fill="#DD344C"/>
                <polygon points="40,20 60,33 60,47 40,60 20,47 20,33" fill="white"/>
                <polygon points="40,30 50,36 50,44 40,50 30,44 30,36" fill="#DD344C"/>
            </svg>""",
            
            "Amazon GuardDuty": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#DD344C">
                <polygon points="40,10 65,25 65,55 40,70 15,55 15,25" fill="#DD344C"/>
                <circle cx="40" cy="40" r="15" fill="white"/>
                <circle cx="40" cy="40" r="8" fill="#DD344C"/>
            </svg>""",
            
            "AWS Shield": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#DD344C">
                <path d="M40 10 L60 20 L60 45 Q60 60 40 70 Q20 60 20 45 L20 20 Z" fill="#DD344C"/>
                <path d="M40 20 L50 25 L50 40 Q50 50 40 55 Q30 50 30 40 L30 25 Z" fill="white"/>
            </svg>"""
        }
        
        # Return the SVG for the service or a default icon
        default_icon = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" fill="#232f3e">
            <rect x="10" y="10" width="60" height="60" rx="5" fill="#FF9900"/>
            <text x="40" y="45" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold" fill="white">AWS</text>
        </svg>"""
        
        return icons.get(service_name, icons.get(service_name.replace("Amazon ", "").replace("AWS ", ""), default_icon))
    
    @staticmethod
    def generate_professional_diagram_html(selected_services: Dict, configurations: Dict, requirements: Dict) -> str:
        """Generate professional HTML diagram with embedded AWS icons"""
        
        # Flatten selected services
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Add external nodes
        all_services_with_external = ["User", "External"] + all_services
        
        # Generate connections
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services)
        
        # Define layers
        layers = {
            "External": ["User", "External"],
            "Frontend": ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"],
            "Application": ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"],
            "Data": ["Amazon S3", "Amazon EBS", "Amazon EFS", "Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"],
            "Analytics": ["Amazon Kinesis", "AWS Glue", "Amazon Redshift", "Amazon OpenSearch"],
            "AI/ML": ["Amazon Bedrock", "Amazon SageMaker"],
            "Security": ["AWS WAF", "Amazon GuardDuty", "AWS Shield"],
            "Integration": ["AWS Step Functions", "Amazon EventBridge", "Amazon SNS", "Amazon SQS"]
        }
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: 'Amazon Ember', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .architecture-container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h2 {
            color: #232f3e;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 14px;
        }
        .layer {
            margin: 25px 0;
            padding: 20px;
            border-radius: 10px;
            background: #f8f9fa;
            border-left: 5px solid;
            position: relative;
        }
        .layer-title {
            font-weight: bold;
            margin-bottom: 15px;
            color: #232f3e;
            font-size: 18px;
            display: flex;
            align-items: center;
        }
        .layer-title::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 10px;
            display: inline-block;
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }
        .service-card {
            background: white;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            padding: 20px 15px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            border-color: #FF9900;
        }
        .service-icon {
            width: 56px;
            height: 56px;
            margin: 0 auto 12px;
            display: block;
        }
        .service-name {
            font-weight: 600;
            margin-bottom: 6px;
            color: #232f3e;
            font-size: 14px;
        }
        .service-config {
            font-size: 11px;
            color: #666;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid #e1e4e8;
        }
        .connections-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .connections-info h3 {
            color: #856404;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .connection-item {
            display: inline-block;
            background: white;
            padding: 8px 12px;
            margin: 5px;
            border-radius: 20px;
            font-size: 12px;
            border: 1px solid #ffeaa7;
        }
        .arrow {
            color: #FF9900;
            font-weight: bold;
            margin: 0 5px;
        }
        
        /* Layer-specific colors */
        .External { border-left-color: #6B7280; }
        .External .layer-title::before { background: #6B7280; }
        
        .Frontend { border-left-color: #EC7211; }
        .Frontend .layer-title::before { background: #EC7211; }
        
        .Application { border-left-color: #FF9900; }
        .Application .layer-title::before { background: #FF9900; }
        
        .Data { border-left-color: #3B48CC; }
        .Data .layer-title::before { background: #3B48CC; }
        
        .Analytics { border-left-color: #8C4FFF; }
        .Analytics .layer-title::before { background: #8C4FFF; }
        
        .AIML { border-left-color: #01A88D; }
        .AIML .layer-title::before { background: #01A88D; }
        
        .Security { border-left-color: #DD344C; }
        .Security .layer-title::before { background: #DD344C; }
        
        .Integration { border-left-color: #C925D1; }
        .Integration .layer-title::before { background: #C925D1; }
    </style>
</head>
<body>
    <div class="architecture-container">
        <div class="header">
            <h2>🏗️ AWS Architecture Diagram</h2>
            <p>Professional architecture with embedded AWS service icons and intelligent connections</p>
        </div>
"""
        
        # Add layers
        for layer_name, layer_services in layers.items():
            services_in_layer = [s for s in all_services_with_external if s in layer_services]
            
            if services_in_layer:
                layer_class = layer_name.replace("/", "").replace(" ", "")
                html_content += f"""
        <div class="layer {layer_class}">
            <div class="layer-title">{layer_name} Layer</div>
            <div class="services-grid">
"""
                
                for service in services_in_layer:
                    config = configurations.get(service, {}).get('config', {})
                    icon_svg = ProfessionalArchitectureGenerator.get_service_icon_svg(service)
                    
                    # Build configuration text
                    config_text = ""
                    if service == "Amazon EC2" and config:
                        instance_type = config.get('instance_type', 't3.micro')
                        instance_count = config.get('instance_count', 1)
                        config_text = f"{instance_count}x {instance_type}"
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        config_text = f"{engine}<br/>{instance_type}"
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        config_text = f"{storage_gb}GB Storage"
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        config_text = f"{memory}MB Memory"
                    elif service == "Amazon ECS" and config:
                        cluster_type = config.get('cluster_type', 'Fargate')
                        config_text = f"{cluster_type}"
                    elif service == "Amazon EKS" and config:
                        node_count = config.get('node_count', 2)
                        config_text = f"{node_count} nodes"
                    elif service == "Amazon EFS" and config:
                        storage_gb = config.get('storage_gb', 100)
                        config_text = f"{storage_gb}GB"
                    elif service == "Amazon Bedrock" and config:
                        input_tokens = config.get('input_tokens_million', 10)
                        config_text = f"{input_tokens}M tokens"
                    elif service == "AWS Step Functions" and config:
                        state_machines = config.get('state_machines', 1)
                        config_text = f"{state_machines} workflows"
                    elif service == "Amazon EventBridge" and config:
                        event_buses = config.get('event_buses', 1)
                        config_text = f"{event_buses} event bus"
                    elif service == "Amazon SNS" and config:
                        topics = config.get('topics', 1)
                        config_text = f"{topics} topics"
                    elif service == "Amazon SQS" and config:
                        queues = config.get('queues', 1)
                        config_text = f"{queues} queues"
                    
                    display_name = service.replace("Amazon ", "").replace("AWS ", "")
                    
                    html_content += f"""
                <div class="service-card">
                    <div class="service-icon">{icon_svg}</div>
                    <div class="service-name">{display_name}</div>
                    <div class="service-config">{config_text}</div>
                </div>
"""
                
                html_content += """
            </div>
        </div>
"""
        
        # Add connections section
        if connections:
            html_content += """
        <div class="connections-info">
            <h3>📊 Service Connections & Data Flow</h3>
            <div>
"""
            for conn in connections:
                html_content += f"""
                <div class="connection-item">
                    {conn['from'].replace('Amazon ', '').replace('AWS ', '')}
                    <span class="arrow">→</span>
                    {conn['to'].replace('Amazon ', '').replace('AWS ', '')}
                    <span style="color: #666; font-size: 10px;">({conn['label']})</span>
                </div>
"""
            
            html_content += """
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        return html_content
    
    @staticmethod
    def generate_connections(selected_services: List[str]) -> List[Dict]:
        """Generate intelligent connections between services"""
        connections = []
        
        # User to frontend
        if "Amazon CloudFront" in selected_services:
            connections.append({"from": "User", "to": "Amazon CloudFront", "label": "HTTPS"})
        if "Elastic Load Balancing" in selected_services:
            connections.append({"from": "User", "to": "Elastic Load Balancing", "label": "API Requests"})
        if "Amazon API Gateway" in selected_services:
            connections.append({"from": "User", "to": "Amazon API Gateway", "label": "API Calls"})
        
        # Frontend to storage
        if "Amazon CloudFront" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "Amazon CloudFront", "to": "Amazon S3", "label": "Static Content"})
        
        # Load balancer to compute
        if "Elastic Load Balancing" in selected_services:
            for compute in ["Amazon EC2", "Amazon ECS", "Amazon EKS"]:
                if compute in selected_services:
                    connections.append({"from": "Elastic Load Balancing", "to": compute, "label": "Routes Traffic"})
        
        # API Gateway to compute
        if "Amazon API Gateway" in selected_services and "AWS Lambda" in selected_services:
            connections.append({"from": "Amazon API Gateway", "to": "AWS Lambda", "label": "Invokes"})
        
        # Compute to database
        compute_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        db_services = ["Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"]
        
        for compute in compute_services:
            if compute in selected_services:
                for db in db_services:
                    if db in selected_services:
                        connections.append({"from": compute, "to": db, "label": "Queries"})
        
        # Analytics pipeline
        if "Amazon Kinesis" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "External", "to": "Amazon Kinesis", "label": "Streams Data"})
            connections.append({"from": "Amazon Kinesis", "to": "Amazon S3", "label": "Stores"})
        
        if "AWS Glue" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "AWS Glue", "to": "Amazon S3", "label": "Processes"})
        
        if "Amazon OpenSearch" in selected_services:
            if "AWS Glue" in selected_services:
                connections.append({"from": "AWS Glue", "to": "Amazon OpenSearch", "label": "Loads"})
        
        # AI/ML connections
        if "Amazon Bedrock" in selected_services:
            for compute in compute_services:
                if compute in selected_services:
                    connections.append({"from": compute, "to": "Amazon Bedrock", "label": "Invokes AI"})
        
        # Step Functions
        if "AWS Step Functions" in selected_services and "AWS Lambda" in selected_services:
            connections.append({"from": "AWS Step Functions", "to": "AWS Lambda", "label": "Orchestrates"})
        
        if "Amazon EventBridge" in selected_services and "AWS Step Functions" in selected_services:
            connections.append({"from": "Amazon EventBridge", "to": "AWS Step Functions", "label": "Triggers"})
        
        # Security
        if "AWS WAF" in selected_services:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]:
                if frontend in selected_services:
                    connections.append({"from": "AWS WAF", "to": frontend, "label": "Protects"})
        
        return connections

    @staticmethod
    def generate_mermaid_diagram(selected_services: Dict, configurations: Dict) -> str:
        """Generate Mermaid.js diagram code"""
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Add external nodes
        all_services_with_external = ["User", "External"] + all_services
        
        # Generate connections
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        
        mermaid_code = "graph TB\n"
        
        # Define node styles
        mermaid_code += "    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n"
        mermaid_code += "    classDef frontend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n"
        mermaid_code += "    classDef application fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n"
        mermaid_code += "    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px\n"
        mermaid_code += "    classDef security fill:#ffebee,stroke:#c62828,stroke-width:2px\n"
        mermaid_code += "    classDef integration fill:#fce4ec,stroke:#ad1457,stroke-width:2px\n"
        
        # Add nodes
        node_ids = {}
        for service in all_services_with_external:
            node_id = service.replace(" ", "").replace("Amazon", "").replace("AWS", "")
            node_ids[service] = node_id
            
            config = configurations.get(service, {}).get('config', {})
            config_text = ""
            
            if service == "Amazon EC2" and config:
                instance_type = config.get('instance_type', 't3.micro')
                instance_count = config.get('instance_count', 1)
                config_text = f"\\n({instance_count}x {instance_type})"
            elif service == "Amazon RDS" and config:
                engine = config.get('engine', 'PostgreSQL')
                config_text = f"\\n({engine})"
            elif service == "Amazon S3" and config:
                storage_gb = config.get('storage_gb', 100)
                config_text = f"\\n({storage_gb}GB)"
            
            display_name = service.replace("Amazon ", "").replace("AWS ", "")
            mermaid_code += f'    {node_id}["{display_name}{config_text}"]\n'
        
        # Add connections
        for conn in connections:
            from_id = node_ids.get(conn['from'], conn['from'].replace(" ", ""))
            to_id = node_ids.get(conn['to'], conn['to'].replace(" ", ""))
            mermaid_code += f'    {from_id} -->|{conn["label"]}| {to_id}\n'
        
        # Apply styling
        external_services = ["User", "External"]
        frontend_services = ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]
        application_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        data_services = ["Amazon S3", "Amazon EBS", "Amazon EFS", "Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"]
        security_services = ["AWS WAF", "Amazon GuardDuty", "AWS Shield"]
        integration_services = ["AWS Step Functions", "Amazon EventBridge", "Amazon SNS", "Amazon SQS"]
        
        for service in all_services_with_external:
            node_id = node_ids[service]
            if service in external_services:
                mermaid_code += f'    class {node_id} external\n'
            elif service in frontend_services:
                mermaid_code += f'    class {node_id} frontend\n'
            elif service in application_services:
                mermaid_code += f'    class {node_id} application\n'
            elif service in data_services:
                mermaid_code += f'    class {node_id} data\n'
            elif service in security_services:
                mermaid_code += f'    class {node_id} security\n'
            elif service in integration_services:
                mermaid_code += f'    class {node_id} integration\n'
        
        return mermaid_code

    @staticmethod
    def generate_graphviz_diagram(selected_services: Dict, configurations: Dict):
        """Generate Graphviz diagram"""
        dot = graphviz.Digraph(comment='AWS Architecture')
        dot.attr(rankdir='TB', size='12,12')
        
        # Define styles
        dot.attr('node', shape='rectangle', style='filled', fontname='Arial')
        dot.attr('edge', color='gray50', fontname='Arial', fontsize='10')
        
        # Add clusters for organization
        with dot.subgraph(name='cluster_external') as c:
            c.attr(label='External', style='filled', fillcolor='lightblue', color='black')
            c.node('User', 'User', fillcolor='#e1f5fe')
            c.node('External', 'External Systems', fillcolor='#e1f5fe')
        
        # Add services by category
        for category, services in selected_services.items():
            if services:
                with dot.subgraph(name=f'cluster_{category.lower()}') as c:
                    c.attr(label=category, style='filled', fillcolor='lightgray', color='black')
                    
                    for service in services:
                        config = configurations.get(service, {}).get('config', {})
                        label = f"{service}\\n{ProfessionalArchitectureGenerator._get_config_summary(service, config)}"
                        
                        # Color coding based on service type
                        if "EC2" in service or "Lambda" in service or "ECS" in service or "EKS" in service:
                            fillcolor = '#e8f5e8'  # Green for compute
                        elif "S3" in service or "EBS" in service or "EFS" in service:
                            fillcolor = '#fff3e0'  # Orange for storage
                        elif "RDS" in service or "DynamoDB" in service:
                            fillcolor = '#e3f2fd'  # Blue for database
                        else:
                            fillcolor = '#f3e5f5'  # Purple for others
                        
                        c.node(service, label, fillcolor=fillcolor)
        
        # Add connections
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        all_services_with_external =        
        
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        all_services_with_external = ["User", "External"] + all_services
        
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        
        for conn in connections:
            dot.edge(conn['from'], conn['to'], label=conn['label'])
        
        return dot

    @staticmethod
    def _get_config_summary(service: str, config: Dict) -> str:
        """Get configuration summary for service labels"""
        if service == "Amazon EC2" and config:
            instance_type = config.get('instance_type', 't3.micro')
            instance_count = config.get('instance_count', 1)
            return f"{instance_count}x {instance_type}"
        elif service == "Amazon RDS" and config:
            instance_type = config.get('instance_type', 'db.t3.micro')
            engine = config.get('engine', 'PostgreSQL')
            return f"{engine}\\n{instance_type}"
        elif service == "Amazon S3" and config:
            storage_gb = config.get('storage_gb', 100)
            return f"{storage_gb}GB"
        elif service == "AWS Lambda" and config:
            memory = config.get('memory_mb', 128)
            return f"{memory}MB"
        elif service == "Amazon ECS" and config:
            cluster_type = config.get('cluster_type', 'Fargate')
            return f"{cluster_type}"
        return ""

def render_service_configuration(service_name: str):
    """Render configuration UI for each service"""
    st.subheader(f"⚙️ {service_name} Configuration")
    
    if service_name == "Amazon EC2":
        col1, col2 = st.columns(2)
        with col1:
            instance_type = st.selectbox(
                "Instance Type",
                ["t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", 
                 "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge",
                 "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge"],
                key=f"ec2_instance_type_{service_name}"
            )
        with col2:
            instance_count = st.number_input("Instance Count", min_value=1, max_value=100, value=1, key=f"ec2_count_{service_name}")
        
        col3, col4 = st.columns(2)
        with col3:
            operating_hours = st.selectbox(
                "Operating Hours",
                ["24/7", "Business Hours", "Custom"],
                key=f"ec2_hours_{service_name}"
            )
        with col4:
            if operating_hours == "Custom":
                daily_hours = st.number_input("Hours per Day", min_value=1, max_value=24, value=8, key=f"ec2_custom_hours_{service_name}")
            else:
                daily_hours = 24 if operating_hours == "24/7" else 12
        
        return {
            "instance_type": instance_type,
            "instance_count": instance_count,
            "operating_hours": operating_hours,
            "daily_hours": daily_hours
        }
    
    elif service_name == "Amazon RDS":
        col1, col2 = st.columns(2)
        with col1:
            instance_type = st.selectbox(
                "Instance Type",
                ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
                 "db.m5.large", "db.m5.xlarge", "db.m5.2xlarge", "db.m5.4xlarge",
                 "db.r5.large", "db.r5.xlarge", "db.r5.2xlarge", "db.r5.4xlarge"],
                key=f"rds_instance_type_{service_name}"
            )
        with col2:
            engine = st.selectbox(
                "Database Engine",
                ["PostgreSQL", "MySQL", "MariaDB", "Aurora MySQL", "Aurora PostgreSQL", "Oracle", "SQL Server"],
                key=f"rds_engine_{service_name}"
            )
        
        storage_gb = st.number_input("Storage (GB)", min_value=20, max_value=10000, value=100, key=f"rds_storage_{service_name}")
        
        return {
            "instance_type": instance_type,
            "engine": engine,
            "storage_gb": storage_gb
        }
    
    elif service_name == "Amazon S3":
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=100000, value=100, key=f"s3_storage_{service_name}")
        
        storage_class = st.selectbox(
            "Storage Class",
            ["Standard", "Intelligent-Tiering", "Standard-IA", "One Zone-IA", "Glacier", "Glacier Deep Archive"],
            key=f"s3_class_{service_name}"
        )
        
        data_transfer_gb = st.number_input("Monthly Data Transfer (GB)", min_value=0, max_value=10000, value=100, key=f"s3_transfer_{service_name}")
        
        return {
            "storage_gb": storage_gb,
            "storage_class": storage_class,
            "data_transfer_gb": data_transfer_gb
        }
    
    elif service_name == "AWS Lambda":
        col1, col2 = st.columns(2)
        with col1:
            memory_mb = st.selectbox(
                "Memory (MB)",
                [128, 256, 512, 1024, 2048, 3008],
                index=0,
                key=f"lambda_memory_{service_name}"
            )
        with col2:
            duration_ms = st.number_input("Average Duration (ms)", min_value=100, max_value=30000, value=1000, key=f"lambda_duration_{service_name}")
        
        monthly_requests = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"lambda_requests_{service_name}")
        
        return {
            "memory_mb": memory_mb,
            "duration_ms": duration_ms,
            "monthly_requests": monthly_requests
        }
    
    elif service_name == "Amazon ECS":
        cluster_type = st.selectbox(
            "Cluster Type",
            ["Fargate", "EC2"],
            key=f"ecs_type_{service_name}"
        )
        
        if cluster_type == "Fargate":
            col1, col2 = st.columns(2)
            with col1:
                cpu_units = st.selectbox("CPU Units", ["0.25 vCPU", "0.5 vCPU", "1 vCPU", "2 vCPU", "4 vCPU"], key=f"ecs_cpu_{service_name}")
            with col2:
                memory_gb = st.selectbox("Memory (GB)", ["0.5GB", "1GB", "2GB", "4GB", "8GB", "16GB"], key=f"ecs_memory_{service_name}")
            
            task_count = st.number_input("Number of Tasks", min_value=1, max_value=100, value=2, key=f"ecs_tasks_{service_name}")
            
            return {
                "cluster_type": cluster_type,
                "cpu_units": cpu_units,
                "memory_gb": memory_gb,
                "task_count": task_count
            }
        else:
            # EC2 cluster configuration
            instance_type = st.selectbox(
                "Instance Type",
                ["t3.micro", "t3.small", "t3.medium", "m5.large", "m5.xlarge"],
                key=f"ecs_ec2_instance_{service_name}"
            )
            instance_count = st.number_input("Instance Count", min_value=1, max_value=20, value=2, key=f"ecs_ec2_count_{service_name}")
            
            return {
                "cluster_type": cluster_type,
                "instance_type": instance_type,
                "instance_count": instance_count
            }
    
    elif service_name == "Amazon EKS":
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=50, value=3, key=f"eks_nodes_{service_name}")
        
        node_type = st.selectbox(
            "Node Type",
            ["t3.medium", "t3.large", "m5.large", "m5.xlarge", "m5.2xlarge"],
            key=f"eks_node_type_{service_name}"
        )
        
        return {
            "node_count": node_count,
            "node_type": node_type
        }
    
    elif service_name == "Amazon EBS":
        volume_type = st.selectbox(
            "Volume Type",
            ["gp3", "gp2", "io1", "io2", "st1", "sc1"],
            key=f"ebs_type_{service_name}"
        )
        
        volume_size_gb = st.number_input("Volume Size (GB)", min_value=1, max_value=10000, value=100, key=f"ebs_size_{service_name}")
        
        if volume_type in ["io1", "io2"]:
            iops = st.number_input("IOPS", min_value=100, max_value=100000, value=3000, key=f"ebs_iops_{service_name}")
        else:
            iops = 0
        
        return {
            "volume_type": volume_type,
            "volume_size_gb": volume_size_gb,
            "iops": iops
        }
    
    elif service_name == "Amazon EFS":
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=100000, value=100, key=f"efs_storage_{service_name}")
        
        storage_class = st.selectbox(
            "Storage Class",
            ["Standard", "Infrequent Access"],
            key=f"efs_class_{service_name}"
        )
        
        return {
            "storage_gb": storage_gb,
            "storage_class": storage_class
        }
    
    elif service_name == "Amazon DynamoDB":
        capacity_mode = st.selectbox(
            "Capacity Mode",
            ["Provisioned", "On-Demand"],
            key=f"dynamo_capacity_{service_name}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            read_units = st.number_input("Read Capacity Units", min_value=1, max_value=100000, value=10, key=f"dynamo_read_{service_name}")
        with col2:
            write_units = st.number_input("Write Capacity Units", min_value=1, max_value=100000, value=10, key=f"dynamo_write_{service_name}")
        
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=10000, value=100, key=f"dynamo_storage_{service_name}")
        
        return {
            "capacity_mode": capacity_mode,
            "read_units": read_units,
            "write_units": write_units,
            "storage_gb": storage_gb
        }
    
    elif service_name == "Amazon ElastiCache":
        node_type = st.selectbox(
            "Node Type",
            ["cache.t3.micro", "cache.t3.small", "cache.t3.medium", "cache.t3.large",
             "cache.m5.large", "cache.m5.xlarge", "cache.m5.2xlarge",
             "cache.r5.large", "cache.r5.xlarge", "cache.r5.2xlarge"],
            key=f"cache_node_type_{service_name}"
        )
        
        engine = st.selectbox(
            "Engine",
            ["Redis", "Memcached"],
            key=f"cache_engine_{service_name}"
        )
        
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=10, value=2, key=f"cache_nodes_{service_name}")
        
        return {
            "node_type": node_type,
            "engine": engine,
            "node_count": node_count
        }
    
    elif service_name == "Amazon CloudFront":
        data_transfer_tb = st.number_input("Monthly Data Transfer (TB)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1, key=f"cf_transfer_{service_name}")
        
        requests_million = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"cf_requests_{service_name}")
        
        return {
            "data_transfer_tb": data_transfer_tb,
            "requests_million": requests_million
        }
    
    elif service_name == "Elastic Load Balancing":
        load_balancer_type = st.selectbox(
            "Load Balancer Type",
            ["Application", "Network", "Gateway"],
            key=f"elb_type_{service_name}"
        )
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=1000.0, value=5.0, step=0.1, key=f"elb_data_{service_name}")
        
        return {
            "load_balancer_type": load_balancer_type,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "Amazon API Gateway":
        api_type = st.selectbox(
            "API Type",
            ["REST API", "HTTP API"],
            key=f"api_type_{service_name}"
        )
        
        requests_million = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1, key=f"api_requests_{service_name}")
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=100.0, value=0.5, step=0.1, key=f"api_data_{service_name}")
        
        return {
            "api_type": api_type,
            "requests_million": requests_million,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "Amazon Kinesis":
        shard_hours = st.number_input("Shard Hours (per month)", min_value=1, max_value=100000, value=720, key=f"kinesis_shards_{service_name}")
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"kinesis_data_{service_name}")
        
        return {
            "shard_hours": shard_hours,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "AWS Glue":
        dpu_hours = st.number_input("DPU Hours (per month)", min_value=1, max_value=10000, value=100, key=f"glue_dpu_{service_name}")
        
        return {
            "dpu_hours": dpu_hours
        }
    
    elif service_name == "Amazon Redshift":
        node_type = st.selectbox(
            "Node Type",
            ["ra3.4xlarge", "ra3.16xlarge", "dc2.large", "dc2.8xlarge", "ds2.xlarge", "ds2.8xlarge"],
            key=f"redshift_node_type_{service_name}"
        )
        
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=100, value=2, key=f"redshift_nodes_{service_name}")
        
        return {
            "node_type": node_type,
            "node_count": node_count
        }
    
    elif service_name == "Amazon Bedrock":
        input_tokens_million = st.number_input("Input Tokens (millions per month)", min_value=1, max_value=1000, value=10, key=f"bedrock_input_{service_name}")
        
        output_tokens_million = st.number_input("Output Tokens (millions per month)", min_value=1, max_value=1000, value=5, key=f"bedrock_output_{service_name}")
        
        return {
            "input_tokens_million": input_tokens_million,
            "output_tokens_million": output_tokens_million
        }
    
    elif service_name == "Amazon SageMaker":
        instance_type = st.selectbox(
            "Instance Type",
            ["ml.t3.medium", "ml.t3.large", "ml.t3.xlarge",
             "ml.m5.large", "ml.m5.xlarge", "ml.m5.2xlarge", "ml.m5.4xlarge",
             "ml.c5.large", "ml.c5.xlarge", "ml.c5.2xlarge", "ml.c5.4xlarge",
             "ml.p3.2xlarge", "ml.p3.8xlarge", "ml.p3.16xlarge"],
            key=f"sagemaker_instance_{service_name}"
        )
        
        hours_per_month = st.number_input("Hours per Month", min_value=1, max_value=744, value=168, key=f"sagemaker_hours_{service_name}")
        
        return {
            "instance_type": instance_type,
            "hours_per_month": hours_per_month
        }
    
    elif service_name == "AWS Step Functions":
        state_machines = st.number_input("Number of State Machines", min_value=1, max_value=100, value=1, key=f"stepfunctions_machines_{service_name}")
        
        state_transitions_million = st.number_input("State Transitions (millions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"stepfunctions_transitions_{service_name}")
        
        return {
            "state_machines": state_machines,
            "state_transitions_million": state_transitions_million
        }
    
    elif service_name == "Amazon EventBridge":
        event_buses = st.number_input("Number of Event Buses", min_value=1, max_value=10, value=1, key=f"eventbridge_buses_{service_name}")
        
        events_million = st.number_input("Events (millions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"eventbridge_events_{service_name}")
        
        return {
            "event_buses": event_buses,
            "events_million": events_million
        }
    
    elif service_name == "Amazon SNS":
        topics = st.number_input("Number of Topics", min_value=1, max_value=100, value=1, key=f"sns_topics_{service_name}")
        
        notifications_million = st.number_input("Notifications (millions per month)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"sns_notifications_{service_name}")
        
        return {
            "topics": topics,
            "notifications_million": notifications_million
        }
    
    elif service_name == "Amazon SQS":
        queues = st.number_input("Number of Queues", min_value=1, max_value=100, value=1, key=f"sqs_queues_{service_name}")
        
        requests_million = st.number_input("Requests (millions per month)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"sqs_requests_{service_name}")
        
        return {
            "queues": queues,
            "requests_million": requests_million
        }
    
    elif service_name == "AWS WAF":
        web_acls = st.number_input("Number of Web ACLs", min_value=1, max_value=10, value=1, key=f"waf_acls_{service_name}")
        
        requests_billion = st.number_input("Requests (billions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"waf_requests_{service_name}")
        
        return {
            "web_acls": web_acls,
            "requests_billion": requests_billion
        }
    
    elif service_name == "Amazon GuardDuty":
        data_sources = st.multiselect(
            "Data Sources",
            ["CloudTrail", "VPC Flow Logs", "DNS Logs"],
            default=["CloudTrail", "VPC Flow Logs"],
            key=f"guardduty_sources_{service_name}"
        )
        
        return {
            "data_sources": data_sources
        }
    
    elif service_name == "AWS Shield":
        protection_type = st.selectbox(
            "Protection Type",
            ["Standard", "Advanced"],
            key=f"shield_type_{service_name}"
        )
        
        return {
            "protection_type": protection_type
        }
    
    elif service_name == "Amazon OpenSearch":
        instance_type = st.selectbox(
            "Instance Type",
            ["t3.small.search", "t3.medium.search", "m5.large.search", "m5.xlarge.search", "r5.large.search", "r5.xlarge.search"],
            key=f"opensearch_instance_{service_name}"
        )
        
        instance_count = st.number_input("Instance Count", min_value=1, max_value=10, value=2, key=f"opensearch_count_{service_name}")
        
        storage_gb = st.number_input("Storage per Instance (GB)", min_value=10, max_value=1000, value=100, key=f"opensearch_storage_{service_name}")
        
        return {
            "instance_type": instance_type,
            "instance_count": instance_count,
            "storage_gb": storage_gb
        }
    
    else:
        # Default configuration for unsupported services
        st.info(f"Configuration for {service_name} will be available soon.")
        return {}

def calculate_service_cost(service_name: str, config: Dict, timeline_config: Dict) -> Dict:
    """Calculate cost for a specific service"""
    try:
        # Get base monthly cost
        if service_name == "Amazon EC2":
            hourly_price = AWSPricingAPI.get_ec2_pricing(config['instance_type'])
            monthly_hours = config['daily_hours'] * 30
            base_monthly_cost = hourly_price * config['instance_count'] * monthly_hours
        
        elif service_name == "Amazon RDS":
            hourly_price = AWSPricingAPI.get_rds_pricing(config['instance_type'], config['engine'])
            base_monthly_cost = hourly_price * 730  # 730 hours per month
            # Add storage cost
            storage_price = 0.115  # gp2 storage per GB-month
            base_monthly_cost += config['storage_gb'] * storage_price
        
        elif service_name == "Amazon S3":
            storage_price = AWSPricingAPI.get_s3_pricing(config['storage_class'])
            base_monthly_cost = config['storage_gb'] * storage_price
            # Add data transfer cost
            transfer_cost = config['data_transfer_gb'] * 0.09  # $0.09 per GB
            base_monthly_cost += transfer_cost
        
        elif service_name == "AWS Lambda":
            lambda_pricing = AWSPricingAPI.get_lambda_pricing()
            # Calculate compute cost
            compute_cost = (config['monthly_requests'] * 1000000) * (config['duration_ms'] / 1000) * (config['memory_mb'] / 1024) * lambda_pricing['compute_price']
            # Calculate request cost
            request_cost = (config['monthly_requests'] * 1000000) * lambda_pricing['request_price']
            base_monthly_cost = compute_cost + request_cost
        
        elif service_name == "Amazon ECS":
            if config['cluster_type'] == "Fargate":
                # Fargate pricing
                cpu_map = {"0.25 vCPU": 0.04048, "0.5 vCPU": 0.08096, "1 vCPU": 0.16192, "2 vCPU": 0.32384, "4 vCPU": 0.64768}
                memory_map = {"0.5GB": 0.004445, "1GB": 0.00889, "2GB": 0.01778, "4GB": 0.03556, "8GB": 0.07112, "16GB": 0.14224}
                
                cpu_cost = cpu_map.get(config['cpu_units'], 0.16192)
                memory_cost = memory_map.get(config['memory_gb'], 0.01778)
                hourly_price = cpu_cost + memory_cost
                base_monthly_cost = hourly_price * config['task_count'] * 730
            else:
                # EC2 pricing
                hourly_price = AWSPricingAPI.get_ec2_pricing(config['instance_type'])
                base_monthly_cost = hourly_price * config['instance_count'] * 730
        
        elif service_name == "Amazon EKS":
            # EKS cluster cost + node cost
            cluster_cost = 0.10 * 730  # $0.10 per hour
            node_hourly_cost = AWSPricingAPI.get_ec2_pricing(config['node_type'])
            nodes_cost = node_hourly_cost * config['node_count'] * 730
            base_monthly_cost = cluster_cost + nodes_cost
        
        elif service_name == "Amazon EBS":
            ebs_pricing = AWSPricingAPI.get_ebs_pricing(config['volume_type'])
            storage_cost = config['volume_size_gb'] * ebs_pricing['storage']
            iops_cost = config['iops'] * ebs_pricing['iops'] if ebs_pricing['iops'] > 0 else 0
            base_monthly_cost = storage_cost + iops_cost
        
        elif service_name == "Amazon EFS":
            storage_price = AWSPricingAPI.get_efs_pricing(config['storage_class'])
            base_monthly_cost = config['storage_gb'] * storage_price
        
        elif service_name == "Amazon DynamoDB":
            base_monthly_cost = AWSPricingAPI.get_dynamodb_pricing(
                config['capacity_mode'],
                config['read_units'],
                config['write_units'],
                config['storage_gb']
            )
        
        elif service_name == "Amazon ElastiCache":
            hourly_price = AWSPricingAPI.get_elasticache_pricing(config['node_type'], config['engine'])
            base_monthly_cost = hourly_price * config['node_count']
        
        elif service_name == "Amazon CloudFront":
            cf_pricing = AWSPricingAPI.get_cloudfront_pricing()
            data_cost = config['data_transfer_tb'] * 1000 * cf_pricing['data_transfer']  # Convert TB to GB
            request_cost = (config['requests_million'] * 10000) * cf_pricing['requests']  # Convert million to 10k units
            base_monthly_cost = data_cost + request_cost
        
        elif service_name == "Elastic Load Balancing":
            # Simplified ELB pricing
            if config['load_balancer_type'] == "Application":
                base_monthly_cost = 0.0225 * 730 + config['data_processed_tb'] * 1000 * 0.008  # $0.0225/hour + $0.008/GB
            elif config['load_balancer_type'] == "Network":
                base_monthly_cost = 0.0225 * 730 + config['data_processed_tb'] * 1000 * 0.006  # $0.0225/hour + $0.006/GB
            else:  # Gateway
                base_monthly_cost = 0.025 * 730 + config['data_processed_tb'] * 1000 * 0.005  # $0.025/hour + $0.005/GB
        
        elif service_name == "Amazon API Gateway":
            base_monthly_cost = AWSPricingAPI.get_api_gateway_pricing(
                config['api_type'],
                config['requests_million'],
                config['data_processed_tb']
            )
        
        elif service_name == "Amazon Kinesis":
            base_monthly_cost = AWSPricingAPI.get_kinesis_pricing(
                config['shard_hours'],
                config['data_processed_tb']
            )
        
        elif service_name == "AWS Glue":
            base_monthly_cost = AWSPricingAPI.get_glue_pricing(config['dpu_hours'])
        
        elif service_name == "Amazon Redshift":
            base_monthly_cost = AWSPricingAPI.get_redshift_pricing(
                config['node_type'],
                config['node_count']
            )
        
        elif service_name == "Amazon Bedrock":
            # Simplified Bedrock pricing (Claude Instant pricing)
            input_cost = config['input_tokens_million'] * 0.00080   # $0.80 per 1M tokens
            output_cost = config['output_tokens_million'] * 0.00240 # $2.40 per 1M tokens
            base_monthly_cost = input_cost + output_cost
        
        elif service_name == "Amazon SageMaker":
            base_monthly_cost = AWSPricingAPI.get_sagemaker_pricing(
                config['instance_type'],
                config['hours_per_month']
            )
        
        elif service_name == "AWS Step Functions":
            # $0.025 per 1000 state transitions
            base_monthly_cost = config['state_transitions_million'] * 1000000 * 0.000025
        
        elif service_name == "Amazon EventBridge":
            # $1.00 per million events
            base_monthly_cost = config['events_million'] * 1.00
        
        elif service_name == "Amazon SNS":
            base_monthly_cost = AWSPricingAPI.get_sns_pricing(config['notifications_million'])
        
        elif service_name == "Amazon SQS":
            base_monthly_cost = AWSPricingAPI.get_sqs_pricing(config['requests_million'])
        
        elif service_name == "AWS WAF":
            # $5 per web ACL per month + $1 per million requests
            base_monthly_cost = config['web_acls'] * 5 + config['requests_billion'] * 1000 * 1.00
        
        elif service_name == "Amazon GuardDuty":
            # $0.00150 per GB of CloudTrail events, $0.00300 per GB of VPC Flow Logs
            base_monthly_cost = 0
            if "CloudTrail" in config['data_sources']:
                base_monthly_cost += 100 * 0.00150  # Assuming 100GB of CloudTrail
            if "VPC Flow Logs" in config['data_sources']:
                base_monthly_cost += 500 * 0.00300  # Assuming 500GB of VPC Flow Logs
            if "DNS Logs" in config['data_sources']:
                base_monthly_cost += 50 * 0.00200   # Assuming 50GB of DNS Logs
        
        elif service_name == "AWS Shield":
            if config['protection_type'] == "Standard":
                base_monthly_cost = 0  # Free
            else:  # Advanced
                base_monthly_cost = 3000  # $3000 per month
        
        elif service_name == "Amazon OpenSearch":
            # Simplified pricing based on EC2 instance types
            instance_prices = {
                "t3.small.search": 0.036, "t3.medium.search": 0.074,
                "m5.large.search": 0.126, "m5.xlarge.search": 0.252,
                "r5.large.search": 0.167, "r5.xlarge.search": 0.334
            }
            hourly_price = instance_prices.get(config['instance_type'], 0.126)
            instance_cost = hourly_price * config['instance_count'] * 730
            storage_cost = config['storage_gb'] * config['instance_count'] * 0.10  # $0.10 per GB
            base_monthly_cost = instance_cost + storage_cost
        
        else:
            base_monthly_cost = 100  # Default cost for unsupported services
        
        # Apply commitment discount
        commitment_discount = 0
        if timeline_config['commitment_type'] == "1-year":
            commitment_discount = 0.20  # 20% discount
        elif timeline_config['commitment_type'] == "3-year":
            commitment_discount = 0.40  # 40% discount
        
        discounted_monthly_cost = base_monthly_cost * (1 - commitment_discount)
        
        # Calculate timeline costs with growth
        monthly_data = {
            'months': [],
            'monthly_costs': [],
            'cumulative_costs': []
        }
        
        total_months = timeline_config['total_months']
        current_cost = discounted_monthly_cost
        cumulative_cost = 0
        
        for month in range(1, total_months + 1):
            # Apply usage pattern
            if timeline_config['usage_pattern'] == "Growing":
                monthly_cost = current_cost * (1 + timeline_config['growth_rate']) ** (month - 1)
            elif timeline_config['usage_pattern'] == "Seasonal":
                # Seasonal pattern: peak every 6 months
                seasonal_factor = 1.5 if month % 6 == 0 else 0.8
                monthly_cost = current_cost * seasonal_factor
            else:  # Steady
                monthly_cost = current_cost
            
            cumulative_cost += monthly_cost
            
            monthly_data['months'].append(f"Month {month}")
            monthly_data['monthly_costs'].append(monthly_cost)
            monthly_data['cumulative_costs'].append(cumulative_cost)
        
        total_timeline_cost = cumulative_cost
        
        return {
            'base_monthly_cost': base_monthly_cost,
            'discounted_monthly_cost': discounted_monthly_cost,
            'total_timeline_cost': total_timeline_cost,
            'monthly_data': monthly_data,
            'commitment_discount': commitment_discount
        }
    
    except Exception as e:
        st.error(f"Error calculating cost for {service_name}: {str(e)}")
        return {
            'base_monthly_cost': 0,
            'discounted_monthly_cost': 0,
            'total_timeline_cost': 0,
            'monthly_data': {'months': [], 'monthly_costs': [], 'cumulative_costs': []},
            'commitment_discount': 0
        }

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AWS Architecture Cost Estimator",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #232f3e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        background: white;
    }
    .cost-highlight {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff9900;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">☁️ AWS Architecture Cost Estimator</h1>', unsafe_allow_html=True)
    
    # Sidebar for service selection
    with st.sidebar:
        st.header("🏗️ Architecture Setup")
        
        # Project requirements
        st.subheader("📋 Project Requirements")
        workload_type = st.selectbox(
            "Workload Type",
            ["Web Application", "Microservices", "Data Pipeline", "AI/ML", "IoT", "Enterprise", "Custom"]
        )
        
        estimated_users = st.selectbox(
            "Estimated Users",
            ["< 1,000", "1,000 - 10,000", "10,000 - 100,000", "100,000 - 1M", "> 1M"]
        )
        
        data_volume = st.selectbox(
            "Data Volume",
            ["Low (< 100GB)", "Medium (100GB - 1TB)", "High (1TB - 10TB)", "Very High (> 10TB)"]
        )
        
        # Service selection
        st.subheader("🔧 AWS Services")
        selected_services = {}
        
        for category, services in AWS_SERVICES.items():
            with st.expander(f"{category} ({len(services)} services)"):
                for service, description in services.items():
                    if st.checkbox(f"{service}", key=f"service_{service}", help=description):
                        if category not in selected_services:
                            selected_services[category] = []
                        selected_services[category].append(service)
        
        # Timeline configuration
        st.subheader("📅 Timeline & Commitment")
        timeline_type = st.selectbox(
            "Timeline Period",
            ["3 months", "6 months", "1 year", "2 years", "3 years", "5 years"]
        )
        
        # Map timeline to months
        timeline_map = {
            "3 months": 3, "6 months": 6, "1 year": 12, 
            "2 years": 24, "3 years": 36, "5 years": 60
        }
        total_months = timeline_map[timeline_type]
        
        usage_pattern = st.selectbox(
            "Usage Pattern",
            ["Steady", "Growing", "Seasonal"]
        )
        
        growth_rate = 0.0
        if usage_pattern == "Growing":
            growth_rate = st.slider("Monthly Growth Rate (%)", 1, 20, 5) / 100.0
        
        commitment_type = st.selectbox(
            "Commitment Type",
            ["On-Demand", "1-year", "3-year"]
        )
        
        timeline_config = {
            'timeline_type': timeline_type,
            'total_months': total_months,
            'usage_pattern': usage_pattern,
            'growth_rate': growth_rate,
            'commitment_type': commitment_type
        }
        
        # Store in session state
        st.session_state.selected_services = selected_services
        st.session_state.timeline_config = timeline_config
    
    # Main content area
    if not st.session_state.selected_services:
        st.info("👈 Select AWS services from the sidebar to get started!")
        return
    
    # Service configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Service Configuration", "💰 Cost Analysis", "🏗️ Architecture Diagram", "📊 Export Results"])
    
    with tab1:
        st.header("Service Configuration")
        
        # Store configurations
        configurations = {}
        
        for category, services in st.session_state.selected_services.items():
            st.subheader(f"{category} Services")
            
            for service in services:
                with st.expander(f"⚙️ {service}", expanded=True):
                    config = render_service_configuration(service)
                    if config:
                        configurations[service] = {
                            'config': config,
                            'category': category
                        }
        
        st.session_state.configurations = configurations
    
    with tab2:
        st.header("Cost Analysis")
        
        if not st.session_state.configurations:
            st.warning("Please configure the services in the Service Configuration tab first.")
        else:
            # Calculate costs
            total_cost = 0
            cost_breakdown = {}
            
            with st.spinner("Calculating costs..."):
                for service, service_data in st.session_state.configurations.items():
                    config = service_data['config']
                    pricing = calculate_service_cost(service, config, st.session_state.timeline_config)
                    
                    cost_breakdown[service] = {
                        'pricing': pricing,
                        'config': config,
                        'category': service_data['category']
                    }
                    total_cost += pricing['total_timeline_cost']
            
            st.session_state.cost_breakdown = cost_breakdown
            st.session_state.total_cost = total_cost
            
            # Display cost summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                monthly_cost = sum([data['pricing']['discounted_monthly_cost'] for data in cost_breakdown.values()])
                st.metric("Estimated Monthly Cost", f"${monthly_cost:,.2f}")
            
            with col2:
                st.metric("Total Timeline Cost", f"${total_cost:,.2f}")
            
            with col3:
                avg_monthly = total_cost / st.session_state.timeline_config['total_months']
                st.metric("Average Monthly Cost", f"${avg_monthly:,.2f}")
            
            # Cost breakdown by service
            st.subheader("Cost Breakdown by Service")
            cost_data = []
            for service, data in cost_breakdown.items():
                cost_data.append({
                    'Service': service,
                    'Category': data['category'],
                    'Monthly Cost': data['pricing']['discounted_monthly_cost'],
                    'Total Cost': data['pricing']['total_timeline_cost'],
                    'Discount': f"{data['pricing']['commitment_discount']*100:.0f}%"
                })
            
            if cost_data:
                cost_df = pd.DataFrame(cost_data)
                st.dataframe(cost_df, use_container_width=True)
                
                # Chart
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly cost by service
                    monthly_chart_data = pd.DataFrame({
                        'Service': [d['Service'] for d in cost_data],
                        'Monthly Cost': [d['Monthly Cost'] for d in cost_data]
                    })
                    st.bar_chart(monthly_chart_data.set_index('Service'))
                
                with col2:
                    # Cost by category
                    category_costs = {}
                    for data in cost_data:
                        category = data['Category']
                        if category not in category_costs:
                            category_costs[category] = 0
                        category_costs[category] += data['Monthly Cost']
                    
                    category_df = pd.DataFrame({
                        'Category': list(category_costs.keys()),
                        'Cost': list(category_costs.values())
                    })
                    st.bar_chart(category_df.set_index('Category'))
            
            # Monthly cost projection
            st.subheader("Monthly Cost Projection")
            if cost_breakdown:
                first_service = list(cost_breakdown.keys())[0]
                monthly_data = cost_breakdown[first_service]['pricing']['monthly_data']
                
                projection_df = pd.DataFrame({
                    'Month': monthly_data['months'],
                    'Monthly Cost': monthly_data['monthly_costs'],
                    'Cumulative Cost': monthly_data['cumulative_costs']
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    st.line_chart(projection_df.set_index('Month')['Monthly Cost'])
                with col2:
                    st.area_chart(projection_df.set_index('Month')['Cumulative Cost'])
    
    with tab3:
        st.header("Architecture Diagram")
        
        if not st.session_state.selected_services:
            st.warning("Please select services first.")
        else:
            # Diagram type selection
            col1, col2 = st.columns([3, 1])
            
            with col2:
                diagram_type = st.selectbox(
                    "Diagram Type",
                    ["Professional HTML", "Mermaid", "Graphviz"]
                )
            
            with col1:
                st.info("💡 The architecture diagram shows how your selected AWS services connect and work together.")
            
            # Generate diagram
            if diagram_type == "Professional HTML":
                html_diagram = ProfessionalArchitectureGenerator.generate_professional_diagram_html(
                    st.session_state.selected_services,
                    st.session_state.configurations,
                    {}
                )
                components.html(html_diagram, height=800, scrolling=True)
            
            elif diagram_type == "Mermaid":
                mermaid_code = ProfessionalArchitectureGenerator.generate_mermaid_diagram(
                    st.session_state.selected_services,
                    st.session_state.configurations
                )
                st.code(mermaid_code, language="mermaid")
                
                # Try to render with mermaid component
                try:
                    components.html(f"""
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad:true}});</script>
                    <div class="mermaid">
                    {mermaid_code}
                    </div>
                    """, height=600)
                except:
                    st.warning("Mermaid diagram rendering not available in this environment.")
            
            elif diagram_type == "Graphviz":
                dot = ProfessionalArchitectureGenerator.generate_graphviz_diagram(
                    st.session_state.selected_services,
                    st.session_state.configurations
                )
                st.graphviz_chart(dot)
    
    with tab4:
        st.header("Export Results")
        
        if not st.session_state.get('cost_breakdown'):
            st.warning("Please generate cost analysis first.")
        else:
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Excel Export
                if st.button("📊 Export to Excel"):
                    excel_data = ExportManager.export_to_excel(
                        st.session_state.cost_breakdown,
                        st.session_state.total_cost,
                        st.session_state.timeline_config
                    )
                    
                    st.download_button(
                        label="⬇️ Download Excel File",
                        data=excel_data,
                        file_name=f"aws_cost_estimate_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col2:
                # PDF Export
                if st.button("📄 Export to PDF"):
                    pdf_data = ExportManager.export_to_pdf(
                        st.session_state.cost_breakdown,
                        st.session_state.total_cost,
                        st.session_state.timeline_config
                    )
                    
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name=f"aws_cost_estimate_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
            
            # Summary report
            st.subheader("Summary Report")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("**Timeline Configuration**")
                st.write(f"**Period:** {st.session_state.timeline_config['timeline_type']}")
                st.write(f"**Usage Pattern:** {st.session_state.timeline_config['usage_pattern']}")
                st.write(f"**Commitment:** {st.session_state.timeline_config['commitment_type']}")
                if st.session_state.timeline_config['usage_pattern'] == "Growing":
                    st.write(f"**Growth Rate:** {st.session_state.timeline_config['growth_rate']*100:.1f}%")
            
            with col2:
                st.info("**Cost Summary**")
                monthly_cost = sum([data['pricing']['discounted_monthly_cost'] for data in st.session_state.cost_breakdown.values()])
                st.write(f"**Monthly Cost:** ${monthly_cost:,.2f}")
                st.write(f"**Total Cost:** ${st.session_state.total_cost:,.2f}")
                st.write(f"**Services:** {len(st.session_state.cost_breakdown)}")
            
            # Recommendations
            st.subheader("💡 Cost Optimization Recommendations")
            
            recommendations = []
            
            # Check for potential optimizations
            for service, data in st.session_state.cost_breakdown.items():
                config = data['config']
                pricing = data['pricing']
                
                if service == "Amazon EC2":
                    if config['instance_type'].startswith('t3') and pricing['discounted_monthly_cost'] > 100:
                        recommendations.append(f"Consider upgrading {service} from {config['instance_type']} to a larger instance type for better performance/cost ratio")
                
                elif service == "Amazon RDS":
                    if config['engine'] in ['Oracle', 'SQL Server'] and pricing['discounted_monthly_cost'] > 500:
                        recommendations.append(f"Consider migrating {service} from {config['engine']} to PostgreSQL or MySQL for significant cost savings")
                
                elif service == "Amazon S3":
                    if config['storage_class'] == 'Standard' and config['storage_gb'] > 1000:
                        recommendations.append(f"Consider moving infrequently accessed data in {service} to S3 Intelligent-Tiering for automatic cost optimization")
            
            if not recommendations:
                st.success("✅ Your architecture appears to be well-optimized! No major cost-saving recommendations at this time.")
            else:
                for rec in recommendations:
                    st.warning(rec)

if __name__ == "__main__":
    main()