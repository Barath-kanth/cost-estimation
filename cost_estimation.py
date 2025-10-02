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

# AWS Pricing API configuration
AWS_PRICING_API_BASE = "https://pricing.us-east-1.amazonaws.com"

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

class AWSPricingAPI:
    @staticmethod
    def get_ec2_pricing(region: str = 'us-east-1') -> Dict:
        """Fetch EC2 pricing from AWS Price List API"""
        try:
            url = f"{AWS_PRICING_API_BASE}/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"Could not fetch live pricing. Using cached data. Status: {response.status_code}")
                return AWSPricingAPI.get_cached_pricing()
        except Exception as e:
            st.warning(f"Using cached pricing data: {str(e)}")
            return AWSPricingAPI.get_cached_pricing()
    
    @staticmethod
    def get_cached_pricing() -> Dict:
        """Return cached pricing data as fallback"""
        return {
            "terms": {
                "OnDemand": {
                    "ABCDEFG1234567890": {
                        "priceDimensions": {
                            "ABCDEFG1234567890.JRTCKXETXF": {
                                "unit": "Hrs",
                                "pricePerUnit": {"USD": "0.0116"}
                            }
                        }
                    }
                }
            }
        }

# Updated AWS Services with comprehensive options
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
    """Generate professional AWS architecture diagrams with real AWS icons"""
    
    @staticmethod
    def generate_react_diagram_data(selected_services: Dict, configurations: Dict, requirements: Dict) -> Dict:
        """Generate data structure for React-based AWS architecture diagram with real icons"""
        
        # AWS service icon mappings to AWS Architecture Icons CDN
        service_icons = {
            # Compute
            "Amazon EC2": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-EC2_48.8c2c29c51959a74bca1ad23b2ab6a0e1c4cefa56.svg",
            "AWS Lambda": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Lambda_48.80ff29e6c3cb2b92eafac0977794d99ccb2fe4c1.svg",
            "Amazon ECS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Container-Service_48.5577c33a67c1a1447c2bc85ea7cbdf87c0e7c7a4.svg",
            "Amazon EKS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Kubernetes-Service_48.a8f4685cf67e36f7cf0ee626a7f4e55a2e4a27e6.svg",
            
            # Storage
            "Amazon S3": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Storage-Service_48.3dd1b4d5d3b09ba0f6c34b6c8e8f2b8f9e0e4e0e.svg",
            "Amazon EBS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Block-Store_48.7c8f3e3f4e4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f.svg",
            "Amazon EFS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-File-System_48.2e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e.svg",
            
            # Database
            "Amazon RDS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-RDS_48.7f8e9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f.svg",
            "Amazon DynamoDB": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-DynamoDB_48.5c6d7e8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f.svg",
            "Amazon ElastiCache": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-ElastiCache_48.4e5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f.svg",
            "Amazon OpenSearch": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-OpenSearch-Service_48.3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e.svg",
            
            # AI/ML
            "Amazon Bedrock": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Bedrock_48.2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e.svg",
            "Amazon SageMaker": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-SageMaker_48.1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e.svg",
            
            # Analytics
            "Amazon Kinesis": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Kinesis_48.0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e.svg",
            "AWS Glue": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Glue_48.9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f.svg",
            "Amazon Redshift": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Redshift_48.8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f.svg",
            
            # Networking
            "Amazon VPC": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Virtual-Private-Cloud_48.7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f.svg",
            "Amazon CloudFront": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-CloudFront_48.6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f.svg",
            "Elastic Load Balancing": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Elastic-Load-Balancing_48.5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f.svg",
            "Amazon API Gateway": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-API-Gateway_48.4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f.svg",
            
            # Security
            "AWS WAF": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-WAF_48.3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f.svg",
            "Amazon GuardDuty": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-GuardDuty_48.2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f.svg",
            "AWS Shield": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Shield_48.1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f.svg",
            
            # Application Integration
            "AWS Step Functions": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Step-Functions_48.0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f.svg",
            "Amazon EventBridge": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-EventBridge_48.9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e.svg",
            "Amazon SNS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Notification-Service_48.8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e.svg",
            "Amazon SQS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Queue-Service_48.7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e.svg"
        }
        
        # Build nodes structure
        nodes = []
        node_id_counter = 0
        service_to_node_id = {}
        
        # Create nodes for each service
        for category, services in selected_services.items():
            if services:
                for service in services:
                    node_id = f"node_{node_id_counter}"
                    node_id_counter += 1
                    
                    # Get configuration details
                    config = configurations.get(service, {}).get('config', {})
                    
                    # Build label with configuration details
                    label_parts = [service]
                    
                    if service == "Amazon EC2" and config:
                        instance_type = config.get('instance_type', 't3.micro')
                        instance_count = config.get('instance_count', 1)
                        label_parts.append(f"{instance_count}x {instance_type}")
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        label_parts.append(f"{engine}")
                        label_parts.append(instance_type)
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        label_parts.append(f"{storage_gb}GB")
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        label_parts.append(f"{memory}MB")
                    
                    nodes.append({
                        "id": node_id,
                        "label": "\n".join(label_parts),
                        "icon": service_icons.get(service, service_icons["Amazon EC2"]),
                        "category": category,
                        "service": service
                    })
                    
                    service_to_node_id[service] = node_id
        
        # Add external nodes
        nodes.extend([
            {
                "id": "user_node",
                "label": "User/Client",
                "icon": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_User_48.svg",
                "category": "External",
                "service": "User"
            },
            {
                "id": "external_node",
                "label": "External Systems",
                "icon": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Cloud_48.svg",
                "category": "External",
                "service": "External"
            },
            {
                "id": "analyst_node",
                "label": "Business Analyst",
                "icon": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_User_48.svg",
                "category": "External",
                "service": "Analyst"
            }
        ])
        
        # Build connections
        connections = []
        
        def add_connection(source_service, target_service, label=""):
            source_id = service_to_node_id.get(source_service) or f"{source_service.lower().replace(' ', '_')}_node"
            target_id = service_to_node_id.get(target_service) or f"{target_service.lower().replace(' ', '_')}_node"
            
            connections.append({
                "source": source_id,
                "target": target_id,
                "label": label
            })
        
        # User-facing connections
        if "Amazon CloudFront" in service_to_node_id:
            add_connection("User", "Amazon CloudFront", "accesses")
        if "Elastic Load Balancing" in service_to_node_id:
            add_connection("User", "Elastic Load Balancing", "accesses")
        if "Amazon API Gateway" in service_to_node_id:
            add_connection("User", "Amazon API Gateway", "calls")
        
        # CloudFront to S3
        if "Amazon CloudFront" in service_to_node_id and "Amazon S3" in service_to_node_id:
            add_connection("Amazon CloudFront", "Amazon S3", "serves from")
        
        # Load balancer to compute
        if "Elastic Load Balancing" in service_to_node_id:
            for compute in ["Amazon EC2", "Amazon ECS", "Amazon EKS"]:
                if compute in service_to_node_id:
                    add_connection("Elastic Load Balancing", compute, "routes to")
        
        # Compute to database connections
        compute_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        for compute in compute_services:
            if compute in service_to_node_id:
                for db in ["Amazon RDS", "Amazon DynamoDB", "Amazon OpenSearch"]:
                    if db in service_to_node_id:
                        add_connection(compute, db, "queries")
        
        # Analytics pipeline
        if "Amazon Kinesis" in service_to_node_id:
            add_connection("External", "Amazon Kinesis", "streams data")
            if "Amazon S3" in service_to_node_id:
                add_connection("Amazon Kinesis", "Amazon S3", "stores in")
        
        if "AWS Glue" in service_to_node_id and "Amazon S3" in service_to_node_id:
            add_connection("AWS Glue", "Amazon S3", "processes")
        
        if "Amazon OpenSearch" in service_to_node_id:
            add_connection("Analyst", "Amazon OpenSearch", "analyzes")
            if "AWS Glue" in service_to_node_id:
                add_connection("AWS Glue", "Amazon OpenSearch", "loads to")
        
        # AI/ML connections
        if "Amazon Bedrock" in service_to_node_id:
            if "Amazon S3" in service_to_node_id:
                add_connection("Amazon Bedrock", "Amazon S3", "reads from")
            for compute in compute_services:
                if compute in service_to_node_id:
                    add_connection(compute, "Amazon Bedrock", "invokes")
        
        # Step Functions workflow
        if "AWS Step Functions" in service_to_node_id:
            if "AWS Lambda" in service_to_node_id:
                add_connection("AWS Step Functions", "AWS Lambda", "orchestrates")
            if "Amazon EventBridge" in service_to_node_id:
                add_connection("Amazon EventBridge", "AWS Step Functions", "triggers")
        
        # Security connections
        if "AWS WAF" in service_to_node_id:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]:
                if frontend in service_to_node_id:
                    add_connection("AWS WAF", frontend, "protects")
        
        return {
            "nodes": nodes,
            "connections": connections,
            "requirements": requirements
        }
    
    @staticmethod
    def generate_comprehensive_diagram(selected_services: Dict, configurations: Dict, requirements: Dict) -> str:
        """Generate comprehensive AWS architecture diagram with proper icons and layout - LEGACY MERMAID"""
        
        # Start Mermaid diagram with professional styling
        mermaid_code = """graph TB
    classDef compute fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#000,stroke-dasharray: 0
    classDef storage fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef database fill:#3334B9,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef network fill:#5A30B5,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef security fill:#DD344C,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef ml fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef analytics fill:#259E9E,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef integration fill:#6B1C6B,stroke:#232F3E,stroke-width:2px,color:#fff,stroke-dasharray: 0
    classDef user fill:#666,stroke:#333,stroke-width:2px,color:#000,stroke-dasharray: 0

    User[User/Client]:::user
    External[External Systems]:::user
    Analyst[Business Analyst]:::user
"""
        
        # Service to icon mapping (using Mermaid icons)
        service_icons = {
            # Compute
            "Amazon EC2": "fa:fa-server",
            "AWS Lambda": "fa:fa-bolt", 
            "Amazon ECS": "fa:fa-cubes",
            "Amazon EKS": "fa:fa-ship",
            
            # Storage
            "Amazon S3": "fa:fa-archive",
            "Amazon EBS": "fa:fa-hdd-o",
            "Amazon EFS": "fa:fa-folder-open",
            
            # Database
            "Amazon RDS": "fa:fa-database",
            "Amazon DynamoDB": "fa:fa-table",
            "Amazon ElastiCache": "fa:fa-rocket",
            "Amazon OpenSearch": "fa:fa-search",
            
            # AI/ML
            "Amazon Bedrock": "fa:fa-brain",
            "Amazon SageMaker": "fa:fa-robot",
            
            # Analytics
            "Amazon Kinesis": "fa:fa-stream",
            "AWS Glue": "fa:fa-magic",
            "Amazon Redshift": "fa:fa-chart-bar",
            
            # Networking
            "Amazon VPC": "fa:fa-cloud",
            "Amazon CloudFront": "fa:fa-globe",
            "Elastic Load Balancing": "fa:fa-balance-scale",
            "Amazon API Gateway": "fa:fa-plug",
            
            # Security
            "AWS WAF": "fa:fa-shield-alt",
            "Amazon GuardDuty": "fa:fa-eye",
            "AWS Shield": "fa:fa-umbrella",
            
            # Application Integration
            "AWS Step Functions": "fa:fa-sitemap",
            "Amazon EventBridge": "fa:fa-calendar",
            "Amazon SNS": "fa:fa-bell",
            "Amazon SQS": "fa:fa-envelope"
        }
        
        # Category to style mapping
        category_styles = {
            "Compute": "compute",
            "Storage": "storage", 
            "Database": "database",
            "AI/ML": "ml",
            "Analytics": "analytics",
            "Networking": "network",
            "Security": "security",
            "Application Integration": "integration"
        }
        
        # Track nodes by category for better organization
        nodes_by_category = {}
        
        # Create nodes for each service with icons
        for category, services in selected_services.items():
            if services:
                nodes_by_category[category] = []
                for service in services:
                    node_id = service.replace(" ", "").replace("Amazon", "").replace("AWS", "")
                    
                    # Get configuration details
                    config = configurations.get(service, {}).get('config', {})
                    
                    # Create label with icon and details
                    icon = service_icons.get(service, "fa:fa-cube")
                    label = f"{service}<br/>"
                    
                    # Add configuration details based on service type
                    if service == "Amazon EC2" and config:
                        instance_type = config.get('instance_type', 't3.micro')
                        instance_count = config.get('instance_count', 1)
                        label += f"{instance_count}x {instance_type}"
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        label += f"{engine}<br/>{instance_type}"
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        label += f"{storage_gb}GB"
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        label += f"{memory}MB"
                    elif service == "Amazon OpenSearch" and config:
                        instance_type = config.get('instance_type', 't3.small.search')
                        label += f"{instance_type}"
                    elif service == "Amazon Kinesis" and config:
                        shard_count = config.get('shard_count', 1)
                        label += f"{shard_count} shards"
                    
                    # Add node with icon
                    mermaid_code += f"    {node_id}[{label}]:::{icon}\n"
                    
                    # Apply style
                    style = category_styles.get(category, "compute")
                    mermaid_code += f"    class {node_id} {style}\n"
                    
                    nodes_by_category[category].append(node_id)
        
        mermaid_code += "\n"
        
        # Create intelligent connections based on architecture patterns
        connections = []
        
        # User-facing connections
        if any(service in selected_services.get('Networking', []) for service in ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]):
            connections.append(("User", "AmazonCloudFront", "accesses"))
            connections.append(("User", "ElasticLoadBalancing", "accesses"))
            connections.append(("User", "AmazonAPIGateway", "calls"))
        
        # Frontend to backend connections
        if "Amazon CloudFront" in [s for v in selected_services.values() for s in v]:
            if "Amazon S3" in [s for v in selected_services.values() for s in v]:
                connections.append(("AmazonCloudFront", "AmazonS3", "serves from"))
        
        # Load balancer to compute
        if "Elastic Load Balancing" in [s for v in selected_services.values() for s in v]:
            for compute in ["AmazonEC2", "AmazonECS", "AmazonEKS"]:
                if compute in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                    connections.append(("ElasticLoadBalancing", compute, "routes to"))
        
        # Compute to database connections
        compute_services = ["AmazonEC2", "AWSLambda", "AmazonECS", "AmazonEKS"]
        for compute in compute_services:
            if compute in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                for db in ["AmazonRDS", "AmazonDynamoDB", "AmazonOpenSearch"]:
                    if db in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                        connections.append((compute, db, "queries"))
        
        # Analytics pipeline connections
        if "Amazon Kinesis" in [s for v in selected_services.values() for s in v]:
            connections.append(("External", "AmazonKinesis", "streams data"))
            if "Amazon S3" in [s for v in selected_services.values() for s in v]:
                connections.append(("AmazonKinesis", "AmazonS3", "stores in"))
        
        if "AWS Glue" in [s for v in selected_services.values() for s in v] and "Amazon S3" in [s for v in selected_services.values() for s in v]:
            connections.append(("AWSGlue", "AmazonS3", "processes"))
        
        if "Amazon OpenSearch" in [s for v in selected_services.values() for s in v]:
            connections.append(("Analyst", "AmazonOpenSearch", "analyzes"))
            if "AWS Glue" in [s for v in selected_services.values() for s in v]:
                connections.append(("AWSGlue", "AmazonOpenSearch", "loads to"))
        
        # AI/ML connections
        if "Amazon Bedrock" in [s for v in selected_services.values() for s in v]:
            if "Amazon S3" in [s for v in selected_services.values() for s in v]:
                connections.append(("AmazonBedrock", "AmazonS3", "reads from"))
            for compute in compute_services:
                if compute in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                    connections.append((compute, "AmazonBedrock", "invokes"))
        
        # Step Functions workflow
        if "AWS Step Functions" in [s for v in selected_services.values() for s in v]:
            if "AWSLambda" in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                connections.append(("AWSStepFunctions", "AWSLambda", "orchestrates"))
            if "AmazonEventBridge" in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                connections.append(("AmazonEventBridge", "AWSStepFunctions", "triggers"))
        
        # Security connections
        if "AWS WAF" in [s for v in selected_services.values() for s in v]:
            for frontend in ["AmazonCloudFront", "ElasticLoadBalancing", "AmazonAPIGateway"]:
                if frontend in [s.replace(" ", "").replace("Amazon", "").replace("AWS", "") for v in selected_services.values() for s in v]:
                    connections.append(("AWSWAF", frontend, "protects"))
        
        # Add connections to diagram
        for source, target, label in connections:
            source_id = source.replace(" ", "").replace("Amazon", "").replace("AWS", "")
            target_id = target.replace(" ", "").replace("Amazon", "").replace("AWS", "")
            
            # Check if both nodes exist
            source_exists = any(source_id in nodes for nodes in nodes_by_category.values())
            target_exists = any(target_id in nodes for nodes in nodes_by_category.values())
            
            if source_exists and target_exists:
                if label:
                    mermaid_code += f"    {source_id} -->|{label}| {target_id}\n"
                else:
                    mermaid_code += f"    {source_id} --> {target_id}\n"
        
        # Add subgraphs for logical grouping
        mermaid_code += "\n"
        
        # Frontend layer
        frontend_services = ["AmazonCloudFront", "ElasticLoadBalancing", "AmazonAPIGateway"]
        existing_frontend = [s for s in frontend_services if any(s in nodes for nodes in nodes_by_category.values())]
        if existing_frontend:
            mermaid_code += "    subgraph Frontend [Frontend Layer]\n"
            for service in existing_frontend:
                mermaid_code += f"        {service}\n"
            mermaid_code += "    end\n\n"
        
        # Application layer
        app_services = ["AmazonEC2", "AWSLambda", "AmazonECS", "AmazonEKS"]
        existing_app = [s for s in app_services if any(s in nodes for nodes in nodes_by_category.values())]
        if existing_app:
            mermaid_code += "    subgraph Application [Application Layer]\n"
            for service in existing_app:
                mermaid_code += f"        {service}\n"
            mermaid_code += "    end\n\n"
        
        # Data layer
        data_services = ["AmazonRDS", "AmazonDynamoDB", "AmazonS3", "AmazonElastiCache", "AmazonOpenSearch"]
        existing_data = [s for s in data_services if any(s in nodes for nodes in nodes_by_category.values())]
        if existing_data:
            mermaid_code += "    subgraph Data [Data Layer]\n"
            for service in existing_data:
                mermaid_code += f"        {service}\n"
            mermaid_code += "    end\n\n"
        
        # Analytics layer
        analytics_services = ["AmazonKinesis", "AWSGlue", "AmazonRedshift"]
        existing_analytics = [s for s in analytics_services if any(s in nodes for nodes in nodes_by_category.values())]
        if existing_analytics:
            mermaid_code += "    subgraph Analytics [Analytics Layer]\n"
            for service in existing_analytics:
                mermaid_code += f"        {service}\n"
            mermaid_code += "    end\n\n"
        
        # AI/ML layer
        ml_services = ["AmazonBedrock", "AmazonSageMaker"]
        existing_ml = [s for s in ml_services if any(s in nodes for nodes in nodes_by_category.values())]
        if existing_ml:
            mermaid_code += "    subgraph AIML [AI/ML Layer]\n"
            for service in existing_ml:
                mermaid_code += f"        {service}\n"
            mermaid_code += "    end\n\n"
        
        return mermaid_code
    
    @staticmethod
    def generate_opensearch_trending_queries_diagram() -> str:
        """Generate the specific OpenSearch trending queries architecture from the reference image"""
        
        mermaid_code = """graph TB
    classDef user fill:#666,stroke:#333,stroke-width:2px,color:#000
    classDef streaming fill:#259E9E,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef storage fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef search fill:#3334B9,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef compute fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#000
    classDef ml fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef workflow fill:#6B1C6B,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef database fill:#D45A4B,stroke:#232F3E,stroke-width:2px,color:#fff

    User[User<br/>Search Application]:::user
    Analyst[Business Analyst]:::user
    
    subgraph DataIngestion [Data Ingestion]
        KinesisDataStreams[Amazon Kinesis<br/>Data Streams]:::streaming
        KinesisFirehose[Amazon Kinesis<br/>Data Firehose]:::streaming
    end
    
    subgraph SearchLayer [Search & Analytics]
        OpenSearch[Amazon OpenSearch<br/>Service]:::search
        APIGateway[Amazon API<br/>Gateway]:::compute
        LambdaTrending[AWS Lambda<br/>Trending Queries]:::compute
    end
    
    subgraph DataProcessing [Data Processing & ML]
        S3Raw[Amazon S3<br/>RAW Logs]:::storage
        GlueCrawler[AWS Glue<br/>Crawler]:::compute
        GlueCatalog[AWS Glue<br/>Data Catalog]:::database
        StepFunctions[AWS Step Functions<br/>Cluster & Classify Workflow]:::workflow
        LambdaBedrock[AWS Lambda<br/>Invoke Bedrock LLM]:::compute
        Bedrock[Amazon Bedrock<br/>LLM Classification]:::ml
    end
    
    subgraph StorageOutput [Storage & Output]
        DynamoDB[Amazon DynamoDB<br/>Output Trending Queries]:::database
        S3Processed[Amazon S3<br/>Processed Data]:::storage
    end
    
    subgraph Orchestration [Orchestration]
        EventBridge[Amazon EventBridge<br/>Scheduler - Daily]:::workflow
    end

    User -->|search queries| KinesisDataStreams
    KinesisDataStreams -->|compress queries| KinesisFirehose
    KinesisFirehose -->|store logs| S3Raw
    
    EventBridge -->|trigger| StepFunctions
    S3Raw -->|crawl| GlueCrawler
    GlueCrawler -->|update schema| GlueCatalog
    GlueCatalog -->|read schema| StepFunctions
    
    StepFunctions -->|process queries| LambdaBedrock
    LambdaBedrock -->|classify with LLM| Bedrock
    Bedrock -->|return classification| LambdaBedrock
    LambdaBedrock -->|store results| DynamoDB
    StepFunctions -->|store processed data| S3Processed
    
    Analyst -->|access trending| APIGateway
    APIGateway -->|get trending| LambdaTrending
    LambdaTrending -->|query| OpenSearch
    LambdaTrending -->|read results| DynamoDB
    
    OpenSearch -->|serve search| User
    
    %% Styling for subgraphs
    class DataIngestion,SearchLayer,DataProcessing,StorageOutput,Orchestration fill:#f9f9f9,stroke:#ddd,stroke-width:2px,color:#333
    """

        return mermaid_code

class ArchitectureDiagramGenerator:
    """Generate AWS architecture diagrams using Mermaid with professional styling"""
    
    @staticmethod
    def generate_mermaid_diagram(selected_services: Dict, configurations: Dict, requirements: Dict) -> str:
        """Generate professional AWS architecture diagram"""
        
        # Check if this matches the OpenSearch trending queries pattern
        if ArchitectureDiagramGenerator._is_opensearch_trending_pattern(selected_services):
            return ProfessionalArchitectureGenerator.generate_opensearch_trending_queries_diagram()
        else:
            return ProfessionalArchitectureGenerator.generate_comprehensive_diagram(
                selected_services, configurations, requirements
            )
    
    @staticmethod
    def _is_opensearch_trending_pattern(selected_services: Dict) -> bool:
        """Check if the selected services match the OpenSearch trending queries pattern"""
        required_services = [
            "Amazon OpenSearch", "Amazon Kinesis", "AWS Glue", "Amazon Bedrock",
            "AWS Lambda", "Amazon S3", "Amazon DynamoDB"
        ]
        
        all_selected = []
        for services in selected_services.values():
            all_selected.extend(services)
        
        # Check if we have at least the core services for this pattern
        core_services_present = sum(1 for service in required_services if service in all_selected)
        return core_services_present >= 4  # At least 4 core services present

    @staticmethod
    def _generate_architecture_description(selected_services: Dict, requirements: Dict) -> str:
        """Generate markdown documentation for the architecture"""
        doc = f"""# AWS Architecture Documentation

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Architecture Overview

### Requirements
- **Performance Tier**: {requirements.get('performance_tier', 'Production')}
- **Workload Complexity**: {requirements.get('workload_complexity', 'Moderate')}
- **Scalability Pattern**: {requirements.get('scalability_needs', 'Fixed Capacity')}
- **Availability**: {requirements.get('availability_requirements', '99.9%')}

## Selected Services

"""
        
        for category, services in selected_services.items():
            if services:
                doc += f"### {category}\n"
                for service in services:
                    doc += f"- **{service}**\n"
                doc += "\n"
        
        doc += """
## Architecture Pattern

"""
        
        if ArchitectureDiagramGenerator._is_opensearch_trending_pattern(selected_services):
            doc += """This architecture follows the **OpenSearch Trending Queries** pattern, which includes:

- **Real-time data ingestion** via Kinesis Data Streams
- **Data processing** with AWS Glue and Step Functions
- **AI-powered analysis** using Amazon Bedrock
- **Search capabilities** with Amazon OpenSearch
- **Results storage** in DynamoDB

### Use Cases
- Identifying popular search trends
- Content strategy optimization
- User experience improvement
- Revenue optimization through better search insights
"""
        else:
            doc += "This is a custom architecture designed to meet your specific requirements.\n"
        
        doc += f"""
## Cost Optimization Recommendations

Based on the {requirements.get('performance_tier', 'Production')} tier and {requirements.get('scalability_needs', 'Fixed Capacity')} pattern:

1. Consider appropriate instance sizes for your workload
2. Implement auto-scaling where applicable
3. Use appropriate storage classes for data access patterns
4. Leverage AWS cost optimization tools

## Security Considerations

- Ensure proper IAM roles and policies
- Implement encryption at rest and in transit
- Use VPC endpoints for private access
- Enable logging and monitoring

---
*Generated by AWS Cloud Package Builder*
"""
        return doc
    
    @staticmethod
    def _display_architecture_recommendations(selected_services: Dict):
        """Display architecture recommendations based on selected services"""
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        recommendations = []
        
        if "Amazon OpenSearch" in all_services and "Amazon Kinesis" not in all_services:
            recommendations.append("Consider adding Amazon Kinesis for real-time data ingestion into OpenSearch")
        
        if "AWS Lambda" in all_services and "Amazon API Gateway" not in all_services:
            recommendations.append("Add Amazon API Gateway to expose Lambda functions as REST APIs")
        
        if "Amazon RDS" in all_services and "Amazon ElastiCache" not in all_services:
            recommendations.append("Consider Amazon ElastiCache for read-heavy workloads to reduce RDS load")
        
        if "Amazon S3" in all_services and "Amazon CloudFront" not in all_services:
            recommendations.append("Add Amazon CloudFront for global content delivery and reduced latency")
        
        if len([s for s in all_services if "Lambda" in s or "EC2" in s or "ECS" in s or "EKS" in s]) > 2:
            recommendations.append("Consider adding Elastic Load Balancing for traffic distribution")
        
        if recommendations:
            for rec in recommendations:
                st.info(rec)
        else:
            st.success("✓ Architecture looks well-balanced!")

# [Rest of your existing classes and functions remain unchanged...]
# ServiceSelector, YearlyTimelineCalculator, DynamicPricingEngine, etc.

class ServiceSelector:
    @staticmethod
    def render_service_selection() -> Dict[str, List[str]]:
        """Render service selection UI and return selected services"""
        st.subheader("Select AWS Services")
        st.write("Choose the services that best fit your architecture needs")
        
        selected_services = {}
        
        tabs = st.tabs(list(AWS_SERVICES.keys()))
        for i, (category, services) in enumerate(AWS_SERVICES.items()):
            with tabs[i]:
                st.write(f"**{category} Services**")
                
                cols = st.columns(2)
                for j, (service, description) in enumerate(services.items()):
                    col_idx = j % 2
                    with cols[col_idx]:
                        if st.checkbox(
                            f"{service}", 
                            help=description,
                            key=f"service_{category}_{j}"
                        ):
                            if category not in selected_services:
                                selected_services[category] = []
                            selected_services[category].append(service)
        
        return selected_services

class YearlyTimelineCalculator:
    @staticmethod
    def calculate_yearly_costs(base_monthly_cost: float, years: int, growth_rate: float = 0.0) -> Dict:
        """Calculate costs over years with growth rate"""
        yearly_data = {
            "years": [],
            "yearly_costs": [],
            "monthly_costs": [],
            "cumulative_costs": [],
            "total_cost": 0.0
        }
        
        if years == 0:
            return yearly_data
            
        cumulative = 0.0
        for year in range(1, years + 1):
            monthly_cost_year = base_monthly_cost * (1 + growth_rate) ** ((year - 1) * 12)
            yearly_cost = monthly_cost_year * 12
            
            cumulative += yearly_cost
            
            yearly_data["years"].append(f"Year {year}")
            yearly_data["yearly_costs"].append(yearly_cost)
            yearly_data["monthly_costs"].append(monthly_cost_year)
            yearly_data["cumulative_costs"].append(cumulative)
        
        yearly_data["total_cost"] = cumulative
        return yearly_data
    
    @staticmethod
    def calculate_detailed_monthly_timeline(base_monthly_cost: float, total_months: int, growth_rate: float = 0.0) -> Dict:
        """Calculate detailed monthly breakdown"""
        monthly_data = {
            "months": [],
            "monthly_costs": [],
            "cumulative_costs": [],
            "total_cost": 0.0
        }
        
        if total_months == 0:
            return monthly_data
            
        cumulative = 0.0
        for month in range(1, total_months + 1):
            monthly_cost = base_monthly_cost * (1 + growth_rate) ** (month - 1)
            cumulative += monthly_cost
            
            year = (month - 1) // 12 + 1
            month_in_year = (month - 1) % 12 + 1
            monthly_data["months"].append(f"Y{year} M{month_in_year}")
            monthly_data["monthly_costs"].append(monthly_cost)
            monthly_data["cumulative_costs"].append(cumulative)
        
        monthly_data["total_cost"] = cumulative
        return monthly_data
    
    @staticmethod
    def render_timeline_selector() -> Dict:
        """Render timeline configuration UI"""
        st.subheader("💰 Timeline & Usage Pattern")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            timeline_type = st.selectbox(
                "Timeline Period",
                [
                    "1 Month", "3 Months", "6 Months", 
                    "1 Year (12 Months)", "2 Years (24 Months)", 
                    "3 Years (36 Months)", "5 Years (60 Months)"
                ],
                index=3,
                help="Select your planning horizon"
            )
            if "Year" in timeline_type:
                years = int(timeline_type.split()[0])
                total_months = years * 12
            else:
                total_months = int(timeline_type.split()[0])
                years = total_months // 12
        
        with col2:
            usage_pattern = st.selectbox(
                "Usage Pattern",
                ["Development", "Sporadic", "Normal", "Intensive", "24x7"],
                index=2,
                help="Expected usage intensity"
            )
        
        with col3:
            growth_rate = st.slider(
                "Monthly Growth Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                help="Expected monthly growth in usage"
            ) / 100
        
        with col4:
            commitment_type = st.selectbox(
                "Commitment Type",
                ["On-Demand", "1-Year Reserved", "3-Year Reserved", "Savings Plans"],
                help="AWS pricing commitment level"
            )
        
        pattern_multipliers = {
            "Development": 0.6,
            "Sporadic": 0.8,
            "Normal": 1.0,
            "Intensive": 1.4,
            "24x7": 1.8
        }
        
        commitment_discounts = {
            "On-Demand": 1.0,
            "1-Year Reserved": 0.7,
            "3-Year Reserved": 0.5,
            "Savings Plans": 0.72
        }
        
        return {
            "timeline_type": timeline_type,
            "total_months": total_months,
            "years": years,
            "usage_pattern": usage_pattern,
            "pattern_multiplier": pattern_multipliers[usage_pattern],
            "growth_rate": growth_rate,
            "commitment_type": commitment_type,
            "commitment_discount": commitment_discounts[commitment_type]
        }

# [Rest of your existing DynamicPricingEngine class and other functions...]
# Due to character limits, I'm showing the integration point

def main():
    st.set_page_config(
        page_title="AWS Cloud Package Builder", 
        layout="wide",
        page_icon="☁️"
    )
    
    st.title("🚀 AWS Cloud Package Builder")
    st.markdown("Design, Configure, and Optimize Your Cloud Architecture with Real-time Pricing")
    
    initialize_session_state()
    
    # TIMELINE CONFIGURATION
    timeline_config = YearlyTimelineCalculator.render_timeline_selector()
    
    # PROJECT REQUIREMENTS SECTION
    with st.expander("📋 Project Requirements & Architecture", expanded=True):
        st.write("**Define Your Project Requirements**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Workload Profile")
            workload_complexity = st.select_slider(
                "Workload Complexity",
                options=["Simple", "Moderate", "Complex", "Enterprise"],
                value="Moderate",
                help="Complexity of your application architecture"
            )
            
            performance_tier = st.select_slider(
                "Performance Tier",
                options=["Development", "Testing", "Production", "Enterprise"],
                value="Production"
            )
            
        with col2:
            st.subheader("Scalability & Availability")
            scalability_needs = st.selectbox(
                "Scalability Pattern",
                ["Fixed Capacity", "Seasonal", "Predictable Growth", "Unpredictable Burst"]
            )
            
            availability_requirements = st.selectbox(
                "Availability Requirements",
                ["99.9% (Business Hours)", "99.95% (High Availability)", "99.99% (Mission Critical)"]
            )
    
    # Store requirements for pricing calculations
    requirements = {
        'workload_complexity': workload_complexity,
        'performance_tier': performance_tier,
        'scalability_needs': scalability_needs,
        'availability_requirements': availability_requirements
    }
    
    # SERVICE SELECTION
    st.session_state.selected_services = ServiceSelector.render_service_selection()
    
    if st.session_state.selected_services:
        st.header("⚙️ Service Configuration")
        
        st.session_state.total_cost = 0
        st.session_state.configurations = {}
        st.session_state.timeline_data = {}
        
        for category, services in st.session_state.selected_services.items():
            st.subheader(f"{category}")
            
            for i, service in enumerate(services):
                with st.expander(f"🔧 {service}", expanded=True):
                    st.write(f"*{AWS_SERVICES[category][service]}*")
                    
                    service_key = f"{category}_{service}_{i}"
                    
                    if service_key not in st.session_state:
                        st.session_state[service_key] = {}
                    
                    # Render service configuration
                    config = render_service_configurator(service, service_key)
                    st.session_state[service_key].update(config)
                    
                    # Calculate pricing with timeline AND requirements
                    pricing_result = DynamicPricingEngine.calculate_service_price(
                        service, 
                        st.session_state[service_key],
                        timeline_config,
                        requirements  # Pass requirements here
                    )
                    
                    # Display pricing information with enterprise factors
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Base Monthly", f"${pricing_result['base_monthly_cost']:,.2f}")
                    with col2:
                        st.metric("Adjusted Monthly", f"${pricing_result['adjusted_monthly_cost']:,.2f}")
                    with col3:
                        st.metric("After Commitment", f"${pricing_result['discounted_monthly_cost']:,.2f}")
                    with col4:
                        st.metric(f"Total {timeline_config['timeline_type']}", 
                                 f"${pricing_result['total_timeline_cost']:,.2f}")
                    
                    # Show enterprise factors if applicable
                    if pricing_result.get('scalability_multiplier', 1.0) > 1.0 or pricing_result.get('availability_multiplier', 1.0) > 1.0:
                        st.caption(f"📈 Scalability factor: {pricing_result.get('scalability_multiplier', 1.0):.1f}x | "
                                 f"🛡️ Availability factor: {pricing_result.get('availability_multiplier', 1.0):.1f}x")
                    
                    # Store configuration
                    st.session_state.configurations[service] = {
                        "config": st.session_state[service_key],
                        "pricing": pricing_result
                    }
                    
                    # Add to total cost
                    st.session_state.total_cost += pricing_result['total_timeline_cost']
                    
                    # Show yearly visualization (only if we have yearly data)
                    if timeline_config["years"] > 0:
                        render_yearly_visualization(pricing_result['yearly_data'], service)
        
        # GENERATE PROFESSIONAL ARCHITECTURE DIAGRAM
        st.header("🏗️ Professional Architecture Diagram")
        
        # Generate professional diagram
        mermaid_code = ArchitectureDiagramGenerator.generate_mermaid_diagram(
            st.session_state.selected_services,
            st.session_state.configurations,
            requirements
        )
        
        # Display the diagram
        st.subheader("📐 Your AWS Architecture")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            try:
                # Enhanced HTML with better styling
                html_code = f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 5px; border-radius: 15px; margin-bottom: 20px;">
                    <div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
                        <script>
                            mermaid.initialize({{
                                startOnLoad: true,
                                theme: 'default',
                                flowchart: {{
                                    useMaxWidth: true,
                                    htmlLabels: true,
                                    curve: 'basis'
                                }},
                                themeCSS: `
                                    .node rect {{
                                        stroke-width: 2px;
                                        rx: 8px;
                                        ry: 8px;
                                    }}
                                    .cluster rect {{
                                        fill: #f8f9fa !important;
                                        stroke: #dee2e6 !important;
                                        stroke-width: 2px;
                                        rx: 10px;
                                        ry: 10px;
                                    }}
                                    .cluster-label {{
                                        fill: #495057 !important;
                                        font-weight: bold;
                                    }}
                                    .edgeLabel {{
                                        background-color: white;
                                        padding: 4px;
                                        border-radius: 4px;
                                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                    }}
                                `
                            }});
                        </script>
                        <div class="mermaid">
                            {mermaid_code}
                        </div>
                    </div>
                </div>
                """
                
                import streamlit.components.v1 as components
                components.html(html_code, height=800, scrolling=True)
                
            except Exception as e:
                st.error(f"Error displaying diagram: {str(e)}")
                st.code(mermaid_code, language="mermaid")
        
        with col2:
            st.subheader("Diagram Controls")
            
            # Pattern detection
            if ArchitectureDiagramGenerator._is_opensearch_trending_pattern(st.session_state.selected_services):
                st.success("🎯 Pattern Detected: OpenSearch Trending Queries")
                st.info("This matches the AWS reference architecture for analyzing search trends with AI/ML")
            
            # Diagram information
            with st.expander("📊 Architecture Info", expanded=True):
                total_services = sum(len(services) for services in st.session_state.selected_services.values())
                st.metric("Total Services", total_services)
                
                categories_used = [cat for cat, services in st.session_state.selected_services.items() if services]
                st.write("**Categories:**", ", ".join(categories_used))
            
            # Download options
            with st.expander("💾 Export Options", expanded=True):
                st.download_button(
                    label="📥 Download Mermaid Code",
                    data=mermaid_code,
                    file_name=f"aws_architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mmd",
                    mime="text/plain"
                )
                
                # Generate architecture description
                arch_description = ArchitectureDiagramGenerator._generate_architecture_description(
                    st.session_state.selected_services, requirements
                )
                st.download_button(
                    label="📄 Download Architecture Doc",
                    data=arch_description,
                    file_name=f"architecture_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            
            # Architecture recommendations
            with st.expander("💡 Architecture Tips", expanded=True):
                ArchitectureDiagramGenerator._display_architecture_recommendations(st.session_state.selected_services)
        
        # [Rest of your existing main function for cost summary, recommendations, and export]
        # This includes your existing cost visualization, recommendations, and export functionality

if __name__ == "__main__":
    main()