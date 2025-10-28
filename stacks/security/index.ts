import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    COMMON_PORTS,
    COMMON_CIDRS
} from "../../shared";

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

const STACK_NAME = "security";

// Security Stack - Creates security groups, IAM roles, and KMS keys
console.log(`🚀 Deploying Security Stack for environment: ${deploymentConfig.environment}`);

// =============================================================================
// Security Groups
// =============================================================================

// Load Balancer Security Group
const loadBalancerSg = new aws.ec2.SecurityGroup("load-balancer-sg", {
    name: createResourceName(deploymentConfig, "alb-sg"),
    description: "Security group for Application Load Balancers",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "HTTP from internet",
            fromPort: COMMON_PORTS.HTTP,
            toPort: COMMON_PORTS.HTTP,
            protocol: "tcp",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        },
        {
            description: "HTTPS from internet",
            fromPort: COMMON_PORTS.HTTPS,
            toPort: COMMON_PORTS.HTTPS,
            protocol: "tcp",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "alb-sg"),
        Tier: "load-balancer"
    })
});

// Web Application Security Group
const webApplicationSg = new aws.ec2.SecurityGroup("web-application-sg", {
    name: createResourceName(deploymentConfig, "web-app-sg"),
    description: "Security group for web applications",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "HTTP from ALB",
            fromPort: COMMON_PORTS.HTTP,
            toPort: COMMON_PORTS.HTTP,
            protocol: "tcp",
            securityGroups: [loadBalancerSg.id]
        },
        {
            description: "HTTPS from ALB",
            fromPort: COMMON_PORTS.HTTPS,
            toPort: COMMON_PORTS.HTTPS,
            protocol: "tcp",
            securityGroups: [loadBalancerSg.id]
        },
        {
            description: "Application port from ALB",
            fromPort: COMMON_PORTS.APPLICATION,
            toPort: COMMON_PORTS.APPLICATION,
            protocol: "tcp",
            securityGroups: [loadBalancerSg.id]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "web-app-sg"),
        Tier: "web-application"
    })
});

// API Application Security Group
const apiApplicationSg = new aws.ec2.SecurityGroup("api-application-sg", {
    name: createResourceName(deploymentConfig, "api-app-sg"),
    description: "Security group for API applications",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "API port from web apps",
            fromPort: COMMON_PORTS.APPLICATION,
            toPort: COMMON_PORTS.APPLICATION,
            protocol: "tcp",
            securityGroups: [webApplicationSg.id]
        },
        {
            description: "Node.js port from web apps",
            fromPort: COMMON_PORTS.NODEJS,
            toPort: COMMON_PORTS.NODEJS,
            protocol: "tcp",
            securityGroups: [webApplicationSg.id]
        },
        {
            description: "From ALB for health checks",
            fromPort: COMMON_PORTS.HEALTH_CHECK,
            toPort: COMMON_PORTS.HEALTH_CHECK,
            protocol: "tcp",
            securityGroups: [loadBalancerSg.id]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "api-app-sg"),
        Tier: "api-application"
    })
});

// Database Security Group
const databaseSg = new aws.ec2.SecurityGroup("database-sg", {
    name: createResourceName(deploymentConfig, "database-sg"),
    description: "Security group for databases",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "PostgreSQL from app tier",
            fromPort: COMMON_PORTS.POSTGRESQL,
            toPort: COMMON_PORTS.POSTGRESQL,
            protocol: "tcp",
            securityGroups: [webApplicationSg.id, apiApplicationSg.id]
        },
        {
            description: "MySQL from app tier",
            fromPort: COMMON_PORTS.MYSQL,
            toPort: COMMON_PORTS.MYSQL,
            protocol: "tcp",
            securityGroups: [webApplicationSg.id, apiApplicationSg.id]
        },
        {
            description: "Redis from app tier",
            fromPort: COMMON_PORTS.REDIS,
            toPort: COMMON_PORTS.REDIS,
            protocol: "tcp",
            securityGroups: [webApplicationSg.id, apiApplicationSg.id]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "database-sg"),
        Tier: "database"
    })
});

// ECS Security Group
const ecsSg = new aws.ec2.SecurityGroup("ecs-sg", {
    name: createResourceName(deploymentConfig, "ecs-sg"),
    description: "Security group for ECS containers",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "Container ports from ALB",
            fromPort: 8000,
            toPort: 8999,
            protocol: "tcp",
            securityGroups: [loadBalancerSg.id]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "ecs-sg"),
        Tier: "container"
    })
});

// EKS Security Group
const eksSg = new aws.ec2.SecurityGroup("eks-sg", {
    name: createResourceName(deploymentConfig, "eks-sg"),
    description: "Security group for EKS nodes",
    vpcId: networkStackOutputs.vpcId,
    ingress: [
        {
            description: "Node communication",
            fromPort: 0,
            toPort: 65535,
            protocol: "tcp",
            self: true
        },
        {
            description: "Pod communication",
            fromPort: 1025,
            toPort: 65535,
            protocol: "tcp",
            cidrBlocks: [COMMON_CIDRS.VPC]
        }
    ],
    egress: [
        {
            description: "All outbound traffic",
            fromPort: 0,
            toPort: 0,
            protocol: "-1",
            cidrBlocks: [COMMON_CIDRS.ALL_TRAFFIC]
        }
    ],
    tags: createResourceTags(deploymentConfig, "security-group", {
        Name: createResourceName(deploymentConfig, "eks-sg"),
        Tier: "kubernetes"
    })
});

// =============================================================================
// IAM Roles
// =============================================================================

// ECS Execution Role
const ecsExecutionRole = new aws.iam.Role("ecs-execution-role", {
    name: createResourceName(deploymentConfig, "ecs-execution-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ecs-tasks.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "ecs-execution-role"),
        Service: "ECS"
    })
});

const ecsExecutionRolePolicy = new aws.iam.RolePolicyAttachment("ecs-execution-role-policy", {
    role: ecsExecutionRole.name,
    policyArn: "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
});

// ECS Task Role
const ecsTaskRole = new aws.iam.Role("ecs-task-role", {
    name: createResourceName(deploymentConfig, "ecs-task-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ecs-tasks.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "ecs-task-role"),
        Service: "ECS"
    })
});

// EKS Cluster Role
const eksClusterRole = new aws.iam.Role("eks-cluster-role", {
    name: createResourceName(deploymentConfig, "eks-cluster-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "eks.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "eks-cluster-role"),
        Service: "EKS"
    })
});

const eksClusterPolicyAttachment = new aws.iam.RolePolicyAttachment("eks-cluster-policy", {
    role: eksClusterRole.name,
    policyArn: "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
});

// EKS Node Group Role
const eksNodeGroupRole = new aws.iam.Role("eks-node-group-role", {
    name: createResourceName(deploymentConfig, "eks-node-group-role"),
    assumeRolePolicy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [{
            Action: "sts:AssumeRole",
            Effect: "Allow",
            Principal: {
                Service: "ec2.amazonaws.com"
            }
        }]
    }),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "eks-node-group-role"),
        Service: "EKS"
    })
});

const eksNodeGroupPolicies = [
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
];

const eksNodeGroupPolicyAttachments = eksNodeGroupPolicies.map((policyArn, index) => {
    return new aws.iam.RolePolicyAttachment(`eks-node-group-policy-${index}`, {
        role: eksNodeGroupRole.name,
        policyArn: policyArn
    });
});

// =============================================================================
// KMS Keys
// =============================================================================

// Application KMS Key
const applicationKey = new aws.kms.Key("application-key", {
    description: "KMS key for application encryption",
    keyUsage: "ENCRYPT_DECRYPT",
    keySpec: "SYMMETRIC_DEFAULT",
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Sid: "Enable IAM User Permissions",
                Effect: "Allow",
                Principal: {
                    AWS: `arn:aws:iam::${aws.getCallerIdentity().then(id => id.accountId)}:root`
                },
                Action: "kms:*",
                Resource: "*"
            },
            {
                Sid: "Allow application services",
                Effect: "Allow",
                Principal: {
                    AWS: [
                        ecsExecutionRole.arn,
                        ecsTaskRole.arn,
                        eksClusterRole.arn
                    ]
                },
                Action: [
                    "kms:Decrypt",
                    "kms:GenerateDataKey"
                ],
                Resource: "*"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "kms-key", {
        Name: createResourceName(deploymentConfig, "application-key"),
        Type: "Application"
    })
});

const applicationKeyAlias = new aws.kms.Alias("application-key-alias", {
    name: `alias/${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-application`,
    targetKeyId: applicationKey.keyId
});

// Database KMS Key
const databaseKey = new aws.kms.Key("database-key", {
    description: "KMS key for database encryption",
    keyUsage: "ENCRYPT_DECRYPT",
    keySpec: "SYMMETRIC_DEFAULT",
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Sid: "Enable IAM User Permissions",
                Effect: "Allow",
                Principal: {
                    AWS: `arn:aws:iam::${aws.getCallerIdentity().then(id => id.accountId)}:root`
                },
                Action: "kms:*",
                Resource: "*"
            },
            {
                Sid: "Allow RDS service",
                Effect: "Allow",
                Principal: {
                    Service: "rds.amazonaws.com"
                },
                Action: [
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:ReEncrypt*",
                    "kms:CreateGrant",
                    "kms:DescribeKey"
                ],
                Resource: "*"
            }
        ]
    }),
    tags: createResourceTags(deploymentConfig, "kms-key", {
        Name: createResourceName(deploymentConfig, "database-key"),
        Type: "Database"
    })
});

const databaseKeyAlias = new aws.kms.Alias("database-key-alias", {
    name: `alias/${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-database`,
    targetKeyId: databaseKey.keyId
});

// Infrastructure KMS Key
const infrastructureKey = new aws.kms.Key("infrastructure-key", {
    description: "KMS key for infrastructure encryption",
    keyUsage: "ENCRYPT_DECRYPT",
    keySpec: "SYMMETRIC_DEFAULT",
    tags: createResourceTags(deploymentConfig, "kms-key", {
        Name: createResourceName(deploymentConfig, "infrastructure-key"),
        Type: "Infrastructure"
    })
});

const infrastructureKeyAlias = new aws.kms.Alias("infrastructure-key-alias", {
    name: `alias/${deploymentConfig.projectName}-${deploymentConfig.deploymentId}-infrastructure`,
    targetKeyId: infrastructureKey.keyId
});

// Export all stack outputs
export const loadBalancerSgId = loadBalancerSg.id;
export const webApplicationSgId = webApplicationSg.id;
export const apiApplicationSgId = apiApplicationSg.id;
export const databaseSgId = databaseSg.id;
export const ecsSgId = ecsSg.id;
export const eksSgId = eksSg.id;

export const ecsExecutionRoleArn = ecsExecutionRole.arn;
export const ecsExecutionRoleName = ecsExecutionRole.name;
export const ecsTaskRoleArn = ecsTaskRole.arn;
export const ecsTaskRoleName = ecsTaskRole.name;
export const eksClusterRoleArn = eksClusterRole.arn;
export const eksClusterRoleName = eksClusterRole.name;
export const eksNodeGroupRoleArn = eksNodeGroupRole.arn;
export const eksNodeGroupRoleName = eksNodeGroupRole.name;

export const applicationKeyId = applicationKey.keyId;
export const applicationKeyArn = applicationKey.arn;
export const databaseKeyId = databaseKey.keyId;
export const databaseKeyArn = databaseKey.arn;
export const infrastructureKeyId = infrastructureKey.keyId;
export const infrastructureKeyArn = infrastructureKey.arn;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    securityGroups: {
        loadBalancer: loadBalancerSgId,
        webApplication: webApplicationSgId,
        apiApplication: apiApplicationSgId,
        database: databaseSgId,
        ecs: ecsSgId,
        eks: eksSgId
    },
    iamRoles: {
        ecsExecution: ecsExecutionRoleArn,
        ecsTask: ecsTaskRoleArn,
        eksCluster: eksClusterRoleArn,
        eksNodeGroup: eksNodeGroupRoleArn
    },
    kmsKeys: {
        application: applicationKeyArn,
        database: databaseKeyArn,
        infrastructure: infrastructureKeyArn
    }
};