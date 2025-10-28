import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    getCurrentRegion,
    getCurrentAccountId,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS,
    createLogGroup
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();
const STACK_NAME = "monitoring";

// Validate required configuration
validateConfig(STACK_NAME, config, []);

// Get dependency stack outputs
const networkStackOutputs: NetworkOutputs = {
    vpcId: centralState.getStackOutput<string>("network", "vpcId"),
    vpcCidrBlock: centralState.getStackOutput<string>("network", "vpcCidrBlock"),
    internetGatewayId: centralState.getStackOutput<string>("network", "internetGatewayId"),
    publicSubnetIds: centralState.getStackOutput<string[]>("network", "publicSubnetIds"),
    privateSubnetIds: centralState.getStackOutput<string[]>("network", "privateSubnetIds"),
    databaseSubnetIds: centralState.getStackOutput<string[]>("network", "databaseSubnetIds"),
    availabilityZones: centralState.getStackOutput<string[]>("network", "availabilityZones"),
    natGatewayIds: centralState.getStackOutput<string[]>("network", "natGatewayIds")
};

const securityStackOutputs: SecurityOutputs = {
    loadBalancerSgId: centralState.getStackOutput<string>("security", "loadBalancerSgId"),
    webApplicationSgId: centralState.getStackOutput<string>("security", "webApplicationSgId"),
    apiApplicationSgId: centralState.getStackOutput<string>("security", "apiApplicationSgId"),
    databaseSgId: centralState.getStackOutput<string>("security", "databaseSgId"),
    ecsExecutionRoleArn: centralState.getStackOutput<string>("security", "ecsExecutionRoleArn"),
    ecsTaskRoleArn: centralState.getStackOutput<string>("security", "ecsTaskRoleArn"),
    eksClusterRoleArn: centralState.getStackOutput<string>("security", "eksClusterRoleArn"),
    eksNodeGroupRoleArn: centralState.getStackOutput<string>("security", "eksNodeGroupRoleArn"),
    applicationKeyId: centralState.getStackOutput<string>("security", "applicationKeyId"),
    applicationKeyArn: centralState.getStackOutput<string>("security", "applicationKeyArn"),
    databaseKeyId: centralState.getStackOutput<string>("security", "databaseKeyId"),
    databaseKeyArn: centralState.getStackOutput<string>("security", "databaseKeyArn")
};

// Get database stack outputs
const databaseStackOutputs = {
    databaseEndpoint: centralState.getStackOutput<string>("database-rds", "databaseEndpoint"),
    databaseInstanceId: centralState.getStackOutput<string>("database-rds", "primaryDatabaseId"),
    databaseClusterIdentifier: centralState.getStackOutput<string>("database-rds", "databaseClusterIdentifier")
};

// Get containers-apps stack outputs
const containerAppsStackOutputs = {
    clusterName: centralState.getStackOutput<string>("containers-apps", "clusterName"),
    publicAlbArn: centralState.getStackOutput<string>("containers-apps", "publicAlbArn"),
    frontendServiceName: centralState.getStackOutput<string>("containers-apps", "frontendServiceName"),
    backendServiceArn: centralState.getStackOutput<string>("containers-apps", "backendServiceArn"),
    apiServiceArn: centralState.getStackOutput<string>("containers-apps", "apiServiceArn"),
    publicAlbDnsName: centralState.getStackOutput<string>("containers-apps", "publicAlbDnsName")
};

console.log(`🚀 Deploying Monitoring Stack for environment: ${deploymentConfig.environment}`);

// Get current AWS region and account ID
const currentRegion = getCurrentRegion();
const currentAccountId = getCurrentAccountId();

// =============================================================================
// Configuration Parameters
// =============================================================================

const monitoringConfig = {
    // Email notification settings
    alertEmail: config.get("alertEmail") || `ops-team@${deploymentConfig.deployDomain}`,

    // Slack integration settings
    slackWebhookUrl: config.get("slackWebhookUrl"),
    slackChannelName: config.get("slackChannelName") || "#alerts",

    // Alarm thresholds
    thresholds: {
        cpuUtilization: config.getNumber("cpuThreshold") || 80,
        memoryUtilization: config.getNumber("memoryThreshold") || 85,
        databaseConnections: config.getNumber("databaseConnectionsThreshold") || 80,
        responseTime: config.getNumber("responseTimeThreshold") || 5000, // 5 seconds
        errorRate: config.getNumber("errorRateThreshold") || 5, // 5%
        diskUtilization: config.getNumber("diskThreshold") || 80
    },

    // Log retention and monitoring
    logRetentionDays: config.getNumber("logRetentionDays") || (deploymentConfig.environment === "prod" ? 90 : 30),
    enableDetailedMonitoring: config.getBoolean("enableDetailedMonitoring") !== false,

    // Synthetics configuration
    enableSynthetics: config.getBoolean("enableSynthetics") !== false,
    syntheticsCheckFrequency: config.getNumber("syntheticsCheckFrequency") || 300, // 5 minutes

    // Dashboard configuration
    dashboardRefreshInterval: config.getNumber("dashboardRefreshInterval") || 300 // 5 minutes
};

// =============================================================================
// S3 Bucket for Synthetics Artifacts
// =============================================================================

const syntheticsArtifactsBucket = new aws.s3.Bucket("synthetics-artifacts", {
    bucket: createResourceName(deploymentConfig, "synthetics-artifacts"),
    forceDestroy: deploymentConfig.environment !== "prod",
    serverSideEncryptionConfiguration: {
        rule: {
            applyServerSideEncryptionByDefault: {
                sseAlgorithm: "aws:kms",
                kmsMasterKeyId: securityStackOutputs.applicationKeyArn
            }
        }
    },
    publicAccessBlock: {
        blockPublicAcls: true,
        blockPublicPolicy: true,
        ignorePublicAcls: true,
        restrictPublicBuckets: true
    },
    lifecycleRules: [{
        id: "cleanup-old-artifacts",
        enabled: true,
        expiration: {
            days: monitoringConfig.logRetentionDays
        }
    }],
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "synthetics-artifacts"),
        Purpose: "synthetics-artifacts",
        Type: "monitoring"
    })
});

// =============================================================================
// SNS Topics for Notifications
// =============================================================================

// Primary alerts topic
const alertsTopic = new aws.sns.Topic("alerts-topic", {
    name: createResourceName(deploymentConfig, "alerts"),
    description: `Alert notifications for ${deploymentConfig.projectName} (${deploymentConfig.environment})`,
    kmsKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "sns-topic", {
        Name: createResourceName(deploymentConfig, "alerts"),
        Type: "alerts",
        NotificationChannel: "primary"
    })
});

// Email subscription
const emailSubscription = new aws.sns.TopicSubscription("email-alerts", {
    topicArn: alertsTopic.arn,
    protocol: "email",
    endpoint: monitoringConfig.alertEmail
});

// Slack webhook subscription (if configured)
let slackSubscription: aws.sns.TopicSubscription | undefined;
if (monitoringConfig.slackWebhookUrl) {
    slackSubscription = new aws.sns.TopicSubscription("slack-alerts", {
        topicArn: alertsTopic.arn,
        protocol: "https",
        endpoint: monitoringConfig.slackWebhookUrl
    });
}

// Critical alerts topic (for immediate notifications)
const criticalAlertsTopic = new aws.sns.Topic("critical-alerts", {
    name: createResourceName(deploymentConfig, "critical-alerts"),
    description: `Critical alert notifications for ${deploymentConfig.projectName} (${deploymentConfig.environment})`,
    kmsKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "sns-topic", {
        Name: createResourceName(deploymentConfig, "critical-alerts"),
        Type: "alerts",
        NotificationChannel: "critical"
    })
});

const criticalEmailSubscription = new aws.sns.TopicSubscription("critical-email-alerts", {
    topicArn: criticalAlertsTopic.arn,
    protocol: "email",
    endpoint: monitoringConfig.alertEmail
});

// =============================================================================
// Centralized Log Groups
// =============================================================================

// Main application log group
const applicationLogGroup = createLogGroup(
    `/aws/application/${createResourceName(deploymentConfig, "app")}`,
    monitoringConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "application",
        Type: "centralized-logging"
    })
);

// Infrastructure log group
const infrastructureLogGroup = createLogGroup(
    `/aws/infrastructure/${createResourceName(deploymentConfig, "infra")}`,
    monitoringConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "infrastructure",
        Type: "centralized-logging"
    })
);

// Security log group
const securityLogGroup = createLogGroup(
    `/aws/security/${createResourceName(deploymentConfig, "security")}`,
    monitoringConfig.logRetentionDays * 2, // Keep security logs longer
    createResourceTags(deploymentConfig, "log-group", {
        Service: "security",
        Type: "centralized-logging"
    })
);

// =============================================================================
// Metric Filters
// =============================================================================

// Error rate metric filter
const errorMetricFilter = new aws.cloudwatch.LogMetricFilter("error-metric-filter", {
    name: createResourceName(deploymentConfig, "error-rate"),
    logGroupName: applicationLogGroup.name,
    pattern: "[ERROR]",
    metricTransformation: {
        name: "ErrorCount",
        namespace: `${deploymentConfig.projectName}/Application`,
        value: "1",
        defaultValue: "0"
    }
});

// 4xx response metric filter
const clientErrorMetricFilter = new aws.cloudwatch.LogMetricFilter("client-error-filter", {
    name: createResourceName(deploymentConfig, "4xx-errors"),
    logGroupName: applicationLogGroup.name,
    pattern: "[timestamp, requestId, \"ERROR\", statusCode=4*, ...]",
    metricTransformation: {
        name: "4xxErrors",
        namespace: `${deploymentConfig.projectName}/Application`,
        value: "1",
        defaultValue: "0"
    }
});

// 5xx response metric filter
const serverErrorMetricFilter = new aws.cloudwatch.LogMetricFilter("server-error-filter", {
    name: createResourceName(deploymentConfig, "5xx-errors"),
    logGroupName: applicationLogGroup.name,
    pattern: "[timestamp, requestId, \"ERROR\", statusCode=5*, ...]",
    metricTransformation: {
        name: "5xxErrors",
        namespace: `${deploymentConfig.projectName}/Application`,
        value: "1",
        defaultValue: "0"
    }
});

// Security events metric filter
const securityEventsFilter = new aws.cloudwatch.LogMetricFilter("security-events-filter", {
    name: createResourceName(deploymentConfig, "security-events"),
    logGroupName: securityLogGroup.name,
    pattern: "[timestamp, level, \"SECURITY\", event, ...]",
    metricTransformation: {
        name: "SecurityEvents",
        namespace: `${deploymentConfig.projectName}/Security`,
        value: "1",
        defaultValue: "0"
    }
});

// =============================================================================
// CloudWatch Alarms
// =============================================================================

// Application Load Balancer alarms
const albHighLatencyAlarm = new aws.cloudwatch.MetricAlarm("alb-high-latency", {
    name: createResourceName(deploymentConfig, "alb-high-latency"),
    description: "Application Load Balancer high latency alarm",
    metricName: "TargetResponseTime",
    namespace: "AWS/ApplicationELB",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: monitoringConfig.thresholds.responseTime / 1000, // Convert to seconds
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        LoadBalancer: containerAppsStackOutputs.publicAlbArn.apply(arn => arn.split('/').slice(1).join('/'))
    },
    alarmActions: [alertsTopic.arn],
    okActions: [alertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "latency",
        Resource: "load-balancer"
    })
});

const alb5xxErrorsAlarm = new aws.cloudwatch.MetricAlarm("alb-5xx-errors", {
    name: createResourceName(deploymentConfig, "alb-5xx-errors"),
    description: "Application Load Balancer 5xx errors alarm",
    metricName: "HTTPCode_Target_5XX_Count",
    namespace: "AWS/ApplicationELB",
    statistic: "Sum",
    period: 300,
    evaluationPeriods: 2,
    threshold: 10,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        LoadBalancer: containerAppsStackOutputs.publicAlbArn.apply(arn => arn.split('/').slice(1).join('/'))
    },
    alarmActions: [criticalAlertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "error-rate",
        Resource: "load-balancer"
    })
});

// ECS Cluster alarms
const ecsHighCpuAlarm = new aws.cloudwatch.MetricAlarm("ecs-high-cpu", {
    name: createResourceName(deploymentConfig, "ecs-high-cpu"),
    description: "ECS Cluster high CPU utilization alarm",
    metricName: "CPUUtilization",
    namespace: "AWS/ECS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: monitoringConfig.thresholds.cpuUtilization,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        ClusterName: containerAppsStackOutputs.clusterName
    },
    alarmActions: [alertsTopic.arn],
    okActions: [alertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "cpu-utilization",
        Resource: "ecs-cluster"
    })
});

const ecsHighMemoryAlarm = new aws.cloudwatch.MetricAlarm("ecs-high-memory", {
    name: createResourceName(deploymentConfig, "ecs-high-memory"),
    description: "ECS Cluster high memory utilization alarm",
    metricName: "MemoryUtilization",
    namespace: "AWS/ECS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: monitoringConfig.thresholds.memoryUtilization,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        ClusterName: containerAppsStackOutputs.clusterName
    },
    alarmActions: [alertsTopic.arn],
    okActions: [alertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "memory-utilization",
        Resource: "ecs-cluster"
    })
});

// Database alarms
const databaseHighConnectionsAlarm = new aws.cloudwatch.MetricAlarm("database-high-connections", {
    name: createResourceName(deploymentConfig, "db-high-connections"),
    description: "Database high connection count alarm",
    metricName: "DatabaseConnections",
    namespace: "AWS/RDS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 2,
    threshold: monitoringConfig.thresholds.databaseConnections,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        DBInstanceIdentifier: databaseStackOutputs.databaseInstanceId
    },
    alarmActions: [alertsTopic.arn],
    okActions: [alertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "database-connections",
        Resource: "rds-database"
    })
});

const databaseHighCpuAlarm = new aws.cloudwatch.MetricAlarm("database-high-cpu", {
    name: createResourceName(deploymentConfig, "db-high-cpu"),
    description: "Database high CPU utilization alarm",
    metricName: "CPUUtilization",
    namespace: "AWS/RDS",
    statistic: "Average",
    period: 300,
    evaluationPeriods: 3,
    threshold: monitoringConfig.thresholds.cpuUtilization,
    comparisonOperator: "GreaterThanThreshold",
    dimensions: {
        DBInstanceIdentifier: databaseStackOutputs.databaseInstanceId
    },
    alarmActions: [alertsTopic.arn],
    okActions: [alertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "cpu-utilization",
        Resource: "rds-database"
    })
});

// Custom metric alarms based on log filters
const highErrorRateAlarm = new aws.cloudwatch.MetricAlarm("high-error-rate", {
    name: createResourceName(deploymentConfig, "high-error-rate"),
    description: "High error rate alarm based on application logs",
    metricName: "ErrorCount",
    namespace: `${deploymentConfig.projectName}/Application`,
    statistic: "Sum",
    period: 300,
    evaluationPeriods: 2,
    threshold: 20, // More than 20 errors in 5 minutes
    comparisonOperator: "GreaterThanThreshold",
    alarmActions: [criticalAlertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "error-rate",
        Resource: "application"
    })
});

const securityEventsAlarm = new aws.cloudwatch.MetricAlarm("security-events", {
    name: createResourceName(deploymentConfig, "security-events"),
    description: "Security events detected in logs",
    metricName: "SecurityEvents",
    namespace: `${deploymentConfig.projectName}/Security`,
    statistic: "Sum",
    period: 300,
    evaluationPeriods: 1,
    threshold: 1, // Any security event triggers alarm
    comparisonOperator: "GreaterThanOrEqualToThreshold",
    alarmActions: [criticalAlertsTopic.arn],
    treatMissingData: "notBreaching",
    tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
        AlarmType: "security-event",
        Resource: "security-logs"
    })
});

// =============================================================================
// CloudWatch Synthetics
// =============================================================================

// IAM role for Synthetics canary
const syntheticsRole = new aws.iam.Role("synthetics-role", {
    name: createResourceName(deploymentConfig, "synthetics-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Effect: "Allow",
            Principal: {
                Service: "lambda.amazonaws.com"
            },
            Action: "sts:AssumeRole"
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Service: "synthetics",
        Type: "execution-role"
    })
});

// Attach CloudWatch Synthetics execution policy
const syntheticsRolePolicyAttachment = new aws.iam.RolePolicyAttachment("synthetics-policy", {
    role: syntheticsRole.name,
    policyArn: "arn:aws:iam::aws:policy/CloudWatchSyntheticsExecutionRolePolicy"
});

// Custom policy for S3 access to artifacts bucket
const syntheticsS3Policy = new aws.iam.RolePolicy("synthetics-s3-policy", {
    name: "SyntheticsS3Access",
    role: syntheticsRole.id,
    policy: pulumi.all([syntheticsArtifactsBucket.arn]).apply(([bucketArn]) =>
        JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Effect: "Allow",
                Action: [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                Resource: [
                    bucketArn,
                    `${bucketArn}/*`
                ]
            }]
        })
    )
});

// Synthetics canary for website monitoring
let websiteCanary: aws.synthetics.Canary | undefined;
if (monitoringConfig.enableSynthetics) {
    websiteCanary = new aws.synthetics.Canary("website-monitoring", {
        name: createResourceName(deploymentConfig, "website-check"),
        artifactS3Location: pulumi.interpolate`s3://${syntheticsArtifactsBucket.bucket}/canary-artifacts`,
        executionRoleArn: syntheticsRole.arn,
        handler: "pageLoadBlueprint.handler",
        zipFile: "pageLoadBlueprint.zip",
        runtimeVersion: "syn-nodejs-puppeteer-6.2",
        startCanary: true,
        schedule: {
            expression: `rate(${Math.floor(monitoringConfig.syntheticsCheckFrequency / 60)} minutes)`
        },
        failureRetentionPeriod: monitoringConfig.logRetentionDays,
        successRetentionPeriod: monitoringConfig.logRetentionDays,
        runConfig: {
            timeoutInSeconds: 60,
            environmentVariables: {
                TARGET_URL: pulumi.interpolate`https://${containerAppsStackOutputs.publicAlbDnsName}`
            }
        },
        tags: createResourceTags(deploymentConfig, "synthetics-canary", {
            Type: "website-monitoring",
            Target: "primary-domain"
        })
    }, {
        dependsOn: [syntheticsRolePolicyAttachment, syntheticsS3Policy]
    });

    // Synthetics canary alarm
    const canaryFailureAlarm = new aws.cloudwatch.MetricAlarm("canary-failure", {
        name: createResourceName(deploymentConfig, "canary-failure"),
        description: "Synthetics canary failure alarm",
        metricName: "Failed",
        namespace: "CloudWatchSynthetics",
        statistic: "Sum",
        period: 300,
        evaluationPeriods: 1,
        threshold: 1,
        comparisonOperator: "GreaterThanOrEqualToThreshold",
        dimensions: {
            CanaryName: websiteCanary.name
        },
        alarmActions: [criticalAlertsTopic.arn],
        treatMissingData: "notBreaching",
        tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
            AlarmType: "synthetics-failure",
            Resource: "website-canary"
        })
    });
}

// =============================================================================
// CloudWatch Dashboard
// =============================================================================

// Create comprehensive dashboard
const infrastructureDashboard = new aws.cloudwatch.Dashboard("infrastructure-dashboard", {
    dashboardName: createResourceName(deploymentConfig, "infrastructure"),
    dashboardBody: pulumi.all([
        containerAppsStackOutputs.clusterName,
        containerAppsStackOutputs.publicAlbArn,
        databaseStackOutputs.databaseInstanceId,
        currentRegion
    ]).apply(([clusterName, albArn, dbInstanceId, region]) => {
        const albName = albArn.split('/').slice(1).join('/');

        return JSON.stringify({
            widgets: [
                {
                    type: "metric",
                    x: 0,
                    y: 0,
                    width: 12,
                    height: 6,
                    properties: {
                        metrics: [
                            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", albName],
                            [".", "RequestCount", ".", "."],
                            [".", "HTTPCode_Target_2XX_Count", ".", "."],
                            [".", "HTTPCode_Target_4XX_Count", ".", "."],
                            [".", "HTTPCode_Target_5XX_Count", ".", "."]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: region,
                        title: "Application Load Balancer Metrics",
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
                            ["AWS/ECS", "CPUUtilization", "ClusterName", clusterName],
                            [".", "MemoryUtilization", ".", "."]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: region,
                        title: "ECS Cluster Resource Utilization",
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
                            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", dbInstanceId],
                            [".", "DatabaseConnections", ".", "."],
                            [".", "FreeStorageSpace", ".", "."]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: region,
                        title: "RDS Database Metrics",
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
                            [`${deploymentConfig.projectName}/Application`, "ErrorCount"],
                            [".", "4xxErrors"],
                            [".", "5xxErrors"],
                            [`${deploymentConfig.projectName}/Security`, "SecurityEvents"]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: region,
                        title: "Application Error Metrics",
                        period: 300
                    }
                },
                ...(websiteCanary ? [{
                    type: "metric",
                    x: 0,
                    y: 12,
                    width: 24,
                    height: 6,
                    properties: {
                        metrics: [
                            ["CloudWatchSynthetics", "SuccessPercent", "CanaryName", websiteCanary.name],
                            [".", "Duration", ".", "."],
                            [".", "Failed", ".", "."]
                        ],
                        view: "timeSeries",
                        stacked: false,
                        region: region,
                        title: "Synthetic Monitoring",
                        period: 300
                    }
                }] : []),
                {
                    type: "log",
                    x: 0,
                    y: websiteCanary ? 18 : 12,
                    width: 24,
                    height: 6,
                    properties: {
                        query: `SOURCE '${applicationLogGroup.name}' | fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100`,
                        region: region,
                        title: "Recent Error Logs",
                        view: "table"
                    }
                }
            ]
        });
    })
});

// =============================================================================
// Outputs
// =============================================================================

// Required outputs
export const alertsTopicArn = alertsTopic.arn;
export const infrastructureDashboardUrl = pulumi.interpolate`https://${currentRegion}.console.aws.amazon.com/cloudwatch/home?region=${currentRegion}#dashboards:name=${infrastructureDashboard.dashboardName}`;
export const logGroupName = applicationLogGroup.name;

// Additional notification outputs
export const criticalAlertsTopicArn = criticalAlertsTopic.arn;
export const alertsTopicName = alertsTopic.name;
export const criticalAlertsTopicName = criticalAlertsTopic.name;

// Log group outputs
export const applicationLogGroupArn = applicationLogGroup.arn;
export const infrastructureLogGroupName = infrastructureLogGroup.name;
export const infrastructureLogGroupArn = infrastructureLogGroup.arn;
export const securityLogGroupName = securityLogGroup.name;
export const securityLogGroupArn = securityLogGroup.arn;

// Dashboard outputs
export const dashboardName = infrastructureDashboard.dashboardName;
export const dashboardArn = infrastructureDashboard.dashboardArn;

// Synthetics outputs
export const syntheticsArtifactsBucketName = syntheticsArtifactsBucket.bucket;
export const syntheticsArtifactsBucketArn = syntheticsArtifactsBucket.arn;
export const syntheticsRoleArn = syntheticsRole.arn;
export const websiteCanaryName = websiteCanary?.name || "";
export const websiteCanaryArn = websiteCanary?.arn || "";

// Alarm outputs
export const albHighLatencyAlarmArn = albHighLatencyAlarm.arn;
export const alb5xxErrorsAlarmArn = alb5xxErrorsAlarm.arn;
export const ecsHighCpuAlarmArn = ecsHighCpuAlarm.arn;
export const ecsHighMemoryAlarmArn = ecsHighMemoryAlarm.arn;
export const databaseHighConnectionsAlarmArn = databaseHighConnectionsAlarm.arn;
export const databaseHighCpuAlarmArn = databaseHighCpuAlarm.arn;
export const highErrorRateAlarmArn = highErrorRateAlarm.arn;
export const securityEventsAlarmArn = securityEventsAlarm.arn;

// Metric filter outputs
export const errorMetricFilterName = errorMetricFilter.name;
export const clientErrorMetricFilterName = clientErrorMetricFilter.name;
export const serverErrorMetricFilterName = serverErrorMetricFilter.name;
export const securityEventsFilterName = securityEventsFilter.name;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const environment = deploymentConfig.environment;
export const __exists = true;

// Comprehensive summary
export const summary = {
    notifications: {
        alertsTopicArn: alertsTopicArn,
        criticalAlertsTopicArn: criticalAlertsTopicArn,
        emailNotificationsEnabled: true,
        slackNotificationsEnabled: !!monitoringConfig.slackWebhookUrl,
        alertEmail: monitoringConfig.alertEmail,
        slackChannel: monitoringConfig.slackChannelName
    },
    logging: {
        applicationLogGroup: logGroupName,
        infrastructureLogGroup: infrastructureLogGroupName,
        securityLogGroup: securityLogGroupName,
        logRetentionDays: monitoringConfig.logRetentionDays,
        metricFilters: {
            errorRate: errorMetricFilterName,
            clientErrors: clientErrorMetricFilterName,
            serverErrors: serverErrorMetricFilterName,
            securityEvents: securityEventsFilterName
        }
    },
    monitoring: {
        dashboardUrl: infrastructureDashboardUrl,
        dashboardName: dashboardName,
        syntheticsEnabled: monitoringConfig.enableSynthetics,
        canaryName: websiteCanaryName,
        artifactsBucket: syntheticsArtifactsBucketName,
        detailedMonitoring: monitoringConfig.enableDetailedMonitoring
    },
    alarms: {
        total: 8,
        loadBalancer: {
            highLatency: albHighLatencyAlarmArn,
            serverErrors: alb5xxErrorsAlarmArn
        },
        ecsCluster: {
            highCpu: ecsHighCpuAlarmArn,
            highMemory: ecsHighMemoryAlarmArn
        },
        database: {
            highConnections: databaseHighConnectionsAlarmArn,
            highCpu: databaseHighCpuAlarmArn
        },
        application: {
            highErrorRate: highErrorRateAlarmArn,
            securityEvents: securityEventsAlarmArn
        }
    },
    thresholds: monitoringConfig.thresholds,
    configuration: {
        environment: deploymentConfig.environment,
        enableSynthetics: monitoringConfig.enableSynthetics,
        syntheticsCheckFrequency: monitoringConfig.syntheticsCheckFrequency,
        dashboardRefreshInterval: monitoringConfig.dashboardRefreshInterval
    }
};

console.log(`✅ Monitoring Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`📊 Dashboard: ${infrastructureDashboardUrl}`);
console.log(`🔔 Alerts Topic: ${alertsTopicArn}`);
console.log(`📧 Email Notifications: ${monitoringConfig.alertEmail}`);
console.log(`💬 Slack Notifications: ${monitoringConfig.slackWebhookUrl ? 'Enabled' : 'Disabled'}`);
console.log(`📝 Log Groups: ${logGroupName} (+ infrastructure, security)`);
console.log(`🎯 Synthetics Monitoring: ${monitoringConfig.enableSynthetics ? 'Enabled' : 'Disabled'}`);
console.log(`⚠️  Total Alarms: 8 (ALB: 2, ECS: 2, RDS: 2, App: 2)`);
console.log(`🗂️  Artifacts Bucket: ${syntheticsArtifactsBucketName}`);