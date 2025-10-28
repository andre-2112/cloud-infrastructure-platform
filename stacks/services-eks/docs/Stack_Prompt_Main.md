# EKS Services Stack Pulumi Generation Prompt

Create Pulumi TypeScript code for Kubernetes orchestration with EKS for ${PROJECT_NAME}. Include EKS cluster, node groups, addons (VPC CNI, CoreDNS, kube-proxy, EBS CSI). Dependencies: network, security, services-ecr. Key outputs: clusterEndpoint, clusterArn, primaryNodeGroupArn. Use variables: ${DEPLOYMENT_ID}, ${PROJECT_NAME}.
