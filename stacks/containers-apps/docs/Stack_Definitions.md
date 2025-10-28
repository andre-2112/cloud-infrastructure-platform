```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: containers-apps
  version: v1
  description: Container applications running on ECS with load balancing
  language: typescript
  priority: 90

spec:
  dependencies:
    - network
    - security
    - dns
    - containers-images

  resources:
    load_balancers:
      public_alb:
        name: "${config.project}-${config.environment}-public-alb"
        load_balancer_type: "application"
        scheme: "internet-facing"
        subnets: "${deps.network.subnet_info.public_subnet_ids}"
        security_groups:
          - "${deps.security.security_group_ids.load_balancer_sg_id}"
        enable_deletion_protection: "${config.enable_deletion_protection}"
        tags:
          Name: "${config.project}-${config.environment}-public-alb"
          Environment: "${config.environment}"

    ecs_cluster:
      main_cluster:
        name: "${config.project}-${config.environment}-cluster"
        capacity_providers: ["FARGATE", "FARGATE_SPOT"]
        default_capacity_provider_strategy:
          - capacity_provider: "FARGATE"
            weight: 1
            base: 1
        setting:
          - name: "containerInsights"
            value: "enabled"
        tags:
          Name: "${config.project}-${config.environment}-cluster"
          Environment: "${config.environment}"

    ecs_services:
      frontend_service:
        name: "${config.project}-${config.environment}-frontend"
        cluster: "${resources.ecs_cluster.main_cluster.id}"
        task_definition: "${resources.ecs_task_definitions.frontend_task.arn}"
        desired_count: "${config.frontend_desired_count}"
        launch_type: "FARGATE"
        platform_version: "LATEST"
        network_configuration:
          subnets: "${deps.network.subnet_info.private_subnet_ids}"
          security_groups:
            - "${deps.security.security_group_ids.web_application_sg_id}"
          assign_public_ip: false
        load_balancer:
          - target_group_arn: "${resources.target_groups.frontend_tg.arn}"
            container_name: "frontend"
            container_port: 3000
        service_registries:
          - registry_arn: "${resources.service_discovery.frontend_service.arn}"
        tags:
          Name: "${config.project}-${config.environment}-frontend-service"
          Environment: "${config.environment}"

    ecs_task_definitions:
      frontend_task:
        family: "${config.project}-${config.environment}-frontend"
        network_mode: "awsvpc"
        requires_compatibilities: ["FARGATE"]
        cpu: "${config.frontend_cpu}"
        memory: "${config.frontend_memory}"
        execution_role_arn: "${deps.security.iam_role_arns.ecs_execution_role_arn}"
        task_role_arn: "${deps.security.iam_role_arns.ecs_task_role_arn}"
        container_definitions: |
          [
            {
              "name": "frontend",
              "image": "${deps.containers-images.repository_info.frontend_repo_url}:latest",
              "cpu": ${config.frontend_cpu},
              "memory": ${config.frontend_memory},
              "essential": true,
              "portMappings": [
                {
                  "containerPort": 3000,
                  "protocol": "tcp"
                }
              ],
              "environment": [
                {
                  "name": "NODE_ENV",
                  "value": "${config.environment}"
                },
                {
                  "name": "API_URL",
                  "value": "https://api.${var.domain}"
                }
              ],
              "secrets": [
                {
                  "name": "JWT_SECRET",
                  "valueFrom": "${deps.secrets.secret_arns.jwt_signing_key_arn}"
                }
              ],
              "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                  "awslogs-group": "${resources.cloudwatch_log_groups.frontend_logs.name}",
                  "awslogs-region": "${var.region}",
                  "awslogs-stream-prefix": "ecs"
                }
              }
            }
          ]

    target_groups:
      frontend_tg:
        name: "${config.project}-${config.environment}-frontend-tg"
        port: 3000
        protocol: "HTTP"
        vpc_id: "${deps.network.vpc_info.vpc_id}"
        target_type: "ip"
        health_check:
          enabled: true
          healthy_threshold: 2
          unhealthy_threshold: 3
          timeout: 5
          interval: 30
          path: "/health"
          matcher: "200"
        tags:
          Name: "${config.project}-${config.environment}-frontend-tg"
          Environment: "${config.environment}"

    cloudwatch_log_groups:
      frontend_logs:
        name: "/ecs/${config.project}-${config.environment}-frontend"
        retention_in_days: "${config.log_retention_days}"
        kms_key_id: "${deps.security.kms_key_ids.application_key_arn}"

    service_discovery:
      namespace:
        name: "${config.project}-${config.environment}.local"
        vpc: "${deps.network.vpc_info.vpc_id}"
        description: "Service discovery namespace for ${config.project}"

      frontend_service:
        name: "frontend"
        namespace_id: "${resources.service_discovery.namespace.id}"
        dns_config:
          namespace_id: "${resources.service_discovery.namespace.id}"
          dns_records:
            - ttl: 10
              type: "A"

  outputs:
    load_balancer_info:
      public_alb_dns_name:
        description: "Public ALB DNS name"
        value: "${resources.load_balancers.public_alb.dns_name}"

      public_alb_zone_id:
        description: "Public ALB zone ID"
        value: "${resources.load_balancers.public_alb.zone_id}"

      public_alb_arn:
        description: "Public ALB ARN"
        value: "${resources.load_balancers.public_alb.arn}"

    cluster_info:
      cluster_id:
        description: "ECS cluster ID"
        value: "${resources.ecs_cluster.main_cluster.id}"

      cluster_arn:
        description: "ECS cluster ARN"
        value: "${resources.ecs_cluster.main_cluster.arn}"

    service_info:
      frontend_service_name:
        description: "Frontend ECS service name"
        value: "${resources.ecs_services.frontend_service.name}"

      service_discovery_namespace_id:
        description: "Service discovery namespace ID"
        value: "${resources.service_discovery.namespace.id}"

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

    domain:
      type: string
      description: "Application domain name"
      required: true
      default: "${DEPLOY_DOMAIN}"

    frontend_desired_count:
      type: number
      description: "Desired number of frontend tasks"
      default: 2
      validation:
        minimum: 1
        maximum: 10

    frontend_cpu:
      type: number
      description: "Frontend task CPU units"
      default: 512

    frontend_memory:
      type: number
      description: "Frontend task memory in MB"
      default: 1024

    enable_deletion_protection:
      type: boolean
      description: "Enable deletion protection for load balancer"
      default: true

    log_retention_days:
      type: number
      description: "CloudWatch log retention in days"
      default: 30

  dependencies:
    outputs_required:
      - network.subnet_info.public_subnet_ids
      - network.subnet_info.private_subnet_ids
      - network.vpc_info.vpc_id
      - security.security_group_ids.load_balancer_sg_id
      - security.security_group_ids.web_application_sg_id
      - security.iam_role_arns.ecs_execution_role_arn
      - security.iam_role_arns.ecs_task_role_arn
      - containers-images.repository_info.frontend_repo_url
      - secrets.secret_arns.jwt_signing_key_arn

  tags:
    - containers
    - ecs
    - applications
    - load-balancer
    - microservices
```