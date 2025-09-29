import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# AWS Price List API Handler
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

    def _get_suitable_instances(self, requirements: CustomerRequirement) -> List[str]:
        """Get suitable EC2 instances based on requirements"""
        if requirements.performance_tier == "Development":
            return ["t3.micro", "t3.small"]
        elif requirements.performance_tier == "Production":
            return ["t3.medium", "t3.large"]
        else:  # Enterprise
            return ["t3.large", "t3.xlarge"]

class ComputeAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if requirements.workload_type == "serverless":
            return self._recommend_lambda(requirements)
        return self._recommend_ec2(requirements)

    def _recommend_ec2(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        instance_types = self._get_suitable_instances(requirements)
        pricing_data = self.price_list.get_service_pricing("AmazonEC2", requirements.regions[0])
        
        recommendations = []
        for instance_type in instance_types:
            monthly_cost = self._calculate_ec2_cost(instance_type, requirements)
            if monthly_cost <= requirements.monthly_budget:
                recommendations.append(
                    ServiceRecommendation(
                        service_name="Amazon EC2",
                        configuration={
                            "instance_type": instance_type,
                            "region": requirements.regions[0],
                            "auto_scaling": "Auto Scaling" in requirements.special_requirements
                        },
                        monthly_cost=monthly_cost,
                        justification=f"Selected {instance_type} based on {requirements.performance_tier} tier requirements",
                        alternatives=["AWS Lambda", "AWS Fargate"]
                    )
                )
        return recommendations

    def _recommend_lambda(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        # Lambda recommendation implementation
        monthly_cost = self._calculate_lambda_cost(requirements)
        return [
            ServiceRecommendation(
                service_name="AWS Lambda",
                configuration={
                    "memory": 128,
                    "timeout": 30,
                    "concurrent_executions": requirements.expected_users // 100
                },
                monthly_cost=monthly_cost,
                justification="Serverless compute for cost-effective scaling",
                alternatives=["Amazon EC2", "AWS Fargate"]
            )
        ]

    def _calculate_ec2_cost(self, instance_type: str, requirements: CustomerRequirement) -> float:
        base_price = self.price_list._get_default_pricing("AmazonEC2").get(instance_type, 0.0)
        hours_per_month = 730
        return base_price * hours_per_month

    def _calculate_lambda_cost(self, requirements: CustomerRequirement) -> float:
        requests_per_month = requirements.expected_users * 100  # Estimate
        gb_seconds = requests_per_month * 0.128 * 0.1  # 128MB, 100ms average
        return (requests_per_month * 0.0000002) + (gb_seconds * 0.0000166667)

class StorageAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if requirements.data_volume_gb > 1000:
            return self._recommend_s3(requirements)
        return self._recommend_ebs(requirements)

    def _recommend_s3(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        monthly_cost = self._calculate_s3_cost(requirements)
        return [
            ServiceRecommendation(
                service_name="Amazon S3",
                configuration={
                    "storage_class": "Standard",
                    "lifecycle_rules": True if requirements.data_volume_gb > 5000 else False
                },
                monthly_cost=monthly_cost,
                justification="Scalable object storage with high durability",
                alternatives=["Amazon EFS", "Amazon EBS"]
            )
        ]

    def _calculate_s3_cost(self, requirements: CustomerRequirement) -> float:
        pricing = self.price_list._get_default_pricing("AmazonS3")
        return requirements.data_volume_gb * pricing.get("standard", 0.023)

class DatabaseAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        if "High Availability" in requirements.special_requirements:
            return self._recommend_aurora(requirements)
        return self._recommend_rds(requirements)

    def _recommend_rds(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        instance_type = "db.t3.medium"
        monthly_cost = self._calculate_rds_cost(instance_type, requirements)
        return [
            ServiceRecommendation(
                service_name="Amazon RDS",
                configuration={
                    "instance_type": instance_type,
                    "engine": "PostgreSQL",
                    "multi_az": "High Availability" in requirements.special_requirements
                },
                monthly_cost=monthly_cost,
                justification="Managed relational database service",
                alternatives=["Amazon Aurora", "Amazon DynamoDB"]
            )
        ]

    def _calculate_rds_cost(self, instance_type: str, requirements: CustomerRequirement) -> float:
        pricing = self.price_list._get_default_pricing("AmazonRDS")
        base_cost = pricing.get(instance_type, 0.068) * 730
        storage_cost = requirements.data_volume_gb * 0.115
        return base_cost + storage_cost

class NetworkingAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        recommendations = []
        if "Content Delivery" in requirements.special_requirements:
            recommendations.extend(self._recommend_cloudfront(requirements))
        return recommendations

    def _recommend_cloudfront(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        monthly_cost = self._calculate_cloudfront_cost(requirements)
        return [
            ServiceRecommendation(
                service_name="Amazon CloudFront",
                configuration={
                    "price_class": "PriceClass_100",
                    "ssl_certificate": "ACM"
                },
                monthly_cost=monthly_cost,
                justification="Global content delivery network",
                alternatives=["AWS Global Accelerator"]
            )
        ]

    def _calculate_cloudfront_cost(self, requirements: CustomerRequirement) -> float:
        data_transfer_gb = requirements.data_volume_gb * 0.5  # Estimate 50% of data through CDN
        return data_transfer_gb * 0.085  # Average cost per GB

class SecurityAgent(CloudServiceAgent):
    def recommend(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        recommendations = []
        if requirements.compliance_needs:
            recommendations.extend(self._recommend_security_services(requirements))
        return recommendations

    def _recommend_security_services(self, requirements: CustomerRequirement) -> List[ServiceRecommendation]:
        services = []
        monthly_cost = 0.0

        if "HIPAA" in requirements.compliance_needs or "PCI DSS" in requirements.compliance_needs:
            services.append(
                ServiceRecommendation(
                    service_name="AWS WAF",
                    configuration={
                        "rules": ["SQL injection", "Cross-site scripting"]
                    },
                    monthly_cost=20.0,
                    justification="Web application firewall for security compliance",
                    alternatives=["Third-party WAF"]
                )
            )
            monthly_cost += 20.0

        return services

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

        return CloudPackage(
            total_monthly_cost=sum(r.monthly_cost for r in filtered_recommendations),
            services=filtered_recommendations,
            architecture_diagram=self._generate_architecture_diagram(filtered_recommendations),
            optimization_tips=self._generate_optimization_tips(filtered_recommendations),
            compliance_notes=self._generate_compliance_notes(requirements, filtered_recommendations)
        )

    def _filter_by_budget(self, recommendations: List[ServiceRecommendation], 
                         budget: float) -> List[ServiceRecommendation]:
        """Filter recommendations to stay within budget"""
        recommendations.sort(key=lambda x: x.monthly_cost)
        filtered = []
        total_cost = 0
        
        for rec in recommendations:
            if total_cost + rec.monthly_cost <= budget:
                filtered.append(rec)
                total_cost += rec.monthly_cost
        
        return filtered

    def _generate_architecture_diagram(self, recommendations: List[ServiceRecommendation]) -> str:
        """Generate Mermaid.js architecture diagram"""
        diagram = """graph TD
    Client((Client))"""
        
        # Add services
        service_nodes = []
        for i, rec in enumerate(recommendations):
            service_id = f"svc{i}"
            service_nodes.append(service_id)
            diagram += f'\n    {service_id}["{rec.service_name}"]'
        
        # Add connections
        if service_nodes:
            diagram += f'\n    Client --> {service_nodes[0]}'
            for i in range(len(service_nodes)-1):
                diagram += f'\n    {service_nodes[i]} --> {service_nodes[i+1]}'
        
        return diagram

    def _generate_optimization_tips(self, recommendations: List[ServiceRecommendation]) -> List[str]:
        """Generate cost optimization tips"""
        tips = []
        total_cost = sum(r.monthly_cost for r in recommendations)
        
        if total_cost > 1000:
            tips.append("Consider reserved instances for predictable workloads")
        if any(r.service_name == "Amazon EC2" for r in recommendations):
            tips.append("Use Auto Scaling to optimize compute costs")
        if any(r.service_name == "Amazon S3" for r in recommendations):
            tips.append("Implement S3 lifecycle policies for cost-effective storage")
            
        return tips

    def _generate_compliance_notes(self, requirements: CustomerRequirement, 
                                 recommendations: List[ServiceRecommendation]) -> str:
        """Generate compliance-related notes"""
        if not requirements.compliance_needs:
            return ""
            
        notes = ["Compliance Considerations:"]
        for compliance in requirements.compliance_needs:
            notes.append(f"- {compliance} requirements are addressed through:")
            for rec in recommendations:
                if rec.service_name in ["AWS WAF", "Amazon GuardDuty"]:
                    notes.append(f"  * {rec.service_name}: {rec.justification}")
                    
        return "\n".join(notes)

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