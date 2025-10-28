```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: secrets
  version: v1
  description: Secrets management with AWS Secrets Manager
  language: typescript
  priority: 40

spec:
  dependencies:
    - security

  resources:
    secrets:
      database_master_password:
        name: "${config.project}/${config.environment}/database/master-password"
        description: "Database master user password"
        generate_secret_string:
          secret_string_template: '{"username": "postgres"}'
          generate_string_key: "password"
          exclude_characters: '"@/\'
          password_length: 32
        kms_key_id: "${deps.security.kms_key_ids.database_key_id}"

      database_readonly_password:
        name: "${config.project}/${config.environment}/database/readonly-password"
        description: "Database read-only user password"
        generate_secret_string:
          secret_string_template: '{"username": "readonly"}'
          generate_string_key: "password"
          exclude_characters: '"@/\'
          password_length: 32
        kms_key_id: "${deps.security.kms_key_ids.database_key_id}"

      jwt_signing_key:
        name: "${config.project}/${config.environment}/auth/jwt-signing-key"
        description: "JWT token signing key"
        secret_string: "${random.jwt_key}"
        kms_key_id: "${deps.security.kms_key_ids.application_key_id}"

      session_secret:
        name: "${config.project}/${config.environment}/auth/session-secret"
        description: "Session encryption secret"
        generate_secret_string:
          password_length: 64
          exclude_characters: '"@/\'
        kms_key_id: "${deps.security.kms_key_ids.application_key_id}"

      external_api_keys:
        name: "${config.project}/${config.environment}/external/api-keys"
        description: "External service API keys"
        secret_string: |
          {
            "stripe_secret_key": "${var.stripe_secret_key}",
            "sendgrid_api_key": "${var.sendgrid_api_key}",
            "github_client_secret": "${var.github_client_secret}",
            "google_client_secret": "${var.google_client_secret}"
          }
        kms_key_id: "${deps.security.kms_key_ids.application_key_id}"

      redis_password:
        name: "${config.project}/${config.environment}/cache/redis-password"
        description: "Redis authentication password"
        generate_secret_string:
          password_length: 32
          exclude_characters: '"@/\'
        kms_key_id: "${deps.security.kms_key_ids.application_key_id}"

    secret_rotation:
      database_master_rotation:
        secret_id: "${resources.secrets.database_master_password.id}"
        automatically_after_days: 30
        rotation_lambda_arn: "${resources.lambda_functions.db_rotation_lambda.arn}"

      database_readonly_rotation:
        secret_id: "${resources.secrets.database_readonly_password.id}"
        automatically_after_days: 30
        rotation_lambda_arn: "${resources.lambda_functions.db_rotation_lambda.arn}"

    lambda_functions:
      db_rotation_lambda:
        function_name: "${config.project}-${config.environment}-db-rotation"
        runtime: "python3.9"
        handler: "lambda_function.lambda_handler"
        role_arn: "${resources.iam_roles.lambda_rotation_role.arn}"
        timeout: 30
        environment_variables:
          SECRET_ARN: "${resources.secrets.database_master_password.arn}"

    iam_policies:
      secrets_read_policy:
        name: "${config.project}-${config.environment}-secrets-read"
        description: "Read access to application secrets"
        policy_document: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Action": [
                  "secretsmanager:GetSecretValue",
                  "secretsmanager:DescribeSecret"
                ],
                "Resource": [
                  "${resources.secrets.jwt_signing_key.arn}",
                  "${resources.secrets.session_secret.arn}",
                  "${resources.secrets.external_api_keys.arn}",
                  "${resources.secrets.redis_password.arn}"
                ]
              }
            ]
          }

      secrets_rotation_policy:
        name: "${config.project}-${config.environment}-secrets-rotation"
        description: "Rotation access for database secrets"
        policy_document: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Action": [
                  "secretsmanager:RotateSecret",
                  "secretsmanager:GetSecretValue",
                  "secretsmanager:PutSecretValue",
                  "secretsmanager:UpdateSecretVersionStage"
                ],
                "Resource": [
                  "${resources.secrets.database_master_password.arn}",
                  "${resources.secrets.database_readonly_password.arn}"
                ]
              }
            ]
          }

  outputs:
    secret_arns:
      database_master_password_arn:
        description: "Database master password secret ARN"
        value: "${resources.secrets.database_master_password.arn}"

      database_readonly_password_arn:
        description: "Database readonly password secret ARN"
        value: "${resources.secrets.database_readonly_password.arn}"

      jwt_signing_key_arn:
        description: "JWT signing key secret ARN"
        value: "${resources.secrets.jwt_signing_key.arn}"

      session_secret_arn:
        description: "Session secret ARN"
        value: "${resources.secrets.session_secret.arn}"

      external_api_keys_arn:
        description: "External API keys secret ARN"
        value: "${resources.secrets.external_api_keys.arn}"

      redis_password_arn:
        description: "Redis password secret ARN"
        value: "${resources.secrets.redis_password.arn}"

    iam_policy_arns:
      secrets_read_policy_arn:
        description: "Secrets read policy ARN"
        value: "${resources.iam_policies.secrets_read_policy.arn}"

      secrets_rotation_policy_arn:
        description: "Secrets rotation policy ARN"
        value: "${resources.iam_policies.secrets_rotation_policy.arn}"

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

    enable_automatic_rotation:
      type: boolean
      description: "Enable automatic secret rotation"
      default: true

    rotation_interval_days:
      type: number
      description: "Secret rotation interval in days"
      default: 30
      validation:
        minimum: 7
        maximum: 90

  dependencies:
    outputs_required:
      - security.kms_key_ids.application_key_id
      - security.kms_key_ids.database_key_id

  tags:
    - secrets
    - security
    - encryption
    - rotation
    - credentials
```