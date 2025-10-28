```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: compute-lambda
  version: v1
  description: Lambda functions, serverless compute, event processing, and function orchestration
  language: typescript
  priority: 150

spec:
  dependencies:
    - network
    - security
    - storage
    - database-rds

  resources:
    lambda:
      layers:
        shared_dependencies:
          layer_name: "${config.project}-${config.environment}-shared-deps"
          description: "Shared dependencies layer for Lambda functions"
          compatible_runtimes: ["nodejs18.x", "nodejs16.x"]
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-layers/shared-dependencies.zip"

        utilities_layer:
          layer_name: "${config.project}-${config.environment}-utilities"
          description: "Common utilities and helper functions"
          compatible_runtimes: ["nodejs18.x", "nodejs16.x"]
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-layers/utilities.zip"

      functions:
        api_processor:
          function_name: "${config.project}-${config.environment}-api-processor"
          description: "Processes API requests and responses"
          runtime: "nodejs18.x"
          handler: "src/handlers/api-processor.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/api-processor.zip"
          timeout: 30
          memory_size: 512
          layers:
            - "${resources.lambda.layers.shared_dependencies.arn}"
            - "${resources.lambda.layers.utilities_layer.arn}"
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              DATABASE_URL: "${deps.database_rds.connection_string}"
              S3_BUCKET: "${deps.storage.primary_bucket_name}"
          vpc_config:
            subnet_ids: "${deps.network.private_subnet_ids}"
            security_group_ids: ["${deps.security.lambda_sg_id}"]

        data_processor:
          function_name: "${config.project}-${config.environment}-data-processor"
          description: "Processes data transformation tasks"
          runtime: "nodejs18.x"
          handler: "src/handlers/data-processor.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/data-processor.zip"
          timeout: 300
          memory_size: 1024
          layers:
            - "${resources.lambda.layers.shared_dependencies.arn}"
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              DATABASE_URL: "${deps.database_rds.connection_string}"
          vpc_config:
            subnet_ids: "${deps.network.private_subnet_ids}"
            security_group_ids: ["${deps.security.lambda_sg_id}"]

        scheduler:
          function_name: "${config.project}-${config.environment}-scheduler"
          description: "Handles scheduled tasks and cron jobs"
          runtime: "nodejs18.x"
          handler: "src/handlers/scheduler.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/scheduler.zip"
          timeout: 600
          memory_size: 512
          layers:
            - "${resources.lambda.layers.shared_dependencies.arn}"
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              SQS_QUEUE_URL: "${resources.sqs.queues.task_queue.url}"

        notification_handler:
          function_name: "${config.project}-${config.environment}-notifications"
          description: "Processes notifications and alerts"
          runtime: "nodejs18.x"
          handler: "src/handlers/notifications.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/notifications.zip"
          timeout: 60
          memory_size: 256
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              SNS_TOPIC_ARN: "${resources.sns.topics.notifications.arn}"

        file_processor:
          function_name: "${config.project}-${config.environment}-file-processor"
          description: "Processes file uploads and transformations"
          runtime: "nodejs18.x"
          handler: "src/handlers/file-processor.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/file-processor.zip"
          timeout: 300
          memory_size: 2048
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              SOURCE_BUCKET: "${deps.storage.primary_bucket_name}"
              PROCESSED_BUCKET: "${deps.storage.static_assets_bucket_name}"

        auth_handler:
          function_name: "${config.project}-${config.environment}-auth-handler"
          description: "Custom authentication and authorization logic"
          runtime: "nodejs18.x"
          handler: "src/handlers/auth.handler"
          s3_bucket: "${deps.storage.artifacts_bucket_name}"
          s3_key: "lambda-functions/auth-handler.zip"
          timeout: 30
          memory_size: 256
          environment:
            variables:
              NODE_ENV: "${config.environment}"
              JWT_SECRET: "${deps.secrets.jwt_secret_arn}"

      permissions:
        api_gateway_invoke_api_processor:
          statement_id: "AllowExecutionFromAPIGateway"
          action: "lambda:InvokeFunction"
          function_name: "${resources.lambda.functions.api_processor.function_name}"
          principal: "apigateway.amazonaws.com"

        s3_invoke_file_processor:
          statement_id: "AllowExecutionFromS3"
          action: "lambda:InvokeFunction"
          function_name: "${resources.lambda.functions.file_processor.function_name}"
          principal: "s3.amazonaws.com"
          source_arn: "${deps.storage.primary_bucket_arn}"

        sns_invoke_notification:
          statement_id: "AllowExecutionFromSNS"
          action: "lambda:InvokeFunction"
          function_name: "${resources.lambda.functions.notification_handler.function_name}"
          principal: "sns.amazonaws.com"
          source_arn: "${resources.sns.topics.notifications.arn}"

      event_source_mappings:
        sqs_task_queue_mapping:
          event_source_arn: "${resources.sqs.queues.task_queue.arn}"
          function_name: "${resources.lambda.functions.data_processor.function_name}"
          batch_size: 10
          maximum_batching_window_in_seconds: 5

      function_urls:
        api_processor_url:
          function_name: "${resources.lambda.functions.api_processor.function_name}"
          authorization_type: "AWS_IAM"
          cors:
            allow_credentials: true
            allow_headers: ["date", "keep-alive"]
            allow_methods: ["*"]
            allow_origins: ["*"]
            expose_headers: ["date", "keep-alive"]
            max_age: 86400

    sqs:
      queues:
        task_queue:
          name: "${config.project}-${config.environment}-tasks"
          delay_seconds: 0
          max_message_size: 262144
          message_retention_seconds: 1209600 # 14 days
          visibility_timeout_seconds: 300
          redrive_policy:
            dead_letter_target_arn: "${resources.sqs.queues.task_dlq.arn}"
            max_receive_count: 3

        task_dlq:
          name: "${config.project}-${config.environment}-tasks-dlq"
          message_retention_seconds: 1209600 # 14 days

        notification_queue:
          name: "${config.project}-${config.environment}-notifications"
          delay_seconds: 0
          max_message_size: 262144
          message_retention_seconds: 345600 # 4 days
          visibility_timeout_seconds: 60

    sns:
      topics:
        notifications:
          name: "${config.project}-${config.environment}-notifications"
          display_name: "Application Notifications"

      subscriptions:
        notification_lambda:
          topic_arn: "${resources.sns.topics.notifications.arn}"
          protocol: "lambda"
          endpoint: "${resources.lambda.functions.notification_handler.arn}"

        notification_sqs:
          topic_arn: "${resources.sns.topics.notifications.arn}"
          protocol: "sqs"
          endpoint: "${resources.sqs.queues.notification_queue.arn}"

    eventbridge:
      rules:
        daily_scheduler:
          name: "${config.project}-${config.environment}-daily-scheduler"
          description: "Trigger daily scheduled tasks"
          schedule_expression: "cron(0 6 * * ? *)" # Daily at 6 AM UTC
          state: "ENABLED"

        hourly_cleanup:
          name: "${config.project}-${config.environment}-hourly-cleanup"
          description: "Trigger hourly cleanup tasks"
          schedule_expression: "rate(1 hour)"
          state: "ENABLED"

      targets:
        daily_scheduler_target:
          rule: "${resources.eventbridge.rules.daily_scheduler.name}"
          arn: "${resources.lambda.functions.scheduler.arn}"
          input: |
            {
              "task_type": "daily_maintenance",
              "environment": "${config.environment}"
            }

        hourly_cleanup_target:
          rule: "${resources.eventbridge.rules.hourly_cleanup.name}"
          arn: "${resources.lambda.functions.scheduler.arn}"
          input: |
            {
              "task_type": "cleanup",
              "environment": "${config.environment}"
            }

    step_functions:
      state_machines:
        data_pipeline:
          name: "${config.project}-${config.environment}-data-pipeline"
          role_arn: "${resources.iam.roles.step_functions_role.arn}"
          definition: |
            {
              "Comment": "Data processing pipeline",
              "StartAt": "ValidateInput",
              "States": {
                "ValidateInput": {
                  "Type": "Task",
                  "Resource": "${resources.lambda.functions.data_processor.arn}",
                  "Parameters": {
                    "action": "validate",
                    "input.$": "$"
                  },
                  "Next": "ProcessData",
                  "Catch": [
                    {
                      "ErrorEquals": ["ValidationError"],
                      "Next": "ValidationFailed"
                    }
                  ]
                },
                "ProcessData": {
                  "Type": "Task",
                  "Resource": "${resources.lambda.functions.data_processor.arn}",
                  "Parameters": {
                    "action": "process",
                    "input.$": "$"
                  },
                  "Next": "NotifyCompletion"
                },
                "NotifyCompletion": {
                  "Type": "Task",
                  "Resource": "${resources.lambda.functions.notification_handler.arn}",
                  "Parameters": {
                    "message": "Data processing completed successfully"
                  },
                  "End": true
                },
                "ValidationFailed": {
                  "Type": "Task",
                  "Resource": "${resources.lambda.functions.notification_handler.arn}",
                  "Parameters": {
                    "message": "Data validation failed"
                  },
                  "End": true
                }
              }
            }

    iam:
      roles:
        lambda_execution_role:
          name: "${config.project}-${config.environment}-lambda-execution"
          assume_role_policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": {
                    "Service": "lambda.amazonaws.com"
                  },
                  "Action": "sts:AssumeRole"
                }
              ]
            }
          managed_policy_arns:
            - "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
            - "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

        step_functions_role:
          name: "${config.project}-${config.environment}-step-functions"
          assume_role_policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": {
                    "Service": "states.amazonaws.com"
                  },
                  "Action": "sts:AssumeRole"
                }
              ]
            }

      policies:
        lambda_s3_policy:
          name: "${config.project}-${config.environment}-lambda-s3"
          policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                  ],
                  "Resource": [
                    "${deps.storage.primary_bucket_arn}/*",
                    "${deps.storage.static_assets_bucket_arn}/*",
                    "${deps.storage.artifacts_bucket_arn}/*"
                  ]
                }
              ]
            }

        lambda_sqs_policy:
          name: "${config.project}-${config.environment}-lambda-sqs"
          policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:SendMessage"
                  ],
                  "Resource": [
                    "${resources.sqs.queues.task_queue.arn}",
                    "${resources.sqs.queues.notification_queue.arn}"
                  ]
                }
              ]
            }

      role_policy_attachments:
        lambda_s3_attachment:
          role: "${resources.iam.roles.lambda_execution_role.name}"
          policy_arn: "${resources.iam.policies.lambda_s3_policy.arn}"

        lambda_sqs_attachment:
          role: "${resources.iam.roles.lambda_execution_role.name}"
          policy_arn: "${resources.iam.policies.lambda_sqs_policy.arn}"

    cloudwatch:
      log_groups:
        api_processor_logs:
          name: "/aws/lambda/${resources.lambda.functions.api_processor.function_name}"
          retention_in_days: 14

        data_processor_logs:
          name: "/aws/lambda/${resources.lambda.functions.data_processor.function_name}"
          retention_in_days: 14

        scheduler_logs:
          name: "/aws/lambda/${resources.lambda.functions.scheduler.function_name}"
          retention_in_days: 14

      metric_alarms:
        api_processor_errors:
          alarm_name: "${config.project}-${config.environment}-api-processor-errors"
          comparison_operator: "GreaterThanThreshold"
          evaluation_periods: 2
          metric_name: "Errors"
          namespace: "AWS/Lambda"
          period: 60
          statistic: "Sum"
          threshold: 5
          alarm_description: "API processor function error rate is too high"
          dimensions:
            FunctionName: "${resources.lambda.functions.api_processor.function_name}"

        api_processor_duration:
          alarm_name: "${config.project}-${config.environment}-api-processor-duration"
          comparison_operator: "GreaterThanThreshold"
          evaluation_periods: 2
          metric_name: "Duration"
          namespace: "AWS/Lambda"
          period: 60
          statistic: "Average"
          threshold: 25000 # 25 seconds
          alarm_description: "API processor function duration is too high"
          dimensions:
            FunctionName: "${resources.lambda.functions.api_processor.function_name}"

  outputs:
    lambda_info:
      api_processor_arn:
        description: "API processor Lambda function ARN"
        value: "${resources.lambda.functions.api_processor.arn}"

      data_processor_arn:
        description: "Data processor Lambda function ARN"
        value: "${resources.lambda.functions.data_processor.arn}"

      scheduler_arn:
        description: "Scheduler Lambda function ARN"
        value: "${resources.lambda.functions.scheduler.arn}"

      api_processor_function_url:
        description: "API processor function URL"
        value: "${resources.lambda.function_urls.api_processor_url.function_url}"

    queues_info:
      task_queue_url:
        description: "Task processing queue URL"
        value: "${resources.sqs.queues.task_queue.url}"

      task_queue_arn:
        description: "Task processing queue ARN"
        value: "${resources.sqs.queues.task_queue.arn}"

      notification_queue_url:
        description: "Notification queue URL"
        value: "${resources.sqs.queues.notification_queue.url}"

    topics_info:
      notifications_topic_arn:
        description: "Notifications topic ARN"
        value: "${resources.sns.topics.notifications.arn}"

    step_functions_info:
      data_pipeline_arn:
        description: "Data pipeline state machine ARN"
        value: "${resources.step_functions.state_machines.data_pipeline.arn}"

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

    lambda_timeout_default:
      type: number
      description: "Default timeout for Lambda functions (seconds)"
      default: 30
      validation:
        minimum: 3
        maximum: 900

    lambda_memory_default:
      type: number
      description: "Default memory allocation for Lambda functions (MB)"
      default: 512
      validation:
        minimum: 128
        maximum: 10240

    enable_vpc_config:
      type: boolean
      description: "Enable VPC configuration for Lambda functions"
      default: true

    log_retention_days:
      type: number
      description: "CloudWatch log retention period (days)"
      default: 14
      validation:
        allowed_values: [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]

  dependencies:
    outputs_required:
      - network.vpc_id
      - network.private_subnet_ids
      - security.lambda_sg_id
      - storage.primary_bucket_name
      - storage.primary_bucket_arn
      - storage.static_assets_bucket_name
      - storage.static_assets_bucket_arn
      - storage.artifacts_bucket_name
      - storage.artifacts_bucket_arn
      - database_rds.connection_string
      - secrets.jwt_secret_arn

  tags:
    - lambda
    - serverless
    - compute
    - events
    - processing
    - microservices
```