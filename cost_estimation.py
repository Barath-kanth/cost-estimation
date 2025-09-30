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
        time_multiplier = 0.8 if 0 <= current_hour < 6 else 1.0  # Night time discount
        
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
            vcpu = float(instance_type.split('.')[-1].replace('xlarge', '')) * 2
            base_price = vcpu * 0.05 * 730  # $0.05 per vCPU hour
            
        elif service == "Amazon RDS":
            storage_gb = config.get('storage_gb', 20)
            base_price = storage_gb * 0.115 + 0.17 * 730  # Storage + compute
            
        elif service == "AWS Lambda":
            requests = config.get('requests_per_month', 1000000)
            memory = config.get('memory_mb', 128)
            base_price = (requests * 0.0000002) + (memory * 0.0000166667 * 730)
            
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

if __name__ == "__main__":
    main()