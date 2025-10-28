import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import * as eks from "@pulumi/eks";
import {
    centralState,
    createResourceName,
    createResourceTags,
    validateConfig,
    NetworkOutputs,
    SecurityOutputs,
    getCurrentRegion,
    getCurrentAccountId,
    isDevelopment,
    isProduction,
    ENVIRONMENT_DEFAULTS
} from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Get dependent stack outputs
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

// ECR stack outputs for container image integration
const ecrRegistryId = centralState.getStackOutput<string>("services-ecr", "registryId");
const ecrRegistryUri = centralState.getStackOutput<string>("services-ecr", "registryUri");

const STACK_NAME = "services-eks";

// EKS Services Stack - Kubernetes orchestration with EKS cluster and node groups
console.log(`🚀 Deploying EKS Services Stack for environment: ${deploymentConfig.environment}`);

// Configuration parameters based on environment
const envDefaults = ENVIRONMENT_DEFAULTS[deploymentConfig.environment];
const currentRegion = getCurrentRegion();
const currentAccountId = getCurrentAccountId();

// EKS Configuration
const eksConfig = {
    // Kubernetes version
    version: config.get("kubernetesVersion") || "1.27",

    // API endpoint access configuration
    endpointPrivateAccess: config.getBoolean("endpointPrivateAccess") !== false, // Default true
    endpointPublicAccess: config.getBoolean("endpointPublicAccess") || false, // Default false for security
    endpointPublicAccessCidrs: config.getObject<string[]>("endpointPublicAccessCidrs") || ["0.0.0.0/0"],

    // Encryption configuration
    enableSecretsEncryption: config.getBoolean("enableSecretsEncryption") !== false, // Default true

    // Logging configuration
    enabledLogTypes: config.getObject<string[]>("enabledLogTypes") || [
        "api",
        "audit",
        "authenticator",
        "controllerManager",
        "scheduler"
    ],

    // Node group configuration
    nodeGroup: {
        instanceTypes: config.getObject<string[]>("nodeInstanceTypes") ||
            (isDevelopment(deploymentConfig) ? ["t3.medium", "t3.large"] : ["m5.large", "m5.xlarge", "c5.large"]),
        minSize: config.getNumber("nodeMinSize") || envDefaults.autoScaling.minCapacity,
        maxSize: config.getNumber("nodeMaxSize") || envDefaults.autoScaling.maxCapacity,
        desiredSize: config.getNumber("nodeDesiredSize") || envDefaults.autoScaling.minCapacity,
        diskSize: config.getNumber("nodeDiskSize") || 50,
        amiType: config.get("nodeAmiType") || "AL2_x86_64",
        capacityType: config.get("nodeCapacityType") || "ON_DEMAND",

        // Spot instance configuration
        enableSpotInstances: config.getBoolean("enableSpotInstances") || !isProduction(deploymentConfig),
        spotInstanceTypes: config.getObject<string[]>("spotInstanceTypes") || ["t3.medium", "t3.large", "m5.large"],
        spotMaxPrice: config.get("spotMaxPrice") || "0.10"
    },

    // Add-ons configuration
    addons: {
        vpcCni: {
            version: config.get("vpcCniVersion") || "v1.13.4-eksbuild.1",
            resolve: config.get("vpcCniResolveConflicts") || "OVERWRITE"
        },
        coreDns: {
            version: config.get("coreDnsVersion") || "v1.10.1-eksbuild.1",
            resolve: config.get("coreDnsResolveConflicts") || "OVERWRITE"
        },
        kubeProxy: {
            version: config.get("kubeProxyVersion") || "v1.27.3-eksbuild.1",
            resolve: config.get("kubeProxyResolveConflicts") || "OVERWRITE"
        },
        ebsCsiDriver: {
            version: config.get("ebsCsiVersion") || "v1.20.0-eksbuild.1",
            resolve: config.get("ebsCsiResolveConflicts") || "OVERWRITE"
        }
    }
};

// =============================================================================
// EKS Cluster Security Groups
// =============================================================================

// Additional security group for EKS cluster control plane
const eksClusterAdditionalSg = new aws.ec2.SecurityGroup("eks-cluster-additional-sg", {
    name: createResourceName(deploymentConfig, "eks-cluster-additional-sg"),
    description: "Additional security group for EKS cluster control plane",
    vpcId: networkStackOutputs.vpcId,

    ingress: [
        {
            description: "HTTPS API access from VPC",
            fromPort: 443,
            toPort: 443,
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
        Name: createResourceName(deploymentConfig, "eks-cluster-additional-sg"),
        Service: "eks-cluster",
        Component: "control-plane"
    })
});

// =============================================================================
// EKS Cluster
// =============================================================================

const eksCluster = new aws.eks.Cluster("eks-cluster", {
    name: createResourceName(deploymentConfig, "eks"),
    version: eksConfig.version,
    roleArn: securityStackOutputs.eksClusterRoleArn,

    vpcConfig: {
        subnetIds: pulumi.all([
            networkStackOutputs.privateSubnetIds,
            eksConfig.endpointPublicAccess ? networkStackOutputs.publicSubnetIds : []
        ]).apply(([privateSubnets, publicSubnets]) => [...privateSubnets, ...publicSubnets]),
        endpointPrivateAccess: eksConfig.endpointPrivateAccess,
        endpointPublicAccess: eksConfig.endpointPublicAccess,
        publicAccessCidrs: eksConfig.endpointPublicAccessCidrs,
        securityGroupIds: [eksClusterAdditionalSg.id]
    },

    // Encryption configuration for secrets
    encryptionConfig: eksConfig.enableSecretsEncryption ? {
        provider: {
            keyArn: securityStackOutputs.applicationKeyArn
        },
        resources: ["secrets"]
    } : undefined,

    // Enable control plane logging
    enabledClusterLogTypes: eksConfig.enabledLogTypes,

    tags: createResourceTags(deploymentConfig, "eks-cluster", {
        Name: createResourceName(deploymentConfig, "eks"),
        KubernetesVersion: eksConfig.version,
        Environment: deploymentConfig.environment,
        Service: "kubernetes"
    }),

    // Ensure cluster is created before node groups
    dependsOn: []
});

// =============================================================================
// EKS Add-ons
// =============================================================================

// VPC CNI Add-on
const vpcCniAddon = new aws.eks.Addon("vpc-cni-addon", {
    clusterName: eksCluster.name,
    addonName: "vpc-cni",
    addonVersion: eksConfig.addons.vpcCni.version,
    resolveConflicts: eksConfig.addons.vpcCni.resolve,
    tags: createResourceTags(deploymentConfig, "eks-addon", {
        Name: createResourceName(deploymentConfig, "vpc-cni-addon"),
        Addon: "vpc-cni"
    })
});

// CoreDNS Add-on
const coreDnsAddon = new aws.eks.Addon("coredns-addon", {
    clusterName: eksCluster.name,
    addonName: "coredns",
    addonVersion: eksConfig.addons.coreDns.version,
    resolveConflicts: eksConfig.addons.coreDns.resolve,
    tags: createResourceTags(deploymentConfig, "eks-addon", {
        Name: createResourceName(deploymentConfig, "coredns-addon"),
        Addon: "coredns"
    })
}, { dependsOn: [vpcCniAddon] });

// Kube-proxy Add-on
const kubeProxyAddon = new aws.eks.Addon("kube-proxy-addon", {
    clusterName: eksCluster.name,
    addonName: "kube-proxy",
    addonVersion: eksConfig.addons.kubeProxy.version,
    resolveConflicts: eksConfig.addons.kubeProxy.resolve,
    tags: createResourceTags(deploymentConfig, "eks-addon", {
        Name: createResourceName(deploymentConfig, "kube-proxy-addon"),
        Addon: "kube-proxy"
    })
});

// EBS CSI Driver Add-on
const ebsCsiAddon = new aws.eks.Addon("ebs-csi-addon", {
    clusterName: eksCluster.name,
    addonName: "aws-ebs-csi-driver",
    addonVersion: eksConfig.addons.ebsCsiDriver.version,
    resolveConflicts: eksConfig.addons.ebsCsiDriver.resolve,
    serviceAccountRoleArn: pulumi.interpolate`arn:aws:iam::${currentAccountId}:role/AmazonEKS_EBS_CSI_DriverRole`,
    tags: createResourceTags(deploymentConfig, "eks-addon", {
        Name: createResourceName(deploymentConfig, "ebs-csi-addon"),
        Addon: "aws-ebs-csi-driver"
    })
});

// =============================================================================
// Launch Template for Node Groups
// =============================================================================

const nodeGroupLaunchTemplate = new aws.ec2.LaunchTemplate("eks-node-group-lt", {
    name: createResourceName(deploymentConfig, "eks-node-lt"),
    description: "Launch template for EKS node groups",

    imageId: pulumi.output(aws.eks.getNodeGroupAmiType({
        amiType: eksConfig.nodeGroup.amiType,
        kubernetesVersion: eksConfig.version
    })).apply(ami => ami.id),

    instanceType: eksConfig.nodeGroup.instanceTypes[0],

    keyName: config.get("keyPairName"), // Optional SSH key pair

    vpcSecurityGroupIds: [securityStackOutputs.eksSgId],

    blockDeviceMappings: [{
        deviceName: "/dev/xvda",
        ebs: {
            volumeSize: eksConfig.nodeGroup.diskSize,
            volumeType: "gp3",
            encrypted: true,
            kmsKeyId: securityStackOutputs.applicationKeyArn,
            deleteOnTermination: true
        }
    }],

    metadataOptions: {
        httpEndpoint: "enabled",
        httpTokens: "required",
        httpPutResponseHopLimit: 2
    },

    userData: pulumi.interpolate`#!/bin/bash
/etc/eks/bootstrap.sh ${eksCluster.name}
yum update -y
`,

    tags: createResourceTags(deploymentConfig, "launch-template", {
        Name: createResourceName(deploymentConfig, "eks-node-lt"),
        Service: "eks-nodes"
    }),

    tagSpecifications: [
        {
            resourceType: "instance",
            tags: createResourceTags(deploymentConfig, "eks-node", {
                Name: createResourceName(deploymentConfig, "eks-node"),
                Service: "kubernetes"
            })
        },
        {
            resourceType: "volume",
            tags: createResourceTags(deploymentConfig, "eks-node-volume", {
                Name: createResourceName(deploymentConfig, "eks-node-volume"),
                Service: "kubernetes"
            })
        }
    ]
});

// =============================================================================
// Primary Node Group (On-Demand)
// =============================================================================

const primaryNodeGroup = new aws.eks.NodeGroup("primary-node-group", {
    clusterName: eksCluster.name,
    nodeGroupName: createResourceName(deploymentConfig, "primary-ng"),
    nodeRoleArn: securityStackOutputs.eksNodeGroupRoleArn,

    subnetIds: networkStackOutputs.privateSubnetIds,

    scalingConfig: {
        minSize: eksConfig.nodeGroup.minSize,
        maxSize: eksConfig.nodeGroup.maxSize,
        desiredSize: eksConfig.nodeGroup.desiredSize
    },

    updateConfig: {
        maxUnavailablePercentage: 25
    },

    instanceTypes: eksConfig.nodeGroup.instanceTypes,
    capacityType: eksConfig.nodeGroup.capacityType,
    amiType: eksConfig.nodeGroup.amiType,
    diskSize: eksConfig.nodeGroup.diskSize,

    launchTemplate: {
        id: nodeGroupLaunchTemplate.id,
        version: nodeGroupLaunchTemplate.latestVersion
    },

    // Taints for primary nodes (none by default)
    taints: [],

    labels: {
        "nodegroup-type": "primary",
        "capacity-type": "on-demand",
        "environment": deploymentConfig.environment
    },

    tags: createResourceTags(deploymentConfig, "eks-nodegroup", {
        Name: createResourceName(deploymentConfig, "primary-ng"),
        Type: "primary",
        CapacityType: "on-demand"
    }),

    // Ensure cluster and addons are ready before creating node group
    dependsOn: [eksCluster, vpcCniAddon, coreDnsAddon, kubeProxyAddon, ebsCsiAddon]
});

// =============================================================================
// Spot Instance Node Group (Optional)
// =============================================================================

let spotNodeGroup: aws.eks.NodeGroup | undefined;

if (eksConfig.nodeGroup.enableSpotInstances) {
    const spotLaunchTemplate = new aws.ec2.LaunchTemplate("eks-spot-node-group-lt", {
        name: createResourceName(deploymentConfig, "eks-spot-node-lt"),
        description: "Launch template for EKS spot node groups",

        instanceType: eksConfig.nodeGroup.spotInstanceTypes[0],

        keyName: config.get("keyPairName"),

        vpcSecurityGroupIds: [securityStackOutputs.eksSgId],

        blockDeviceMappings: [{
            deviceName: "/dev/xvda",
            ebs: {
                volumeSize: eksConfig.nodeGroup.diskSize,
                volumeType: "gp3",
                encrypted: true,
                kmsKeyId: securityStackOutputs.applicationKeyArn,
                deleteOnTermination: true
            }
        }],

        instanceMarketOptions: {
            marketType: "spot",
            spotOptions: {
                maxPrice: eksConfig.nodeGroup.spotMaxPrice,
                spotInstanceType: "one-time"
            }
        },

        userData: pulumi.interpolate`#!/bin/bash
/etc/eks/bootstrap.sh ${eksCluster.name}
yum update -y
`,

        tags: createResourceTags(deploymentConfig, "launch-template", {
            Name: createResourceName(deploymentConfig, "eks-spot-node-lt"),
            Service: "eks-spot-nodes"
        })
    });

    spotNodeGroup = new aws.eks.NodeGroup("spot-node-group", {
        clusterName: eksCluster.name,
        nodeGroupName: createResourceName(deploymentConfig, "spot-ng"),
        nodeRoleArn: securityStackOutputs.eksNodeGroupRoleArn,

        subnetIds: networkStackOutputs.privateSubnetIds,

        scalingConfig: {
            minSize: 0,
            maxSize: Math.max(eksConfig.nodeGroup.maxSize, 10),
            desiredSize: isDevelopment(deploymentConfig) ? 1 : 2
        },

        updateConfig: {
            maxUnavailablePercentage: 50 // Higher percentage for spot instances
        },

        instanceTypes: eksConfig.nodeGroup.spotInstanceTypes,
        capacityType: "SPOT",
        amiType: eksConfig.nodeGroup.amiType,
        diskSize: eksConfig.nodeGroup.diskSize,

        launchTemplate: {
            id: spotLaunchTemplate.id,
            version: spotLaunchTemplate.latestVersion
        },

        // Taints for spot nodes
        taints: [{
            key: "spot-instance",
            value: "true",
            effect: "NO_SCHEDULE"
        }],

        labels: {
            "nodegroup-type": "spot",
            "capacity-type": "spot",
            "environment": deploymentConfig.environment,
            "spot-instance": "true"
        },

        tags: createResourceTags(deploymentConfig, "eks-nodegroup", {
            Name: createResourceName(deploymentConfig, "spot-ng"),
            Type: "spot",
            CapacityType: "spot"
        }),

        dependsOn: [primaryNodeGroup]
    });
}

// =============================================================================
// CloudWatch Log Groups for EKS
// =============================================================================

const eksLogGroups = eksConfig.enabledLogTypes.map(logType => {
    return new aws.cloudwatch.LogGroup(`eks-${logType}-logs`, {
        name: `/aws/eks/${createResourceName(deploymentConfig, "eks")}/cluster/${logType}`,
        retentionInDays: isDevelopment(deploymentConfig) ? 7 : 30,
        kmsKeyId: securityStackOutputs.applicationKeyArn,
        tags: createResourceTags(deploymentConfig, "log-group", {
            Name: createResourceName(deploymentConfig, `eks-${logType}-logs`),
            LogType: logType,
            Service: "eks"
        })
    });
});

// =============================================================================
// OIDC Identity Provider for Service Accounts
// =============================================================================

const eksOidcProvider = new aws.iam.OpenIdConnectProvider("eks-oidc-provider", {
    url: eksCluster.identities[0].oidcs[0].issuer,
    clientIdList: ["sts.amazonaws.com"],
    thumbprintList: ["9e99a48a9960b14926bb7f3b02e22da2b0ab7280"], // EKS OIDC root CA thumbprint
    tags: createResourceTags(deploymentConfig, "oidc-provider", {
        Name: createResourceName(deploymentConfig, "eks-oidc-provider"),
        Service: "eks-oidc"
    })
});

// =============================================================================
// EBS CSI Driver Service Account Role
// =============================================================================

const ebsCsiServiceAccountRole = new aws.iam.Role("ebs-csi-service-account-role", {
    name: "AmazonEKS_EBS_CSI_DriverRole",
    assumeRolePolicy: pulumi.all([eksCluster.identities[0].oidcs[0].issuer, currentAccountId])
        .apply(([issuer, accountId]) => JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Effect: "Allow",
                Principal: {
                    Federated: `arn:aws:iam::${accountId}:oidc-provider/${issuer.replace("https://", "")}`
                },
                Action: "sts:AssumeRoleWithWebIdentity",
                Condition: {
                    StringEquals: {
                        [`${issuer.replace("https://", "")}:sub`]: "system:serviceaccount:kube-system:ebs-csi-controller-sa",
                        [`${issuer.replace("https://", "")}:aud`]: "sts.amazonaws.com"
                    }
                }
            }]
        })),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: "AmazonEKS_EBS_CSI_DriverRole",
        Service: "eks-ebs-csi"
    })
});

const ebsCsiServiceAccountPolicyAttachment = new aws.iam.RolePolicyAttachment("ebs-csi-service-account-policy", {
    role: ebsCsiServiceAccountRole.name,
    policyArn: "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
});

// =============================================================================
// Cluster Autoscaler IAM Role
// =============================================================================

const clusterAutoscalerRole = new aws.iam.Role("cluster-autoscaler-role", {
    name: createResourceName(deploymentConfig, "cluster-autoscaler-role"),
    assumeRolePolicy: pulumi.all([eksCluster.identities[0].oidcs[0].issuer, currentAccountId])
        .apply(([issuer, accountId]) => JSON.stringify({
            Version: "2012-10-17",
            Statement: [{
                Effect: "Allow",
                Principal: {
                    Federated: `arn:aws:iam::${accountId}:oidc-provider/${issuer.replace("https://", "")}`
                },
                Action: "sts:AssumeRoleWithWebIdentity",
                Condition: {
                    StringEquals: {
                        [`${issuer.replace("https://", "")}:sub`]: "system:serviceaccount:kube-system:cluster-autoscaler",
                        [`${issuer.replace("https://", "")}:aud`]: "sts.amazonaws.com"
                    }
                }
            }]
        })),
    tags: createResourceTags(deploymentConfig, "iam-role", {
        Name: createResourceName(deploymentConfig, "cluster-autoscaler-role"),
        Service: "cluster-autoscaler"
    })
});

const clusterAutoscalerPolicy = new aws.iam.RolePolicy("cluster-autoscaler-policy", {
    role: clusterAutoscalerRole.id,
    policy: JSON.stringify({
        Version: "2012-10-17",
        Statement: [
            {
                Effect: "Allow",
                Action: [
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:DescribeAutoScalingInstances",
                    "autoscaling:DescribeLaunchConfigurations",
                    "autoscaling:DescribeTags",
                    "autoscaling:SetDesiredCapacity",
                    "autoscaling:TerminateInstanceInAutoScalingGroup",
                    "ec2:DescribeLaunchTemplateVersions"
                ],
                Resource: "*"
            }
        ]
    })
});

// =============================================================================
// Outputs
// =============================================================================

// Cluster information
export const clusterName = eksCluster.name;
export const clusterArn = eksCluster.arn;
export const clusterEndpoint = eksCluster.endpoint;
export const clusterVersion = eksCluster.version;
export const clusterSecurityGroupId = eksCluster.vpcConfig.clusterSecurityGroupId;
export const clusterCertificateAuthority = eksCluster.certificateAuthorityData;

// OIDC information
export const clusterOidcIssuerUrl = eksCluster.identities[0].oidcs[0].issuer;
export const oidcProviderArn = eksOidcProvider.arn;

// Node group information
export const primaryNodeGroupName = primaryNodeGroup.nodeGroupName;
export const primaryNodeGroupArn = primaryNodeGroup.arn;
export const primaryNodeGroupStatus = primaryNodeGroup.status;

export const spotNodeGroupName = spotNodeGroup?.nodeGroupName;
export const spotNodeGroupArn = spotNodeGroup?.arn;
export const spotNodeGroupEnabled = eksConfig.nodeGroup.enableSpotInstances;

// Launch template information
export const nodeGroupLaunchTemplateId = nodeGroupLaunchTemplate.id;
export const spotLaunchTemplateId = spotNodeGroup ? spotLaunchTemplate.id : undefined;

// Add-on information
export const vpcCniAddonArn = vpcCniAddon.arn;
export const coreDnsAddonArn = coreDnsAddon.arn;
export const kubeProxyAddonArn = kubeProxyAddon.arn;
export const ebsCsiAddonArn = ebsCsiAddon.arn;

// Service account roles
export const ebsCsiServiceAccountRoleArn = ebsCsiServiceAccountRole.arn;
export const clusterAutoscalerRoleArn = clusterAutoscalerRole.arn;

// ECR integration
export const ecrIntegration = {
    registryId: ecrRegistryId,
    registryUri: ecrRegistryUri
};

// Kubeconfig
export const kubeconfig = pulumi.all([
    eksCluster.name,
    eksCluster.endpoint,
    eksCluster.certificateAuthorityData,
    currentRegion
]).apply(([name, endpoint, ca, region]) => JSON.stringify({
    apiVersion: "v1",
    clusters: [{
        cluster: {
            server: endpoint,
            "certificate-authority-data": ca
        },
        name: "kubernetes"
    }],
    contexts: [{
        context: {
            cluster: "kubernetes",
            user: "aws"
        },
        name: "aws"
    }],
    "current-context": "aws",
    kind: "Config",
    preferences: {},
    users: [{
        name: "aws",
        user: {
            exec: {
                apiVersion: "client.authentication.k8s.io/v1beta1",
                command: "aws",
                args: ["eks", "get-token", "--cluster-name", name, "--region", region]
            }
        }
    }]
}));

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Comprehensive summary
export const summary = {
    cluster: {
        name: clusterName,
        arn: clusterArn,
        endpoint: clusterEndpoint,
        version: clusterVersion,
        oidcIssuer: clusterOidcIssuerUrl,
        privateAccess: eksConfig.endpointPrivateAccess,
        publicAccess: eksConfig.endpointPublicAccess,
        encryptionEnabled: eksConfig.enableSecretsEncryption,
        logTypesEnabled: eksConfig.enabledLogTypes
    },
    nodeGroups: {
        primary: {
            name: primaryNodeGroupName,
            arn: primaryNodeGroupArn,
            instanceTypes: eksConfig.nodeGroup.instanceTypes,
            capacityType: eksConfig.nodeGroup.capacityType,
            minSize: eksConfig.nodeGroup.minSize,
            maxSize: eksConfig.nodeGroup.maxSize,
            desiredSize: eksConfig.nodeGroup.desiredSize
        },
        spot: spotNodeGroup ? {
            name: spotNodeGroupName,
            arn: spotNodeGroupArn,
            instanceTypes: eksConfig.nodeGroup.spotInstanceTypes,
            capacityType: "SPOT",
            enabled: eksConfig.nodeGroup.enableSpotInstances
        } : null
    },
    addons: {
        vpcCni: {
            version: eksConfig.addons.vpcCni.version,
            arn: vpcCniAddonArn
        },
        coreDns: {
            version: eksConfig.addons.coreDns.version,
            arn: coreDnsAddonArn
        },
        kubeProxy: {
            version: eksConfig.addons.kubeProxy.version,
            arn: kubeProxyAddonArn
        },
        ebsCsi: {
            version: eksConfig.addons.ebsCsiDriver.version,
            arn: ebsCsiAddonArn
        }
    },
    serviceAccounts: {
        ebsCsiDriver: ebsCsiServiceAccountRoleArn,
        clusterAutoscaler: clusterAutoscalerRoleArn
    },
    integration: {
        ecr: ecrIntegration,
        oidcProvider: oidcProviderArn
    },
    networking: {
        vpc: networkStackOutputs.vpcId,
        privateSubnets: networkStackOutputs.privateSubnetIds,
        securityGroups: {
            cluster: clusterSecurityGroupId,
            additional: eksClusterAdditionalSg.id
        }
    }
};

console.log(`✅ EKS Services Stack deployment completed for ${deploymentConfig.environment}`);
console.log(`🎯 EKS Cluster: ${createResourceName(deploymentConfig, "eks")} (v${eksConfig.version})`);
console.log(`🚀 Primary Node Group: ${eksConfig.nodeGroup.instanceTypes.join(", ")} (${eksConfig.nodeGroup.minSize}-${eksConfig.nodeGroup.maxSize} nodes)`);
console.log(`💰 Spot Instances: ${eksConfig.nodeGroup.enableSpotInstances ? "Enabled" : "Disabled"}`);
console.log(`🔒 API Access: Private=${eksConfig.endpointPrivateAccess}, Public=${eksConfig.endpointPublicAccess}`);
console.log(`🔐 Secrets Encryption: ${eksConfig.enableSecretsEncryption ? "Enabled" : "Disabled"}`);
console.log(`📋 Add-ons: VPC-CNI, CoreDNS, Kube-proxy, EBS-CSI`);