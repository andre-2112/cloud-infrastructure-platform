```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: services-eks
  version: v1
  description: Kubernetes orchestration with EKS cluster and node groups
  language: typescript
  priority: 120

spec:
  dependencies:
    - network
    - security
    - services-ecr

  resources:
    eks_cluster:
      main_cluster:
        name: "${config.project}-${config.environment}-eks"
        role_arn: "${deps.security.iam_role_arns.eks_cluster_role_arn}"
        version: "${config.kubernetes_version}"
        vpc_config:
          subnet_ids: "${deps.network.subnet_info.private_subnet_ids}"
          security_group_ids:
            - "${deps.security.security_group_ids.eks_cluster_sg_id}"
          endpoint_config:
            private_access: true
            public_access: "${config.public_access_enabled}"
            public_access_cidrs: "${config.public_access_cidrs}"
        encryption_config:
          resources: ["secrets"]
          provider:
            key_arn: "${deps.security.kms_key_ids.infrastructure_key_arn}"
        enabled_cluster_log_types: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
        tags:
          Name: "${config.project}-${config.environment}-eks-cluster"
          Environment: "${config.environment}"

    eks_node_groups:
      primary_nodes:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        node_group_name: "${config.project}-${config.environment}-primary"
        node_role_arn: "${deps.security.iam_role_arns.eks_node_group_role_arn}"
        subnet_ids: "${deps.network.subnet_info.private_subnet_ids}"
        capacity_type: "ON_DEMAND"
        instance_types: "${config.node_instance_types}"
        disk_size: "${config.node_disk_size}"
        scaling_config:
          desired_size: "${config.node_desired_size}"
          max_size: "${config.node_max_size}"
          min_size: "${config.node_min_size}"
        update_config:
          max_unavailable: 1
        tags:
          Name: "${config.project}-${config.environment}-primary-nodes"
          Environment: "${config.environment}"

      spot_nodes:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        node_group_name: "${config.project}-${config.environment}-spot"
        node_role_arn: "${deps.security.iam_role_arns.eks_node_group_role_arn}"
        subnet_ids: "${deps.network.subnet_info.private_subnet_ids}"
        capacity_type: "SPOT"
        instance_types: "${config.spot_instance_types}"
        disk_size: "${config.node_disk_size}"
        scaling_config:
          desired_size: "${config.spot_desired_size}"
          max_size: "${config.spot_max_size}"
          min_size: "${config.spot_min_size}"
        condition: "${config.enable_spot_instances}"
        tags:
          Name: "${config.project}-${config.environment}-spot-nodes"
          Environment: "${config.environment}"

    eks_addons:
      vpc_cni:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        addon_name: "vpc-cni"
        addon_version: "${config.vpc_cni_version}"
        resolve_conflicts: "OVERWRITE"

      coredns:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        addon_name: "coredns"
        addon_version: "${config.coredns_version}"
        resolve_conflicts: "OVERWRITE"

      kube_proxy:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        addon_name: "kube-proxy"
        addon_version: "${config.kube_proxy_version}"
        resolve_conflicts: "OVERWRITE"

      ebs_csi_driver:
        cluster_name: "${resources.eks_cluster.main_cluster.name}"
        addon_name: "aws-ebs-csi-driver"
        addon_version: "${config.ebs_csi_version}"
        service_account_role_arn: "${deps.security.iam_role_arns.ebs_csi_role_arn}"
        resolve_conflicts: "OVERWRITE"

  outputs:
    cluster_info:
      cluster_id:
        description: "EKS cluster ID"
        value: "${resources.eks_cluster.main_cluster.id}"

      cluster_arn:
        description: "EKS cluster ARN"
        value: "${resources.eks_cluster.main_cluster.arn}"

      cluster_endpoint:
        description: "EKS cluster endpoint"
        value: "${resources.eks_cluster.main_cluster.endpoint}"

      cluster_version:
        description: "EKS cluster Kubernetes version"
        value: "${resources.eks_cluster.main_cluster.version}"

      cluster_security_group_id:
        description: "EKS cluster security group ID"
        value: "${resources.eks_cluster.main_cluster.vpc_config[0].cluster_security_group_id}"

    node_group_info:
      primary_node_group_arn:
        description: "Primary node group ARN"
        value: "${resources.eks_node_groups.primary_nodes.arn}"

      spot_node_group_arn:
        description: "Spot node group ARN"
        value: "${config.enable_spot_instances ? resources.eks_node_groups.spot_nodes.arn : null}"

    cluster_auth:
      cluster_ca_certificate:
        description: "EKS cluster certificate authority data"
        value: "${resources.eks_cluster.main_cluster.certificate_authority[0].data}"
        sensitive: true

  parameters:
    project:
      type: string
      description: "Project name for resource naming"
      required: true
      default: "${PROJECT_NAME}"

    environment:
      type: string
      description: "Environment name"
      required: true
      validation:
        allowed_values: ["dev", "stage", "prod"]

    kubernetes_version:
      type: string
      description: "Kubernetes version for EKS cluster"
      default: "1.27"

    node_instance_types:
      type: array
      description: "EC2 instance types for primary node group"
      default: ["t3.medium"]

    spot_instance_types:
      type: array
      description: "EC2 instance types for spot node group"
      default: ["t3.medium", "t3.large"]

    node_desired_size:
      type: number
      description: "Desired number of nodes in primary group"
      default: 2

    node_max_size:
      type: number
      description: "Maximum number of nodes in primary group"
      default: 5

    node_min_size:
      type: number
      description: "Minimum number of nodes in primary group"
      default: 1

    enable_spot_instances:
      type: boolean
      description: "Enable spot instance node group"
      default: false

    public_access_enabled:
      type: boolean
      description: "Enable public API server access"
      default: true

    public_access_cidrs:
      type: array
      description: "CIDR blocks for public API access"
      default: ["0.0.0.0/0"]

  dependencies:
    outputs_required:
      - network.subnet_info.private_subnet_ids
      - security.iam_role_arns.eks_cluster_role_arn
      - security.iam_role_arns.eks_node_group_role_arn
      - security.kms_key_ids.infrastructure_key_arn

  tags:
    - eks
    - kubernetes
    - orchestration
    - containers
    - compute
```