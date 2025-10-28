```yaml
apiVersion: v1
kind: StackDefinition
metadata:
  name: authentication
  version: v1
  description: Authentication and authorization with AWS Cognito
  language: typescript
  priority: 50

spec:
  dependencies:
    - security
    - secrets

  resources:
    cognito_user_pool:
      main_user_pool:
        name: "${config.project}-${config.environment}-users"
        alias_attributes: ["email", "preferred_username"]
        auto_verified_attributes: ["email"]
        password_policy:
          minimum_length: 12
          require_lowercase: true
          require_uppercase: true
          require_numbers: true
          require_symbols: true
          temporary_password_validity_days: 7
        mfa_configuration: "OPTIONAL"
        account_recovery_setting:
          recovery_mechanisms:
            - name: "verified_email"
              priority: 1
        tags:
          Name: "${config.project}-${config.environment}-user-pool"
          Environment: "${config.environment}"

    cognito_user_pool_clients:
      web_client:
        name: "${config.project}-${config.environment}-web-client"
        user_pool_id: "${resources.cognito_user_pool.main_user_pool.id}"
        generate_secret: false
        explicit_auth_flows:
          - "ALLOW_USER_SRP_AUTH"
          - "ALLOW_REFRESH_TOKEN_AUTH"
        supported_identity_providers: ["COGNITO", "Google", "GitHub"]
        callback_urls:
          - "https://${var.domain}/auth/callback"
          - "http://localhost:3000/auth/callback"
        logout_urls:
          - "https://${var.domain}/auth/logout"
          - "http://localhost:3000/auth/logout"

      mobile_client:
        name: "${config.project}-${config.environment}-mobile-client"
        user_pool_id: "${resources.cognito_user_pool.main_user_pool.id}"
        generate_secret: true
        explicit_auth_flows:
          - "ALLOW_USER_SRP_AUTH"
          - "ALLOW_REFRESH_TOKEN_AUTH"

    cognito_identity_pool:
      main_identity_pool:
        identity_pool_name: "${config.project}_${config.environment}_identity"
        allow_unauthenticated_identities: true
        cognito_identity_providers:
          - client_id: "${resources.cognito_user_pool_clients.web_client.id}"
            provider_name: "${resources.cognito_user_pool.main_user_pool.endpoint}"
            server_side_token_check: false

    cognito_identity_providers:
      google_provider:
        user_pool_id: "${resources.cognito_user_pool.main_user_pool.id}"
        provider_name: "Google"
        provider_type: "Google"
        provider_details:
          client_id: "${var.google_client_id}"
          client_secret: "${deps.secrets.external_api_keys.google_client_secret}"
          authorize_scopes: "email openid profile"

      github_provider:
        user_pool_id: "${resources.cognito_user_pool.main_user_pool.id}"
        provider_name: "GitHub"
        provider_type: "OIDC"
        provider_details:
          client_id: "${var.github_client_id}"
          client_secret: "${deps.secrets.external_api_keys.github_client_secret}"
          oidc_issuer: "https://github.com"
          authorize_scopes: "openid read:user user:email"

  outputs:
    user_pool_info:
      user_pool_id:
        description: "Cognito User Pool ID"
        value: "${resources.cognito_user_pool.main_user_pool.id}"

      user_pool_arn:
        description: "Cognito User Pool ARN"
        value: "${resources.cognito_user_pool.main_user_pool.arn}"

      user_pool_endpoint:
        description: "Cognito User Pool endpoint"
        value: "${resources.cognito_user_pool.main_user_pool.endpoint}"

    client_info:
      web_client_id:
        description: "Web application client ID"
        value: "${resources.cognito_user_pool_clients.web_client.id}"

      mobile_client_id:
        description: "Mobile application client ID"
        value: "${resources.cognito_user_pool_clients.mobile_client.id}"

      mobile_client_secret:
        description: "Mobile application client secret"
        value: "${resources.cognito_user_pool_clients.mobile_client.client_secret}"
        sensitive: true

    identity_pool_info:
      identity_pool_id:
        description: "Cognito Identity Pool ID"
        value: "${resources.cognito_identity_pool.main_identity_pool.id}"

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

    domain:
      type: string
      description: "Application domain name"
      required: true
      default: "${DEPLOY_DOMAIN}"

    enable_mfa:
      type: boolean
      description: "Enable multi-factor authentication"
      default: true

    password_minimum_length:
      type: number
      description: "Minimum password length"
      default: 12
      validation:
        minimum: 8
        maximum: 128

  dependencies:
    outputs_required:
      - secrets.secret_arns.external_api_keys_arn

  tags:
    - authentication
    - cognito
    - oauth
    - identity
    - security
```