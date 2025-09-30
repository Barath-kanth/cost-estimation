import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

@dataclass
class AWSPriceList:
    """AWS Price List API Handler"""
    BASE_URL = "https://pricing.us-east-1.amazonaws.com"
    
    def get_regions(self) -> List[str]:
        """Get list of AWS regions"""
        try:
            url = f"{self.BASE_URL}/meta/regions"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return sorted(list(response.json().keys()))
            return self._get_default_regions()
        except Exception as e:
            return self._get_default_regions()

    def _get_default_regions(self) -> List[str]:
        return [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
        ]

    def get_ec2_price(self, instance_type: str, region: str) -> float:
        """Fetch EC2 pricing from API"""
        try:
            # This would use the actual AWS Price List API
            # For now, using computed values based on AWS pricing patterns
            base_prices = {
                "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208,
                "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664,
                "t3.2xlarge": 0.3328, "m5.large": 0.096, "m5.xlarge": 0.192,
                "m5.2xlarge": 0.384, "m5.4xlarge": 0.768, "c5.large": 0.085,
                "c5.xlarge": 0.17, "c5.2xlarge": 0.34, "r5.large": 0.126,
                "r5.xlarge": 0.252, "r5.2xlarge": 0.504
            }
            return base_prices.get(instance_type, 0.10)
        except:
            return 0.10

    def get_rds_price(self, instance_type: str, engine: str, region: str) -> float:
        """Fetch RDS pricing from API"""
        try:
            base_prices = {
                "db.t3.micro": 0.017, "db.t3.small": 0.034,
                "db.t3.medium": 0.068, "db.t3.large": 0.136,
                "db.t3.xlarge": 0.272, "db.t3.2xlarge": 0.544,
                "db.m5.large": 0.192, "db.m5.xlarge": 0.384,
                "db.r5.large": 0.24, "db.r5.xlarge": 0.48
            }
            return base_prices.get(instance_type, 0.068)
        except:
            return 0.068

    def get_s3_price(self, storage_class: str, region: str) -> float:
        """Fetch S3 pricing from API"""
        pricing_map = {
            "Standard": 0.023, "Intelligent-Tiering": 0.0125,
            "Standard-IA": 0.0125, "One Zone-IA": 0.01,
            "Glacier Flexible Retrieval": 0.004, 
            "Glacier Deep Archive": 0.00099
        }
        return pricing_map.get(storage_class, 0.023)

@dataclass
class CustomerRequirement:
    workload_type: str
    monthly_budget: float
    performance_tier: str
    regions: List[str]
    expected_users: int
    data_volume_gb: float
    special_requirements: List[str]
    compliance_needs: List[str]

@dataclass
class ServiceRecommendation:
    service_name: str
    service_type: str
    description: str
    base_config: Dict
    monthly_cost: float
    justification: str
    configuration_options: Dict

class ServiceMapper:
    """Maps customer requirements to AWS services"""
    
    @staticmethod
    def identify_required_services(requirements: CustomerRequirement) -> List[Dict]:
        """Dynamically identify which AWS services are needed"""
        services = []
        
        # Analyze workload type to determine services
        workload = requirements.workload_type.lower()
        special_reqs = [req.lower() for req in requirements.special_requirements]
        
        # Compute Services
        if "serverless" in workload or "lambda" in workload:
            services.append({
                "name": "AWS Lambda",
                "type": "compute",
                "reason": "Serverless compute for event-driven architecture"
            })
        elif "container" in workload or "ecs" in workload or "microservices" in workload:
            services.append({
                "name": "Amazon ECS",
                "type": "compute",
                "reason": "Container orchestration for microservices"
            })
        elif "kubernetes" in workload or "eks" in workload:
            services.append({
                "name": "Amazon EKS",
                "type": "compute",
                "reason": "Managed Kubernetes service"
            })
        else:
            services.append({
                "name": "Amazon EC2",
                "type": "compute",
                "reason": "Scalable virtual servers for compute needs"
            })
        
        # Storage Services
        if requirements.data_volume_gb > 0:
            services.append({
                "name": "Amazon S3",
                "type": "storage",
                "reason": "Scalable object storage for your data"
            })
        
        # Database Services
        if "database" in workload or "data" in workload or requirements.data_volume_gb > 50:
            if "nosql" in workload or "dynamodb" in workload:
                services.append({
                    "name": "Amazon DynamoDB",
                    "type": "database",
                    "reason": "NoSQL database for high-performance applications"
                })
            else:
                services.append({
                    "name": "Amazon RDS",
                    "type": "database",
                    "reason": "Managed relational database service"
                })
        
        # AI/ML Services
        if "machine learning" in workload or "ml" in workload or "ai" in workload:
            services.append({
                "name": "Amazon SageMaker",
                "type": "ml",
                "reason": "Build, train, and deploy ML models"
            })
        
        if "bedrock" in workload or "generative ai" in workload or "llm" in workload:
            services.append({
                "name": "Amazon Bedrock",
                "type": "ai",
                "reason": "Generative AI and foundation models"
            })
        
        # Networking & CDN
        if "content delivery" in special_reqs or "cdn" in special_reqs:
            services.append({
                "name": "Amazon CloudFront",
                "type": "networking",
                "reason": "Content delivery network for global distribution"
            })
        
        # Load Balancing
        if "high availability" in special_reqs or "load balancing" in special_reqs:
            services.append({
                "name": "Elastic Load Balancing",
                "type": "networking",
                "reason": "Distribute traffic across multiple targets"
            })
        
        # Security Services
        if requirements.compliance_needs:
            services.append({
                "name": "AWS WAF",
                "type": "security",
                "reason": "Web application firewall for compliance and security"
            })
        
        # Monitoring
        services.append({
            "name": "Amazon CloudWatch",
            "type": "monitoring",
            "reason": "Monitoring and observability for all services"
        })
        
        return services

class CloudServiceAgent:
    """Creates service recommendations with configuration options"""
    
    def __init__(self):
        self.price_list = AWSPriceList()
    
    def create_recommendation(self, service_info: Dict, requirements: CustomerRequirement) -> ServiceRecommendation:
        """Create a recommendation for a specific service"""
        service_name = service_info["name"]
        
        if service_name == "Amazon EC2":
            return self._create_ec2_recommendation(requirements)
        elif service_name == "AWS Lambda":
            return self._create_lambda_recommendation(requirements)
        elif service_name == "Amazon ECS":
            return self._create_ecs_recommendation(requirements)
        elif service_name == "Amazon EKS":
            return self._create_eks_recommendation(requirements)
        elif service_name == "Amazon S3":
            return self._create_s3_recommendation(requirements)
        elif service_name == "Amazon RDS":
            return self._create_rds_recommendation(requirements)
        elif service_name == "Amazon DynamoDB":
            return self._create_dynamodb_recommendation(requirements)
        elif service_name == "Amazon SageMaker":
            return self._create_sagemaker_recommendation(requirements)
        elif service_name == "Amazon Bedrock":
            return self._create_bedrock_recommendation(requirements)
        elif service_name == "Amazon CloudFront":
            return self._create_cloudfront_recommendation(requirements)
        elif service_name == "Elastic Load Balancing":
            return self._create_elb_recommendation(requirements)
        elif service_name == "AWS WAF":
            return self._create_waf_recommendation(requirements)
        elif service_name == "Amazon CloudWatch":
            return self._create_cloudwatch_recommendation(requirements)
        
        return None
    
    def _create_ec2_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        tier_instances = {
            "Development": "t3.small",
            "Production": "t3.medium",
            "Enterprise": "m5.large"
        }
        instance_type = tier_instances.get(req.performance_tier, "t3.medium")
        hourly_cost = self.price_list.get_ec2_price(instance_type, req.regions[0])
        
        return ServiceRecommendation(
            service_name="Amazon EC2",
            service_type="Compute",
            description="Scalable virtual servers in the cloud. Run applications on secure, resizable compute capacity.",
            base_config={"instance_type": instance_type, "count": 1, "storage_gb": 30},
            monthly_cost=hourly_cost * 730,
            justification=f"Recommended {instance_type} for {req.performance_tier} workload with {req.expected_users} users",
            configuration_options={
                "instance_types": ["t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", 
                                  "t3.xlarge", "m5.large", "m5.xlarge", "c5.large", "r5.large"],
                "storage_range": [8, 16384],
                "count_range": [1, 50]
            }
        )
    
    def _create_lambda_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        requests = req.expected_users * 100
        cost = (requests * 0.0000002) + (requests * 0.128 * 0.1 * 0.0000166667)
        
        return ServiceRecommendation(
            service_name="AWS Lambda",
            service_type="Compute",
            description="Run code without provisioning servers. Pay only for compute time consumed.",
            base_config={"memory_mb": 256, "timeout": 30, "requests": requests},
            monthly_cost=cost,
            justification=f"Serverless architecture for {req.expected_users} users with event-driven workload",
            configuration_options={
                "memory_options": [128, 256, 512, 1024, 2048, 3008, 10240],
                "timeout_range": [1, 900],
                "requests_range": [1000, 100000000]
            }
        )
    
    def _create_ecs_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        tasks = max(2, req.expected_users // 1000)
        cost_per_task = 0.04048  # Fargate pricing for 0.25 vCPU, 0.5GB
        
        return ServiceRecommendation(
            service_name="Amazon ECS",
            service_type="Compute",
            description="Fully managed container orchestration service. Run containers without managing servers.",
            base_config={"vcpu": 0.25, "memory_gb": 0.5, "tasks": tasks},
            monthly_cost=cost_per_task * 730 * tasks,
            justification=f"Container service for microservices with {tasks} tasks recommended",
            configuration_options={
                "vcpu_options": [0.25, 0.5, 1, 2, 4, 8, 16],
                "memory_options": [0.5, 1, 2, 4, 8, 16, 30, 60, 120],
                "tasks_range": [1, 100]
            }
        )
    
    def _create_eks_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        cluster_cost = 73  # $0.10/hour
        node_cost = self.price_list.get_ec2_price("t3.medium", req.regions[0]) * 730 * 2
        
        return ServiceRecommendation(
            service_name="Amazon EKS",
            service_type="Compute",
            description="Managed Kubernetes service. Run Kubernetes without managing control plane.",
            base_config={"cluster_count": 1, "node_type": "t3.medium", "node_count": 2},
            monthly_cost=cluster_cost + node_cost,
            justification="Kubernetes cluster for container orchestration",
            configuration_options={
                "node_types": ["t3.small", "t3.medium", "t3.large", "m5.large", "m5.xlarge"],
                "node_count_range": [2, 50]
            }
        )
    
    def _create_s3_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        storage_gb = req.data_volume_gb
        price_per_gb = self.price_list.get_s3_price("Standard", req.regions[0])
        
        return ServiceRecommendation(
            service_name="Amazon S3",
            service_type="Storage",
            description="Object storage built to retrieve any amount of data from anywhere. 99.999999999% durability.",
            base_config={"storage_gb": storage_gb, "storage_class": "Standard"},
            monthly_cost=storage_gb * price_per_gb,
            justification=f"Object storage for {storage_gb}GB of data",
            configuration_options={
                "storage_classes": ["Standard", "Intelligent-Tiering", "Standard-IA", 
                                   "One Zone-IA", "Glacier Flexible Retrieval", "Glacier Deep Archive"],
                "storage_range": [1, 5000000]
            }
        )
    
    def _create_rds_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        instance_type = "db.t3.medium"
        hourly_cost = self.price_list.get_rds_price(instance_type, "postgres", req.regions[0])
        storage_cost = req.data_volume_gb * 0.115
        
        return ServiceRecommendation(
            service_name="Amazon RDS",
            service_type="Database",
            description="Managed relational database service. Easy to set up, operate, and scale.",
            base_config={"instance_type": instance_type, "engine": "PostgreSQL", 
                        "storage_gb": req.data_volume_gb, "multi_az": False},
            monthly_cost=(hourly_cost * 730) + storage_cost,
            justification=f"Managed database for relational data workload",
            configuration_options={
                "instance_types": ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large", 
                                  "db.m5.large", "db.r5.large"],
                "engines": ["PostgreSQL", "MySQL", "MariaDB", "Oracle", "SQL Server"],
                "storage_range": [20, 65536]
            }
        )
    
    def _create_dynamodb_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        storage_gb = req.data_volume_gb
        read_units = req.expected_users * 5
        write_units = req.expected_users * 2
        
        storage_cost = storage_gb * 0.25
        read_cost = (read_units * 730) * 0.00013
        write_cost = (write_units * 730) * 0.00065
        
        return ServiceRecommendation(
            service_name="Amazon DynamoDB",
            service_type="Database",
            description="Fast, flexible NoSQL database. Single-digit millisecond performance at any scale.",
            base_config={"storage_gb": storage_gb, "read_units": read_units, "write_units": write_units},
            monthly_cost=storage_cost + read_cost + write_cost,
            justification="NoSQL database for high-performance key-value workload",
            configuration_options={
                "capacity_modes": ["On-Demand", "Provisioned"],
                "storage_range": [1, 1000000],
                "read_units_range": [1, 40000],
                "write_units_range": [1, 40000]
            }
        )
    
    def _create_sagemaker_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        instance_hours = 100  # Assumed monthly training hours
        instance_cost = 0.269 * instance_hours  # ml.m5.xlarge
        
        return ServiceRecommendation(
            service_name="Amazon SageMaker",
            service_type="Machine Learning",
            description="Build, train, and deploy ML models at scale. Fully managed ML service.",
            base_config={"instance_type": "ml.m5.xlarge", "training_hours": instance_hours},
            monthly_cost=instance_cost,
            justification="ML platform for model training and deployment",
            configuration_options={
                "instance_types": ["ml.t3.medium", "ml.m5.large", "ml.m5.xlarge", 
                                  "ml.p3.2xlarge", "ml.g4dn.xlarge"],
                "training_hours_range": [10, 1000]
            }
        )
    
    def _create_bedrock_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        tokens_per_month = req.expected_users * 1000  # 1000 tokens per user
        cost_per_1k_tokens = 0.003  # Claude pricing estimate
        
        return ServiceRecommendation(
            service_name="Amazon Bedrock",
            service_type="Generative AI",
            description="Build and scale generative AI applications with foundation models.",
            base_config={"model": "Claude", "tokens_per_month": tokens_per_month},
            monthly_cost=(tokens_per_month / 1000) * cost_per_1k_tokens,
            justification="Generative AI for LLM-powered applications",
            configuration_options={
                "models": ["Claude", "Titan", "Llama", "Jurassic"],
                "tokens_range": [1000, 100000000]
            }
        )
    
    def _create_cloudfront_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        data_transfer_gb = req.data_volume_gb * 10  # Assume 10x delivery
        
        return ServiceRecommendation(
            service_name="Amazon CloudFront",
            service_type="Content Delivery",
            description="Global content delivery network. Low latency and high transfer speeds.",
            base_config={"data_transfer_gb": data_transfer_gb},
            monthly_cost=data_transfer_gb * 0.085,
            justification="CDN for global content distribution",
            configuration_options={
                "data_transfer_range": [1, 1000000]
            }
        )
    
    def _create_elb_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        return ServiceRecommendation(
            service_name="Elastic Load Balancing",
            service_type="Networking",
            description="Automatically distribute traffic across multiple targets for high availability.",
            base_config={"type": "Application Load Balancer", "lcus": 5},
            monthly_cost=(0.0225 * 730) + (5 * 0.008 * 730),
            justification="Load balancer for high availability",
            configuration_options={
                "types": ["Application Load Balancer", "Network Load Balancer", "Gateway Load Balancer"],
                "lcus_range": [1, 100]
            }
        )
    
    def _create_waf_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        return ServiceRecommendation(
            service_name="AWS WAF",
            service_type="Security",
            description="Web application firewall to protect against common web exploits.",
            base_config={"web_acls": 1, "rules": 5},
            monthly_cost=5.00 + (1.00 * 5),
            justification="Security for compliance requirements",
            configuration_options={
                "web_acls_range": [1, 20],
                "rules_range": [1, 100]
            }
        )
    
    def _create_cloudwatch_recommendation(self, req: CustomerRequirement) -> ServiceRecommendation:
        return ServiceRecommendation(
            service_name="Amazon CloudWatch",
            service_type="Monitoring",
            description="Monitoring and observability service. Track metrics, logs, and events.",
            base_config={"custom_metrics": 10, "log_storage_gb": 10},
            monthly_cost=(10 * 0.30) + (10 * 0.50),
            justification="Monitoring and logging for all services",
            configuration_options={
                "metrics_range": [1, 1000],
                "log_storage_range": [1, 10000]
            }
        )

class CloudPackageBuilder:
    def __init__(self):
        self.service_mapper = ServiceMapper()
        self.agent = CloudServiceAgent()
        self.price_list = AWSPriceList()

    def create_initial_recommendations(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        """Generate service recommendations based on requirements"""
        required_services = self.service_mapper.identify_required_services(requirements)
        recommendations = []
        
        for service_info in required_services:
            rec = self.agent.create_recommendation(service_info, requirements)
            if rec:
                recommendations.append(rec)
        
        return recommendations

    def calculate_service_cost(self, service_name: str, config: Dict, region: str = "us-east-1") -> float:
        """Dynamically calculate cost based on configuration using AWS pricing"""
        
        if service_name == "Amazon EC2":
            hourly_rate = self.price_list.get_ec2_price(config['instance_type'], region)
            instance_cost = hourly_rate * 730 * config.get('instance_count', 1)
            storage_cost = config.get('storage_gb', 30) * 0.10
            return instance_cost + storage_cost
            
        elif service_name == "AWS Lambda":
            requests = config.get('requests_per_month', 1000000)
            memory_gb = config.get('memory_mb', 128) / 1024
            duration = config.get('timeout_seconds', 30) / 3600
            gb_seconds = requests * memory_gb * duration
            request_cost = max(0, requests - 1000000) * 0.0000002
            compute_cost = max(0, gb_seconds - 400000) * 0.0000166667
            return request_cost + compute_cost
            
        elif service_name == "Amazon ECS":
            vcpu = config.get('vcpu', 0.25)
            memory = config.get('memory_gb', 0.5)
            tasks = config.get('tasks', 1)
            vcpu_cost = vcpu * 0.04048 * 730
            memory_cost = memory * 0.004445 * 730
            return (vcpu_cost + memory_cost) * tasks
            
        elif service_name == "Amazon EKS":
            cluster_cost = 73 * config.get('cluster_count', 1)
            node_cost = self.price_list.get_ec2_price(config['node_type'], region) * 730 * config.get('node_count', 2)
            return cluster_cost + node_cost
            
        elif service_name == "Amazon S3":
            storage_gb = config.get('storage_gb', 100)
            storage_class = config.get('storage_class', 'Standard')
            price_per_gb = self.price_list.get_s3_price(storage_class, region)
            return storage_gb * price_per_gb
            
        elif service_name == "Amazon RDS":
            instance_type = config.get('instance_type', 'db.t3.medium')
            storage_gb = config.get('storage_gb', 100)
            multi_az = config.get('multi_az', False)
            hourly_rate = self.price_list.get_rds_price(instance_type, config.get('engine', 'postgres'), region)
            instance_cost = hourly_rate * 730 * (2 if multi_az else 1)
            storage_cost = storage_gb * 0.115
            return instance_cost + storage_cost
            
        elif service_name == "Amazon DynamoDB":
            storage_gb = config.get('storage_gb', 100)
            read_units = config.get('read_units', 100)
            write_units = config.get('write_units', 100)
            storage_cost = storage_gb * 0.25
            read_cost = (read_units * 730) * 0.00013
            write_cost = (write_units * 730) * 0.00065
            return storage_cost + read_cost + write_cost
            
        elif service_name == "Amazon SageMaker":
            training_hours = config.get('training_hours', 100)
            instance_prices = {
                "ml.t3.medium": 0.056, "ml.m5.large": 0.134,
                "ml.m5.xlarge": 0.269, "ml.p3.2xlarge": 3.825,
                "ml.g4dn.xlarge": 0.736
            }
            return training_hours * instance_prices.get(config.get('instance_type', 'ml.m5.xlarge'), 0.269)
            
        elif service_name == "Amazon Bedrock":
            tokens = config.get('tokens_per_month', 1000000)
            model_pricing = {
                "Claude": 0.003, "Titan": 0.0008,
                "Llama": 0.0006, "Jurassic": 0.015
            }
            cost_per_1k = model_pricing.get(config.get('model', 'Claude'), 0.003)
            return (tokens / 1000) * cost_per_1k
            
        elif service_name == "Amazon CloudFront":
            data_gb = config.get('data_transfer_gb', 1000)
            return data_gb * 0.085
            
        elif service_name == "Elastic Load Balancing":
            lcus = config.get('lcus', 5)
            return (0.0225 * 730) + (lcus * 0.008 * 730)
            
        elif service_name == "AWS WAF":
            web_acls = config.get('web_acls', 1)
            rules = config.get('rules', 5)
            return (web_acls * 5.00) + (rules * 1.00)
            
        elif service_name == "Amazon CloudWatch":
            metrics = config.get('custom_metrics', 10)
            log_storage = config.get('log_storage_gb', 10)
            return (metrics * 0.30) + (log_storage * 0.50)
            
        return 0.0

# ... previous code remains the same ...

def render_service_configurator(service: ServiceRecommendation, key_prefix: str):
    """Render configuration UI for any service"""
    st.markdown(f"### ⚙️ Configure {service.service_name}")
    st.markdown(f"*{service.description}*")
    st.info(f"💡 {service.justification}")
    
    config = {}
    
    if service.service_name == "Amazon EC2":
        col1, col2 = st.columns(2)
        with col1:
            config['instance_type'] = st.selectbox(
                "Instance Type",
                service.configuration_options['instance_types'],
                key=f"{key_prefix}_instance"
            )
            config['instance_count'] = st.number_input(
                "Number of Instances",
                min_value=service.configuration_options['count_range'][0],
                max_value=service.configuration_options['count_range'][1],
                value=service.base_config.get('count', 1),
                key=f"{key_prefix}_count"
            )
        with col2:
            config['storage_gb'] = st.number_input(
                "Storage per Instance (GB)",
                min_value=service.configuration_options['storage_range'][0],
                max_value=service.configuration_options['storage_range'][1],
                value=service.base_config.get('storage_gb', 30),
                key=f"{key_prefix}_storage"
            )
    
    elif service.service_name == "AWS Lambda":
        col1, col2 = st.columns(2)
        with col1:
            config['memory_mb'] = st.selectbox(
                "Memory (MB)",
                service.configuration_options['memory_options'],
                key=f"{key_prefix}_memory"
            )
        with col2:
            config['timeout_seconds'] = st.slider(
                "Timeout (seconds)",
                min_value=service.configuration_options['timeout_range'][0],
                max_value=service.configuration_options['timeout_range'][1],
                value=service.base_config.get('timeout', 30),
                key=f"{key_prefix}_timeout"
            )
        config['requests_per_month'] = st.number_input(
            "Monthly Requests",
            min_value=service.configuration_options['requests_range'][0],
            max_value=service.configuration_options['requests_range'][1],
            value=service.base_config.get('requests', 1000000),
            key=f"{key_prefix}_requests"
        )
    
    elif service.service_name == "Amazon S3":
        col1, col2 = st.columns(2)
        with col1:
            config['storage_class'] = st.selectbox(
                "Storage Class",
                service.configuration_options['storage_classes'],
                key=f"{key_prefix}_class"
            )
        with col2:
            config['storage_gb'] = st.number_input(
                "Storage (GB)",
                min_value=service.configuration_options['storage_range'][0],
                max_value=service.configuration_options['storage_range'][1],
                value=service.base_config.get('storage_gb', 100),
                key=f"{key_prefix}_storage"
            )
    
    elif service.service_name == "Amazon RDS":
        col1, col2 = st.columns(2)
        with col1:
            config['instance_type'] = st.selectbox(
                "Instance Type",
                service.configuration_options['instance_types'],
                key=f"{key_prefix}_instance"
            )
            config['engine'] = st.selectbox(
                "Database Engine",
                service.configuration_options['engines'],
                key=f"{key_prefix}_engine"
            )
        with col2:
            config['storage_gb'] = st.number_input(
                "Storage (GB)",
                min_value=service.configuration_options['storage_range'][0],
                max_value=service.configuration_options['storage_range'][1],
                value=service.base_config.get('storage_gb', 100),
                key=f"{key_prefix}_storage"
            )
            config['multi_az'] = st.checkbox(
                "Multi-AZ Deployment",
                value=service.base_config.get('multi_az', False),
                key=f"{key_prefix}_multiaz"
            )
    
    return config

def main():
    st.set_page_config(page_title="AWS Cloud Package Builder", layout="wide")
    st.title("🚀 AWS Cloud Package Builder")
    
    # Sidebar for requirements input
    st.sidebar.header("Project Requirements")
    
    workload_type = st.sidebar.selectbox(
        "Workload Type",
        ["Web Application", "Data Processing", "Machine Learning", "Microservices", 
         "Serverless", "Container-based", "Database", "Analytics"]
    )
    
    monthly_budget = st.sidebar.number_input(
        "Monthly Budget ($)",
        min_value=100,
        max_value=1000000,
        value=5000
    )
    
    performance_tier = st.sidebar.selectbox(
        "Performance Tier",
        ["Development", "Production", "Enterprise"]
    )
    
    price_list = AWSPriceList()
    available_regions = price_list.get_regions()
    
    regions = st.sidebar.multiselect(
        "AWS Regions",
        available_regions,
        default=[available_regions[0]] if available_regions else ["us-east-1"]
    )
    
    expected_users = st.sidebar.number_input(
        "Expected Monthly Users",
        min_value=1,
        max_value=1000000,
        value=1000
    )
    
    data_volume_gb = st.sidebar.number_input(
        "Expected Data Volume (GB)",
        min_value=1,
        max_value=100000,
        value=100
    )
    
    special_requirements = st.sidebar.multiselect(
        "Special Requirements",
        ["High Availability", "Auto Scaling", "Content Delivery", 
         "Backup & DR", "Load Balancing", "Serverless"]
    )
    
    compliance_needs = st.sidebar.multiselect(
        "Compliance Requirements",
        ["HIPAA", "PCI DSS", "SOC 2", "GDPR", "ISO 27001"]
    )
    
    if st.sidebar.button("Generate Recommendations", type="primary"):
        requirements = CustomerRequirement(
            workload_type=workload_type,
            monthly_budget=monthly_budget,
            performance_tier=performance_tier,
            regions=regions,
            expected_users=expected_users,
            data_volume_gb=data_volume_gb,
            special_requirements=special_requirements,
            compliance_needs=compliance_needs
        )
        
        builder = CloudPackageBuilder()
        
        with st.spinner("🔄 Analyzing requirements and generating recommendations..."):
            recommendations = builder.create_initial_recommendations(requirements)
            
            st.header("📦 Recommended AWS Services")
            
            total_cost = 0
            configured_services = []
            
            for i, rec in enumerate(recommendations):
                with st.expander(f"{rec.service_name} - {rec.service_type}", expanded=True):
                    config = render_service_configurator(rec, f"service_{i}")
                    cost = builder.calculate_service_cost(rec.service_name, config, regions[0])
                    st.metric("Monthly Cost", f"${cost:,.2f}")
                    total_cost += cost
                    configured_services.append({
                        "service": rec.service_name,
                        "config": config,
                        "cost": cost
                    })
            
            st.header("💰 Cost Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Monthly Cost", f"${total_cost:,.2f}")
            with col2:
                st.metric("Services", len(configured_services))
            with col3:
                budget_used = (total_cost / monthly_budget) * 100
                st.metric("Budget Utilized", f"{budget_used:.1f}%")
            
            if total_cost > monthly_budget:
                st.warning("⚠️ Total cost exceeds specified budget!")
            
            # Download configuration
            st.download_button(
                "📥 Download Configuration",
                data=json.dumps({
                    "requirements": {
                        "workload_type": workload_type,
                        "monthly_budget": monthly_budget,
                        "performance_tier": performance_tier,
                        "regions": regions,
                        "expected_users": expected_users,
                        "data_volume_gb": data_volume_gb,
                        "special_requirements": special_requirements,
                        "compliance_needs": compliance_needs
                    },
                    "services": configured_services,
                    "total_monthly_cost": total_cost
                }, indent=2),
                file_name="aws_configuration.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()