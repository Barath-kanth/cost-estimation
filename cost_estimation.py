import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

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
        
        cumulative = 0.0
        for year in range(1, years + 1):
            # Calculate monthly cost for this year (with growth applied)
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
        
        cumulative = 0.0
        for month in range(1, total_months + 1):
            monthly_cost = base_monthly_cost * (1 + growth_rate) ** (month - 1)
            cumulative += monthly_cost
            
            # Format month display
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
            # Extract months from selection
            if "Year" in timeline_type:
                years = int(timeline_type.split()[0])
                total_months = years * 12
            else:
                total_months = int(timeline_type.split()[0])
        
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
        
        # Usage pattern multipliers
        pattern_multipliers = {
            "Development": 0.6,
            "Sporadic": 0.8,
            "Normal": 1.0,
            "Intensive": 1.4,
            "24x7": 1.8
        }
        
        # Commitment discounts
        commitment_discounts = {
            "On-Demand": 1.0,
            "1-Year Reserved": 0.7,  # 30% discount
            "3-Year Reserved": 0.5,  # 50% discount
            "Savings Plans": 0.72    # 28% discount
        }
        
        return {
            "timeline_type": timeline_type,
            "total_months": total_months,
            "years": total_months // 12,
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
        
        # Apply usage pattern multiplier
        adjusted_price = base_price * timeline_config["pattern_multiplier"]
        
        # Apply commitment discount
        discounted_price = adjusted_price * timeline_config["commitment_discount"]
        
        # Calculate yearly breakdown
        yearly_data = YearlyTimelineCalculator.calculate_yearly_costs(
            discounted_price, 
            timeline_config["years"],
            timeline_config["growth_rate"]
        )
        
        # Calculate detailed monthly timeline
        monthly_data = YearlyTimelineCalculator.calculate_detailed_monthly_timeline(
            discounted_price,
            timeline_config["total_months"],
            timeline_config["growth_rate"]
        )
        
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
        
        # Add more services as needed...
        return 0.0

def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.write("**Instance Configuration**")
        
        # Instance families with realistic specs
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
        
        # Get description safely
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
        
        # Get description safely
        engine_description = ""
        if engine in database_engines:
            engine_description = database_engines[engine]["Description"]
        
        st.caption(f"*{engine_description}*")
        
        # Instance types for RDS
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
        
        # Get description safely
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
    
    # Region selection for all services
    config["region"] = st.selectbox(
        "Region",
        ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"],
        key=f"{key_prefix}_region"
    )
    
    return config

def render_yearly_visualization(yearly_data: Dict, service_name: str):
    """Render yearly visualization for service costs using Streamlit native charts"""
    if not yearly_data or "years" not in yearly_data:
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
    
    # Create bar chart for yearly costs
    chart_data = pd.DataFrame({
        'Year': yearly_data["years"],
        'Yearly Cost': yearly_data["yearly_costs"],
        'Cumulative Cost': yearly_data["cumulative_costs"]
    })
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${yearly_data['total_cost']:,.2f}")
    with col2:
        avg_yearly = yearly_data['total_cost'] / len(yearly_data["years"])
        st.metric("Average Yearly", f"${avg_yearly:,.2f}")
    with col3:
        st.metric("Final Yearly", f"${yearly_data['yearly_costs'][-1]:,.2f}")
    
    # Create simple bar chart using Streamlit
    st.subheader("📊 Yearly Cost Chart")
    chart_df = pd.DataFrame({
        'Year': yearly_data["years"],
        'Yearly Cost ($)': yearly_data["yearly_costs"]
    })
    st.bar_chart(chart_df.set_index('Year'))

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
                    
                    # Show yearly visualization
                    render_yearly_visualization(pricing_result['yearly_data'], service)
        
        # COST SUMMARY & VISUALIZATION
        st.header("💰 Cost Summary & Analysis")
        
        # Calculate overall yearly breakdown
        overall_yearly_data = YearlyTimelineCalculator.calculate_yearly_costs(
            sum([config['pricing']['discounted_monthly_cost'] for config in st.session_state.configurations.values()]),
            timeline_config["years"],
            timeline_config["growth_rate"]
        )
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Timeline Cost", f"${st.session_state.total_cost:,.2f}")
        with col2:
            avg_monthly = st.session_state.total_cost / timeline_config["total_months"]
            st.metric("Average Monthly Cost", f"${avg_monthly:,.2f}")
        with col3:
            avg_yearly = st.session_state.total_cost / timeline_config["years"]
            st.metric("Average Yearly Cost", f"${avg_yearly:,.2f}")
        with col4:
            st.metric("Timeline Period", timeline_config["timeline_type"])
        
        # Overall yearly visualization
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
                "average_monthly_cost": st.session_state.total_cost / timeline_config["total_months"],
                "average_yearly_cost": st.session_state.total_cost / timeline_config["years"],
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