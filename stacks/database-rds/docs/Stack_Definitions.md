```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: database-rds
  version: v1
  description: PostgreSQL RDS database with high availability and backups
  language: typescript
  priority: 70

spec:
  dependencies:
    - network
    - security
    - secrets

  resources:
    rds_subnet_group:
      main_db_subnet_group:
        name: "${config.project}-${config.environment}-db-subnet-group"
        subnet_ids: "${deps.network.subnet_info.database_subnet_ids}"
        tags:
          Name: "${config.project}-${config.environment}-db-subnet-group"
          Environment: "${config.environment}"

    rds_instance:
      primary_database:
        identifier: "${config.project}-${config.environment}-primary"
        engine: "postgres"
        engine_version: "${config.postgres_version}"
        instance_class: "${config.db_instance_class}"
        allocated_storage: "${config.db_allocated_storage}"
        max_allocated_storage: "${config.db_max_allocated_storage}"
        storage_type: "gp3"
        storage_encrypted: true
        kms_key_id: "${deps.security.kms_key_ids.database_key_arn}"
        db_subnet_group_name: "${resources.rds_subnet_group.main_db_subnet_group.name}"
        vpc_security_group_ids:
          - "${deps.security.security_group_ids.database_sg_id}"
        manage_master_user_password: true
        master_user_secret_kms_key_id: "${deps.security.kms_key_ids.database_key_id}"
        backup_retention_period: "${config.backup_retention_days}"
        backup_window: "${config.backup_window}"
        maintenance_window: "${config.maintenance_window}"
        auto_minor_version_upgrade: "${config.auto_minor_version_upgrade}"
        deletion_protection: "${config.deletion_protection}"
        skip_final_snapshot: false
        final_snapshot_identifier: "${config.project}-${config.environment}-final-snapshot-${timestamp}"
        performance_insights_enabled: true
        monitoring_interval: 60
        monitoring_role_arn: "${resources.iam_roles.rds_monitoring_role.arn}"
        tags:
          Name: "${config.project}-${config.environment}-primary-db"
          Environment: "${config.environment}"

      read_replica:
        identifier: "${config.project}-${config.environment}-replica"
        replicate_source_db: "${resources.rds_instance.primary_database.identifier}"
        instance_class: "${config.replica_instance_class}"
        storage_encrypted: true
        performance_insights_enabled: true
        monitoring_interval: 60
        monitoring_role_arn: "${resources.iam_roles.rds_monitoring_role.arn}"
        condition: "${config.create_read_replica}"
        tags:
          Name: "${config.project}-${config.environment}-replica-db"
          Environment: "${config.environment}"

    rds_parameter_group:
      postgres_params:
        name: "${config.project}-${config.environment}-postgres-params"
        family: "postgres${split('.', config.postgres_version)[0]}"
        description: "PostgreSQL parameter group for ${config.project}"
        parameters:
          - name: "shared_preload_libraries"
            value: "pg_stat_statements"
          - name: "log_statement"
            value: "all"
          - name: "log_min_duration_statement"
            value: "1000"
        tags:
          Name: "${config.project}-${config.environment}-postgres-params"
          Environment: "${config.environment}"

    cloudwatch_log_groups:
      postgres_logs:
        name: "/aws/rds/instance/${resources.rds_instance.primary_database.identifier}/postgresql"
        retention_in_days: "${config.log_retention_days}"
        kms_key_id: "${deps.security.kms_key_ids.infrastructure_key_arn}"

    iam_roles:
      rds_monitoring_role:
        name: "${config.project}-${config.environment}-rds-monitoring-role"
        assume_role_policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "monitoring.rds.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }
        managed_policy_arns:
          - "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"

  outputs:
    database_info:
      primary_endpoint:
        description: "RDS primary database endpoint"
        value: "${resources.rds_instance.primary_database.endpoint}"

      primary_port:
        description: "RDS primary database port"
        value: "${resources.rds_instance.primary_database.port}"

      replica_endpoint:
        description: "RDS read replica endpoint"
        value: "${config.create_read_replica ? resources.rds_instance.read_replica.endpoint : null}"

      database_name:
        description: "Default database name"
        value: "${resources.rds_instance.primary_database.db_name}"

    connection_info:
      master_user_secret_arn:
        description: "Master user credentials secret ARN"
        value: "${resources.rds_instance.primary_database.master_user_secret[0].secret_arn}"

      subnet_group_name:
        description: "Database subnet group name"
        value: "${resources.rds_subnet_group.main_db_subnet_group.name}"

      security_group_id:
        description: "Database security group ID"
        value: "${deps.security.security_group_ids.database_sg_id}"

    monitoring_info:
      parameter_group_name:
        description: "Database parameter group name"
        value: "${resources.rds_parameter_group.postgres_params.name}"

      log_group_name:
        description: "CloudWatch log group name"
        value: "${resources.cloudwatch_log_groups.postgres_logs.name}"

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

    postgres_version:
      type: string
      description: "PostgreSQL engine version"
      default: "15.4"

    db_instance_class:
      type: string
      description: "RDS instance class"
      default: "db.t3.medium"

    replica_instance_class:
      type: string
      description: "Read replica instance class"
      default: "db.t3.small"

    db_allocated_storage:
      type: number
      description: "Allocated storage in GB"
      default: 100
      validation:
        minimum: 20
        maximum: 65536

    db_max_allocated_storage:
      type: number
      description: "Maximum allocated storage for autoscaling in GB"
      default: 1000

    create_read_replica:
      type: boolean
      description: "Create read replica for production workloads"
      default: false

    backup_retention_days:
      type: number
      description: "Backup retention period in days"
      default: 7
      validation:
        minimum: 1
        maximum: 35

    backup_window:
      type: string
      description: "Backup window in UTC"
      default: "03:00-04:00"

    maintenance_window:
      type: string
      description: "Maintenance window in UTC"
      default: "sun:04:00-sun:05:00"

    auto_minor_version_upgrade:
      type: boolean
      description: "Enable automatic minor version upgrades"
      default: true

    deletion_protection:
      type: boolean
      description: "Enable deletion protection"
      default: true

    log_retention_days:
      type: number
      description: "CloudWatch log retention in days"
      default: 30

  dependencies:
    outputs_required:
      - network.subnet_info.database_subnet_ids
      - security.security_group_ids.database_sg_id
      - security.kms_key_ids.database_key_id
      - security.kms_key_ids.database_key_arn

  tags:
    - database
    - postgresql
    - rds
    - storage
    - backup
    - monitoring
```