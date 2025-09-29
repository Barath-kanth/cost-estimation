import json
import pandas as pd
import streamlit as st
from typing import Optional

# ---------- Fallback Pricing Data ----------
# Pricing data for common instances (US East N. Virginia baseline)
EC2_PRICING = {
    # T3 instances - Burstable
    "t3.nano": {"Linux": 0.0052, "Windows": 0.0104, "RHEL": 0.0652, "SUSE": 0.0252},
    "t3.micro": {"Linux": 0.0104, "Windows": 0.0208, "RHEL": 0.0704, "SUSE": 0.0304},
    "t3.small": {"Linux": 0.0208, "Windows": 0.0416, "RHEL": 0.0808, "SUSE": 0.0408},
    "t3.medium": {"Linux": 0.0416, "Windows": 0.0832, "RHEL": 0.1016, "SUSE": 0.0616},
    "t3.large": {"Linux": 0.0832, "Windows": 0.1664, "RHEL": 0.1432, "SUSE": 0.1032},
    "t3.xlarge": {"Linux": 0.1664, "Windows": 0.3328, "RHEL": 0.2264, "SUSE": 0.1864},
    "t3.2xlarge": {"Linux": 0.3328, "Windows": 0.6656, "RHEL": 0.3928, "SUSE": 0.3528},
    
    # T4g instances - Graviton
    "t4g.nano": {"Linux": 0.0042, "Windows": 0.0084, "RHEL": 0.0642, "SUSE": 0.0242},
    "t4g.micro": {"Linux": 0.0084, "Windows": 0.0168, "RHEL": 0.0684, "SUSE": 0.0284},
    "t4g.small": {"Linux": 0.0168, "Windows": 0.0336, "RHEL": 0.0768, "SUSE": 0.0368},
    "t4g.medium": {"Linux": 0.0336, "Windows": 0.0672, "RHEL": 0.0936, "SUSE": 0.0536},
    "t4g.large": {"Linux": 0.0672, "Windows": 0.1344, "RHEL": 0.1272, "SUSE": 0.0872},
    "t4g.xlarge": {"Linux": 0.1344, "Windows": 0.2688, "RHEL": 0.1944, "SUSE": 0.1544},
    "t4g.2xlarge": {"Linux": 0.2688, "Windows": 0.5376, "RHEL": 0.3288, "SUSE": 0.2888},
    
    # M5 instances - General Purpose
    "m5.large": {"Linux": 0.096, "Windows": 0.192, "RHEL": 0.156, "SUSE": 0.116},
    "m5.xlarge": {"Linux": 0.192, "Windows": 0.384, "RHEL": 0.252, "SUSE": 0.212},
    "m5.2xlarge": {"Linux": 0.384, "Windows": 0.768, "RHEL": 0.444, "SUSE": 0.404},
    "m5.4xlarge": {"Linux": 0.768, "Windows": 1.536, "RHEL": 0.828, "SUSE": 0.788},
    "m5.8xlarge": {"Linux": 1.536, "Windows": 3.072, "RHEL": 1.596, "SUSE": 1.556},
    "m5.12xlarge": {"Linux": 2.304, "Windows": 4.608, "RHEL": 2.364, "SUSE": 2.324},
    "m5.16xlarge": {"Linux": 3.072, "Windows": 6.144, "RHEL": 3.132, "SUSE": 3.092},
    "m5.24xlarge": {"Linux": 4.608, "Windows": 9.216, "RHEL": 4.668, "SUSE": 4.628},
    
    # M6i instances
    "m6i.large": {"Linux": 0.096, "Windows": 0.192, "RHEL": 0.156, "SUSE": 0.116},
    "m6i.xlarge": {"Linux": 0.192, "Windows": 0.384, "RHEL": 0.252, "SUSE": 0.212},
    "m6i.2xlarge": {"Linux": 0.384, "Windows": 0.768, "RHEL": 0.444, "SUSE": 0.404},
    "m6i.4xlarge": {"Linux": 0.768, "Windows": 1.536, "RHEL": 0.828, "SUSE": 0.788},
    "m6i.8xlarge": {"Linux": 1.536, "Windows": 3.072, "RHEL": 1.596, "SUSE": 1.556},
    "m6i.12xlarge": {"Linux": 2.304, "Windows": 4.608, "RHEL": 2.364, "SUSE": 2.324},
    "m6i.16xlarge": {"Linux": 3.072, "Windows": 6.144, "RHEL": 3.132, "SUSE": 3.092},
    "m6i.24xlarge": {"Linux": 4.608, "Windows": 9.216, "RHEL": 4.668, "SUSE": 4.628},
    "m6i.32xlarge": {"Linux": 6.144, "Windows": 12.288, "RHEL": 6.204, "SUSE": 6.164},
    
    # M6g instances - Graviton
    "m6g.medium": {"Linux": 0.0385, "Windows": 0.077, "RHEL": 0.0985, "SUSE": 0.0585},
    "m6g.large": {"Linux": 0.077, "Windows": 0.154, "RHEL": 0.137, "SUSE": 0.097},
    "m6g.xlarge": {"Linux": 0.154, "Windows": 0.308, "RHEL": 0.214, "SUSE": 0.174},
    "m6g.2xlarge": {"Linux": 0.308, "Windows": 0.616, "RHEL": 0.368, "SUSE": 0.328},
    "m6g.4xlarge": {"Linux": 0.616, "Windows": 1.232, "RHEL": 0.676, "SUSE": 0.636},
    "m6g.8xlarge": {"Linux": 1.232, "Windows": 2.464, "RHEL": 1.292, "SUSE": 1.252},
    "m6g.12xlarge": {"Linux": 1.848, "Windows": 3.696, "RHEL": 1.908, "SUSE": 1.868},
    "m6g.16xlarge": {"Linux": 2.464, "Windows": 4.928, "RHEL": 2.524, "SUSE": 2.484},
    
    # C5 instances - Compute Optimized
    "c5.large": {"Linux": 0.085, "Windows": 0.17, "RHEL": 0.145, "SUSE": 0.105},
    "c5.xlarge": {"Linux": 0.17, "Windows": 0.34, "RHEL": 0.23, "SUSE": 0.19},
    "c5.2xlarge": {"Linux": 0.34, "Windows": 0.68, "RHEL": 0.40, "SUSE": 0.36},
    "c5.4xlarge": {"Linux": 0.68, "Windows": 1.36, "RHEL": 0.74, "SUSE": 0.70},
    "c5.9xlarge": {"Linux": 1.53, "Windows": 3.06, "RHEL": 1.59, "SUSE": 1.55},
    "c5.12xlarge": {"Linux": 2.04, "Windows": 4.08, "RHEL": 2.10, "SUSE": 2.06},
    "c5.18xlarge": {"Linux": 3.06, "Windows": 6.12, "RHEL": 3.12, "SUSE": 3.08},
    "c5.24xlarge": {"Linux": 4.08, "Windows": 8.16, "RHEL": 4.14, "SUSE": 4.10},
    
    # C6g instances - Graviton Compute
    "c6g.medium": {"Linux": 0.034, "Windows": 0.068, "RHEL": 0.094, "SUSE": 0.054},
    "c6g.large": {"Linux": 0.068, "Windows": 0.136, "RHEL": 0.128, "SUSE": 0.088},
    "c6g.xlarge": {"Linux": 0.136, "Windows": 0.272, "RHEL": 0.196, "SUSE": 0.156},
    "c6g.2xlarge": {"Linux": 0.272, "Windows": 0.544, "RHEL": 0.332, "SUSE": 0.292},
    "c6g.4xlarge": {"Linux": 0.544, "Windows": 1.088, "RHEL": 0.604, "SUSE": 0.564},
    "c6g.8xlarge": {"Linux": 1.088, "Windows": 2.176, "RHEL": 1.148, "SUSE": 1.108},
    "c6g.12xlarge": {"Linux": 1.632, "Windows": 3.264, "RHEL": 1.692, "SUSE": 1.652},
    "c6g.16xlarge": {"Linux": 2.176, "Windows": 4.352, "RHEL": 2.236, "SUSE": 2.196},
    
    # R5 instances - Memory Optimized
    "r5.large": {"Linux": 0.126, "Windows": 0.252, "RHEL": 0.186, "SUSE": 0.146},
    "r5.xlarge": {"Linux": 0.252, "Windows": 0.504, "RHEL": 0.312, "SUSE": 0.272},
    "r5.2xlarge": {"Linux": 0.504, "Windows": 1.008, "RHEL": 0.564, "SUSE": 0.524},
    "r5.4xlarge": {"Linux": 1.008, "Windows": 2.016, "RHEL": 1.068, "SUSE": 1.028},
    "r5.8xlarge": {"Linux": 2.016, "Windows": 4.032, "RHEL": 2.076, "SUSE": 2.036},
    "r5.12xlarge": {"Linux": 3.024, "Windows": 6.048, "RHEL": 3.084, "SUSE": 3.044},
    "r5.16xlarge": {"Linux": 4.032, "Windows": 8.064, "RHEL": 4.092, "SUSE": 4.052},
    "r5.24xlarge": {"Linux": 6.048, "Windows": 12.096, "RHEL": 6.108, "SUSE": 6.068},
    
    # R6g instances - Graviton Memory
    "r6g.medium": {"Linux": 0.0504, "Windows": 0.1008, "RHEL": 0.1104, "SUSE": 0.0704},
    "r6g.large": {"Linux": 0.1008, "Windows": 0.2016, "RHEL": 0.1608, "SUSE": 0.1208},
    "r6g.xlarge": {"Linux": 0.2016, "Windows": 0.4032, "RHEL": 0.2616, "SUSE": 0.2216},
    "r6g.2xlarge": {"Linux": 0.4032, "Windows": 0.8064, "RHEL": 0.4632, "SUSE": 0.4232},
    "r6g.4xlarge": {"Linux": 0.8064, "Windows": 1.6128, "RHEL": 0.8664, "SUSE": 0.8264},
    "r6g.8xlarge": {"Linux": 1.6128, "Windows": 3.2256, "RHEL": 1.6728, "SUSE": 1.6328},
    "r6g.12xlarge": {"Linux": 2.4192, "Windows": 4.8384, "RHEL": 2.4792, "SUSE": 2.4392},
    "r6g.16xlarge": {"Linux": 3.2256, "Windows": 6.4512, "RHEL": 3.2856, "SUSE": 3.2456},
}

# Regional price multipliers (relative to us-east-1)
REGION_MULTIPLIERS = {
    "US East (N. Virginia)": 1.00,
    "US East (Ohio)": 1.00,
    "US West (Oregon)": 1.00,
    "US West (N. California)": 1.05,
    "Canada (Central)": 1.04,
    "Europe (Ireland)": 1.03,
    "Europe (London)": 1.04,
    "Europe (Frankfurt)": 1.05,
    "Europe (Paris)": 1.05,
    "Europe (Stockholm)": 1.03,
    "Asia Pacific (Tokyo)": 1.08,
    "Asia Pacific (Seoul)": 1.06,
    "Asia Pacific (Singapore)": 1.08,
    "Asia Pacific (Sydney)": 1.10,
    "Asia Pacific (Mumbai)": 1.06,
    "South America (São Paulo)": 1.20,
    "Middle East (Bahrain)": 1.10,
}

# Bedrock pricing (per 1000 tokens)
BEDROCK_PRICING = {
    "Claude 3.5 Sonnet": {"input": 0.003, "output": 0.015},
    "Claude 3.5 Haiku": {"input": 0.0008, "output": 0.004},
    "Claude 3 Opus": {"input": 0.015, "output": 0.075},
    "Claude 3 Sonnet": {"input": 0.003, "output": 0.015},
    "Claude 3 Haiku": {"input": 0.00025, "output": 0.00125},
    "Titan Text Express": {"input": 0.0008, "output": 0.0016},
    "Titan Text Lite": {"input": 0.0003, "output": 0.0004},
    "Titan Embeddings G1": {"input": 0.0001, "output": 0.0},
    "Titan Multimodal Embeddings": {"input": 0.0008, "output": 0.0},
    "Llama 3.1 405B": {"input": 0.00532, "output": 0.016},
    "Llama 3.1 70B": {"input": 0.00099, "output": 0.00099},
    "Llama 3.1 8B": {"input": 0.0003, "output": 0.0006},
    "Llama 2 70B": {"input": 0.00195, "output": 0.00256},
    "Llama 2 13B": {"input": 0.00075, "output": 0.001},
    "Mistral Large": {"input": 0.008, "output": 0.024},
    "Mistral 7B": {"input": 0.00015, "output": 0.0002},
    "Cohere Command R+": {"input": 0.003, "output": 0.015},
    "Cohere Command R": {"input": 0.0005, "output": 0.0015},
    "Cohere Command": {"input": 0.0015, "output": 0.002},
    "Cohere Embed": {"input": 0.0001, "output": 0.0}
}

# ---------- Helper Functions ----------
def currency(v: float) -> str:
    """Format currency"""
    if v == 0:
        return "$0.00"
    if v < 0.01:
        return f"${v:.6f}".rstrip("0").rstrip(".")
    return f"${v:,.2f}"

def compute_line(price_per_unit: float, quantity: float) -> float:
    """Calculate line item cost"""
    return float(price_per_unit) * float(quantity)

def get_ec2_price(instance_type: str, os: str, region: str) -> Optional[float]:
    """Get EC2 price with regional adjustment"""
    base_price = EC2_PRICING.get(instance_type, {}).get(os)
    if base_price is None:
        return None
    
    multiplier = REGION_MULTIPLIERS.get(region, 1.0)
    return base_price * multiplier

# ---------- Streamlit Configuration ----------
st.set_page_config(
    page_title="AWS Cost Estimator - Dynamic Pricing",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 AWS Cost Estimator - Dynamic Pricing")
st.markdown("*Comprehensive pricing calculator with offline pricing data*")

# ---------- Sidebar Configuration ----------
st.sidebar.header("🌍 Configuration")
region = st.sidebar.selectbox(
    "AWS Region",
    list(REGION_MULTIPLIERS.keys()),
    index=6  # Default to London
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Services")
include_ec2 = st.sidebar.checkbox("💻 EC2 Instances", value=True)
include_bedrock = st.sidebar.checkbox("🤖 Amazon Bedrock", value=True)

# ---------- Results Storage ----------
rows = []

# ========================================
# EC2 INSTANCES - COMPREHENSIVE
# ========================================
if include_ec2:
    st.header("💻 EC2 Instances")
    st.markdown("Configure your EC2 instances with detailed options")
    
    # Row 1: Basic Configuration
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ec2_instance_type = st.selectbox(
            "Instance Type",
            sorted(EC2_PRICING.keys()),
            index=list(EC2_PRICING.keys()).index("t3.medium")
        )
    
    with col2:
        ec2_os = st.selectbox(
            "Operating System",
            ["Linux", "Windows", "RHEL", "SUSE"],
            index=0
        )
    
    with col3:
        ec2_quantity = st.number_input(
            "Instance Count",
            min_value=1,
            value=1,
            max_value=1000
        )
    
    with col4:
        ec2_hours_per_month = st.number_input(
            "Hours/Month",
            min_value=1,
            value=730,
            max_value=744,
            help="730 hours = 24/7 operation"
        )
    
    # Row 2: Advanced Options
    st.markdown("#### Advanced Options")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ec2_tenancy = st.selectbox(
            "Tenancy",
            ["Shared", "Dedicated", "Host"],
            index=0,
            help="Shared = Default, Dedicated = Dedicated Instance, Host = Dedicated Host"
        )
    
    with col2:
        ec2_pricing_model = st.selectbox(
            "Pricing Model",
            ["On-Demand", "Reserved (1yr)", "Reserved (3yr)", "Spot"],
            index=0
        )
    
    with col3:
        ec2_storage_type = st.selectbox(
            "Root Volume Type",
            ["gp3", "gp2", "io2", "io1", "st1", "sc1"],
            index=0
        )
    
    with col4:
        ec2_storage_gb = st.number_input(
            "Root Volume (GB)",
            min_value=8,
            value=30,
            max_value=16384
        )
    
    # Row 3: Network & Data Transfer
    st.markdown("#### Network & Data Transfer")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ec2_data_transfer_out_gb = st.number_input(
            "Data Transfer Out (GB/month)",
            min_value=0.0,
            value=0.0,
            help="Data transferred out to internet"
        )
    
    with col2:
        ec2_ebs_snapshot_gb = st.number_input(
            "EBS Snapshots (GB)",
            min_value=0.0,
            value=0.0,
            help="EBS snapshot storage"
        )
    
    with col3:
        ec2_elastic_ip = st.checkbox(
            "Elastic IP (unused)",
            value=False,
            help="Additional charge for unused Elastic IPs"
        )
    
    # Get EC2 Pricing
    st.markdown("---")
    ec2_price_per_hour = get_ec2_price(ec2_instance_type, ec2_os, region)
    
    if ec2_price_per_hour is None:
        st.warning("⚠️ Price not available for this configuration. Please enter manually.")
        ec2_price_per_hour = st.number_input(
            "EC2 Price per Hour (USD)",
            min_value=0.0,
            value=0.05,
            format="%.6f"
        )
    else:
        st.success(f"✅ EC2 Instance Price: **{currency(ec2_price_per_hour)}/hour** (Base price adjusted for {region})")
    
    # Calculate pricing adjustments
    pricing_multiplier = 1.0
    if ec2_pricing_model == "Reserved (1yr)":
        pricing_multiplier = 0.60  # ~40% savings
        st.info("💡 Reserved 1yr pricing: ~40% discount applied")
    elif ec2_pricing_model == "Reserved (3yr)":
        pricing_multiplier = 0.40  # ~60% savings
        st.info("💡 Reserved 3yr pricing: ~60% discount applied")
    elif ec2_pricing_model == "Spot":
        pricing_multiplier = 0.30  # ~70% savings
        st.info("💡 Spot pricing: ~70% discount applied (varies by availability)")
    
    # Tenancy adjustment
    if ec2_tenancy == "Dedicated":
        pricing_multiplier *= 1.1  # 10% premium
    elif ec2_tenancy == "Host":
        st.warning("⚠️ Dedicated Host pricing varies significantly. Additional costs may apply.")
    
    adjusted_price = ec2_price_per_hour * pricing_multiplier
    
    # Calculate costs
    ec2_compute_cost = compute_line(adjusted_price, ec2_hours_per_month * ec2_quantity)
    
    # EBS Storage cost
    storage_prices = {
        "gp3": 0.08,
        "gp2": 0.10,
        "io2": 0.125,
        "io1": 0.125,
        "st1": 0.045,
        "sc1": 0.015
    }
    ec2_storage_cost = ec2_storage_gb * storage_prices.get(ec2_storage_type, 0.08) * ec2_quantity
    
    # Data transfer cost (simplified - first 10TB tier)
    ec2_data_transfer_cost = 0
    if ec2_data_transfer_out_gb > 0:
        if ec2_data_transfer_out_gb <= 10240:  # First 10TB
            ec2_data_transfer_cost = max(0, ec2_data_transfer_out_gb - 100) * 0.09  # First 100GB free
        else:
            ec2_data_transfer_cost = (10140 * 0.09) + ((ec2_data_transfer_out_gb - 10240) * 0.085)
    
    # Snapshot cost
    ec2_snapshot_cost = ec2_ebs_snapshot_gb * 0.05
    
    # Elastic IP cost
    ec2_eip_cost = 0.005 * 730 * ec2_quantity if ec2_elastic_ip else 0
    
    # Total EC2 cost
    ec2_total_cost = (ec2_compute_cost + ec2_storage_cost + 
                      ec2_data_transfer_cost + ec2_snapshot_cost + ec2_eip_cost)
    
    # Display breakdown
    st.markdown("### 💰 EC2 Cost Breakdown")
    breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
    
    with breakdown_col1:
        st.metric("Compute Cost", currency(ec2_compute_cost))
        st.metric("Storage Cost", currency(ec2_storage_cost))
    
    with breakdown_col2:
        st.metric("Data Transfer", currency(ec2_data_transfer_cost))
        st.metric("Snapshots", currency(ec2_snapshot_cost))
    
    with breakdown_col3:
        st.metric("Elastic IP", currency(ec2_eip_cost))
        st.metric("**TOTAL EC2**", f"**{currency(ec2_total_cost)}**")
    
    # Add to results
    rows.append({
        "Category": "Compute",
        "Service": "EC2",
        "Type": f"{ec2_instance_type} ({ec2_os}) - {ec2_pricing_model}",
        "Unit": "hour",
        "Unit Price": adjusted_price,
        "Quantity": ec2_hours_per_month * ec2_quantity,
        "Monthly Cost": ec2_total_cost
    })

# ========================================
# AMAZON BEDROCK - COMPREHENSIVE
# ========================================
if include_bedrock:
    st.header("🤖 Amazon Bedrock")
    st.markdown("Configure your generative AI workload")
    
    # Row 1: Model Selection
    col1, col2 = st.columns(2)
    
    with col1:
        bedrock_model = st.selectbox(
            "Model",
            list(BEDROCK_PRICING.keys()),
            index=0
        )
    
    with col2:
        bedrock_usage_pattern = st.selectbox(
            "Usage Pattern",
            ["Custom", "Light (Dev/Test)", "Medium (Production)", "Heavy (Enterprise)"],
            index=0
        )
    
    # Set defaults based on usage pattern
    if bedrock_usage_pattern == "Light (Dev/Test)":
        default_input = 100000
        default_output = 50000
    elif bedrock_usage_pattern == "Medium (Production)":
        default_input = 1000000
        default_output = 500000
    elif bedrock_usage_pattern == "Heavy (Enterprise)":
        default_input = 10000000
        default_output = 5000000
    else:
        default_input = 100000
        default_output = 50000
    
    # Row 2: Token Configuration
    st.markdown("#### Token Usage (per month)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bedrock_input_tokens = st.number_input(
            "Input Tokens",
            min_value=0,
            value=default_input,
            step=10000,
            help="Number of tokens in requests"
        )
    
    with col2:
        bedrock_output_tokens = st.number_input(
            "Output Tokens",
            min_value=0,
            value=default_output,
            step=10000,
            help="Number of tokens in responses"
        )
    
    with col3:
        st.markdown("**Token Estimates**")
        st.caption(f"Input: ~{bedrock_input_tokens:,} tokens")
        st.caption(f"Output: ~{bedrock_output_tokens:,} tokens")
        st.caption(f"Total: ~{bedrock_input_tokens + bedrock_output_tokens:,} tokens")
    
    # Row 3: Advanced Options
    st.markdown("#### Advanced Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bedrock_model_customization = st.checkbox(
            "Model Customization",
            value=False,
            help="Additional cost for custom model training"
        )
        
        if bedrock_model_customization:
            bedrock_training_tokens = st.number_input(
                "Training Tokens (millions)",
                min_value=0.0,
                value=1.0,
                step=0.1
            )
    
    with col2:
        bedrock_provisioned_throughput = st.checkbox(
            "Provisioned Throughput",
            value=False,
            help="Reserve model capacity for consistent performance"
        )
        
        if bedrock_provisioned_throughput:
            bedrock_model_units = st.number_input(
                "Model Units",
                min_value=1,
                value=1,
                help="Each unit provides guaranteed throughput"
            )
    
    with col3:
        bedrock_guardrails = st.checkbox(
            "Guardrails",
            value=False,
            help="Content filtering and safety guardrails"
        )
        
        if bedrock_guardrails:
            bedrock_guardrail_units = st.number_input(
                "Guardrail Units (1000s)",
                min_value=0,
                value=100,
                help="Number of guardrail evaluations"
            )
    
    # Get pricing
    pricing = BEDROCK_PRICING.get(bedrock_model, {"input": 0.001, "output": 0.002})
    
    # Calculate costs
    bedrock_input_cost = (bedrock_input_tokens / 1000) * pricing["input"]
    bedrock_output_cost = (bedrock_output_tokens / 1000) * pricing["output"]
    
    # Model customization cost
        # Calculate customization costs
    bedrock_customization_cost = 0
    if bedrock_model_customization:
        customization_rate = 0.0004  # $0.0004 per 1000 training tokens
        bedrock_customization_cost = bedrock_training_tokens * 1000000 * customization_rate

    # Provisioned throughput cost
    bedrock_throughput_cost = 0
    if bedrock_provisioned_throughput:
        throughput_rate = 10.0  # $10 per model unit per day
        bedrock_throughput_cost = bedrock_model_units * throughput_rate * 30

    # Guardrails cost
    bedrock_guardrails_cost = 0
    if bedrock_guardrails:
        guardrails_rate = 0.001  # $0.001 per 1000 evaluations
        bedrock_guardrails_cost = (bedrock_guardrail_units * 1000 * guardrails_rate)

    # Total Bedrock cost
    bedrock_total_cost = (
        bedrock_input_cost + 
        bedrock_output_cost + 
        bedrock_customization_cost + 
        bedrock_throughput_cost + 
        bedrock_guardrails_cost
    )

    # Display breakdown
    st.markdown("### 💰 Bedrock Cost Breakdown")
    breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)

    with breakdown_col1:
        st.metric("Input Cost", currency(bedrock_input_cost))
        st.metric("Output Cost", currency(bedrock_output_cost))

    with breakdown_col2:
        st.metric("Customization", currency(bedrock_customization_cost))
        st.metric("Throughput", currency(bedrock_throughput_cost))

    with breakdown_col3:
        st.metric("Guardrails", currency(bedrock_guardrails_cost))
        st.metric("**TOTAL BEDROCK**", f"**{currency(bedrock_total_cost)}**")

    # Add to results
    rows.append({
        "Category": "AI/ML",
        "Service": "Bedrock",
        "Type": bedrock_model,
        "Unit": "1000 tokens",
        "Unit Price": f"In: {currency(pricing['input'])}, Out: {currency(pricing['output'])}",
        "Quantity": f"{bedrock_input_tokens/1000:.1f}k in + {bedrock_output_tokens/1000:.1f}k out",
        "Monthly Cost": bedrock_total_cost
    })

# ========================================
# RESULTS & SUMMARY
# ========================================
st.markdown("---")

if len(rows) == 0:
    st.info("👆 Select services from the sidebar to begin your estimate.")
else:
    # Create summary DataFrame
    df = pd.DataFrame(rows)
    
    # Display total cost
    total_cost = df["Monthly Cost"].sum()
    st.metric("💰 Total Monthly Cost", f"**{currency(total_cost)}**")
    
    # Convert numeric columns to strings for display
    display_df = df.copy()
    display_df["Monthly Cost"] = display_df["Monthly Cost"].apply(currency)
    
    # Display detailed breakdown
    st.markdown("### Detailed Breakdown")
    st.dataframe(
        display_df,
        column_config={
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Service": st.column_config.TextColumn("Service", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="large"),
            "Unit": st.column_config.TextColumn("Unit", width="medium"),
            "Unit Price": st.column_config.TextColumn("Unit Price", width="medium"),
            "Quantity": st.column_config.TextColumn("Quantity", width="medium"),
            "Monthly Cost": st.column_config.TextColumn("Monthly Cost", width="medium"),
        },
        hide_index=True
    )

# Footer
st.markdown("---")
st.caption("💡 **Note**: Prices are estimates based on standard pricing. Actual costs may vary based on usage patterns, commitments, and other factors.")
st.caption(f"🌍 Region: {region} | 📅 Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d')}")