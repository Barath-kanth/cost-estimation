import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

# Add this after imports
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

# Add this new class for service selection
class ServiceSelector:
    def render_service_selection() -> Dict[str, List[str]]:
        """Render service selection UI and return selected services"""
        st.subheader("🎯 Select AWS Services")
        
        selected_services = {}
        
        # Use tabs for service categories
        tabs = st.tabs(list(AWS_SERVICES.keys()))
        for i, (category, services) in enumerate(AWS_SERVICES.items()):
            with tabs[i]:
                st.markdown(f"### {category} Services")
                
                # Create columns for better layout
                cols = st.columns(2)
                for j, (service, description) in enumerate(services.items()):
                    col_idx = j % 2
                    with cols[col_idx]:
                        if st.checkbox(f"{service}", help=description):
                            if category not in selected_services:
                                selected_services[category] = []
                            selected_services[category].append(service)
        
        return selected_services

# Add this new class for innovative pricing
class InnovativePricing:
    @staticmethod
    def calculate_price(service: str, config: Dict, usage_pattern: str = "normal") -> float:
        """Calculate price using innovative factors"""
        base_price = 0.0
        
        # Usage pattern multipliers
        pattern_multipliers = {
            "sporadic": 0.7,    # Less consistent usage
            "normal": 1.0,      # Regular usage
            "intensive": 1.3    # Heavy usage
        }
        
        # Time-based discounts
        current_hour = datetime.now().hour
        time_multiplier = 0.8 if 0 <= current_hour < 6 else 1.0
        
        # Region-based adjustments
        region_multipliers = {
            "us-east-1": 1.0,
            "us-west-2": 1.05,
            "eu-west-1": 1.1,
            "ap-southeast-1": 1.15
        }
        
        # Calculate base price based on service and configuration
        if service == "Amazon EC2":
            instance_type = config.get('instance_type', 't3.micro')
            # Get price from INSTANCE_FAMILIES
            for family in INSTANCE_FAMILIES.values():
                if instance_type in family:
                    base_price = family[instance_type]['Price'] * 730  # Hours per month
                    break
            
            # Add storage cost
            storage_gb = config.get('storage_gb', 30)
            storage_cost = storage_gb * 0.10  # $0.10 per GB/month for EBS
            base_price = (base_price * config.get('instance_count', 1)) + storage_cost
            
        elif service == "Amazon RDS":
            instance_type = config.get('instance_type')
            engine = config.get('engine')
            if engine in DATABASE_PRICING and instance_type in DATABASE_PRICING[engine]:
                base_price = DATABASE_PRICING[engine][instance_type]['Price'] * 730
                
            storage_gb = config.get('storage_gb', 20)
            base_price += storage_gb * 0.115  # RDS storage cost
            
            if config.get('multi_az', False):
                base_price *= 2  # Double cost for Multi-AZ
            
        elif service == "Amazon S3":
            storage_class = config.get('storage_class', 'Standard')
            storage_gb = config.get('storage_gb', 100)
            requests = config.get('requests_per_month', 100000)
            
            base_price = (storage_gb * STORAGE_PRICING[storage_class]) + (requests / 1000 * 0.0004)
            
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
            
            base_price = (acls * SECURITY_PRICING['WAF']['price_per_acl'] +
                         rules * SECURITY_PRICING['WAF']['price_per_rule'])
        
        # Apply multipliers
        final_price = (
            base_price *
            pattern_multipliers.get(usage_pattern, 1.0) *
            time_multiplier *
            region_multipliers.get(config.get('region', 'us-east-1'), 1.0)
        )
        
        # Apply volume discounts
        if final_price > 1000:
            final_price *= 0.9  # 10% discount for high volume
        if final_price > 5000:
            final_price *= 0.85  # Additional 15% discount
            
        return final_price
# Add after the InnovativePricing class
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

# Add these pricing configurations after INSTANCE_FAMILIES
DATABASE_PRICING = {
    "PostgreSQL": {
        "db.t3.micro": {"vCPU": 1, "Memory": 1, "Price": 0.017},
        "db.t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.034},
        "db.t3.medium": {"vCPU": 2, "Memory": 4, "Price": 0.068},
        "db.r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.24}
    },
    "MySQL": {
        "db.t3.micro": {"vCPU": 1, "Memory": 1, "Price": 0.017},
        "db.t3.small": {"vCPU": 2, "Memory": 2, "Price": 0.034},
        "db.t3.medium": {"vCPU": 2, "Memory": 4, "Price": 0.068},
        "db.r5.large": {"vCPU": 2, "Memory": 16, "Price": 0.24}
    }
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

def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.markdown("##### Instance Configuration")
        
        # Instance family selection
        family = st.selectbox(
            "Instance Family",
            list(INSTANCE_FAMILIES.keys()),
            help="Choose instance family based on your workload",
            key=f"{key_prefix}_family"
        )
        
        # Instance type selection with specs display
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
        
        config["instance_type"] = selected_type
        config["instance_count"] = st.number_input(
            "Number of Instances", 
            1, 100, 1,
            key=f"{key_prefix}_count"
        )
        config["storage_gb"] = st.number_input(
            "EBS Storage per Instance (GB)", 
            8, 16384, 30,
            key=f"{key_prefix}_storage"
        )
    
    elif service == "Amazon RDS":
        st.markdown("##### Database Configuration")
        
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
        
        config["engine"] = engine
        config["instance_type"] = selected_type
        config["storage_gb"] = st.number_input(
            "Storage (GB)", 
            20, 65536, 100,
            key=f"{key_prefix}_storage"
        )
        config["multi_az"] = st.checkbox(
            "Multi-AZ Deployment",
            key=f"{key_prefix}_multiaz"
        )
        config["backup_retention"] = st.slider(
            "Backup Retention (Days)", 
            0, 35, 7,
            key=f"{key_prefix}_backup"
        )
    
    elif service == "Amazon S3":
        st.markdown("##### Storage Configuration")
        
        storage_class = st.selectbox(
            "Storage Class",
            list(STORAGE_PRICING.keys()),
            key=f"{key_prefix}_class"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            storage_gb = st.number_input(
                "Storage (GB)", 
                1, 1000000, 100,
                key=f"{key_prefix}_storage"
            )
            st.metric("Price/GB/Month", f"${STORAGE_PRICING[storage_class]}")
        with col2:
            requests_per_month = st.number_input(
                "Monthly Requests (thousands)",
                1, 1000000, 100,
                key=f"{key_prefix}_requests"
            ) * 1000
        
        config["storage_class"] = storage_class
        config["storage_gb"] = storage_gb
        config["requests_per_month"] = requests_per_month
    
    # ... Add configurations for other services with unique keys ...
    
    # Add region selection with unique key
    config["region"] = st.selectbox(
        "Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
        key=f"{key_prefix}_region"
    )
    
    return config

# Update the main function to pass unique keys
def main():
    # ... existing code ...
    
    if st.button("Generate Configuration", type="primary"):
        if not selected_services:
            st.warning("⚠️ Please select at least one service")
            return
        
        st.header("🛠️ Service Configuration")
        
        total_cost = 0
        configurations = {}
        
        # Configure each selected service with unique keys
        for category, services in selected_services.items():
            st.subheader(f"{category} Services")
            
            for i, service in enumerate(services):
                with st.expander(f"⚙️ {service}", expanded=True):
                    st.markdown(f"*{AWS_SERVICES[category][service]}*")
                    
                    # Generate unique key for each service configuration
                    service_key = f"{category}_{service}_{i}"
                    config = render_service_configurator(service, service_key)
                    cost = InnovativePricing.calculate_price(
                        service, config, usage_pattern
                    )
                    
                    st.metric("Estimated Monthly Cost", f"${cost:,.2f}")
                    total_cost += cost
                    
                    configurations[service] = {
                        "config": config,
                        "cost": cost
                    }
        
        # ... rest of the main function ...

def render_service_configurator(service: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.markdown("##### Instance Configuration")
        
        # Instance family selection
        family = st.selectbox(
            "Instance Family",
            list(INSTANCE_FAMILIES.keys()),
            help="Choose instance family based on your workload"
        )
        
        # Instance type selection with specs display
        instance_types = list(INSTANCE_FAMILIES[family].keys())
        selected_type = st.selectbox("Instance Type", instance_types)
        specs = INSTANCE_FAMILIES[family][selected_type]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("vCPU", specs["vCPU"])
        with col2:
            st.metric("Memory (GiB)", specs["Memory"])
        with col3:
            st.metric("Price/Hour", f"${specs['Price']}")
        
        config["instance_type"] = selected_type
        config["instance_count"] = st.number_input("Number of Instances", 1, 100, 1)
        config["storage_gb"] = st.number_input("EBS Storage per Instance (GB)", 8, 16384, 30)
    
    elif service == "Amazon RDS":
        st.markdown("##### Database Configuration")
        
        config["engine"] = st.selectbox(
            "Database Engine",
            ["PostgreSQL", "MySQL", "MariaDB", "Oracle", "SQL Server"]
        )
        
        config["instance_type"] = st.selectbox(
            "Instance Type",
            ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large", 
             "db.r5.large", "db.r5.xlarge"]
        )
        
        config["storage_gb"] = st.number_input("Storage (GB)", 20, 65536, 100)
        config["multi_az"] = st.checkbox("Multi-AZ Deployment")
        config["backup_retention"] = st.slider("Backup Retention (Days)", 0, 35, 7)
    
    elif service == "Amazon S3":
        st.markdown("##### Storage Configuration")
        
        config["storage_class"] = st.selectbox(
            "Storage Class",
            ["Standard", "Intelligent-Tiering", "Standard-IA", 
             "One Zone-IA", "Glacier", "Glacier Deep Archive"]
        )
        
        config["storage_gb"] = st.number_input("Storage (GB)", 1, 1000000, 100)
        config["requests_per_month"] = st.number_input(
            "Estimated Monthly Requests (thousands)",
            1, 1000000, 100
        ) * 1000
    
    elif service == "AWS Lambda":
        st.markdown("##### Function Configuration")
        
        config["memory_mb"] = st.select_slider(
            "Memory (MB)",
            options=[128, 256, 512, 1024, 2048, 4096, 8192, 10240]
        )
        config["timeout_seconds"] = st.slider("Timeout (seconds)", 1, 900, 30)
        config["requests_per_month"] = st.number_input(
            "Monthly Invocations",
            1000, 1000000000, 100000
        )
        config["avg_duration_ms"] = st.slider("Average Duration (ms)", 1, 1000, 100)
    
    elif service == "Amazon ECS" or service == "Amazon EKS":
        st.markdown("##### Container Configuration")
        
        config["cluster_type"] = st.radio(
            "Cluster Type",
            ["Fargate", "EC2"] if service == "Amazon ECS" else ["Managed Node Groups"]
        )
        
        if config["cluster_type"] in ["EC2", "Managed Node Groups"]:
            config["node_instance_type"] = st.selectbox(
                "Node Instance Type",
                ["t3.medium", "t3.large", "m5.large", "m5.xlarge"]
            )
            config["node_count"] = st.number_input("Number of Nodes", 1, 100, 2)
        else:
            config["vcpu"] = st.number_input("vCPU Units", 0.25, 16.0, 1.0, 0.25)
            config["memory_gb"] = st.number_input("Memory (GB)", 0.5, 120.0, 2.0, 0.5)
        
        config["desired_tasks"] = st.number_input("Desired Number of Tasks/Pods", 1, 1000, 2)
    
    elif service == "Amazon Bedrock":
        st.markdown("##### Model Configuration")
        
        config["model"] = st.selectbox(
            "Foundation Model",
            ["Claude", "Llama 2", "Stable Diffusion", "Jurassic"]
        )
        config["requests_per_month"] = st.number_input(
            "Monthly Requests",
            1000, 10000000, 10000
        )
        config["avg_tokens"] = st.number_input("Average Tokens per Request", 100, 10000, 1000)
    
    elif service == "AWS WAF":
        st.markdown("##### WAF Configuration")
        
        config["web_acls"] = st.number_input("Number of Web ACLs", 1, 100, 1)
        config["rules"] = st.number_input("Number of Rules", 1, 1000, 5)
        
        rule_types = st.multiselect(
            "Rule Types",
            ["Rate Limiting", "IP Reputation", "SQL Injection", "XSS Protection",
             "Geo Blocking", "Custom Rules"]
        )
        config["rule_types"] = rule_types
    
    # Add region selection for all services
    config["region"] = st.selectbox(
        "Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    )
    
    return config
# Modify the main function
def main():
    st.set_page_config(page_title="AWS Cloud Package Builder", layout="wide")
    st.title("🚀 AWS Cloud Package Builder")
    
    # Project Requirements
    with st.expander("📋 Project Requirements", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            workload_type = st.selectbox(
                "Workload Type",
                ["Web Application", "Data Processing", "Machine Learning", 
                 "Microservices", "Serverless", "Container-based"]
            )
            monthly_budget = st.number_input("Monthly Budget ($)", 100, 1000000, 5000)
            performance_tier = st.selectbox(
                "Performance Tier", 
                ["Development", "Production", "Enterprise"]
            )
        with col2:
            usage_pattern = st.selectbox(
                "Usage Pattern",
                ["sporadic", "normal", "intensive"],
                help="How will the services be used?"
            )
            data_volume_gb = st.number_input("Data Volume (GB)", 1, 100000, 100)
            expected_users = st.number_input("Expected Users", 1, 1000000, 1000)
    
    # Service Selection
    selected_services = ServiceSelector.render_service_selection()
    
    if st.button("Generate Configuration", type="primary"):
        if not selected_services:
            st.warning("⚠️ Please select at least one service")
            return
        
        st.header("🛠️ Service Configuration")
        
        total_cost = 0
        configurations = {}
        
        # Configure each selected service
        for category, services in selected_services.items():
            st.subheader(f"{category} Services")
            
            for service in services:
                with st.expander(f"⚙️ {service}", expanded=True):
                    st.markdown(f"*{AWS_SERVICES[category][service]}*")
                    
                    config = render_service_configurator(service)
                    cost = InnovativePricing.calculate_price(
                        service, config, usage_pattern
                    )
                    
                    st.metric("Estimated Monthly Cost", f"${cost:,.2f}")
                    total_cost += cost
                    
                    configurations[service] = {
                        "config": config,
                        "cost": cost
                    }
        
        # Cost Summary
        st.header("💰 Cost Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Monthly Cost", f"${total_cost:,.2f}")
        with col2:
            st.metric("Services Selected", len(configurations))
        with col3:
            budget_used = (total_cost / monthly_budget) * 100
            st.metric("Budget Utilized", f"{budget_used:.1f}%")
        
        # Export Configuration
        st.download_button(
            "📥 Export Configuration",
            data=json.dumps({
                "requirements": {
                    "workload_type": workload_type,
                    "monthly_budget": monthly_budget,
                    "performance_tier": performance_tier,
                    "usage_pattern": usage_pattern,
                    "data_volume_gb": data_volume_gb,
                    "expected_users": expected_users
                },
                "services": configurations
            }, indent=2),
            file_name="aws_config.json",
            mime="application/json"
        )

def main():
    # ... existing code ...
    
    if st.button("Generate Configuration", type="primary"):
        if not selected_services:
            st.warning("⚠️ Please select at least one service")
            return
        
        st.header("🛠️ Service Configuration")
        
        total_cost = 0
        configurations = {}
        
        # Configure each selected service with unique keys
        for category, services in selected_services.items():
            st.subheader(f"{category} Services")
            
            for i, service in enumerate(services):
                with st.expander(f"⚙️ {service}", expanded=True):
                    st.markdown(f"*{AWS_SERVICES[category][service]}*")
                    
                    # Generate unique key for each service configuration
                    service_key = f"{category}_{service}_{i}"
                    config = render_service_configurator(service, service_key)
                    cost = InnovativePricing.calculate_price(
                        service, config, usage_pattern
                    )
                    
                    st.metric("Estimated Monthly Cost", f"${cost:,.2f}")
                    total_cost += cost
                    
                    configurations[service] = {
                        "config": config,
                        "cost": cost
                    }
if __name__ == "__main__":
    main()