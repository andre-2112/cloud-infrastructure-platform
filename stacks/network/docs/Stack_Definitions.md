```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: network
  version: v1
  description: VPC networking infrastructure with public/private subnets and multi-AZ design
  language: typescript
  priority: 20

spec:
  dependencies: []

  resources:
    vpc:
      main_vpc:
        name: "${config.project}-${config.environment}-vpc"
        cidr_block: "${config.vpc_cidr}"
        instance_tenancy: "default"
        enable_dns_hostnames: true
        enable_dns_support: true
        enable_network_address_usage_metrics: true
        tags:
          Name: "${config.project}-${config.environment}-vpc"
          Environment: "${config.environment}"
          Purpose: "Main VPC for ${PROJECT_NAME} infrastructure"

    dhcp_options:
      main_dhcp:
        name: "${config.project}-${config.environment}-dhcp"
        domain_name: "${config.region}.compute.internal"
        domain_name_servers: ["AmazonProvidedDNS"]
        tags:
          Name: "${config.project}-${config.environment}-dhcp"
          Environment: "${config.environment}"

    internet_gateway:
      main_igw:
        name: "${config.project}-${config.environment}-igw"
        vpc_id: "${resources.vpc.main_vpc.id}"
        tags:
          Name: "${config.project}-${config.environment}-igw"
          Environment: "${config.environment}"
          Purpose: "Internet access for public subnets"

    subnets:
      public:
        public_subnet_a:
          name: "${config.project}-${config.environment}-public-1a"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.public_subnet_a_cidr}"
          availability_zone: "${config.region}a"
          map_public_ip_on_launch: true
          tags:
            Name: "${config.project}-${config.environment}-public-1a"
            Environment: "${config.environment}"
            Type: "Public"
            Tier: "DMZ"

        public_subnet_b:
          name: "${config.project}-${config.environment}-public-1b"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.public_subnet_b_cidr}"
          availability_zone: "${config.region}b"
          map_public_ip_on_launch: true
          tags:
            Name: "${config.project}-${config.environment}-public-1b"
            Environment: "${config.environment}"
            Type: "Public"
            Tier: "DMZ"

      private:
        private_subnet_a:
          name: "${config.project}-${config.environment}-private-1a"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.private_subnet_a_cidr}"
          availability_zone: "${config.region}a"
          map_public_ip_on_launch: false
          tags:
            Name: "${config.project}-${config.environment}-private-1a"
            Environment: "${config.environment}"
            Type: "Private"
            Tier: "Application"

        private_subnet_b:
          name: "${config.project}-${config.environment}-private-1b"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.private_subnet_b_cidr}"
          availability_zone: "${config.region}b"
          map_public_ip_on_launch: false
          tags:
            Name: "${config.project}-${config.environment}-private-1b"
            Environment: "${config.environment}"
            Type: "Private"
            Tier: "Application"

      database:
        db_subnet_a:
          name: "${config.project}-${config.environment}-db-1a"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.db_subnet_a_cidr}"
          availability_zone: "${config.region}a"
          map_public_ip_on_launch: false
          tags:
            Name: "${config.project}-${config.environment}-db-1a"
            Environment: "${config.environment}"
            Type: "Database"
            Tier: "Data"

        db_subnet_b:
          name: "${config.project}-${config.environment}-db-1b"
          vpc_id: "${resources.vpc.main_vpc.id}"
          cidr_block: "${config.db_subnet_b_cidr}"
          availability_zone: "${config.region}b"
          map_public_ip_on_launch: false
          tags:
            Name: "${config.project}-${config.environment}-db-1b"
            Environment: "${config.environment}"
            Type: "Database"
            Tier: "Data"

    nat_gateways:
      nat_gateway_a:
        name: "${config.project}-${config.environment}-nat-1a"
        subnet_id: "${resources.subnets.public.public_subnet_a.id}"
        allocation_id: "${resources.elastic_ips.nat_eip_a.id}"
        connectivity_type: "public"
        tags:
          Name: "${config.project}-${config.environment}-nat-1a"
          Environment: "${config.environment}"
          AZ: "${config.region}a"

      nat_gateway_b:
        name: "${config.project}-${config.environment}-nat-1b"
        subnet_id: "${resources.subnets.public.public_subnet_b.id}"
        allocation_id: "${resources.elastic_ips.nat_eip_b.id}"
        connectivity_type: "public"
        condition: "${config.high_availability}"
        tags:
          Name: "${config.project}-${config.environment}-nat-1b"
          Environment: "${config.environment}"
          AZ: "${config.region}b"

    elastic_ips:
      nat_eip_a:
        name: "${config.project}-${config.environment}-nat-eip-1a"
        domain: "vpc"
        tags:
          Name: "${config.project}-${config.environment}-nat-eip-1a"
          Environment: "${config.environment}"
          Purpose: "NAT Gateway AZ-a"

      nat_eip_b:
        name: "${config.project}-${config.environment}-nat-eip-1b"
        domain: "vpc"
        condition: "${config.high_availability}"
        tags:
          Name: "${config.project}-${config.environment}-nat-eip-1b"
          Environment: "${config.environment}"
          Purpose: "NAT Gateway AZ-b"

    route_tables:
      public_rt:
        name: "${config.project}-${config.environment}-public-rt"
        vpc_id: "${resources.vpc.main_vpc.id}"
        routes:
          - cidr_block: "0.0.0.0/0"
            gateway_id: "${resources.internet_gateway.main_igw.id}"
        tags:
          Name: "${config.project}-${config.environment}-public-rt"
          Environment: "${config.environment}"
          Type: "Public"

      private_rt_a:
        name: "${config.project}-${config.environment}-private-rt-1a"
        vpc_id: "${resources.vpc.main_vpc.id}"
        routes:
          - cidr_block: "0.0.0.0/0"
            nat_gateway_id: "${resources.nat_gateways.nat_gateway_a.id}"
        tags:
          Name: "${config.project}-${config.environment}-private-rt-1a"
          Environment: "${config.environment}"
          Type: "Private"
          AZ: "${config.region}a"

      private_rt_b:
        name: "${config.project}-${config.environment}-private-rt-1b"
        vpc_id: "${resources.vpc.main_vpc.id}"
        routes:
          - cidr_block: "0.0.0.0/0"
            nat_gateway_id: "${config.high_availability ? resources.nat_gateways.nat_gateway_b.id : resources.nat_gateways.nat_gateway_a.id}"
        tags:
          Name: "${config.project}-${config.environment}-private-rt-1b"
          Environment: "${config.environment}"
          Type: "Private"
          AZ: "${config.region}b"

      database_rt:
        name: "${config.project}-${config.environment}-database-rt"
        vpc_id: "${resources.vpc.main_vpc.id}"
        tags:
          Name: "${config.project}-${config.environment}-database-rt"
          Environment: "${config.environment}"
          Type: "Database"
          Purpose: "Isolated database subnets"

    flow_logs:
      vpc_flow_log:
        name: "${config.project}-${config.environment}-vpc-flow-log"
        iam_role_arn: "${resources.iam_roles.flow_log_role.arn}"
        log_destination: "${resources.cloudwatch_log_groups.flow_log_group.arn}"
        resource_id: "${resources.vpc.main_vpc.id}"
        resource_type: "VPC"
        traffic_type: "${config.flow_log_traffic_type}"
        log_format: "${config.flow_log_format}"
        condition: "${config.enable_flow_logs}"
        tags:
          Name: "${config.project}-${config.environment}-vpc-flow-log"
          Environment: "${config.environment}"

    vpc_endpoints:
      s3_endpoint:
        name: "${config.project}-${config.environment}-s3-endpoint"
        vpc_id: "${resources.vpc.main_vpc.id}"
        service_name: "com.amazonaws.${config.region}.s3"
        vpc_endpoint_type: "Gateway"
        route_table_ids:
          - "${resources.route_tables.private_rt_a.id}"
          - "${resources.route_tables.private_rt_b.id}"
        condition: "${config.enable_vpc_endpoints}"
        tags:
          Name: "${config.project}-${config.environment}-s3-endpoint"
          Environment: "${config.environment}"

      ecr_api_endpoint:
        name: "${config.project}-${config.environment}-ecr-api-endpoint"
        vpc_id: "${resources.vpc.main_vpc.id}"
        service_name: "com.amazonaws.${config.region}.ecr.api"
        vpc_endpoint_type: "Interface"
        subnet_ids:
          - "${resources.subnets.private.private_subnet_a.id}"
          - "${resources.subnets.private.private_subnet_b.id}"
        security_group_ids:
          - "${deps.security.security_group_ids.vpc_endpoints}"
        condition: "${config.enable_vpc_endpoints}"
        tags:
          Name: "${config.project}-${config.environment}-ecr-api-endpoint"
          Environment: "${config.environment}"

  outputs:
    vpc_info:
      vpc_id:
        description: "Main VPC ID"
        value: "${resources.vpc.main_vpc.id}"

      vpc_arn:
        description: "Main VPC ARN"
        value: "${resources.vpc.main_vpc.arn}"

      vpc_cidr_block:
        description: "VPC CIDR block"
        value: "${resources.vpc.main_vpc.cidr_block}"

      vpc_default_security_group_id:
        description: "VPC default security group ID"
        value: "${resources.vpc.main_vpc.default_security_group_id}"

    subnet_info:
      public_subnet_ids:
        description: "Public subnet IDs"
        value:
          - "${resources.subnets.public.public_subnet_a.id}"
          - "${resources.subnets.public.public_subnet_b.id}"

      private_subnet_ids:
        description: "Private subnet IDs"
        value:
          - "${resources.subnets.private.private_subnet_a.id}"
          - "${resources.subnets.private.private_subnet_b.id}"

      database_subnet_ids:
        description: "Database subnet IDs"
        value:
          - "${resources.subnets.database.db_subnet_a.id}"
          - "${resources.subnets.database.db_subnet_b.id}"

      availability_zones:
        description: "Availability zones used"
        value:
          - "${config.region}a"
          - "${config.region}b"

    gateway_info:
      internet_gateway_id:
        description: "Internet Gateway ID"
        value: "${resources.internet_gateway.main_igw.id}"

      nat_gateway_ids:
        description: "NAT Gateway IDs"
        value:
          - "${resources.nat_gateways.nat_gateway_a.id}"
          - "${config.high_availability ? resources.nat_gateways.nat_gateway_b.id : null}"

      nat_gateway_ips:
        description: "NAT Gateway Elastic IP addresses"
        value:
          - "${resources.elastic_ips.nat_eip_a.public_ip}"
          - "${config.high_availability ? resources.elastic_ips.nat_eip_b.public_ip : null}"

    route_table_info:
      public_route_table_id:
        description: "Public route table ID"
        value: "${resources.route_tables.public_rt.id}"

      private_route_table_ids:
        description: "Private route table IDs"
        value:
          - "${resources.route_tables.private_rt_a.id}"
          - "${resources.route_tables.private_rt_b.id}"

      database_route_table_id:
        description: "Database route table ID"
        value: "${resources.route_tables.database_rt.id}"

  parameters:
    project:
      type: string
      description: "Project name for resource naming"
      required: true
      default: "${PROJECT_NAME}"

    environment:
      type: string
      description: "Environment name"
      required: true
      validation:
        allowed_values: ["dev", "stage", "prod"]

    region:
      type: string
      description: "AWS region"
      required: true
      default: "us-east-1"

    vpc_cidr:
      type: string
      description: "CIDR block for VPC"
      default: "10.0.0.0/16"
      validation:
        pattern: "^10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/16$"

    public_subnet_a_cidr:
      type: string
      description: "CIDR for public subnet A"
      default: "10.0.1.0/24"

    public_subnet_b_cidr:
      type: string
      description: "CIDR for public subnet B"
      default: "10.0.2.0/24"

    private_subnet_a_cidr:
      type: string
      description: "CIDR for private subnet A"
      default: "10.0.10.0/24"

    private_subnet_b_cidr:
      type: string
      description: "CIDR for private subnet B"
      default: "10.0.11.0/24"

    db_subnet_a_cidr:
      type: string
      description: "CIDR for database subnet A"
      default: "10.0.20.0/24"

    db_subnet_b_cidr:
      type: string
      description: "CIDR for database subnet B"
      default: "10.0.21.0/24"

    high_availability:
      type: boolean
      description: "Enable high availability with multiple NAT Gateways"
      default: false

    enable_flow_logs:
      type: boolean
      description: "Enable VPC Flow Logs"
      default: true

    flow_log_traffic_type:
      type: string
      description: "Type of traffic to log (ALL, ACCEPT, REJECT)"
      default: "ALL"
      validation:
        allowed_values: ["ALL", "ACCEPT", "REJECT"]

    flow_log_format:
      type: string
      description: "Flow log format"
      default: "${version} ${account-id} ${interface-id} ${srcaddr} ${dstaddr} ${srcport} ${dstport} ${protocol} ${packets} ${bytes} ${windowstart} ${windowend} ${action} ${flowlogstatus}"

    enable_vpc_endpoints:
      type: boolean
      description: "Enable VPC endpoints for AWS services"
      default: false

    enable_dns_hostnames:
      type: boolean
      description: "Enable DNS hostnames in VPC"
      default: true

    enable_dns_support:
      type: boolean
      description: "Enable DNS support in VPC"
      default: true

  dependencies:
    outputs_required: []

  tags:
    - networking
    - vpc
    - subnets
    - foundation
    - infrastructure
    - multi-az
```