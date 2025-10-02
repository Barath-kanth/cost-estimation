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

# Remove matplotlib imports and replace with plotly or streamlit native charts

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
    if 'architecture_diagram' not in st.session_state:
        st.session_state.architecture_diagram = None

class ProfessionalArchitectureGenerator:
    """Generate professional AWS architecture diagrams with real AWS icons"""
    
    @staticmethod
    def generate_professional_diagram_html(selected_services: Dict, configurations: Dict, requirements: Dict) -> str:
        """Generate professional HTML-based diagram with real AWS icons"""
        
        # AWS service icon mappings to AWS Architecture Icons CDN
        service_icons = {
            # Compute
            "Amazon EC2": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-EC2_48.8c2c29c51959a74bca1ad23b2ab6a0e1c4cefa56.svg",
            "AWS Lambda": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Lambda_48.80ff29e6c3cb2b92eafac0977794d99ccb2fe4c1.svg",
            "Amazon ECS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Container-Service_48.5577c33a67c1a1447c2bc85ea7cbdf87c0e7c7a4.svg",
            "Amazon EKS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Kubernetes-Service_48.a8f4685cf67e36f7cf0ee626a7f4e55a2e4a27e6.svg",
            
            # Storage
            "Amazon S3": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Storage-Service_48.3dd1b4d5d3b09ba0f6c34b6c8e8f2b8f9e0e4e0e.svg",
            "Amazon EBS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-Block-Store_48.7c8f3e3f4e4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f.svg",
            "Amazon EFS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Elastic-File-System_48.2e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e.svg",
            
            # Database
            "Amazon RDS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-RDS_48.7f8e9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f.svg",
            "Amazon DynamoDB": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-DynamoDB_48.5c6d7e8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f.svg",
            "Amazon ElastiCache": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-ElastiCache_48.4e5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f.svg",
            "Amazon OpenSearch": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-OpenSearch-Service_48.3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e.svg",
            
            # AI/ML
            "Amazon Bedrock": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Bedrock_48.2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e.svg",
            "Amazon SageMaker": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-SageMaker_48.1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e0e.svg",
            
            # Analytics
            "Amazon Kinesis": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Kinesis_48.0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e9e.svg",
            "AWS Glue": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Glue_48.9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f.svg",
            "Amazon Redshift": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Redshift_48.8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f.svg",
            
            # Networking
            "Amazon VPC": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Virtual-Private-Cloud_48.7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f.svg",
            "Amazon CloudFront": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-CloudFront_48.6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f.svg",
            "Elastic Load Balancing": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Elastic-Load-Balancing_48.5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f.svg",
            "Amazon API Gateway": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-API-Gateway_48.4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f3f.svg",
            
            # Security
            "AWS WAF": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-WAF_48.3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f2f.svg",
            "Amazon GuardDuty": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-GuardDuty_48.2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f1f.svg",
            "AWS Shield": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Shield_48.1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f0f.svg",
            
            # Application Integration
            "AWS Step Functions": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_AWS-Step-Functions_48.0f1f2f3f4f5f6f7f8f9f0f1f2f3f4f5f6f7f8f9f.svg",
            "Amazon EventBridge": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-EventBridge_48.9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e8e.svg",
            "Amazon SNS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Notification-Service_48.8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e7e.svg",
            "Amazon SQS": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Amazon-Simple-Queue-Service_48.7e8e9e0e1e2e3e4e5e6e7e8e9e0e1e2e3e4e5e6e.svg",
            
            # External
            "User": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_User_48.svg",
            "External": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_Cloud_48.svg",
            "Analyst": "https://d1.awsstatic.com/webteam/architecture-icons/q3-2023/Arch_User_48.svg"
        }
        
        # Build HTML for the diagram
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .architecture-container {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    font-family: Arial, sans-serif;
                }
                .layer {
                    margin: 20px 0;
                    padding: 15px;
                    border-radius: 8px;
                    background: #f8f9fa;
                }
                .layer-title {
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #333;
                    font-size: 16px;
                }
                .services-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                }
                .service-card {
                    background: white;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    padding: 15px;
                    text-align: center;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .service-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
                }
                .service-icon {
                    width: 48px;
                    height: 48px;
                    margin: 0 auto 10px;
                }
                .service-name {
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: #333;
                }
                .service-config {
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 5px;
                }
                .connections {
                    margin: 20px 0;
                    text-align: center;
                    color: #666;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <div class="architecture-container">
                <h2 style="text-align: center; color: #333; margin-bottom: 30px;">AWS Architecture Diagram</h2>
        """
        
        # Define layers for better organization
        layers = {
            "External": ["User", "External", "Analyst"],
            "Frontend": ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"],
            "Application": ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"],
            "Data": ["Amazon S3", "Amazon EBS", "Amazon EFS", "Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"],
            "Analytics": ["Amazon Kinesis", "AWS Glue", "Amazon Redshift", "Amazon OpenSearch"],
            "AI/ML": ["Amazon Bedrock", "Amazon SageMaker"],
            "Security": ["AWS WAF", "Amazon GuardDuty", "AWS Shield"],
            "Integration": ["AWS Step Functions", "Amazon EventBridge", "Amazon SNS", "Amazon SQS"]
        }
        
        # Add services to their respective layers
        all_selected_services = []
        for services in selected_services.values():
            all_selected_services.extend(services)
        
        for layer_name, layer_services in layers.items():
            # Filter services that are selected and belong to this layer
            services_in_layer = [s for s in all_selected_services if s in layer_services]
            
            if services_in_layer:
                html_content += f"""
                <div class="layer">
                    <div class="layer-title">{layer_name} Layer</div>
                    <div class="services-grid">
                """
                
                for service in services_in_layer:
                    config = configurations.get(service, {}).get('config', {})
                    
                    # Build configuration text
                    config_text = ""
                    if service == "Amazon EC2" and config:
                        instance_type = config.get('instance_type', 't3.micro')
                        instance_count = config.get('instance_count', 1)
                        config_text = f"{instance_count}x {instance_type}"
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        config_text = f"{engine} - {instance_type}"
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        config_text = f"{storage_gb}GB"
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        config_text = f"{memory}MB"
                    
                    html_content += f"""
                    <div class="service-card">
                        <img src="{service_icons.get(service, service_icons['Amazon EC2'])}" alt="{service}" class="service-icon">
                        <div class="service-name">{service.replace('Amazon ', '').replace('AWS ', '')}</div>
                        <div class="service-config">{config_text}</div>
                    </div>
                    """
                
                html_content += """
                    </div>
                </div>
                """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return html_content

    @staticmethod
    def generate_opensearch_trending_queries_diagram() -> str:
        """Generate the specific OpenSearch trending queries architecture from the reference image"""
        
        mermaid_code = """graph TB
    classDef user fill:#666,stroke:#333,stroke-width:2px,color:#000
    classDef streaming fill:#259E9E,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef storage fill:#3B48CC,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef search fill:#3334B9,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef compute fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#000
    classDef ml fill:#01A88D,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef workflow fill:#6B1C6B,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef database fill:#D45A4B,stroke:#232F3E,stroke-width:2px,color:#fff

    User[User<br/>Search Application]:::user
    Analyst[Business Analyst]:::user
    
    subgraph DataIngestion [Data Ingestion]
        KinesisDataStreams[Amazon Kinesis<br/>Data Streams]:::streaming
        KinesisFirehose[Amazon Kinesis<br/>Data Firehose]:::streaming
    end
    
    subgraph SearchLayer [Search & Analytics]
        OpenSearch[Amazon OpenSearch<br/>Service]:::search
        APIGateway[Amazon API<br/>Gateway]:::compute
        LambdaTrending[AWS Lambda<br/>Trending Queries]:::compute
    end
    
    subgraph DataProcessing [Data Processing & ML]
        S3Raw[Amazon S3<br/>RAW Logs]:::storage
        GlueCrawler[AWS Glue<br/>Crawler]:::compute
        GlueCatalog[AWS Glue<br/>Data Catalog]:::database
        StepFunctions[AWS Step Functions<br/>Cluster & Classify Workflow]:::workflow
        LambdaBedrock[AWS Lambda<br/>Invoke Bedrock LLM]:::compute
        Bedrock[Amazon Bedrock<br/>LLM Classification]:::ml
    end
    
    subgraph StorageOutput [Storage & Output]
        DynamoDB[Amazon DynamoDB<br/>Output Trending Queries]:::database
        S3Processed[Amazon S3<br/>Processed Data]:::storage
    end
    
    subgraph Orchestration [Orchestration]
        EventBridge[Amazon EventBridge<br/>Scheduler - Daily]:::workflow
    end

    User -->|search queries| KinesisDataStreams
    KinesisDataStreams -->|compress queries| KinesisFirehose
    KinesisFirehose -->|store logs| S3Raw
    
    EventBridge -->|trigger| StepFunctions
    S3Raw -->|crawl| GlueCrawler
    GlueCrawler -->|update schema| GlueCatalog
    GlueCatalog -->|read schema| StepFunctions
    
    StepFunctions -->|process queries| LambdaBedrock
    LambdaBedrock -->|classify with LLM| Bedrock
    Bedrock -->|return classification| LambdaBedrock
    LambdaBedrock -->|store results| DynamoDB
    StepFunctions -->|store processed data| S3Processed
    
    Analyst -->|access trending| APIGateway
    APIGateway -->|get trending| LambdaTrending
    LambdaTrending -->|query| OpenSearch
    LambdaTrending -->|read results| DynamoDB
    
    OpenSearch -->|serve search| User
    
    %% Styling for subgraphs
    class DataIngestion,SearchLayer,DataProcessing,StorageOutput,Orchestration fill:#f9f9f9,stroke:#ddd,stroke-width:2px,color:#333
    """

        return mermaid_code

# ... (keep all your existing classes and functions, but remove matplotlib usage)

# In the main function, replace the cost breakdown visualization:

def main():
    # ... (previous setup code)
    
    # TOTAL COST SUMMARY - Replace matplotlib with native Streamlit charts
    st.header("💰 Total Cost Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Estimated Cost", 
            f"${st.session_state.total_cost:,.2f}",
            f"for {timeline_config['timeline_type']}"
        )
    
    with col2:
        avg_monthly = st.session_state.total_cost / timeline_config['total_months'] if timeline_config['total_months'] > 0 else 0
        st.metric("Average Monthly Cost", f"${avg_monthly:,.2f}")
    
    with col3:
        commitment_savings = sum(
            config['pricing'].get('commitment_savings', 0) * timeline_config['total_months'] 
            for config in st.session_state.configurations.values()
        )
        st.metric("Commitment Savings", f"${commitment_savings:,.2f}")
    
    # Cost breakdown using native Streamlit charts
    st.subheader("📊 Cost Breakdown by Service")
    
    cost_data = []
    for service, config in st.session_state.configurations.items():
        cost_data.append({
            'Service': service,
            'Total Cost': config['pricing']['total_timeline_cost'],
            'Monthly Cost': config['pricing']['discounted_monthly_cost']
        })
    
    if cost_data:
        cost_df = pd.DataFrame(cost_data)
        st.dataframe(cost_df, use_container_width=True)
        
        # Use Streamlit native bar chart instead of matplotlib
        st.bar_chart(cost_df.set_index('Service')['Total Cost'])
        
        # For pie chart equivalent, use a bar chart or create a custom visualization
        st.write("**Cost Distribution**")
        chart_data = cost_df[['Service', 'Total Cost']].set_index('Service')
        st.bar_chart(chart_data)

if __name__ == "__main__":
    main()