```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: compute-ec2
  version: v1
  description: EC2 instances, Auto Scaling Groups, Load Balancers, and compute infrastructure
  language: typescript
  priority: 140

spec:
  dependencies:
    - network
    - security
    - storage

  resources:
    key_pairs:
      main_key_pair:
        name: "${config.project}-${config.environment}-key"
        public_key: "${config.ssh_public_key}"

    launch_templates:
      web_server_template:
        name: "${config.project}-${config.environment}-web-template"
        description: "Launch template for web servers"
        image_id: "${config.ami_id}"
        instance_type: "${config.web_instance_type}"
        key_name: "${resources.key_pairs.main_key_pair.key_name}"
        vpc_security_group_ids: ["${deps.security.web_server_sg_id}"]
        iam_instance_profile:
          name: "${resources.iam.instance_profiles.web_server_profile.name}"
        block_device_mappings:
          - device_name: "/dev/xvda"
            ebs:
              volume_type: "gp3"
              volume_size: 20
              encrypted: true
              kms_key_id: "${deps.security.ebs_key_id}"
              delete_on_termination: true
        user_data: |
          #!/bin/bash
          yum update -y
          yum install -y amazon-cloudwatch-agent
          # Install application dependencies
          curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
          yum install -y nodejs
          # Configure CloudWatch agent
          /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
            -a fetch-config -m ec2 -s -c ssm:${resources.ssm.parameters.cloudwatch_config.name}
        tag_specifications:
          - resource_type: "instance"
            tags:
              Name: "${config.project}-${config.environment}-web-server"
              Environment: "${config.environment}"
              Project: "${config.project}"
              Backup: "Required"

      worker_server_template:
        name: "${config.project}-${config.environment}-worker-template"
        description: "Launch template for background worker servers"
        image_id: "${config.ami_id}"
        instance_type: "${config.worker_instance_type}"
        key_name: "${resources.key_pairs.main_key_pair.key_name}"
        vpc_security_group_ids: ["${deps.security.worker_server_sg_id}"]
        iam_instance_profile:
          name: "${resources.iam.instance_profiles.worker_server_profile.name}"
        user_data: |
          #!/bin/bash
          yum update -y
          yum install -y amazon-cloudwatch-agent
          # Install worker dependencies
          curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
          yum install -y nodejs redis

    auto_scaling_groups:
      web_server_asg:
        name: "${config.project}-${config.environment}-web-asg"
        launch_template:
          id: "${resources.launch_templates.web_server_template.id}"
          version: "$Latest"
        min_size: "${config.web_min_capacity}"
        max_size: "${config.web_max_capacity}"
        desired_capacity: "${config.web_desired_capacity}"
        vpc_zone_identifier: "${deps.network.private_subnet_ids}"
        target_group_arns: ["${resources.load_balancer.target_groups.web_targets.arn}"]
        health_check_type: "ELB"
        health_check_grace_period: 300
        default_cooldown: 300
        enabled_metrics:
          - "GroupMinSize"
          - "GroupMaxSize"
          - "GroupDesiredCapacity"
          - "GroupInServiceInstances"
          - "GroupTotalInstances"
        tags:
          - key: "Name"
            value: "${config.project}-${config.environment}-web-asg"
            propagate_at_launch: true
          - key: "Environment"
            value: "${config.environment}"
            propagate_at_launch: true

      worker_server_asg:
        name: "${config.project}-${config.environment}-worker-asg"
        launch_template:
          id: "${resources.launch_templates.worker_server_template.id}"
          version: "$Latest"
        min_size: "${config.worker_min_capacity}"
        max_size: "${config.worker_max_capacity}"
        desired_capacity: "${config.worker_desired_capacity}"
        vpc_zone_identifier: "${deps.network.private_subnet_ids}"
        health_check_type: "EC2"
        health_check_grace_period: 300

    auto_scaling_policies:
      web_scale_up:
        name: "${config.project}-${config.environment}-web-scale-up"
        scaling_adjustment: 1
        adjustment_type: "ChangeInCapacity"
        cooldown: 300
        autoscaling_group_name: "${resources.auto_scaling_groups.web_server_asg.name}"
        policy_type: "SimpleScaling"

      web_scale_down:
        name: "${config.project}-${config.environment}-web-scale-down"
        scaling_adjustment: -1
        adjustment_type: "ChangeInCapacity"
        cooldown: 300
        autoscaling_group_name: "${resources.auto_scaling_groups.web_server_asg.name}"
        policy_type: "SimpleScaling"

    load_balancer:
      application_load_balancer:
        name: "${config.project}-${config.environment}-alb"
        load_balancer_type: "application"
        scheme: "internet-facing"
        subnets: "${deps.network.public_subnet_ids}"
        security_groups: ["${deps.security.alb_sg_id}"]
        enable_deletion_protection: "${config.enable_deletion_protection}"

      target_groups:
        web_targets:
          name: "${config.project}-${config.environment}-web-tg"
          port: 3000
          protocol: "HTTP"
          vpc_id: "${deps.network.vpc_id}"
          target_type: "instance"
          health_check:
            enabled: true
            healthy_threshold: 2
            interval: 30
            matcher: "200"
            path: "/health"
            port: "traffic-port"
            protocol: "HTTP"
            timeout: 5
            unhealthy_threshold: 2

      listeners:
        https_listener:
          load_balancer_arn: "${resources.load_balancer.application_load_balancer.arn}"
          port: 443
          protocol: "HTTPS"
          ssl_policy: "ELBSecurityPolicy-TLS-1-2-2017-01"
          certificate_arn: "${deps.dns.primary_certificate_arn}"
          default_actions:
            - type: "forward"
              target_group_arn: "${resources.load_balancer.target_groups.web_targets.arn}"

        http_listener:
          load_balancer_arn: "${resources.load_balancer.application_load_balancer.arn}"
          port: 80
          protocol: "HTTP"
          default_actions:
            - type: "redirect"
              redirect:
                port: "443"
                protocol: "HTTPS"
                status_code: "HTTP_301"

    iam:
      roles:
        web_server_role:
          name: "${config.project}-${config.environment}-web-server-role"
          assume_role_policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": {
                    "Service": "ec2.amazonaws.com"
                  },
                  "Action": "sts:AssumeRole"
                }
              ]
            }
          managed_policy_arns:
            - "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
            - "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"

        worker_server_role:
          name: "${config.project}-${config.environment}-worker-server-role"
          assume_role_policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": {
                    "Service": "ec2.amazonaws.com"
                  },
                  "Action": "sts:AssumeRole"
                }
              ]
            }

      policies:
        s3_access_policy:
          name: "${config.project}-${config.environment}-s3-access"
          policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                  ],
                  "Resource": [
                    "${deps.storage.primary_bucket_arn}/*",
                    "${deps.storage.static_assets_bucket_arn}/*"
                  ]
                }
              ]
            }

      role_policy_attachments:
        web_s3_policy:
          role: "${resources.iam.roles.web_server_role.name}"
          policy_arn: "${resources.iam.policies.s3_access_policy.arn}"

        worker_s3_policy:
          role: "${resources.iam.roles.worker_server_role.name}"
          policy_arn: "${resources.iam.policies.s3_access_policy.arn}"

      instance_profiles:
        web_server_profile:
          name: "${config.project}-${config.environment}-web-server-profile"
          role: "${resources.iam.roles.web_server_role.name}"

        worker_server_profile:
          name: "${config.project}-${config.environment}-worker-server-profile"
          role: "${resources.iam.roles.worker_server_role.name}"

    cloudwatch:
      metric_alarms:
        web_cpu_high:
          alarm_name: "${config.project}-${config.environment}-web-cpu-high"
          comparison_operator: "GreaterThanThreshold"
          evaluation_periods: 2
          metric_name: "CPUUtilization"
          namespace: "AWS/AutoScaling"
          period: 60
          statistic: "Average"
          threshold: 80
          alarm_description: "This metric monitors web server cpu utilization"
          alarm_actions: ["${resources.auto_scaling_policies.web_scale_up.arn}"]
          dimensions:
            AutoScalingGroupName: "${resources.auto_scaling_groups.web_server_asg.name}"

        web_cpu_low:
          alarm_name: "${config.project}-${config.environment}-web-cpu-low"
          comparison_operator: "LessThanThreshold"
          evaluation_periods: 2
          metric_name: "CPUUtilization"
          namespace: "AWS/AutoScaling"
          period: 60
          statistic: "Average"
          threshold: 20
          alarm_description: "This metric monitors web server cpu utilization"
          alarm_actions: ["${resources.auto_scaling_policies.web_scale_down.arn}"]
          dimensions:
            AutoScalingGroupName: "${resources.auto_scaling_groups.web_server_asg.name}"

    ssm:
      parameters:
        cloudwatch_config:
          name: "/${config.project}/${config.environment}/cloudwatch-config"
          type: "String"
          value: |
            {
              "metrics": {
                "namespace": "${config.project}/${config.environment}",
                "metrics_collected": {
                  "cpu": {
                    "measurement": ["cpu_usage_idle", "cpu_usage_iowait", "cpu_usage_user", "cpu_usage_system"],
                    "metrics_collection_interval": 60
                  },
                  "disk": {
                    "measurement": ["used_percent"],
                    "metrics_collection_interval": 60,
                    "resources": ["*"]
                  },
                  "mem": {
                    "measurement": ["mem_used_percent"],
                    "metrics_collection_interval": 60
                  }
                }
              },
              "logs": {
                "logs_collected": {
                  "files": {
                    "collect_list": [
                      {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/${config.project}/${config.environment}/system",
                        "log_stream_name": "{instance_id}"
                      }
                    ]
                  }
                }
              }
            }

  outputs:
    compute_info:
      web_asg_name:
        description: "Web servers Auto Scaling Group name"
        value: "${resources.auto_scaling_groups.web_server_asg.name}"

      worker_asg_name:
        description: "Worker servers Auto Scaling Group name"
        value: "${resources.auto_scaling_groups.worker_server_asg.name}"

      alb_dns_name:
        description: "Application Load Balancer DNS name"
        value: "${resources.load_balancer.application_load_balancer.dns_name}"

      alb_arn:
        description: "Application Load Balancer ARN"
        value: "${resources.load_balancer.application_load_balancer.arn}"

      alb_zone_id:
        description: "Application Load Balancer hosted zone ID"
        value: "${resources.load_balancer.application_load_balancer.zone_id}"

    iam_info:
      web_server_role_arn:
        description: "Web server IAM role ARN"
        value: "${resources.iam.roles.web_server_role.arn}"

      worker_server_role_arn:
        description: "Worker server IAM role ARN"
        value: "${resources.iam.roles.worker_server_role.arn}"

  parameters:
    region:
      type: string
      description: "AWS region for deployment"
      required: true
      default: "${AWS_REGION}"

    project:
      type: string
      description: "Project name for resource naming"
      required: true
      default: "${PROJECT_NAME}"

    environment:
      type: string
      description: "Environment name (dev, stage, prod)"
      required: true
      validation:
        allowed_values: ["dev", "stage", "prod"]

    ami_id:
      type: string
      description: "AMI ID for EC2 instances"
      required: true
      default: "ami-0abcdef1234567890" # Amazon Linux 2

    ssh_public_key:
      type: string
      description: "SSH public key for instance access"
      required: true

    web_instance_type:
      type: string
      description: "Instance type for web servers"
      default: "t3.small"
      validation:
        allowed_values: ["t3.micro", "t3.small", "t3.medium", "t3.large"]

    worker_instance_type:
      type: string
      description: "Instance type for worker servers"
      default: "t3.small"

    web_min_capacity:
      type: number
      description: "Minimum number of web server instances"
      default: 1
      validation:
        minimum: 1
        maximum: 10

    web_max_capacity:
      type: number
      description: "Maximum number of web server instances"
      default: 5
      validation:
        minimum: 1
        maximum: 20

    web_desired_capacity:
      type: number
      description: "Desired number of web server instances"
      default: 2

    worker_min_capacity:
      type: number
      description: "Minimum number of worker server instances"
      default: 1

    worker_max_capacity:
      type: number
      description: "Maximum number of worker server instances"
      default: 3

    worker_desired_capacity:
      type: number
      description: "Desired number of worker server instances"
      default: 1

    enable_deletion_protection:
      type: boolean
      description: "Enable deletion protection for ALB"
      default: false

  dependencies:
    outputs_required:
      - network.vpc_id
      - network.public_subnet_ids
      - network.private_subnet_ids
      - security.web_server_sg_id
      - security.worker_server_sg_id
      - security.alb_sg_id
      - security.ebs_key_id
      - storage.primary_bucket_arn
      - storage.static_assets_bucket_arn
      - dns.primary_certificate_arn

  tags:
    - compute
    - ec2
    - autoscaling
    - loadbalancer
    - infrastructure
    - application
```