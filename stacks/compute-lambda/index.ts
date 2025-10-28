import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { centralState, createResourceName, createResourceTags, validateConfig, isDevelopment } from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Validate required configuration
validateConfig("compute-lambda", config, ["deployDomain"]);

const STACK_NAME = "compute-lambda";

// Compute Lambda Stack - Serverless compute infrastructure with Lambda functions, event processing, and orchestration
console.log(`🚀 Deploying Compute Lambda Stack with environment: ${deploymentConfig.environment}`);

// Get dependency outputs
const networkOutputs = {
    vpcId: centralState.getStackOutput<string>("network", "vpcId"),
    privateSubnetIds: centralState.getStackOutput<string[]>("network", "privateSubnetIds"),
    publicSubnetIds: centralState.getStackOutput<string[]>("network", "publicSubnetIds")
};

const securityOutputs = {
    lambdaSgId: centralState.getStackOutput<string>("security", "lambdaSgId"),
    applicationKeyArn: centralState.getStackOutput<string>("security", "applicationKeyArn")
};

const storageOutputs = {
    primaryBucketName: centralState.getStackOutput<string>("storage", "primaryBucketName"),
    primaryBucketArn: centralState.getStackOutput<string>("storage", "primaryBucketArn"),
    staticAssetsBucketName: centralState.getStackOutput<string>("storage", "staticAssetsBucketName"),
    staticAssetsBucketArn: centralState.getStackOutput<string>("storage", "staticAssetsBucketArn"),
    artifactsBucketName: centralState.getStackOutput<string>("storage", "artifactsBucketName"),
    artifactsBucketArn: centralState.getStackOutput<string>("storage", "artifactsBucketArn")
};

const databaseOutputs = {
    connectionString: centralState.getStackOutput<string>("database-rds", "connectionString")
};

const secretsOutputs = {
    jwtSigningKeyArn: centralState.getStackOutput<string>("secrets", "jwtSigningKeyArn")
};

// Environment-specific configurations
const environmentConfig = {
    dev: {
        logRetentionDays: 7,
        reservedConcurrency: 5,
        enableXRayTracing: false
    },
    staging: {
        logRetentionDays: 14,
        reservedConcurrency: 10,
        enableXRayTracing: true
    },
    prod: {
        logRetentionDays: 30,
        reservedConcurrency: 50,
        enableXRayTracing: true
    }
}[deploymentConfig.environment];

// =============================================================================
// IAM ROLES AND POLICIES
// =============================================================================

// Lambda execution role
const lambdaExecutionRole = new aws.iam.Role("lambda-execution-role", {
    name: createResourceName(deploymentConfig, "lambda-execution-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Service: "lambda.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }
        ]
    }),
    managedPolicyArns: [
        "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
    ],
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Purpose: "Lambda execution role with VPC access"
    })
});

// Step Functions execution role
const stepFunctionsRole = new aws.iam.Role("step-functions-role", {
    name: createResourceName(deploymentConfig, "step-functions-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Service: "states.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Purpose: "Step Functions state machine execution"
    })
});

// Lambda S3 access policy
const lambdaS3Policy = new aws.iam.Policy("lambda-s3-policy", {
    name: createResourceName(deploymentConfig, "lambda-s3-policy"),
    policy: pulumi.all([storageOutputs.primaryBucketArn, storageOutputs.staticAssetsBucketArn, storageOutputs.artifactsBucketArn])
        .apply(([primaryArn, staticArn, artifactsArn]) => JSON.stringify({
            Version: "2012-10-17",
            Statement: [
                {
                    Effect: "Allow",
                    Action: [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    Resource: [
                        `${primaryArn}/*`,
                        primaryArn,
                        `${staticArn}/*`,
                        staticArn,
                        `${artifactsArn}/*`,
                        artifactsArn
                    ]
                }
            ]
        })),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Purpose: "Lambda S3 access permissions"
    })
});

// Lambda SQS access policy
const lambdaSqsPolicy = new aws.iam.Policy("lambda-sqs-policy", {
    name: createResourceName(deploymentConfig, "lambda-sqs-policy"),
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:SendMessage",
                    "sqs:GetQueueUrl"
                ],
                Resource: "*"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Purpose: "Lambda SQS access permissions"
    })
});

// Lambda SNS access policy
const lambdaSnsPolicy = new aws.iam.Policy("lambda-sns-policy", {
    name: createResourceName(deploymentConfig, "lambda-sns-policy"),
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "sns:Publish",
                    "sns:Subscribe",
                    "sns:GetTopicAttributes"
                ],
                Resource: "*"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Purpose: "Lambda SNS access permissions"
    })
});

// Lambda Secrets Manager access policy
const lambdaSecretsPolicy = new aws.iam.Policy("lambda-secrets-policy", {
    name: createResourceName(deploymentConfig, "lambda-secrets-policy"),
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                Resource: "*"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Purpose: "Lambda Secrets Manager access"
    })
});

// Attach policies to Lambda execution role
const lambdaS3PolicyAttachment = new aws.iam.RolePolicyAttachment("lambda-s3-policy-attachment", {
    role: lambdaExecutionRole.name,
    policyArn: lambdaS3Policy.arn
});

const lambdaSqsPolicyAttachment = new aws.iam.RolePolicyAttachment("lambda-sqs-policy-attachment", {
    role: lambdaExecutionRole.name,
    policyArn: lambdaSqsPolicy.arn
});

const lambdaSnsPolicyAttachment = new aws.iam.RolePolicyAttachment("lambda-sns-policy-attachment", {
    role: lambdaExecutionRole.name,
    policyArn: lambdaSnsPolicy.arn
});

const lambdaSecretsPolicyAttachment = new aws.iam.RolePolicyAttachment("lambda-secrets-policy-attachment", {
    role: lambdaExecutionRole.name,
    policyArn: lambdaSecretsPolicy.arn
});

// =============================================================================
// LAMBDA LAYERS
// =============================================================================

// Shared dependencies layer
const sharedDependenciesLayer = new aws.lambda.LayerVersion("shared-dependencies-layer", {
    layerName: createResourceName(deploymentConfig, "shared-dependencies"),
    description: "Shared dependencies layer for Lambda functions",
    compatibleRuntimes: ["nodejs18.x", "nodejs16.x"],
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-layers/shared-dependencies.zip"
});

// Utilities layer
const utilitiesLayer = new aws.lambda.LayerVersion("utilities-layer", {
    layerName: createResourceName(deploymentConfig, "utilities"),
    description: "Common utilities and helper functions",
    compatibleRuntimes: ["nodejs18.x", "nodejs16.x"],
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-layers/utilities.zip"
});

// =============================================================================
// SQS QUEUES
// =============================================================================

// Task processing dead letter queue
const taskDlq = new aws.sqs.Queue("task-dlq", {
    name: createResourceName(deploymentConfig, "task-dlq"),
    messageRetentionSeconds: 1209600, // 14 days
    tags: createResourceTags(deploymentConfig, "sqs-queue", {
        Purpose: "Dead letter queue for failed task processing"
    })
});

// Task processing queue
const taskQueue = new aws.sqs.Queue("task-queue", {
    name: createResourceName(deploymentConfig, "task-queue"),
    delaySeconds: 0,
    maxMessageSize: 262144,
    messageRetentionSeconds: 1209600, // 14 days
    visibilityTimeoutSeconds: 300,
    redrivePolicy: pulumi.jsonStringify({
        deadLetterTargetArn: taskDlq.arn,
        maxReceiveCount: 3
    }),
    tags: createResourceTags(deploymentConfig, "sqs-queue", {
        Purpose: "Task processing queue for async operations"
    })
});

// Notification queue
const notificationQueue = new aws.sqs.Queue("notification-queue", {
    name: createResourceName(deploymentConfig, "notification-queue"),
    delaySeconds: 0,
    maxMessageSize: 262144,
    messageRetentionSeconds: 345600, // 4 days
    visibilityTimeoutSeconds: 60,
    tags: createResourceTags(deploymentConfig, "sqs-queue", {
        Purpose: "Notification queue for message processing"
    })
});

// =============================================================================
// SNS TOPICS
// =============================================================================

// Notifications topic
const notificationsTopic = new aws.sns.Topic("notifications-topic", {
    name: createResourceName(deploymentConfig, "notifications"),
    displayName: "Application Notifications",
    tags: createResourceTags(deploymentConfig, "sns-topic", {
        Purpose: "Fan-out notifications to multiple subscribers"
    })
});

// =============================================================================
// CLOUDWATCH LOG GROUPS
// =============================================================================

// API Processor log group
const apiProcessorLogGroup = new aws.cloudwatch.LogGroup("api-processor-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "api-processor")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "API Processor"
    })
});

// Data Processor log group
const dataProcessorLogGroup = new aws.cloudwatch.LogGroup("data-processor-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "data-processor")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "Data Processor"
    })
});

// Scheduler log group
const schedulerLogGroup = new aws.cloudwatch.LogGroup("scheduler-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "scheduler")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "Scheduler"
    })
});

// File Processor log group
const fileProcessorLogGroup = new aws.cloudwatch.LogGroup("file-processor-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "file-processor")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "File Processor"
    })
});

// Auth Handler log group
const authHandlerLogGroup = new aws.cloudwatch.LogGroup("auth-handler-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "auth-handler")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "Auth Handler"
    })
});

// Notification Handler log group
const notificationHandlerLogGroup = new aws.cloudwatch.LogGroup("notification-handler-logs", {
    name: pulumi.interpolate`/aws/lambda/${createResourceName(deploymentConfig, "notification-handler")}`,
    retentionInDays: environmentConfig.logRetentionDays,
    tags: createResourceTags(deploymentConfig, "log-group", {
        Function: "Notification Handler"
    })
});

// =============================================================================
// LAMBDA FUNCTIONS
// =============================================================================

// API Processor Function
const apiProcessor = new aws.lambda.Function("api-processor", {
    name: createResourceName(deploymentConfig, "api-processor"),
    description: "Processes API requests and responses with database access",
    runtime: "nodejs18.x",
    handler: "src/handlers/api-processor.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/api-processor.zip",
    timeout: 30,
    memorySize: 512,
    reservedConcurrencyLimit: environmentConfig.reservedConcurrency,
    layers: [sharedDependenciesLayer.arn, utilitiesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            DATABASE_URL: databaseOutputs.connectionString,
            S3_BUCKET: storageOutputs.primaryBucketName,
            CORS_ORIGIN: pulumi.interpolate`https://${deploymentConfig.deployDomain}`,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    vpcConfig: {
        subnetIds: networkOutputs.privateSubnetIds,
        securityGroupIds: [securityOutputs.lambdaSgId]
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [apiProcessorLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "API request processing with database access",
        Tier: "API"
    })
});

// Data Processor Function
const dataProcessor = new aws.lambda.Function("data-processor", {
    name: createResourceName(deploymentConfig, "data-processor"),
    description: "Processes data transformation tasks with higher memory allocation",
    runtime: "nodejs18.x",
    handler: "src/handlers/data-processor.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/data-processor.zip",
    timeout: 300, // 5 minutes
    memorySize: 1024,
    reservedConcurrencyLimit: Math.floor(environmentConfig.reservedConcurrency * 0.6),
    layers: [sharedDependenciesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            DATABASE_URL: databaseOutputs.connectionString,
            TASK_QUEUE_URL: taskQueue.url,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    vpcConfig: {
        subnetIds: networkOutputs.privateSubnetIds,
        securityGroupIds: [securityOutputs.lambdaSgId]
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [dataProcessorLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "Data transformation and processing",
        Tier: "Processing"
    })
});

// Scheduler Function
const scheduler = new aws.lambda.Function("scheduler", {
    name: createResourceName(deploymentConfig, "scheduler"),
    description: "Handles scheduled tasks and cron jobs",
    runtime: "nodejs18.x",
    handler: "src/handlers/scheduler.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/scheduler.zip",
    timeout: 600, // 10 minutes
    memorySize: 512,
    reservedConcurrencyLimit: Math.floor(environmentConfig.reservedConcurrency * 0.2),
    layers: [sharedDependenciesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            TASK_QUEUE_URL: taskQueue.url,
            SNS_TOPIC_ARN: notificationsTopic.arn,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [schedulerLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "Scheduled task execution",
        Tier: "Automation"
    })
});

// File Processor Function
const fileProcessor = new aws.lambda.Function("file-processor", {
    name: createResourceName(deploymentConfig, "file-processor"),
    description: "Processes file uploads and transformations with high memory allocation",
    runtime: "nodejs18.x",
    handler: "src/handlers/file-processor.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/file-processor.zip",
    timeout: 300, // 5 minutes
    memorySize: 2048,
    reservedConcurrencyLimit: Math.floor(environmentConfig.reservedConcurrency * 0.3),
    layers: [sharedDependenciesLayer.arn, utilitiesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            SOURCE_BUCKET: storageOutputs.primaryBucketName,
            PROCESSED_BUCKET: storageOutputs.staticAssetsBucketName,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [fileProcessorLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "File processing and transformation",
        Tier: "Processing"
    })
});

// Auth Handler Function
const authHandler = new aws.lambda.Function("auth-handler", {
    name: createResourceName(deploymentConfig, "auth-handler"),
    description: "Custom authentication and JWT token processing",
    runtime: "nodejs18.x",
    handler: "src/handlers/auth.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/auth-handler.zip",
    timeout: 30,
    memorySize: 256,
    reservedConcurrencyLimit: Math.floor(environmentConfig.reservedConcurrency * 0.4),
    layers: [utilitiesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            JWT_SECRET_ARN: secretsOutputs.jwtSigningKeyArn,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [authHandlerLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "Authentication and JWT processing",
        Tier: "Security"
    })
});

// Notification Handler Function
const notificationHandler = new aws.lambda.Function("notification-handler", {
    name: createResourceName(deploymentConfig, "notification-handler"),
    description: "Processes notifications and alerts",
    runtime: "nodejs18.x",
    handler: "src/handlers/notifications.handler",
    role: lambdaExecutionRole.arn,
    s3Bucket: storageOutputs.artifactsBucketName,
    s3Key: "lambda-functions/notifications.zip",
    timeout: 60,
    memorySize: 256,
    reservedConcurrencyLimit: Math.floor(environmentConfig.reservedConcurrency * 0.3),
    layers: [utilitiesLayer.arn],
    environment: {
        variables: {
            NODE_ENV: deploymentConfig.environment,
            SNS_TOPIC_ARN: notificationsTopic.arn,
            LOG_LEVEL: isDevelopment(deploymentConfig) ? "debug" : "info"
        }
    },
    tracingConfig: {
        mode: environmentConfig.enableXRayTracing ? "Active" : "PassThrough"
    },
    dependsOn: [notificationHandlerLogGroup],
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Purpose: "Notification processing and alerting",
        Tier: "Messaging"
    })
});

// =============================================================================
// LAMBDA PERMISSIONS
// =============================================================================

// API Gateway invoke permission for API processor
const apiGatewayInvokePermission = new aws.lambda.Permission("api-gateway-invoke-permission", {
    statementId: "AllowExecutionFromAPIGateway",
    action: "lambda:InvokeFunction",
    function: apiProcessor.name,
    principal: "apigateway.amazonaws.com"
});

// S3 invoke permission for file processor
const s3InvokePermission = new aws.lambda.Permission("s3-invoke-permission", {
    statementId: "AllowExecutionFromS3",
    action: "lambda:InvokeFunction",
    function: fileProcessor.name,
    principal: "s3.amazonaws.com",
    sourceArn: storageOutputs.primaryBucketArn
});

// SNS invoke permission for notification handler
const snsInvokePermission = new aws.lambda.Permission("sns-invoke-permission", {
    statementId: "AllowExecutionFromSNS",
    action: "lambda:InvokeFunction",
    function: notificationHandler.name,
    principal: "sns.amazonaws.com",
    sourceArn: notificationsTopic.arn
});

// =============================================================================
// EVENT SOURCE MAPPINGS
// =============================================================================

// SQS event source mapping for data processor
const sqsEventSourceMapping = new aws.lambda.EventSourceMapping("sqs-event-source-mapping", {
    eventSourceArn: taskQueue.arn,
    functionName: dataProcessor.name,
    batchSize: 10,
    maximumBatchingWindowInSeconds: 5,
    enabled: true
});

// =============================================================================
// FUNCTION URLs
// =============================================================================

// Function URL for API processor
const apiProcessorUrl = new aws.lambda.FunctionUrl("api-processor-url", {
    functionName: apiProcessor.name,
    authorizationType: "AWS_IAM",
    cors: {
        allowCredentials: true,
        allowHeaders: ["date", "keep-alive", "content-type", "authorization"],
        allowMethods: ["*"],
        allowOrigins: [
            pulumi.interpolate`https://${deploymentConfig.deployDomain}`,
            pulumi.interpolate`https://api.${deploymentConfig.deployDomain}`
        ],
        exposeHeaders: ["date", "keep-alive"],
        maxAge: 86400
    }
});

// =============================================================================
// SNS SUBSCRIPTIONS
// =============================================================================

// SNS subscription for notification handler
const notificationLambdaSubscription = new aws.sns.TopicSubscription("notification-lambda-subscription", {
    topicArn: notificationsTopic.arn,
    protocol: "lambda",
    endpoint: notificationHandler.arn
});

// SNS subscription for notification queue
const notificationSqsSubscription = new aws.sns.TopicSubscription("notification-sqs-subscription", {
    topicArn: notificationsTopic.arn,
    protocol: "sqs",
    endpoint: notificationQueue.arn
});

// =============================================================================
// EVENTBRIDGE RULES AND TARGETS
// =============================================================================

// Daily scheduler rule
const dailySchedulerRule = new aws.cloudwatch.EventRule("daily-scheduler-rule", {
    name: createResourceName(deploymentConfig, "daily-scheduler"),
    description: "Trigger daily scheduled tasks",
    scheduleExpression: "cron(0 6 * * ? *)", // Daily at 6 AM UTC
    state: "ENABLED",
    tags: createResourceTags(deploymentConfig, "eventbridge-rule", {
        Schedule: "Daily",
        Purpose: "Maintenance tasks"
    })
});

// Daily scheduler target
const dailySchedulerTarget = new aws.cloudwatch.EventTarget("daily-scheduler-target", {
    rule: dailySchedulerRule.name,
    arn: scheduler.arn,
    input: JSON.stringify({
        taskType: "daily_maintenance",
        environment: deploymentConfig.environment
    })
});

// EventBridge permission for daily scheduler
const dailySchedulerPermission = new aws.lambda.Permission("daily-scheduler-permission", {
    statementId: "AllowExecutionFromEventBridge-Daily",
    action: "lambda:InvokeFunction",
    function: scheduler.name,
    principal: "events.amazonaws.com",
    sourceArn: dailySchedulerRule.arn
});

// Hourly cleanup rule
const hourlyCleanupRule = new aws.cloudwatch.EventRule("hourly-cleanup-rule", {
    name: createResourceName(deploymentConfig, "hourly-cleanup"),
    description: "Trigger hourly cleanup tasks",
    scheduleExpression: "rate(1 hour)",
    state: "ENABLED",
    tags: createResourceTags(deploymentConfig, "eventbridge-rule", {
        Schedule: "Hourly",
        Purpose: "Cleanup tasks"
    })
});

// Hourly cleanup target
const hourlyCleanupTarget = new aws.cloudwatch.EventTarget("hourly-cleanup-target", {
    rule: hourlyCleanupRule.name,
    arn: scheduler.arn,
    input: JSON.stringify({
        taskType: "cleanup",
        environment: deploymentConfig.environment
    })
});

// EventBridge permission for hourly cleanup
const hourlyCleanupPermission = new aws.lambda.Permission("hourly-cleanup-permission", {
    statementId: "AllowExecutionFromEventBridge-Hourly",
    action: "lambda:InvokeFunction",
    function: scheduler.name,
    principal: "events.amazonaws.com",
    sourceArn: hourlyCleanupRule.arn
});

// =============================================================================
// STEP FUNCTIONS STATE MACHINE
// =============================================================================

// Step Functions policy for Lambda invocation
const stepFunctionsLambdaPolicy = new aws.iam.Policy("step-functions-lambda-policy", {
    name: createResourceName(deploymentConfig, "step-functions-lambda-policy"),
    policy: pulumi.all([dataProcessor.arn, notificationHandler.arn])
        .apply(([dataProcessorArn, notificationArn]) => JSON.stringify({
            Version: "2012-10-17",
            Statement: [
                {
                    Effect: "Allow",
                    Action: [
                        "lambda:InvokeFunction"
                    ],
                    Resource: [
                        dataProcessorArn,
                        notificationArn
                    ]
                }
            ]
        })),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Purpose: "Step Functions Lambda invocation"
    })
});

// Attach Step Functions Lambda policy
const stepFunctionsLambdaPolicyAttachment = new aws.iam.RolePolicyAttachment("step-functions-lambda-policy-attachment", {
    role: stepFunctionsRole.name,
    policyArn: stepFunctionsLambdaPolicy.arn
});

// Data processing pipeline state machine
const dataPipeline = new aws.sfn.StateMachine("data-pipeline", {
    name: createResourceName(deploymentConfig, "data-pipeline"),
    roleArn: stepFunctionsRole.arn,
    definition: pulumi.all([dataProcessor.arn, notificationHandler.arn])
        .apply(([dataProcessorArn, notificationArn]) => JSON.stringify({
            Comment: "Data processing pipeline with error handling",
            StartAt: "ValidateInput",
            States: {
                ValidateInput: {
                    Type: "Task",
                    Resource: dataProcessorArn,
                    Parameters: {
                        "action": "validate",
                        "input.$": "$"
                    },
                    Next: "ProcessData",
                    Catch: [
                        {
                            ErrorEquals: ["ValidationError"],
                            Next: "ValidationFailed",
                            ResultPath: "$.error"
                        }
                    ],
                    Retry: [
                        {
                            ErrorEquals: ["Lambda.ServiceException", "Lambda.AWSLambdaException"],
                            IntervalSeconds: 2,
                            MaxAttempts: 3,
                            BackoffRate: 2.0
                        }
                    ]
                },
                ProcessData: {
                    Type: "Task",
                    Resource: dataProcessorArn,
                    Parameters: {
                        "action": "process",
                        "input.$": "$"
                    },
                    Next: "NotifyCompletion",
                    Catch: [
                        {
                            ErrorEquals: ["States.All"],
                            Next: "ProcessingFailed",
                            ResultPath: "$.error"
                        }
                    ],
                    Retry: [
                        {
                            ErrorEquals: ["Lambda.ServiceException", "Lambda.AWSLambdaException"],
                            IntervalSeconds: 2,
                            MaxAttempts: 3,
                            BackoffRate: 2.0
                        }
                    ]
                },
                NotifyCompletion: {
                    Type: "Task",
                    Resource: notificationArn,
                    Parameters: {
                        "message": "Data processing completed successfully",
                        "status": "success",
                        "input.$": "$"
                    },
                    End: true
                },
                ValidationFailed: {
                    Type: "Task",
                    Resource: notificationArn,
                    Parameters: {
                        "message": "Data validation failed",
                        "status": "validation_failed",
                        "error.$": "$.error"
                    },
                    End: true
                },
                ProcessingFailed: {
                    Type: "Task",
                    Resource: notificationArn,
                    Parameters: {
                        "message": "Data processing failed",
                        "status": "processing_failed",
                        "error.$": "$.error"
                    },
                    End: true
                }
            }
        })),
    dependsOn: [stepFunctionsLambdaPolicyAttachment],
    tags: createResourceTags(deploymentConfig, "state-machine", {
        Purpose: "Data processing workflow orchestration",
        Type: "Pipeline"
    })
});

// =============================================================================
// CLOUDWATCH ALARMS
// =============================================================================

// API Processor error alarm
const apiProcessorErrorAlarm = new aws.cloudwatch.MetricAlarm("api-processor-error-alarm", {
    alarmName: createResourceName(deploymentConfig, "api-processor-errors"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "Errors",
    namespace: "AWS/Lambda",
    period: 60,
    statistic: "Sum",
    threshold: isDevelopment(deploymentConfig) ? 10 : 5,
    alarmDescription: "API processor function error rate is too high",
    dimensions: {
        FunctionName: apiProcessor.name
    },
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Function: "API Processor",
        Type: "Error Rate"
    })
});

// API Processor duration alarm
const apiProcessorDurationAlarm = new aws.cloudwatch.MetricAlarm("api-processor-duration-alarm", {
    alarmName: createResourceName(deploymentConfig, "api-processor-duration"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "Duration",
    namespace: "AWS/Lambda",
    period: 60,
    statistic: "Average",
    threshold: 25000, // 25 seconds
    alarmDescription: "API processor function duration is too high",
    dimensions: {
        FunctionName: apiProcessor.name
    },
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Function: "API Processor",
        Type: "Duration"
    })
});

// Data Processor error alarm
const dataProcessorErrorAlarm = new aws.cloudwatch.MetricAlarm("data-processor-error-alarm", {
    alarmName: createResourceName(deploymentConfig, "data-processor-errors"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "Errors",
    namespace: "AWS/Lambda",
    period: 300, // 5 minutes
    statistic: "Sum",
    threshold: isDevelopment(deploymentConfig) ? 5 : 3,
    alarmDescription: "Data processor function error rate is too high",
    dimensions: {
        FunctionName: dataProcessor.name
    },
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Function: "Data Processor",
        Type: "Error Rate"
    })
});

// Task queue age alarm
const taskQueueAgeAlarm = new aws.cloudwatch.MetricAlarm("task-queue-age-alarm", {
    alarmName: createResourceName(deploymentConfig, "task-queue-age"),
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 2,
    metricName: "ApproximateAgeOfOldestMessage",
    namespace: "AWS/SQS",
    period: 300, // 5 minutes
    statistic: "Maximum",
    threshold: 900, // 15 minutes
    alarmDescription: "Messages in task queue are getting too old",
    dimensions: {
        QueueName: taskQueue.name
    },
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        Queue: "Task Queue",
        Type: "Message Age"
    })
});

// =============================================================================
// MONITORING DASHBOARD
// =============================================================================

const lambdaDashboard = new aws.cloudwatch.Dashboard("lambda-dashboard", {
    dashboardName: createResourceName(deploymentConfig, "lambda-dashboard"),
    dashboardBody: pulumi.all([
        apiProcessor.name,
        dataProcessor.name,
        scheduler.name,
        fileProcessor.name,
        taskQueue.name,
        notificationQueue.name
    ]).apply(([apiName, dataName, schedulerName, fileName, taskQueueName, notifQueueName]) =>
        JSON.stringify({
            widgets: [
                {
                    type: "metric",
                    x: 0,
                    y: 0,
                    width: 12,
                    height: 6,
                    properties: {
                        metrics: [
                            ["AWS/Lambda", "Invocations", "FunctionName", apiName],
                            [".", ".", ".", dataName],
                            [".", ".", ".", schedulerName],
                            [".", ".", ".", fileName]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: deploymentConfig.region,
                        title: "Lambda Function Invocations",
                        period: 300
                    }
                },
                {
                    type: "metric",
                    x: 12,
                    y: 0,
                    width: 12,
                    height: 6,
                    properties: {
                        metrics: [
                            ["AWS/Lambda", "Errors", "FunctionName", apiName],
                            [".", ".", ".", dataName],
                            [".", ".", ".", schedulerName],
                            [".", ".", ".", fileName]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: deploymentConfig.region,
                        title: "Lambda Function Errors",
                        period: 300
                    }
                },
                {
                    type: "metric",
                    x: 0,
                    y: 6,
                    width: 12,
                    height: 6,
                    properties: {
                        metrics: [
                            ["AWS/Lambda", "Duration", "FunctionName", apiName],
                            [".", ".", ".", dataName],
                            [".", ".", ".", schedulerName],
                            [".", ".", ".", fileName]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: deploymentConfig.region,
                        title: "Lambda Function Duration",
                        period: 300
                    }
                },
                {
                    type: "metric",
                    x: 12,
                    y: 6,
                    width: 12,
                    height: 6,
                    properties: {
                        metrics: [
                            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", taskQueueName],
                            [".", "NumberOfMessagesReceived", ".", "."],
                            [".", "NumberOfMessagesSent", ".", notifQueueName],
                            [".", "NumberOfMessagesReceived", ".", "."]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: deploymentConfig.region,
                        title: "SQS Queue Metrics",
                        period: 300
                    }
                }
            ]
        })
    )
});

// =============================================================================
// EXPORTS
// =============================================================================

// Lambda Function ARNs
export const apiProcessorArn = apiProcessor.arn;
export const dataProcessorArn = dataProcessor.arn;
export const schedulerArn = scheduler.arn;
export const fileProcessorArn = fileProcessor.arn;
export const authHandlerArn = authHandler.arn;
export const notificationHandlerArn = notificationHandler.arn;

// Function URL
export const apiProcessorFunctionUrl = apiProcessorUrl.functionUrl;

// Queue Information
export const taskQueueUrl = taskQueue.url;
export const taskQueueArn = taskQueue.arn;
export const notificationQueueUrl = notificationQueue.url;
export const notificationQueueArn = notificationQueue.arn;

// Topic Information
export const notificationsTopicArn = notificationsTopic.arn;

// Step Functions
export const dataPipelineArn = dataPipeline.arn;

// Lambda Layers
export const sharedDependenciesLayerArn = sharedDependenciesLayer.arn;
export const utilitiesLayerArn = utilitiesLayer.arn;

// IAM Role ARNs
export const lambdaExecutionRoleArn = lambdaExecutionRole.arn;
export const stepFunctionsRoleArn = stepFunctionsRole.arn;

// EventBridge Rules
export const dailySchedulerRuleArn = dailySchedulerRule.arn;
export const hourlyCleanupRuleArn = hourlyCleanupRule.arn;

// CloudWatch Dashboard
export const dashboardUrl = pulumi.interpolate`https://console.aws.amazon.com/cloudwatch/home?region=${deploymentConfig.region}#dashboards:name=${lambdaDashboard.dashboardName}`;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    functions: {
        apiProcessor: {
            arn: apiProcessorArn,
            url: apiProcessorFunctionUrl,
            memory: "512MB",
            timeout: "30s"
        },
        dataProcessor: {
            arn: dataProcessorArn,
            memory: "1024MB",
            timeout: "300s"
        },
        scheduler: {
            arn: schedulerArn,
            memory: "512MB",
            timeout: "600s"
        },
        fileProcessor: {
            arn: fileProcessorArn,
            memory: "2048MB",
            timeout: "300s"
        },
        authHandler: {
            arn: authHandlerArn,
            memory: "256MB",
            timeout: "30s"
        },
        notificationHandler: {
            arn: notificationHandlerArn,
            memory: "256MB",
            timeout: "60s"
        }
    },
    queues: {
        taskQueue: {
            url: taskQueueUrl,
            arn: taskQueueArn
        },
        notificationQueue: {
            url: notificationQueueUrl,
            arn: notificationQueueArn
        }
    },
    topics: {
        notifications: {
            arn: notificationsTopicArn
        }
    },
    orchestration: {
        dataPipeline: {
            arn: dataPipelineArn
        }
    },
    monitoring: {
        dashboard: dashboardUrl,
        alarms: [
            "api-processor-errors",
            "api-processor-duration",
            "data-processor-errors",
            "task-queue-age"
        ]
    },
    environment: deploymentConfig.environment,
    reservedConcurrency: environmentConfig.reservedConcurrency,
    xrayTracing: environmentConfig.enableXRayTracing
};