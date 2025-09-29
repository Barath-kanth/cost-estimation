import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

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
    configuration: Dict
    monthly_cost: float
    justification: str
    alternatives: List[str]

@dataclass
class CloudPackage:
    total_monthly_cost: float
    services: List[ServiceRecommendation]
    architecture_diagram: str
    optimization_tips: List[str]
    compliance_notes: str

class CloudServiceAgent:
    """Base agent class for cloud service recommendations"""
    def __init__(self, service_category: str):
        self.category = service_category
        self.price_list = AWSPriceList()

    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        raise NotImplementedError

class ComputeAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if requirements.workload_type == "serverless":
            return self._recommend_lambda(requirements)
        return self._recommend_ec2(requirements)

    def _recommend_ec2(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        instance_types = self._get_suitable_instances(requirements)
        pricing = self.price_list.get_service_pricing("AmazonEC2", requirements.regions[0])
        # Implementation details for EC2 recommendation

class StorageAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if requirements.data_volume_gb > 1000:
            return self._recommend_s3(requirements)
        return self._recommend_ebs(requirements)

class DatabaseAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if "High Availability" in requirements.special_requirements:
            return self._recommend_aurora(requirements)
        return self._recommend_rds(requirements)

class NetworkingAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        recommendations = []
        if "Content Delivery" in requirements.special_requirements:
            recommendations.extend(self._recommend_cloudfront(requirements))
        return recommendations

class SecurityAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        recommendations = []
        if requirements.compliance_needs:
            recommendations.extend(self._recommend_security_services(requirements))
        return recommendations

class CloudPackageBuilder:
    def __init__(self):
        self.agents = {
            "compute": ComputeAgent("compute"),
            "storage": StorageAgent("storage"),
            "database": DatabaseAgent("database"),
            "networking": NetworkingAgent("networking"),
            "security": SecurityAgent("security")
        }
        self.price_list = AWSPriceList()

    def create_package(self, requirements: CustomerRequirement) -> CloudPackage:
        recommendations = []
        
        # Parallel agent execution
        with ThreadPoolExecutor() as executor:
            future_to_agent = {
                executor.submit(agent.recommend, requirements): name 
                for name, agent in self.agents.items()
            }
            
            for future in future_to_agent:
                agent_recommendations = future.result()
                recommendations.extend(agent_recommendations)

        # Filter recommendations based on budget
        filtered_recommendations = self._filter_by_budget(
            recommendations, 
            requirements.monthly_budget
        )

        return CloudPackage(
            total_monthly_cost=sum(r.monthly_cost for r in filtered_recommendations),
            services=filtered_recommendations,
            architecture_diagram=self._generate_architecture_diagram(filtered_recommendations),
            optimization_tips=self._generate_optimization_tips(filtered_recommendations),
            compliance_notes=self._generate_compliance_notes(requirements, filtered_recommendations)
        )

def main():
    st.set_page_config(page_title="AWS Cloud Package Builder", layout="wide")
    st.title("🚀 AWS Cloud Package Builder")

    # Get available regions
    price_list = AWSPriceList()
    available_regions = price_list.get_regions()

    # Sidebar for requirements
    st.sidebar.header("Requirements")
    
    workload_type = st.sidebar.selectbox(
        "Workload Type",
        ["Web Application", "Data Processing", "Machine Learning", "Microservices"]
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
        default=[available_regions[0]]
    )
    
    availability_target = st.sidebar.selectbox(
        "Availability Target",
        ["99.9%", "99.99%", "99.999%"]
    )
    
    compliance_needs = st.sidebar.multiselect(
        "Compliance Requirements",
        ["HIPAA", "PCI DSS", "SOC 2", "GDPR", "ISO 27001"]
    )
    
    expected_users = st.sidebar.number_input(
        "Expected Users",
        min_value=1,
        max_value=1000000,
        value=1000
    )
    
    data_volume_gb = st.sidebar.number_input(
        "Data Volume (GB)",
        min_value=1,
        max_value=100000,
        value=100
    )
    
    special_requirements = st.sidebar.multiselect(
        "Special Requirements",
        ["Auto Scaling", "Content Delivery", "Backup & DR", "High Availability"]
    )

    # Create package button
    if st.sidebar.button("Generate Package", type="primary"):
        requirements = CustomerRequirement(
            workload_type=workload_type,
            monthly_budget=monthly_budget,
            performance_tier=performance_tier,
            regions=regions,
            availability_target=availability_target,
            compliance_needs=compliance_needs,
            expected_users=expected_users,
            data_volume_gb=data_volume_gb,
            special_requirements=special_requirements
        )
        
        builder = CloudPackageBuilder()
        
        with st.spinner("🤖 Generating your cloud package..."):
            package = builder.create_package(requirements)
            
            # Display package details
            st.header("📦 Your Cloud Package")
            
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Monthly Cost", f"${package.total_monthly_cost:,.2f}")
            with col2:
                st.metric("Services", len(package.services))
            with col3:
                st.metric("Regions", len(regions))
            
            # Architecture diagram
            st.subheader("Architecture")
            st.mermaid(package.architecture_diagram)
            
            # Services table
            st.subheader("Services Breakdown")
            services_df = pd.DataFrame([
                {
                    "Service": rec.service_name,
                    "Monthly Cost": f"${rec.monthly_cost:,.2f}",
                    "Configuration": json.dumps(rec.configuration, indent=2),
                    "Justification": rec.justification
                }
                for rec in package.services
            ])
            st.dataframe(services_df)
            
            # Optimization tips
            st.subheader("💡 Optimization Tips")
            for tip in package.optimization_tips:
                st.markdown(f"- {tip}")
            
            # Compliance notes
            if package.compliance_notes:
                st.subheader("🛡️ Compliance Notes")
                st.info(package.compliance_notes)
            
            # Download options
            st.download_button(
                "📥 Download Package Details",
                data=json.dumps({
                    "requirements": requirements.__dict__,
                    "package": {
                        "total_monthly_cost": package.total_monthly_cost,
                        "services": [s.__dict__ for s in package.services],
                        "optimization_tips": package.optimization_tips,
                        "compliance_notes": package.compliance_notes
                    }
                }, indent=2),
                file_name="cloud_package.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()