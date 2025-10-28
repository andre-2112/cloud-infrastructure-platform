```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: services-ecs
  version: v1
  description: ECS orchestration services with auto-scaling and service discovery
  language: typescript
  priority: 110

spec:
  dependencies:
    - network
    - security
    - services-ecr

  resources:
    ecs_cluster:
      services_cluster:
        name: "${config.project}-${config.environment}-services"
        capacity_providers: ["FARGATE", "FARGATE_SPOT"]
        default_capacity_provider_strategy:
          - capacity_provider: "FARGATE"
            weight: 50
            base: 2
          - capacity_provider: "FARGATE_SPOT"
            weight: 50
        setting:
          - name: "containerInsights"
            value: "enabled"
        tags:
          Name: "${config.project}-${config.environment}-services-cluster"
          Environment: "${config.environment}"

    auto_scaling_targets:
      api_service_target:
        max_capacity: "${config.api_max_capacity}"
        min_capacity: "${config.api_min_capacity}"
        resource_id: "service/${resources.ecs_cluster.services_cluster.name}/${config.project}-${config.environment}-api"
        scalable_dimension: "ecs:service:DesiredCount"
        service_namespace: "ecs"

    auto_scaling_policies:
      cpu_scaling_policy:
        name: "${config.project}-${config.environment}-cpu-scaling"
        resource_id: "${resources.auto_scaling_targets.api_service_target.resource_id}"
        scalable_dimension: "${resources.auto_scaling_targets.api_service_target.scalable_dimension}"
        service_namespace: "${resources.auto_scaling_targets.api_service_target.service_namespace}"
        policy_type: "TargetTrackingScaling"
        target_tracking_scaling_policy_configuration:
          predefined_metric_specification:
            predefined_metric_type: "ECSServiceAverageCPUUtilization"
          target_value: 70.0
          scale_out_cooldown: 300
          scale_in_cooldown: 300

    service_discovery:
      private_namespace:
        name: "${config.project}-${config.environment}.internal"
        vpc: "${deps.network.vpc_info.vpc_id}"
        description: "Private DNS namespace for ECS services"

  outputs:
    cluster_info:
      services_cluster_id:
        description: "ECS services cluster ID"
        value: "${resources.ecs_cluster.services_cluster.id}"

      services_cluster_arn:
        description: "ECS services cluster ARN"
        value: "${resources.ecs_cluster.services_cluster.arn}"

    service_discovery_info:
      private_namespace_id:
        description: "Private DNS namespace ID"
        value: "${resources.service_discovery.private_namespace.id}"

      private_namespace_name:
        description: "Private DNS namespace name"
        value: "${resources.service_discovery.private_namespace.name}"

    auto_scaling_info:
      api_scaling_target_arn:
        description: "API service auto scaling target ARN"
        value: "${resources.auto_scaling_targets.api_service_target.arn}"

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

    api_min_capacity:
      type: number
      description: "Minimum API service capacity"
      default: 2

    api_max_capacity:
      type: number
      description: "Maximum API service capacity"
      default: 10

    enable_container_insights:
      type: boolean
      description: "Enable CloudWatch Container Insights"
      default: true

    cpu_target_utilization:
      type: number
      description: "Target CPU utilization for auto scaling"
      default: 70
      validation:
        minimum: 10
        maximum: 90

  dependencies:
    outputs_required:
      - network.vpc_info.vpc_id
      - security.iam_role_arns.ecs_execution_role_arn
      - security.iam_role_arns.ecs_task_role_arn

  tags:
    - ecs
    - orchestration
    - auto-scaling
    - service-discovery
    - microservices
```