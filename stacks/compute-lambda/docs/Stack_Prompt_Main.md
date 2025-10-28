# Compute Lambda Stack Pulumi Generation Prompt

Create comprehensive Pulumi TypeScript code for serverless compute infrastructure including Lambda functions, event processing, orchestration, and supporting services for ${PROJECT_NAME}.

## Requirements

### Lambda Function Architecture
- **API Processing Functions**: Handle API requests with proper VPC configuration for database access
- **Data Processing Functions**: Transform and process data with higher memory and timeout configurations
- **Scheduled Functions**: Cron-based tasks using EventBridge rules for automation
- **Event-Driven Functions**: S3, SQS, SNS triggered functions for reactive processing
- **Authentication Functions**: Custom auth logic and JWT token processing
- **File Processing Functions**: Image/document processing with high memory allocation

### Serverless Infrastructure
- **Lambda Layers**: Shared dependencies and utilities to reduce deployment package size
- **Function URLs**: HTTP endpoints for specific functions with proper CORS configuration
- **SQS Integration**: Message queues for asynchronous processing with dead letter queues
- **SNS Integration**: Notification topics for fan-out messaging patterns
- **EventBridge Rules**: Scheduled and event-driven triggers with proper targeting

### Data Flow and Processing
- **Step Functions**: Orchestrate complex workflows with error handling and retries
- **Event Source Mappings**: Connect Lambda functions to SQS queues and other event sources
- **Batch Processing**: Handle batch operations efficiently with appropriate concurrency settings
- **Error Handling**: Comprehensive error handling with DLQs and alerting

### Dependencies and Integration
- **Network Stack**: VPC configuration for database and service access
- **Security Stack**: Lambda security groups, KMS keys for encryption
- **Storage Stack**: S3 bucket access for file processing and artifacts
- **Database Stack**: RDS connection for data persistence
- **Secrets Stack**: Secure access to JWT secrets and API keys
- **Centralized State**: Use shared state management for cross-stack communication

### Security and Performance
- **VPC Configuration**: Secure database access through private subnets
- **IAM Roles**: Function-specific roles with least-privilege access
- **Environment Variables**: Secure configuration management
- **Memory Optimization**: Appropriate memory allocation for each function type
- **Timeout Configuration**: Balanced timeout settings to prevent hanging functions

### Event Processing Architecture
```
API Gateway ’ Lambda (API Processor) ’ Database
S3 Events ’ Lambda (File Processor) ’ Processed Storage
SQS Queue ’ Lambda (Data Processor) ’ Database/Notification
EventBridge Schedule ’ Lambda (Scheduler) ’ SQS/SNS
SNS Topic ’ Lambda (Notification Handler) ’ External Services
```

### Environment Configuration
- **Development**: Generous timeouts, detailed logging, lower concurrency limits
- **Production**: Optimized timeouts, structured logging, auto-scaling enabled
- **Staging**: Balanced configuration for testing complex workflows

### Key Outputs Required
```typescript
export const apiProcessorArn = apiProcessor.arn;
export const dataProcessorArn = dataProcessor.arn;
export const schedulerArn = scheduler.arn;
export const fileProcessorArn = fileProcessor.arn;
export const authHandlerArn = authHandler.arn;
export const notificationHandlerArn = notificationHandler.arn;
export const apiProcessorFunctionUrl = apiProcessorUrl.functionUrl;
export const taskQueueUrl = taskQueue.url;
export const taskQueueArn = taskQueue.arn;
export const notificationQueueUrl = notificationQueue.url;
export const notificationsTopicArn = notificationsTopic.arn;
export const dataPipelineArn = dataPipeline.arn;
```

### Function Specifications
- **API Processor**: 512MB, 30s timeout, VPC enabled for DB access
- **Data Processor**: 1GB, 5min timeout, SQS event source mapping
- **File Processor**: 2GB, 5min timeout, S3 event triggers
- **Scheduler**: 512MB, 10min timeout, EventBridge scheduled triggers
- **Notification Handler**: 256MB, 1min timeout, SNS triggers
- **Auth Handler**: 256MB, 30s timeout, lightweight for JWT processing

### Monitoring and Observability
- **CloudWatch Logs**: Function-specific log groups with appropriate retention
- **CloudWatch Metrics**: Custom metrics for business logic monitoring
- **CloudWatch Alarms**: Error rate, duration, and throttle monitoring
- **X-Ray Tracing**: Distributed tracing for performance analysis
- **Custom Dashboards**: Function performance and error rate visualization

### Variables to Use
- **${DEPLOYMENT_ID}**: Unique deployment identifier
- **${PROJECT_NAME}**: Project name for resource naming and tagging
- **${DEPLOY_DOMAIN}**: Domain for CORS configuration
- **${AWS_REGION}**: Target AWS region for deployment
- **Environment-specific**: Use centralized state to determine dev/stage/prod configurations

### Integration Notes
- Configure appropriate reserved concurrency for critical functions
- Implement proper error handling with exponential backoff for retries
- Set up comprehensive logging with structured JSON for easy parsing
- Configure appropriate DLQ policies to prevent message loss
- Implement circuit breaker patterns for external service calls
- Use Lambda layers effectively to reduce deployment package sizes
- Configure appropriate timeout values based on function complexity
- Implement proper resource cleanup in function code
- Set up monitoring for cold start performance issues
- Configure appropriate memory settings based on function requirements

This stack provides the serverless compute foundation for event-driven architecture, enabling scalable, cost-effective processing of various workloads including API handling, data transformation, file processing, and workflow orchestration.