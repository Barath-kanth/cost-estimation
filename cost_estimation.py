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
import base64
import io
import streamlit.components.v1 as components
import graphviz

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

# AWS Services configuration
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
        "Amazon ElastiCache": "In-memory caching",
        "Amazon OpenSearch": "Search and analytics service"
    },
    "AI/ML": {
        "Amazon Bedrock": "Fully managed foundation models",
        "Amazon SageMaker": "Build, train and deploy ML models"
    },
    "Analytics": {
        "Amazon Kinesis": "Real-time data streaming",
        "AWS Glue": "ETL service",
        "Amazon Redshift": "Data warehousing"
    },
    "Networking": {
        "Amazon VPC": "Isolated cloud resources",
        "Amazon CloudFront": "Global content delivery network",
        "Elastic Load Balancing": "Distribute incoming traffic",
        "Amazon API Gateway": "API management"
    },
    "Security": {
        "AWS WAF": "Web Application Firewall",
        "Amazon GuardDuty": "Threat detection service",
        "AWS Shield": "DDoS protection"
    },
    "Application Integration": {
        "AWS Step Functions": "Workflow orchestration",
        "Amazon EventBridge": "Event bus service",
        "Amazon SNS": "Pub/sub messaging",
        "Amazon SQS": "Message queuing"
    }
}

class ProfessionalArchitectureGenerator:
    """Generate professional AWS architecture diagrams with real AWS icons"""
    
    @staticmethod
    def get_service_icon_url(service_name: str) -> str:
        """Get real AWS icon URL from icon.icepanel.io"""
        icon_mapping = {
            "Amazon EC2": "https://icon.icepanel.io/AWS/svg/Compute/EC2.svg",
            "AWS Lambda": "https://icon.icepanel.io/AWS/svg/Compute/Lambda.svg",
            "Amazon ECS": "https://icon.icepanel.io/AWS/svg/Compute/Elastic-Container-Service.svg",
            "Amazon EKS": "https://icon.icepanel.io/AWS/svg/Compute/Elastic-Kubernetes-Service.svg",
            "Amazon S3": "https://icon.icepanel.io/AWS/svg/Storage/Simple-Storage-Service.svg",
            "Amazon EBS": "https://icon.icepanel.io/AWS/svg/Storage/Elastic-Block-Store.svg",
            "Amazon EFS": "https://icon.icepanel.io/AWS/svg/Storage/Elastic-File-System.svg",
            "Amazon RDS": "https://icon.icepanel.io/AWS/svg/Database/RDS.svg",
            "Amazon DynamoDB": "https://icon.icepanel.io/AWS/svg/Database/DynamoDB.svg",
            "Amazon ElastiCache": "https://icon.icepanel.io/AWS/svg/Database/ElastiCache.svg",
            "Amazon OpenSearch": "https://icon.icepanel.io/AWS/svg/Analytics/OpenSearch-Service.svg",
            "Amazon Bedrock": "https://icon.icepanel.io/AWS/svg/Machine-Learning/Bedrock.svg",
            "Amazon SageMaker": "https://icon.icepanel.io/AWS/svg/Machine-Learning/SageMaker.svg",
            "Amazon Kinesis": "https://icon.icepanel.io/AWS/svg/Analytics/Kinesis.svg",
            "AWS Glue": "https://icon.icepanel.io/AWS/svg/Analytics/Glue.svg",
            "Amazon Redshift": "https://icon.icepanel.io/AWS/svg/Analytics/Redshift.svg",
            "Amazon VPC": "https://icon.icepanel.io/AWS/svg/Networking-Content-Delivery/Virtual-Private-Cloud.svg",
            "Amazon CloudFront": "https://icon.icepanel.io/AWS/svg/Networking-Content-Delivery/CloudFront.svg",
            "Elastic Load Balancing": "https://icon.icepanel.io/AWS/svg/Networking-Content-Delivery/Elastic-Load-Balancing.svg",
            "Amazon API Gateway": "https://icon.icepanel.io/AWS/svg/Networking-Content-Delivery/API-Gateway.svg",
            "AWS WAF": "https://icon.icepanel.io/AWS/svg/Security-Identity-Compliance/WAF.svg",
            "Amazon GuardDuty": "https://icon.icepanel.io/AWS/svg/Security-Identity-Compliance/GuardDuty.svg",
            "AWS Shield": "https://icon.icepanel.io/AWS/svg/Security-Identity-Compliance/Shield.svg",
            "AWS Step Functions": "https://icon.icepanel.io/AWS/svg/Application-Integration/Step-Functions.svg",
            "Amazon EventBridge": "https://icon.icepanel.io/AWS/svg/Application-Integration/EventBridge.svg",
            "Amazon SNS": "https://icon.icepanel.io/AWS/svg/Application-Integration/Simple-Notification-Service.svg",
            "Amazon SQS": "https://icon.icepanel.io/AWS/svg/Application-Integration/Simple-Queue-Service.svg",
            "User": "https://icon.icepanel.io/AWS/svg/General-Icons/User.svg",
            "External": "https://icon.icepanel.io/AWS/svg/General-Icons/Internet-alt1.svg"
        }
        return icon_mapping.get(service_name, "https://icon.icepanel.io/AWS/svg/General-Icons/General.svg")
    
    @staticmethod
    def generate_connections(selected_services: List[str]) -> List[Dict]:
        """Generate intelligent connections between services"""
        connections = []
        
        # User to frontend
        if "Amazon CloudFront" in selected_services:
            connections.append({"from": "User", "to": "Amazon CloudFront", "label": "HTTPS"})
        if "Elastic Load Balancing" in selected_services:
            connections.append({"from": "User", "to": "Elastic Load Balancing", "label": "API Requests"})
        if "Amazon API Gateway" in selected_services:
            connections.append({"from": "User", "to": "Amazon API Gateway", "label": "API Calls"})
        
        # Frontend to storage
        if "Amazon CloudFront" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "Amazon CloudFront", "to": "Amazon S3", "label": "Static Content"})
        
        # Load balancer to compute
        if "Elastic Load Balancing" in selected_services:
            for compute in ["Amazon EC2", "Amazon ECS", "Amazon EKS"]:
                if compute in selected_services:
                    connections.append({"from": "Elastic Load Balancing", "to": compute, "label": "Routes Traffic"})
        
        # API Gateway to compute
        if "Amazon API Gateway" in selected_services and "AWS Lambda" in selected_services:
            connections.append({"from": "Amazon API Gateway", "to": "AWS Lambda", "label": "Invokes"})
        
        # Compute to database
        compute_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        db_services = ["Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"]
        
        for compute in compute_services:
            if compute in selected_services:
                for db in db_services:
                    if db in selected_services:
                        connections.append({"from": compute, "to": db, "label": "Queries"})
        
        # Analytics pipeline
        if "Amazon Kinesis" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "External", "to": "Amazon Kinesis", "label": "Streams Data"})
            connections.append({"from": "Amazon Kinesis", "to": "Amazon S3", "label": "Stores"})
        
        if "AWS Glue" in selected_services and "Amazon S3" in selected_services:
            connections.append({"from": "AWS Glue", "to": "Amazon S3", "label": "Processes"})
        
        if "Amazon OpenSearch" in selected_services:
            if "AWS Glue" in selected_services:
                connections.append({"from": "AWS Glue", "to": "Amazon OpenSearch", "label": "Loads"})
        
        # AI/ML connections
        if "Amazon Bedrock" in selected_services:
            for compute in compute_services:
                if compute in selected_services:
                    connections.append({"from": compute, "to": "Amazon Bedrock", "label": "Invokes AI"})
        
        # Step Functions
        if "AWS Step Functions" in selected_services and "AWS Lambda" in selected_services:
            connections.append({"from": "AWS Step Functions", "to": "AWS Lambda", "label": "Orchestrates"})
        
        if "Amazon EventBridge" in selected_services and "AWS Step Functions" in selected_services:
            connections.append({"from": "Amazon EventBridge", "to": "AWS Step Functions", "label": "Triggers"})
        
        # Security
        if "AWS WAF" in selected_services:
            for frontend in ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]:
                if frontend in selected_services:
                    connections.append({"from": "AWS WAF", "to": frontend, "label": "Protects"})
        
        return connections
    
    @staticmethod
    def generate_professional_diagram_html(selected_services: Dict, configurations: Dict, requirements: Dict) -> str:
        """Generate professional HTML diagram with real AWS icons and connections"""
        
        # Flatten selected services
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Add external nodes
        all_services_with_external = ["User", "External"] + all_services
        
        # Generate connections
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        
        # Define layers
        layers = {
            "External": ["User", "External"],
            "Frontend": ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"],
            "Application": ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"],
            "Data": ["Amazon S3", "Amazon EBS", "Amazon EFS", "Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"],
            "Analytics": ["Amazon Kinesis", "AWS Glue", "Amazon Redshift", "Amazon OpenSearch"],
            "AI/ML": ["Amazon Bedrock", "Amazon SageMaker"],
            "Security": ["AWS WAF", "Amazon GuardDuty", "AWS Shield"],
            "Integration": ["AWS Step Functions", "Amazon EventBridge", "Amazon SNS", "Amazon SQS"]
        }
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: 'Amazon Ember', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .architecture-container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h2 {
            color: #232f3e;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            color: #666;
            font-size: 14px;
        }
        .layer {
            margin: 25px 0;
            padding: 20px;
            border-radius: 10px;
            background: #f8f9fa;
            border-left: 5px solid;
            position: relative;
        }
        .layer-title {
            font-weight: bold;
            margin-bottom: 15px;
            color: #232f3e;
            font-size: 18px;
            display: flex;
            align-items: center;
        }
        .layer-title::before {
            content: '';
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 10px;
            display: inline-block;
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }
        .service-card {
            background: white;
            border: 2px solid #e1e4e8;
            border-radius: 8px;
            padding: 20px 15px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            border-color: #FF9900;
        }
        .service-icon {
            width: 56px;
            height: 56px;
            margin: 0 auto 12px;
            display: block;
        }
        .service-name {
            font-weight: 600;
            margin-bottom: 6px;
            color: #232f3e;
            font-size: 14px;
        }
        .service-config {
            font-size: 11px;
            color: #666;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid #e1e4e8;
        }
        .connections-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }
        .connections-info h3 {
            color: #856404;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .connection-item {
            display: inline-block;
            background: white;
            padding: 8px 12px;
            margin: 5px;
            border-radius: 20px;
            font-size: 12px;
            border: 1px solid #ffeaa7;
        }
        .arrow {
            color: #FF9900;
            font-weight: bold;
            margin: 0 5px;
        }
        
        /* Layer-specific colors */
        .External { border-left-color: #6B7280; }
        .External .layer-title::before { background: #6B7280; }
        
        .Frontend { border-left-color: #EC7211; }
        .Frontend .layer-title::before { background: #EC7211; }
        
        .Application { border-left-color: #FF9900; }
        .Application .layer-title::before { background: #FF9900; }
        
        .Data { border-left-color: #3B48CC; }
        .Data .layer-title::before { background: #3B48CC; }
        
        .Analytics { border-left-color: #8C4FFF; }
        .Analytics .layer-title::before { background: #8C4FFF; }
        
        .AIML { border-left-color: #01A88D; }
        .AIML .layer-title::before { background: #01A88D; }
        
        .Security { border-left-color: #DD344C; }
        .Security .layer-title::before { background: #DD344C; }
        
        .Integration { border-left-color: #C925D1; }
        .Integration .layer-title::before { background: #C925D1; }
    </style>
</head>
<body>
    <div class="architecture-container">
        <div class="header">
            <h2>🏗️ AWS Architecture Diagram</h2>
            <p>Professional architecture with real AWS service icons and intelligent connections</p>
        </div>
"""
        
        # Add layers
        for layer_name, layer_services in layers.items():
            services_in_layer = [s for s in all_services_with_external if s in layer_services]
            
            if services_in_layer:
                layer_class = layer_name.replace("/", "").replace(" ", "")
                html_content += f"""
        <div class="layer {layer_class}">
            <div class="layer-title">{layer_name} Layer</div>
            <div class="services-grid">
"""
                
                for service in services_in_layer:
                    config = configurations.get(service, {}).get('config', {})
                    icon_url = ProfessionalArchitectureGenerator.get_service_icon_url(service)
                    
                    # Build configuration text
                    config_text = ""
                    if service == "Amazon EC2" and config:
                        instance_type = config.get('instance_type', 't3.micro')
                        instance_count = config.get('instance_count', 1)
                        config_text = f"{instance_count}x {instance_type}"
                    elif service == "Amazon RDS" and config:
                        instance_type = config.get('instance_type', 'db.t3.micro')
                        engine = config.get('engine', 'PostgreSQL')
                        config_text = f"{engine}<br/>{instance_type}"
                    elif service == "Amazon S3" and config:
                        storage_gb = config.get('storage_gb', 100)
                        config_text = f"{storage_gb}GB Storage"
                    elif service == "AWS Lambda" and config:
                        memory = config.get('memory_mb', 128)
                        config_text = f"{memory}MB Memory"
                    elif service == "Amazon ECS" and config:
                        cluster_type = config.get('cluster_type', 'Fargate')
                        service_count = config.get('service_count', 1)
                        config_text = f"{service_count} services"
                    elif service == "Amazon EKS" and config:
                        node_count = config.get('node_count', 2)
                        config_text = f"{node_count} nodes"
                    
                    display_name = service.replace("Amazon ", "").replace("AWS ", "")
                    
                    html_content += f"""
                <div class="service-card">
                    <img src="{icon_url}" alt="{service}" class="service-icon" onerror="this.src='https://icon.icepanel.io/AWS/svg/General-Icons/General.svg'">
                    <div class="service-name">{display_name}</div>
                    <div class="service-config">{config_text}</div>
                </div>
"""
                
                html_content += """
            </div>
        </div>
"""
        
        # Add connections section
        if connections:
            html_content += """
        <div class="connections-info">
            <h3>📊 Service Connections & Data Flow</h3>
            <div>
"""
            for conn in connections:
                html_content += f"""
                <div class="connection-item">
                    {conn['from'].replace('Amazon ', '').replace('AWS ', '')}
                    <span class="arrow">→</span>
                    {conn['to'].replace('Amazon ', '').replace('AWS ', '')}
                    <span style="color: #666; font-size: 10px;">({conn['label']})</span>
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
    def generate_mermaid_diagram(selected_services: Dict, configurations: Dict) -> str:
        """Generate Mermaid.js diagram code"""
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        
        # Add external nodes
        all_services_with_external = ["User", "External"] + all_services
        
        # Generate connections
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        
        mermaid_code = "graph TB\n"
        
        # Define node styles
        mermaid_code += "    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n"
        mermaid_code += "    classDef frontend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n"
        mermaid_code += "    classDef application fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n"
        mermaid_code += "    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px\n"
        mermaid_code += "    classDef security fill:#ffebee,stroke:#c62828,stroke-width:2px\n"
        mermaid_code += "    classDef integration fill:#fce4ec,stroke:#ad1457,stroke-width:2px\n"
        
        # Add nodes
        node_ids = {}
        for service in all_services_with_external:
            node_id = service.replace(" ", "").replace("Amazon", "").replace("AWS", "")
            node_ids[service] = node_id
            
            config = configurations.get(service, {}).get('config', {})
            config_text = ""
            
            if service == "Amazon EC2" and config:
                instance_type = config.get('instance_type', 't3.micro')
                instance_count = config.get('instance_count', 1)
                config_text = f"\\n({instance_count}x {instance_type})"
            elif service == "Amazon RDS" and config:
                engine = config.get('engine', 'PostgreSQL')
                config_text = f"\\n({engine})"
            elif service == "Amazon S3" and config:
                storage_gb = config.get('storage_gb', 100)
                config_text = f"\\n({storage_gb}GB)"
            elif service == "AWS Lambda" and config:
                memory = config.get('memory_mb', 128)
                config_text = f"\\n({memory}MB)"
            elif service == "Amazon ECS" and config:
                service_count = config.get('service_count', 1)
                config_text = f"\\n({service_count} services)"
            elif service == "Amazon EKS" and config:
                node_count = config.get('node_count', 2)
                config_text = f"\\n({node_count} nodes)"
            
            display_name = service.replace("Amazon ", "").replace("AWS ", "")
            mermaid_code += f'    {node_id}["{display_name}{config_text}"]\n'
        
        # Add connections
        for conn in connections:
            from_id = node_ids.get(conn['from'], conn['from'].replace(" ", ""))
            to_id = node_ids.get(conn['to'], conn['to'].replace(" ", ""))
            mermaid_code += f'    {from_id} -->|{conn["label"]}| {to_id}\n'
        
        # Apply styling
        external_services = ["User", "External"]
        frontend_services = ["Amazon CloudFront", "Elastic Load Balancing", "Amazon API Gateway"]
        application_services = ["Amazon EC2", "AWS Lambda", "Amazon ECS", "Amazon EKS"]
        data_services = ["Amazon S3", "Amazon EBS", "Amazon EFS", "Amazon RDS", "Amazon DynamoDB", "Amazon ElastiCache"]
        security_services = ["AWS WAF", "Amazon GuardDuty", "AWS Shield"]
        integration_services = ["AWS Step Functions", "Amazon EventBridge", "Amazon SNS", "Amazon SQS"]
        
        for service in all_services_with_external:
            node_id = node_ids[service]
            if service in external_services:
                mermaid_code += f'    class {node_id} external\n'
            elif service in frontend_services:
                mermaid_code += f'    class {node_id} frontend\n'
            elif service in application_services:
                mermaid_code += f'    class {node_id} application\n'
            elif service in data_services:
                mermaid_code += f'    class {node_id} data\n'
            elif service in security_services:
                mermaid_code += f'    class {node_id} security\n'
            elif service in integration_services:
                mermaid_code += f'    class {node_id} integration\n'
        
        return mermaid_code

    @staticmethod
    def generate_graphviz_diagram(selected_services: Dict, configurations: Dict):
        """Generate Graphviz diagram"""
        dot = graphviz.Digraph(comment='AWS Architecture')
        dot.attr(rankdir='TB', size='12,12')
        
        # Define styles
        dot.attr('node', shape='rectangle', style='filled', fontname='Arial')
        dot.attr('edge', color='gray50', fontname='Arial', fontsize='10')
        
        # Add clusters for organization
        with dot.subgraph(name='cluster_external') as c:
            c.attr(label='External', style='filled', fillcolor='lightblue', color='black')
            c.node('User', 'User', fillcolor='#e1f5fe')
            c.node('External', 'External Systems', fillcolor='#e1f5fe')
        
        # Add services by category
        for category, services in selected_services.items():
            if services:
                with dot.subgraph(name=f'cluster_{category.lower()}') as c:
                    c.attr(label=category, style='filled', fillcolor='lightgray', color='black')
                    
                    for service in services:
                        config = configurations.get(service, {}).get('config', {})
                        label = f"{service}\\n{ProfessionalArchitectureGenerator._get_config_summary(service, config)}"
                        
                        # Color coding based on service type
                        if "EC2" in service or "Lambda" in service or "ECS" in service or "EKS" in service:
                            fillcolor = '#e8f5e8'  # Green for compute
                        elif "S3" in service or "EBS" in service or "EFS" in service:
                            fillcolor = '#fff3e0'  # Orange for storage
                        elif "RDS" in service or "DynamoDB" in service:
                            fillcolor = '#e3f2fd'  # Blue for database
                        else:
                            fillcolor = '#f3e5f5'  # Purple for others
                        
                        c.node(service, label, fillcolor=fillcolor)
        
        # Add connections
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        all_services_with_external = ["User", "External"] + all_services
        
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        for conn in connections:
            dot.edge(conn['from'], conn['to'], label=conn['label'])
        
        return dot

    @staticmethod
    def _get_config_summary(service: str, config: Dict) -> str:
        """Get configuration summary for node label"""
        if service == "Amazon EC2":
            return f"{config.get('instance_count', 1)}x {config.get('instance_type', 't3.micro')}"
        elif service == "Amazon RDS":
            return f"{config.get('engine', 'PostgreSQL')}"
        elif service == "Amazon S3":
            return f"{config.get('storage_gb', 100)}GB"
        elif service == "AWS Lambda":
            return f"{config.get('memory_mb', 128)}MB"
        elif service == "Amazon ECS":
            return f"{config.get('service_count', 1)} services"
        elif service == "Amazon EKS":
            return f"{config.get('node_count', 2)} nodes"
        return ""

class DiagramRenderer:
    """Render different types of architecture diagrams"""
    
    @staticmethod
    def render_mermaid_diagram(selected_services: Dict, configurations: Dict):
        """Render Mermaid.js diagram"""
        st.subheader("🔗 Mermaid.js Diagram")
        
        mermaid_code = ProfessionalArchitectureGenerator.generate_mermaid_diagram(
            selected_services, configurations
        )
        
        # Display Mermaid diagram
        components.html(
            f"""
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <div class="mermaid">
                {mermaid_code}
            </div>
            <script>
                mermaid.initialize({{ 
                    startOnLoad: true, 
                    theme: 'default',
                    flowchart: {{ 
                        useMaxWidth: true,
                        htmlLabels: true
                    }}
                }});
            </script>
            <style>
                .mermaid {{ 
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #e1e4e8;
                }}
            </style>
            """,
            height=600,
            scrolling=True
        )
        
        with st.expander("View Mermaid Code"):
            st.code(mermaid_code, language="mermaid")

    @staticmethod
    def render_graphviz_diagram(selected_services: Dict, configurations: Dict):
        """Render Graphviz diagram"""
        st.subheader("📊 Graphviz Diagram")
        
        dot = ProfessionalArchitectureGenerator.generate_graphviz_diagram(
            selected_services, configurations
        )
        
        # Display Graphviz diagram
        st.graphviz_chart(dot.source)

class YearlyTimelineCalculator:
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
            if "Year" in timeline_type:
                years = int(timeline_type.split()[0])
                total_months = years * 12
            else:
                total_months = int(timeline_type.split()[0])
                years = total_months // 12
        
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
        
        pattern_multipliers = {
            "Development": 0.6,
            "Sporadic": 0.8,
            "Normal": 1.0,
            "Intensive": 1.4,
            "24x7": 1.8
        }
        
        commitment_discounts = {
            "On-Demand": 1.0,
            "1-Year Reserved": 0.7,
            "3-Year Reserved": 0.5,
            "Savings Plans": 0.72
        }
        
        return {
            "timeline_type": timeline_type,
            "total_months": total_months,
            "years": years,
            "usage_pattern": usage_pattern,
            "pattern_multiplier": pattern_multipliers[usage_pattern],
            "growth_rate": growth_rate,
            "commitment_type": commitment_type,
            "commitment_discount": commitment_discounts[commitment_type]
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

# ... (Keep the rest of your existing DynamicPricingEngine class and other functions exactly as they were)
# [The DynamicPricingEngine, render_service_configurator, and main function remain unchanged]

# Remove the PlantUML option from the diagram type selection in main()
# Change this part in main():

        # ARCHITECTURE DIAGRAMS SECTION
        st.header("🏗️ Architecture Diagrams")
        
        # Diagram type selection (removed PlantUML)
        diagram_type = st.selectbox(
            "Select Diagram Type",
            ["Professional HTML", "Mermaid.js", "Graphviz"],
            index=0,
            help="Choose the type of architecture diagram to generate"
        )
        
        if diagram_type == "Professional HTML":
            # Generate professional diagram
            html_diagram = ProfessionalArchitectureGenerator.generate_professional_diagram_html(
                st.session_state.selected_services,
                st.session_state.configurations,
                requirements
            )
            
            # Display the professional diagram
            st.subheader("📐 Your AWS Architecture")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                try:
                    components.html(html_diagram, height=1000, scrolling=True)
                    
                except Exception as e:
                    st.error(f"Error displaying diagram: {str(e)}")
                    st.code(html_diagram, language="html")
            
            with col2:
                st.subheader("Diagram Controls")
                
                # Diagram information
                with st.expander("📊 Architecture Info", expanded=True):
                    total_services = sum(len(services) for services in st.session_state.selected_services.values())
                    st.metric("Total Services", total_services)
                    
                    categories_used = [cat for cat, services in st.session_state.selected_services.items() if services]
                    st.write("**Categories:**", ", ".join(categories_used))
        
        elif diagram_type == "Mermaid.js":
            DiagramRenderer.render_mermaid_diagram(st.session_state.selected_services, st.session_state.configurations)
        
        elif diagram_type == "Graphviz":
            DiagramRenderer.render_graphviz_diagram(st.session_state.selected_services, st.session_state.configurations)

# ... (Rest of main function remains the same)
        
        # TOTAL COST SUMMARY
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
            
            # Use Streamlit native bar chart
            st.bar_chart(cost_df.set_index('Service')['Total Cost'])

if __name__ == "__main__":
    main()