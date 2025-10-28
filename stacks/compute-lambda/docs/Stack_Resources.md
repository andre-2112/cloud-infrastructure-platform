# AWS Resources for Compute Lambda Stack

## Lambda Function Resources
- **aws.lambda.Function** - API processing functions
- **aws.lambda.Function** - Data processing functions
- **aws.lambda.Function** - Background job functions
- **aws.lambda.Function** - Scheduled task functions
- **aws.lambda.Function** - Event-driven functions
- **aws.lambda.Function** - Authentication functions
- **aws.lambda.Function** - File processing functions
- **aws.lambda.Function** - Notification functions

## Lambda Layer Resources
- **aws.lambda.LayerVersion** - Shared libraries layer
- **aws.lambda.LayerVersion** - Dependencies layer
- **aws.lambda.LayerVersion** - Runtime utilities layer

## Lambda Permission Resources
- **aws.lambda.Permission** - API Gateway invoke permissions
- **aws.lambda.Permission** - S3 event permissions
- **aws.lambda.Permission** - DynamoDB stream permissions
- **aws.lambda.Permission** - EventBridge permissions
- **aws.lambda.Permission** - SQS trigger permissions
- **aws.lambda.Permission** - SNS trigger permissions

## Lambda Event Source Mapping
- **aws.lambda.EventSourceMapping** - DynamoDB stream triggers
- **aws.lambda.EventSourceMapping** - Kinesis stream triggers
- **aws.lambda.EventSourceMapping** - SQS queue triggers

## Lambda Function URL Resources
- **aws.lambda.FunctionUrl** - HTTP endpoints for functions

## Application Load Balancer Integration
- **aws.lb.TargetGroup** - Lambda target groups for ALB
- **aws.lb.TargetGroupAttachment** - Lambda function attachments

## CloudWatch Resources
- **aws.cloudwatch.LogGroup** - Lambda function log groups
- **aws.cloudwatch.MetricAlarm** - Function duration alarms
- **aws.cloudwatch.MetricAlarm** - Function error rate alarms
- **aws.cloudwatch.MetricAlarm** - Function throttle alarms
- **aws.cloudwatch.Dashboard** - Lambda monitoring dashboard

## EventBridge Resources
- **aws.cloudwatch.EventRule** - Scheduled event rules
- **aws.cloudwatch.EventRule** - Custom event rules
- **aws.cloudwatch.EventTarget** - Lambda function targets

## SQS Resources
- **aws.sqs.Queue** - Processing queues for async operations
- **aws.sqs.Queue** - Dead letter queues for failed messages
- **aws.sqs.QueuePolicy** - Queue access policies

## SNS Resources
- **aws.sns.Topic** - Notification topics
- **aws.sns.TopicSubscription** - Lambda function subscriptions
- **aws.sns.TopicPolicy** - Topic access policies

## Step Functions Resources (Optional)
- **aws.sfn.StateMachine** - Workflow orchestration
- **aws.sfn.Activity** - Manual activities

## DynamoDB Resources (for Lambda state)
- **aws.dynamodb.Table** - Function state table
- **aws.dynamodb.Table** - Configuration table

## VPC Configuration Resources
- **aws.lambda.Function** - VPC configuration for database access

## X-Ray Resources
- **aws.xray.SamplingRule** - Distributed tracing configuration

## Systems Manager Resources
- **aws.ssm.Parameter** - Function configuration parameters
- **aws.ssm.Parameter** - Environment variables

## Secrets Manager Resources
- **aws.secretsmanager.Secret** - Function-specific secrets

## KMS Resources
- **aws.kms.Key** - Function-specific encryption keys

## Estimated Resource Count: 50 resources
## Estimated Monthly Cost: $10-100 (depending on function execution volume)

## Resource Dependencies
- Depends on: network, security, storage, database-rds
- Used by: services-api, services-auth, services-webapp