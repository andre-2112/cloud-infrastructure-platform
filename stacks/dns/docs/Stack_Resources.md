# AWS Resources for DNS Stack

## Route 53 Resources
- **aws.route53.Zone** - Hosted zone for primary domain (${DEPLOY_DOMAIN})
- **aws.route53.Zone** - Hosted zone for subdomains (if needed)
- **aws.route53.Record** - A record for apex domain
- **aws.route53.Record** - CNAME records for www subdomain
- **aws.route53.Record** - A records for API subdomains (api.${DEPLOY_DOMAIN})
- **aws.route53.Record** - A records for CDN subdomains (cdn.${DEPLOY_DOMAIN})
- **aws.route53.Record** - MX records for email (if needed)
- **aws.route53.Record** - TXT records for domain verification
- **aws.route53.HealthCheck** - Health checks for critical endpoints
- **aws.route53.HealthCheck** - Health check for API endpoints

## Certificate Manager Resources
- **aws.acm.Certificate** - Primary SSL certificate for domain
- **aws.acm.Certificate** - Wildcard SSL certificate for subdomains (*.${DEPLOY_DOMAIN})
- **aws.acm.CertificateValidation** - DNS validation for primary certificate
- **aws.acm.CertificateValidation** - DNS validation for wildcard certificate

## CloudFront (Optional)
- **aws.cloudfront.Distribution** - CDN distribution for static assets
- **aws.cloudfront.OriginAccessIdentity** - OAI for S3 bucket access

## Estimated Resource Count: 16 resources
## Estimated Monthly Cost: $2-5 (Route53 hosted zone + health checks)

## Resource Dependencies
- No dependencies (foundation stack)
- Must be deployed before load balancers that need SSL certificates