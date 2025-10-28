import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    isDevelopment,
    ENVIRONMENT_DEFAULTS
} from "../../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Get network stack outputs
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

const STACK_NAME = "storage";

// Environment-specific configuration
const envConfig = ENVIRONMENT_DEFAULTS[deploymentConfig.environment];
const isDevEnvironment = isDevelopment(deploymentConfig);

// Storage Stack - Creates S3 buckets, EFS file systems, VPC endpoints, and backup services
console.log(`🚀 Deploying Storage Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// S3 Buckets
// =============================================================================

// Primary Storage Bucket
const primaryStorageBucket = new aws.s3.Bucket("primary-storage-bucket", {
    bucket: createResourceName(deploymentConfig, "primary-storage"),
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "primary-storage"),
        Purpose: "Primary Data Storage"
    })
});

const primaryStorageVersioning = new aws.s3.BucketVersioning("primary-storage-versioning", {
    bucket: primaryStorageBucket.id,
    versioningConfiguration: {
        status: "Enabled"
    }
});

const primaryStorageEncryption = new aws.s3.BucketServerSideEncryptionConfiguration("primary-storage-encryption", {
    bucket: primaryStorageBucket.id,
    rules: [{
        applyServerSideEncryptionByDefault: {
            sseAlgorithm: "aws:kms",
            kmsMasterKeyId: securityStackOutputs.applicationKeyArn
        },
        bucketKeyEnabled: true
    }]
});

const primaryStoragePublicAccessBlock = new aws.s3.BucketPublicAccessBlock("primary-storage-public-access-block", {
    bucket: primaryStorageBucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true
});

const primaryStorageLifecycle = new aws.s3.BucketLifecycleConfiguration("primary-storage-lifecycle", {
    bucket: primaryStorageBucket.id,
    rules: [
        {
            id: "transition_to_ia",
            status: "Enabled",
            transitions: [
                {
                    days: isDevEnvironment ? 7 : 30,
                    storageClass: "STANDARD_IA"
                }
            ]
        },
        {
            id: "transition_to_glacier",
            status: "Enabled",
            transitions: [
                {
                    days: isDevEnvironment ? 30 : 90,
                    storageClass: "GLACIER"
                }
            ]
        }
    ]
});

// Static Assets Bucket
const staticAssetsBucket = new aws.s3.Bucket("static-assets-bucket", {
    bucket: createResourceName(deploymentConfig, "static-assets"),
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "static-assets"),
        Purpose: "Static Web Assets"
    })
});

const staticAssetsEncryption = new aws.s3.BucketServerSideEncryptionConfiguration("static-assets-encryption", {
    bucket: staticAssetsBucket.id,
    rules: [{
        applyServerSideEncryptionByDefault: {
            sseAlgorithm: "aws:kms",
            kmsMasterKeyId: securityStackOutputs.applicationKeyArn
        },
        bucketKeyEnabled: true
    }]
});

const staticAssetsPublicAccessBlock = new aws.s3.BucketPublicAccessBlock("static-assets-public-access-block", {
    bucket: staticAssetsBucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true
});

const staticAssetsCors = new aws.s3.BucketCorsConfiguration("static-assets-cors", {
    bucket: staticAssetsBucket.id,
    corsRules: [{
        allowedOrigins: [`https://${deploymentConfig.deployDomain}`, `https://www.${deploymentConfig.deployDomain}`],
        allowedMethods: ["GET", "HEAD"],
        allowedHeaders: ["*"],
        maxAgeSeconds: 3600,
        exposeHeaders: ["ETag"]
    }]
});

// Logs Storage Bucket
const logsBucket = new aws.s3.Bucket("logs-bucket", {
    bucket: createResourceName(deploymentConfig, "logs"),
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "logs"),
        Purpose: "Centralized Logs Storage"
    })
});

const logsVersioning = new aws.s3.BucketVersioning("logs-versioning", {
    bucket: logsBucket.id,
    versioningConfiguration: {
        status: "Enabled"
    }
});

const logsEncryption = new aws.s3.BucketServerSideEncryptionConfiguration("logs-encryption", {
    bucket: logsBucket.id,
    rules: [{
        applyServerSideEncryptionByDefault: {
            sseAlgorithm: "aws:kms",
            kmsMasterKeyId: securityStackOutputs.applicationKeyArn
        },
        bucketKeyEnabled: true
    }]
});

const logsPublicAccessBlock = new aws.s3.BucketPublicAccessBlock("logs-public-access-block", {
    bucket: logsBucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true
});

const logsLifecycle = new aws.s3.BucketLifecycleConfiguration("logs-lifecycle", {
    bucket: logsBucket.id,
    rules: [
        {
            id: "expire_logs",
            status: "Enabled",
            expiration: {
                days: isDevEnvironment ? 30 : 90
            }
        },
        {
            id: "transition_old_logs",
            status: "Enabled",
            transitions: [
                {
                    days: isDevEnvironment ? 7 : 30,
                    storageClass: "STANDARD_IA"
                }
            ]
        }
    ]
});

// Backup Storage Bucket
const backupBucket = new aws.s3.Bucket("backup-bucket", {
    bucket: createResourceName(deploymentConfig, "backups"),
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "backups"),
        Purpose: "Database and System Backups"
    })
});

const backupVersioning = new aws.s3.BucketVersioning("backup-versioning", {
    bucket: backupBucket.id,
    versioningConfiguration: {
        status: "Enabled"
    }
});

const backupEncryption = new aws.s3.BucketServerSideEncryptionConfiguration("backup-encryption", {
    bucket: backupBucket.id,
    rules: [{
        applyServerSideEncryptionByDefault: {
            sseAlgorithm: "aws:kms",
            kmsMasterKeyId: securityStackOutputs.databaseKeyArn
        },
        bucketKeyEnabled: true
    }]
});

const backupPublicAccessBlock = new aws.s3.BucketPublicAccessBlock("backup-public-access-block", {
    bucket: backupBucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true
});

const backupLifecycle = new aws.s3.BucketLifecycleConfiguration("backup-lifecycle", {
    bucket: backupBucket.id,
    rules: [
        {
            id: "archive_backups",
            status: "Enabled",
            transitions: [
                {
                    days: isDevEnvironment ? 3 : 7,
                    storageClass: "GLACIER"
                },
                {
                    days: isDevEnvironment ? 30 : 90,
                    storageClass: "DEEP_ARCHIVE"
                }
            ]
        }
    ]
});

// Artifacts Storage Bucket
const artifactsBucket = new aws.s3.Bucket("artifacts-bucket", {
    bucket: createResourceName(deploymentConfig, "artifacts"),
    tags: createResourceTags(deploymentConfig, "s3-bucket", {
        Name: createResourceName(deploymentConfig, "artifacts"),
        Purpose: "CI/CD Artifacts and Deployments"
    })
});

const artifactsVersioning = new aws.s3.BucketVersioning("artifacts-versioning", {
    bucket: artifactsBucket.id,
    versioningConfiguration: {
        status: "Enabled"
    }
});

const artifactsEncryption = new aws.s3.BucketServerSideEncryptionConfiguration("artifacts-encryption", {
    bucket: artifactsBucket.id,
    rules: [{
        applyServerSideEncryptionByDefault: {
            sseAlgorithm: "aws:kms",
            kmsMasterKeyId: securityStackOutputs.applicationKeyArn
        },
        bucketKeyEnabled: true
    }]
});

const artifactsPublicAccessBlock = new aws.s3.BucketPublicAccessBlock("artifacts-public-access-block", {
    bucket: artifactsBucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true
});

const artifactsLifecycle = new aws.s3.BucketLifecycleConfiguration("artifacts-lifecycle", {
    bucket: artifactsBucket.id,
    rules: [
        {
            id: "expire_old_artifacts",
            status: "Enabled",
            expiration: {
                days: isDevEnvironment ? 30 : 180
            }
        }
    ]
});

// =============================================================================
// EFS File System
// =============================================================================

// EFS Security Group
const efsSg = new aws.ec2.SecurityGroup("efs-sg", {
    name: createResourceName(deploymentConfig, "efs-sg"),
    description: "Security group for EFS mount targets",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "NFS from private subnets",
            fromPort: 2049,
            toPort: 2049,
            protocol: "tcp",
            cidrBlocks: [networkStackOutputs.vpcCidrBlock]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: ["0.0.0.0/0"]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "efs-sg"),
        Purpose: "EFS Access"
    })
});

// Shared EFS File System
const sharedEfs = new aws.efs.FileSystem("shared-efs", {
    creationToken: createResourceName(deploymentConfig, "shared-efs"),
    performanceMode: "generalPurpose",
    throughputMode: isDevEnvironment ? "bursting" : "provisioned",
    provisionedThroughputInMibps: isDevEnvironment ? undefined : 100,
    encrypted: true,
    kmsKeyId: securityStackOutputs.applicationKeyArn,
    lifecyclePolicy: {
        transitionToIa: isDevEnvironment ? "AFTER_7_DAYS" : "AFTER_30_DAYS",
        transitionToPrimaryStorageClass: "AFTER_1_ACCESS"
    },
    tags: createResourceTags(deploymentConfig, "efs-filesystem", {
        Name: createResourceName(deploymentConfig, "shared-efs"),
        Purpose: "Shared Application Storage"
    })
});

// EFS Mount Targets (one per AZ)
const mountTargets = networkStackOutputs.privateSubnetIds.apply(subnetIds =>
    subnetIds.map((subnetId, index) => {
        return new aws.efs.MountTarget(`efs-mount-target-${index}`, {
            fileSystemId: sharedEfs.id,
            subnetId: subnetId,
            securityGroups: [efsSg.id]
        });
    })
);

// EFS Access Points
const appAccessPoint = new aws.efs.AccessPoint("app-access-point", {
    fileSystemId: sharedEfs.id,
    posixUser: {
        uid: 1001,
        gid: 1001
    },
    rootDirectory: {
        path: "/app-data",
        creationInfo: {
            ownerUid: 1001,
            ownerGid: 1001,
            permissions: "755"
        }
    },
    tags: createResourceTags(deploymentConfig, "efs-access-point", {
        Name: createResourceName(deploymentConfig, "app-access-point"),
        Purpose: "Application Data Access"
    })
});

// EFS Backup Policy
const efsBackupPolicy = new aws.efs.BackupPolicy("efs-backup-policy", {
    fileSystemId: sharedEfs.id,
    backupPolicy: {
        status: "ENABLED"
    }
});

// =============================================================================
// VPC Endpoints
// =============================================================================

// Get current region and account ID for VPC endpoint policy
const currentRegion = aws.getRegion();
const currentIdentity = aws.getCallerIdentity();

// S3 VPC Endpoint
const s3VpcEndpoint = new aws.ec2.VpcEndpoint("s3-vpc-endpoint", {
    vpcId: networkStackOutputs.vpcId,
    serviceName: pulumi.interpolate`com.amazonaws.${currentRegion.then(r => r.name)}.s3`,
    routeTableIds: networkStackOutputs.privateSubnetIds.apply(async (subnetIds) => {
        // Get route table IDs for private subnets
        const routeTables = await Promise.all(
            subnetIds.map(async (subnetId) => {
                const subnet = await aws.ec2.getSubnet({ id: subnetId });
                return subnet.routeTableId;
            })
        );
        return routeTables;
    }),
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: "*",
                Action: [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                Resource: [
                    primaryStorageBucket.arn,
                    pulumi.interpolate`${primaryStorageBucket.arn}/*`,
                    staticAssetsBucket.arn,
                    pulumi.interpolate`${staticAssetsBucket.arn}/*`,
                    logsBucket.arn,
                    pulumi.interpolate`${logsBucket.arn}/*`,
                    backupBucket.arn,
                    pulumi.interpolate`${backupBucket.arn}/*`,
                    artifactsBucket.arn,
                    pulumi.interpolate`${artifactsBucket.arn}/*`
                ]
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "vpc-endpoint", {
        Name: createResourceName(deploymentConfig, "s3-vpc-endpoint"),
        Service: "S3"
    })
});

// =============================================================================
// AWS Backup
// =============================================================================

// Backup Vault
const backupVault = new aws.backup.Vault("backup-vault", {
    name: createResourceName(deploymentConfig, "backup-vault"),
    kmsKeyArn: securityStackOutputs.databaseKeyArn,
    tags: createResourceTags(deploymentConfig, "backup-vault", {
        Name: createResourceName(deploymentConfig, "backup-vault"),
        Purpose: "Centralized Backup Storage"
    })
});

// Backup Plan
const backupPlan = new aws.backup.Plan("backup-plan", {
    name: createResourceName(deploymentConfig, "backup-plan"),
    rules: [
        {
            ruleName: "daily_backups",
            targetVaultName: backupVault.name,
            schedule: "cron(0 5 ? * * *)", // 5 AM UTC daily
            lifecycle: {
                deleteAfterDays: envConfig.backup.retentionDays,
                moveToColdStorageAfterDays: Math.min(7, Math.floor(envConfig.backup.retentionDays / 4))
            },
            recoveryPointTags: createResourceTags(deploymentConfig, "backup-recovery-point", {
                BackupType: "Daily",
                RetentionDays: envConfig.backup.retentionDays.toString()
            })
        }
    ],
    tags: createResourceTags(deploymentConfig, "backup-plan", {
        Name: createResourceName(deploymentConfig, "backup-plan"),
        Schedule: "Daily"
    })
});

// Backup Service Role
const backupServiceRole = new aws.iam.Role("backup-service-role", {
    name: createResourceName(deploymentConfig, "backup-service-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Principal: {
                    Service: "backup.amazonaws.com"
                },
                Action: "sts:AssumeRole"
            }
        ]
    }),
    managedPolicyArns: [
        "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup",
        "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
    ],
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "backup-service-role"),
        Service: "AWS Backup"
    })
});

// Backup Selection for EBS Volumes
const backupSelection = new aws.backup.Selection("backup-selection", {
    iamRoleArn: backupServiceRole.arn,
    name: createResourceName(deploymentConfig, "ebs-backup-selection"),
    planId: backupPlan.id,
    resources: ["*"],
    conditions: [
        {
            stringEquals: [
                {
                    key: "aws:ResourceTag/Backup",
                    value: "Required"
                }
            ]
        }
    ]
});

// =============================================================================
// Bucket Notifications (for potential processing workflows)
// =============================================================================

// S3 Bucket Notifications for primary storage (example setup)
const bucketNotification = new aws.s3.BucketNotification("primary-storage-notification", {
    bucket: primaryStorageBucket.id
    // Topics, queues, or Lambda functions can be added here for processing workflows
});

// =============================================================================
// Exports - All required outputs for other stacks
// =============================================================================

// S3 Bucket Outputs
export const primaryBucketName = primaryStorageBucket.bucket;
export const primaryBucketArn = primaryStorageBucket.arn;
export const staticAssetsBucketName = staticAssetsBucket.bucket;
export const staticAssetsBucketArn = staticAssetsBucket.arn;
export const logsBucketName = logsBucket.bucket;
export const logsBucketArn = logsBucket.arn;
export const backupBucketName = backupBucket.bucket;
export const backupBucketArn = backupBucket.arn;
export const artifactsBucketName = artifactsBucket.bucket;
export const artifactsBucketArn = artifactsBucket.arn;

// EFS Outputs
export const sharedEfsId = sharedEfs.id;
export const sharedEfsDnsName = sharedEfs.dnsName;
export const efsSecurityGroupId = efsSg.id;
export const appAccessPointId = appAccessPoint.id;
export const appAccessPointArn = appAccessPoint.arn;

// Backup Outputs
export const backupVaultArn = backupVault.arn;
export const backupVaultName = backupVault.name;
export const backupPlanId = backupPlan.id;
export const backupPlanArn = backupPlan.arn;
export const backupServiceRoleArn = backupServiceRole.arn;

// VPC Endpoint Outputs
export const s3VpcEndpointId = s3VpcEndpoint.id;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information for monitoring and management
export const summary = {
    s3Buckets: {
        primary: {
            name: primaryBucketName,
            arn: primaryBucketArn,
            purpose: "Primary data storage with intelligent tiering"
        },
        staticAssets: {
            name: staticAssetsBucketName,
            arn: staticAssetsBucketArn,
            purpose: "Static web assets with CORS configuration"
        },
        logs: {
            name: logsBucketName,
            arn: logsBucketArn,
            purpose: "Centralized application and system logs"
        },
        backup: {
            name: backupBucketName,
            arn: backupBucketArn,
            purpose: "Database and system backups with archival"
        },
        artifacts: {
            name: artifactsBucketName,
            arn: artifactsBucketArn,
            purpose: "CI/CD artifacts and deployment packages"
        }
    },
    efs: {
        fileSystemId: sharedEfsId,
        dnsName: sharedEfsDnsName,
        accessPoint: appAccessPointId,
        purpose: "Shared storage for applications across availability zones"
    },
    backup: {
        vaultArn: backupVaultArn,
        planId: backupPlanId,
        retentionDays: envConfig.backup.retentionDays,
        purpose: "Automated backup and recovery for critical resources"
    },
    vpc: {
        s3EndpointId: s3VpcEndpointId,
        purpose: "Private access to S3 services without internet gateway"
    }
};

// Environment-specific storage configurations
export const storageConfig = {
    environment: deploymentConfig.environment,
    encryption: {
        applicationKeyId: securityStackOutputs.applicationKeyId,
        databaseKeyId: securityStackOutputs.databaseKeyId,
        enabled: true
    },
    lifecycle: {
        intelligentTiering: !isDevEnvironment,
        glacierTransitionDays: isDevEnvironment ? 30 : 90,
        logRetentionDays: isDevEnvironment ? 30 : 90
    },
    efs: {
        performanceMode: "generalPurpose",
        throughputMode: isDevEnvironment ? "bursting" : "provisioned",
        encrypted: true
    },
    backup: {
        enabled: true,
        schedule: "cron(0 5 ? * * *)",
        retentionDays: envConfig.backup.retentionDays
    }
};