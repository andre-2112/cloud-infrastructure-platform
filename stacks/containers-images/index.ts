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

const STACK_NAME = "containers-images";

// Container Images Stack - Creates ECR repositories, CodeBuild projects, and CI/CD pipelines
console.log(`🚀 Deploying Container Images Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters
const containerConfig = {
    repositoryNames: ["frontend", "backend", "worker", "nginx"],
    githubRepo: config.get("githubRepo") || "myorg/myapp",
    githubBranch: config.get("githubBranch") || "main",
    buildTimeout: config.getNumber("buildTimeout") || 60,
    enableVulnerabilityScanning: config.getBoolean("enableVulnerabilityScanning") || true,
    maxImageCount: config.getNumber("maxImageCount") || 10,
    imageTagImmutability: config.get("imageTagImmutability") || "MUTABLE"
};

// Get current AWS account ID and region for resource ARNs
const currentAccountId = getCurrentAccountId();
const currentRegion = getCurrentRegion();

// =============================================================================
// ECR Repositories
// =============================================================================

// Create ECR repositories for each application container
const ecrRepositories: Record<string, aws.ecr.Repository> = {};
const lifecyclePolicies: Record<string, aws.ecr.LifecyclePolicy> = {};

containerConfig.repositoryNames.forEach(repoName => {
    // ECR Repository
    ecrRepositories[repoName] = new aws.ecr.Repository(`${repoName}-ecr-repo`, {
        name: createResourceName(deploymentConfig, repoName, "ecr"),
        imageTagMutability: containerConfig.imageTagImmutability as "MUTABLE" | "IMMUTABLE",
        imageScanningConfiguration: {
            scanOnPush: containerConfig.enableVulnerabilityScanning
        },
        encryptionConfigurations: [{
            encryptionType: "KMS",
            kmsKey: securityStackOutputs.applicationKeyArn
        }],
        tags: createResourceTags(deploymentConfig, "ecr-repository", {
            Name: createResourceName(deploymentConfig, repoName, "ecr"),
            Application: repoName,
            Service: "container-registry"
        })
    });

    // Lifecycle Policy for cost optimization
    lifecyclePolicies[repoName] = new aws.ecr.LifecyclePolicy(`${repoName}-lifecycle-policy`, {
        repository: ecrRepositories[repoName].name,
        policy: JSON.stringify({
            rules: [
                {
                    rulePriority: 1,
                    description: `Keep last ${containerConfig.maxImageCount} production images`,
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["prod"],
                        countType: "imageCountMoreThan",
                        countNumber: containerConfig.maxImageCount
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 2,
                    description: "Keep last 5 staging images",
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["staging"],
                        countType: "imageCountMoreThan",
                        countNumber: 5
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 3,
                    description: "Keep last 3 development images",
                    selection: {
                        tagStatus: "tagged",
                        tagPrefixList: ["dev"],
                        countType: "imageCountMoreThan",
                        countNumber: 3
                    },
                    action: {
                        type: "expire"
                    }
                },
                {
                    rulePriority: 4,
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

    // Repository Policy for cross-account access if needed
    new aws.ecr.RepositoryPolicy(`${repoName}-repo-policy`, {
        repository: ecrRepositories[repoName].name,
        policy: JSON.stringify({
            Version: "2012-10-17",
            Statement: [
                {
                    Sid: "AllowECSAndEKSAccess",
                    Effect: "Allow",
                    Principal: {
                        AWS: [
                            securityStackOutputs.ecsExecutionRoleArn,
                            securityStackOutputs.ecsTaskRoleArn,
                            securityStackOutputs.eksClusterRoleArn,
                            securityStackOutputs.eksNodeGroupRoleArn
                        ]
                    },
                    Action: [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer"
                    ]
                }
            ]
        })
    });
});

// =============================================================================
// IAM Roles for CodeBuild
// =============================================================================

// CodeBuild Service Role
const codebuildRole = new aws.iam.Role("codebuild-service-role", {
    name: createResourceName(deploymentConfig, "codebuild-service-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "codebuild.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "codebuild-service-role"),
        Service: "CodeBuild"
    })
});

// CodeBuild Policy for ECR and CloudWatch access
const codebuildPolicy = new aws.iam.Policy("codebuild-policy", {
    name: createResourceName(deploymentConfig, "codebuild-policy"),
    description: "Policy for CodeBuild to access ECR and CloudWatch",
    policy: pulumi.all([
        securityStackOutputs.applicationKeyArn,
        currentAccountId,
        currentRegion
    ]).apply(([keyArn, accountId, region]) => JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                Resource: [
                    `arn:aws:logs:${region}:${accountId}:log-group:/aws/codebuild/*`
                ]
            },
            {
                Effect: "Allow",
                Action: [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:GetAuthorizationToken",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload"
                ],
                Resource: "*"
            },
            {
                Effect: "Allow",
                Action: [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                Resource: keyArn
            },
            {
                Effect: "Allow",
                Action: [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject"
                ],
                Resource: "*"
            }
        ]
    })),
    tags: createResourceTags(deploymentConfig, "iam-policy", {
        Name: createResourceName(deploymentConfig, "codebuild-policy")
    })
});

// Attach policy to role
const codebuildPolicyAttachment = new aws.iam.RolePolicyAttachment("codebuild-policy-attachment", {
    role: codebuildRole.name,
    policyArn: codebuildPolicy.arn
});

// =============================================================================
// CodeBuild Projects
// =============================================================================

// Create CodeBuild projects for each repository
const codebuildProjects: Record<string, aws.codebuild.Project> = {};

containerConfig.repositoryNames.forEach(repoName => {
    codebuildProjects[repoName] = new aws.codebuild.Project(`${repoName}-codebuild`, {
        name: createResourceName(deploymentConfig, repoName, "codebuild"),
        description: `Build and push ${repoName} container image to ECR`,
        serviceRole: codebuildRole.arn,

        artifacts: {
            type: "CODEPIPELINE"
        },

        environment: {
            type: "LINUX_CONTAINER",
            computeType: "BUILD_GENERAL1_MEDIUM",
            image: "aws/codebuild/standard:7.0",
            privilegedMode: true,
            environmentVariables: [
                {
                    name: "AWS_DEFAULT_REGION",
                    value: deploymentConfig.region
                },
                {
                    name: "AWS_ACCOUNT_ID",
                    value: currentAccountId
                },
                {
                    name: "IMAGE_REPO_NAME",
                    value: ecrRepositories[repoName].repositoryUrl
                },
                {
                    name: "IMAGE_TAG",
                    value: "latest"
                },
                {
                    name: "ENVIRONMENT",
                    value: deploymentConfig.environment
                },
                {
                    name: "DEPLOYMENT_ID",
                    value: deploymentConfig.deploymentId
                }
            ]
        },

        source: {
            type: "CODEPIPELINE",
            buildspec: `version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG_COMMIT=$ENVIRONMENT-$COMMIT_HASH
      - IMAGE_TAG_ENV=$ENVIRONMENT-latest
      - echo Build started on \`date\`
      - echo Building the Docker image...
  build:
    commands:
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG ./${repoName}/
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG_COMMIT
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:$IMAGE_TAG_ENV
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $REPOSITORY_URI:latest
  post_build:
    commands:
      - echo Build completed on \`date\`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:$IMAGE_TAG_COMMIT
      - docker push $REPOSITORY_URI:$IMAGE_TAG_ENV
      - docker push $REPOSITORY_URI:latest
      - echo Writing image definitions file...
      - printf '[{"name":"${repoName}","imageUri":"%s"}]' $REPOSITORY_URI:$IMAGE_TAG_COMMIT > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - '**/*'`
        },

        timeoutInMinutes: containerConfig.buildTimeout,

        cache: {
            type: "LOCAL",
            modes: ["LOCAL_DOCKER_LAYER_CACHE", "LOCAL_SOURCE_CACHE"]
        },

        logsConfig: {
            cloudwatchLogs: {
                status: "ENABLED",
                groupName: `/aws/codebuild/${createResourceName(deploymentConfig, repoName, "codebuild")}`,
                streamName: "build-logs"
            }
        },

        tags: createResourceTags(deploymentConfig, "codebuild-project", {
            Name: createResourceName(deploymentConfig, repoName, "codebuild"),
            Application: repoName,
            Service: "ci-cd"
        })
    });
});

// =============================================================================
// CloudWatch Log Groups for CodeBuild
// =============================================================================

const codebuildLogGroups: Record<string, aws.cloudwatch.LogGroup> = {};

containerConfig.repositoryNames.forEach(repoName => {
    codebuildLogGroups[repoName] = new aws.cloudwatch.LogGroup(`${repoName}-codebuild-logs`, {
        name: `/aws/codebuild/${createResourceName(deploymentConfig, repoName, "codebuild")}`,
        retentionInDays: deploymentConfig.environment === "prod" ? 90 : 30,
        kmsKeyId: securityStackOutputs.applicationKeyArn,
        tags: createResourceTags(deploymentConfig, "log-group", {
            Name: `/aws/codebuild/${createResourceName(deploymentConfig, repoName, "codebuild")}`,
            Application: repoName,
            Service: "logging"
        })
    });
});

// =============================================================================
// GitHub Webhook and Integration (Optional)
// =============================================================================

// GitHub webhook for automated builds (if GitHub repository is provided)
let githubWebhook: aws.codebuild.Webhook | undefined;

if (containerConfig.githubRepo && containerConfig.githubRepo !== "myorg/myapp") {
    // Create webhook for the main project (typically frontend)
    githubWebhook = new aws.codebuild.Webhook("github-webhook", {
        projectName: codebuildProjects.frontend.name,
        branchFilter: `^(${containerConfig.githubBranch})$`,
        filterGroups: [
            {
                filters: [
                    {
                        type: "EVENT",
                        pattern: "PUSH"
                    },
                    {
                        type: "HEAD_REF",
                        pattern: `^refs/heads/${containerConfig.githubBranch}$`
                    }
                ]
            },
            {
                filters: [
                    {
                        type: "EVENT",
                        pattern: "PULL_REQUEST_CREATED,PULL_REQUEST_UPDATED,PULL_REQUEST_REOPENED"
                    },
                    {
                        type: "BASE_REF",
                        pattern: `^refs/heads/${containerConfig.githubBranch}$`
                    }
                ]
            }
        ]
    });
}

// =============================================================================
// Container Image Scanning Configuration
// =============================================================================

// Enhanced vulnerability scanning with EventBridge rules
const imageScanResultsRule = new aws.cloudwatch.EventRule("image-scan-results", {
    name: createResourceName(deploymentConfig, "image-scan-results"),
    description: "Capture ECR image scan results",
    eventPattern: JSON.stringify({
        source: ["aws.ecr"],
        "detail-type": ["ECR Image Scan"],
        detail: {
            "scan-status": ["COMPLETE"],
            "repository-name": containerConfig.repositoryNames.map(name =>
                createResourceName(deploymentConfig, name, "ecr")
            )
        }
    }),
    tags: createResourceTags(deploymentConfig, "event-rule", {
        Name: createResourceName(deploymentConfig, "image-scan-results")
    })
});

// SNS Topic for scan notifications (if enabled)
const scanNotificationTopic = new aws.sns.Topic("image-scan-notifications", {
    name: createResourceName(deploymentConfig, "image-scan-notifications"),
    displayName: "Container Image Scan Notifications",
    kmsMasterKeyId: securityStackOutputs.applicationKeyArn,
    tags: createResourceTags(deploymentConfig, "sns-topic", {
        Name: createResourceName(deploymentConfig, "image-scan-notifications")
    })
});

// =============================================================================
// Exports
// =============================================================================

// ECR Repository URLs
export const frontendRepoUrl = ecrRepositories.frontend?.repositoryUrl || "";
export const backendRepoUrl = ecrRepositories.backend?.repositoryUrl || "";
export const workerRepoUrl = ecrRepositories.worker?.repositoryUrl || "";
export const nginxRepoUrl = ecrRepositories.nginx?.repositoryUrl || "";

// Repository ARNs
export const frontendRepoArn = ecrRepositories.frontend?.arn || "";
export const backendRepoArn = ecrRepositories.backend?.arn || "";
export const workerRepoArn = ecrRepositories.worker?.arn || "";
export const nginxRepoArn = ecrRepositories.nginx?.arn || "";

// CodeBuild Role and Projects
export const codebuildRoleArn = codebuildRole.arn;
export const codebuildRoleName = codebuildRole.name;

export const codebuildProjects_frontend = codebuildProjects.frontend?.arn || "";
export const codebuildProjects_backend = codebuildProjects.backend?.arn || "";
export const codebuildProjects_worker = codebuildProjects.worker?.arn || "";
export const codebuildProjects_nginx = codebuildProjects.nginx?.arn || "";

// SNS and Monitoring
export const scanNotificationTopicArn = scanNotificationTopic.arn;
export const imageScanResultsRuleArn = imageScanResultsRule.arn;

// GitHub Integration
export const githubWebhookUrl = githubWebhook?.payloadUrl || "";
export const githubWebhookSecret = githubWebhook?.secret || "";

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information for easier consumption
export const summary = {
    repositories: {
        frontend: {
            url: frontendRepoUrl,
            arn: frontendRepoArn
        },
        backend: {
            url: backendRepoUrl,
            arn: backendRepoArn
        },
        worker: {
            url: workerRepoUrl,
            arn: workerRepoArn
        },
        nginx: {
            url: nginxRepoUrl,
            arn: nginxRepoArn
        }
    },
    codebuild: {
        roleArn: codebuildRoleArn,
        projects: {
            frontend: codebuildProjects_frontend,
            backend: codebuildProjects_backend,
            worker: codebuildProjects_worker,
            nginx: codebuildProjects_nginx
        }
    },
    monitoring: {
        scanNotificationTopic: scanNotificationTopicArn,
        scanResultsRule: imageScanResultsRuleArn
    },
    configuration: {
        vulnerabilityScanning: containerConfig.enableVulnerabilityScanning,
        maxImageCount: containerConfig.maxImageCount,
        githubIntegration: !!githubWebhook
    }
};

console.log(`✅ Container Images Stack deployment completed for ${deploymentConfig.environment}`);