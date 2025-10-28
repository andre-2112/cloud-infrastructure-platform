```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: containers-images
  version: v1
  description: Container image building and registry management with ECR
  language: typescript
  priority: 80

spec:
  dependencies:
    - security

  resources:
    ecr_repositories:
      frontend_repo:
        name: "${config.project}/${config.environment}/frontend"
        image_tag_mutability: "MUTABLE"
        image_scanning_configuration:
          scan_on_push: true
        encryption_configuration:
          encryption_type: "KMS"
          kms_key: "${deps.security.kms_key_ids.application_key_arn}"
        lifecycle_policy:
          rules:
            - rulePriority: 1
              selection:
                tagStatus: "untagged"
              action:
                type: "expire"
              description: "Delete untagged images older than 7 days"

      backend_repo:
        name: "${config.project}/${config.environment}/backend"
        image_tag_mutability: "MUTABLE"
        image_scanning_configuration:
          scan_on_push: true
        encryption_configuration:
          encryption_type: "KMS"
          kms_key: "${deps.security.kms_key_ids.application_key_arn}"

    codebuild_projects:
      frontend_build:
        name: "${config.project}-${config.environment}-frontend-build"
        service_role: "${resources.iam_roles.codebuild_role.arn}"
        artifacts:
          type: "NO_ARTIFACTS"
        environment:
          compute_type: "BUILD_GENERAL1_MEDIUM"
          image: "aws/codebuild/standard:5.0"
          type: "LINUX_CONTAINER"
          privileged_mode: true
          environment_variables:
            - name: "AWS_DEFAULT_REGION"
              value: "${var.region}"
            - name: "ECR_REPOSITORY_URI"
              value: "${resources.ecr_repositories.frontend_repo.repository_url}"
        source:
          type: "GITHUB"
          location: "${var.github_repo_url}"
          buildspec: |
            version: 0.2
            phases:
              pre_build:
                commands:
                  - echo Logging in to Amazon ECR...
                  - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
              build:
                commands:
                  - echo Build started on `date`
                  - echo Building the Docker image...
                  - docker build -t $ECR_REPOSITORY_URI:latest .
                  - docker tag $ECR_REPOSITORY_URI:latest $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION
              post_build:
                commands:
                  - echo Build completed on `date`
                  - echo Pushing the Docker images...
                  - docker push $ECR_REPOSITORY_URI:latest
                  - docker push $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION

    iam_roles:
      codebuild_role:
        name: "${config.project}-${config.environment}-codebuild-role"
        assume_role_policy: |
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "codebuild.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }
        managed_policy_arns:
          - "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
        inline_policies:
          - name: "ECRAccess"
            policy: |
              {
                "Version": "2012-10-17",
                "Statement": [
                  {
                    "Effect": "Allow",
                    "Action": [
                      "ecr:BatchCheckLayerAvailability",
                      "ecr:GetDownloadUrlForLayer",
                      "ecr:BatchGetImage",
                      "ecr:GetAuthorizationToken",
                      "ecr:InitiateLayerUpload",
                      "ecr:UploadLayerPart",
                      "ecr:CompleteLayerUpload",
                      "ecr:PutImage"
                    ],
                    "Resource": "*"
                  }
                ]
              }

  outputs:
    repository_info:
      frontend_repo_url:
        description: "Frontend ECR repository URL"
        value: "${resources.ecr_repositories.frontend_repo.repository_url}"

      backend_repo_url:
        description: "Backend ECR repository URL"
        value: "${resources.ecr_repositories.backend_repo.repository_url}"

      frontend_repo_arn:
        description: "Frontend ECR repository ARN"
        value: "${resources.ecr_repositories.frontend_repo.arn}"

      backend_repo_arn:
        description: "Backend ECR repository ARN"
        value: "${resources.ecr_repositories.backend_repo.arn}"

    build_info:
      frontend_build_project:
        description: "Frontend CodeBuild project name"
        value: "${resources.codebuild_projects.frontend_build.name}"

      codebuild_role_arn:
        description: "CodeBuild service role ARN"
        value: "${resources.iam_roles.codebuild_role.arn}"

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

    github_repo_url:
      type: string
      description: "GitHub repository URL for source code"
      required: true

    enable_image_scanning:
      type: boolean
      description: "Enable automatic image vulnerability scanning"
      default: true

    image_retention_count:
      type: number
      description: "Number of images to retain per repository"
      default: 10
      validation:
        minimum: 1
        maximum: 1000

  dependencies:
    outputs_required:
      - security.kms_key_ids.application_key_arn

  tags:
    - containers
    - ecr
    - docker
    - build
    - ci-cd
    - images
```