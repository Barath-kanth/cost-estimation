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
        """Get configuration summary for service labels"""
        if service == "Amazon EC2" and config:
            instance_type = config.get('instance_type', 't3.micro')
            instance_count = config.get('instance_count', 1)
            return f"{instance_count}x {instance_type}"
        elif service == "Amazon RDS" and config:
            instance_type = config.get('instance_type', 'db.t3.micro')
            engine = config.get('engine', 'PostgreSQL')
            return f"{engine}\\n{instance_type}"
        elif service == "Amazon S3" and config:
            storage_gb = config.get('storage_gb', 100)
            return f"{storage_gb}GB"
        elif service == "AWS Lambda" and config:
            memory = config.get('memory_mb', 128)
            return f"{memory}MB"
        elif service == "Amazon ECS" and config:
            cluster_type = config.get('cluster_type', 'Fargate')
            return f"{cluster_type}"
        return ""

def render_service_configuration(service_name: str):
    """Render configuration UI for each service"""
    st.subheader(f"⚙️ {service_name} Configuration")
    
    if service_name == "Amazon EC2":
        col1, col2 = st.columns(2)
        with col1:
            instance_type = st.selectbox(
                "Instance Type",
                ["t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", 
                 "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge",
                 "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge"],
                key=f"ec2_instance_type_{service_name}"
            )
        with col2:
            instance_count = st.number_input("Instance Count", min_value=1, max_value=100, value=1, key=f"ec2_count_{service_name}")
        
        col3, col4 = st.columns(2)
        with col3:
            operating_hours = st.selectbox(
                "Operating Hours",
                ["24/7", "Business Hours", "Custom"],
                key=f"ec2_hours_{service_name}"
            )
        with col4:
            if operating_hours == "Custom":
                daily_hours = st.number_input("Hours per Day", min_value=1, max_value=24, value=8, key=f"ec2_custom_hours_{service_name}")
            else:
                daily_hours = 24 if operating_hours == "24/7" else 12
        
        return {
            "instance_type": instance_type,
            "instance_count": instance_count,
            "operating_hours": operating_hours,
            "daily_hours": daily_hours
        }
    
    elif service_name == "Amazon RDS":
        col1, col2 = st.columns(2)
        with col1:
            instance_type = st.selectbox(
                "Instance Type",
                ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
                 "db.m5.large", "db.m5.xlarge", "db.m5.2xlarge", "db.m5.4xlarge",
                 "db.r5.large", "db.r5.xlarge", "db.r5.2xlarge", "db.r5.4xlarge"],
                key=f"rds_instance_type_{service_name}"
            )
        with col2:
            engine = st.selectbox(
                "Database Engine",
                ["PostgreSQL", "MySQL", "MariaDB", "Aurora MySQL", "Aurora PostgreSQL", "Oracle", "SQL Server"],
                key=f"rds_engine_{service_name}"
            )
        
        storage_gb = st.number_input("Storage (GB)", min_value=20, max_value=10000, value=100, key=f"rds_storage_{service_name}")
        
        return {
            "instance_type": instance_type,
            "engine": engine,
            "storage_gb": storage_gb
        }
    
    elif service_name == "Amazon S3":
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=100000, value=100, key=f"s3_storage_{service_name}")
        
        storage_class = st.selectbox(
            "Storage Class",
            ["Standard", "Intelligent-Tiering", "Standard-IA", "One Zone-IA", "Glacier", "Glacier Deep Archive"],
            key=f"s3_class_{service_name}"
        )
        
        data_transfer_gb = st.number_input("Monthly Data Transfer (GB)", min_value=0, max_value=10000, value=100, key=f"s3_transfer_{service_name}")
        
        return {
            "storage_gb": storage_gb,
            "storage_class": storage_class,
            "data_transfer_gb": data_transfer_gb
        }
    
    elif service_name == "AWS Lambda":
        col1, col2 = st.columns(2)
        with col1:
            memory_mb = st.selectbox(
                "Memory (MB)",
                [128, 256, 512, 1024, 2048, 3008],
                index=0,
                key=f"lambda_memory_{service_name}"
            )
        with col2:
            duration_ms = st.number_input("Average Duration (ms)", min_value=100, max_value=30000, value=1000, key=f"lambda_duration_{service_name}")
        
        monthly_requests = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"lambda_requests_{service_name}")
        
        return {
            "memory_mb": memory_mb,
            "duration_ms": duration_ms,
            "monthly_requests": monthly_requests
        }
    
    elif service_name == "Amazon ECS":
        cluster_type = st.selectbox(
            "Cluster Type",
            ["Fargate", "EC2"],
            key=f"ecs_type_{service_name}"
        )
        
        if cluster_type == "Fargate":
            col1, col2 = st.columns(2)
            with col1:
                cpu_units = st.selectbox("CPU Units", ["0.25 vCPU", "0.5 vCPU", "1 vCPU", "2 vCPU", "4 vCPU"], key=f"ecs_cpu_{service_name}")
            with col2:
                memory_gb = st.selectbox("Memory (GB)", ["0.5GB", "1GB", "2GB", "4GB", "8GB", "16GB"], key=f"ecs_memory_{service_name}")
            
            task_count = st.number_input("Number of Tasks", min_value=1, max_value=100, value=2, key=f"ecs_tasks_{service_name}")
            
            return {
                "cluster_type": cluster_type,
                "cpu_units": cpu_units,
                "memory_gb": memory_gb,
                "task_count": task_count
            }
        else:
            # EC2 cluster configuration
            instance_type = st.selectbox(
                "Instance Type",
                ["t3.micro", "t3.small", "t3.medium", "m5.large", "m5.xlarge"],
                key=f"ecs_ec2_instance_{service_name}"
            )
            instance_count = st.number_input("Instance Count", min_value=1, max_value=20, value=2, key=f"ecs_ec2_count_{service_name}")
            
            return {
                "cluster_type": cluster_type,
                "instance_type": instance_type,
                "instance_count": instance_count
            }
    
    elif service_name == "Amazon EKS":
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=50, value=3, key=f"eks_nodes_{service_name}")
        
        node_type = st.selectbox(
            "Node Type",
            ["t3.medium", "t3.large", "m5.large", "m5.xlarge", "m5.2xlarge"],
            key=f"eks_node_type_{service_name}"
        )
        
        return {
            "node_count": node_count,
            "node_type": node_type
        }
    
    elif service_name == "Amazon EBS":
        volume_type = st.selectbox(
            "Volume Type",
            ["gp3", "gp2", "io1", "io2", "st1", "sc1"],
            key=f"ebs_type_{service_name}"
        )
        
        volume_size_gb = st.number_input("Volume Size (GB)", min_value=1, max_value=10000, value=100, key=f"ebs_size_{service_name}")
        
        if volume_type in ["io1", "io2"]:
            iops = st.number_input("IOPS", min_value=100, max_value=100000, value=3000, key=f"ebs_iops_{service_name}")
        else:
            iops = 0
        
        return {
            "volume_type": volume_type,
            "volume_size_gb": volume_size_gb,
            "iops": iops
        }
    
    elif service_name == "Amazon EFS":
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=100000, value=100, key=f"efs_storage_{service_name}")
        
        storage_class = st.selectbox(
            "Storage Class",
            ["Standard", "Infrequent Access"],
            key=f"efs_class_{service_name}"
        )
        
        return {
            "storage_gb": storage_gb,
            "storage_class": storage_class
        }
    
    elif service_name == "Amazon DynamoDB":
        capacity_mode = st.selectbox(
            "Capacity Mode",
            ["Provisioned", "On-Demand"],
            key=f"dynamo_capacity_{service_name}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            read_units = st.number_input("Read Capacity Units", min_value=1, max_value=100000, value=10, key=f"dynamo_read_{service_name}")
        with col2:
            write_units = st.number_input("Write Capacity Units", min_value=1, max_value=100000, value=10, key=f"dynamo_write_{service_name}")
        
        storage_gb = st.number_input("Storage (GB)", min_value=1, max_value=10000, value=100, key=f"dynamo_storage_{service_name}")
        
        return {
            "capacity_mode": capacity_mode,
            "read_units": read_units,
            "write_units": write_units,
            "storage_gb": storage_gb
        }
    
    elif service_name == "Amazon ElastiCache":
        node_type = st.selectbox(
            "Node Type",
            ["cache.t3.micro", "cache.t3.small", "cache.t3.medium", "cache.t3.large",
             "cache.m5.large", "cache.m5.xlarge", "cache.m5.2xlarge",
             "cache.r5.large", "cache.r5.xlarge", "cache.r5.2xlarge"],
            key=f"cache_node_type_{service_name}"
        )
        
        engine = st.selectbox(
            "Engine",
            ["Redis", "Memcached"],
            key=f"cache_engine_{service_name}"
        )
        
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=10, value=2, key=f"cache_nodes_{service_name}")
        
        return {
            "node_type": node_type,
            "engine": engine,
            "node_count": node_count
        }
    
    elif service_name == "Amazon CloudFront":
        data_transfer_tb = st.number_input("Monthly Data Transfer (TB)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1, key=f"cf_transfer_{service_name}")
        
        requests_million = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"cf_requests_{service_name}")
        
        return {
            "data_transfer_tb": data_transfer_tb,
            "requests_million": requests_million
        }
    
    elif service_name == "Elastic Load Balancing":
        load_balancer_type = st.selectbox(
            "Load Balancer Type",
            ["Application", "Network", "Gateway"],
            key=f"elb_type_{service_name}"
        )
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=1000.0, value=5.0, step=0.1, key=f"elb_data_{service_name}")
        
        return {
            "load_balancer_type": load_balancer_type,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "Amazon API Gateway":
        api_type = st.selectbox(
            "API Type",
            ["REST API", "HTTP API"],
            key=f"api_type_{service_name}"
        )
        
        requests_million = st.number_input("Monthly Requests (millions)", min_value=0.1, max_value=1000.0, value=1.0, step=0.1, key=f"api_requests_{service_name}")
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=100.0, value=0.5, step=0.1, key=f"api_data_{service_name}")
        
        return {
            "api_type": api_type,
            "requests_million": requests_million,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "Amazon Kinesis":
        shard_hours = st.number_input("Shard Hours (per month)", min_value=1, max_value=100000, value=720, key=f"kinesis_shards_{service_name}")
        
        data_processed_tb = st.number_input("Monthly Data Processed (TB)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"kinesis_data_{service_name}")
        
        return {
            "shard_hours": shard_hours,
            "data_processed_tb": data_processed_tb
        }
    
    elif service_name == "AWS Glue":
        dpu_hours = st.number_input("DPU Hours (per month)", min_value=1, max_value=10000, value=100, key=f"glue_dpu_{service_name}")
        
        return {
            "dpu_hours": dpu_hours
        }
    
    elif service_name == "Amazon Redshift":
        node_type = st.selectbox(
            "Node Type",
            ["ra3.4xlarge", "ra3.16xlarge", "dc2.large", "dc2.8xlarge", "ds2.xlarge", "ds2.8xlarge"],
            key=f"redshift_node_type_{service_name}"
        )
        
        node_count = st.number_input("Number of Nodes", min_value=1, max_value=100, value=2, key=f"redshift_nodes_{service_name}")
        
        return {
            "node_type": node_type,
            "node_count": node_count
        }
    
    elif service_name == "Amazon Bedrock":
        input_tokens_million = st.number_input("Input Tokens (millions per month)", min_value=1, max_value=1000, value=10, key=f"bedrock_input_{service_name}")
        
        output_tokens_million = st.number_input("Output Tokens (millions per month)", min_value=1, max_value=1000, value=5, key=f"bedrock_output_{service_name}")
        
        return {
            "input_tokens_million": input_tokens_million,
            "output_tokens_million": output_tokens_million
        }
    
    elif service_name == "Amazon SageMaker":
        instance_type = st.selectbox(
            "Instance Type",
            ["ml.t3.medium", "ml.t3.large", "ml.t3.xlarge",
             "ml.m5.large", "ml.m5.xlarge", "ml.m5.2xlarge", "ml.m5.4xlarge",
             "ml.c5.large", "ml.c5.xlarge", "ml.c5.2xlarge", "ml.c5.4xlarge",
             "ml.p3.2xlarge", "ml.p3.8xlarge", "ml.p3.16xlarge"],
            key=f"sagemaker_instance_{service_name}"
        )
        
        hours_per_month = st.number_input("Hours per Month", min_value=1, max_value=744, value=168, key=f"sagemaker_hours_{service_name}")
        
        return {
            "instance_type": instance_type,
            "hours_per_month": hours_per_month
        }
    
    elif service_name == "AWS Step Functions":
        state_machines = st.number_input("Number of State Machines", min_value=1, max_value=100, value=1, key=f"stepfunctions_machines_{service_name}")
        
        state_transitions_million = st.number_input("State Transitions (millions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"stepfunctions_transitions_{service_name}")
        
        return {
            "state_machines": state_machines,
            "state_transitions_million": state_transitions_million
        }
    
    elif service_name == "Amazon EventBridge":
        event_buses = st.number_input("Number of Event Buses", min_value=1, max_value=10, value=1, key=f"eventbridge_buses_{service_name}")
        
        events_million = st.number_input("Events (millions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"eventbridge_events_{service_name}")
        
        return {
            "event_buses": event_buses,
            "events_million": events_million
        }
    
    elif service_name == "Amazon SNS":
        topics = st.number_input("Number of Topics", min_value=1, max_value=100, value=1, key=f"sns_topics_{service_name}")
        
        notifications_million = st.number_input("Notifications (millions per month)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"sns_notifications_{service_name}")
        
        return {
            "topics": topics,
            "notifications_million": notifications_million
        }
    
    elif service_name == "Amazon SQS":
        queues = st.number_input("Number of Queues", min_value=1, max_value=100, value=1, key=f"sqs_queues_{service_name}")
        
        requests_million = st.number_input("Requests (millions per month)", min_value=0.1, max_value=1000.0, value=10.0, step=0.1, key=f"sqs_requests_{service_name}")
        
        return {
            "queues": queues,
            "requests_million": requests_million
        }
    
    elif service_name == "AWS WAF":
        web_acls = st.number_input("Number of Web ACLs", min_value=1, max_value=10, value=1, key=f"waf_acls_{service_name}")
        
        requests_billion = st.number_input("Requests (billions per month)", min_value=0.1, max_value=100.0, value=1.0, step=0.1, key=f"waf_requests_{service_name}")
        
        return {
            "web_acls": web_acls,
            "requests_billion": requests_billion
        }
    
    elif service_name == "Amazon GuardDuty":
        data_sources = st.multiselect(
            "Data Sources",
            ["CloudTrail", "VPC Flow Logs", "DNS Logs"],
            default=["CloudTrail", "VPC Flow Logs"],
            key=f"guardduty_sources_{service_name}"
        )
        
        return {
            "data_sources": data_sources
        }
    
    elif service_name == "AWS Shield":
        protection_type = st.selectbox(
            "Protection Type",
            ["Standard", "Advanced"],
            key=f"shield_type_{service_name}"
        )
        
        return {
            "protection_type": protection_type
        }
    
    elif service_name == "Amazon OpenSearch":
        instance_type = st.selectbox(
            "Instance Type",
            ["t3.small.search", "t3.medium.search", "m5.large.search", "m5.xlarge.search", "r5.large.search", "r5.xlarge.search"],
            key=f"opensearch_instance_{service_name}"
        )
        
        instance_count = st.number_input("Instance Count", min_value=1, max_value=10, value=2, key=f"opensearch_count_{service_name}")
        
        storage_gb = st.number_input("Storage per Instance (GB)", min_value=10, max_value=1000, value=100, key=f"opensearch_storage_{service_name}")
        
        return {
            "instance_type": instance_type,
            "instance_count": instance_count,
            "storage_gb": storage_gb
        }
    
    else:
        # Default configuration for unsupported services
        st.info(f"Configuration for {service_name} will be available soon.")
        return {}

def calculate_service_cost(service_name: str, config: Dict, timeline_config: Dict) -> Dict:
    """Calculate cost for a specific service"""
    try:
        # Get base monthly cost
        if service_name == "Amazon EC2":
            hourly_price = AWSPricingAPI.get_ec2_pricing(config['instance_type'])
            monthly_hours = config['daily_hours'] * 30
            base_monthly_cost = hourly_price * config['instance_count'] * monthly_hours
        
        elif service_name == "Amazon RDS":
            hourly_price = AWSPricingAPI.get_rds_pricing(config['instance_type'], config['engine'])
            base_monthly_cost = hourly_price * 730  # 730 hours per month
            # Add storage cost
            storage_price = 0.115  # gp2 storage per GB-month
            base_monthly_cost += config['storage_gb'] * storage_price
        
        elif service_name == "Amazon S3":
            storage_price = AWSPricingAPI.get_s3_pricing(config['storage_class'])
            base_monthly_cost = config['storage_gb'] * storage_price
            # Add data transfer cost
            transfer_cost = config['data_transfer_gb'] * 0.09  # $0.09 per GB
            base_monthly_cost += transfer_cost
        
        elif service_name == "AWS Lambda":
            lambda_pricing = AWSPricingAPI.get_lambda_pricing()
            # Calculate compute cost
            compute_cost = (config['monthly_requests'] * 1000000) * (config['duration_ms'] / 1000) * (config['memory_mb'] / 1024) * lambda_pricing['compute_price']
            # Calculate request cost
            request_cost = (config['monthly_requests'] * 1000000) * lambda_pricing['request_price']
            base_monthly_cost = compute_cost + request_cost
        
        elif service_name == "Amazon ECS":
            if config['cluster_type'] == "Fargate":
                # Fargate pricing
                cpu_map = {"0.25 vCPU": 0.04048, "0.5 vCPU": 0.08096, "1 vCPU": 0.16192, "2 vCPU": 0.32384, "4 vCPU": 0.64768}
                memory_map = {"0.5GB": 0.004445, "1GB": 0.00889, "2GB": 0.01778, "4GB": 0.03556, "8GB": 0.07112, "16GB": 0.14224}
                
                cpu_cost = cpu_map.get(config['cpu_units'], 0.16192)
                memory_cost = memory_map.get(config['memory_gb'], 0.01778)
                hourly_price = cpu_cost + memory_cost
                base_monthly_cost = hourly_price * config['task_count'] * 730
            else:
                # EC2 pricing
                hourly_price = AWSPricingAPI.get_ec2_pricing(config['instance_type'])
                base_monthly_cost = hourly_price * config['instance_count'] * 730
        
        elif service_name == "Amazon EKS":
            # EKS cluster cost + node cost
            cluster_cost = 0.10 * 730  # $0.10 per hour
            node_hourly_cost = AWSPricingAPI.get_ec2_pricing(config['node_type'])
            nodes_cost = node_hourly_cost * config['node_count'] * 730
            base_monthly_cost = cluster_cost + nodes_cost
        
        elif service_name == "Amazon EBS":
            ebs_pricing = AWSPricingAPI.get_ebs_pricing(config['volume_type'])
            storage_cost = config['volume_size_gb'] * ebs_pricing['storage']
            iops_cost = config['iops'] * ebs_pricing['iops'] if ebs_pricing['iops'] > 0 else 0
            base_monthly_cost = storage_cost + iops_cost
        
        elif service_name == "Amazon EFS":
            storage_price = AWSPricingAPI.get_efs_pricing(config['storage_class'])
            base_monthly_cost = config['storage_gb'] * storage_price
        
        elif service_name == "Amazon DynamoDB":
            base_monthly_cost = AWSPricingAPI.get_dynamodb_pricing(
                config['capacity_mode'],
                config['read_units'],
                config['write_units'],
                config['storage_gb']
            )
        
        elif service_name == "Amazon ElastiCache":
            hourly_price = AWSPricingAPI.get_elasticache_pricing(config['node_type'], config['engine'])
            base_monthly_cost = hourly_price * config['node_count']
        
        elif service_name == "Amazon CloudFront":
            cf_pricing = AWSPricingAPI.get_cloudfront_pricing()
            data_cost = config['data_transfer_tb'] * 1000 * cf_pricing['data_transfer']  # Convert TB to GB
            request_cost = (config['requests_million'] * 10000) * cf_pricing['requests']  # Convert million to 10k units
            base_monthly_cost = data_cost + request_cost
        
        elif service_name == "Elastic Load Balancing":
            # Simplified ELB pricing
            if config['load_balancer_type'] == "Application":
                base_monthly_cost = 0.0225 * 730 + config['data_processed_tb'] * 1000 * 0.008  # $0.0225/hour + $0.008/GB
            elif config['load_balancer_type'] == "Network":
                base_monthly_cost = 0.0225 * 730 + config['data_processed_tb'] * 1000 * 0.006  # $0.0225/hour + $0.006/GB
            else:  # Gateway
                base_monthly_cost = 0.025 * 730 + config['data_processed_tb'] * 1000 * 0.005  # $0.025/hour + $0.005/GB
        
        elif service_name == "Amazon API Gateway":
            base_monthly_cost = AWSPricingAPI.get_api_gateway_pricing(
                config['api_type'],
                config['requests_million'],
                config['data_processed_tb']
            )
        
        elif service_name == "Amazon Kinesis":
            base_monthly_cost = AWSPricingAPI.get_kinesis_pricing(
                config['shard_hours'],
                config['data_processed_tb']
            )
        
        elif service_name == "AWS Glue":
            base_monthly_cost = AWSPricingAPI.get_glue_pricing(config['dpu_hours'])
        
        elif service_name == "Amazon Redshift":
            base_monthly_cost = AWSPricingAPI.get_redshift_pricing(
                config['node_type'],
                config['node_count']
            )
        
        elif service_name == "Amazon Bedrock":
            # Simplified Bedrock pricing (Claude Instant pricing)
            input_cost = config['input_tokens_million'] * 0.00080   # $0.80 per 1M tokens
            output_cost = config['output_tokens_million'] * 0.00240 # $2.40 per 1M tokens
            base_monthly_cost = input_cost + output_cost
        
        elif service_name == "Amazon SageMaker":
            base_monthly_cost = AWSPricingAPI.get_sagemaker_pricing(
                config['instance_type'],
                config['hours_per_month']
            )
        
        elif service_name == "AWS Step Functions":
            # $0.025 per 1000 state transitions
            base_monthly_cost = config['state_transitions_million'] * 1000000 * 0.000025
        
        elif service_name == "Amazon EventBridge":
            # $1.00 per million events
            base_monthly_cost = config['events_million'] * 1.00
        
        elif service_name == "Amazon SNS":
            base_monthly_cost = AWSPricingAPI.get_sns_pricing(config['notifications_million'])
        
        elif service_name == "Amazon SQS":
            base_monthly_cost = AWSPricingAPI.get_sqs_pricing(config['requests_million'])
        
        elif service_name == "AWS WAF":
            # $5 per web ACL per month + $1 per million requests
            base_monthly_cost = config['web_acls'] * 5 + config['requests_billion'] * 1000 * 1.00
        
        elif service_name == "Amazon GuardDuty":
            # $0.00150 per GB of CloudTrail events, $0.00300 per GB of VPC Flow Logs
            base_monthly_cost = 0
            if "CloudTrail" in config['data_sources']:
                base_monthly_cost += 100 * 0.00150  # Assuming 100GB of CloudTrail
            if "VPC Flow Logs" in config['data_sources']:
                base_monthly_cost += 500 * 0.00300  # Assuming 500GB of VPC Flow Logs
            if "DNS Logs" in config['data_sources']:
                base_monthly_cost += 50 * 0.00200   # Assuming 50GB of DNS Logs
        
        elif service_name == "AWS Shield":
            if config['protection_type'] == "Standard":
                base_monthly_cost = 0  # Free
            else:  # Advanced
                base_monthly_cost = 3000  # $3000 per month
        
        elif service_name == "Amazon OpenSearch":
            # Simplified pricing based on EC2 instance types
            instance_prices = {
                "t3.small.search": 0.036, "t3.medium.search": 0.074,
                "m5.large.search": 0.126, "m5.xlarge.search": 0.252,
                "r5.large.search": 0.167, "r5.xlarge.search": 0.334
            }
            hourly_price = instance_prices.get(config['instance_type'], 0.126)
            instance_cost = hourly_price * config['instance_count'] * 730
            storage_cost = config['storage_gb'] * config['instance_count'] * 0.10  # $0.10 per GB
            base_monthly_cost = instance_cost + storage_cost
        
        else:
            base_monthly_cost = 100  # Default cost for unsupported services
        
        # Apply commitment discount
        commitment_discount = 0
        if timeline_config['commitment_type'] == "1-year":
            commitment_discount = 0.20  # 20% discount
        elif timeline_config['commitment_type'] == "3-year":
            commitment_discount = 0.40  # 40% discount
        
        discounted_monthly_cost = base_monthly_cost * (1 - commitment_discount)
        
        # Calculate timeline costs with growth
        monthly_data = {
            'months': [],
            'monthly_costs': [],
            'cumulative_costs': []
        }
        
        total_months = timeline_config['total_months']
        current_cost = discounted_monthly_cost
        cumulative_cost = 0
        
        for month in range(1, total_months + 1):
            # Apply usage pattern
            if timeline_config['usage_pattern'] == "Growing":
                monthly_cost = current_cost * (1 + timeline_config['growth_rate']) ** (month - 1)
            elif timeline_config['usage_pattern'] == "Seasonal":
                # Seasonal pattern: peak every 6 months
                seasonal_factor = 1.5 if month % 6 == 0 else 0.8
                monthly_cost = current_cost * seasonal_factor
            else:  # Steady
                monthly_cost = current_cost
            
            cumulative_cost += monthly_cost
            
            monthly_data['months'].append(f"Month {month}")
            monthly_data['monthly_costs'].append(monthly_cost)
            monthly_data['cumulative_costs'].append(cumulative_cost)
        
        total_timeline_cost = cumulative_cost
        
        return {
            'base_monthly_cost': base_monthly_cost,
            'discounted_monthly_cost': discounted_monthly_cost,
            'total_timeline_cost': total_timeline_cost,
            'monthly_data': monthly_data,
            'commitment_discount': commitment_discount
        }
    
    except Exception as e:
        st.error(f"Error calculating cost for {service_name}: {str(e)}")
        return {
            'base_monthly_cost': 0,
            'discounted_monthly_cost': 0,
            'total_timeline_cost': 0,
            'monthly_data': {'months': [], 'monthly_costs': [], 'cumulative_costs': []},
            'commitment_discount': 0
        }

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="AWS Architecture Cost Estimator",
        page_icon="☁️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #232f3e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        background: white;
    }
    .cost-highlight {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff9900;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">☁️ AWS Architecture Cost Estimator</h1>', unsafe_allow_html=True)
    
    # Sidebar for service selection
    with st.sidebar:
        st.header("🏗️ Architecture Setup")
        
        # Project requirements
        st.subheader("📋 Project Requirements")
        workload_type = st.selectbox(
            "Workload Type",
            ["Web Application", "Microservices", "Data Pipeline", "AI/ML", "IoT", "Enterprise", "Custom"]
        )
        
        estimated_users = st.selectbox(
            "Estimated Users",
            ["< 1,000", "1,000 - 10,000", "10,000 - 100,000", "100,000 - 1M", "> 1M"]
        )
        
        data_volume = st.selectbox(
            "Data Volume",
            ["Low (< 100GB)", "Medium (100GB - 1TB)", "High (1TB - 10TB)", "Very High (> 10TB)"]
        )
        
        # Service selection
        st.subheader("🔧 AWS Services")
        selected_services = {}
        
        for category, services in AWS_SERVICES.items():
            with st.expander(f"{category} ({len(services)} services)"):
                for service, description in services.items():
                    if st.checkbox(f"{service}", key=f"service_{service}", help=description):
                        if category not in selected_services:
                            selected_services[category] = []
                        selected_services[category].append(service)
        
        # Timeline configuration
        st.subheader("📅 Timeline & Commitment")
        timeline_type = st.selectbox(
            "Timeline Period",
            ["3 months", "6 months", "1 year", "2 years", "3 years", "5 years"]
        )
        
        # Map timeline to months
        timeline_map = {
            "3 months": 3, "6 months": 6, "1 year": 12, 
            "2 years": 24, "3 years": 36, "5 years": 60
        }
        total_months = timeline_map[timeline_type]
        
        usage_pattern = st.selectbox(
            "Usage Pattern",
            ["Steady", "Growing", "Seasonal"]
        )
        
        growth_rate = 0.0
        if usage_pattern == "Growing":
            growth_rate = st.slider("Monthly Growth Rate (%)", 1, 20, 5) / 100.0
        
        commitment_type = st.selectbox(
            "Commitment Type",
            ["On-Demand", "1-year", "3-year"]
        )
        
        timeline_config = {
            'timeline_type': timeline_type,
            'total_months': total_months,
            'usage_pattern': usage_pattern,
            'growth_rate': growth_rate,
            'commitment_type': commitment_type
        }
        
        # Store in session state
        st.session_state.selected_services = selected_services
        st.session_state.timeline_config = timeline_config
    
    # Main content area
    if not st.session_state.selected_services:
        st.info("👈 Select AWS services from the sidebar to get started!")
        return
    
    # Service configuration tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Service Configuration", "💰 Cost Analysis", "🏗️ Architecture Diagram", "📊 Export Results"])
    
    with tab1:
        st.header("Service Configuration")
        
        # Store configurations
        configurations = {}
        
        for category, services in st.session_state.selected_services.items():
            st.subheader(f"{category} Services")
            
            for service in services:
                with st.expander(f"⚙️ {service}", expanded=True):
                    config = render_service_configuration(service)
                    if config:
                        configurations[service] = {
                            'config': config,
                            'category': category
                        }
        
        st.session_state.configurations = configurations
    
    with tab2:
        st.header("Cost Analysis")
        
        if not st.session_state.configurations:
            st.warning("Please configure the services in the Service Configuration tab first.")
        else:
            # Calculate costs
            total_cost = 0
            cost_breakdown = {}
            
            with st.spinner("Calculating costs..."):
                for service, service_data in st.session_state.configurations.items():
                    config = service_data['config']
                    pricing = calculate_service_cost(service, config, st.session_state.timeline_config)
                    
                    cost_breakdown[service] = {
                        'pricing': pricing,
                        'config': config,
                        'category': service_data['category']
                    }
                    total_cost += pricing['total_timeline_cost']
            
            st.session_state.cost_breakdown = cost_breakdown
            st.session_state.total_cost = total_cost
            
            # Display cost summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                monthly_cost = sum([data['pricing']['discounted_monthly_cost'] for data in cost_breakdown.values()])
                st.metric("Estimated Monthly Cost", f"${monthly_cost:,.2f}")
            
            with col2:
                st.metric("Total Timeline Cost", f"${total_cost:,.2f}")
            
            with col3:
                avg_monthly = total_cost / st.session_state.timeline_config['total_months']
                st.metric("Average Monthly Cost", f"${avg_monthly:,.2f}")
            
            # Cost breakdown by service
            st.subheader("Cost Breakdown by Service")
            cost_data = []
            for service, data in cost_breakdown.items():
                cost_data.append({
                    'Service': service,
                    'Category': data['category'],
                    'Monthly Cost': data['pricing']['discounted_monthly_cost'],
                    'Total Cost': data['pricing']['total_timeline_cost'],
                    'Discount': f"{data['pricing']['commitment_discount']*100:.0f}%"
                })
            
            if cost_data:
                cost_df = pd.DataFrame(cost_data)
                st.dataframe(cost_df, use_container_width=True)
                
                # Chart
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly cost by service
                    monthly_chart_data = pd.DataFrame({
                        'Service': [d['Service'] for d in cost_data],
                        'Monthly Cost': [d['Monthly Cost'] for d in cost_data]
                    })
                    st.bar_chart(monthly_chart_data.set_index('Service'))
                
                with col2:
                    # Cost by category
                    category_costs = {}
                    for data in cost_data:
                        category = data['Category']
                        if category not in category_costs:
                            category_costs[category] = 0
                        category_costs[category] += data['Monthly Cost']
                    
                    category_df = pd.DataFrame({
                        'Category': list(category_costs.keys()),
                        'Cost': list(category_costs.values())
                    })
                    st.bar_chart(category_df.set_index('Category'))
            
            # Monthly cost projection
            st.subheader("Monthly Cost Projection")
            if cost_breakdown:
                first_service = list(cost_breakdown.keys())[0]
                monthly_data = cost_breakdown[first_service]['pricing']['monthly_data']
                
                projection_df = pd.DataFrame({
                    'Month': monthly_data['months'],
                    'Monthly Cost': monthly_data['monthly_costs'],
                    'Cumulative Cost': monthly_data['cumulative_costs']
                })
                
                col1, col2 = st.columns(2)
                with col1:
                    st.line_chart(projection_df.set_index('Month')['Monthly Cost'])
                with col2:
                    st.area_chart(projection_df.set_index('Month')['Cumulative Cost'])
    
    with tab3:
        st.header("Architecture Diagram")
        
        if not st.session_state.selected_services:
            st.warning("Please select services first.")
        else:
            # Diagram type selection
            col1, col2 = st.columns([3, 1])
            
            with col2:
                diagram_type = st.selectbox(
                    "Diagram Type",
                    ["Professional HTML", "Mermaid", "Graphviz"]
                )
            
            with col1:
                st.info("💡 The architecture diagram shows how your selected AWS services connect and work together.")
            
            # Generate diagram
            if diagram_type == "Professional HTML":
                html_diagram = ProfessionalArchitectureGenerator.generate_professional_diagram_html(
                    st.session_state.selected_services,
                    st.session_state.configurations,
                    {}
                )
                components.html(html_diagram, height=800, scrolling=True)
            
            elif diagram_type == "Mermaid":
                mermaid_code = ProfessionalArchitectureGenerator.generate_mermaid_diagram(
                    st.session_state.selected_services,
                    st.session_state.configurations
                )
                st.code(mermaid_code, language="mermaid")
                
                # Try to render with mermaid component
                try:
                    components.html(f"""
                    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad:true}});</script>
                    <div class="mermaid">
                    {mermaid_code}
                    </div>
                    """, height=600)
                except:
                    st.warning("Mermaid diagram rendering not available in this environment.")
            
            elif diagram_type == "Graphviz":
                dot = ProfessionalArchitectureGenerator.generate_graphviz_diagram(
                    st.session_state.selected_services,
                    st.session_state.configurations
                )
                st.graphviz_chart(dot)
    
    with tab4:
        st.header("Export Results")
        
        if not st.session_state.get('cost_breakdown'):
            st.warning("Please generate cost analysis first.")
        else:
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Excel Export
                if st.button("📊 Export to Excel"):
                    excel_data = ExportManager.export_to_excel(
                        st.session_state.cost_breakdown,
                        st.session_state.total_cost,
                        st.session_state.timeline_config
                    )
                    
                    st.download_button(
                        label="⬇️ Download Excel File",
                        data=excel_data,
                        file_name=f"aws_cost_estimate_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with col2:
                # PDF Export
                if st.button("📄 Export to PDF"):
                    pdf_data = ExportManager.export_to_pdf(
                        st.session_state.cost_breakdown,
                        st.session_state.total_cost,
                        st.session_state.timeline_config
                    )
                    
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name=f"aws_cost_estimate_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
            
            # Summary report
            st.subheader("Summary Report")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("**Timeline Configuration**")
                st.write(f"**Period:** {st.session_state.timeline_config['timeline_type']}")
                st.write(f"**Usage Pattern:** {st.session_state.timeline_config['usage_pattern']}")
                st.write(f"**Commitment:** {st.session_state.timeline_config['commitment_type']}")
                if st.session_state.timeline_config['usage_pattern'] == "Growing":
                    st.write(f"**Growth Rate:** {st.session_state.timeline_config['growth_rate']*100:.1f}%")
            
            with col2:
                st.info("**Cost Summary**")
                monthly_cost = sum([data['pricing']['discounted_monthly_cost'] for data in st.session_state.cost_breakdown.values()])
                st.write(f"**Monthly Cost:** ${monthly_cost:,.2f}")
                st.write(f"**Total Cost:** ${st.session_state.total_cost:,.2f}")
                st.write(f"**Services:** {len(st.session_state.cost_breakdown)}")
            
            # Recommendations
            st.subheader("💡 Cost Optimization Recommendations")
            
            recommendations = []
            
            # Check for potential optimizations
            for service, data in st.session_state.cost_breakdown.items():
                config = data['config']
                pricing = data['pricing']
                
                if service == "Amazon EC2":
                    if config['instance_type'].startswith('t3') and pricing['discounted_monthly_cost'] > 100:
                        recommendations.append(f"Consider upgrading {service} from {config['instance_type']} to a larger instance type for better performance/cost ratio")
                
                elif service == "Amazon RDS":
                    if config['engine'] in ['Oracle', 'SQL Server'] and pricing['discounted_monthly_cost'] > 500:
                        recommendations.append(f"Consider migrating {service} from {config['engine']} to PostgreSQL or MySQL for significant cost savings")
                
                elif service == "Amazon S3":
                    if config['storage_class'] == 'Standard' and config['storage_gb'] > 1000:
                        recommendations.append(f"Consider moving infrequently accessed data in {service} to S3 Intelligent-Tiering for automatic cost optimization")
            
            if not recommendations:
                st.success("✅ Your architecture appears to be well-optimized! No major cost-saving recommendations at this time.")
            else:
                for rec in recommendations:
                    st.warning(rec)

if __name__ == "__main__":
    main()