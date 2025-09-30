import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

@dataclass
class AWSPriceList:
    """AWS Price List API Handler"""
    BASE_URL = "https://pricing.us-east-1.amazonaws.com"
    
    def get_regions(self) -> List[str]:
        """Get list of AWS regions"""
        try:
            url = f"{self.BASE_URL}/meta/regions"
            response = requests.get(url)
            if response.status_code == 200:
                return sorted(list(response.json().keys()))
            return self._get_default_regions()
        except Exception as e:
            st.warning(f"Using default regions due to: {str(e)}")
            return self._get_default_regions()

    def _get_default_regions(self) -> List[str]:
        return [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
        ]

    def get_ec2_pricing(self, instance_type: str, region: str = "us-east-1") -> float:
        """Get EC2 instance pricing"""
        pricing_map = {
            "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208,
            "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664,
            "t3.2xlarge": 0.3328, "m5.large": 0.096, "m5.xlarge": 0.192,
            "m5.2xlarge": 0.384, "c5.large": 0.085, "c5.xlarge": 0.17,
            "r5.large": 0.126, "r5.xlarge": 0.252
        }
        return pricing_map.get(instance_type, 0.10)

    def get_rds_pricing(self, instance_type: str, engine: str = "postgres") -> float:
        """Get RDS instance pricing"""
        pricing_map = {
            "db.t3.micro": 0.017, "db.t3.small": 0.034,
            "db.t3.medium": 0.068, "db.t3.large": 0.136,
            "db.t3.xlarge": 0.272, "db.m5.large": 0.192,
            "db.m5.xlarge": 0.384, "db.r5.large": 0.24
        }
        return pricing_map.get(instance_type, 0.068)

    def get_s3_pricing(self, storage_class: str) -> float:
        """Get S3 storage pricing per GB"""
        pricing_map = {
            "Standard": 0.023, "Intelligent-Tiering": 0.0125,
            "Standard-IA": 0.0125, "One Zone-IA": 0.01,
            "Glacier": 0.004, "Glacier Deep Archive": 0.00099
        }
        return pricing_map.get(storage_class, 0.023)

@dataclass
class CustomerRequirement:
    workload_type: str
    monthly_budget: float
    performance_tier: str
    regions: List[str]
    availability_target: str
    compliance_needs: List[str]
    expected_users: int
    data_volume_gb: float
    special_requirements: List[str]

@dataclass
class ServiceRecommendation:
    service_name: str
    service_type: str
    base_config: Dict
    monthly_cost: float
    justification: str

class CloudServiceAgent:
    """Base agent class for cloud service recommendations"""
    def __init__(self, service_category: str):
        self.category = service_category
        self.price_list = AWSPriceList()

    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        raise NotImplementedError

class ComputeAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if requirements.workload_type == "Serverless":
            return self._recommend_lambda(requirements)
        return self._recommend_ec2(requirements)

    def _recommend_ec2(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        instance_type = self._get_default_instance(requirements)
        hourly_rate = self.price_list.get_ec2_pricing(instance_type, requirements.regions[0])
        monthly_cost = hourly_rate * 730
        
        return [ServiceRecommendation(
            service_name="Amazon EC2",
            service_type="compute",
            base_config={
                "instance_type": instance_type,
                "region": requirements.regions[0],
                "instance_count": 1,
                "storage_gb": 30
            },
            monthly_cost=monthly_cost,
            justification=f"Recommended for {requirements.workload_type} workload"
        )]

    def _recommend_lambda(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        requests_per_month = requirements.expected_users * 100
        monthly_cost = (requests_per_month * 0.0000002) + (requests_per_month * 0.128 * 0.1 * 0.0000166667)
        
        return [ServiceRecommendation(
            service_name="AWS Lambda",
            service_type="compute",
            base_config={
                "memory_mb": 128,
                "timeout_seconds": 30,
                "requests_per_month": requests_per_month
            },
            monthly_cost=monthly_cost,
            justification="Serverless compute for event-driven workloads"
        )]

    def _get_default_instance(self, requirements: CustomerRequirement) -> str:
        tier_map = {
            "Development": "t3.small",
            "Production": "t3.medium",
            "Enterprise": "t3.large"
        }
        return tier_map.get(requirements.performance_tier, "t3.medium")

class StorageAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        storage_class = "Standard"
        price_per_gb = self.price_list.get_s3_pricing(storage_class)
        monthly_cost = requirements.data_volume_gb * price_per_gb
        
        return [ServiceRecommendation(
            service_name="Amazon S3",
            service_type="storage",
            base_config={
                "storage_class": storage_class,
                "storage_gb": requirements.data_volume_gb,
                "versioning": False
            },
            monthly_cost=monthly_cost,
            justification="Scalable object storage for your data"
        )]

class DatabaseAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        instance_type = "db.t3.medium"
        hourly_rate = self.price_list.get_rds_pricing(instance_type)
        storage_cost = requirements.data_volume_gb * 0.115
        monthly_cost = (hourly_rate * 730) + storage_cost
        
        return [ServiceRecommendation(
            service_name="Amazon RDS",
            service_type="database",
            base_config={
                "instance_type": instance_type,
                "engine": "PostgreSQL",
                "storage_gb": requirements.data_volume_gb,
                "multi_az": False
            },
            monthly_cost=monthly_cost,
            justification="Managed relational database service"
        )]

class CloudPackageBuilder:
    def __init__(self):
        self.agents = {
            "compute": ComputeAgent("compute"),
            "storage": StorageAgent("storage"),
            "database": DatabaseAgent("database")
        }
        self.price_list = AWSPriceList()

    def create_initial_recommendations(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        recommendations = []
        
        with ThreadPoolExecutor() as executor:
            future_to_agent = {
                executor.submit(agent.recommend, requirements): name 
                for name, agent in self.agents.items()
            }
            
            for future in future_to_agent:
                agent_recommendations = future.result()
                if agent_recommendations:
                    recommendations.extend(agent_recommendations)

        return recommendations

    def calculate_service_cost(self, service_name: str, config: Dict) -> float:
        """Dynamically calculate cost based on configuration"""
        if service_name == "Amazon EC2":
            hourly_rate = self.price_list.get_ec2_pricing(config['instance_type'])
            instance_cost = hourly_rate * 730 * config.get('instance_count', 1)
            storage_cost = config.get('storage_gb', 30) * 0.10
            return instance_cost + storage_cost
            
        elif service_name == "AWS Lambda":
            requests = config.get('requests_per_month', 1000000)
            memory_gb = config.get('memory_mb', 128) / 1024
            duration = config.get('timeout_seconds', 30)
            gb_seconds = requests * memory_gb * (duration / 3600)
            return (requests * 0.0000002) + (gb_seconds * 0.0000166667)
            
        elif service_name == "Amazon S3":
            storage_gb = config.get('storage_gb', 100)
            storage_class = config.get('storage_class', 'Standard')
            price_per_gb = self.price_list.get_s3_pricing(storage_class)
            return storage_gb * price_per_gb
            
        elif service_name == "Amazon RDS":
            instance_type = config.get('instance_type', 'db.t3.medium')
            storage_gb = config.get('storage_gb', 100)
            multi_az = config.get('multi_az', False)
            hourly_rate = self.price_list.get_rds_pricing(instance_type)
            instance_cost = hourly_rate * 730 * (2 if multi_az else 1)
            storage_cost = storage_gb * 0.115
            return instance_cost + storage_cost
            
        return 0.0

def render_ec2_configurator(service: ServiceRecommendation, key_prefix: str):
    """Render EC2 configuration UI"""
    st.markdown("### ⚙️ Configure EC2 Instance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        instance_type = st.selectbox(
            "Instance Type",
            ["t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", 
             "t3.xlarge", "t3.2xlarge", "m5.large", "m5.xlarge", "c5.large"],
            index=2,
            key=f"{key_prefix}_instance"
        )
        
        instance_count = st.number_input(
            "Number of Instances",
            min_value=1,
            max_value=20,
            value=1,
            key=f"{key_prefix}_count"
        )
    
    with col2:
        storage_gb = st.number_input(
            "Storage (GB)",
            min_value=8,
            max_value=16384,
            value=30,
            key=f"{key_prefix}_storage"
        )
        
        auto_scaling = st.checkbox(
            "Enable Auto Scaling",
            key=f"{key_prefix}_autoscale"
        )
    
    return {
        "instance_type": instance_type,
        "instance_count": instance_count,
        "storage_gb": storage_gb,
        "auto_scaling": auto_scaling
    }

def render_lambda_configurator(service: ServiceRecommendation, key_prefix: str):
    """Render Lambda configuration UI"""
    st.markdown("### ⚙️ Configure Lambda Function")
    
    col1, col2 = st.columns(2)
    
    with col1:
        memory_mb = st.selectbox(
            "Memory (MB)",
            [128, 256, 512, 1024, 2048, 3008],
            index=0,
            key=f"{key_prefix}_memory"
        )
        
        timeout_seconds = st.slider(
            "Timeout (seconds)",
            min_value=1,
            max_value=900,
            value=30,
            key=f"{key_prefix}_timeout"
        )
    
    with col2:
        requests_per_month = st.number_input(
            "Requests per Month",
            min_value=1000,
            max_value=100000000,
            value=1000000,
            key=f"{key_prefix}_requests"
        )
    
    return {
        "memory_mb": memory_mb,
        "timeout_seconds": timeout_seconds,
        "requests_per_month": requests_per_month
    }

def render_s3_configurator(service: ServiceRecommendation, key_prefix: str):
    """Render S3 configuration UI"""
    st.markdown("### ⚙️ Configure S3 Storage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        storage_gb = st.number_input(
            "Storage (GB)",
            min_value=1,
            max_value=1000000,
            value=int(service.base_config.get('storage_gb', 100)),
            key=f"{key_prefix}_storage"
        )
        
        storage_class = st.selectbox(
            "Storage Class",
            ["Standard", "Intelligent-Tiering", "Standard-IA", 
             "One Zone-IA", "Glacier", "Glacier Deep Archive"],
            key=f"{key_prefix}_class"
        )
    
    with col2:
        versioning = st.checkbox(
            "Enable Versioning",
            key=f"{key_prefix}_versioning"
        )
        
        lifecycle_rules = st.checkbox(
            "Enable Lifecycle Rules",
            key=f"{key_prefix}_lifecycle"
        )
    
    return {
        "storage_gb": storage_gb,
        "storage_class": storage_class,
        "versioning": versioning,
        "lifecycle_rules": lifecycle_rules
    }

def render_rds_configurator(service: ServiceRecommendation, key_prefix: str):
    """Render RDS configuration UI"""
    st.markdown("### ⚙️ Configure RDS Database")
    
    col1, col2 = st.columns(2)
    
    with col1:
        instance_type = st.selectbox(
            "Instance Type",
            ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
             "db.t3.xlarge", "db.m5.large", "db.r5.large"],
            index=2,
            key=f"{key_prefix}_instance"
        )
        
        engine = st.selectbox(
            "Database Engine",
            ["PostgreSQL", "MySQL", "MariaDB", "Oracle", "SQL Server"],
            key=f"{key_prefix}_engine"
        )
    
    with col2:
        storage_gb = st.number_input(
            "Storage (GB)",
            min_value=20,
            max_value=65536,
            value=int(service.base_config.get('storage_gb', 100)),
            key=f"{key_prefix}_storage"
        )
        
        multi_az = st.checkbox(
            "Multi-AZ Deployment",
            key=f"{key_prefix}_multiaz"
        )
    
    return {
        "instance_type": instance_type,
        "engine": engine,
        "storage_gb": storage_gb,
        "multi_az": multi_az
    }

def main():
    st.set_page_config(page_title="Dynamic AWS Cloud Package Builder", layout="wide")
    st.title("🚀 Dynamic AWS Cloud Package Builder")
    st.markdown("Generate tailored cloud packages and configure services with real-time pricing")

    # Initialize session state
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    if 'show_configurator' not in st.session_state:
        st.session_state.show_configurator = False

    price_list = AWSPriceList()
    available_regions = price_list.get_regions()

    # Step 1: Requirements Input
    st.sidebar.header("📋 Step 1: Requirements")
    
    workload_type = st.sidebar.selectbox(
        "Workload Type",
        ["Web Application", "Data Processing", "Machine Learning", "Microservices", "Serverless"]
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
    
    regions = st.sidebar.multiselect(
        "Regions",
        available_regions,
        default=[available_regions[0] if available_regions else "us-east-1"]
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
        ["Auto Scaling", "Content Delivery", "Backup & DR", "High Availability"]
    )
    
    compliance_needs = st.sidebar.multiselect(
        "Compliance Requirements",
        ["HIPAA", "PCI DSS", "SOC 2", "GDPR", "ISO 27001"]
    )

    if st.sidebar.button("🔍 Generate Recommendations", type="primary"):
        requirements = CustomerRequirement(
            workload_type=workload_type,
            monthly_budget=monthly_budget,
            performance_tier=performance_tier,
            regions=regions,
            availability_target="99.9%",
            compliance_needs=compliance_needs,
            expected_users=expected_users,
            data_volume_gb=data_volume_gb,
            special_requirements=special_requirements
        )
        
        builder = CloudPackageBuilder()
        
        with st.spinner("🤖 Analyzing requirements and generating recommendations..."):
            st.session_state.recommendations = builder.create_initial_recommendations(requirements)
            st.session_state.show_configurator = True
            st.session_state.builder = builder

    # Step 2: Configure Services
    if st.session_state.show_configurator and st.session_state.recommendations:
        st.header("⚙️ Step 2: Configure Your Services")
        st.markdown("Customize each service configuration and see pricing update in real-time")
        
        configured_services = []
        total_cost = 0.0
        
        for idx, service in enumerate(st.session_state.recommendations):
            with st.expander(f"🔧 {service.service_name} - {service.justification}", expanded=True):
                config = None
                
                if service.service_name == "Amazon EC2":
                    config = render_ec2_configurator(service, f"ec2_{idx}")
                elif service.service_name == "AWS Lambda":
                    config = render_lambda_configurator(service, f"lambda_{idx}")
                elif service.service_name == "Amazon S3":
                    config = render_s3_configurator(service, f"s3_{idx}")
                elif service.service_name == "Amazon RDS":
                    config = render_rds_configurator(service, f"rds_{idx}")
                
                if config:
                    # Calculate dynamic cost
                    cost = st.session_state.builder.calculate_service_cost(service.service_name, config)
                    total_cost += cost
                    
                    st.success(f"💰 Estimated Monthly Cost: **${cost:,.2f}**")
                    
                    configured_services.append({
                        "service": service.service_name,
                        "config": config,
                        "cost": cost
                    })
        
        # Display Summary
        st.markdown("---")
        st.header("📊 Package Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Monthly Cost", f"${total_cost:,.2f}")
        with col2:
            st.metric("Number of Services", len(configured_services))
        with col3:
            budget_status = "✅ Within Budget" if total_cost <= monthly_budget else "⚠️ Over Budget"
            st.metric("Budget Status", budget_status)
        
        # Detailed breakdown
        st.subheader("💳 Cost Breakdown")
        breakdown_df = pd.DataFrame([
            {
                "Service": svc["service"],
                "Monthly Cost": f"${svc['cost']:,.2f}",
                "% of Total": f"{(svc['cost']/total_cost*100):.1f}%"
            }
            for svc in configured_services
        ])
        st.dataframe(breakdown_df, use_container_width=True)
        
        # Download package
        st.download_button(
            "📥 Download Complete Package Configuration",
            data=json.dumps({
                "total_cost": total_cost,
                "services": configured_services,
                "generated_at": datetime.now().isoformat()
            }, indent=2),
            file_name=f"cloud_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()