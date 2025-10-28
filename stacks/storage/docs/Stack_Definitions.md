```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: storage
  version: v1
  description: S3 buckets, EBS volumes, EFS file systems, and backup storage
  language: typescript
  priority: 60

spec:
  dependencies:
    - network
    - security

  resources:
    s3:
      buckets:
        primary_storage:
          name: "${config.project}-${config.environment}-primary-storage"
          versioning: true
          encryption:
            kms_key_id: "${deps.security.storage_key_id}"
          public_access_block: true
          lifecycle_rules:
            - id: "transition_to_ia"
              status: "Enabled"
              transitions:
                - days: 30
                  storage_class: "STANDARD_IA"
            - id: "transition_to_glacier"
              status: "Enabled"
              transitions:
                - days: 90
                  storage_class: "GLACIER"

        static_assets:
          name: "${config.project}-${config.environment}-static-assets"
          versioning: false
          encryption:
            kms_key_id: "${deps.security.storage_key_id}"
          cors_configuration:
            allowed_origins: ["https://${config.domain}"]
            allowed_methods: ["GET", "HEAD"]
            allowed_headers: ["*"]
            max_age_seconds: 3600

        logs_storage:
          name: "${config.project}-${config.environment}-logs"
          versioning: true
          encryption:
            kms_key_id: "${deps.security.storage_key_id}"
          lifecycle_rules:
            - id: "expire_logs"
              status: "Enabled"
              expiration:
                days: 90

        backup_storage:
          name: "${config.project}-${config.environment}-backups"
          versioning: true
          encryption:
            kms_key_id: "${deps.security.storage_key_id}"
          lifecycle_rules:
            - id: "archive_backups"
              status: "Enabled"
              transitions:
                - days: 7
                  storage_class: "GLACIER"

        artifacts_storage:
          name: "${config.project}-${config.environment}-artifacts"
          versioning: true
          encryption:
            kms_key_id: "${deps.security.storage_key_id}"

    vpc_endpoints:
      s3_endpoint:
        service_name: "com.amazonaws.${config.region}.s3"
        vpc_id: "${deps.network.vpc_id}"
        route_table_ids: "${deps.network.private_route_table_ids}"
        policy_document:
          Version: "2012-10-17"
          Statement:
            - Effect: "Allow"
              Principal: "*"
              Action: "s3:*"
              Resource: "*"

    efs:
      file_systems:
        shared_storage:
          name: "${config.project}-${config.environment}-shared-efs"
          performance_mode: "generalPurpose"
          throughput_mode: "provisioned"
          provisioned_throughput_in_mibps: 100
          encrypted: true
          kms_key_id: "${deps.security.storage_key_id}"

      mount_targets:
        shared_storage_mounts:
          file_system_ref: shared_storage
          subnet_ids: "${deps.network.private_subnet_ids}"
          security_group_ids: ["${deps.security.efs_sg_id}"]

      access_points:
        app_access_point:
          file_system_ref: shared_storage
          path: "/app-data"
          creation_info:
            owner_uid: 1001
            owner_gid: 1001
            permissions: 755

    backup:
      vault:
        primary_vault:
          name: "${config.project}-${config.environment}-backup-vault"
          kms_key_arn: "${deps.security.backup_key_arn}"

      plans:
        daily_backup:
          name: "${config.project}-${config.environment}-daily-backup"
          vault_ref: primary_vault
          rules:
            - rule_name: "daily_backups"
              target_vault: primary_vault
              schedule: "cron(0 5 ? * * *)"
              lifecycle:
                delete_after_days: 30
                move_to_cold_storage_after_days: 7

      selections:
        ebs_selection:
          plan_ref: daily_backup
          resources:
            - "arn:aws:ec2:*:*:volume/*"
          conditions:
            - key: "aws:ResourceTag/Backup"
              value: "Required"
              condition_type: "STRINGEQUALS"

  outputs:
    storage_info:
      primary_bucket_name:
        description: "Primary storage bucket name"
        value: "${resources.s3.buckets.primary_storage.bucket}"

      primary_bucket_arn:
        description: "Primary storage bucket ARN"
        value: "${resources.s3.buckets.primary_storage.arn}"

      static_assets_bucket_name:
        description: "Static assets bucket name"
        value: "${resources.s3.buckets.static_assets.bucket}"

      static_assets_bucket_arn:
        description: "Static assets bucket ARN"
        value: "${resources.s3.buckets.static_assets.arn}"

      logs_bucket_name:
        description: "Logs storage bucket name"
        value: "${resources.s3.buckets.logs_storage.bucket}"

      backup_bucket_name:
        description: "Backup storage bucket name"
        value: "${resources.s3.buckets.backup_storage.bucket}"

      artifacts_bucket_name:
        description: "Artifacts storage bucket name"
        value: "${resources.s3.buckets.artifacts_storage.bucket}"

    efs_info:
      shared_efs_id:
        description: "Shared EFS file system ID"
        value: "${resources.efs.file_systems.shared_storage.id}"

      shared_efs_dns_name:
        description: "Shared EFS DNS name"
        value: "${resources.efs.file_systems.shared_storage.dns_name}"

      app_access_point_id:
        description: "Application access point ID"
        value: "${resources.efs.access_points.app_access_point.id}"

    backup_info:
      backup_vault_arn:
        description: "Backup vault ARN"
        value: "${resources.backup.vault.primary_vault.arn}"

      backup_plan_arn:
        description: "Daily backup plan ARN"
        value: "${resources.backup.plans.daily_backup.arn}"

    endpoints_info:
      s3_vpc_endpoint_id:
        description: "S3 VPC endpoint ID"
        value: "${resources.vpc_endpoints.s3_endpoint.id}"

  parameters:
    region:
      type: string
      description: "AWS region for deployment"
      required: true
      default: "${AWS_REGION}"

    project:
      type: string
      description: "Project name for resource naming"
      required: true
      default: "${PROJECT_NAME}"

    environment:
      type: string
      description: "Environment name (dev, stage, prod)"
      required: true
      validation:
        allowed_values: ["dev", "stage", "prod"]

    domain:
      type: string
      description: "Primary domain name"
      required: true
      default: "${DEPLOY_DOMAIN}"

    enable_backup:
      type: boolean
      description: "Enable automated backup services"
      default: true

    backup_retention_days:
      type: number
      description: "Number of days to retain backups"
      default: 30
      validation:
        minimum: 1
        maximum: 365

    efs_provisioned_throughput:
      type: number
      description: "EFS provisioned throughput in MiB/s"
      default: 100
      validation:
        minimum: 1
        maximum: 1024

  dependencies:
    outputs_required:
      - network.vpc_id
      - network.private_subnet_ids
      - network.private_route_table_ids
      - security.storage_key_id
      - security.storage_key_arn
      - security.backup_key_arn
      - security.efs_sg_id

  tags:
    - storage
    - s3
    - efs
    - backup
    - data
    - foundation
```