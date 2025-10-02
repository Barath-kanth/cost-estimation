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
    """Generate AWS architecture diagrams automatically"""
    
    # Map service names to diagram icons
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
        """Get the appropriate icon class for a service"""
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
            "Bedrock": Sagemaker,  # Using Sagemaker as placeholder for Bedrock
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
        """Generate AWS architecture diagram based on selected services"""
        if not DIAGRAMS_AVAILABLE:
            return None
        
        try:
            # Create temporary directory for diagram
            temp_dir = tempfile.mkdtemp()
            diagram_path = os.path.join(temp_dir, "aws_architecture")
            
            # Create diagram with custom attributes
            with Diagram(
                "AWS Cloud Architecture",
                filename=diagram_path,
                show=False,
                direction="LR",
                graph_attr={
                    "fontsize": "14",
                    "bgcolor": "white",
                    "pad": "0.5",
                    "splines": "ortho"
                }
            ):
                # Group services by category
                service_nodes = {}
                
                for category, services in selected_services.items():
                    if services:  # Only create cluster if there are services
                        with Cluster(category):
                            for service in services:
                                icon_class = ArchitectureDiagramGenerator.get_icon_class(service)
                                
                                # Get configuration details if available
                                config = configurations.get(service, {}).get('config', {})
                                
                                # Create label with key details
                                label = service
                                if service == "Amazon EC2" and config:
                                    instance_count = config.get('instance_count', 1)
                                    instance_type = config.get('instance_type', 't3.micro')
                                    label = f"{service}\n{instance_count}x {instance_type}"
                                elif service == "Amazon RDS" and config:
                                    instance_type = config.get('instance_type', 'db.t3.micro')
                                    label = f"{service}\n{instance_type}"
                                elif service == "Amazon S3" and config:
                                    storage_gb = config.get('storage_gb', 100)
                                    label = f"{service}\n{storage_gb}GB"
                                
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
            return None
    
    @staticmethod
    def _create_service_connections(service_nodes: Dict, selected_services: Dict):
        """Create logical connections between AWS services"""
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
                        connections.append((compute, db, "queries"))
        
        # EC2 -> S3
        if "Amazon EC2" in all_services and "Amazon S3" in all_services:
            connections.append(("Amazon EC2", "Amazon S3", "stores"))
        
        # Lambda -> S3
        if "AWS Lambda" in all_services and "Amazon S3" in all_services:
            connections.append(("AWS Lambda", "Amazon S3", "reads/writes"))
        
        # WAF -> CloudFront/ELB
        if "AWS WAF" in all_services:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing"]:
                if frontend in all_services:
                    connections.append(("AWS WAF", frontend, "protects"))
        
        # EC2 -> ElastiCache
        if "Amazon EC2" in all_services and "Amazon ElastiCache" in all_services:
            connections.append(("Amazon EC2", "Amazon ElastiCache", "caches"))
        
        # SageMaker/Bedrock -> S3
        for ml_service in ["Amazon SageMaker", "Amazon Bedrock"]:
            if ml_service in all_services and "Amazon S3" in all_services:
                connections.append((ml_service, "Amazon S3", "data"))
        
        # Create edges
        for source, target, label in connections:
            if source in service_nodes and target in service_nodes:
                service_nodes[source] >> Edge(label=label) >> service_nodes[target]

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

def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.write("**Instance Configuration**")
        
        instance_families = {
            "General Purpose": {
                "t3.micro": {"vCPU": 2, "Memory": 1, "Description": "Burstable, low cost"},
                "t3.small": {"vCPU": 2, "Memory": 2, "Description": "Burstable, small workloads"},
                "t3.medium": {"vCPU": 2, "Memory": 4, "Description": "Burstable, medium workloads"},
                "m5.large": {"vCPU": 2, "Memory": 8, "Description": "General purpose, balanced"},
                "m5.xlarge": {"vCPU": 4, "Memory": 16, "Description": "General purpose, high performance"}
            },
            "Compute Optimized": {
                "c5.large": {"vCPU": 2, "Memory": 4, "Description": "Compute intensive workloads"},
                "c5.xlarge": {"vCPU": 4, "Memory": 8, "Description": "High performance computing"},
                "c5.2xlarge": {"vCPU": 8, "Memory": 16, "Description": "Heavy computational loads"}
            },
            "Memory Optimized": {
                "r5.large": {"vCPU": 2, "Memory": 16, "Description": "Memory intensive applications"},
                "r5.xlarge": {"vCPU": 4, "Memory": 32, "Description": "High memory workloads"},
                "r5.2xlarge": {"vCPU": 8, "Memory": 64, "Description": "Memory optimized enterprise apps"}
            }
        }
        
        family = st.selectbox(
            "Instance Family",
            list(instance_families.keys()),
            help="Choose instance family based on workload type",
            key=f"{key_prefix}_family"
        )
        
        instance_types = list(instance_families[family].keys())
        selected_type = st.selectbox(
            "Instance Type",
            instance_types,
            key=f"{key_prefix}_type"
        )
        
        description = ""
        if family in instance_families and selected_type in instance_families[family]:
            description = instance_families[family][selected_type]["Description"]
        
        st.caption(f"*{description}*")
        
        if family in instance_families and selected_type in instance_families[family]:
            specs = instance_families[family][selected_type]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("vCPU", specs["vCPU"])
            with col2:
                st.metric("Memory (GiB)", specs["Memory"])
            with col3:
                st.metric("Type", family)
        
        col1, col2 = st.columns(2)
        with col1:
            instance_count = st.number_input("Number of Instances", 1, 100, 1, key=f"{key_prefix}_count")
        with col2:
            volume_type = st.selectbox(
                "EBS Volume Type",
                ["gp3", "gp2", "io1", "io2", "st1", "sc1"],
                key=f"{key_prefix}_volume_type",
                help="gp3: General Purpose SSD, io1/io2: Provisioned IOPS SSD"
            )
        
        storage_gb = st.slider("EBS Storage (GB)", 8, 16384, 30, key=f"{key_prefix}_storage")
        
        config.update({
            "instance_type": selected_type,
            "instance_count": instance_count,
            "storage_gb": storage_gb,
            "volume_type": volume_type
        })
        
    elif service == "Amazon RDS":
        st.write("**Database Configuration**")
        
        database_engines = {
            "PostgreSQL": {"Description": "Open source relational database"},
            "MySQL": {"Description": "Popular open source database"},
            "Aurora MySQL": {"Description": "MySQL-compatible, high performance"},
            "SQL Server": {"Description": "Microsoft SQL Server"}
        }
        
        engine = st.selectbox(
            "Database Engine",
            list(database_engines.keys()),
            key=f"{key_prefix}_engine"
        )
        
        engine_description = ""
        if engine in database_engines:
            engine_description = database_engines[engine]["Description"]
        
        st.caption(f"*{engine_description}*")
        
        rds_instance_types = {
            "db.t3.micro": {"vCPU": 2, "Memory": 1, "Description": "Development & test"},
            "db.t3.small": {"vCPU": 2, "Memory": 2, "Description": "Small workloads"},
            "db.t3.medium": {"vCPU": 2, "Memory": 4, "Description": "Medium workloads"},
            "db.m5.large": {"vCPU": 2, "Memory": 8, "Description": "Production workloads"},
            "db.r5.large": {"vCPU": 2, "Memory": 16, "Description": "Memory optimized"}
        }
        
        selected_type = st.selectbox(
            "Instance Type",
            list(rds_instance_types.keys()),
            key=f"{key_prefix}_type"
        )
        
        instance_description = ""
        if selected_type in rds_instance_types:
            instance_description = rds_instance_types[selected_type]["Description"]
        
        st.caption(f"*{instance_description}*")
        
        if selected_type in rds_instance_types:
            specs = rds_instance_types[selected_type]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("vCPU", specs["vCPU"])
            with col2:
                st.metric("Memory (GiB)", specs["Memory"])
        
        col1, col2 = st.columns(2)
        with col1:
            storage = st.slider("Storage (GB)", 20, 65536, 100, key=f"{key_prefix}_storage")
            backup_retention = st.slider("Backup Retention (Days)", 0, 35, 7, key=f"{key_prefix}_backup")
        with col2:
            multi_az = st.checkbox("Multi-AZ Deployment", key=f"{key_prefix}_multiaz")
            encryption = st.checkbox("Encryption at Rest", value=True, key=f"{key_prefix}_encryption")
        
        config.update({
            "engine": engine,
            "instance_type": selected_type,
            "storage_gb": storage,
            "multi_az": multi_az,
            "backup_retention": backup_retention,
            "encryption": encryption
        })
    
    elif service == "Amazon S3":
        st.write("**Storage Configuration**")
        
        storage_classes = {
            "Standard": {"Description": "Frequently accessed data"},
            "Intelligent-Tiering": {"Description": "Automatically optimizes costs"},
            "Standard-IA": {"Description": "Infrequently accessed data"},
            "One Zone-IA": {"Description": "Infrequently accessed, single AZ"},
            "Glacier": {"Description": "Archive data, retrieval in minutes-hours"},
            "Glacier Deep Archive": {"Description": "Lowest cost, retrieval in hours"}
        }
        
        storage_class = st.selectbox(
            "Storage Class",
            list(storage_classes.keys()),
            key=f"{key_prefix}_class"
        )
        
        # Get description safely
        storage_description = ""
        if storage_class in storage_classes:
            storage_description = storage_classes[storage_class]["Description"]
        
        st.caption(f"*{storage_description}*")
        
        storage_gb = st.slider("Storage (GB)", 1, 1000000, 100, key=f"{key_prefix}_storage")
        
        config.update({
            "storage_class": storage_class,
            "storage_gb": storage_gb
        })
    
    elif service == "AWS Lambda":
        st.write("**Lambda Function Configuration**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            memory_mb = st.selectbox(
                "Memory (MB)",
                [128, 256, 512, 1024, 2048, 3008, 4096, 5120, 6144, 7168, 8192, 9216, 10240],
                index=0,
                key=f"{key_prefix}_memory"
            )
        with col2:
            requests = st.number_input(
                "Monthly Requests",
                min_value=1000,
                max_value=100000000,
                value=1000000,
                step=100000,
                key=f"{key_prefix}_requests"
            )
        with col3:
            duration_ms = st.number_input(
                "Average Duration (ms)",
                min_value=100,
                max_value=90000,
                value=1000,
                step=100,
                key=f"{key_prefix}_duration"
            )
        
        config.update({
            "memory_mb": memory_mb,
            "requests_per_month": requests,
            "avg_duration_ms": duration_ms
        })
    
    elif service == "Amazon ECS":
        st.write("**ECS Cluster Configuration**")
        
        col1, col2 = st.columns(2)
        with col1:
            cluster_type = st.selectbox(
                "Cluster Type",
                ["Fargate", "EC2"],
                key=f"{key_prefix}_cluster_type"
            )
            
            if cluster_type == "Fargate":
                cpu_units = st.selectbox(
                    "CPU Units",
                    [256, 512, 1024, 2048, 4096],
                    index=2,
                    key=f"{key_prefix}_fargate_cpu"
                )
                
                memory_gb = st.selectbox(
                    "Memory (GB)",
                    [0.5, 1, 2, 4, 8, 16, 30],
                    index=3,
                    key=f"{key_prefix}_fargate_memory"
                )
                
                config.update({
                    "cluster_type": cluster_type,
                    "cpu_units": cpu_units,
                    "memory_gb": memory_gb
                })
            else:
                instance_count = st.number_input(
                    "EC2 Instance Count",
                    min_value=1,
                    max_value=20,
                    value=2,
                    key=f"{key_prefix}_ec2_count"
                )
                
                config.update({
                    "cluster_type": cluster_type,
                    "instance_count": instance_count
                })
        
        with col2:
            service_count = st.number_input(
                "Number of Services",
                min_value=1,
                max_value=50,
                value=3,
                key=f"{key_prefix}_service_count"
            )
            
            avg_tasks_per_service = st.slider(
                "Average Tasks per Service",
                min_value=1,
                max_value=20,
                value=2,
                key=f"{key_prefix}_tasks"
            )
            
            config.update({
                "service_count": service_count,
                "avg_tasks_per_service": avg_tasks_per_service
            })
    
    elif service == "Amazon CloudFront":
        st.write("**CDN Configuration**")
        
        col1, col2 = st.columns(2)
        with col1:
            data_transfer_tb = st.slider(
                "Monthly Data Transfer (TB)",
                min_value=1,
                max_value=1000,
                value=50,
                key=f"{key_prefix}_transfer"
            )
            
            requests_million = st.slider(
                "Monthly Requests (Millions)",
                min_value=1,
                max_value=1000,
                value=10,
                key=f"{key_prefix}_cdn_requests"
            )
        
        with col2:
            origin_type = st.selectbox(
                "Origin Type",
                ["S3", "EC2", "ALB", "Custom"],
                key=f"{key_prefix}_origin"
            )
            
            waf_enabled = st.checkbox(
                "Enable WAF",
                value=True,
                key=f"{key_prefix}_waf"
            )
        
        config.update({
            "data_transfer_tb": data_transfer_tb,
            "requests_million": requests_million,
            "origin_type": origin_type,
            "waf_enabled": waf_enabled
        })
    
    elif service == "Amazon DynamoDB":
        st.write("**DynamoDB Configuration**")
        
        capacity_mode = st.radio(
            "Capacity Mode",
            ["Provisioned", "On-Demand"],
            key=f"{key_prefix}_capacity_mode"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if capacity_mode == "Provisioned":
                read_capacity = st.number_input(
                    "Read Capacity Units",
                    min_value=1,
                    max_value=100000,
                    value=10,
                    key=f"{key_prefix}_read_capacity"
                )
                
                write_capacity = st.number_input(
                    "Write Capacity Units",
                    min_value=1,
                    max_value=100000,
                    value=10,
                    key=f"{key_prefix}_write_capacity"
                )
                
                config.update({
                    "capacity_mode": capacity_mode,
                    "read_capacity": read_capacity,
                    "write_capacity": write_capacity
                })
            else:
                config.update({
                    "capacity_mode": capacity_mode
                })
        
        with col2:
            storage_gb = st.slider(
                "Storage (GB)",
                min_value=1,
                max_value=10000,
                value=100,
                key=f"{key_prefix}_dynamo_storage"
            )
            
            backup_enabled = st.checkbox(
                "Enable Point-in-Time Recovery",
                value=True,
                key=f"{key_prefix}_backup"
            )
        
        config.update({
            "storage_gb": storage_gb,
            "backup_enabled": backup_enabled
        })
    
    elif service == "Elastic Load Balancing":
        st.write("**Load Balancer Configuration**")
        
        lb_type = st.selectbox(
            "Load Balancer Type",
            ["Application Load Balancer", "Network Load Balancer"],
            key=f"{key_prefix}_lb_type"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            lcu_count = st.slider(
                "Estimated LCU Hours/Month" if lb_type == "Application Load Balancer" else "Estimated NLCU Hours/Month",
                min_value=100,
                max_value=1000000,
                value=10000,
                key=f"{key_prefix}_lcu"
            )
            
        with col2:
            data_processed_tb = st.slider(
                "Data Processed (TB/Month)",
                min_value=1,
                max_value=1000,
                value=10,
                key=f"{key_prefix}_lb_data"
            )
        
        config.update({
            "lb_type": lb_type,
            "lcu_count": lcu_count,
            "data_processed_tb": data_processed_tb
        })
    
    elif service == "Amazon VPC":
        st.write("**VPC Configuration**")
        
        col1, col2 = st.columns(2)
        with col1:
            vpc_count = st.number_input(
                "Number of VPCs",
                min_value=1,
                max_value=10,
                value=1,
                key=f"{key_prefix}_vpc_count"
            )
            
            nat_gateways = st.number_input(
                "NAT Gateways",
                min_value=0,
                max_value=20,
                value=2,
                key=f"{key_prefix}_nat"
            )
        
        with col2:
            vpc_endpoints = st.number_input(
                "VPC Endpoints",
                min_value=0,
                max_value=50,
                value=5,
                key=f"{key_prefix}_endpoints"
            )
            
            vpn_connections = st.number_input(
                "VPN Connections",
                min_value=0,
                max_value=10,
                value=0,
                key=f"{key_prefix}_vpn"
            )
        
        config.update({
            "vpc_count": vpc_count,
            "nat_gateways": nat_gateways,
            "vpc_endpoints": vpc_endpoints,
            "vpn_connections": vpn_connections
        })
    
    elif service == "AWS WAF":
        st.write("**WAF Configuration**")
        
        col1, col2 = st.columns(2)
        with col1:
            web_acls = st.number_input(
                "Web ACLs",
                min_value=1,
                max_value=100,
                value=2,
                key=f"{key_prefix}_web_acls"
            )
            
            rules_per_acl = st.slider(
                "Rules per Web ACL",
                min_value=1,
                max_value=150,
                value=10,
                key=f"{key_prefix}_rules"
            )
        
        with col2:
            requests_billion = st.slider(
                "Monthly Requests (Billions)",
                min_value=0.1,
                max_value=100.0,
                value=1.0,
                step=0.1,
                key=f"{key_prefix}_waf_requests"
            )
            
            managed_rules = st.checkbox(
                "Use AWS Managed Rules",
                value=True,
                key=f"{key_prefix}_managed_rules"
            )
        
        config.update({
            "web_acls": web_acls,
            "rules_per_acl": rules_per_acl,
            "requests_billion": requests_billion,
            "managed_rules": managed_rules
        })
    
    elif service == "Amazon SageMaker":
        st.write("**SageMaker Configuration**")
        
        usage_type = st.selectbox(
            "Primary Usage",
            ["Training", "Inference", "Notebooks", "All"],
            key=f"{key_prefix}_sagemaker_usage"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if usage_type in ["Training", "All"]:
                training_hours = st.slider(
                    "Training Hours/Month",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    key=f"{key_prefix}_training_hours"
                )
                config["training_hours"] = training_hours
            
            if usage_type in ["Inference", "All"]:
                inference_hours = st.slider(
                    "Inference Hours/Month",
                    min_value=100,
                    max_value=10000,
                    value=1000,
                    key=f"{key_prefix}_inference_hours"
                )
                config["inference_hours"] = inference_hours
        
        with col2:
            if usage_type in ["Notebooks", "All"]:
                notebook_hours = st.slider(
                    "Notebook Instance Hours/Month",
                    min_value=10,
                    max_value=500,
                    value=160,
                    key=f"{key_prefix}_notebook_hours"
                )
                config["notebook_hours"] = notebook_hours
            
            storage_gb = st.slider(
                "Model/Data Storage (GB)",
                min_value=10,
                max_value=10000,
                value=500,
                key=f"{key_prefix}_sagemaker_storage"
            )
        
        config.update({
            "usage_type": usage_type,
            "storage_gb": storage_gb
        })
    
    elif service == "Amazon Bedrock":
        st.write("**Bedrock Configuration**")
        
        model_family = st.selectbox(
            "Primary Model Family",
            ["Claude", "Jurassic", "Command", "Titan", "Multiple"],
            key=f"{key_prefix}_model_family"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            input_tokens_million = st.slider(
                "Input Tokens/Month (Millions)",
                min_value=1,
                max_value=1000,
                value=10,
                key=f"{key_prefix}_input_tokens"
            )
            
            output_tokens_million = st.slider(
                "Output Tokens/Month (Millions)",
                min_value=1,
                max_value=1000,
                value=5,
                key=f"{key_prefix}_output_tokens"
            )
        
        with col2:
            custom_models = st.number_input(
                "Custom Models",
                min_value=0,
                max_value=50,
                value=0,
                key=f"{key_prefix}_custom_models"
            )
            
            fine_tuning_hours = st.slider(
                "Fine-tuning Hours/Month",
                min_value=0,
                max_value=500,
                value=0,
                key=f"{key_prefix}_fine_tuning"
            )
        
        config.update({
            "model_family": model_family,
            "input_tokens_million": input_tokens_million,
            "output_tokens_million": output_tokens_million,
            "custom_models": custom_models,
            "fine_tuning_hours": fine_tuning_hours
        })

    # Region selection for all services
    config["region"] = st.selectbox(
        "Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"],
        key=f"{key_prefix}_region"
    )
    
    return config

def render_yearly_visualization(yearly_data: Dict, service_name: str):
    """Render yearly visualization for service costs using Streamlit native charts"""
    if not yearly_data or "years" not in yearly_data or not yearly_data["years"]:
        st.info(f"No yearly data available for {service_name}")
        return
    
    # Display yearly breakdown table
    st.subheader(f"📅 {service_name} - Yearly Cost Breakdown")
    
    # Create DataFrame for display
    yearly_df = pd.DataFrame({
        'Year': yearly_data["years"],
        'Monthly Cost': [f'${cost:,.2f}' for cost in yearly_data["monthly_costs"]],
        'Yearly Cost': [f'${cost:,.2f}' for cost in yearly_data["yearly_costs"]],
        'Cumulative Cost': [f'${cost:,.2f}' for cost in yearly_data["cumulative_costs"]]
    })
    
    # Display table
    st.dataframe(yearly_df, use_container_width=True)
    
    # Display metrics with safe division
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${yearly_data['total_cost']:,.2f}")
    with col2:
        # Safe division - avoid division by zero
        if len(yearly_data["years"]) > 0:
            avg_yearly = yearly_data['total_cost'] / len(yearly_data["years"])
            st.metric("Average Yearly", f"${avg_yearly:,.2f}")
        else:
            st.metric("Average Yearly", "$0.00")
    with col3:
        if yearly_data["yearly_costs"]:
            st.metric("Final Yearly", f"${yearly_data['yearly_costs'][-1]:,.2f}")
        else:
            st.metric("Final Yearly", "$0.00")
    
    # Create simple bar chart using Streamlit
    st.subheader("📊 Yearly Cost Chart")
    chart_df = pd.DataFrame({
        'Year': yearly_data["years"],
        'Yearly Cost ($)': yearly_data["yearly_costs"]
    })
    st.bar_chart(chart_df.set_index('Year'))

# Update the DynamicPricingEngine to include pricing calculations for additional services
class DynamicPricingEngine:
    @staticmethod
    def calculate_service_price(service: str, config: Dict, timeline_config: Dict) -> Dict:
        """Calculate service price with dynamic factors and timeline"""
        base_price = DynamicPricingEngine._calculate_base_price(service, config)
        
        # Apply usage pattern multiplier
        adjusted_price = base_price * timeline_config["pattern_multiplier"]
        
        # Apply commitment discount
        discounted_price = adjusted_price * timeline_config["commitment_discount"]
        
        # Calculate yearly breakdown (handle case when years is 0)
        if timeline_config["years"] > 0:
            yearly_data = YearlyTimelineCalculator.calculate_yearly_costs(
                discounted_price, 
                timeline_config["years"],
                timeline_config["growth_rate"]
            )
        else:
            yearly_data = {"years": [], "yearly_costs": [], "monthly_costs": [], "cumulative_costs": [], "total_cost": 0.0}
        
        # Calculate detailed monthly timeline
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
            
            # Sample pricing
            instance_prices = {
                't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                'm5.large': 0.096, 'm5.xlarge': 0.192,
                'c5.large': 0.085, 'c5.xlarge': 0.17,
                'r5.large': 0.126, 'r5.xlarge': 0.252
            }
            
            base_price = instance_prices.get(instance_type, 0.1) * 730 * instance_count
            
            # Add storage costs
            storage_gb = config.get('storage_gb', 30)
            volume_type = config.get('volume_type', 'gp3')
            storage_price_per_gb = {
                'gp3': 0.08, 'gp2': 0.10, 'io1': 0.125, 'io2': 0.125,
                'st1': 0.045, 'sc1': 0.015
            }
            base_price += storage_gb * storage_price_per_gb.get(volume_type, 0.08)
            
            return base_price
            
        elif service == "Amazon RDS":
            engine = config.get('engine', 'PostgreSQL')
            instance_type = config.get('instance_type', 'db.t3.micro')
            
            # Sample RDS pricing
            rds_prices = {
                'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
                'db.m5.large': 0.17, 'db.r5.large': 0.24
            }
            
            base_price = rds_prices.get(instance_type, 0.1) * 730
            
            # Add storage
            storage_gb = config.get('storage_gb', 20)
            base_price += storage_gb * 0.115
            
            # Multi-AZ multiplier
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
        
        elif service == "Amazon ECS":
            cluster_type = config.get('cluster_type', 'Fargate')
            
            if cluster_type == 'Fargate':
                cpu_units = config.get('cpu_units', 1024)
                memory_gb = config.get('memory_gb', 2)
                service_count = config.get('service_count', 3)
                avg_tasks = config.get('avg_tasks_per_service', 2)
                
                # Fargate pricing per vCPU and GB
                cpu_price_per_hour = 0.04048  # per vCPU
                memory_price_per_hour = 0.004445  # per GB
                
                total_tasks = service_count * avg_tasks
                monthly_cost = total_tasks * 730 * (cpu_units/1024 * cpu_price_per_hour + memory_gb * memory_price_per_hour)
                return monthly_cost
            else:
                # EC2 pricing would be similar to regular EC2 instances
                instance_count = config.get('instance_count', 2)
                return instance_count * 50  # Simplified pricing
        
        elif service == "Amazon CloudFront":
            data_transfer_tb = config.get('data_transfer_tb', 50)
            requests_million = config.get('requests_million', 10)
            
            # Simplified CloudFront pricing
            data_transfer_cost = data_transfer_tb * 0.085  # $0.085 per GB
            request_cost = requests_million * 0.0075  # $0.0075 per 10,000 requests
            
            return data_transfer_cost + request_cost
        
        elif service == "Amazon DynamoDB":
            capacity_mode = config.get('capacity_mode', 'Provisioned')
            storage_gb = config.get('storage_gb', 100)
            
            if capacity_mode == 'Provisioned':
                read_capacity = config.get('read_capacity', 10)
                write_capacity = config.get('write_capacity', 10)
                
                read_cost = read_capacity * 0.00013 * 730  # per hour
                write_cost = write_capacity * 0.00065 * 730  # per hour
                storage_cost = storage_gb * 0.25  # per GB-month
                
                return read_cost + write_cost + storage_cost
            else:
                # On-demand pricing
                return storage_gb * 0.25 + 100  # Simplified on-demand cost
        
        elif service == "Elastic Load Balancing":
            lb_type = config.get('lb_type', 'Application Load Balancer')
            lcu_count = config.get('lcu_count', 10000)
            data_processed_tb = config.get('data_processed_tb', 10)
            
            if lb_type == 'Application Load Balancer':
                lcu_cost = lcu_count * 0.008  # per LCU-hour
                return lcu_cost + (data_processed_tb * 0.01)
            else:
                nlu_cost = lcu_count * 0.006  # per NLCU-hour
                return nlu_cost + (data_processed_tb * 0.01)
        
        elif service == "Amazon VPC":
            vpc_count = config.get('vpc_count', 1)
            nat_gateways = config.get('nat_gateways', 2)
            vpc_endpoints = config.get('vpc_endpoints', 5)
            vpn_connections = config.get('vpn_connections', 0)
            
            # VPC is free, but associated services have costs
            nat_cost = nat_gateways * 0.045 * 730  # per hour
            endpoint_cost = vpc_endpoints * 0.01 * 730  # per hour
            vpn_cost = vpn_connections * 0.05 * 730  # per hour
            
            return nat_cost + endpoint_cost + vpn_cost
        
        elif service == "AWS WAF":
            web_acls = config.get('web_acls', 2)
            rules_per_acl = config.get('rules_per_acl', 10)
            requests_billion = config.get('requests_billion', 1.0)
            managed_rules = config.get('managed_rules', True)
            
            web_acl_cost = web_acls * 5.00  # per month
            rule_cost = web_acls * rules_per_acl * 1.00  # per rule per month
            request_cost = requests_billion * 0.60  # per million requests
            managed_rule_cost = 1.00 if managed_rules else 0  # per rule per month
            
            return web_acl_cost + rule_cost + request_cost + managed_rule_cost
        
        elif service == "Amazon SageMaker":
            usage_type = config.get('usage_type', 'Training')
            storage_gb = config.get('storage_gb', 500)
            
            base_cost = 0
            
            if usage_type in ['Training', 'All']:
                training_hours = config.get('training_hours', 100)
                base_cost += training_hours * 0.50  # ml.m5.xlarge instance
            
            if usage_type in ['Inference', 'All']:
                inference_hours = config.get('inference_hours', 1000)
                base_cost += inference_hours * 0.10  # ml.m5.large instance
            
            if usage_type in ['Notebooks', 'All']:
                notebook_hours = config.get('notebook_hours', 160)
                base_cost += notebook_hours * 0.077  # ml.t3.medium instance
            
            base_cost += storage_gb * 0.23  # EBS storage
            
            return base_cost
        
        elif service == "Amazon Bedrock":
            input_tokens_million = config.get('input_tokens_million', 10)
            output_tokens_million = config.get('output_tokens_million', 5)
            custom_models = config.get('custom_models', 0)
            fine_tuning_hours = config.get('fine_tuning_hours', 0)
            
            # Simplified Bedrock pricing (Claude model pricing)
            input_cost = input_tokens_million * 0.80  # per million tokens
            output_cost = output_tokens_million * 4.00  # per million tokens
            custom_model_cost = custom_models * 100  # per model per month
            fine_tuning_cost = fine_tuning_hours * 50  # per hour
            
            return input_cost + output_cost + custom_model_cost + fine_tuning_cost
        
        # Add more services as needed...
        return 0.0

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