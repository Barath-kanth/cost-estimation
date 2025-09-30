import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time



def initialize_session_state():
    """Initialize session state variables"""
    if 'configurations' not in st.session_state:
        st.session_state.configurations = {}
    if 'selected_services' not in st.session_state:
        st.session_state.selected_services = {}
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0

AWS_SERVICES = {
    "🚀 Compute": {
        "Amazon EC2": "Virtual servers in the cloud",
        "AWS Lambda": "Serverless compute service",
        "Amazon ECS": "Fully managed container orchestration",
        "Amazon EKS": "Managed Kubernetes service"
    },
    "💾 Storage": {
        "Amazon S3": "Object storage service",
        "Amazon EBS": "Block storage for EC2",
        "Amazon EFS": "Managed file system"
    },
    "🗄️ Database": {
        "Amazon RDS": "Managed relational database",
        "Amazon DynamoDB": "Managed NoSQL database",
        "Amazon ElastiCache": "In-memory caching"
    },
    "🤖 AI/ML": {
        "Amazon Bedrock": "Fully managed foundation models",
        "Amazon SageMaker": "Build, train and deploy ML models",
        "Amazon Comprehend": "Natural language processing"
    },
    "🌐 Networking": {
        "Amazon VPC": "Isolated cloud resources",
        "Amazon CloudFront": "Global content delivery network",
        "Elastic Load Balancing": "Distribute incoming traffic"
    },
    "🔒 Security": {
        "AWS WAF": "Web Application Firewall",
        "Amazon GuardDuty": "Threat detection service",
        "AWS Shield": "DDoS protection"
    }
}

class ServiceSelector:
    @staticmethod
    def render_service_selection() -> Dict[str, List[str]]:
        """Render service selection UI and return selected services"""
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #1e293b !important; margin-bottom: 0.5rem;'>🎯 Select AWS Services</h3>
            <p style='color: #64748b !important; margin: 0;'>Choose the services that best fit your architecture needs</p>
        </div>
        """, unsafe_allow_html=True)
        
        selected_services = {}
        
        tabs = st.tabs(list(AWS_SERVICES.keys()))
        for i, (category, services) in enumerate(AWS_SERVICES.items()):
            with tabs[i]:
                st.markdown(f"### {category.split(' ')[1]} Services")
                
                cols = st.columns(2)
                for j, (service, description) in enumerate(services.items()):
                    col_idx = j % 2
                    with cols[col_idx]:
                        if st.checkbox(
                            f"**{service}**", 
                            help=description,
                            key=f"service_{category}_{j}"
                        ):
                            if category not in selected_services:
                                selected_services[category] = []
                            selected_services[category].append(service)
        
        return selected_services

# Pricing configurations (keeping the same as before)
INSTANCE_FAMILIES = {
    "General Purpose": {
        "t3.micro": {"vCPU": 2, "Memory": 1, "Price": 0.0104},
        "t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.0208},
        "t3.medium": {"vCPU": 2, "Memory": 4, "Price": 0.0416},
        "m5.large": {"vCPU": 2, "Memory": 8, "Price": 0.096},
        "m5.xlarge": {"vCPU": 4, "Memory": 16, "Price": 0.192}
    },
    "Compute Optimized": {
        "c5.large": {"vCPU": 2, "Memory": 4, "Price": 0.085},
        "c5.xlarge": {"vCPU": 4, "Memory": 8, "Price": 0.17},
        "c5.2xlarge": {"vCPU": 8, "Memory": 16, "Price": 0.34}
    },
    "Memory Optimized": {
        "r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.126},
        "r5.xlarge": {"vCPU": 4, "Memory": 32, "Price": 0.252},
        "r5.2xlarge": {"vCPU": 8, "Memory": 64, "Price": 0.504}
    }
}

DATABASE_PRICING = {
    "PostgreSQL": {
        "db.t3.micro": {"vCPU": 1, "Memory": 1, "Price": 0.017, "Storage": 0.115},
        "db.t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.034, "Storage": 0.115},
        "db.t3.medium": {"vCPU": 2, "Memory": 4, "Price": 0.068, "Storage": 0.115},
        "db.r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.24, "Storage": 0.115},
        "db.m5.large": {"vCPU": 2, "Memory": 8, "Price": 0.17, "Storage": 0.115}
    },
    "MySQL": {
        "db.t3.micro": {"vCPU": 1, "Memory": 1, "Price": 0.017, "Storage": 0.115},
        "db.t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.034, "Storage": 0.115},
        "db.t3.medium": {"vCPU": 2, "Memory": 4, "Price": 0.068, "Storage": 0.115},
        "db.r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.24, "Storage": 0.115}
    },
    "Aurora MySQL": {
        "db.r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.29, "Storage": 0.10},
        "db.r5.xlarge": {"vCPU": 4, "Memory": 32, "Price": 0.58, "Storage": 0.10}
    },
    "SQL Server": {
        "db.t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.075, "Storage": 0.115},
        "db.m5.large": {"vCPU": 2, "Memory": 8, "Price": 0.315, "Storage": 0.115}
    }
}

EBS_PRICING = {
    "gp3": {"price_per_gb": 0.08, "iops_price": 0.005, "throughput_price": 0.04},
    "gp2": {"price_per_gb": 0.10, "iops_price": 0.00, "throughput_price": 0.00},
    "io1": {"price_per_gb": 0.125, "iops_price": 0.065, "throughput_price": 0.00},
    "io2": {"price_per_gb": 0.125, "iops_price": 0.065, "throughput_price": 0.00},
    "st1": {"price_per_gb": 0.045, "iops_price": 0.00, "throughput_price": 0.00},
    "sc1": {"price_per_gb": 0.015, "iops_price": 0.00, "throughput_price": 0.00}
}

STORAGE_PRICING = {
    "Standard": 0.023,
    "Intelligent-Tiering": 0.0125,
    "Standard-IA": 0.0125,
    "One Zone-IA": 0.01,
    "Glacier": 0.004,
    "Glacier Deep Archive": 0.00099
}

AI_ML_PRICING = {
    "Bedrock": {
        "Claude": 0.0008,
        "Llama 2": 0.0004,
        "Stable Diffusion": 0.001,
        "Jurassic": 0.001
    },
    "SageMaker": {
        "ml.t3.medium": 0.0464,
        "ml.t3.large": 0.0928,
        "ml.t3.xlarge": 0.1856,
        "ml.p3.2xlarge": 3.06
    }
}

NETWORKING_PRICING = {
    "CloudFront": {
        "price_per_gb": 0.085,
        "requests_per_1000": 0.0075
    },
    "ELB": {
        "Application": 0.0225,
        "Network": 0.0225,
        "Gateway": 0.0225,
        "price_per_lcu_hour": 0.008
    }
}

SECURITY_PRICING = {
    "WAF": {
        "price_per_rule": 1,
        "price_per_request_million": 0.60,
        "price_per_acl": 5
    },
    "GuardDuty": {
        "price_per_gb": 0.001,
        "base_price": 4.00
    },
    "Shield": {
        "standard": 0,
        "advanced": 3000
    }
}

EKS_PRICING = {
    "cluster_per_hour": 0.10,
    "node_group_per_hour": 0.0,
}

class InnovativePricing:
    @staticmethod
    def calculate_price(service: str, config: Dict, usage_pattern: str = "normal") -> float:
        """Calculate price using innovative factors"""
        base_price = 0.0
        
        pattern_multipliers = {
            "development": 0.6,
            "sporadic": 0.8,
            "normal": 1.0,
            "intensive": 1.4,
            "24x7": 1.8
        }
        
        current_hour = datetime.now().hour
        if 0 <= current_hour < 6:
            time_multiplier = 0.7
        elif 6 <= current_hour < 9 or 17 <= current_hour < 20:
            time_multiplier = 1.2
        else:
            time_multiplier = 1.0
        
        region_multipliers = {
            "us-east-1": 1.0,
            "us-west-2": 1.08,
            "eu-west-1": 1.15,
            "ap-southeast-1": 1.25,
            "ap-northeast-1": 1.30
        }
        
        if service == "Amazon EC2":
            instance_type = config.get('instance_type', 't3.micro')
            for family in INSTANCE_FAMILIES.values():
                if instance_type in family:
                    base_price = family[instance_type]['Price'] * 730
                    break
            
            storage_gb = config.get('storage_gb', 30)
            volume_type = config.get('volume_type', 'gp3')
            iops = config.get('iops', 3000) if volume_type in ['gp3', 'io1', 'io2'] else 0
            throughput = config.get('throughput', 125) if volume_type == 'gp3' else 0
            
            ebs_pricing = EBS_PRICING.get(volume_type, EBS_PRICING['gp3'])
            storage_cost = (storage_gb * ebs_pricing['price_per_gb'] + 
                          iops * ebs_pricing['iops_price'] + 
                          throughput * ebs_pricing['throughput_price'])
            
            base_price = (base_price * config.get('instance_count', 1)) + storage_cost
            
        elif service == "Amazon RDS":
            instance_type = config.get('instance_type')
            engine = config.get('engine')
            if engine in DATABASE_PRICING and instance_type in DATABASE_PRICING[engine]:
                instance_price = DATABASE_PRICING[engine][instance_type]['Price']
                storage_price = DATABASE_PRICING[engine][instance_type]['Storage']
                base_price = instance_price * 730
                
                storage_gb = config.get('storage_gb', 20)
                base_price += storage_gb * storage_price
                
                if config.get('backup_retention', 0) > 0:
                    base_price += storage_gb * 0.095 * config.get('backup_retention', 0) / 30
                
                if config.get('multi_az', False):
                    base_price *= 2
                
                if config.get('encryption', False):
                    base_price *= 1.05
                    
        elif service == "Amazon EBS":
            storage_gb = config.get('storage_gb', 100)
            volume_type = config.get('volume_type', 'gp3')
            iops = config.get('iops', 3000) if volume_type in ['gp3', 'io1', 'io2'] else 0
            throughput = config.get('throughput', 125) if volume_type == 'gp3' else 0
            snapshots = config.get('monthly_snapshots', 0)
            
            ebs_pricing = EBS_PRICING.get(volume_type, EBS_PRICING['gp3'])
            base_price = (storage_gb * ebs_pricing['price_per_gb'] + 
                         iops * ebs_pricing['iops_price'] + 
                         throughput * ebs_pricing['throughput_price'])
            
            base_price += snapshots * storage_gb * 0.05
            
        elif service == "Amazon S3":
            storage_class = config.get('storage_class', 'Standard')
            storage_gb = config.get('storage_gb', 100)
            requests = config.get('requests_per_month', 100000)
            data_transfer = config.get('data_transfer_gb', 0)
            
            base_price = (storage_gb * STORAGE_PRICING[storage_class] + 
                         (requests / 1000 * 0.0004) +
                         (data_transfer * 0.09))
            
        elif service == "AWS Lambda":
            memory_mb = config.get('memory_mb', 128)
            requests = config.get('requests_per_month', 1000000)
            duration_ms = config.get('avg_duration_ms', 100)
            
            gb_seconds = (requests * duration_ms * memory_mb) / (1000 * 1024)
            base_price = (requests * 0.0000002) + (gb_seconds * 0.0000166667)
            
        elif service == "Amazon Bedrock":
            model = config.get('model', 'Claude')
            requests = config.get('requests_per_month', 10000)
            tokens = config.get('avg_tokens', 1000)
            
            base_price = (requests * tokens / 1000) * AI_ML_PRICING['Bedrock'][model]
            
        elif service == "Amazon CloudFront":
            data_gb = config.get('data_transfer_gb', 1000)
            requests = config.get('requests', 100000)
            
            base_price = (data_gb * NETWORKING_PRICING['CloudFront']['price_per_gb'] +
                         (requests / 1000) * NETWORKING_PRICING['CloudFront']['requests_per_1000'])
            
        elif service == "AWS WAF":
            acls = config.get('web_acls', 1)
            rules = config.get('rules', 5)
            requests = config.get('requests_million', 1)
            
            base_price = (acls * SECURITY_PRICING['WAF']['price_per_acl'] +
                         rules * SECURITY_PRICING['WAF']['price_per_rule'] +
                         requests * SECURITY_PRICING['WAF']['price_per_request_million'])
            
        elif service == "Amazon EKS":
            cluster_hours = config.get('cluster_hours', 730)
            base_price = cluster_hours * EKS_PRICING['cluster_per_hour']
            
            node_count = config.get('node_count', 2)
            node_instance_type = config.get('node_instance_type', 't3.medium')
            
            node_price_per_hour = 0.0
            for family in INSTANCE_FAMILIES.values():
                if node_instance_type in family:
                    node_price_per_hour = family[node_instance_type]['Price']
                    break
            
            node_cost = node_count * node_price_per_hour * cluster_hours
            base_price += node_cost
            
            if config.get('load_balancer', False):
                base_price += NETWORKING_PRICING['ELB']['Application'] * cluster_hours
            
        elif service == "Amazon ECS":
            launch_type = config.get('launch_type', 'Fargate')
            tasks = config.get('tasks', 1)
            hours_per_month = 730
            
            if launch_type == "Fargate":
                vcpu = config.get('vcpu', 0.5)
                memory_gb = config.get('memory_gb', 1.0)
                
                price_per_hour = (vcpu * 0.04048) + (memory_gb * 0.004445)
                base_price = price_per_hour * hours_per_month * tasks
                
            elif launch_type == "EC2":
                instance_type = config.get('instance_type', 't3.medium')
                instance_count = config.get('instance_count', 1)
                
                for family in INSTANCE_FAMILIES.values():
                    if instance_type in family:
                        instance_price = family[instance_type]['Price']
                        base_price = instance_price * hours_per_month * instance_count
                        break
        
        final_price = (
            base_price *
            pattern_multipliers.get(usage_pattern, 1.0) *
            time_multiplier *
            region_multipliers.get(config.get('region', 'us-east-1'), 1.0)
        )
        
        if final_price > 10000:
            final_price *= 0.75
        elif final_price > 5000:
            final_price *= 0.80
        elif final_price > 1000:
            final_price *= 0.85
        elif final_price > 500:
            final_price *= 0.90
            
        if config.get('commitment', 'none') == '1-year':
            final_price *= 0.85
        elif config.get('commitment', 'none') == '3-year':
            final_price *= 0.70
            
        return final_price

def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.markdown("##### 🖥️ Instance Configuration")
        family = st.selectbox(
            "Instance Family",
            list(INSTANCE_FAMILIES.keys()),
            help="Choose instance family based on workload",
            key=f"{key_prefix}_family"
        )
        instance_types = list(INSTANCE_FAMILIES[family].keys())
        selected_type = st.selectbox(
            "Instance Type",
            instance_types,
            key=f"{key_prefix}_type"
        )
        specs = INSTANCE_FAMILIES[family][selected_type]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("vCPU", specs["vCPU"])
        with col2:
            st.metric("Memory (GiB)", specs["Memory"])
        with col3:
            st.metric("Price/Hour", f"${specs['Price']}")
        
        col1, col2 = st.columns(2)
        with col1:
            instance_count = st.number_input("Number of Instances", 1, 100, 1, key=f"{key_prefix}_count")
        with col2:
            volume_type = st.selectbox(
                "EBS Volume Type",
                list(EBS_PRICING.keys()),
                key=f"{key_prefix}_volume_type"
            )
        
        storage_gb = st.number_input("EBS Storage (GB)", 8, 16384, 30, key=f"{key_prefix}_storage")
        
        if volume_type in ['gp3', 'io1', 'io2']:
            iops = st.number_input("IOPS", 100, 64000, 3000, key=f"{key_prefix}_iops")
            config["iops"] = iops
        
        if volume_type == 'gp3':
            throughput = st.number_input("Throughput (MB/s)", 125, 1000, 125, key=f"{key_prefix}_throughput")
            config["throughput"] = throughput
        
        config.update({
            "instance_type": selected_type,
            "instance_count": instance_count,
            "storage_gb": storage_gb,
            "volume_type": volume_type
        })
        
    elif service == "Amazon RDS":
        st.markdown("##### 🗄️ Database Configuration")
        engine = st.selectbox(
            "Database Engine",
            list(DATABASE_PRICING.keys()),
            key=f"{key_prefix}_engine"
        )
        instance_types = list(DATABASE_PRICING[engine].keys())
        selected_type = st.selectbox(
            "Instance Type",
            instance_types,
            key=f"{key_prefix}_type"
        )
        specs = DATABASE_PRICING[engine][selected_type]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("vCPU", specs["vCPU"])
        with col2:
            st.metric("Memory (GiB)", specs["Memory"])
        with col3:
            st.metric("Price/Hour", f"${specs['Price']}")
        
        col1, col2 = st.columns(2)
        with col1:
            storage = st.number_input("Storage (GB)", 20, 65536, 100, key=f"{key_prefix}_storage")
            backup_retention = st.number_input("Backup Retention (Days)", 0, 35, 7, key=f"{key_prefix}_backup")
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
        
    elif service == "Amazon EBS":
        st.markdown("##### 💾 EBS Volume Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            volume_type = st.selectbox(
                "Volume Type",
                list(EBS_PRICING.keys()),
                help="gp3: General Purpose, io1/io2: Provisioned IOPS, st1: Throughput Optimized, sc1: Cold",
                key=f"{key_prefix}_volume_type"
            )
            storage_gb = st.number_input("Storage Size (GB)", 1, 16384, 100, key=f"{key_prefix}_storage")
        with col2:
            monthly_snapshots = st.number_input("Monthly Snapshots", 0, 30, 4, key=f"{key_prefix}_snapshots")
            st.metric("Price/GB/Month", f"${EBS_PRICING[volume_type]['price_per_gb']}")
        
        if volume_type in ['gp3', 'io1', 'io2']:
            iops = st.number_input("Provisioned IOPS", 100, 64000, 3000, key=f"{key_prefix}_iops")
            config["iops"] = iops
        
        if volume_type == 'gp3':
            throughput = st.number_input("Throughput (MB/s)", 125, 1000, 125, key=f"{key_prefix}_throughput")
            config["throughput"] = throughput
        
        ebs_pricing = EBS_PRICING[volume_type]
        estimated_cost = storage_gb * ebs_pricing['price_per_gb']
        if 'iops' in config:
            estimated_cost += config['iops'] * ebs_pricing['iops_price']
        if 'throughput' in config:
            estimated_cost += config['throughput'] * ebs_pricing['throughput_price']
        estimated_cost += monthly_snapshots * storage_gb * 0.05
        
        st.metric("Estimated Monthly Cost", f"${estimated_cost:,.2f}")
        
        config.update({
            "volume_type": volume_type,
            "storage_gb": storage_gb,
            "monthly_snapshots": monthly_snapshots
        })
        
    elif service == "AWS Lambda":
        st.markdown("##### ⚡ Lambda Function Configuration")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            memory_mb = st.selectbox(
                "Memory (MB)",
                [128, 256, 512, 1024, 2048, 3008, 4096, 5120, 6144, 7168, 8192, 9216, 10240],
                index=0,
                key=f"{key_prefix}_memory"
            )
            st.metric("Memory", f"{memory_mb} MB")
        
        with col2:
            requests = st.number_input(
                "Monthly Requests",
                min_value=1000,
                max_value=100000000,
                value=1000000,
                step=100000,
                key=f"{key_prefix}_requests"
            )
            st.metric("Requests/Month", f"{requests:,}")
        
        with col3:
            duration_ms = st.number_input(
                "Average Duration (ms)",
                min_value=100,
                max_value=90000,
                value=1000,
                step=100,
                key=f"{key_prefix}_duration"
            )
            st.metric("Duration", f"{duration_ms} ms")
        
        gb_seconds = (requests * duration_ms * memory_mb) / (1000 * 1024)
        estimated_cost = (requests * 0.0000002) + (gb_seconds * 0.0000166667)
        st.metric("Estimated Monthly Cost", f"${estimated_cost:,.2f}")
        
        config.update({
            "memory_mb": memory_mb,
            "requests_per_month": requests,
            "avg_duration_ms": duration_ms
        })
        
    elif service == "Amazon EKS":
        st.markdown("##### 🐳 EKS Cluster Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            node_count = st.number_input("Number of Worker Nodes", 1, 100, 2, key=f"{key_prefix}_nodes")
        with col2:
            cluster_hours = st.number_input("Cluster Hours/Month", 1, 744, 730, key=f"{key_prefix}_hours")
        
        family = st.selectbox(
            "Node Instance Family",
            list(INSTANCE_FAMILIES.keys()),
            key=f"{key_prefix}_node_family"
        )
        node_instance_types = list(INSTANCE_FAMILIES[family].keys())
        node_instance_type = st.selectbox(
            "Node Instance Type",
            node_instance_types,
            key=f"{key_prefix}_node_type"
        )
        
        node_specs = INSTANCE_FAMILIES[family][node_instance_type]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Node vCPU", node_specs["vCPU"])
        with col2:
            st.metric("Node Memory (GiB)", node_specs["Memory"])
        with col3:
            st.metric("Node Price/Hour", f"${node_specs['Price']}")
        
        load_balancer = st.checkbox("Add Application Load Balancer", value=True, key=f"{key_prefix}_alb")
        auto_scaling = st.checkbox("Enable Auto Scaling", value=True, key=f"{key_prefix}_asg")
        
        config.update({
            "node_count": node_count,
            "node_instance_type": node_instance_type,
            "cluster_hours": cluster_hours,
            "load_balancer": load_balancer,
            "auto_scaling": auto_scaling
        })
        
        cluster_cost = cluster_hours * EKS_PRICING['cluster_per_hour']
        node_cost = node_count * node_specs['Price'] * cluster_hours
        total_estimated = cluster_cost + node_cost
        
        if load_balancer:
            alb_cost = NETWORKING_PRICING['ELB']['Application'] * cluster_hours
            total_estimated += alb_cost
        
        st.metric("Estimated Monthly Cost", f"${total_estimated:,.2f}")
        
    elif service == "Amazon ECS":
        st.markdown("##### 🐳 Container Configuration")
        launch_type = st.radio(
            "Launch Type",
            ["Fargate", "EC2"],
            key=f"{key_prefix}_launch_type"
        )
        
        tasks = st.number_input("Number of Tasks", 1, 100, 1, key=f"{key_prefix}_tasks")
        
        if launch_type == "Fargate":
            col1, col2 = st.columns(2)
            with col1:
                vcpu = st.number_input("vCPU Units", 0.25, 4.0, 0.5, 0.25, key=f"{key_prefix}_vcpu")
                st.metric("vCPU", vcpu)
            with col2:
                memory = st.number_input("Memory (GB)", 0.5, 30.0, 1.0, 0.5, key=f"{key_prefix}_memory")
                st.metric("Memory (GB)", memory)
            
            price_per_vcpu_hour = 0.04048
            price_per_gb_hour = 0.004445
            price_per_task_hour = (vcpu * price_per_vcpu_hour) + (memory * price_per_gb_hour)
            price_per_task_month = price_per_task_hour * 24 * 30
            total_price = price_per_task_month * tasks
            st.metric("Estimated Monthly Cost", f"${total_price:,.2f}")
            
            config.update({
                "launch_type": launch_type,
                "vcpu": vcpu,
                "memory_gb": memory,
                "tasks": tasks
            })
            
        elif launch_type == "EC2":
            family = st.selectbox(
                "Instance Family",
                list(INSTANCE_FAMILIES.keys()),
                key=f"{key_prefix}_ec2_family"
            )
            instance_types = list(INSTANCE_FAMILIES[family].keys())
            instance_type = st.selectbox(
                "Instance Type",
                instance_types,
                key=f"{key_prefix}_ec2_type"
            )
            instance_count = st.number_input("Number of Instances", 1, 20, 1, key=f"{key_prefix}_ec2_count")
            
            specs = INSTANCE_FAMILIES[family][instance_type]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("vCPU", specs["vCPU"])
            with col2:
                st.metric("Memory (GiB)", specs["Memory"])
            with col3:
                st.metric("Price/Hour", f"${specs['Price']}")
            
            instance_price_per_month = specs['Price'] * 730
            total_price = instance_price_per_month * instance_count
            st.metric("Estimated Monthly Cost", f"${total_price:,.2f}")
            
            config.update({
                "launch_type": launch_type,
                "instance_type": instance_type,
                "instance_count": instance_count,
                "tasks": tasks
            })
            
    elif service == "Amazon S3":
        st.markdown("##### ☁️ Storage Configuration")
        storage_class = st.selectbox(
            "Storage Class",
            list(STORAGE_PRICING.keys()),
            key=f"{key_prefix}_class"
        )
        col1, col2 = st.columns(2)
        with col1:
            storage = st.number_input("Storage (GB)", 1, 1000000, 100, key=f"{key_prefix}_storage")
            st.metric("Price/GB/Month", f"${STORAGE_PRICING[storage_class]}")
        with col2:
            requests = st.number_input("Monthly Requests (1000s)", 1, 100000, 100, key=f"{key_prefix}_requests")
            data_transfer = st.number_input("Data Transfer Out (GB)", 0, 100000, 0, key=f"{key_prefix}_transfer")
        config.update({
            "storage_class": storage_class,
            "storage_gb": storage,
            "requests_per_month": requests * 1000,
            "data_transfer_gb": data_transfer
        })
        
    elif service == "Amazon Bedrock":
        st.markdown("##### 🤖 Model Configuration")
        model = st.selectbox(
            "Foundation Model",
            list(AI_ML_PRICING["Bedrock"].keys()),
            key=f"{key_prefix}_model"
        )
        col1, col2 = st.columns(2)
        with col1:
            requests = st.number_input("Monthly Requests", 1000, 10000000, 10000, key=f"{key_prefix}_requests")
        with col2:
            tokens = st.number_input("Avg Tokens/Request", 100, 10000, 1000, key=f"{key_prefix}_tokens")
            st.metric("Price/1K Tokens", f"${AI_ML_PRICING['Bedrock'][model]}")
        config.update({
            "model": model,
            "requests_per_month": requests,
            "avg_tokens": tokens
        })
    
    commitment = st.selectbox(
        "💎 Commitment Level",
        ["none", "1-year", "3-year"],
        help="Savings Plans/Reserved Instances commitment",
        key=f"{key_prefix}_commitment"
    )
    config["commitment"] = commitment
    
    config["region"] = st.selectbox(
        "🌍 Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"],
        key=f"{key_prefix}_region"
    )
    
    return config

def main():
    st.set_page_config(page_title="AWS Cloud Package Builder", layout="wide")
    
    # Inject custom CSS
    inject_custom_css()
    
    # Main title
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>🚀 AWS Cloud Package Builder</h1>
        <p style='color: #64748b !important; font-size: 1.1rem;'>Design, Configure, and Optimize Your Cloud Architecture</p>
    </div>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    # PROJECT REQUIREMENTS SECTION
    with st.expander("🎯 Project Requirements & Architecture", expanded=True):
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #1e293b !important; margin-bottom: 0.5rem;'>📋 Define Your Project Requirements</h3>
            <p style='color: #64748b !important; margin: 0;'>Configure your workload profile, performance needs, and budget constraints</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📊 Workload Profile")
            workload_complexity = st.select_slider(
                "Workload Complexity",
                options=["Simple", "Moderate", "Complex", "Enterprise"],
                value="Moderate",
                help="Complexity of your application architecture"
            )
            
            availability_requirements = st.selectbox(
                "Availability Requirements",
                ["99.9% (Business Hours)", "99.95% (High Availability)", "99.99% (Mission Critical)"],
                help="Required uptime SLA"
            )
            
            data_classification = st.selectbox(
                "Data Classification",
                ["Public", "Internal", "Confidential", "Restricted"],
                help="Security requirements based on data sensitivity"
            )
            
        with col2:
            st.subheader("⚡ Performance Needs")
            performance_tier = st.select_slider(
                "Performance Tier",
                options=["Development", "Testing", "Production", "Enterprise"],
                value="Production"
            )
            
            response_time = st.selectbox(
                "Response Time Requirements",
                ["Standard (>1s)", "Fast (<1s)", "Real-time (<100ms)", "Ultra-fast (<10ms)"]
            )
            
            scalability_needs = st.selectbox(
                "Scalability Pattern",
                ["Fixed Capacity", "Seasonal", "Predictable Growth", "Unpredictable Burst"]
            )
            
        with col3:
            st.subheader("💰 Budget & Strategy")
            monthly_budget = st.number_input(
                "Monthly Budget ($)", 
                100, 1000000, 100,
                key="monthly_budget"
            )
            
            cost_strategy = st.selectbox(
                "Cost Optimization Strategy",
                ["Cost-Conscious", "Balanced", "Performance-First", "Enterprise-Optimized"]
            )
            
            usage_pattern = st.selectbox(
                "Usage Pattern",
                ["development", "sporadic", "normal", "intensive", "24x7"],
                help="How will the services be used?",
                key="usage_pattern"
            )
            
        # Additional requirements
        with st.expander("🔧 Advanced Requirements"):
            col1, col2 = st.columns(2)
            with col1:
                compliance_requirements = st.multiselect(
                    "Compliance Requirements",
                    ["HIPAA", "PCI-DSS", "SOC2", "GDPR", "ISO27001", "None"]
                )
                
                disaster_recovery = st.selectbox(
                    "Disaster Recovery RTO/RPO",
                    ["Basic (24h/24h)", "Standard (12h/12h)", "Advanced (4h/4h)", "Mission Critical (1h/15m)"]
                )
                
            with col2:
                data_volume_gb = st.number_input(
                    "Estimated Data Volume (GB/Month)", 
                    1, 1000000, 100,
                    key="data_volume"
                )
                
                expected_users = st.number_input(
                    "Expected Concurrent Users", 
                    1, 1000000, 1000,
                    key="expected_users"
                )
    
    st.session_state.selected_services = ServiceSelector.render_service_selection()
    
    if st.session_state.selected_services:
        st.header("🛠️ Service Configuration")
        
        st.session_state.total_cost = 0
        st.session_state.configurations = {}
        
        for category, services in st.session_state.selected_services.items():
            st.subheader(f"{category}")
            
            for i, service in enumerate(services):
                with st.expander(f"⚙️ {service}", expanded=True):
                    st.markdown(f"*{AWS_SERVICES[category][service]}*")
                    
                    service_key = f"{category}_{service}_{i}"
                    
                    if service_key not in st.session_state:
                        st.session_state[service_key] = {}
                    
                    config = render_service_configurator(service, service_key)
                    st.session_state[service_key].update(config)
                    
                    cost = InnovativePricing.calculate_price(
                        service, 
                        st.session_state[service_key],
                        usage_pattern
                    )
                    
                    st.metric("Estimated Monthly Cost", f"${cost:,.2f}")
                    st.session_state.total_cost += cost
                    
                    st.session_state.configurations[service] = {
                        "config": st.session_state[service_key],
                        "cost": cost
                    }
        
        # Cost Summary
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #1e293b !important; margin-bottom: 1rem;'>💰 Cost Summary & Recommendations</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Monthly Cost", f"${st.session_state.total_cost:,.2f}")
        with col2:
            st.metric("Services Selected", len(st.session_state.configurations))
        with col3:
            budget_used = (st.session_state.total_cost / monthly_budget) * 100 if monthly_budget > 0 else 0
            st.metric("Budget Utilized", f"{budget_used:.1f}%")
        with col4:
            savings_potential = st.session_state.total_cost * 0.15
            st.metric("Savings Potential", f"${savings_potential:,.2f}")
        
        # Progress bar for budget utilization
        if monthly_budget > 0:
            budget_percentage = min(st.session_state.total_cost / monthly_budget, 1.0)
            st.progress(budget_percentage)
        
        # Cost optimization recommendations
        with st.expander("💡 Cost Optimization Recommendations", expanded=True):
            if st.session_state.total_cost > monthly_budget:
                st.error("⚠️ Your estimated costs exceed your budget. Consider:")
                st.write("• 🔧 Right-size instances based on actual usage patterns")
                st.write("• 📈 Implement auto-scaling for variable workloads")
                st.write("• 💰 Use Savings Plans for committed usage")
                st.write("• 🎯 Consider spot instances for fault-tolerant workloads")
                st.write("• 💾 Optimize storage classes and lifecycle policies")
            else:
                st.success("✅ Your architecture is within budget! Suggestions:")
                st.write("• 📊 Implement monitoring for cost optimization")
                st.write("• 💎 Consider Reserved Instances for stable workloads")
                st.write("• 🔄 Review storage lifecycle policies")
                st.write("• ⚡ Enable cost anomaly detection")
        
        # Export configuration
        st.markdown("""
        <div class='custom-card'>
            <h3 style='color: #1e293b !important; margin-bottom: 0.5rem;'>📥 Export Configuration</h3>
            <p style='color: #64748b !important; margin: 0;'>Download your complete architecture configuration for future reference</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.download_button(
            "📥 Export Configuration as JSON",
            data=json.dumps({
                "requirements": {
                    "workload_complexity": workload_complexity,
                    "availability_requirements": availability_requirements,
                    "data_classification": data_classification,
                    "performance_tier": performance_tier,
                    "response_time": response_time,
                    "scalability_needs": scalability_needs,
                    "monthly_budget": monthly_budget,
                    "cost_strategy": cost_strategy,
                    "usage_pattern": usage_pattern,
                    "compliance_requirements": compliance_requirements,
                    "disaster_recovery": disaster_recovery,
                    "data_volume_gb": data_volume_gb,
                    "expected_users": expected_users
                },
                "services": st.session_state.configurations,
                "total_estimated_cost": st.session_state.total_cost,
                "generated_at": datetime.now().isoformat()
            }, indent=2),
            file_name="aws_architecture_plan.json",
            mime="application/json",
            key="download_config"
        )

if __name__ == "__main__":
    main()