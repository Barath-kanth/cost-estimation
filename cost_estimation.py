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
            "External": "https://icon.icepanel.io/AWS/svg/General-Icons/Internet-Gateway.svg"
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

    @staticmethod
    def render_plantuml_diagram(selected_services: Dict, configurations: Dict):
        """Render PlantUML diagram (converted to image)"""
        st.subheader("🌿 PlantUML Diagram")
        
        plantuml_code = DiagramRenderer._generate_plantuml_code(selected_services, configurations)
        
        if st.button("Generate PlantUML Diagram"):
            with st.spinner("Generating PlantUML diagram..."):
                diagram_image = DiagramRenderer._plantuml_to_image(plantuml_code)
                if diagram_image:
                    st.image(diagram_image, caption="AWS Architecture Diagram (PlantUML)", use_column_width=True)
        
        with st.expander("View PlantUML Code"):
            st.code(plantuml_code, language="plantuml")

    @staticmethod
    def _generate_plantuml_code(selected_services: Dict, configurations: Dict) -> str:
        """Generate PlantUML code for the architecture"""
        plantuml_code = """@startuml
!define AWSPREFIX https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v14.0/dist
!includeurl AWSPREFIX/AWSCommon.puml

skinparam nodesep 10
skinparam ranksep 10
skinparam defaultTextAlignment center
skinparam roundcorner 10

rectangle "User" as user
rectangle "External Systems" as external

cloud AWS {
"""
        
        # Add services
        for category, services in selected_services.items():
            if services:
                plantuml_code += f"  folder {category} {{\n"
                for service in services:
                    config = configurations.get(service, {}).get('config', {})
                    config_text = ProfessionalArchitectureGenerator._get_config_summary(service, config)
                    
                    if service == "Amazon EC2":
                        plantuml_code += f'    EC2("{service}\\n{config_text}") as {service.replace(" ", "")}\n'
                    elif service == "Amazon S3":
                        plantuml_code += f'    S3("{service}\\n{config_text}") as {service.replace(" ", "")}\n'
                    elif service == "Amazon RDS":
                        plantuml_code += f'    RDS("{service}\\n{config_text}") as {service.replace(" ", "")}\n'
                    elif service == "AWS Lambda":
                        plantuml_code += f'    Lambda("{service}\\n{config_text}") as {service.replace(" ", "")}\n'
                    elif service == "Amazon EKS":
                        plantuml_code += f'    EKS("{service}\\n{config_text}") as {service.replace(" ", "")}\n'
                    else:
                        plantuml_code += f'    rectangle "{service}\\n{config_text}" as {service.replace(" ", "")}\n'
                plantuml_code += "  }\n"
        
        plantuml_code += "}\n\n"
        
        # Add connections
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        all_services_with_external = ["User", "External"] + all_services
        
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        for conn in connections:
            from_node = conn['from'].replace(" ", "")
            to_node = conn['to'].replace(" ", "")
            plantuml_code += f'{from_node} --> {to_node} : {conn["label"]}\n'
        
        plantuml_code += "@enduml"
        return plantuml_code

    @staticmethod
    def _plantuml_to_image(plantuml_code: str) -> Image:
        """Convert PlantUML code to image using PlantUML server with correct encoding"""
        try:
            # Compress the PlantUML code using DEFLATE algorithm
            compressed = zlib.compress(plantuml_code.encode('utf-8'))[2:-4]
            
            # Encode to base64
            encoded = base64.b64encode(compressed).decode('utf-8')
            
            # Replace characters for PlantUML URL encoding
            encoded = encoded.translate(bytes.maketrans(
                b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
                b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
            ))
            
            # Add the ~1 header for HUFFMAN encoding
            plantuml_url = f"https://www.plantuml.com/plantuml/png/~1{encoded}"
            
            response = requests.get(plantuml_url)
            if response.status_code == 200:
                return Image.open(io.BytesIO(response.content))
            else:
                st.error(f"Failed to generate PlantUML diagram. Status code: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error generating PlantUML diagram: {e}")
            return None

    @staticmethod
    def _generate_plantuml_code(selected_services: Dict, configurations: Dict) -> str:
        """Generate PlantUML code for the architecture"""
        plantuml_code = """@startuml
!define AWSPREFIX https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v14.0/dist
!includeurl AWSPREFIX/AWSCommon.puml

title AWS Architecture Diagram

skinparam nodesep 10
skinparam ranksep 10
skinparam defaultTextAlignment center
skinparam roundcorner 10
skinparam backgroundColor #FFFFFF
skinparam shadowing false

rectangle "User" as user
rectangle "External Systems" as external

cloud AWS {
"""
        
        # Add services by category
        for category, services in selected_services.items():
            if services:
                plantuml_code += f"  folder {category} {{\n"
                for service in services:
                    config = configurations.get(service, {}).get('config', {})
                    config_text = ProfessionalArchitectureGenerator._get_config_summary(service, config)
                    
                    # Use AWS icons for common services
                    if service == "Amazon EC2":
                        plantuml_code += f'    EC2("{service}\\n{config_text}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    elif service == "Amazon S3":
                        plantuml_code += f'    S3("{service}\\n{config_text}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    elif service == "Amazon RDS":
                        plantuml_code += f'    RDS("{service}\\n{config_text}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    elif service == "AWS Lambda":
                        plantuml_code += f'    Lambda("{service}\\n{config_text}") as {service.replace(" ", "").replace("AWS", "")}\n'
                    elif service == "Amazon EKS":
                        plantuml_code += f'    EKS("{service}\\n{config_text}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    elif service == "Amazon CloudFront":
                        plantuml_code += f'    CloudFront("{service}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    elif service == "Elastic Load Balancing":
                        plantuml_code += f'    ElasticLoadBalancing("{service}") as {service.replace(" ", "")}\n'
                    elif service == "Amazon API Gateway":
                        plantuml_code += f'    APIGateway("{service}") as {service.replace(" ", "").replace("Amazon", "")}\n'
                    else:
                        plantuml_code += f'    rectangle "{service}\\n{config_text}" as {service.replace(" ", "").replace("Amazon", "").replace("AWS", "")}\n'
                plantuml_code += "  }\n"
        
        plantuml_code += "}\n\n"
        
        # Add connections
        all_services = []
        for services in selected_services.values():
            all_services.extend(services)
        all_services_with_external = ["User", "External"] + all_services
        
        connections = ProfessionalArchitectureGenerator.generate_connections(all_services_with_external)
        for conn in connections:
            from_node = conn['from'].replace(" ", "").replace("Amazon", "").replace("AWS", "")
            to_node = conn['to'].replace(" ", "").replace("Amazon", "").replace("AWS", "")
            plantuml_code += f'{from_node} --> {to_node} : {conn["label"]}\n'
        
        plantuml_code += "@enduml"
        return plantuml_code

    @staticmethod
    def render_plantuml_diagram(selected_services: Dict, configurations: Dict):
        """Render PlantUML diagram with improved error handling"""
        st.subheader("🌿 PlantUML Diagram")
        
        if not selected_services:
            st.info("Please select some AWS services first.")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            st.write("**Diagram Options**")
            diagram_theme = st.selectbox(
                "Theme",
                ["Default", "AWS", "Simple"],
                key="plantuml_theme"
            )
            
            if st.button("🔄 Generate PlantUML Diagram", type="primary"):
                st.session_state.generate_plantuml = True
        
        with col1:
            if st.session_state.get('generate_plantuml', False):
                with st.spinner("Generating PlantUML diagram..."):
                    plantuml_code = DiagramRenderer._generate_plantuml_code(selected_services, configurations)
                    diagram_image = DiagramRenderer._plantuml_to_image(plantuml_code)
                    
                    if diagram_image:
                        st.image(diagram_image, caption="AWS Architecture Diagram (PlantUML)", use_column_width=True)
                        st.success("✅ PlantUML diagram generated successfully!")
                    else:
                        st.error("❌ Failed to generate PlantUML diagram. Please try again.")
            
            # Always show the code
            with st.expander("📋 View PlantUML Code", expanded=True):
                plantuml_code = DiagramRenderer._generate_plantuml_code(selected_services, configurations)
                st.code(plantuml_code, language="plantuml")
                
                # Download button for PlantUML code
                st.download_button(
                    label="📥 Download PlantUML Code",
                    data=plantuml_code,
                    file_name="aws_architecture.puml",
                    mime="text/plain"
                )

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
            yearly_data = DynamicPricingEngine.calculate_yearly_costs(
                discounted_price, 
                timeline_config["years"],
                timeline_config["growth_rate"]
            )
        else:
            yearly_data = {"years": [], "yearly_costs": [], "monthly_costs": [], "cumulative_costs": [], "total_cost": 0.0}
        
        if timeline_config["total_months"] > 0:
            monthly_data = DynamicPricingEngine.calculate_detailed_monthly_timeline(
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
    def calculate_yearly_costs(base_monthly_cost: float, years: int, growth_rate: float = 0.0) -> Dict:
        """Calculate costs over years with growth rate"""
        yearly_data = {
            "years": [],
            "yearly_costs": [],
            "monthly_costs": [],
            "cumulative_costs": [],
            "total_cost": 0.0
        }
        
        if years == 0:
            return yearly_data
            
        cumulative = 0.0
        for year in range(1, years + 1):
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
        
        if total_months == 0:
            return monthly_data
            
        cumulative = 0.0
        for month in range(1, total_months + 1):
            monthly_cost = base_monthly_cost * (1 + growth_rate) ** (month - 1)
            cumulative += monthly_cost
            
            year = (month - 1) // 12 + 1
            month_in_year = (month - 1) % 12 + 1
            monthly_data["months"].append(f"Y{year} M{month_in_year}")
            monthly_data["monthly_costs"].append(monthly_cost)
            monthly_data["cumulative_costs"].append(cumulative)
        
        monthly_data["total_cost"] = cumulative
        return monthly_data
    
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
            
        elif service == "Amazon EBS":
            storage_gb = config.get('storage_gb', 30)
            volume_type = config.get('volume_type', 'gp3')
            iops = config.get('iops', 3000) if volume_type in ['io1', 'io2'] else 0
            
            storage_price_per_gb = {
                'gp3': 0.08, 'gp2': 0.10, 'io1': 0.125, 'io2': 0.125,
                'st1': 0.045, 'sc1': 0.015
            }
            
            base_price = storage_gb * storage_price_per_gb.get(volume_type, 0.08)
            
            # Add IOPS cost for provisioned IOPS volumes
            if volume_type in ['io1', 'io2']:
                base_price += iops * 0.065  # $0.065 per provisioned IOPS
            
            return base_price
            
        elif service == "Amazon EFS":
            storage_gb = config.get('storage_gb', 100)
            storage_class = config.get('storage_class', 'Standard')
            
            efs_prices = {
                'Standard': 0.30,  # $0.30 per GB-month
                'Infrequent Access': 0.025  # $0.025 per GB-month
            }
            
            return storage_gb * efs_prices.get(storage_class, 0.30)
            
        elif service == "Amazon ElastiCache":
            node_type = config.get('node_type', 'cache.t3.micro')
            node_count = config.get('node_count', 1)
            engine = config.get('engine', 'Redis')
            
            cache_prices = {
                'cache.t3.micro': 0.020, 'cache.t3.small': 0.038, 'cache.t3.medium': 0.076,
                'cache.m5.large': 0.171, 'cache.r5.large': 0.242
            }
            
            base_price = cache_prices.get(node_type, 0.1) * 730 * node_count
            
            # Engine multiplier
            if engine == 'Memcached':
                base_price *= 0.9  # Memcached is slightly cheaper
            
            return base_price
            
        elif service == "Amazon CloudFront":
            data_transfer_tb = config.get('data_transfer_tb', 50)
            requests_million = config.get('requests_million', 10)
            
            # Data transfer pricing (per GB)
            data_transfer_cost = data_transfer_tb * 1024 * 0.085  # $0.085 per GB
            
            # Request pricing (per 10,000 requests)
            request_cost = requests_million * 100 * 0.0075  # $0.0075 per 10,000 requests
            
            return data_transfer_cost + request_cost
            
        elif service == "Elastic Load Balancing":
            lb_type = config.get('lb_type', 'Application Load Balancer')
            lcu_count = config.get('lcu_count', 10000)
            data_processed_tb = config.get('data_processed_tb', 10)
            
            if lb_type == 'Application Load Balancer':
                # ALB pricing: $0.0225 per ALB-hour + $0.008 per LCU-hour
                alb_hourly = 0.0225 * 730  # $0.0225 per hour
                lcu_cost = lcu_count * 0.008  # $0.008 per LCU-hour
                return alb_hourly + lcu_cost
            else:
                # NLB pricing: $0.0225 per NLB-hour + $0.006 per NLCU-hour
                nlb_hourly = 0.0225 * 730  # $0.0225 per hour
                nlcu_cost = lcu_count * 0.006  # $0.006 per NLCU-hour
                return nlb_hourly + nlcu_cost
            
        elif service == "Amazon VPC":
            vpc_count = config.get('vpc_count', 1)
            nat_gateways = config.get('nat_gateways', 2)
            vpc_endpoints = config.get('vpc_endpoints', 5)
            vpn_connections = config.get('vpn_connections', 0)
            
            # VPC is free, but associated services have costs
            nat_cost = nat_gateways * 0.045 * 730  # $0.045 per NAT Gateway-hour
            endpoint_cost = vpc_endpoints * 0.01 * 730  # $0.01 per endpoint-hour
            vpn_cost = vpn_connections * 0.05 * 730  # $0.05 per VPN connection-hour
            
            return nat_cost + endpoint_cost + vpn_cost
            
        elif service == "AWS WAF":
            web_acls = config.get('web_acls', 2)
            rules_per_acl = config.get('rules_per_acl', 10)
            requests_billion = config.get('requests_billion', 1.0)
            managed_rules = config.get('managed_rules', True)
            
            web_acl_cost = web_acls * 5.00  # $5.00 per web ACL per month
            rule_cost = web_acls * rules_per_acl * 1.00  # $1.00 per rule per month
            request_cost = requests_billion * 0.60  # $0.60 per million requests
            managed_rule_cost = web_acls * 1.00 if managed_rules else 0  # $1.00 per managed rule set
            
            return web_acl_cost + rule_cost + request_cost + managed_rule_cost
            
        elif service == "AWS Shield":
            protection_level = config.get('protection_level', 'Standard')
            protected_resources = config.get('protected_resources', 5)
            
            if protection_level == 'Standard':
                # Shield Standard is free
                return 0
            else:
                # Shield Advanced: $3000 per month + $XXX per protected resource
                shield_advanced_cost = 3000  # $3000 per month
                resource_cost = protected_resources * 100  # $100 per protected resource
                return shield_advanced_cost + resource_cost
            
        elif service == "Amazon GuardDuty":
            data_sources = config.get('data_sources', ['CloudTrail', 'VPC', 'DNS'])
            protected_accounts = config.get('protected_accounts', 1)
            
            # GuardDuty pricing per GB of data analyzed
            cloudtrail_cost = 1.00 if 'CloudTrail' in data_sources else 0  # $1.00 per GB
            vpc_cost = 0.50 if 'VPC' in data_sources else 0  # $0.50 per GB
            dns_cost = 0.50 if 'DNS' in data_sources else 0  # $0.50 per GB
            
            # Estimate data volumes (simplified)
            estimated_data_gb = 100  # Simplified estimate
            
            base_cost = (cloudtrail_cost + vpc_cost + dns_cost) * estimated_data_gb
            
            # Multi-account multiplier
            if protected_accounts > 1:
                base_cost *= protected_accounts * 0.8  # Volume discount
            
            return base_cost
            
        elif service == "Amazon SageMaker":
            usage_type = config.get('usage_type', 'Training')
            training_hours = config.get('training_hours', 100)
            inference_hours = config.get('inference_hours', 1000)
            notebook_hours = config.get('notebook_hours', 160)
            storage_gb = config.get('storage_gb', 500)
            
            base_cost = 0
            
            if usage_type in ['Training', 'All']:
                # ml.m5.xlarge instance: $0.269 per hour
                base_cost += training_hours * 0.269
            
            if usage_type in ['Inference', 'All']:
                # ml.m5.large instance: $0.134 per hour
                base_cost += inference_hours * 0.134
            
            if usage_type in ['Notebooks', 'All']:
                # ml.t3.medium instance: $0.0582 per hour
                base_cost += notebook_hours * 0.0582
            
            # EBS storage for models and data
            base_cost += storage_gb * 0.23  # $0.23 per GB-month
            
            return base_cost
            
        elif service == "Amazon Bedrock":
            input_tokens_million = config.get('input_tokens_million', 10)
            output_tokens_million = config.get('output_tokens_million', 5)
            custom_models = config.get('custom_models', 0)
            fine_tuning_hours = config.get('fine_tuning_hours', 0)
            
            # Claude model pricing (example)
            input_cost = input_tokens_million * 0.80  # $0.80 per million input tokens
            output_cost = output_tokens_million * 4.00  # $4.00 per million output tokens
            custom_model_cost = custom_models * 100  # $100 per custom model per month
            fine_tuning_cost = fine_tuning_hours * 50  # $50 per fine-tuning hour
            
            return input_cost + output_cost + custom_model_cost + fine_tuning_cost
        
        # Default case for services without specific pricing
        return 0.0

def render_service_configurator(service: str, key_prefix: str) -> Dict:
    """Render configuration options for selected service"""
    config = {}
    
    if service == "Amazon EC2":
        st.write("**Instance Configuration**")
        
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
                "c5.xlarge": {"vCPU": 4, "Memory": 8, "Description": "High performance compute"}
            },
            "Memory Optimized": {
                "r5.large": {"vCPU": 2, "Memory": 16, "Description": "Memory intensive applications"},
                "r5.xlarge": {"vCPU": 4, "Memory": 32, "Description": "High memory workloads"}
            }
        }
        
        selected_family = st.selectbox(
            "Instance Family",
            list(instance_families.keys()),
            key=f"{key_prefix}_family"
        )
        
        if selected_family:
            instance_options = instance_families[selected_family]
            selected_instance = st.selectbox(
                "Instance Type",
                list(instance_options.keys()),
                format_func=lambda x: f"{x} ({instance_options[x]['vCPU']} vCPU, {instance_options[x]['Memory']}GB) - {instance_options[x]['Description']}",
                key=f"{key_prefix}_instance_type"
            )
            config['instance_type'] = selected_instance
            
            config['instance_count'] = st.slider(
                "Number of Instances",
                min_value=1,
                max_value=20,
                value=2,
                key=f"{key_prefix}_instance_count"
            )
            
            st.write("**Storage Configuration**")
            config['storage_gb'] = st.slider(
                "Storage (GB)",
                min_value=20,
                max_value=1000,
                value=100,
                step=10,
                key=f"{key_prefix}_storage_gb"
            )
            
            config['volume_type'] = st.selectbox(
                "Volume Type",
                ["gp3", "gp2", "io1", "io2", "st1", "sc1"],
                index=0,
                key=f"{key_prefix}_volume_type"
            )
            
            if config['volume_type'] in ['io1', 'io2']:
                config['iops'] = st.slider(
                    "Provisioned IOPS",
                    min_value=100,
                    max_value=16000,
                    value=3000,
                    step=100,
                    key=f"{key_prefix}_iops"
                )
    
    elif service == "Amazon RDS":
        st.write("**Database Configuration**")
        
        config['engine'] = st.selectbox(
            "Database Engine",
            ["PostgreSQL", "MySQL", "Aurora MySQL", "SQL Server"],
            key=f"{key_prefix}_engine"
        )
        
        instance_types = {
            "db.t3.micro": "Burstable micro instance",
            "db.t3.small": "Burstable small instance", 
            "db.t3.medium": "Burstable medium instance",
            "db.m5.large": "General purpose large",
            "db.m5.xlarge": "General purpose xlarge",
            "db.r5.large": "Memory optimized large"
        }
        
        config['instance_type'] = st.selectbox(
            "Instance Type",
            list(instance_types.keys()),
            format_func=lambda x: f"{x} - {instance_types[x]}",
            key=f"{key_prefix}_rds_instance"
        )
        
        config['storage_gb'] = st.slider(
            "Storage (GB)",
            min_value=20,
            max_value=1000,
            value=100,
            key=f"{key_prefix}_rds_storage"
        )
        
        config['multi_az'] = st.checkbox(
            "Multi-AZ Deployment",
            value=False,
            key=f"{key_prefix}_multi_az"
        )
        
        config['backup_retention'] = st.slider(
            "Backup Retention (days)",
            min_value=1,
            max_value=35,
            value=7,
            key=f"{key_prefix}_backup_retention"
        )
    
    elif service == "Amazon S3":
        st.write("**Storage Configuration**")
        
        config['storage_gb'] = st.slider(
            "Storage Capacity (GB)",
            min_value=10,
            max_value=10000,
            value=1000,
            step=10,
            key=f"{key_prefix}_s3_storage"
        )
        
        config['storage_class'] = st.selectbox(
            "Storage Class",
            ["Standard", "Intelligent-Tiering", "Standard-IA", "One Zone-IA", "Glacier", "Glacier Deep Archive"],
            key=f"{key_prefix}_storage_class"
        )
    
    elif service == "AWS Lambda":
        st.write("**Function Configuration**")
        
        config['memory_mb'] = st.slider(
            "Memory (MB)",
            min_value=128,
            max_value=10240,
            value=512,
            step=128,
            key=f"{key_prefix}_memory"
        )
        
        config['requests_per_month'] = st.slider(
            "Monthly Requests",
            min_value=100000,
            max_value=10000000,
            value=1000000,
            step=100000,
            key=f"{key_prefix}_requests"
        )
        
        config['avg_duration_ms'] = st.slider(
            "Average Duration (ms)",
            min_value=50,
            max_value=10000,
            value=200,
            step=50,
            key=f"{key_prefix}_duration"
        )
    
    # Add configuration for other services as needed...
    
    return config

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
                        requirements
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
        
        # MULTIPLE DIAGRAM VIEWS
        st.header("🎨 Architecture Diagrams")
        
        diagram_tabs = st.tabs(["Professional HTML", "Mermaid.js", "Graphviz", "PlantUML"])
        
        with diagram_tabs[0]:
            # Generate professional diagram
            html_diagram = ProfessionalArchitectureGenerator.generate_professional_diagram_html(
                st.session_state.selected_services,
                st.session_state.configurations,
                requirements
            )
            
            # Display the professional diagram
            st.subheader("📐 Professional Architecture Diagram")
            components.html(html_diagram, height=1000, scrolling=True)
        
        with diagram_tabs[1]:
            DiagramRenderer.render_mermaid_diagram(
                st.session_state.selected_services,
                st.session_state.configurations
            )
        
        with diagram_tabs[2]:
            DiagramRenderer.render_graphviz_diagram(
                st.session_state.selected_services,
                st.session_state.configurations
            )
        
        with diagram_tabs[3]:
            DiagramRenderer.render_plantuml_diagram(
                st.session_state.selected_services,
                st.session_state.configurations
            )
        
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
            
            # Pie chart for cost distribution
            st.subheader("🥧 Cost Distribution")
            st.plotly_chart(
                px.pie(cost_df, values='Total Cost', names='Service', 
                      title='Cost Distribution by Service'),
                use_container_width=True
            )

if __name__ == "__main__":
    main()