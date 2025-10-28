import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    DNSOutputs,
    createLogGroup,
    createTargetGroup,
    getCurrentRegion,
    getCurrentAccountId,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Validate required configuration
validateConfig("containers-apps", config, []);

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

const dnsStackOutputs: DNSOutputs = {
    hostedZoneId: centralState.getStackOutput<string>("dns", "hostedZoneId"),
    domainName: centralState.getStackOutput<string>("dns", "domainName"),
    primaryCertificateArn: centralState.getStackOutput<string>("dns", "primaryCertificateArn"),
    wildcardCertificateArn: centralState.getStackOutput<string>("dns", "wildcardCertificateArn"),
    primaryHealthCheckId: centralState.getStackOutput<string>("dns", "primaryHealthCheckId")
};

// Get container images stack outputs
const containerImagesStackOutputs = {
    frontendRepoUrl: centralState.getStackOutput<string>("containers-images", "frontendRepoUrl"),
    backendRepoUrl: centralState.getStackOutput<string>("containers-images", "backendRepoUrl"),
    workerRepoUrl: centralState.getStackOutput<string>("containers-images", "workerRepoUrl"),
    nginxRepoUrl: centralState.getStackOutput<string>("containers-images", "nginxRepoUrl")
};

const STACK_NAME = "containers-apps";

// Container Applications Stack - ECS Fargate cluster with ALB and auto-scaling
console.log(`🚀 Deploying Container Applications Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters
const containerAppsConfig = {
    // Cluster configuration
    enableContainerInsights: config.getBoolean("enableContainerInsights") !== false, // Default true

    // Load Balancer configuration
    enableAccessLogging: config.getBoolean("enableAccessLogging") !== false, // Default true
    idleTimeout: config.getNumber("idleTimeout") || 60,
    enableDeletionProtection: config.getBoolean("enableDeletionProtection") || (deploymentConfig.environment === "prod"),

    // Auto-scaling configuration
    enableAutoScaling: config.getBoolean("enableAutoScaling") !== false, // Default true
    targetCpuUtilization: config.getNumber("targetCpuUtilization") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.targetCpuUtilization,
    scaleInCooldown: config.getNumber("scaleInCooldown") || 300, // 5 minutes
    scaleOutCooldown: config.getNumber("scaleOutCooldown") || 60, // 1 minute

    // Service discovery
    enableServiceDiscovery: config.getBoolean("enableServiceDiscovery") !== false, // Default true
    privateNamespace: config.get("privateNamespace") || `${deploymentConfig.deploymentId}.internal`,

    // Application services configuration
    services: {
        frontend: {
            cpu: config.getNumber("frontendCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("frontendMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("frontendDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.NODEJS,
            healthCheckPath: "/health",
            priority: 100,
            pathPattern: "*"
        },
        backend: {
            cpu: config.getNumber("backendCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("backendMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("backendDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.APPLICATION,
            healthCheckPath: "/api/health",
            priority: 200,
            pathPattern: "/api/*"
        },
        api: {
            cpu: config.getNumber("apiCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("apiMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("apiDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.APPLICATION,
            healthCheckPath: "/v1/health",
            priority: 300,
            pathPattern: "/v1/*"
        }
    },

    // Monitoring
    logRetentionDays: config.getNumber("logRetentionDays") || (deploymentConfig.environment === "prod" ? 90 : 30),
    enableDetailedMonitoring: config.getBoolean("enableDetailedMonitoring") !== false
};

// Get current AWS region and account ID
const currentRegion = getCurrentRegion();
const currentAccountId = getCurrentAccountId();

// =============================================================================
// ECS Cluster with Container Insights
// =============================================================================

const containerCluster = new aws.ecs.Cluster("container-cluster", {
    name: createResourceName(deploymentConfig, "container-cluster"),
    settings: [{
        name: "containerInsights",
        value: containerAppsConfig.enableContainerInsights ? "enabled" : "disabled"
    }],
    configuration: {
        executeCommandConfiguration: {
            kmsKeyId: securityStackOutputs.applicationKeyArn,
            logging: "OVERRIDE",
            logConfiguration: {
                cloudWatchEncryptionEnabled: true,
                cloudWatchLogGroupName: `/aws/ecs/cluster/${createResourceName(deploymentConfig, "container-cluster")}`
            }
        }
    },
    tags: createResourceTags(deploymentConfig, "ecs-cluster", {
        Name: createResourceName(deploymentConfig, "container-cluster"),
        Tier: "orchestration",
        Type: "container-apps"
    })
});

// CloudWatch Log Group for cluster logging
const clusterLogGroup = createLogGroup(
    `/aws/ecs/cluster/${createResourceName(deploymentConfig, "container-cluster")}`,
    containerAppsConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "ecs-cluster"
    })
);

// Cluster Capacity Providers
const clusterCapacityProviders = new aws.ecs.ClusterCapacityProviders("cluster-capacity-providers", {
    clusterName: containerCluster.name,
    capacityProviders: ["FARGATE", "FARGATE_SPOT"],
    defaultCapacityProviderStrategy: [
        {
            capacityProvider: "FARGATE",
            weight: 1,
            base: 1
        },
        {
            capacityProvider: "FARGATE_SPOT",
            weight: 3
        }
    ]
});

// =============================================================================
// Application Load Balancer
// =============================================================================

// S3 Bucket for ALB access logs (if enabled)
let albLogsBucket: aws.s3.Bucket | undefined;
if (containerAppsConfig.enableAccessLogging) {
    albLogsBucket = new aws.s3.Bucket("alb-access-logs", {
        bucket: createResourceName(deploymentConfig, "alb-access-logs"),
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
            id: "cleanup-old-logs",
            enabled: true,
            expiration: {
                days: containerAppsConfig.logRetentionDays
            }
        }],
        tags: createResourceTags(deploymentConfig, "s3-bucket", {
            Name: createResourceName(deploymentConfig, "alb-access-logs"),
            Purpose: "alb-logs"
        })
    });

    // Allow ALB to write to S3 bucket
    const albLogsBucketPolicy = new aws.s3.BucketPolicy("alb-logs-bucket-policy", {
        bucket: albLogsBucket.id,
        policy: pulumi.all([albLogsBucket.arn, currentAccountId]).apply(([bucketArn, accountId]) =>
            JSON.stringify({
                Version: "2012-10-17",
                Statement: [{
                    Effect: "Allow",
                    Principal: {
                        AWS: `arn:aws:iam::${getElbAccountId(deploymentConfig.region)}:root`
                    },
                    Action: "s3:PutObject",
                    Resource: `${bucketArn}/*`
                }, {
                    Effect: "Allow",
                    Principal: {
                        Service: "delivery.logs.amazonaws.com"
                    },
                    Action: "s3:PutObject",
                    Resource: `${bucketArn}/*`,
                    Condition: {
                        StringEquals: {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }, {
                    Effect: "Allow",
                    Principal: {
                        Service: "delivery.logs.amazonaws.com"
                    },
                    Action: "s3:GetBucketAcl",
                    Resource: bucketArn
                }]
            })
        )
    });
}

// Application Load Balancer
const publicAlb = new aws.lb.LoadBalancer("public-alb", {
    name: createResourceName(deploymentConfig, "public-alb"),
    internal: false,
    loadBalancerType: "application",
    securityGroups: [securityStackOutputs.loadBalancerSgId],
    subnets: networkStackOutputs.publicSubnetIds,
    enableDeletionProtection: containerAppsConfig.enableDeletionProtection,
    idleTimeout: containerAppsConfig.idleTimeout,
    accessLogs: containerAppsConfig.enableAccessLogging && albLogsBucket ? {
        bucket: albLogsBucket.bucket,
        enabled: true,
        prefix: "alb-logs"
    } : {
        enabled: false
    },
    tags: createResourceTags(deploymentConfig, "load-balancer", {
        Name: createResourceName(deploymentConfig, "public-alb"),
        Type: "application",
        Scheme: "internet-facing"
    })
});

// =============================================================================
// Service Discovery
// =============================================================================

let privateNamespace: aws.servicediscovery.PrivateDnsNamespace | undefined;
if (containerAppsConfig.enableServiceDiscovery) {
    privateNamespace = new aws.servicediscovery.PrivateDnsNamespace("container-apps-namespace", {
        name: containerAppsConfig.privateNamespace,
        description: `Private DNS namespace for ${deploymentConfig.deploymentId} container applications`,
        vpc: networkStackOutputs.vpcId,
        tags: createResourceTags(deploymentConfig, "service-discovery", {
            Name: containerAppsConfig.privateNamespace,
            Type: "private-dns"
        })
    });
}

// =============================================================================
// CloudWatch Log Groups for Services
// =============================================================================

const serviceLogGroups: Record<string, aws.cloudwatch.LogGroup> = {};

Object.keys(containerAppsConfig.services).forEach(serviceName => {
    serviceLogGroups[serviceName] = createLogGroup(
        `/aws/ecs/container-apps/${createResourceName(deploymentConfig, serviceName)}`,
        containerAppsConfig.logRetentionDays,
        createResourceTags(deploymentConfig, "log-group", {
            Service: serviceName,
            Type: "ecs-service"
        })
    );
});

// =============================================================================
// Target Groups for ALB
// =============================================================================

const targetGroups: Record<string, aws.lb.TargetGroup> = {};

Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
    targetGroups[serviceName] = createTargetGroup(
        createResourceName(deploymentConfig, serviceName, "tg"),
        serviceConfig.port,
        "HTTP",
        networkStackOutputs.vpcId,
        serviceConfig.healthCheckPath,
        createResourceTags(deploymentConfig, "target-group", {
            Service: serviceName
        })
    );
});

// =============================================================================
// Task Definitions
// =============================================================================

const taskDefinitions: Record<string, aws.ecs.TaskDefinition> = {};

Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
    const imageUrl = pulumi.interpolate`${containerImagesStackOutputs[`${serviceName}RepoUrl` as keyof typeof containerImagesStackOutputs]}:${deploymentConfig.environment}-latest`;

    taskDefinitions[serviceName] = new aws.ecs.TaskDefinition(`${serviceName}-task`, {
        family: createResourceName(deploymentConfig, serviceName, "task"),
        networkMode: "awsvpc",
        requiresCompatibilities: ["FARGATE"],
        cpu: serviceConfig.cpu.toString(),
        memory: serviceConfig.memory.toString(),
        executionRoleArn: securityStackOutputs.ecsExecutionRoleArn,
        taskRoleArn: securityStackOutputs.ecsTaskRoleArn,
        containerDefinitions: JSON.stringify([{
            name: serviceName,
            image: imageUrl,
            cpu: serviceConfig.cpu,
            memory: serviceConfig.memory,
            memoryReservation: Math.floor(serviceConfig.memory * 0.8),
            essential: true,
            portMappings: [{
                containerPort: serviceConfig.port,
                protocol: "tcp",
                name: serviceName
            }],
            healthCheck: {
                command: [
                    "CMD-SHELL",
                    `curl -f http://localhost:${serviceConfig.port}${serviceConfig.healthCheckPath} || exit 1`
                ],
                interval: 30,
                timeout: 5,
                retries: 3,
                startPeriod: 60
            },
            logConfiguration: {
                logDriver: "awslogs",
                options: {
                    "awslogs-group": serviceLogGroups[serviceName].name,
                    "awslogs-region": deploymentConfig.region,
                    "awslogs-stream-prefix": "ecs"
                }
            },
            environment: [
                {
                    name: "NODE_ENV",
                    value: deploymentConfig.environment
                },
                {
                    name: "AWS_REGION",
                    value: deploymentConfig.region
                },
                {
                    name: "SERVICE_NAME",
                    value: serviceName
                },
                {
                    name: "DEPLOYMENT_ID",
                    value: deploymentConfig.deploymentId
                },
                {
                    name: "DEPLOY_DOMAIN",
                    value: deploymentConfig.deployDomain
                },
                {
                    name: "PROJECT_NAME",
                    value: deploymentConfig.projectName
                },
                {
                    name: "PRIVATE_NAMESPACE",
                    value: containerAppsConfig.privateNamespace
                }
            ]
        }]),
        tags: createResourceTags(deploymentConfig, "task-definition", {
            Name: createResourceName(deploymentConfig, serviceName, "task"),
            Service: serviceName,
            Type: "fargate"
        })
    });
});

// =============================================================================
// Service Discovery Services
// =============================================================================

const discoveryServices: Record<string, aws.servicediscovery.Service> = {};

if (containerAppsConfig.enableServiceDiscovery && privateNamespace) {
    Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
        discoveryServices[serviceName] = new aws.servicediscovery.Service(`${serviceName}-discovery`, {
            name: serviceName,
            dnsConfig: {
                namespaceId: privateNamespace!.id,
                dnsRecords: [{
                    ttl: 10,
                    type: "A"
                }],
                routingPolicy: "MULTIVALUE"
            },
            healthCheckCustomConfig: {
                failureThreshold: 1
            },
            tags: createResourceTags(deploymentConfig, "service-discovery", {
                Name: serviceName,
                Service: serviceName
            })
        });
    });
}

// =============================================================================
// ECS Services
// =============================================================================

const ecsServices: Record<string, aws.ecs.Service> = {};

Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
    const serviceRegistries = containerAppsConfig.enableServiceDiscovery && discoveryServices[serviceName] ? [{
        registryArn: discoveryServices[serviceName].arn,
        containerName: serviceName,
        containerPort: serviceConfig.port
    }] : undefined;

    ecsServices[serviceName] = new aws.ecs.Service(`${serviceName}-service`, {
        name: createResourceName(deploymentConfig, serviceName, "service"),
        cluster: containerCluster.arn,
        taskDefinition: taskDefinitions[serviceName].arn,
        desiredCount: serviceConfig.desiredCount,
        launchType: "FARGATE",
        platformVersion: "LATEST",
        enableExecuteCommand: true,
        networkConfiguration: {
            subnets: networkStackOutputs.publicSubnetIds,
            securityGroups: [
                serviceName === "frontend" ? securityStackOutputs.webApplicationSgId : securityStackOutputs.apiApplicationSgId
            ],
            assignPublicIp: true
        },
        loadBalancers: [{
            targetGroupArn: targetGroups[serviceName].arn,
            containerName: serviceName,
            containerPort: serviceConfig.port
        }],
        serviceRegistries: serviceRegistries,
        deploymentConfiguration: {
            maximumPercent: 200,
            minimumHealthyPercent: 100,
            deploymentCircuitBreaker: {
                enable: true,
                rollback: true
            }
        },
        capacityProviderStrategy: [
            {
                capacityProvider: "FARGATE",
                weight: 1,
                base: 1
            },
            {
                capacityProvider: "FARGATE_SPOT",
                weight: 3
            }
        ],
        tags: createResourceTags(deploymentConfig, "ecs-service", {
            Name: createResourceName(deploymentConfig, serviceName, "service"),
            Service: serviceName,
            Type: "container-app"
        })
    }, {
        dependsOn: [clusterCapacityProviders, targetGroups[serviceName]]
    });
});

// =============================================================================
// ALB Listeners and Rules
// =============================================================================

// HTTPS Listener
const httpsListener = new aws.lb.Listener("https-listener", {
    loadBalancerArn: publicAlb.arn,
    port: COMMON_PORTS.HTTPS,
    protocol: "HTTPS",
    sslPolicy: "ELBSecurityPolicy-TLS-1-2-2017-01",
    certificateArn: dnsStackOutputs.wildcardCertificateArn,
    defaultActions: [{
        type: "forward",
        targetGroupArn: targetGroups.frontend.arn
    }],
    tags: createResourceTags(deploymentConfig, "lb-listener", {
        Name: "https-listener",
        Port: "443"
    })
});

// HTTP Listener (redirect to HTTPS)
const httpListener = new aws.lb.Listener("http-listener", {
    loadBalancerArn: publicAlb.arn,
    port: COMMON_PORTS.HTTP,
    protocol: "HTTP",
    defaultActions: [{
        type: "redirect",
        redirect: {
            port: COMMON_PORTS.HTTPS.toString(),
            protocol: "HTTPS",
            statusCode: "HTTP_301"
        }
    }],
    tags: createResourceTags(deploymentConfig, "lb-listener", {
        Name: "http-listener",
        Port: "80"
    })
});

// Listener Rules for path-based routing
const listenerRules: Record<string, aws.lb.ListenerRule> = {};

Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
    // Skip frontend as it's the default action
    if (serviceName === "frontend") return;

    listenerRules[serviceName] = new aws.lb.ListenerRule(`${serviceName}-rule`, {
        listenerArn: httpsListener.arn,
        priority: serviceConfig.priority,
        actions: [{
            type: "forward",
            targetGroupArn: targetGroups[serviceName].arn
        }],
        conditions: [{
            pathPattern: {
                values: [serviceConfig.pathPattern]
            }
        }],
        tags: createResourceTags(deploymentConfig, "lb-listener-rule", {
            Service: serviceName,
            PathPattern: serviceConfig.pathPattern
        })
    });
});

// =============================================================================
// Auto Scaling Configuration
// =============================================================================

const scalingTargets: Record<string, aws.appautoscaling.Target> = {};
const scalingPolicies: Record<string, aws.appautoscaling.Policy> = {};

if (containerAppsConfig.enableAutoScaling) {
    Object.entries(containerAppsConfig.services).forEach(([serviceName, serviceConfig]) => {
        // Auto-scaling target
        scalingTargets[serviceName] = new aws.appautoscaling.Target(`${serviceName}-scaling-target`, {
            maxCapacity: ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.maxCapacity,
            minCapacity: ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            resourceId: pulumi.interpolate`service/${containerCluster.name}/${ecsServices[serviceName].name}`,
            scalableDimension: "ecs:service:DesiredCount",
            serviceNamespace: "ecs",
            tags: createResourceTags(deploymentConfig, "scaling-target", {
                Service: serviceName
            })
        });

        // CPU-based scaling policy
        scalingPolicies[serviceName] = new aws.appautoscaling.Policy(`${serviceName}-cpu-scaling-policy`, {
            name: createResourceName(deploymentConfig, serviceName, "cpu-scaling"),
            policyType: "TargetTrackingScaling",
            resourceId: scalingTargets[serviceName].resourceId,
            scalableDimension: scalingTargets[serviceName].scalableDimension,
            serviceNamespace: scalingTargets[serviceName].serviceNamespace,
            targetTrackingScalingPolicyConfiguration: {
                targetValue: containerAppsConfig.targetCpuUtilization,
                predefinedMetricSpecification: {
                    predefinedMetricType: "ECSServiceAverageCPUUtilization"
                },
                scaleInCooldown: containerAppsConfig.scaleInCooldown,
                scaleOutCooldown: containerAppsConfig.scaleOutCooldown
            }
        });
    });
}

// =============================================================================
// DNS Records
// =============================================================================

// Primary DNS record for the application
const primaryDnsRecord = new aws.route53.Record("primary-dns-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: deploymentConfig.deployDomain,
    type: "A",
    aliases: [{
        name: publicAlb.dnsName,
        zoneId: publicAlb.zoneId,
        evaluateTargetHealth: true
    }],
    tags: createResourceTags(deploymentConfig, "dns-record", {
        Name: deploymentConfig.deployDomain,
        Type: "primary"
    })
});

// API subdomain record
const apiDnsRecord = new aws.route53.Record("api-dns-record", {
    zoneId: dnsStackOutputs.hostedZoneId,
    name: `api.${deploymentConfig.deployDomain}`,
    type: "A",
    aliases: [{
        name: publicAlb.dnsName,
        zoneId: publicAlb.zoneId,
        evaluateTargetHealth: true
    }],
    tags: createResourceTags(deploymentConfig, "dns-record", {
        Name: `api.${deploymentConfig.deployDomain}`,
        Type: "api"
    })
});

// =============================================================================
// CloudWatch Alarms for Monitoring
// =============================================================================

const cloudWatchAlarms: Record<string, aws.cloudwatch.MetricAlarm> = {};

if (containerAppsConfig.enableDetailedMonitoring) {
    Object.keys(containerAppsConfig.services).forEach(serviceName => {
        // High CPU alarm
        cloudWatchAlarms[`${serviceName}-high-cpu`] = new aws.cloudwatch.MetricAlarm(`${serviceName}-high-cpu-alarm`, {
            name: createResourceName(deploymentConfig, serviceName, "high-cpu"),
            description: `High CPU utilization for ${serviceName} service`,
            metricName: "CPUUtilization",
            namespace: "AWS/ECS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 80,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                ServiceName: ecsServices[serviceName].name,
                ClusterName: containerCluster.name
            },
            treatMissingData: "notBreaching",
            tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
                Service: serviceName,
                Type: "cpu-utilization"
            })
        });

        // Target group healthy hosts alarm
        cloudWatchAlarms[`${serviceName}-unhealthy-hosts`] = new aws.cloudwatch.MetricAlarm(`${serviceName}-unhealthy-hosts-alarm`, {
            name: createResourceName(deploymentConfig, serviceName, "unhealthy-hosts"),
            description: `Unhealthy hosts in ${serviceName} target group`,
            metricName: "HealthyHostCount",
            namespace: "AWS/ApplicationELB",
            statistic: "Average",
            period: 60,
            evaluationPeriods: 2,
            threshold: 1,
            comparisonOperator: "LessThanThreshold",
            dimensions: {
                TargetGroup: targetGroups[serviceName].arnSuffix,
                LoadBalancer: publicAlb.arnSuffix
            },
            treatMissingData: "breaching",
            tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
                Service: serviceName,
                Type: "target-health"
            })
        });
    });

    // ALB response time alarm
    const albResponseTimeAlarm = new aws.cloudwatch.MetricAlarm("alb-response-time-alarm", {
        name: createResourceName(deploymentConfig, "alb-response-time"),
        description: "High response time for Application Load Balancer",
        metricName: "TargetResponseTime",
        namespace: "AWS/ApplicationELB",
        statistic: "Average",
        period: 300,
        evaluationPeriods: 2,
        threshold: 1, // 1 second
        comparisonOperator: "GreaterThanThreshold",
        dimensions: {
            LoadBalancer: publicAlb.arnSuffix
        },
        treatMissingData: "notBreaching",
        tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
            Type: "response-time",
            Resource: "load-balancer"
        })
    });
}

// =============================================================================
// Utility Functions
// =============================================================================

// Get ELB Account ID for the region (for S3 bucket policies)
function getElbAccountId(region: string): string {
    const elbAccountIds: Record<string, string> = {
        "us-east-1": "127311923021",
        "us-east-2": "033677994240",
        "us-west-1": "027434742980",
        "us-west-2": "797873946194",
        "eu-west-1": "156460612806",
        "eu-central-1": "054676820928",
        "ap-southeast-1": "114774131450",
        "ap-northeast-1": "582318560864"
    };
    return elbAccountIds[region] || "127311923021"; // Default to us-east-1
}

// =============================================================================
// Outputs
// =============================================================================

// Required outputs
export const publicAlbDnsName = publicAlb.dnsName;
export const clusterArn = containerCluster.arn;
export const frontendServiceName = ecsServices.frontend?.name || "";

// ALB outputs
export const publicAlbArn = publicAlb.arn;
export const publicAlbZoneId = publicAlb.zoneId;
export const publicAlbCanonicalHostedZoneId = publicAlb.zoneId;
export const httpsListenerArn = httpsListener.arn;
export const httpListenerArn = httpListener.arn;

// Cluster outputs
export const clusterName = containerCluster.name;
export const clusterId = containerCluster.id;
export const containerInsightsEnabled = containerAppsConfig.enableContainerInsights;

// Service outputs
export const frontendServiceArn = ecsServices.frontend?.arn || "";
export const backendServiceArn = ecsServices.backend?.arn || "";
export const apiServiceArn = ecsServices.api?.arn || "";

// Task definition outputs
export const frontendTaskDefinitionArn = taskDefinitions.frontend?.arn || "";
export const backendTaskDefinitionArn = taskDefinitions.backend?.arn || "";
export const apiTaskDefinitionArn = taskDefinitions.api?.arn || "";

// Target group outputs
export const frontendTargetGroupArn = targetGroups.frontend?.arn || "";
export const backendTargetGroupArn = targetGroups.backend?.arn || "";
export const apiTargetGroupArn = targetGroups.api?.arn || "";

// Service discovery outputs
export const privateNamespaceId = privateNamespace?.id || "";
export const privateNamespaceName = privateNamespace?.name || "";
export const frontendDiscoveryServiceArn = discoveryServices.frontend?.arn || "";
export const backendDiscoveryServiceArn = discoveryServices.backend?.arn || "";
export const apiDiscoveryServiceArn = discoveryServices.api?.arn || "";

// Auto-scaling outputs
export const frontendScalingTargetArn = scalingTargets.frontend?.arn || "";
export const backendScalingTargetArn = scalingTargets.backend?.arn || "";
export const apiScalingTargetArn = scalingTargets.api?.arn || "";

// DNS outputs
export const primaryDnsName = deploymentConfig.deployDomain;
export const apiDnsName = `api.${deploymentConfig.deployDomain}`;
export const primaryDnsRecordName = primaryDnsRecord.name;
export const apiDnsRecordName = apiDnsRecord.name;

// Log group outputs
export const clusterLogGroupArn = clusterLogGroup.arn;
export const clusterLogGroupName = clusterLogGroup.name;
export const frontendLogGroupName = serviceLogGroups.frontend?.name || "";
export const backendLogGroupName = serviceLogGroups.backend?.name || "";
export const apiLogGroupName = serviceLogGroups.api?.name || "";

// Access logs bucket
export const albLogsBucketName = albLogsBucket?.bucket || "";
export const albLogsBucketArn = albLogsBucket?.arn || "";

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const environment = deploymentConfig.environment;
export const __exists = true;

// Comprehensive summary for easier consumption
export const summary = {
    loadBalancer: {
        dnsName: publicAlbDnsName,
        arn: publicAlbArn,
        zoneId: publicAlbZoneId,
        httpsListener: httpsListenerArn,
        accessLogs: containerAppsConfig.enableAccessLogging
    },
    cluster: {
        arn: clusterArn,
        name: clusterName,
        containerInsights: containerInsightsEnabled
    },
    services: {
        count: Object.keys(ecsServices).length,
        names: Object.keys(ecsServices),
        frontend: {
            serviceArn: frontendServiceArn,
            taskDefinitionArn: frontendTaskDefinitionArn,
            targetGroupArn: frontendTargetGroupArn,
            discoveryServiceArn: frontendDiscoveryServiceArn,
            logGroupName: frontendLogGroupName
        },
        backend: {
            serviceArn: backendServiceArn,
            taskDefinitionArn: backendTaskDefinitionArn,
            targetGroupArn: backendTargetGroupArn,
            discoveryServiceArn: backendDiscoveryServiceArn,
            logGroupName: backendLogGroupName
        },
        api: {
            serviceArn: apiServiceArn,
            taskDefinitionArn: apiTaskDefinitionArn,
            targetGroupArn: apiTargetGroupArn,
            discoveryServiceArn: apiDiscoveryServiceArn,
            logGroupName: apiLogGroupName
        }
    },
    serviceDiscovery: {
        enabled: containerAppsConfig.enableServiceDiscovery,
        namespaceId: privateNamespaceId,
        namespaceName: containerAppsConfig.privateNamespace
    },
    autoScaling: {
        enabled: containerAppsConfig.enableAutoScaling,
        targetCpuUtilization: containerAppsConfig.targetCpuUtilization,
        policies: Object.keys(scalingPolicies).length
    },
    dns: {
        primaryDomain: primaryDnsName,
        apiDomain: apiDnsName,
        sslCertificate: "wildcard-enabled"
    },
    monitoring: {
        containerInsights: containerInsightsEnabled,
        detailedMonitoring: containerAppsConfig.enableDetailedMonitoring,
        logRetentionDays: containerAppsConfig.logRetentionDays,
        alarms: Object.keys(cloudWatchAlarms).length
    },
    configuration: {
        environment: deploymentConfig.environment,
        logRetentionDays: containerAppsConfig.logRetentionDays,
        enableDeletionProtection: containerAppsConfig.enableDeletionProtection,
        enableAccessLogging: containerAppsConfig.enableAccessLogging
    }
};

console.log(`✅ Container Applications Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`🌐 Public ALB DNS: ${publicAlbDnsName}`);
console.log(`🏗️  ECS Cluster: ${clusterName} (${containerInsightsEnabled ? 'Container Insights enabled' : 'Basic monitoring'})`);
console.log(`🎯 Service Discovery: ${containerAppsConfig.enableServiceDiscovery ? 'Enabled' : 'Disabled'}${privateNamespace ? ` (${containerAppsConfig.privateNamespace})` : ''}`);
console.log(`📈 Auto-scaling: ${containerAppsConfig.enableAutoScaling ? 'Enabled' : 'Disabled'} (CPU target: ${containerAppsConfig.targetCpuUtilization}%)`);
console.log(`🚀 Deployed ${Object.keys(ecsServices).length} container applications: ${Object.keys(ecsServices).join(', ')}`);
console.log(`🔐 SSL/TLS: Enabled with wildcard certificate`);
console.log(`📊 Monitoring: ${containerAppsConfig.enableDetailedMonitoring ? 'Detailed' : 'Basic'} (${Object.keys(cloudWatchAlarms).length} alarms)`);
console.log(`🌍 Primary Domain: ${primaryDnsName}`);
console.log(`🔗 API Domain: ${apiDnsName}`);