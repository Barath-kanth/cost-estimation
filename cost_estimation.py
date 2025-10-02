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

# Try to import diagrams library for architecture generation
try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.aws.compute import EC2, Lambda, ECS, EKS
    from diagrams.aws.database import RDS, Dynamodb, ElastiCache
    from diagrams.aws.storage import S3, EBS, EFS
    from diagrams.aws.network import VPC, CloudFront, ELB
    from diagrams.aws.security import WAF, GuardDuty, Shield
    from diagrams.aws.ml import Sagemaker, Comprehend
    from diagrams.aws.integration import Bedrock
    DIAGRAMS_AVAILABLE = True
except ImportError:
    DIAGRAMS_AVAILABLE = False
    st.warning("⚠️ Install 'diagrams' library for automatic architecture generation: pip install diagrams")

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
        "Amazon ElastiCache": "In-memory caching"
    },
    "AI/ML": {
        "Amazon Bedrock": "Fully managed foundation models",
        "Amazon SageMaker": "Build, train and deploy ML models",
        "Amazon Comprehend": "Natural language processing"
    },
    "Networking": {
        "Amazon VPC": "Isolated cloud resources",
        "Amazon CloudFront": "Global content delivery network",
        "Elastic Load Balancing": "Distribute incoming traffic"
    },
    "Security": {
        "AWS WAF": "Web Application Firewall",
        "Amazon GuardDuty": "Threat detection service",
        "AWS Shield": "DDoS protection"
    }
}

class ArchitectureDiagramGenerator:
    """Generate AWS architecture diagrams using Mermaid (No Graphviz required)"""
    
    @staticmethod
    def generate_mermaid_diagram(selected_services: Dict, configurations: Dict) -> str:
        """Generate Mermaid diagram code for AWS architecture"""
        
        # Start Mermaid diagram
        mermaid_code = "graph LR\n"
        mermaid_code += "    classDef compute fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff\n"
        mermaid_code += "    classDef storage fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:#fff\n"
        mermaid_code += "    classDef database fill:#3334B9,stroke:#232F3E,stroke-width:2px,color:#fff\n"
        mermaid_code += "    classDef network fill:#5A30B5,stroke:#232F3E,stroke-width:2px,color:#fff\n"
        mermaid_code += "    classDef security fill:#DD344C,stroke:#232F3E,stroke-width:2px,color:#fff\n"
        mermaid_code += "    classDef ml fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff\n\n"
        
        # Track node IDs
        node_ids = {}
        node_counter = 0
        
        # Category to style mapping
        category_styles = {
            "Compute": "compute",
            "Storage": "storage",
            "Database": "database",
            "AI/ML": "ml",
            "Networking": "network",
            "Security": "security"
        }
        
        # Create nodes for each service
        for category, services in selected_services.items():
            if services:
                for service in services:
                    node_id = f"S{node_counter}"
                    node_counter += 1
                    
                    # Get configuration details
                    config = configurations.get(service, {}).get('config', {})
                    
                    # Create label with details
                    label = service.replace("Amazon ", "").replace("AWS ", "")
                    
                    if service == "Amazon EC2" and config:
                        instance_count = config.get('instance_count', 1)
                        instance_type = config.get('instance_type', 't3.micro')
                        label = f"{label}<br/>{instance_count}x {instance_type}"
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        label = f"{label}<br/>{engine}<br/>{instance_type}"
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        label = f"{label}<br/>{storage_gb}GB"
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        label = f"{label}<br/>{memory}MB"
                    
                    # Add node
                    mermaid_code += f"    {node_id}[\"{label}\"]\n"
                    
                    # Apply style
                    style = category_styles.get(category, "compute")
                    mermaid_code += f"    class {node_id} {style}\n"
                    
                    node_ids[service] = node_id
        
        mermaid_code += "\n"
        
        # Flatten services list
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Create connections
        connections = []
        
        # CloudFront -> S3
        if "Amazon CloudFront" in all_services and "Amazon S3" in all_services:
            connections.append(("Amazon CloudFront", "Amazon S3", "distributes"))
        
        # ELB -> EC2/ECS/EKS
        if "Elastic Load Balancing" in all_services:
            for compute in ["Amazon EC2", "Amazon ECS", "Amazon EKS"]:
                if compute in all_services:
                    connections.append(("Elastic Load Balancing", compute, "routes"))
        
        # EC2/Lambda -> RDS/DynamoDB
        compute_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        database_services = ["Amazon RDS", "Amazon DynamoDB"]
        
        for compute in compute_services:
            if compute in all_services:
                for db in database_services:
                    if db in all_services:
                        connections.append((compute, db, "queries"))
                        break
        
        # EC2 -> S3
        if "Amazon EC2" in all_services and "Amazon S3" in all_services:
            if not any(c[0] == "Amazon EC2" and c[1] == "Amazon S3" for c in connections):
                connections.append(("Amazon EC2", "Amazon S3", "stores"))
        
        # Lambda -> S3
        if "AWS Lambda" in all_services and "Amazon S3" in all_services:
            connections.append(("AWS Lambda", "Amazon S3", "reads/writes"))
        
        # WAF -> CloudFront/ELB
        if "AWS WAF" in all_services:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing"]:
                if frontend in all_services:
                    connections.append(("AWS WAF", frontend, "protects"))
                    break
        
        # EC2 -> ElastiCache
        if "Amazon EC2" in all_services and "Amazon ElastiCache" in all_services:
            connections.append(("Amazon EC2", "Amazon ElastiCache", "caches"))
        
        # SageMaker/Bedrock -> S3
        for ml_service in ["Amazon SageMaker", "Amazon Bedrock"]:
            if ml_service in all_services and "Amazon S3" in all_services:
                connections.append((ml_service, "Amazon S3", "data"))
        
        # Add connections to diagram
        for source, target, label in connections:
            if source in node_ids and target in node_ids:
                source_id = node_ids[source]
                target_id = node_ids[target]
                if label:
                    mermaid_code += f"    {source_id} -->|{label}| {target_id}\n"
                else:
                    mermaid_code += f"    {source_id} --> {target_id}\n"
        
        return mermaid_code

    # Map service names to diagram icons (for Graphviz version)
    SERVICE_ICON_MAP = {
        "Amazon EC2": "EC2",
        "AWS Lambda": "Lambda",
        "Amazon ECS": "ECS",
        "Amazon EKS": "EKS",
        "Amazon S3": "S3",
        "Amazon EBS": "EBS",
        "Amazon EFS": "EFS",
        "Amazon RDS": "RDS",
        "Amazon DynamoDB": "Dynamodb",
        "Amazon ElastiCache": "ElastiCache",
        "Amazon Bedrock": "Bedrock",
        "Amazon SageMaker": "Sagemaker",
        "Amazon Comprehend": "Comprehend",
        "Amazon VPC": "VPC",
        "Amazon CloudFront": "CloudFront",
        "Elastic Load Balancing": "ELB",
        "AWS WAF": "WAF",
        "Amazon GuardDuty": "GuardDuty",
        "AWS Shield": "Shield"
    }
    
    @staticmethod
    def get_icon_class(service_name: str):
        """Get the appropriate icon class for a service (for Graphviz version)"""
        icon_mapping = {
            "EC2": EC2,
            "Lambda": Lambda,
            "ECS": ECS,
            "EKS": EKS,
            "S3": S3,
            "EBS": EBS,
            "EFS": EFS,
            "RDS": RDS,
            "Dynamodb": Dynamodb,
            "ElastiCache": ElastiCache,
            "Bedrock": Sagemaker,  # Using Sagemaker as placeholder
            "Sagemaker": Sagemaker,
            "Comprehend": Comprehend,
            "VPC": VPC,
            "CloudFront": CloudFront,
            "ELB": ELB,
            "WAF": WAF,
            "GuardDuty": GuardDuty,
            "Shield": Shield
        }
        
        icon_name = ArchitectureDiagramGenerator.SERVICE_ICON_MAP.get(service_name)
        return icon_mapping.get(icon_name, EC2)  # Default to EC2 if not found
    
    @staticmethod
    def generate_architecture_diagram(selected_services: Dict, configurations: Dict) -> Optional[str]:
        """Generate AWS architecture diagram based on selected services (Graphviz version)"""
        if not DIAGRAMS_AVAILABLE:
            st.warning("⚠️ Install 'diagrams' and 'graphviz' for automatic architecture generation")
            st.code("pip install diagrams graphviz", language="bash")
            return None
        
        try:
            # Create temporary directory for diagram
            temp_dir = tempfile.gettempdir()
            diagram_path = os.path.join(temp_dir, "aws_architecture")
            
            # Remove old diagram if exists
            if os.path.exists(f"{diagram_path}.png"):
                os.remove(f"{diagram_path}.png")
            
            # Create diagram with custom attributes
            with Diagram(
                "AWS Cloud Architecture",
                filename=diagram_path,
                show=False,
                direction="LR",
                outformat="png",
                graph_attr={
                    "fontsize": "14",
                    "bgcolor": "white",
                    "pad": "0.5",
                    "splines": "ortho",
                    "nodesep": "0.8",
                    "ranksep": "1.0"
                }
            ):
                # Group services by category
                service_nodes = {}
                
                for category, services in selected_services.items():
                    if services:  # Only create cluster if there are services
                        with Cluster(f"{category} Layer"):
                            for service in services:
                                icon_class = ArchitectureDiagramGenerator.get_icon_class(service)
                                
                                # Get configuration details if available
                                config = configurations.get(service, {}).get('config', {})
                                
                                # Create label with key details
                                label = service.replace("Amazon ", "").replace("AWS ", "")
                                
                                if service == "Amazon EC2" and config:
                                    instance_count = config.get('instance_count', 1)
                                    instance_type = config.get('instance_type', 't3.micro')
                                    label = f"{label}\\n{instance_count}x {instance_type}"
                                elif service == "Amazon RDS" and config:
                                    instance_type = config.get('instance_type', 'db.t3.micro')
                                    engine = config.get('engine', 'PostgreSQL')
                                    label = f"{label}\\n{engine}\\n{instance_type}"
                                elif service == "Amazon S3" and config:
                                    storage_gb = config.get('storage_gb', 100)
                                    label = f"{label}\\n{storage_gb}GB"
                                elif service == "AWS Lambda" and config:
                                    memory = config.get('memory_mb', 128)
                                    label = f"{label}\\n{memory}MB"
                                
                                service_nodes[service] = icon_class(label)
                
                # Create logical connections between services
                ArchitectureDiagramGenerator._create_service_connections(service_nodes, selected_services)
            
            # Return the path to generated diagram
            diagram_file = f"{diagram_path}.png"
            if os.path.exists(diagram_file):
                return diagram_file
            
            return None
            
        except Exception as e:
            st.error(f"Error generating architecture diagram: {str(e)}")
            st.info("Make sure Graphviz is installed on your system: https://graphviz.org/download/")
            return None
    
    @staticmethod
    def _create_service_connections(service_nodes: Dict, selected_services: Dict):
        """Create logical connections between AWS services (for Graphviz version)"""
        # Flatten services list
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Define common service connection patterns
        connections = []
        
        # CloudFront -> S3
        if "Amazon CloudFront" in all_services and "Amazon S3" in all_services:
            connections.append(("Amazon CloudFront", "Amazon S3", "distributes"))
        
        # ELB -> EC2/ECS/EKS
        if "Elastic Load Balancing" in all_services:
            for compute in ["Amazon EC2", "Amazon ECS", "Amazon EKS"]:
                if compute in all_services:
                    connections.append(("Elastic Load Balancing", compute, "routes"))
        
        # EC2/ECS/Lambda -> RDS/DynamoDB
        compute_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        database_services = ["Amazon RDS", "Amazon DynamoDB"]
        
        for compute in compute_services:
            if compute in all_services:
                for db in database_services:
                    if db in all_services:
                        connections.append((compute, db, ""))
                        break  # Only connect to one database
        
        # EC2 -> S3
        if "Amazon EC2" in all_services and "Amazon S3" in all_services:
            if ("Amazon EC2", "Amazon S3", "") not in [(c[0], c[1], "") for c in connections]:
                connections.append(("Amazon EC2", "Amazon S3", ""))
        
        # Lambda -> S3
        if "AWS Lambda" in all_services and "Amazon S3" in all_services:
            connections.append(("AWS Lambda", "Amazon S3", ""))
        
        # WAF -> CloudFront/ELB
        if "AWS WAF" in all_services:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing"]:
                if frontend in all_services:
                    connections.append(("AWS WAF", frontend, "protects"))
                    break
        
        # EC2 -> ElastiCache
        if "Amazon EC2" in all_services and "Amazon ElastiCache" in all_services:
            connections.append(("Amazon EC2", "Amazon ElastiCache", ""))
        
        # SageMaker/Bedrock -> S3
        for ml_service in ["Amazon SageMaker", "Amazon Bedrock"]:
            if ml_service in all_services and "Amazon S3" in all_services:
                connections.append((ml_service, "Amazon S3", ""))
        
        # EBS -> EC2 (storage connection)
        if "Amazon EBS" in all_services and "Amazon EC2" in all_services:
            connections.append(("Amazon EC2", "Amazon EBS", ""))
        
        # Create edges with labels only for important connections
        for source, target, label in connections:
            if source in service_nodes and target in service_nodes:
                if label:
                    service_nodes[source] >> Edge(label=label, style="bold", color="blue") >> service_nodes[target]
                else:
                    service_nodes[source] >> service_nodes[target]

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

class DynamicPricingEngine:
    @staticmethod
    def calculate_service_price(service: str, config: Dict, timeline_config: Dict) -> Dict:
        """Calculate service price with dynamic factors and timeline"""
        base_price = DynamicPricingEngine._calculate_base_price(service, config)
        
        adjusted_price = base_price * timeline_config["pattern_multiplier"]
        discounted_price = adjusted_price * timeline_config["commitment_discount"]
        
        if timeline_config["years"] > 0:
            yearly_data = YearlyTimelineCalculator.calculate_yearly_costs(
                discounted_price, 
                timeline_config["years"],
                timeline_config["growth_rate"]
            )
        else:
            yearly_data = {"years": [], "yearly_costs": [], "monthly_costs": [], "cumulative_costs": [], "total_cost": 0.0}
        
        if timeline_config["total_months"] > 0:
            monthly_data = YearlyTimelineCalculator.calculate_detailed_monthly_timeline(
                discounted_price,
                timeline_config["total_months"],
                timeline_config["growth_rate"]
            )
        else:
            monthly_data = {"months": [], "monthly_costs": [], "cumulative_costs": [], "total_cost": 0.0}
        
        return {
            "base_monthly_cost": base_price,
            "adjusted_monthly_cost": adjusted_price,
            "discounted_monthly_cost": discounted_price,
            "yearly_data": yearly_data,
            "monthly_data": monthly_data,
            "total_timeline_cost": monthly_data["total_cost"],
            "commitment_savings": adjusted_price - discounted_price
        }
    
    @staticmethod
    def _calculate_base_price(service: str, config: Dict) -> float:
        """Calculate base monthly price for service"""
        
        if service == "Amazon EC2":
            instance_type = config.get('instance_type', 't3.micro')
            instance_count = config.get('instance_count', 1)
            
            instance_prices = {
                't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                'm5.large': 0.096, 'm5.xlarge': 0.192,
                'c5.large': 0.085, 'c5.xlarge': 0.17,
                'r5.large': 0.126, 'r5.xlarge': 0.252
            }
            
            base_price = instance_prices.get(instance_type, 0.1) * 730 * instance_count
            
            storage_gb = config.get('storage_gb', 30)
            volume_type = config.get('volume_type', 'gp3')
            storage_price_per_gb = {
                'gp3': 0.08, 'gp2': 0.10, 'io1': 0.125, 'io2': 0.125,
                'st1': 0.045, 'sc1': 0.015
            }
            base_price += storage_gb * storage_price_per_gb.get(volume_type, 0.08)
            
            return base_price
            
        elif service == "Amazon RDS":
            instance_type = config.get('instance_type', 'db.t3.micro')
            
            rds_prices = {
                'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
                'db.m5.large': 0.17, 'db.r5.large': 0.24
            }
            
            base_price = rds_prices.get(instance_type, 0.1) * 730
            
            storage_gb = config.get('storage_gb', 20)
            base_price += storage_gb * 0.115
            
            if config.get('multi_az', False):
                base_price *= 2
            
            return base_price
            
        elif service == "Amazon S3":
            storage_gb = config.get('storage_gb', 100)
            storage_class = config.get('storage_class', 'Standard')
            
            storage_prices = {
                'Standard': 0.023, 'Intelligent-Tiering': 0.0125,
                'Standard-IA': 0.0125, 'One Zone-IA': 0.01,
                'Glacier': 0.004, 'Glacier Deep Archive': 0.00099
            }
            
            return storage_gb * storage_prices.get(storage_class, 0.023)
            
        elif service == "AWS Lambda":
            memory_mb = config.get('memory_mb', 128)
            requests = config.get('requests_per_month', 1000000)
            duration_ms = config.get('avg_duration_ms', 100)
            
            gb_seconds = (requests * duration_ms * memory_mb) / (1000 * 1024)
            return (requests * 0.0000002) + (gb_seconds * 0.0000166667)
        
        return 0.0

# ... (keep all the render_service_configurator and other functions exactly as they were)

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
                    
                    # Calculate pricing with timeline
                    pricing_result = DynamicPricingEngine.calculate_service_price(
                        service, 
                        st.session_state[service_key],
                        timeline_config
                    )
                    
                    # Display pricing information
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
        
        # GENERATE ARCHITECTURE DIAGRAM (MERMAID VERSION - NO GRAPHVIZ NEEDED)
        st.header("🏗️ Architecture Diagram")
        
        # Generate Mermaid diagram
        mermaid_code = ArchitectureDiagramGenerator.generate_mermaid_diagram(
            st.session_state.selected_services,
            st.session_state.configurations
        )
        
        # Display the diagram using Streamlit's built-in mermaid support
        st.subheader("📐 Your AWS Architecture")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            try:
                # Use Streamlit's native mermaid rendering
                import streamlit.components.v1 as components
                
                # Create HTML with Mermaid
                html_code = f"""
                <div style="background: white; padding: 20px; border-radius: 10px;">
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>
                        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
                    </script>
                    <div class="mermaid">
                        {mermaid_code}
                    </div>
                </div>
                """
                
                components.html(html_code, height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"Error displaying diagram: {str(e)}")
                st.code(mermaid_code, language="mermaid")
        
        with col2:
            # Show mermaid code
            with st.expander("📝 Mermaid Code"):
                st.code(mermaid_code, language="mermaid")
                
            # Download button
            st.download_button(
                label="📥 Download Mermaid",
                data=mermaid_code,
                file_name=f"aws_architecture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mmd",
                mime="text/plain"
            )
        
        st.info("💡 Tip: You can copy the Mermaid code and paste it into https://mermaid.live for editing")
        
        st.markdown("---")
        
        # COST SUMMARY & VISUALIZATION
        st.header("💰 Cost Summary & Analysis")
        
        # Calculate overall yearly breakdown (only if we have years)
        if timeline_config["years"] > 0:
            overall_yearly_data = YearlyTimelineCalculator.calculate_yearly_costs(
                sum([config['pricing']['discounted_monthly_cost'] for config in st.session_state.configurations.values()]),
                timeline_config["years"],
                timeline_config["growth_rate"]
            )
        else:
            overall_yearly_data = {"years": [], "yearly_costs": [], "monthly_costs": [], "cumulative_costs": [], "total_cost": 0.0}
        
        # Key metrics with safe division
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Timeline Cost", f"${st.session_state.total_cost:,.2f}")
        with col2:
            # Safe division for monthly average
            if timeline_config["total_months"] > 0:
                avg_monthly = st.session_state.total_cost / timeline_config["total_months"]
                st.metric("Average Monthly Cost", f"${avg_monthly:,.2f}")
            else:
                st.metric("Average Monthly Cost", "$0.00")
        with col3:
            # Safe division for yearly average
            if timeline_config["years"] > 0:
                avg_yearly = st.session_state.total_cost / timeline_config["years"]
                st.metric("Average Yearly Cost", f"${avg_yearly:,.2f}")
            else:
                st.metric("Average Yearly Cost", "$0.00")
        with col4:
            st.metric("Timeline Period", timeline_config["timeline_type"])
        
        # Overall yearly visualization (only if we have yearly data)
        if timeline_config["years"] > 0 and overall_yearly_data["years"]:
            st.subheader("📊 Overall Yearly Cost Breakdown")
            render_yearly_visualization(overall_yearly_data, "All Services")
        
        # Cost breakdown by service
        st.subheader("🔍 Cost Breakdown by Service")
        service_costs = {
            service: config['pricing']['total_timeline_cost']
            for service, config in st.session_state.configurations.items()
        }
        
        if service_costs:
            # Create a simple bar chart for service costs
            cost_df = pd.DataFrame({
                'Service': list(service_costs.keys()),
                'Total Cost': list(service_costs.values())
            })
            st.bar_chart(cost_df.set_index('Service'))
            
            # Display service costs table
            st.write("**Detailed Service Costs:**")
            for service, cost in service_costs.items():
                st.write(f"- **{service}**: ${cost:,.2f}")
        
        # COMMITMENT SAVINGS ANALYSIS
        st.subheader("💵 Commitment Savings Analysis")
        total_savings = sum([config['pricing']['commitment_savings'] * timeline_config["total_months"] 
                           for config in st.session_state.configurations.values()])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Commitment Type", timeline_config["commitment_type"])
        with col2:
            discount_pct = (1 - timeline_config["commitment_discount"]) * 100
            st.metric("Discount Applied", f"{discount_pct:.1f}%")
        with col3:
            st.metric("Total Savings", f"${total_savings:,.2f}")
        
        # RECOMMENDATIONS
        with st.expander("💡 Optimization Recommendations", expanded=True):
            st.write("Based on your configuration, here are some optimization suggestions:")
            
            # Analyze configurations and provide recommendations
            for service, config in st.session_state.configurations.items():
                service_config = config['config']
                pricing = config['pricing']
                
                if service == "Amazon EC2":
                    if service_config.get('instance_count', 1) > 1 and timeline_config["usage_pattern"] == "Development":
                        st.info(f"**{service}**: Consider using fewer instances or smaller instance types for development workload")
                    
                    if pricing['adjusted_monthly_cost'] > 1000:
                        st.info(f"**{service}**: Explore Reserved Instances for potential 30-50% savings")
                
                elif service == "Amazon RDS":
                    if service_config.get('multi_az', False) and timeline_config["usage_pattern"] == "Development":
                        st.info(f"**{service}**: Consider single-AZ deployment for development to reduce costs")
                
                elif service == "Amazon S3":
                    if service_config.get('storage_class') == 'Standard' and service_config.get('storage_gb', 0) > 1000:
                        st.info(f"**{service}**: Consider Intelligent-Tiering for automatic cost optimization")
        
        # EXPORT CONFIGURATION
        st.header("📤 Export Configuration")
        
        export_data = {
            "timeline_config": timeline_config,
            "requirements": {
                "workload_complexity": workload_complexity,
                "performance_tier": performance_tier,
                "scalability_needs": scalability_needs,
                "availability_requirements": availability_requirements
            },
            "services": {
                service: {
                    "config": config["config"],
                    "pricing": {
                        "base_monthly_cost": config["pricing"]["base_monthly_cost"],
                        "adjusted_monthly_cost": config["pricing"]["adjusted_monthly_cost"],
                        "discounted_monthly_cost": config["pricing"]["discounted_monthly_cost"],
                        "total_timeline_cost": config["pricing"]["total_timeline_cost"],
                        "yearly_breakdown": config["pricing"]["yearly_data"]
                    }
                }
                for service, config in st.session_state.configurations.items()
            },
            "summary": {
                "total_timeline_cost": st.session_state.total_cost,
                "average_monthly_cost": st.session_state.total_cost / timeline_config["total_months"] if timeline_config["total_months"] > 0 else 0,
                "average_yearly_cost": st.session_state.total_cost / timeline_config["years"] if timeline_config["years"] > 0 else 0,
                "services_count": len(st.session_state.configurations),
                "timeline_period": timeline_config["timeline_type"],
                "generated_at": datetime.now().isoformat()
            }
        }
        
        st.download_button(
            "📥 Download Complete Configuration",
            data=json.dumps(export_data, indent=2),
            file_name=f"aws_architecture_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_config"
        )

if __name__ == "__main__":
    main()