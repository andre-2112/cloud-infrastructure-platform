```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: security
  version: v1
  description: Security infrastructure with IAM roles, security groups, and KMS keys
  language: typescript
  priority: 30

spec:
  dependencies:
    - network

  resources:
    security_groups:
      load_balancer_sg:
        name: "${config.project}-${config.environment}-alb-sg"
        description: "Load balancer security group"
        vpc_id: "${deps.network.vpc_info.vpc_id}"
        ingress_rules:
          - from_port: 80
            to_port: 80
            protocol: "tcp"
            cidr_blocks: ["0.0.0.0/0"]
          - from_port: 443
            to_port: 443
            protocol: "tcp"
            cidr_blocks: ["0.0.0.0/0"]

      web_application_sg:
        name: "${config.project}-${config.environment}-web-sg"
        description: "Web application security group"
        vpc_id: "${deps.network.vpc_info.vpc_id}"
        ingress_rules:
          - from_port: 3000
            to_port: 3000
            protocol: "tcp"
            source_security_group_id: "${resources.security_groups.load_balancer_sg.id}"

      api_application_sg:
        name: "${config.project}-${config.environment}-api-sg"
        description: "API application security group"
        vpc_id: "${deps.network.vpc_info.vpc_id}"
        ingress_rules:
          - from_port: 8080
            to_port: 8080
            protocol: "tcp"
            source_security_group_id: "${resources.security_groups.load_balancer_sg.id}"

      database_sg:
        name: "${config.project}-${config.environment}-db-sg"
        description: "Database security group"
        vpc_id: "${deps.network.vpc_info.vpc_id}"
        ingress_rules:
          - from_port: 5432
            to_port: 5432
            protocol: "tcp"
            source_security_group_id: "${resources.security_groups.api_application_sg.id}"

    iam_roles:
      ecs_execution_role:
        name: "${config.project}-${config.environment}-ecs-execution-role"
        assume_role_policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }
        managed_policy_arns:
          - "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

      ecs_task_role:
        name: "${config.project}-${config.environment}-ecs-task-role"
        assume_role_policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }

      eks_cluster_role:
        name: "${config.project}-${config.environment}-eks-cluster-role"
        assume_role_policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "eks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }
        managed_policy_arns:
          - "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"

    kms_keys:
      application_key:
        name: "${config.project}-${config.environment}-app-key"
        description: "Application encryption key"
        deletion_window_in_days: 30
        enable_key_rotation: true
        policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Sid": "Enable IAM User Permissions",
                "Effect": "Allow",
                "Principal": {
                  "AWS": "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
                },
                "Action": "kms:*",
                "Resource": "*"
              }
            ]
          }

      database_key:
        name: "${config.project}-${config.environment}-db-key"
        description: "Database encryption key"
        deletion_window_in_days: 30
        enable_key_rotation: true

      infrastructure_key:
        name: "${config.project}-${config.environment}-infra-key"
        description: "Infrastructure encryption key"
        deletion_window_in_days: 30
        enable_key_rotation: true

    kms_aliases:
      app_key_alias:
        name: "alias/${config.project}-${config.environment}-app-key"
        target_key_id: "${resources.kms_keys.application_key.key_id}"

      db_key_alias:
        name: "alias/${config.project}-${config.environment}-db-key"
        target_key_id: "${resources.kms_keys.database_key.key_id}"

      infra_key_alias:
        name: "alias/${config.project}-${config.environment}-infra-key"
        target_key_id: "${resources.kms_keys.infrastructure_key.key_id}"

  outputs:
    security_group_ids:
      load_balancer_sg_id:
        description: "Load balancer security group ID"
        value: "${resources.security_groups.load_balancer_sg.id}"

      web_application_sg_id:
        description: "Web application security group ID"
        value: "${resources.security_groups.web_application_sg.id}"

      api_application_sg_id:
        description: "API application security group ID"
        value: "${resources.security_groups.api_application_sg.id}"

      database_sg_id:
        description: "Database security group ID"
        value: "${resources.security_groups.database_sg.id}"

    iam_role_arns:
      ecs_execution_role_arn:
        description: "ECS execution role ARN"
        value: "${resources.iam_roles.ecs_execution_role.arn}"

      ecs_task_role_arn:
        description: "ECS task role ARN"
        value: "${resources.iam_roles.ecs_task_role.arn}"

      eks_cluster_role_arn:
        description: "EKS cluster role ARN"
        value: "${resources.iam_roles.eks_cluster_role.arn}"

    kms_key_ids:
      application_key_id:
        description: "Application KMS key ID"
        value: "${resources.kms_keys.application_key.key_id}"

      application_key_arn:
        description: "Application KMS key ARN"
        value: "${resources.kms_keys.application_key.arn}"

      database_key_id:
        description: "Database KMS key ID"
        value: "${resources.kms_keys.database_key.key_id}"

      database_key_arn:
        description: "Database KMS key ARN"
        value: "${resources.kms_keys.database_key.arn}"

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

    enable_key_rotation:
      type: boolean
      description: "Enable automatic KMS key rotation"
      default: true

    key_deletion_window:
      type: number
      description: "KMS key deletion window in days"
      default: 30
      validation:
        minimum: 7
        maximum: 30

  dependencies:
    outputs_required:
      - network.vpc_info.vpc_id

  tags:
    - security
    - iam
    - kms
    - security-groups
    - encryption
```