```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: services-ecr
  version: v1
  description: Enhanced ECR registry services with cross-region replication
  language: typescript
  priority: 100

spec:
  dependencies:
    - security

  resources:
    ecr_registry:
      scanning_configuration:
        scan_type: "ENHANCED"
        rules:
          - scan_frequency: "SCAN_ON_PUSH"
            repository_filters:
              - filter: "*"
                filter_type: "WILDCARD"

      replication_configuration:
        rules:
          - destinations:
              - region: "us-west-2"
                registry_id: "${data.aws_caller_identity.current.account_id}"
          repository_filters:
            - filter: "${config.project}/*"
              filter_type: "PREFIX_MATCH"

    ecr_repositories:
      base_images:
        name: "${config.project}/base-images"
        image_tag_mutability: "IMMUTABLE"
        encryption_configuration:
          encryption_type: "KMS"
          kms_key: "${deps.security.kms_key_ids.application_key_arn}"
        image_scanning_configuration:
          scan_on_push: true

    lifecycle_policies:
      base_images_lifecycle:
        repository: "${resources.ecr_repositories.base_images.name}"
        policy: |
          {
            "rules": [
              {
                "rulePriority": 1,
                "description": "Keep last 5 production images",
                "selection": {
                  "tagStatus": "tagged",
                  "tagPrefixList": ["prod-"],
                  "countType": "imageCountMoreThan",
                  "countNumber": 5
                },
                "action": {
                  "type": "expire"
                }
              }
            ]
          }

  outputs:
    registry_info:
      registry_id:
        description: "ECR registry ID"
        value: "${data.aws_caller_identity.current.account_id}"

      base_images_repo_url:
        description: "Base images repository URL"
        value: "${resources.ecr_repositories.base_images.repository_url}"

    replication_info:
      replication_enabled:
        description: "Cross-region replication status"
        value: true

      destination_regions:
        description: "Replication destination regions"
        value: ["us-west-2"]

  parameters:
    project:
      type: string
      description: "Project name for resource naming"
      required: true
      default: "${PROJECT_NAME}"

    enable_cross_region_replication:
      type: boolean
      description: "Enable cross-region ECR replication"
      default: false

    scanning_frequency:
      type: string
      description: "Image scanning frequency"
      default: "SCAN_ON_PUSH"
      validation:
        allowed_values: ["SCAN_ON_PUSH", "CONTINUOUS_SCAN"]

  dependencies:
    outputs_required:
      - security.kms_key_ids.application_key_arn

  tags:
    - ecr
    - registry
    - containers
    - replication
    - security
```