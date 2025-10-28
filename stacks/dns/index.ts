import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";
import { centralState, createResourceName, createResourceTags, validateConfig } from "../../shared";

// Stack configuration
const config = new pulumi.Config();
const deploymentConfig = centralState.getDeploymentConfig();

// Validate required configuration
validateConfig("dns", config, ["deployDomain"]);

const STACK_NAME = "dns";

// DNS Stack - Creates Route53 hosted zones and SSL certificates
console.log(`🚀 Deploying DNS Stack for domain: ${deploymentConfig.deployDomain}`);

// Create hosted zone for primary domain
const hostedZone = new aws.route53.Zone("primary-hosted-zone", {
    name: deploymentConfig.deployDomain,
    comment: `Hosted zone for ${deploymentConfig.deployDomain} - managed by ${deploymentConfig.projectName}`,
    tags: createResourceTags(deploymentConfig, "hosted-zone", {
        Domain: deploymentConfig.deployDomain,
        Type: "Primary"
    })
});

// Create SSL certificate for primary domain
const primaryCertificate = new aws.acm.Certificate("primary-certificate", {
    domainName: deploymentConfig.deployDomain,
    validationMethod: "DNS",
    lifecycle: {
        createBeforeDestroy: true
    },
    tags: createResourceTags(deploymentConfig, "certificate", {
        Domain: deploymentConfig.deployDomain,
        Type: "Primary"
    })
});

// Create wildcard SSL certificate
const wildcardCertificate = new aws.acm.Certificate("wildcard-certificate", {
    domainName: `*.${deploymentConfig.deployDomain}`,
    subjectAlternativeNames: [deploymentConfig.deployDomain],
    validationMethod: "DNS",
    lifecycle: {
        createBeforeDestroy: true
    },
    tags: createResourceTags(deploymentConfig, "certificate", {
        Domain: deploymentConfig.deployDomain,
        Type: "Wildcard"
    })
});

// DNS validation records for primary certificate
const primaryCertValidation = new aws.route53.Record("primary-cert-validation", {
    name: primaryCertificate.domainValidationOptions[0].resourceRecordName,
    records: [primaryCertificate.domainValidationOptions[0].resourceRecordValue],
    ttl: 60,
    type: primaryCertificate.domainValidationOptions[0].resourceRecordType,
    zoneId: hostedZone.zoneId
});

// DNS validation records for wildcard certificate
const wildcardCertValidation = new aws.route53.Record("wildcard-cert-validation", {
    name: wildcardCertificate.domainValidationOptions[0].resourceRecordName,
    records: [wildcardCertificate.domainValidationOptions[0].resourceRecordValue],
    ttl: 60,
    type: wildcardCertificate.domainValidationOptions[0].resourceRecordType,
    zoneId: hostedZone.zoneId
});

// Certificate validation completion
const primaryCertificateValidation = new aws.acm.CertificateValidation("primary-certificate-validation", {
    certificateArn: primaryCertificate.arn,
    validationRecordFqdns: [primaryCertValidation.fqdn]
});

const wildcardCertificateValidation = new aws.acm.CertificateValidation("wildcard-certificate-validation", {
    certificateArn: wildcardCertificate.arn,
    validationRecordFqdns: [wildcardCertValidation.fqdn]
});

// Create health check for primary domain
const primaryHealthCheck = new aws.route53.HealthCheck("primary-health-check", {
    fqdn: deploymentConfig.deployDomain,
    port: 443,
    type: "HTTPS",
    resourcePath: "/health",
    failureThreshold: 3,
    requestInterval: 30,
    tags: createResourceTags(deploymentConfig, "health-check", {
        Domain: deploymentConfig.deployDomain,
        Type: "Primary"
    })
});

// Create API health check
const apiHealthCheck = new aws.route53.HealthCheck("api-health-check", {
    fqdn: `api.${deploymentConfig.deployDomain}`,
    port: 443,
    type: "HTTPS",
    resourcePath: "/api/health",
    failureThreshold: 3,
    requestInterval: 30,
    tags: createResourceTags(deploymentConfig, "health-check", {
        Domain: `api.${deploymentConfig.deployDomain}`,
        Type: "API"
    })
});

// DNS records will be created by other stacks that need them (container-apps, etc.)
// This stack provides the foundation for DNS management

// Export stack outputs
export const hostedZoneId = hostedZone.zoneId;
export const hostedZoneName = hostedZone.name;
export const domainName = deploymentConfig.deployDomain;
export const nameServers = hostedZone.nameServers;

export const primaryCertificateArn = primaryCertificateValidation.certificateArn;
export const wildcardCertificateArn = wildcardCertificateValidation.certificateArn;

export const primaryHealthCheckId = primaryHealthCheck.id;
export const apiHealthCheckId = apiHealthCheck.id;

// Stack metadata
export const stackName = STACK_NAME;
export const deploymentId = deploymentConfig.deploymentId;
export const region = deploymentConfig.region;
export const __exists = true;

// Summary information
export const summary = {
    domain: deploymentConfig.deployDomain,
    certificates: {
        primary: primaryCertificateArn,
        wildcard: wildcardCertificateArn
    },
    healthChecks: {
        primary: primaryHealthCheckId,
        api: apiHealthCheckId
    },
    hostedZone: {
        id: hostedZoneId,
        nameServers: nameServers
    }
};