```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: dns
  version: v1
  description: DNS management with Route53 and SSL certificates
  language: typescript
  priority: 10

spec:
  dependencies: []

  resources:
    route53:
      hosted_zones:
        primary_zone:
          name: "${config.domain}"
          domain: "${config.domain}"
          comment: "Primary hosted zone for ${config.project} ${config.environment}"
          private_zone: false
          force_destroy: false

      records:
        apex_record:
          zone_ref: primary_zone
          name: ""
          type: A
          alias:
            name: "${deps.loadbalancer.public_alb_dns_name}"
            zone_id: "${deps.loadbalancer.public_alb_zone_id}"
            evaluate_target_health: true

        www_record:
          zone_ref: primary_zone
          name: "www"
          type: CNAME
          ttl: 300
          records: ["${config.domain}"]

        api_record:
          zone_ref: primary_zone
          name: "api"
          type: A
          alias:
            name: "${deps.loadbalancer.internal_alb_dns_name}"
            zone_id: "${deps.loadbalancer.internal_alb_zone_id}"
            evaluate_target_health: true

        cdn_record:
          zone_ref: primary_zone
          name: "cdn"
          type: A
          alias:
            name: "${deps.cloudfront.distribution_domain_name}"
            zone_id: "${deps.cloudfront.distribution_zone_id}"
            evaluate_target_health: false

      health_checks:
        primary_endpoint_check:
          name: "${config.project}-${config.environment}-primary-health"
          fqdn: "${config.domain}"
          type: HTTPS
          port: 443
          resource_path: "/health"
          failure_threshold: 3
          request_interval: 30

        api_endpoint_check:
          name: "${config.project}-${config.environment}-api-health"
          fqdn: "api.${config.domain}"
          type: HTTPS
          port: 443
          resource_path: "/health"
          failure_threshold: 3
          request_interval: 30

    acm:
      certificates:
        primary_cert:
          name: "${config.project}-${config.environment}-primary-cert"
          domain_name: "${config.domain}"
          subject_alternative_names:
            - "*.${config.domain}"
          validation_method: DNS
          lifecycle:
            create_before_destroy: true
          tags:
            Name: "${config.project}-${config.environment}-primary-cert"
            Environment: "${config.environment}"
            Purpose: "Primary SSL certificate"

        wildcard_cert:
          name: "${config.project}-${config.environment}-wildcard-cert"
          domain_name: "*.${config.domain}"
          validation_method: DNS
          lifecycle:
            create_before_destroy: true
          tags:
            Name: "${config.project}-${config.environment}-wildcard-cert"
            Environment: "${config.environment}"
            Purpose: "Wildcard SSL certificate"

  outputs:
    hosted_zone_info:
      hosted_zone_id:
        description: "Primary hosted zone ID"
        value: "${resources.route53.hosted_zones.primary_zone.zone_id}"

      hosted_zone_name_servers:
        description: "Name servers for domain delegation"
        value: "${resources.route53.hosted_zones.primary_zone.name_servers}"

      domain_name:
        description: "Primary domain name"
        value: "${config.domain}"

    certificate_info:
      primary_certificate_arn:
        description: "Primary SSL certificate ARN"
        value: "${resources.acm.certificates.primary_cert.arn}"

      wildcard_certificate_arn:
        description: "Wildcard SSL certificate ARN"
        value: "${resources.acm.certificates.wildcard_cert.arn}"

      domain_validation_options:
        description: "DNS validation records for certificates"
        value: "${resources.acm.certificates.primary_cert.domain_validation_options}"

    health_checks:
      primary_health_check_id:
        description: "Primary endpoint health check ID"
        value: "${resources.route53.health_checks.primary_endpoint_check.id}"

      api_health_check_id:
        description: "API endpoint health check ID"
        value: "${resources.route53.health_checks.api_endpoint_check.id}"

    dns_records:
      apex_record_fqdn:
        description: "Apex domain FQDN"
        value: "${resources.route53.records.apex_record.fqdn}"

      www_record_fqdn:
        description: "WWW subdomain FQDN"
        value: "${resources.route53.records.www_record.fqdn}"

      api_record_fqdn:
        description: "API subdomain FQDN"
        value: "${resources.route53.records.api_record.fqdn}"

  parameters:
    domain:
      type: string
      description: "Primary domain name (e.g., ${DEPLOY_DOMAIN})"
      required: true
      validation:
        pattern: "^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\\.[a-z]{2,}$"

    project:
      type: string
      description: "Project name for tagging and naming"
      required: true
      default: "${PROJECT_NAME}"

    environment:
      type: string
      description: "Environment name (dev, stage, prod)"
      required: true
      validation:
        allowed_values: ["dev", "stage", "prod"]

    enable_health_checks:
      type: boolean
      description: "Enable Route53 health checks for monitoring"
      default: true

    health_check_regions:
      type: array
      description: "AWS regions for health check monitoring"
      default: ["us-east-1", "us-west-2", "eu-west-1"]

    ttl_default:
      type: number
      description: "Default TTL for DNS records in seconds"
      default: 300
      validation:
        minimum: 60
        maximum: 86400

  dependencies:
    outputs_required: []

  tags:
    - dns
    - ssl
    - route53
    - certificates
    - foundation
    - networking
```