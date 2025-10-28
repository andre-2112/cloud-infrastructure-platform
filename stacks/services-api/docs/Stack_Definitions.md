```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: services-api
  version: v1
  description: API Gateway, REST APIs, GraphQL APIs, and API management
  language: typescript
  priority: 130

spec:
  dependencies:
    - network
    - security
    - authentication
    - containers-apps

  resources:
    api_gateway:
      rest_apis:
        primary_api:
          name: "${config.project}-${config.environment}-api"
          description: "Primary REST API for ${config.project}"
          endpoint_configuration:
            types: ["REGIONAL"]
          policy: |
            {
              "Version": "2012-10-17",
              "Statement": [
                {
                  "Effect": "Allow",
                  "Principal": "*",
                  "Action": "execute-api:Invoke",
                  "Resource": "*"
                }
              ]
            }

        admin_api:
          name: "${config.project}-${config.environment}-admin-api"
          description: "Admin API for management operations"
          endpoint_configuration:
            types: ["REGIONAL"]

      authorizers:
        cognito_authorizer:
          name: "${config.project}-${config.environment}-cognito-auth"
          rest_api_ref: primary_api
          type: "COGNITO_USER_POOLS"
          provider_arns: ["${deps.authentication.user_pool_arn}"]
          identity_source: "method.request.header.Authorization"

      resources:
        api_v1:
          rest_api_ref: primary_api
          parent_id: "root"
          path_part: "v1"

        users_resource:
          rest_api_ref: primary_api
          parent_ref: api_v1
          path_part: "users"

        orders_resource:
          rest_api_ref: primary_api
          parent_ref: api_v1
          path_part: "orders"

        products_resource:
          rest_api_ref: primary_api
          parent_ref: api_v1
          path_part: "products"

      methods:
        users_get:
          rest_api_ref: primary_api
          resource_ref: users_resource
          http_method: "GET"
          authorization: "COGNITO_USER_POOLS"
          authorizer_ref: cognito_authorizer

        users_post:
          rest_api_ref: primary_api
          resource_ref: users_resource
          http_method: "POST"
          authorization: "COGNITO_USER_POOLS"
          authorizer_ref: cognito_authorizer

        orders_get:
          rest_api_ref: primary_api
          resource_ref: orders_resource
          http_method: "GET"
          authorization: "COGNITO_USER_POOLS"
          authorizer_ref: cognito_authorizer

        products_get:
          rest_api_ref: primary_api
          resource_ref: products_resource
          http_method: "GET"
          authorization: "NONE"

      integrations:
        users_get_integration:
          rest_api_ref: primary_api
          resource_ref: users_resource
          http_method: "GET"
          integration_http_method: "GET"
          type: "HTTP_PROXY"
          uri: "http://${deps.containers_apps.private_alb_dns_name}/api/users"
          connection_type: "VPC_LINK"
          connection_id: "${resources.api_gateway.vpc_links.main_vpc_link.id}"

        orders_get_integration:
          rest_api_ref: primary_api
          resource_ref: orders_resource
          http_method: "GET"
          integration_http_method: "GET"
          type: "HTTP_PROXY"
          uri: "http://${deps.containers_apps.private_alb_dns_name}/api/orders"
          connection_type: "VPC_LINK"
          connection_id: "${resources.api_gateway.vpc_links.main_vpc_link.id}"

      vpc_links:
        main_vpc_link:
          name: "${config.project}-${config.environment}-vpc-link"
          description: "VPC Link to internal ALB"
          target_arns: ["${deps.containers_apps.private_alb_arn}"]

      deployments:
        primary_deployment:
          rest_api_ref: primary_api
          stage_name: "${config.environment}"
          stage_description: "API deployment for ${config.environment}"

      usage_plans:
        standard_plan:
          name: "${config.project}-${config.environment}-standard"
          description: "Standard usage plan"
          api_stages:
            - api_ref: primary_api
              stage: "${config.environment}"
          quota_settings:
            limit: 10000
            period: "MONTH"
          throttle_settings:
            rate_limit: 100
            burst_limit: 200

    api_gateway_v2:
      apis:
        http_api:
          name: "${config.project}-${config.environment}-http-api"
          description: "High-performance HTTP API"
          protocol_type: "HTTP"
          cors_configuration:
            allow_credentials: true
            allow_headers: ["content-type", "authorization"]
            allow_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            allow_origins: ["https://${config.domain}"]
            max_age: 300

      stages:
        http_api_stage:
          api_ref: http_api
          name: "${config.environment}"
          auto_deploy: true
          access_log_settings:
            destination_arn: "${resources.cloudwatch.log_groups.http_api_logs.arn}"
            format: "$requestId $requestTime $httpMethod $routeKey $status"

      integrations:
        http_alb_integration:
          api_ref: http_api
          integration_type: "HTTP_PROXY"
          integration_uri: "${deps.containers_apps.private_alb_listener_arn}"
          integration_method: "ANY"
          connection_type: "VPC_LINK"
          connection_id: "${resources.api_gateway_v2.vpc_links.http_vpc_link.id}"

      vpc_links:
        http_vpc_link:
          name: "${config.project}-${config.environment}-http-vpc-link"
          security_group_ids: ["${deps.security.api_gateway_sg_id}"]
          subnet_ids: "${deps.network.private_subnet_ids}"

      routes:
        catch_all_route:
          api_ref: http_api
          route_key: "ANY /{proxy+}"
          target: "integrations/${resources.api_gateway_v2.integrations.http_alb_integration.id}"

    cloudfront:
      distributions:
        api_cdn:
          name: "${config.project}-${config.environment}-api-cdn"
          origins:
            - domain_name: "${resources.api_gateway.rest_apis.primary_api.id}.execute-api.${config.region}.amazonaws.com"
              origin_id: "api-gateway-origin"
              origin_path: "/${config.environment}"
              custom_origin_config:
                http_port: 80
                https_port: 443
                origin_protocol_policy: "https-only"
                origin_ssl_protocols: ["TLSv1.2"]
          default_cache_behavior:
            target_origin_id: "api-gateway-origin"
            viewer_protocol_policy: "redirect-to-https"
            allowed_methods: ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
            cached_methods: ["GET", "HEAD", "OPTIONS"]
            compress: true
            cache_policy_id: "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled

    route53:
      records:
        api_record:
          zone_id: "${deps.dns.hosted_zone_id}"
          name: "api.${config.domain}"
          type: "A"
          alias:
            name: "${resources.cloudfront.distributions.api_cdn.domain_name}"
            zone_id: "${resources.cloudfront.distributions.api_cdn.hosted_zone_id}"
            evaluate_target_health: false

        admin_api_record:
          zone_id: "${deps.dns.hosted_zone_id}"
          name: "admin-api.${config.domain}"
          type: "A"
          alias:
            name: "${resources.api_gateway.rest_apis.admin_api.id}.execute-api.${config.region}.amazonaws.com"
            zone_id: "Z1UJRXOUMOOFQ8" # API Gateway hosted zone ID for us-east-1
            evaluate_target_health: true

    waf:
      web_acls:
        api_protection:
          name: "${config.project}-${config.environment}-api-waf"
          scope: "CLOUDFRONT"
          default_action:
            allow: {}
          rules:
            - name: "RateLimitRule"
              priority: 1
              action:
                block: {}
              statement:
                rate_based_statement:
                  limit: 2000
                  aggregate_key_type: "IP"
              visibility_config:
                sampled_requests_enabled: true
                cloudwatch_metrics_enabled: true
                metric_name: "RateLimitRule"

      web_acl_associations:
        api_cdn_association:
          resource_arn: "${resources.cloudfront.distributions.api_cdn.arn}"
          web_acl_arn: "${resources.waf.web_acls.api_protection.arn}"

    cloudwatch:
      log_groups:
        api_gateway_logs:
          name: "/aws/apigateway/${config.project}-${config.environment}"
          retention_in_days: 14

        http_api_logs:
          name: "/aws/apigateway-v2/${config.project}-${config.environment}"
          retention_in_days: 14

      dashboards:
        api_dashboard:
          name: "${config.project}-${config.environment}-api-dashboard"
          dashboard_body: |
            {
              "widgets": [
                {
                  "type": "metric",
                  "properties": {
                    "metrics": [
                      ["AWS/ApiGateway", "Count", "ApiName", "${config.project}-${config.environment}-api"],
                      [".", "Latency", ".", "."],
                      [".", "4XXError", ".", "."],
                      [".", "5XXError", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "${config.region}",
                    "title": "API Gateway Metrics"
                  }
                }
              ]
            }

  outputs:
    api_info:
      primary_api_id:
        description: "Primary REST API ID"
        value: "${resources.api_gateway.rest_apis.primary_api.id}"

      primary_api_arn:
        description: "Primary REST API ARN"
        value: "${resources.api_gateway.rest_apis.primary_api.arn}"

      primary_api_endpoint:
        description: "Primary API endpoint URL"
        value: "https://${resources.api_gateway.rest_apis.primary_api.id}.execute-api.${config.region}.amazonaws.com/${config.environment}"

      http_api_id:
        description: "HTTP API ID"
        value: "${resources.api_gateway_v2.apis.http_api.id}"

      http_api_endpoint:
        description: "HTTP API endpoint URL"
        value: "${resources.api_gateway_v2.apis.http_api.api_endpoint}"

    dns_info:
      api_domain:
        description: "API custom domain"
        value: "api.${config.domain}"

      admin_api_domain:
        description: "Admin API custom domain"
        value: "admin-api.${config.domain}"

    cdn_info:
      api_cdn_domain_name:
        description: "API CloudFront distribution domain name"
        value: "${resources.cloudfront.distributions.api_cdn.domain_name}"

      api_cdn_distribution_id:
        description: "API CloudFront distribution ID"
        value: "${resources.cloudfront.distributions.api_cdn.id}"

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

    domain:
      type: string
      description: "Primary domain name"
      required: true
      default: "${DEPLOY_DOMAIN}"

    enable_waf:
      type: boolean
      description: "Enable WAF protection for APIs"
      default: true

    api_throttle_rate:
      type: number
      description: "API Gateway throttle rate limit"
      default: 100
      validation:
        minimum: 1
        maximum: 10000

    api_throttle_burst:
      type: number
      description: "API Gateway throttle burst limit"
      default: 200
      validation:
        minimum: 1
        maximum: 5000

  dependencies:
    outputs_required:
      - network.vpc_id
      - network.private_subnet_ids
      - security.api_gateway_sg_id
      - authentication.user_pool_arn
      - containers_apps.private_alb_dns_name
      - containers_apps.private_alb_arn
      - containers_apps.private_alb_listener_arn
      - dns.hosted_zone_id

  tags:
    - api
    - gateway
    - rest
    - graphql
    - services
    - integration
```