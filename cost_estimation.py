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
from PIL import Image

# [Previous imports and initialization remain the same...]

class DynamicPricingEngine:
    @staticmethod
    def calculate_service_price(service: str, config: Dict, timeline_config: Dict, requirements: Dict) -> Dict:
        """Calculate service price with dynamic factors, timeline, and enterprise requirements"""
        
        # Apply enterprise requirements to configuration
        config = DynamicPricingEngine._apply_enterprise_requirements(config, service, requirements)
        
        base_price = DynamicPricingEngine._calculate_base_price(service, config, requirements)
        
        # Apply scalability pattern adjustments
        scalability_multiplier = DynamicPricingEngine._get_scalability_multiplier(
            requirements.get('scalability_needs', 'Fixed Capacity')
        )
        
        # Apply availability requirements
        availability_multiplier = DynamicPricingEngine._get_availability_multiplier(
            requirements.get('availability_requirements', '99.9% (Business Hours)')
        )
        
        adjusted_price = base_price * timeline_config["pattern_multiplier"] * scalability_multiplier * availability_multiplier
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
            "commitment_savings": adjusted_price - discounted_price,
            "scalability_multiplier": scalability_multiplier,
            "availability_multiplier": availability_multiplier
        }
    
    @staticmethod
    def _apply_enterprise_requirements(config: Dict, service: str, requirements: Dict) -> Dict:
        """Apply enterprise defaults based on requirements"""
        performance_tier = requirements.get('performance_tier', 'Production')
        workload_complexity = requirements.get('workload_complexity', 'Moderate')
        
        # Only apply enterprise defaults if performance tier is Enterprise
        if performance_tier != 'Enterprise':
            return config
        
        # Enterprise defaults for different services
        if service == "Amazon EC2":
            if 'instance_type' not in config or config['instance_type'] in ['t3.micro', 't3.small']:
                config['instance_type'] = 'm5.xlarge'  # Enterprise default
            if 'instance_count' not in config or config['instance_count'] < 2:
                config['instance_count'] = 2  # Minimum 2 for HA
        
        elif service == "Amazon RDS":
            if 'instance_type' not in config or config['instance_type'] in ['db.t3.micro', 'db.t3.small']:
                config['instance_type'] = 'db.m5.xlarge'  # Enterprise default
            config['multi_az'] = True  # Enterprise enables Multi-AZ by default
            config['backup_retention'] = 35  # Longer retention for enterprise
            if 'storage_gb' not in config or config['storage_gb'] < 100:
                config['storage_gb'] = 100
        
        elif service == "Amazon EBS":
            if config.get('volume_type', 'gp3') == 'gp3':
                config['volume_type'] = 'io1'  # Provisioned IOPS for enterprise
                config['iops'] = 3000
        
        elif service == "Amazon ECS":
            if config.get('cluster_type', 'Fargate') == 'Fargate':
                config['cpu_units'] = max(config.get('cpu_units', 1024), 2048)
                config['memory_gb'] = max(config.get('memory_gb', 2), 4)
        
        elif service == "Elastic Load Balancing":
            # Enterprise might need more capacity
            config['lcu_count'] = config.get('lcu_count', 10000) * 2
        
        return config
    
    @staticmethod
    def _get_scalability_multiplier(scalability_pattern: str) -> float:
        """Get cost multiplier based on scalability pattern"""
        multipliers = {
            "Fixed Capacity": 1.0,
            "Seasonal": 1.3,  # Higher for seasonal scaling needs
            "Predictable Growth": 1.1,
            "Unpredictable Burst": 1.5  # Highest for unpredictable bursts
        }
        return multipliers.get(scalability_pattern, 1.0)
    
    @staticmethod
    def _get_availability_multiplier(availability: str) -> float:
        """Get cost multiplier based on availability requirements"""
        multipliers = {
            "99.9% (Business Hours)": 1.0,
            "99.95% (High Availability)": 1.3,
            "99.99% (Mission Critical)": 1.8
        }
        return multipliers.get(availability, 1.0)
    
    @staticmethod
    def _calculate_base_price(service: str, config: Dict, requirements: Dict) -> float:
        """Calculate base monthly price for service with enterprise considerations"""
        
        performance_tier = requirements.get('performance_tier', 'Production')
        
        if service == "Amazon EC2":
            instance_type = config.get('instance_type', 't3.micro')
            instance_count = config.get('instance_count', 1)
            
            # Different pricing tiers based on performance requirements
            if performance_tier == 'Enterprise':
                instance_prices = {
                    't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                    'm5.large': 0.096, 'm5.xlarge': 0.192, 'm5.2xlarge': 0.384,
                    'c5.large': 0.085, 'c5.xlarge': 0.17, 'c5.2xlarge': 0.34,
                    'r5.large': 0.126, 'r5.xlarge': 0.252, 'r5.2xlarge': 0.504
                }
            else:
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
            
            # Add provisioned IOPS cost if applicable
            if volume_type in ['io1', 'io2']:
                iops = config.get('iops', 3000)
                base_price += iops * 0.065  # $0.065 per provisioned IOPS
            
            return base_price
            
        elif service == "Amazon RDS":
            instance_type = config.get('instance_type', 'db.t3.micro')
            engine = config.get('engine', 'PostgreSQL')
            
            # RDS instance pricing with enterprise considerations
            if performance_tier == 'Enterprise':
                rds_prices = {
                    'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
                    'db.m5.large': 0.17, 'db.m5.xlarge': 0.34, 'db.m5.2xlarge': 0.68,
                    'db.r5.large': 0.24, 'db.r5.xlarge': 0.48, 'db.r5.2xlarge': 0.96
                }
            else:
                rds_prices = {
                    'db.t3.micro': 0.017, 'db.t3.small': 0.034, 'db.t3.medium': 0.068,
                    'db.m5.large': 0.17, 'db.m5.xlarge': 0.34,
                    'db.r5.large': 0.24, 'db.r5.xlarge': 0.48
                }
            
            # Engine-specific adjustments
            engine_multipliers = {
                'PostgreSQL': 1.0,
                'MySQL': 1.0,
                'Aurora MySQL': 1.2,
                'SQL Server': 1.5
            }
            
            base_price = rds_prices.get(instance_type, 0.1) * 730 * engine_multipliers.get(engine, 1.0)
            
            # Storage costs
            storage_gb = config.get('storage_gb', 20)
            
            # Use provisioned IOPS storage for enterprise
            if performance_tier == 'Enterprise':
                base_price += storage_gb * 0.25  # Higher cost for provisioned IOPS
                # Add provisioned IOPS cost
                iops = config.get('iops', 1000)
                base_price += iops * 0.10  # $0.10 per provisioned IOPS
            else:
                base_price += storage_gb * 0.115  # $0.115 per GB-month for standard
            
            # Backup storage with longer retention for enterprise
            backup_retention = config.get('backup_retention', 7)
            backup_multiplier = 2.0 if backup_retention > 7 else 1.0  # More backups cost more
            base_price += storage_gb * 0.095 * backup_multiplier
            
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
            
            # Lambda pricing calculation
            request_cost = requests * 0.0000002  # $0.20 per 1M requests
            gb_seconds = (requests * duration_ms * memory_mb) / (1000 * 1024)
            compute_cost = gb_seconds * 0.0000166667  # $0.0000166667 per GB-second
            
            return request_cost + compute_cost
            
        elif service == "Amazon ECS":
            cluster_type = config.get('cluster_type', 'Fargate')
            
            if cluster_type == 'Fargate':
                cpu_units = config.get('cpu_units', 1024)
                memory_gb = config.get('memory_gb', 2)
                service_count = config.get('service_count', 3)
                avg_tasks = config.get('avg_tasks_per_service', 2)
                
                # Fargate pricing per vCPU and GB
                cpu_price_per_hour = 0.04048  # per vCPU per hour
                memory_price_per_hour = 0.004445  # per GB per hour
                
                total_tasks = service_count * avg_tasks
                monthly_cost = total_tasks * 730 * (cpu_units/1024 * cpu_price_per_hour + memory_gb * memory_price_per_hour)
                return monthly_cost
            else:
                # EC2-based ECS pricing
                instance_count = config.get('instance_count', 2)
                instance_type = config.get('ecs_instance_type', 't3.medium')
                
                # Use EC2 pricing for the instances
                ec2_prices = {
                    't3.medium': 0.0416, 'm5.large': 0.096, 'm5.xlarge': 0.192
                }
                
                base_price = ec2_prices.get(instance_type, 0.1) * 730 * instance_count
                return base_price
            
        elif service == "Amazon EKS":
            node_count = config.get('node_count', 2)
            node_type = config.get('node_type', 't3.medium')
            managed_node_groups = config.get('managed_node_groups', 1)
            
            # EKS cluster cost ($0.10 per hour)
            eks_cluster_cost = 0.10 * 730
            
            # Node instance costs
            node_prices = {
                't3.medium': 0.0416, 'm5.large': 0.096, 'm5.xlarge': 0.192,
                'c5.large': 0.085, 'r5.large': 0.126
            }
            
            node_cost = node_prices.get(node_type, 0.1) * 730 * node_count
            
            return eks_cluster_cost + node_cost
            
        # [Rest of the service pricing calculations remain similar but can be enhanced...]
        
        # Default case for services without specific pricing
        return 0.0

# Update the main function to pass requirements to pricing engine
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
    
    # Store requirements for pricing calculations
    requirements = {
        'workload_complexity': workload_complexity,
        'performance_tier': performance_tier,
        'scalability_needs': scalability_needs,
        'availability_requirements': availability_requirements
    }
    
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
                    
                    # Calculate pricing with timeline AND requirements
                    pricing_result = DynamicPricingEngine.calculate_service_price(
                        service, 
                        st.session_state[service_key],
                        timeline_config,
                        requirements  # Pass requirements here
                    )
                    
                    # Display pricing information with enterprise factors
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
                    
                    # Show enterprise factors if applicable
                    if pricing_result.get('scalability_multiplier', 1.0) > 1.0 or pricing_result.get('availability_multiplier', 1.0) > 1.0:
                        st.caption(f"📈 Scalability factor: {pricing_result.get('scalability_multiplier', 1.0):.1f}x | "
                                 f"🛡️ Availability factor: {pricing_result.get('availability_multiplier', 1.0):.1f}x")
                    
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
        
        # [Rest of the main function remains the same...]

# Update the RDS configuration section to include enterprise options
def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon RDS":
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
        
        # Enhanced instance types with enterprise options
        rds_instance_types = {
            "db.t3.micro": {"vCPU": 2, "Memory": 1, "Description": "Development & test", "Tier": "Basic"},
            "db.t3.small": {"vCPU": 2, "Memory": 2, "Description": "Small workloads", "Tier": "Basic"},
            "db.t3.medium": {"vCPU": 2, "Memory": 4, "Description": "Medium workloads", "Tier": "Basic"},
            "db.m5.large": {"vCPU": 2, "Memory": 8, "Description": "Production workloads", "Tier": "Production"},
            "db.m5.xlarge": {"vCPU": 4, "Memory": 16, "Description": "Enterprise workloads", "Tier": "Enterprise"},
            "db.m5.2xlarge": {"vCPU": 8, "Memory": 32, "Description": "High performance", "Tier": "Enterprise"},
            "db.r5.large": {"vCPU": 2, "Memory": 16, "Description": "Memory optimized", "Tier": "Production"},
            "db.r5.xlarge": {"vCPU": 4, "Memory": 32, "Description": "Memory intensive", "Tier": "Enterprise"}
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
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("vCPU", specs["vCPU"])
            with col2:
                st.metric("Memory (GiB)", specs["Memory"])
            with col3:
                st.metric("Tier", specs["Tier"])
        
        col1, col2 = st.columns(2)
        with col1:
            storage = st.slider("Storage (GB)", 20, 65536, 100, key=f"{key_prefix}_storage")
            backup_retention = st.slider("Backup Retention (Days)", 0, 35, 7, key=f"{key_prefix}_backup")
            
            # Provisioned IOPS for enterprise
            if selected_type in ['db.m5.xlarge', 'db.m5.2xlarge', 'db.r5.xlarge']:
                iops = st.slider("Provisioned IOPS", 1000, 80000, 3000, key=f"{key_prefix}_iops")
                config["iops"] = iops
        
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
    
    # [Rest of the configuration functions remain similar...]

if __name__ == "__main__":
    main()