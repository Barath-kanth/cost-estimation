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

    def get_service_pricing(self, service: str, region: str) -> Dict:
        """Get pricing data for a specific service and region"""
        try:
            url = f"{self.BASE_URL}/offers/v1.0/aws/{service}/current/{region}/index.json"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return self._get_default_pricing(service)
        except Exception as e:
            st.warning(f"Using default pricing for {service} due to: {str(e)}")
            return self._get_default_pricing(service)

    def _get_default_pricing(self, service: str) -> Dict:
        """Default pricing for common services"""
        return {
            "AmazonEC2": {
                "t3.micro": 0.0104,
                "t3.small": 0.0208,
                "t3.medium": 0.0416,
                "t3.large": 0.0832
            },
            "AmazonS3": {
                "standard": 0.023,
                "intelligent_tiering": 0.0125
            },
            "AmazonRDS": {
                "db.t3.micro": 0.017,
                "db.t3.small": 0.034,
                "db.t3.medium": 0.068
            }
        }.get(service, {})

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
    optimization_tips: List[str]
    compliance_notes: str
    recommendations: Dict[str, List[str]]

# ... Rest of your existing agent classes (ComputeAgent, StorageAgent, etc.) ...

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
                if agent_recommendations:
                    recommendations.extend(agent_recommendations)

        # Filter recommendations based on budget
        filtered_recommendations = self._filter_by_budget(
            recommendations, 
            requirements.monthly_budget
        )

        # Generate service-specific recommendations
        service_recommendations = self._generate_service_recommendations(
            filtered_recommendations,
            requirements
        )

        return CloudPackage(
            total_monthly_cost=sum(r.monthly_cost for r in filtered_recommendations),
            services=filtered_recommendations,
            optimization_tips=self._generate_optimization_tips(filtered_recommendations),
            compliance_notes=self._generate_compliance_notes(requirements, filtered_recommendations),
            recommendations=service_recommendations
        )

    def _generate_service_recommendations(self, recommendations: List[ServiceRecommendation], 
                                       requirements: CustomerRequirement) -> Dict[str, List[str]]:
        """Generate detailed recommendations for each service"""
        service_recommendations = {}
        
        for rec in recommendations:
            if rec.service_name == "Amazon EC2":
                service_recommendations["Compute"] = [
                    f"Instance Type: {rec.configuration['instance_type']} optimized for {requirements.performance_tier}",
                    "Enable detailed monitoring for better scaling decisions",
                    "Implement proper instance tagging for cost allocation",
                    f"Configure Auto Scaling group with min={max(1, requirements.expected_users//1000)} instances"
                ]
            
            elif rec.service_name == "Amazon RDS":
                service_recommendations["Database"] = [
                    f"Database Instance: {rec.configuration['instance_type']}",
                    "Enable automated backups with 7-day retention",
                    "Set up read replicas for better performance",
                    "Configure Parameter Groups for workload optimization"
                ]
            
            elif rec.service_name == "Amazon S3":
                service_recommendations["Storage"] = [
                    f"Storage Class: {rec.configuration['storage_class']}",
                    "Enable versioning for critical data",
                    "Configure lifecycle rules for cost optimization",
                    "Set up bucket policies for secure access"
                ]
            
            elif rec.service_name == "AWS WAF":
                service_recommendations["Security"] = [
                    "Deploy managed rules for common vulnerabilities",
                    "Set up rate limiting rules",
                    "Enable logging for security analysis",
                    "Implement custom rules based on application needs"
                ]

        return service_recommendations

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
    
    availability_target = st.sidebar.selectbox(
        "Availability Target",
        ["99.9%", "99.99%", "99.999%"]
    )
    
    compliance_needs = st.sidebar.multiselect(
        "Compliance Requirements",
        ["HIPAA", "PCI DSS", "SOC 2", "GDPR", "ISO 27001"]
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


        
        # ... rest of your existing code ...

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
            
            # Detailed Recommendations
            st.subheader("🔧 Service Configurations & Recommendations")
            for category, recs in package.recommendations.items():
                with st.expander(f"{category} Configuration"):
                    for rec in recs:
                        st.markdown(f"- {rec}")
            
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
                        "compliance_notes": package.compliance_notes,
                        "recommendations": package.recommendations
                    }
                }, indent=2),
                file_name="cloud_package.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()