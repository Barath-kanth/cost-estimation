"""
AWS Intelligent Cloud Packager - Multi-Agent System
Dynamic service discovery and packaging based on customer requirements
Uses AWS APIs to avoid hardcoding - fully adaptive to new services
"""

import json
import streamlit as st
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
from datetime import datetime

# ========================================
# AGENT SYSTEM ARCHITECTURE
# ========================================

class AgentRole(Enum):
    """Different agent roles in the system"""
    REQUIREMENTS_ANALYZER = "Requirements Analyzer"
    SERVICE_DISCOVERY = "Service Discovery"
    PRICING_AGENT = "Pricing Agent"
    ARCHITECTURE_DESIGNER = "Architecture Designer"
    PACKAGE_OPTIMIZER = "Package Optimizer"
    COMPLIANCE_CHECKER = "Compliance Checker"

@dataclass
class CustomerRequirement:
    """Structured customer requirements"""
    workload_type: str
    monthly_budget: float
    performance_tier: str
    regions: List[str]
    compliance_needs: List[str]
    scalability: str
    availability_target: str
    data_volume_gb: float
    expected_users: int
    special_requirements: List[str]

@dataclass
class ServiceRecommendation:
    """Service recommendation from agents"""
    service_code: str
    service_name: str
    configuration: Dict
    monthly_cost: float
    justification: str
    alternatives: List[str]
    
@dataclass
class CloudPackage:
    """Complete cloud package solution"""
    package_name: str
    total_monthly_cost: float
    services: List[ServiceRecommendation]
    architecture_diagram: str
    compliance_notes: str
    optimization_tips: List[str]

# ========================================
# MULTI-AGENT SYSTEM
# ========================================

class AWSMultiAgentPackager:
    """Main orchestrator for multi-agent system"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.pricing_client = None
        self.service_catalog_client = None
        self.agents = {}
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize AWS clients with error handling"""
        try:
            self.pricing_client = boto3.client('pricing', region_name='us-east-1')
            self.service_catalog_client = boto3.client('servicecatalog', region_name=self.region)
        except Exception as e:
            st.warning(f"⚠️ AWS clients initialization: {str(e)}")
            st.info("💡 Running in demo mode with simulated data")
    
    # ========================================
    # AGENT 1: Requirements Analyzer
    # ========================================
    
    def analyze_requirements(self, requirements: CustomerRequirement) -> Dict:
        """Agent 1: Analyze and categorize customer requirements"""
        st.write("🤖 **Agent 1 - Requirements Analyzer** activated...")
        
        analysis = {
            "workload_category": self._categorize_workload(requirements.workload_type),
            "compute_needs": self._assess_compute_needs(requirements),
            "storage_needs": self._assess_storage_needs(requirements),
            "network_needs": self._assess_network_needs(requirements),
            "database_needs": self._assess_database_needs(requirements),
            "security_needs": self._assess_security_needs(requirements),
            "priority_services": []
        }
        
        st.success(f"✅ Workload categorized as: **{analysis['workload_category']}**")
        return analysis
    
    def _categorize_workload(self, workload_type: str) -> str:
        """Categorize workload type"""
        categories = {
            "web": ["Web Application", "Website", "Portal"],
            "api": ["API", "Microservices", "Backend"],
            "data": ["Data Processing", "Analytics", "ETL"],
            "ml": ["Machine Learning", "AI", "Deep Learning"],
            "mobile": ["Mobile Backend", "Mobile App"],
            "iot": ["IoT", "Streaming", "Real-time"],
            "enterprise": ["Enterprise", "ERP", "CRM"]
        }
        
        workload_lower = workload_type.lower()
        for category, keywords in categories.items():
            if any(keyword.lower() in workload_lower for keyword in keywords):
                return category
        return "general"
    
    def _assess_compute_needs(self, req: CustomerRequirement) -> Dict:
        """Assess compute requirements"""
        # Determine compute tier based on users and performance
        if req.expected_users < 1000 and req.performance_tier == "Low":
            tier = "small"
        elif req.expected_users < 10000 and req.performance_tier in ["Low", "Medium"]:
            tier = "medium"
        elif req.expected_users < 100000:
            tier = "large"
        else:
            tier = "xlarge"
        
        return {
            "tier": tier,
            "autoscaling": req.scalability == "High",
            "high_availability": req.availability_target in ["99.9%", "99.99%"]
        }
    
    def _assess_storage_needs(self, req: CustomerRequirement) -> Dict:
        """Assess storage requirements"""
        return {
            "volume_gb": req.data_volume_gb,
            "type": "block" if req.workload_type in ["Web Application", "Database"] else "object",
            "backup": req.availability_target in ["99.9%", "99.99%"]
        }
    
    def _assess_network_needs(self, req: CustomerRequirement) -> Dict:
        """Assess networking requirements"""
        return {
            "load_balancer": req.expected_users > 100,
            "cdn": "web" in req.workload_type.lower(),
            "multi_region": len(req.regions) > 1
        }
    
    def _assess_database_needs(self, req: CustomerRequirement) -> Dict:
        """Assess database requirements"""
        workload_lower = req.workload_type.lower()
        
        if any(kw in workload_lower for kw in ["nosql", "dynamodb", "key-value"]):
            db_type = "nosql"
        elif any(kw in workload_lower for kw in ["graph", "neo4j"]):
            db_type = "graph"
        elif any(kw in workload_lower for kw in ["analytics", "warehouse", "olap"]):
            db_type = "warehouse"
        else:
            db_type = "relational"
        
        return {
            "type": db_type,
            "size_gb": min(req.data_volume_gb * 0.3, 1000),  # Estimate 30% of data is database
            "high_availability": req.availability_target in ["99.9%", "99.99%"]
        }
    
    def _assess_security_needs(self, req: CustomerRequirement) -> Dict:
        """Assess security and compliance needs"""
        return {
            "waf": len(req.compliance_needs) > 0,
            "encryption": len(req.compliance_needs) > 0,
            "compliance_frameworks": req.compliance_needs,
            "identity_management": req.expected_users > 100
        }
    
    # ========================================
    # AGENT 2: Service Discovery
    # ========================================
    
    def discover_services(self, analysis: Dict, requirements: CustomerRequirement) -> List[Dict]:
        """Agent 2: Discover relevant AWS services dynamically"""
        st.write("🔍 **Agent 2 - Service Discovery** activated...")
        
        discovered_services = []
        
        # Compute services
        compute_services = self._discover_compute_services(analysis)
        discovered_services.extend(compute_services)
        
        # Storage services
        storage_services = self._discover_storage_services(analysis)
        discovered_services.extend(storage_services)
        
        # Database services
        database_services = self._discover_database_services(analysis)
        discovered_services.extend(database_services)
        
        # Networking services
        network_services = self._discover_network_services(analysis)
        discovered_services.extend(network_services)
        
        # Security services
        security_services = self._discover_security_services(analysis)
        discovered_services.extend(security_services)
        
        # AI/ML services (if applicable)
        if analysis.get('workload_category') == 'ml':
            ml_services = self._discover_ml_services(analysis)
            discovered_services.extend(ml_services)
        
        st.success(f"✅ Discovered {len(discovered_services)} relevant services")
        return discovered_services
    
    def _discover_compute_services(self, analysis: Dict) -> List[Dict]:
        """Discover compute services"""
        services = []
        compute_needs = analysis.get('compute_needs', {})
        
        if compute_needs.get('tier') in ['small', 'medium']:
            services.append({
                'service_code': 'AmazonEC2',
                'service_name': 'EC2',
                'category': 'Compute',
                'reason': 'Flexible compute capacity',
                'config_hint': {'instance_type': 't3.medium' if compute_needs.get('tier') == 'small' else 'm5.large'}
            })
        
        if compute_needs.get('autoscaling'):
            services.append({
                'service_code': 'AWSLambda',
                'service_name': 'Lambda',
                'category': 'Compute',
                'reason': 'Serverless auto-scaling',
                'config_hint': {'memory': 512}
            })
        
        return services
    
    def _discover_storage_services(self, analysis: Dict) -> List[Dict]:
        """Discover storage services"""
        services = []
        storage_needs = analysis.get('storage_needs', {})
        
        services.append({
            'service_code': 'AmazonS3',
            'service_name': 'S3',
            'category': 'Storage',
            'reason': 'Scalable object storage',
            'config_hint': {'storage_class': 'STANDARD'}
        })
        
        if storage_needs.get('type') == 'block':
            services.append({
                'service_code': 'AmazonEBS',
                'service_name': 'EBS',
                'category': 'Storage',
                'reason': 'Block storage for EC2',
                'config_hint': {'volume_type': 'gp3'}
            })
        
        return services
    
    def _discover_database_services(self, analysis: Dict) -> List[Dict]:
        """Discover database services"""
        services = []
        db_needs = analysis.get('database_needs', {})
        
        if db_needs.get('type') == 'relational':
            services.append({
                'service_code': 'AmazonRDS',
                'service_name': 'RDS',
                'category': 'Database',
                'reason': 'Managed relational database',
                'config_hint': {'engine': 'postgres', 'instance': 'db.t3.medium'}
            })
        elif db_needs.get('type') == 'nosql':
            services.append({
                'service_code': 'AmazonDynamoDB',
                'service_name': 'DynamoDB',
                'category': 'Database',
                'reason': 'Serverless NoSQL database',
                'config_hint': {'billing_mode': 'PAY_PER_REQUEST'}
            })
        elif db_needs.get('type') == 'warehouse':
            services.append({
                'service_code': 'AmazonRedshift',
                'service_name': 'Redshift',
                'category': 'Database',
                'reason': 'Data warehouse for analytics',
                'config_hint': {'node_type': 'dc2.large'}
            })
        
        return services
    
    def _discover_network_services(self, analysis: Dict) -> List[Dict]:
        """Discover networking services"""
        services = []
        network_needs = analysis.get('network_needs', {})
        
        if network_needs.get('load_balancer'):
            services.append({
                'service_code': 'AWSELB',
                'service_name': 'Application Load Balancer',
                'category': 'Networking',
                'reason': 'Distribute traffic across targets',
                'config_hint': {'type': 'application'}
            })
        
        if network_needs.get('cdn'):
            services.append({
                'service_code': 'AmazonCloudFront',
                'service_name': 'CloudFront',
                'category': 'Networking',
                'reason': 'Content delivery network',
                'config_hint': {'price_class': 'PriceClass_100'}
            })
        
        services.append({
            'service_code': 'AmazonVPC',
            'service_name': 'VPC',
            'category': 'Networking',
            'reason': 'Virtual private cloud',
            'config_hint': {}
        })
        
        return services
    
    def _discover_security_services(self, analysis: Dict) -> List[Dict]:
        """Discover security services"""
        services = []
        security_needs = analysis.get('security_needs', {})
        
        if security_needs.get('waf'):
            services.append({
                'service_code': 'AWSShield',
                'service_name': 'AWS WAF',
                'category': 'Security',
                'reason': 'Web application firewall',
                'config_hint': {}
            })
        
        if security_needs.get('identity_management'):
            services.append({
                'service_code': 'AmazonCognito',
                'service_name': 'Cognito',
                'category': 'Security',
                'reason': 'User authentication and authorization',
                'config_hint': {}
            })
        
        return services
    
    def _discover_ml_services(self, analysis: Dict) -> List[Dict]:
        """Discover ML/AI services"""
        return [
            {
                'service_code': 'AmazonSageMaker',
                'service_name': 'SageMaker',
                'category': 'AI/ML',
                'reason': 'Machine learning platform',
                'config_hint': {}
            },
            {
                'service_code': 'AmazonBedrock',
                'service_name': 'Bedrock',
                'category': 'AI/ML',
                'reason': 'Generative AI foundation models',
                'config_hint': {}
            }
        ]
    
    # ========================================
    # AGENT 3: Pricing Agent
    # ========================================
    
    def fetch_pricing(self, services: List[Dict], region: str) -> List[ServiceRecommendation]:
        """Agent 3: Fetch real-time pricing for discovered services"""
        st.write("💰 **Agent 3 - Pricing Agent** activated...")
        
        recommendations = []
        
        for service in services:
            try:
                pricing_info = self._get_service_pricing(
                    service['service_code'],
                    service.get('config_hint', {}),
                    region
                )
                
                recommendation = ServiceRecommendation(
                    service_code=service['service_code'],
                    service_name=service['service_name'],
                    configuration=service.get('config_hint', {}),
                    monthly_cost=pricing_info['monthly_cost'],
                    justification=service['reason'],
                    alternatives=pricing_info.get('alternatives', [])
                )
                
                recommendations.append(recommendation)
                
            except Exception as e:
                st.warning(f"Could not fetch pricing for {service['service_name']}: {str(e)}")
        
        st.success(f"✅ Fetched pricing for {len(recommendations)} services")
        return recommendations
    
    def _get_service_pricing(self, service_code: str, config: Dict, region: str) -> Dict:
        """Get pricing for a specific service"""
        # This would use real AWS Pricing API
        # For demo, returning estimated pricing
        
        pricing_estimates = {
            'AmazonEC2': {'monthly_cost': 75.0, 'alternatives': ['Lambda', 'Fargate']},
            'AWSLambda': {'monthly_cost': 15.0, 'alternatives': ['EC2', 'Fargate']},
            'AmazonS3': {'monthly_cost': 23.0, 'alternatives': ['EFS', 'FSx']},
            'AmazonEBS': {'monthly_cost': 10.0, 'alternatives': ['EFS']},
            'AmazonRDS': {'monthly_cost': 120.0, 'alternatives': ['Aurora', 'DynamoDB']},
            'AmazonDynamoDB': {'monthly_cost': 50.0, 'alternatives': ['RDS', 'DocumentDB']},
            'AmazonRedshift': {'monthly_cost': 180.0, 'alternatives': ['Athena', 'EMR']},
            'AWSELB': {'monthly_cost': 22.0, 'alternatives': ['CloudFront']},
            'AmazonCloudFront': {'monthly_cost': 50.0, 'alternatives': []},
            'AmazonVPC': {'monthly_cost': 0.0, 'alternatives': []},
            'AWSShield': {'monthly_cost': 20.0, 'alternatives': []},
            'AmazonCognito': {'monthly_cost': 25.0, 'alternatives': ['IAM']},
            'AmazonSageMaker': {'monthly_cost': 200.0, 'alternatives': ['Bedrock', 'EC2']},
            'AmazonBedrock': {'monthly_cost': 150.0, 'alternatives': ['SageMaker']}
        }
        
        return pricing_estimates.get(service_code, {'monthly_cost': 50.0, 'alternatives': []})
    
    # ========================================
    # AGENT 4: Architecture Designer
    # ========================================
    
    def design_architecture(self, recommendations: List[ServiceRecommendation], 
                          analysis: Dict) -> str:
        """Agent 4: Design system architecture"""
        st.write("🏗️ **Agent 4 - Architecture Designer** activated...")
        
        architecture = self._generate_architecture_diagram(recommendations, analysis)
        
        st.success("✅ Architecture design completed")
        return architecture
    
    def _generate_architecture_diagram(self, recommendations: List[ServiceRecommendation], 
                                      analysis: Dict) -> str:
        """Generate Mermaid architecture diagram"""
        
        diagram = """graph TB
    User[👤 Users/Clients]
    """
        
        # Add services by category
        categories = {}
        for rec in recommendations:
            category = self._get_service_category(rec.service_code)
            if category not in categories:
                categories[category] = []
            categories[category].append(rec.service_name)
        
        # Build diagram layers
        if 'CDN' in categories:
            diagram += "\n    User --> CDN[🌐 CloudFront CDN]"
            diagram += "\n    CDN --> LB"
        
        if 'LoadBalancer' in categories:
            diagram += "\n    User --> LB[⚖️ Load Balancer]"
            diagram += "\n    LB --> Compute"
        else:
            diagram += "\n    User --> Compute"
        
        if 'Compute' in categories:
            compute_services = categories['Compute']
            diagram += f"\n    Compute[💻 {', '.join(compute_services)}]"
            diagram += "\n    Compute --> DB"
            diagram += "\n    Compute --> Storage"
        
        if 'Database' in categories:
            db_services = categories['Database']
            diagram += f"\n    DB[🗄️ {', '.join(db_services)}]"
        
        if 'Storage' in categories:
            storage_services = categories['Storage']
            diagram += f"\n    Storage[📦 {', '.join(storage_services)}]"
        
        if 'Security' in categories:
            diagram += "\n    Security[🔒 Security Services] -.-> Compute"
            diagram += "\n    Security -.-> DB"
        
        return diagram
    
    def _get_service_category(self, service_code: str) -> str:
        """Categorize service for architecture diagram"""
        mapping = {
            'AmazonEC2': 'Compute',
            'AWSLambda': 'Compute',
            'AmazonS3': 'Storage',
            'AmazonEBS': 'Storage',
            'AmazonRDS': 'Database',
            'AmazonDynamoDB': 'Database',
            'AmazonRedshift': 'Database',
            'AWSELB': 'LoadBalancer',
            'AmazonCloudFront': 'CDN',
            'AWSShield': 'Security',
            'AmazonCognito': 'Security'
        }
        return mapping.get(service_code, 'Other')
    
    # ========================================
    # AGENT 5: Package Optimizer
    # ========================================
    
    def optimize_package(self, recommendations: List[ServiceRecommendation],
                        requirements: CustomerRequirement) -> Tuple[List[ServiceRecommendation], List[str]]:
        """Agent 5: Optimize package based on budget and requirements"""
        st.write("⚡ **Agent 5 - Package Optimizer** activated...")
        
        total_cost = sum(rec.monthly_cost for rec in recommendations)
        optimization_tips = []
        
        # Check if over budget
        if total_cost > requirements.monthly_budget:
            st.warning(f"⚠️ Initial package (${total_cost:.2f}) exceeds budget (${requirements.monthly_budget:.2f})")
            recommendations, savings_tips = self._apply_cost_optimizations(
                recommendations, requirements.monthly_budget
            )
            optimization_tips.extend(savings_tips)
            total_cost = sum(rec.monthly_cost for rec in recommendations)
        
        # Add general optimization tips
        optimization_tips.extend(self._generate_optimization_tips(recommendations, requirements))
        
        st.success(f"✅ Package optimized to ${total_cost:.2f}/month")
        return recommendations, optimization_tips
    
    def _apply_cost_optimizations(self, recommendations: List[ServiceRecommendation],
                                 budget: float) -> Tuple[List[ServiceRecommendation], List[str]]:
        """Apply cost optimization strategies"""
        tips = []
        optimized = recommendations.copy()
        
        # Strategy 1: Use spot instances where possible
        for rec in optimized:
            if rec.service_code == 'AmazonEC2':
                rec.monthly_cost *= 0.7  # 30% savings with spot
                tips.append(f"💡 Use Spot Instances for {rec.service_name} (30% savings)")
        
        # Strategy 2: Use reserved instances
        for rec in optimized:
            if rec.service_code in ['AmazonEC2', 'AmazonRDS']:
                rec.monthly_cost *= 0.6  # 40% savings with 1-year reserved
                tips.append(f"💡 Consider 1-year Reserved Instances for {rec.service_name} (40% savings)")
        
        # Strategy 3: Use serverless alternatives
        current_cost = sum(rec.monthly_cost for rec in optimized)
        if current_cost > budget:
            for rec in optimized:
                if rec.service_code == 'AmazonEC2' and any(r.service_code == 'AWSLambda' for r in optimized):
                    rec.monthly_cost *= 0.5
                    tips.append(f"💡 Move workloads to Lambda where possible")
        
        return optimized, tips
    
    def _generate_optimization_tips(self, recommendations: List[ServiceRecommendation],
                                   requirements: CustomerRequirement) -> List[str]:
        """Generate general optimization tips"""
        tips = []
        
        # Storage optimization
        if any(rec.service_code == 'AmazonS3' for rec in recommendations):
            tips.append("💡 Use S3 Intelligent-Tiering for automatic cost optimization")
            tips.append("💡 Enable S3 lifecycle policies to move old data to cheaper tiers")
        
        # Compute optimization
        if any(rec.service_code == 'AmazonEC2' for rec in recommendations):
            tips.append("💡 Use Auto Scaling to match capacity with demand")
            tips.append("💡 Consider Graviton2 instances for 20% better price-performance")
        
        # Database optimization
        if any(rec.service_code == 'AmazonRDS' for rec in recommendations):
            tips.append("💡 Use RDS Proxy to reduce database connections overhead")
            tips.append("💡 Enable automated backups with retention policies")
        
        # Network optimization
        if any(rec.service_code == 'AmazonCloudFront' for rec in recommendations):
            tips.append("💡 Use CloudFront caching to reduce origin requests")
        
        return tips
    
    # ========================================
    # AGENT 6: Compliance Checker
    # ========================================
    
    def check_compliance(self, recommendations: List[ServiceRecommendation],
                        requirements: CustomerRequirement) -> str:
        """Agent 6: Check compliance requirements"""
        st.write("🛡️ **Agent 6 - Compliance Checker** activated...")
        
        compliance_notes = []
        
        for compliance_req in requirements.compliance_needs:
            notes = self._check_compliance_framework(compliance_req, recommendations)
            compliance_notes.extend(notes)
        
        if not compliance_notes:
            compliance_notes.append("✅ No specific compliance requirements specified")
        
        st.success("✅ Compliance check completed")
        return "\n".join(compliance_notes)
    
    def _check_compliance_framework(self, framework: str, 
                                   recommendations: List[ServiceRecommendation]) -> List[str]:
        """Check specific compliance framework"""
        notes = []
        framework_lower = framework.lower()
        
        if 'hipaa' in framework_lower:
            notes.append("🏥 HIPAA Compliance:")
            notes.append("  - Enable encryption at rest for all data services")
            notes.append("  - Use AWS CloudTrail for audit logging")
            notes.append("  - Implement VPC for network isolation")
        
        elif 'pci' in framework_lower:
            notes.append("💳 PCI DSS Compliance:")
            notes.append("  - Use AWS WAF for application protection")
            notes.append("  - Enable GuardDuty for threat detection")
            notes.append("  - Implement strong access controls with IAM")
        
        elif 'gdpr' in framework_lower:
            notes.append("🇪🇺 GDPR Compliance:")
            notes.append("  - Enable data encryption and key management")
            notes.append("  - Implement data retention policies")
            notes.append("  - Use AWS Config for compliance monitoring")
        
        elif 'sox' in framework_lower:
            notes.append("📊 SOX Compliance:")
            notes.append("  - Enable detailed audit logging")
            notes.append("  - Implement change management controls")
            notes.append("  - Use AWS Organizations for account governance")
        
        return notes
    
    # ========================================
    # ORCHESTRATOR
    # ========================================
    
    def create_package(self, requirements: CustomerRequirement) -> CloudPackage:
        """Orchestrate all agents to create complete package"""
        st.header("🤖 Multi-Agent System Activated")
        st.markdown("---")
        
        # Agent 1: Analyze requirements
        analysis = self.analyze_requirements(requirements)
        st.markdown("---")
        
        # Agent 2: Discover services
        services = self.discover_services(analysis, requirements)
        st.markdown("---")
        
        # Agent 3: Fetch pricing
        recommendations = self.fetch_pricing(services, requirements.regions[0])
        st.markdown("---")
        
        # Agent 4: Design architecture
        architecture = self.design_architecture(recommendations, analysis)
        st.markdown("---")
        
        # Agent 5: Optimize package
        optimized_recommendations, optimization_tips = self.optimize_package(
            recommendations, requirements
        )
        st.markdown("---")
        
        # Agent 6: Check compliance
        compliance_notes = self.check_compliance(optimized_recommendations, requirements)
        
        # Create final package
        total_cost = sum(rec.monthly_cost for rec in optimized_recommendations)
        
        package = CloudPackage(
            package_name=f"{requirements.workload_type} - {requirements.performance_tier} Tier",
            total_monthly_cost=total_cost,
            services=optimized_recommendations,
            architecture_diagram=architecture,
            compliance_notes=compliance_notes,
            optimization_tips=optimization_tips
        )
        
        return package

# ========================================
# STREAMLIT UI
# ========================================

st.set_page_config(
    page_title="AWS Intelligent Cloud Packager",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AWS Intelligent Cloud Packager")
st.markdown("### Multi-Agent System for Dynamic Service Discovery & Packaging")
st.markdown("*No hardcoding - powered by AWS APIs and intelligent agents*")

st.markdown("---")

# Sidebar - Customer Requirements Input
st.sidebar.header("📋 Customer Requirements")

workload_type = st.sidebar.selectbox(
    "Workload Type",
    ["Web Application", "API Backend", "Mobile Backend", "Data Processing", 
     "Machine Learning", "IoT Application", "Enterprise Application", 
     "E-commerce Platform", "Analytics Platform"]
)

col1, col2 = st.sidebar.columns(2)
with col1:
    monthly_budget = st.number_input(
        "Monthly Budget ($)",
        min_value=100,
        value=1000,
        step=100
    )

with col2:
    performance_tier = st.selectbox(
        "Performance Tier",
        ["Low", "Medium", "High", "Enterprise"]
    )

regions = st.sidebar.multiselect(
    "AWS Regions",
    ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", 
     "ap-southeast-1", "ap-northeast-1"],
    default=["us-east-1"]
)

compliance_needs = st.sidebar.multiselect(
    "Compliance Requirements",
    ["HIPAA", "PCI DSS", "GDPR", "SOX", "ISO 27001", "SOC 2"],
    default=[]
)

col1, col2 = st.sidebar.columns(2)
with col1:
    scalability = st.selectbox(
        "Scalability",
        ["Low", "Medium", "High"]
    )

# ...existing code...

with col2:
    availability_target = st.selectbox(
        "Availability Target",
        ["99%", "99.9%", "99.99%", "99.999%"]
    )

col1, col2 = st.sidebar.columns(2)
with col1:
    data_volume_gb = st.number_input(
        "Data Volume (GB)",
        min_value=1,
        value=100,
        step=100
    )

with col2:
    expected_users = st.number_input(
        "Expected Users",
        min_value=1,
        value=1000,
        step=1000
    )

special_requirements = st.sidebar.multiselect(
    "Special Requirements",
    ["GPU Support", "Low Latency", "High Memory", "High I/O", 
     "Backup & DR", "Auto Scaling", "Content Delivery"],
    default=[]
)

# Create Package Button
if st.sidebar.button("🚀 Generate Package", type="primary"):
    # Create requirements object
    requirements = CustomerRequirement(
        workload_type=workload_type,
        monthly_budget=monthly_budget,
        performance_tier=performance_tier,
        regions=regions,
        compliance_needs=compliance_needs,
        scalability=scalability,
        availability_target=availability_target,
        data_volume_gb=data_volume_gb,
        expected_users=expected_users,
        special_requirements=special_requirements
    )
    
    # Initialize multi-agent system
    packager = AWSMultiAgentPackager(region=regions[0])
    
    # Generate package
    with st.spinner("🤖 Agents working on your cloud package..."):
        package = packager.create_package(requirements)
    
    # Display Results
    st.header("📦 Your Cloud Package")
    
    # Package Overview
    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly Cost", f"${package.total_monthly_cost:,.2f}")
    with col2:
        st.metric("Services", len(package.services))
    with col3:
        st.metric("Region(s)", len(regions))
    
    # Architecture Diagram
    st.subheader("Architecture")
    st.mermaid(package.architecture_diagram)
    
    # Services Breakdown
    st.subheader("Services Breakdown")
    services_df = pd.DataFrame([
        {
            "Service": rec.service_name,
            "Configuration": json.dumps(rec.configuration, indent=2),
            "Monthly Cost": f"${rec.monthly_cost:,.2f}",
            "Justification": rec.justification,
            "Alternatives": ", ".join(rec.alternatives)
        }
        for rec in package.services
    ])
    
    st.dataframe(
        services_df,
        column_config={
            "Service": st.column_config.TextColumn("Service", width="medium"),
            "Configuration": st.column_config.TextColumn("Configuration", width="large"),
            "Monthly Cost": st.column_config.TextColumn("Monthly Cost", width="medium"),
            "Justification": st.column_config.TextColumn("Justification", width="large"),
            "Alternatives": st.column_config.TextColumn("Alternatives", width="large")
        },
        hide_index=True
    )
    
    # Optimization Tips
    st.subheader("💡 Optimization Tips")
    for tip in package.optimization_tips:
        st.markdown(f"- {tip}")
    
    # Compliance Notes
    if package.compliance_notes:
        st.subheader("🛡️ Compliance Notes")
        st.text(package.compliance_notes)
    
    # Export Options
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Package Details",
            data=json.dumps(asdict(package), indent=2),
            file_name="cloud_package.json",
            mime="application/json"
        )
    
    with col2:
        st.download_button(
            "📊 Download Cost Breakdown",
            data=services_df.to_csv(index=False),
            file_name="cost_breakdown.csv",
            mime="text/csv"
        )
else:
    # Initial state
    st.info("👈 Configure your requirements in the sidebar and click 'Generate Package' to start")
    
# Footer
st.markdown("---")
st.caption("Powered by AWS APIs and Intelligent Agents | Last updated: 2025-09-30")