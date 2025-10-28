import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    SecurityOutputs,
    getCurrentAccountId,
    getCurrentRegion,
    ENVIRONMENT_DEFAULTS
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Get security stack outputs
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

const STACK_NAME = "services-ecr";

// ECR Services Stack - Enhanced registry services with cross-region replication and advanced scanning
console.log(`🚀 Deploying ECR Services Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters
const ecrConfig = {
    // Base image repositories
    baseImageRepos: ["alpine", "node", "nginx", "postgres", "redis", "python"],

    // Application repositories
    applicationRepos: ["frontend", "backend", "api", "worker", "scheduler"],

    // Registry configuration
    enableRegistryScanning: config.getBoolean("enableRegistryScanning") !== false, // Default true
    enableCrossRegionReplication: config.getBoolean("enableCrossRegionReplication") !== false, // Default true
    replicationRegions: config.getObject<string[]>("replicationRegions") || ["us-west-2", "eu-west-1"],

    // Image management
    imageTagImmutability: config.get("imageTagImmutability") || "IMMUTABLE", // For base images
    appImageTagImmutability: config.get("appImageTagImmutability") || "MUTABLE", // For app images
    maxProductionImages: config.getNumber("maxProductionImages") || 20,
    maxStagingImages: config.getNumber("maxStagingImages") || 10,
    maxDevelopmentImages: config.getNumber("maxDevelopmentImages") || 5,

    // Vulnerability scanning
    enableEnhancedScanning: config.getBoolean("enableEnhancedScanning") !== false,
    scanOnPush: config.getBoolean("scanOnPush") !== false,
    continuousScanning: config.getBoolean("continuousScanning") !== false,

    // Notification settings
    enableScanNotifications: config.getBoolean("enableScanNotifications") !== false,
    criticalVulnerabilityThreshold: config.getNumber("criticalVulnerabilityThreshold") || 0,
    highVulnerabilityThreshold: config.getNumber("highVulnerabilityThreshold") || 5
};

// Get current AWS account ID and region
const currentAccountId = getCurrentAccountId();
const currentRegion = getCurrentRegion();

// Filter replication regions to exclude current region
const replicationTargets = ecrConfig.replicationRegions.filter(region => region !== deploymentConfig.region);

// =============================================================================
// Registry Scanning Configuration
// =============================================================================

// Enhanced scanning configuration for the entire registry
const registryScanningConfig = new aws.ecr.RegistryScanningConfiguration("registry-scanning-config", {
    scanType: ecrConfig.enableEnhancedScanning ? "ENHANCED" : "BASIC",
    rules: [
        {
            scanFrequency: ecrConfig.continuousScanning ? "CONTINUOUS_SCAN" : "SCAN_ON_PUSH",
            repositoryFilters: [
                {
                    filter: "*",
                    filterType: "WILDCARD"
                }
            ]
        }
    ]
});

// =============================================================================
// Base Image Repositories (Immutable)
// =============================================================================

const baseImageRepositories: Record<string, aws.ecr.Repository> = {};
const baseImageLifecyclePolicies: Record<string, aws.ecr.LifecyclePolicy> = {};

ecrConfig.baseImageRepos.forEach(repoName => {
    // Base image repository with immutable tags
    baseImageRepositories[repoName] = new aws.ecr.Repository(`base-${repoName}-repo`, {
        name: createResourceName(deploymentConfig, "base", repoName),
        imageTagMutability: "IMMUTABLE",
        imageScanningConfiguration: {
            scanOnPush: ecrConfig.scanOnPush
        },
        encryptionConfigurations: [{
            encryptionType: "KMS",
            kmsKey: securityStackOutputs.applicationKeyArn
        }],
        tags: createResourceTags(deploymentConfig, "ecr-repository", {
            Name: createResourceName(deploymentConfig, "base", repoName),
            Type: "base-image",
            Repository: repoName,
            ImageTagMutability: "IMMUTABLE"
        })
    });

    // Conservative lifecycle policy for base images
    baseImageLifecyclePolicies[repoName] = new aws.ecr.LifecyclePolicy(`base-${repoName}-lifecycle`, {
        repository: baseImageRepositories[repoName].name,
        policy: JSON.stringify({
            rules: [
                {
                    rulePriority: 1,
                    description: "Keep last 50 base images with semantic version tags",
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["v", "stable", "lts"],
                        countType: "imageCountMoreThan",
                        countNumber: 50
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 2,
                    description: "Keep last 10 latest tagged images",
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["latest"],
                        countType: "imageCountMoreThan",
                        countNumber: 10
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 3,
                    description: "Delete untagged base images older than 3 days",
                    selection: {
                        tagStatus: "untagged",
                        countType: "sinceImagePushed",
                        countUnit: "days",
                        countNumber: 3
                    },
                    action: {
                        type: "expire"
                    }
                }
            ]
        })
    });

    // Repository policy for base images
    new aws.ecr.RepositoryPolicy(`base-${repoName}-policy`, {
        repository: baseImageRepositories[repoName].name,
        policy: JSON.stringify({
            Version: "2012-10-17",
            Statement: [
                {
                    Sid: "AllowServiceAccess",
                    Effect: "Allow",
                    Principal: {
                        AWS: [
                            securityStackOutputs.ecsExecutionRoleArn,
                            securityStackOutputs.ecsTaskRoleArn,
                            securityStackOutputs.eksNodeGroupRoleArn
                        ]
                    },
                    Action: [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer"
                    ]
                },
                {
                    Sid: "AllowCrossAccountAccess",
                    Effect: "Allow",
                    Principal: {
                        Service: [
                            "codebuild.amazonaws.com",
                            "ecs.amazonaws.com",
                            "eks.amazonaws.com"
                        ]
                    },
                    Action: [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetAuthorizationToken"
                    ]
                }
            ]
        })
    });
});

// =============================================================================
// Application Repositories (Mutable)
// =============================================================================

const applicationRepositories: Record<string, aws.ecr.Repository> = {};
const applicationLifecyclePolicies: Record<string, aws.ecr.LifecyclePolicy> = {};

ecrConfig.applicationRepos.forEach(repoName => {
    // Application repository with mutable tags for flexibility
    applicationRepositories[repoName] = new aws.ecr.Repository(`app-${repoName}-repo`, {
        name: createResourceName(deploymentConfig, "app", repoName),
        imageTagMutability: ecrConfig.appImageTagImmutability as "MUTABLE" | "IMMUTABLE",
        imageScanningConfiguration: {
            scanOnPush: ecrConfig.scanOnPush
        },
        encryptionConfigurations: [{
            encryptionType: "KMS",
            kmsKey: securityStackOutputs.applicationKeyArn
        }],
        tags: createResourceTags(deploymentConfig, "ecr-repository", {
            Name: createResourceName(deploymentConfig, "app", repoName),
            Type: "application-image",
            Repository: repoName,
            ImageTagMutability: ecrConfig.appImageTagImmutability
        })
    });

    // Environment-aware lifecycle policy for application images
    applicationLifecyclePolicies[repoName] = new aws.ecr.LifecyclePolicy(`app-${repoName}-lifecycle`, {
        repository: applicationRepositories[repoName].name,
        policy: JSON.stringify({
            rules: [
                {
                    rulePriority: 1,
                    description: `Keep last ${ecrConfig.maxProductionImages} production images`,
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["prod", "production", "release"],
                        countType: "imageCountMoreThan",
                        countNumber: ecrConfig.maxProductionImages
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 2,
                    description: `Keep last ${ecrConfig.maxStagingImages} staging images`,
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["staging", "stage", "pre-prod"],
                        countType: "imageCountMoreThan",
                        countNumber: ecrConfig.maxStagingImages
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 3,
                    description: `Keep last ${ecrConfig.maxDevelopmentImages} development images`,
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["dev", "develop", "feature"],
                        countType: "imageCountMoreThan",
                        countNumber: ecrConfig.maxDevelopmentImages
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 4,
                    description: "Keep last 3 latest tagged images",
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["latest"],
                        countType: "imageCountMoreThan",
                        countNumber: 3
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 5,
                    description: "Delete untagged images older than 1 day",
                    selection: {
                        tagStatus: "untagged",
                        countType: "sinceImagePushed",
                        countUnit: "days",
                        countNumber: 1
                    },
                    action: {
                        type: "expire"
                    }
                }
            ]
        })
    });

    // Repository policy for application images
    new aws.ecr.RepositoryPolicy(`app-${repoName}-policy`, {
        repository: applicationRepositories[repoName].name,
        policy: JSON.stringify({
            Version: "2012-10-17",
            Statement: [
                {
                    Sid: "AllowServiceAccess",
                    Effect: "Allow",
                    Principal: {
                        AWS: [
                            securityStackOutputs.ecsExecutionRoleArn,
                            securityStackOutputs.ecsTaskRoleArn,
                            securityStackOutputs.eksNodeGroupRoleArn
                        ]
                    },
                    Action: [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload"
                    ]
                },
                {
                    Sid: "AllowBuildServices",
                    Effect: "Allow",
                    Principal: {
                        Service: [
                            "codebuild.amazonaws.com",
                            "codepipeline.amazonaws.com"
                        ]
                    },
                    Action: [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                        "ecr:GetAuthorizationToken"
                    ]
                }
            ]
        })
    });
});

// =============================================================================
// Cross-Region Replication Configuration
// =============================================================================

let replicationConfiguration: aws.ecr.ReplicationConfiguration | undefined;

if (ecrConfig.enableCrossRegionReplication && replicationTargets.length > 0) {
    replicationConfiguration = new aws.ecr.ReplicationConfiguration("cross-region-replication", {
        replicationConfiguration: {
            rules: replicationTargets.map(targetRegion => ({
                destinations: [{
                    region: targetRegion,
                    registryId: currentAccountId
                }],
                repositoryFilters: [
                    // Replicate base images to all regions
                    {
                        filter: createResourceName(deploymentConfig, "base", "*"),
                        filterType: "PREFIX_MATCH"
                    },
                    // Replicate production application images only
                    {
                        filter: createResourceName(deploymentConfig, "app", "*"),
                        filterType: "PREFIX_MATCH"
                    }
                ]
            }))
        }
    });
}

// =============================================================================
// Vulnerability Scanning and Monitoring
// =============================================================================

// EventBridge rule for scan results
const scanResultsEventRule = new aws.cloudwatch.EventRule("ecr-scan-results", {
    name: createResourceName(deploymentConfig, "ecr-scan-results"),
    description: "Capture ECR vulnerability scan results",
    eventPattern: JSON.stringify({
        source: ["aws.ecr"],
        "detail-type": ["ECR Image Scan"],
        detail: {
            "scan-status": ["COMPLETE"],
            "repository-name": [
                ...ecrConfig.baseImageRepos.map(name => createResourceName(deploymentConfig, "base", name)),
                ...ecrConfig.applicationRepos.map(name => createResourceName(deploymentConfig, "app", name))
            ]
        }
    }),
    tags: createResourceTags(deploymentConfig, "event-rule", {
        Name: createResourceName(deploymentConfig, "ecr-scan-results"),
        Service: "ecr-monitoring"
    })
});

// SNS Topic for critical vulnerability notifications
const criticalVulnerabilityTopic = new aws.sns.Topic("ecr-critical-vulnerabilities", {
    name: createResourceName(deploymentConfig, "ecr-critical-vulns"),
    displayName: "ECR Critical Vulnerabilities",
    kmsMasterKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "sns-topic", {
        Name: createResourceName(deploymentConfig, "ecr-critical-vulns"),
        Service: "vulnerability-monitoring"
    })
});

// Lambda function for processing scan results
const scanResultsProcessor = new aws.lambda.Function("scan-results-processor", {
    name: createResourceName(deploymentConfig, "scan-results-processor"),
    runtime: "python3.11",
    handler: "index.lambda_handler",
    role: securityStackOutputs.ecsExecutionRoleArn, // Reuse execution role for simplicity
    code: new pulumi.asset.AssetArchive({
        "index.py": new pulumi.asset.StringAsset(`
import json
import boto3
import os

def lambda_handler(event, context):
    """Process ECR scan results and send notifications for critical vulnerabilities."""

    sns = boto3.client('sns')
    topic_arn = os.environ['SNS_TOPIC_ARN']
    critical_threshold = int(os.environ.get('CRITICAL_THRESHOLD', '0'))
    high_threshold = int(os.environ.get('HIGH_THRESHOLD', '5'))

    try:
        detail = event['detail']
        repository_name = detail['repository-name']
        scan_status = detail['scan-status']

        if scan_status == 'COMPLETE' and 'finding-counts' in detail:
            findings = detail['finding-counts']
            critical_count = findings.get('CRITICAL', 0)
            high_count = findings.get('HIGH', 0)

            if critical_count > critical_threshold or high_count > high_threshold:
                message = {
                    'repository': repository_name,
                    'critical_vulnerabilities': critical_count,
                    'high_vulnerabilities': high_count,
                    'scan_timestamp': detail.get('scan-timestamp'),
                    'environment': os.environ.get('ENVIRONMENT', 'unknown')
                }

                sns.publish(
                    TopicArn=topic_arn,
                    Subject=f'Critical Vulnerabilities Found in {repository_name}',
                    Message=json.dumps(message, indent=2)
                )

        return {
            'statusCode': 200,
            'body': json.dumps('Scan results processed successfully')
        }

    except Exception as e:
        print(f'Error processing scan results: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
`)
    }),
    environment: {
        variables: {
            SNS_TOPIC_ARN: criticalVulnerabilityTopic.arn,
            CRITICAL_THRESHOLD: ecrConfig.criticalVulnerabilityThreshold.toString(),
            HIGH_THRESHOLD: ecrConfig.highVulnerabilityThreshold.toString(),
            ENVIRONMENT: deploymentConfig.environment
        }
    },
    timeout: 60,
    tags: createResourceTags(deploymentConfig, "lambda-function", {
        Name: createResourceName(deploymentConfig, "scan-results-processor"),
        Service: "vulnerability-processing"
    })
});

// EventBridge target to trigger Lambda
const scanResultsTarget = new aws.cloudwatch.EventTarget("scan-results-target", {
    rule: scanResultsEventRule.name,
    targetId: "ScanResultsProcessorTarget",
    arn: scanResultsProcessor.arn
});

// Permission for EventBridge to invoke Lambda
const lambdaEventBridgePermission = new aws.lambda.Permission("lambda-eventbridge-permission", {
    statementId: "AllowExecutionFromEventBridge",
    action: "lambda:InvokeFunction",
    functionName: scanResultsProcessor.name,
    principal: "events.amazonaws.com",
    sourceArn: scanResultsEventRule.arn
});

// =============================================================================
// IAM Policies for Enhanced ECR Operations
// =============================================================================

// Enhanced ECR policy for cross-region replication and advanced features
const ecrEnhancedPolicy = new aws.iam.Policy("ecr-enhanced-policy", {
    name: createResourceName(deploymentConfig, "ecr-enhanced-policy"),
    description: "Enhanced ECR policy for cross-region replication and scanning",
    policy: pulumi.all([
        currentAccountId,
        currentRegion
    ]).apply(([accountId, region]) => JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Sid: "ECRFullAccess",
                Effect: "Allow",
                Action: [
                    "ecr:*"
                ],
                Resource: "*"
            },
            {
                Sid: "CrossRegionReplication",
                Effect: "Allow",
                Action: [
                    "ecr:CreateRepository",
                    "ecr:ReplicateImage",
                    "ecr:BatchImportLayerPart",
                    "ecr:CompleteLayerUpload"
                ],
                Resource: replicationTargets.map(targetRegion =>
                    `arn:aws:ecr:${targetRegion}:${accountId}:repository/*`
                )
            },
            {
                Sid: "EnhancedScanning",
                Effect: "Allow",
                Action: [
                    "inspector2:*",
                    "ecr:PutRegistryScanningConfiguration",
                    "ecr:GetRegistryScanningConfiguration",
                    "ecr:DescribeImageScanFindings"
                ],
                Resource: "*"
            }
        ]
    })),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Name: createResourceName(deploymentConfig, "ecr-enhanced-policy"),
        Service: "ecr"
    })
});

// =============================================================================
// Outputs
// =============================================================================

// Registry information
export const registryId = currentAccountId;
export const registryUri = pulumi.interpolate`${currentAccountId}.dkr.ecr.${deploymentConfig.region}.amazonaws.com`;

// Base image repositories
export const baseImagesRepoUrl = baseImageRepositories.node?.repositoryUrl || "";
export const baseAlpineRepoUrl = baseImageRepositories.alpine?.repositoryUrl || "";
export const baseNginxRepoUrl = baseImageRepositories.nginx?.repositoryUrl || "";
export const basePostgresRepoUrl = baseImageRepositories.postgres?.repositoryUrl || "";
export const baseRedisRepoUrl = baseImageRepositories.redis?.repositoryUrl || "";
export const basePythonRepoUrl = baseImageRepositories.python?.repositoryUrl || "";

// Application repositories
export const frontendRepoUrl = applicationRepositories.frontend?.repositoryUrl || "";
export const backendRepoUrl = applicationRepositories.backend?.repositoryUrl || "";
export const apiRepoUrl = applicationRepositories.api?.repositoryUrl || "";
export const workerRepoUrl = applicationRepositories.worker?.repositoryUrl || "";
export const schedulerRepoUrl = applicationRepositories.scheduler?.repositoryUrl || "";

// Replication status
export const replicationEnabled = ecrConfig.enableCrossRegionReplication && replicationTargets.length > 0;
export const replicationRegions = replicationTargets;

// Scanning configuration
export const registryScanningEnabled = ecrConfig.enableRegistryScanning;
export const enhancedScanningEnabled = ecrConfig.enableEnhancedScanning;
export const scanOnPushEnabled = ecrConfig.scanOnPush;

// Monitoring resources
export const scanNotificationTopicArn = criticalVulnerabilityTopic.arn;
export const scanResultsRuleArn = scanResultsEventRule.arn;
export const scanProcessorFunctionArn = scanResultsProcessor.arn;

// Policies and permissions
export const ecrEnhancedPolicyArn = ecrEnhancedPolicy.arn;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Comprehensive summary for easier consumption
export const summary = {
    registry: {
        id: registryId,
        uri: registryUri,
        scanningEnabled: registryScanningEnabled,
        enhancedScanning: enhancedScanningEnabled,
        replicationEnabled: replicationEnabled,
        replicationRegions: replicationRegions
    },
    baseImages: {
        alpine: baseImageRepositories.alpine?.repositoryUrl || "",
        node: baseImageRepositories.node?.repositoryUrl || "",
        nginx: baseImageRepositories.nginx?.repositoryUrl || "",
        postgres: baseImageRepositories.postgres?.repositoryUrl || "",
        redis: baseImageRepositories.redis?.repositoryUrl || "",
        python: baseImageRepositories.python?.repositoryUrl || ""
    },
    applications: {
        frontend: applicationRepositories.frontend?.repositoryUrl || "",
        backend: applicationRepositories.backend?.repositoryUrl || "",
        api: applicationRepositories.api?.repositoryUrl || "",
        worker: applicationRepositories.worker?.repositoryUrl || "",
        scheduler: applicationRepositories.scheduler?.repositoryUrl || ""
    },
    monitoring: {
        scanNotificationTopic: scanNotificationTopicArn,
        scanResultsRule: scanResultsEventRule.arn,
        scanProcessor: scanResultsProcessor.arn
    },
    policies: {
        enhancedEcrPolicy: ecrEnhancedPolicyArn
    },
    configuration: {
        baseImageTagImmutability: "IMMUTABLE",
        appImageTagImmutability: ecrConfig.appImageTagImmutability,
        maxProductionImages: ecrConfig.maxProductionImages,
        maxStagingImages: ecrConfig.maxStagingImages,
        maxDevelopmentImages: ecrConfig.maxDevelopmentImages,
        vulnerabilityThresholds: {
            critical: ecrConfig.criticalVulnerabilityThreshold,
            high: ecrConfig.highVulnerabilityThreshold
        }
    }
};

console.log(`✅ ECR Services Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`📊 Created ${ecrConfig.baseImageRepos.length} base image repositories with immutable tags`);
console.log(`🚀 Created ${ecrConfig.applicationRepos.length} application repositories with ${ecrConfig.appImageTagImmutability} tags`);
console.log(`🔒 Registry scanning: ${registryScanningEnabled ? 'Enabled' : 'Disabled'} (${ecrConfig.enableEnhancedScanning ? 'Enhanced' : 'Basic'})`);
console.log(`🌍 Cross-region replication: ${replicationEnabled ? `Enabled to ${replicationTargets.length} regions` : 'Disabled'}`);