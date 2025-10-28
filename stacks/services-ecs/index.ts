import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    createLogGroup,
    getCurrentRegion,
    getCurrentAccountId,
    ENVIRONMENT_DEFAULTS,
    COMMON_PORTS
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Validate required configuration
validateConfig("services-ecs", config, []);

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

// Get ECR stack outputs
const ecrStackOutputs = {
    registryUri: centralState.getStackOutput<string>("services-ecr", "registryUri"),
    frontendRepoUrl: centralState.getStackOutput<string>("services-ecr", "frontendRepoUrl"),
    backendRepoUrl: centralState.getStackOutput<string>("services-ecr", "backendRepoUrl"),
    apiRepoUrl: centralState.getStackOutput<string>("services-ecr", "apiRepoUrl"),
    workerRepoUrl: centralState.getStackOutput<string>("services-ecr", "workerRepoUrl"),
    schedulerRepoUrl: centralState.getStackOutput<string>("services-ecr", "schedulerRepoUrl")
};

const STACK_NAME = "services-ecs";

// ECS Services Stack - Dedicated ECS cluster for microservices with auto-scaling and service discovery
console.log(`🚀 Deploying ECS Services Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters
const ecsConfig = {
    // Cluster configuration
    enableContainerInsights: config.getBoolean("enableContainerInsights") !== false, // Default true

    // Capacity providers configuration
    enableFargateSpot: config.getBoolean("enableFargateSpot") !== false, // Default true
    fargateBaseCapacity: config.getNumber("fargateBaseCapacity") || 1,
    fargateSpotCapacity: config.getNumber("fargateSpotCapacity") || 3,

    // Auto-scaling configuration
    enableAutoScaling: config.getBoolean("enableAutoScaling") !== false, // Default true
    targetCpuUtilization: config.getNumber("targetCpuUtilization") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.targetCpuUtilization,
    scaleInCooldown: config.getNumber("scaleInCooldown") || 300, // 5 minutes
    scaleOutCooldown: config.getNumber("scaleOutCooldown") || 60, // 1 minute

    // Service discovery
    enableServiceDiscovery: config.getBoolean("enableServiceDiscovery") !== false, // Default true
    privateNamespace: config.get("privateNamespace") || `${deploymentConfig.deploymentId}.internal`,

    // Services configuration
    services: {
        frontend: {
            cpu: config.getNumber("frontendCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("frontendMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("frontendDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.NODEJS,
            healthCheckPath: "/health"
        },
        backend: {
            cpu: config.getNumber("backendCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("backendMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("backendDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.APPLICATION,
            healthCheckPath: "/api/health"
        },
        api: {
            cpu: config.getNumber("apiCpu") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.cpu,
            memory: config.getNumber("apiMemory") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].container.memory,
            desiredCount: config.getNumber("apiDesiredCount") || ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            port: COMMON_PORTS.APPLICATION,
            healthCheckPath: "/api/health"
        }
    },

    // Monitoring
    logRetentionDays: config.getNumber("logRetentionDays") || 14,
    enableDetailedMonitoring: config.getBoolean("enableDetailedMonitoring") !== false
};

// Get current AWS region and account ID
const currentRegion = getCurrentRegion();
const currentAccountId = getCurrentAccountId();

// =============================================================================
// ECS Cluster with Mixed Capacity Providers
// =============================================================================

// ECS Cluster
const servicesCluster = new aws.ecs.Cluster("services-cluster", {
    name: createResourceName(deploymentConfig, "services-cluster"),
    settings: [{
        name: "containerInsights",
        value: ecsConfig.enableContainerInsights ? "enabled" : "disabled"
    }],
    configuration: {
        executeCommandConfiguration: {
            kmsKeyId: securityStackOutputs.applicationKeyArn,
            logging: "OVERRIDE",
            logConfiguration: {
                cloudWatchEncryptionEnabled: true,
                cloudWatchLogGroupName: `/aws/ecs/cluster/${createResourceName(deploymentConfig, "services-cluster")}`
            }
        }
    },
    tags: createResourceTags(deploymentConfig, "ecs-cluster", {
        Name: createResourceName(deploymentConfig, "services-cluster"),
        Tier: "orchestration",
        Type: "microservices"
    })
});

// CloudWatch Log Group for cluster logging
const clusterLogGroup = createLogGroup(
    `cluster-${servicesCluster.name}-logs`,
    ecsConfig.logRetentionDays,
    createResourceTags(deploymentConfig, "log-group", {
        Service: "ecs-cluster"
    })
);

// Fargate Capacity Provider
const fargateCapacityProvider = new aws.ecs.CapacityProvider("fargate-cp", {
    name: createResourceName(deploymentConfig, "fargate-cp"),
    autoScalingGroupProvider: {
        autoScalingGroupArn: "", // Not used for Fargate
        managedTerminationProtection: "DISABLED"
    },
    tags: createResourceTags(deploymentConfig, "capacity-provider", {
        Name: createResourceName(deploymentConfig, "fargate-cp"),
        Type: "fargate"
    })
});

// Fargate Spot Capacity Provider (if enabled)
let fargateSpotCapacityProvider: aws.ecs.CapacityProvider | undefined;
if (ecsConfig.enableFargateSpot) {
    fargateSpotCapacityProvider = new aws.ecs.CapacityProvider("fargate-spot-cp", {
        name: createResourceName(deploymentConfig, "fargate-spot-cp"),
        autoScalingGroupProvider: {
            autoScalingGroupArn: "", // Not used for Fargate
            managedTerminationProtection: "DISABLED"
        },
        tags: createResourceTags(deploymentConfig, "capacity-provider", {
            Name: createResourceName(deploymentConfig, "fargate-spot-cp"),
            Type: "fargate-spot"
        })
    });
}

// Cluster Capacity Providers Association
const capacityProviders = ecsConfig.enableFargateSpot
    ? ["FARGATE", "FARGATE_SPOT"]
    : ["FARGATE"];

const clusterCapacityProviders = new aws.ecs.ClusterCapacityProviders("cluster-capacity-providers", {
    clusterName: servicesCluster.name,
    capacityProviders: capacityProviders,
    defaultCapacityProviderStrategy: ecsConfig.enableFargateSpot ? [
        {
            capacityProvider: "FARGATE",
            weight: ecsConfig.fargateBaseCapacity,
            base: 1
        },
        {
            capacityProvider: "FARGATE_SPOT",
            weight: ecsConfig.fargateSpotCapacity
        }
    ] : [
        {
            capacityProvider: "FARGATE",
            weight: 1,
            base: 1
        }
    ]
});

// =============================================================================
// Service Discovery with Private DNS Namespace
// =============================================================================

let privateNamespace: aws.servicediscovery.PrivateDnsNamespace | undefined;
if (ecsConfig.enableServiceDiscovery) {
    privateNamespace = new aws.servicediscovery.PrivateDnsNamespace("services-private-namespace", {
        name: ecsConfig.privateNamespace,
        description: `Private DNS namespace for ${deploymentConfig.deploymentId} microservices`,
        vpc: networkStackOutputs.vpcId,
        tags: createResourceTags(deploymentConfig, "service-discovery", {
            Name: ecsConfig.privateNamespace,
            Type: "private-dns"
        })
    });
}

// =============================================================================
// CloudWatch Log Groups for Services
// =============================================================================

const serviceLogGroups: Record<string, aws.cloudwatch.LogGroup> = {};

Object.keys(ecsConfig.services).forEach(serviceName => {
    serviceLogGroups[serviceName] = createLogGroup(
        `/aws/ecs/${createResourceName(deploymentConfig, serviceName)}`,
        ecsConfig.logRetentionDays,
        createResourceTags(deploymentConfig, "log-group", {
            Service: serviceName,
            Type: "ecs-service"
        })
    );
});

// =============================================================================
// Task Definitions for Services
// =============================================================================

const taskDefinitions: Record<string, aws.ecs.TaskDefinition> = {};

Object.entries(ecsConfig.services).forEach(([serviceName, serviceConfig]) => {
    const imageUrl = pulumi.interpolate`${ecrStackOutputs[`${serviceName}RepoUrl` as keyof typeof ecrStackOutputs]}:latest`;

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
// Auto-Scaling Targets and Policies
// =============================================================================

const scalingTargets: Record<string, aws.appautoscaling.Target> = {};
const scalingPolicies: Record<string, aws.appautoscaling.Policy> = {};

if (ecsConfig.enableAutoScaling) {
    Object.entries(ecsConfig.services).forEach(([serviceName, serviceConfig]) => {
        // Auto-scaling target
        scalingTargets[serviceName] = new aws.appautoscaling.Target(`${serviceName}-scaling-target`, {
            maxCapacity: ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.maxCapacity,
            minCapacity: ENVIRONMENT_DEFAULTS[deploymentConfig.environment].autoScaling.minCapacity,
            resourceId: pulumi.interpolate`service/${servicesCluster.name}/${createResourceName(deploymentConfig, serviceName, "service")}`,
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
                targetValue: ecsConfig.targetCpuUtilization,
                predefinedMetricSpecification: {
                    predefinedMetricType: "ECSServiceAverageCPUUtilization"
                },
                scaleInCooldown: ecsConfig.scaleInCooldown,
                scaleOutCooldown: ecsConfig.scaleOutCooldown
            }
        });
    });
}

// =============================================================================
// Service Discovery Services
// =============================================================================

const discoveryServices: Record<string, aws.servicediscovery.Service> = {};

if (ecsConfig.enableServiceDiscovery && privateNamespace) {
    Object.entries(ecsConfig.services).forEach(([serviceName, serviceConfig]) => {
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

Object.entries(ecsConfig.services).forEach(([serviceName, serviceConfig]) => {
    const serviceRegistries = ecsConfig.enableServiceDiscovery && discoveryServices[serviceName] ? [{
        registryArn: discoveryServices[serviceName].arn,
        containerName: serviceName,
        containerPort: serviceConfig.port
    }] : undefined;

    ecsServices[serviceName] = new aws.ecs.Service(`${serviceName}-service`, {
        name: createResourceName(deploymentConfig, serviceName, "service"),
        cluster: servicesCluster.arn,
        taskDefinition: taskDefinitions[serviceName].arn,
        desiredCount: serviceConfig.desiredCount,
        launchType: "FARGATE",
        platformVersion: "LATEST",
        enableExecuteCommand: true,
        networkConfiguration: {
            subnets: networkStackOutputs.privateSubnetIds,
            securityGroups: [
                serviceName === "frontend" ? securityStackOutputs.webApplicationSgId : securityStackOutputs.apiApplicationSgId
            ],
            assignPublicIp: false
        },
        serviceRegistries: serviceRegistries,
        deploymentConfiguration: {
            maximumPercent: 200,
            minimumHealthyPercent: 100,
            deploymentCircuitBreaker: {
                enable: true,
                rollback: true
            }
        },
        capacityProviderStrategy: ecsConfig.enableFargateSpot ? [
            {
                capacityProvider: "FARGATE",
                weight: ecsConfig.fargateBaseCapacity,
                base: 1
            },
            {
                capacityProvider: "FARGATE_SPOT",
                weight: ecsConfig.fargateSpotCapacity
            }
        ] : [
            {
                capacityProvider: "FARGATE",
                weight: 1,
                base: 1
            }
        ],
        tags: createResourceTags(deploymentConfig, "ecs-service", {
            Name: createResourceName(deploymentConfig, serviceName, "service"),
            Service: serviceName,
            Type: "microservice"
        })
    }, {
        dependsOn: [clusterCapacityProviders]
    });
});

// =============================================================================
// CloudWatch Alarms for Monitoring
// =============================================================================

const cloudWatchAlarms: Record<string, aws.cloudwatch.MetricAlarm> = {};

if (ecsConfig.enableDetailedMonitoring) {
    Object.keys(ecsConfig.services).forEach(serviceName => {
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
                ServiceName: createResourceName(deploymentConfig, serviceName, "service"),
                ClusterName: servicesCluster.name
            },
            alarmActions: [],
            treatMissingData: "notBreaching",
            tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
                Service: serviceName,
                Type: "cpu-utilization"
            })
        });

        // High memory alarm
        cloudWatchAlarms[`${serviceName}-high-memory`] = new aws.cloudwatch.MetricAlarm(`${serviceName}-high-memory-alarm`, {
            name: createResourceName(deploymentConfig, serviceName, "high-memory"),
            description: `High memory utilization for ${serviceName} service`,
            metricName: "MemoryUtilization",
            namespace: "AWS/ECS",
            statistic: "Average",
            period: 300,
            evaluationPeriods: 2,
            threshold: 80,
            comparisonOperator: "GreaterThanThreshold",
            dimensions: {
                ServiceName: createResourceName(deploymentConfig, serviceName, "service"),
                ClusterName: servicesCluster.name
            },
            alarmActions: [],
            treatMissingData: "notBreaching",
            tags: createResourceTags(deploymentConfig, "cloudwatch-alarm", {
                Service: serviceName,
                Type: "memory-utilization"
            })
        });
    });
}

// =============================================================================
// Outputs
// =============================================================================

// Required outputs
export const servicesClusterArn = servicesCluster.arn;
export const servicesClusterId = servicesCluster.id;
export const servicesClusterName = servicesCluster.name;
export const privateNamespaceId = privateNamespace?.id || "";
export const privateNamespaceName = privateNamespace?.name || "";

// Primary API scaling target ARN (as requested)
export const apiScalingTargetArn = scalingTargets.api?.arn || "";

// Service outputs
export const frontendServiceArn = ecsServices.frontend?.arn || "";
export const backendServiceArn = ecsServices.backend?.arn || "";
export const apiServiceArn = ecsServices.api?.arn || "";

// Task definition outputs
export const frontendTaskDefinitionArn = taskDefinitions.frontend?.arn || "";
export const backendTaskDefinitionArn = taskDefinitions.backend?.arn || "";
export const apiTaskDefinitionArn = taskDefinitions.api?.arn || "";

// Service discovery outputs
export const frontendDiscoveryServiceArn = discoveryServices.frontend?.arn || "";
export const backendDiscoveryServiceArn = discoveryServices.backend?.arn || "";
export const apiDiscoveryServiceArn = discoveryServices.api?.arn || "";

// Auto-scaling outputs
export const frontendScalingTargetArn = scalingTargets.frontend?.arn || "";
export const backendScalingTargetArn = scalingTargets.backend?.arn || "";

// Capacity provider outputs
export const fargateCapacityProviderName = "FARGATE";
export const fargateSpotCapacityProviderName = ecsConfig.enableFargateSpot ? "FARGATE_SPOT" : "";
export const capacityProviderStrategy = clusterCapacityProviders.defaultCapacityProviderStrategy;

// Monitoring outputs
export const containerInsightsEnabled = ecsConfig.enableContainerInsights;
export const clusterLogGroupArn = clusterLogGroup.arn;
export const clusterLogGroupName = clusterLogGroup.name;

// Service configuration outputs
export const serviceConfiguration = {
    cluster: {
        arn: servicesClusterArn,
        name: servicesClusterName,
        containerInsights: ecsConfig.enableContainerInsights,
        capacityProviders: capacityProviders
    },
    serviceDiscovery: {
        enabled: ecsConfig.enableServiceDiscovery,
        namespaceId: privateNamespaceId,
        namespaceName: privateNamespaceName
    },
    autoScaling: {
        enabled: ecsConfig.enableAutoScaling,
        targetCpuUtilization: ecsConfig.targetCpuUtilization,
        scaleInCooldown: ecsConfig.scaleInCooldown,
        scaleOutCooldown: ecsConfig.scaleOutCooldown
    },
    services: Object.keys(ecsConfig.services).reduce((acc, serviceName) => {
        acc[serviceName] = {
            serviceArn: ecsServices[serviceName]?.arn || "",
            taskDefinitionArn: taskDefinitions[serviceName]?.arn || "",
            discoveryServiceArn: discoveryServices[serviceName]?.arn || "",
            scalingTargetArn: scalingTargets[serviceName]?.arn || "",
            logGroupName: serviceLogGroups[serviceName]?.name || "",
            cpu: ecsConfig.services[serviceName].cpu,
            memory: ecsConfig.services[serviceName].memory,
            desiredCount: ecsConfig.services[serviceName].desiredCount
        };
        return acc;
    }, {} as Record<string, any>)
};

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const environment = deploymentConfig.environment;
export const __exists = true;

// Comprehensive summary
export const summary = {
    cluster: {
        arn: servicesClusterArn,
        name: servicesClusterName,
        containerInsights: containerInsightsEnabled,
        capacityProviders: capacityProviders
    },
    serviceDiscovery: {
        enabled: ecsConfig.enableServiceDiscovery,
        namespaceId: privateNamespaceId,
        namespace: ecsConfig.privateNamespace
    },
    autoScaling: {
        enabled: ecsConfig.enableAutoScaling,
        targetCpuUtilization: ecsConfig.targetCpuUtilization,
        policies: Object.keys(scalingPolicies).length
    },
    services: {
        count: Object.keys(ecsServices).length,
        names: Object.keys(ecsServices),
        totalDesiredCapacity: Object.values(ecsConfig.services).reduce((sum, config) => sum + config.desiredCount, 0)
    },
    monitoring: {
        containerInsights: containerInsightsEnabled,
        detailedMonitoring: ecsConfig.enableDetailedMonitoring,
        logGroups: Object.keys(serviceLogGroups).length,
        alarms: Object.keys(cloudWatchAlarms).length
    },
    configuration: {
        enableFargateSpot: ecsConfig.enableFargateSpot,
        logRetentionDays: ecsConfig.logRetentionDays,
        environment: deploymentConfig.environment
    }
};

console.log(`✅ ECS Services Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`🎯 Created ECS cluster: ${servicesClusterName} with ${capacityProviders.length} capacity providers`);
console.log(`🔍 Service Discovery: ${ecsConfig.enableServiceDiscovery ? 'Enabled' : 'Disabled'}${privateNamespace ? ` (${ecsConfig.privateNamespace})` : ''}`);
console.log(`📈 Auto-scaling: ${ecsConfig.enableAutoScaling ? 'Enabled' : 'Disabled'} (CPU target: ${ecsConfig.targetCpuUtilization}%)`);
console.log(`🚀 Deployed ${Object.keys(ecsServices).length} microservices: ${Object.keys(ecsServices).join(', ')}`);
console.log(`📊 Container Insights: ${containerInsightsEnabled ? 'Enabled' : 'Disabled'}`);
console.log(`💰 Fargate Spot: ${ecsConfig.enableFargateSpot ? 'Enabled' : 'Disabled'} (Cost optimization)`);