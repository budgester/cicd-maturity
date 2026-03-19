RECOMMENDATIONS = {
    "version_control": {
        2: {
            "priority": "high",
            "title": "Get everything into version control",
            "description": "All application code, configuration, and infrastructure scripts must be in VCS.",
            "actions": [
                "Audit all artefacts and identify what is not in VCS",
                "Move infrastructure scripts and config files into the repository",
                "Establish a policy: if it's not in VCS, it doesn't exist",
            ],
            "reference": "Continuous Delivery, Ch. 2 - Configuration Management",
        },
        3: {
            "priority": "medium",
            "title": "Adopt a consistent branching strategy",
            "description": "Move towards trunk-based development with short-lived branches.",
            "actions": [
                "Document and agree on a branching strategy",
                "Set up branch protection rules and required reviews",
                "Aim for branches that live less than one day",
            ],
            "reference": "Continuous Delivery, Ch. 14 - Advanced Version Control",
        },
        4: {
            "priority": "low",
            "title": "Achieve infrastructure-as-code maturity",
            "description": "All environments should be reproducible from version control alone.",
            "actions": [
                "Adopt IaC tools (Terraform, Pulumi, or CloudFormation)",
                "Version control database schemas and migration scripts",
                "Automate environment provisioning from VCS",
            ],
            "reference": "Continuous Delivery, Ch. 11 - Managing Infrastructure",
        },
        5: {
            "priority": "low",
            "title": "Trunk-based development with feature flags",
            "description": "Eliminate long-lived branches entirely; use feature flags for incomplete work.",
            "actions": [
                "Implement a feature flag system",
                "Practice continuous integration to trunk",
                "Remove feature flags once features are fully rolled out",
            ],
            "reference": "Continuous Delivery, Ch. 14 - Advanced Version Control",
        },
    },
    "build_process": {
        2: {
            "priority": "high",
            "title": "Automate the build on every commit",
            "description": "Set up CI to trigger a build on every push to the repository.",
            "actions": [
                "Choose a CI server (Jenkins, GitHub Actions, GitLab CI)",
                "Create a build script that runs on every commit",
                "Make the build self-testing — fail on test failures",
            ],
            "reference": "Continuous Delivery, Ch. 3 - Continuous Integration",
        },
        3: {
            "priority": "medium",
            "title": "Speed up the build",
            "description": "Target a build time under 10 minutes to maintain fast feedback.",
            "actions": [
                "Profile the build to find bottlenecks",
                "Parallelise test execution",
                "Use build caching and incremental compilation",
            ],
            "reference": "Continuous Delivery, Ch. 3 - Continuous Integration",
        },
        4: {
            "priority": "medium",
            "title": "Make builds hermetic and reproducible",
            "description": "Ensure builds produce identical output regardless of environment.",
            "actions": [
                "Containerise the build environment",
                "Pin all dependency versions",
                "Verify builds are reproducible by running on clean environments",
            ],
            "reference": "Continuous Delivery, Ch. 6 - Build and Deployment Scripting",
        },
        5: {
            "priority": "low",
            "title": "Optimise with incremental and cached builds",
            "description": "Use remote caching and incremental builds for sub-5-minute feedback.",
            "actions": [
                "Implement remote build caching",
                "Use incremental build tools",
                "Monitor build times and set alerts for regressions",
            ],
            "reference": "Continuous Delivery, Ch. 6 - Build and Deployment Scripting",
        },
    },
    "testing": {
        2: {
            "priority": "high",
            "title": "Establish a unit test foundation",
            "description": "Start with unit tests for critical business logic.",
            "actions": [
                "Set up a test framework and make tests easy to run",
                "Write tests for the most critical and complex code paths",
                "Add test execution to the CI pipeline",
            ],
            "reference": "Continuous Delivery, Ch. 4 - Implementing a Testing Strategy",
        },
        3: {
            "priority": "high",
            "title": "Build the test pyramid",
            "description": "Add integration and acceptance tests while maintaining fast unit tests.",
            "actions": [
                "Automate integration tests for key service interactions",
                "Add acceptance tests for critical user journeys",
                "Ensure the test pyramid shape — many unit, fewer integration, few E2E",
            ],
            "reference": "Continuous Delivery, Ch. 4 - Implementing a Testing Strategy",
        },
        4: {
            "priority": "medium",
            "title": "Add performance and non-functional testing",
            "description": "Include performance, security, and accessibility testing in the pipeline.",
            "actions": [
                "Set up automated performance tests with baselines",
                "Add performance gates to the CI pipeline",
                "Track performance trends over time",
            ],
            "reference": "Continuous Delivery, Ch. 9 - Testing Non-Functional Requirements",
        },
        5: {
            "priority": "low",
            "title": "Practise TDD and continuous testing",
            "description": "Tests drive design; coverage is a natural by-product.",
            "actions": [
                "Adopt test-driven development practices",
                "Use mutation testing to validate test quality",
                "Implement continuous performance benchmarking",
            ],
            "reference": "Continuous Delivery, Ch. 4 - Implementing a Testing Strategy",
        },
    },
    "deployment": {
        2: {
            "priority": "high",
            "title": "Automate the deployment process",
            "description": "Create a repeatable, scripted deployment that anyone can run.",
            "actions": [
                "Script the entire deployment process end to end",
                "Automate deployment to at least one environment",
                "Document and test the rollback procedure",
            ],
            "reference": "Continuous Delivery, Ch. 6 - Build and Deployment Scripting",
        },
        3: {
            "priority": "high",
            "title": "Deploy to production with one command",
            "description": "Remove manual steps and gate production deploys on automated checks.",
            "actions": [
                "Implement one-click deployment to production",
                "Add automated smoke tests after deployment",
                "Practise deploying small changes frequently",
            ],
            "reference": "Continuous Delivery, Ch. 10 - Deploying and Releasing Applications",
        },
        4: {
            "priority": "medium",
            "title": "Achieve zero-downtime deployments",
            "description": "Use blue-green or canary deployments to eliminate downtime.",
            "actions": [
                "Implement blue-green or rolling deployment strategy",
                "Add automated canary analysis",
                "Test rollback procedures regularly",
            ],
            "reference": "Continuous Delivery, Ch. 10 - Deploying and Releasing Applications",
        },
        5: {
            "priority": "low",
            "title": "Continuous deployment with progressive delivery",
            "description": "Every green build goes to production with feature flags and traffic shifting.",
            "actions": [
                "Implement continuous deployment pipeline",
                "Use feature flags for progressive rollout",
                "Implement automated traffic shifting based on metrics",
            ],
            "reference": "Continuous Delivery, Ch. 10 - Deploying and Releasing Applications",
        },
    },
    "monitoring": {
        2: {
            "priority": "high",
            "title": "Centralise logging",
            "description": "Aggregate logs in a central, searchable system.",
            "actions": [
                "Set up a log aggregation tool (ELK, Loki, CloudWatch)",
                "Use structured logging (JSON) in all services",
                "Add correlation IDs to trace requests across services",
            ],
            "reference": "Continuous Delivery, Ch. 12 - Managing Data",
        },
        3: {
            "priority": "medium",
            "title": "Implement application metrics and dashboards",
            "description": "Collect and visualise application-level metrics.",
            "actions": [
                "Instrument key application metrics (latency, errors, throughput)",
                "Create dashboards for each service",
                "Set up basic alerting on error rates and latency",
            ],
            "reference": "Accelerate, Ch. 7 - Management Practices for Software",
        },
        4: {
            "priority": "medium",
            "title": "Define SLOs and error budgets",
            "description": "Move from reactive monitoring to proactive SLO-based observability.",
            "actions": [
                "Define SLOs for critical user journeys",
                "Implement error budget tracking",
                "Alert on SLO burn rate rather than static thresholds",
            ],
            "reference": "Accelerate, Ch. 7 - Management Practices for Software",
        },
        5: {
            "priority": "low",
            "title": "Full observability with automated remediation",
            "description": "Integrate logs, metrics, and traces; automate responses to common failures.",
            "actions": [
                "Implement distributed tracing across all services",
                "Build automated runbooks for common incidents",
                "Use AIOps or anomaly detection for proactive alerting",
            ],
            "reference": "Accelerate, Ch. 7 - Management Practices for Software",
        },
    },
    "security": {
        2: {
            "priority": "high",
            "title": "Integrate security scanning into the pipeline",
            "description": "Add automated security checks to the CI process.",
            "actions": [
                "Add a SAST tool to the CI pipeline",
                "Enable dependency vulnerability scanning",
                "Remove any secrets from version control",
            ],
            "reference": "Continuous Delivery, Ch. 15 - Managing Continuous Delivery",
        },
        3: {
            "priority": "medium",
            "title": "Implement secrets management",
            "description": "Use a dedicated secrets manager instead of environment variables.",
            "actions": [
                "Adopt a secrets management tool (Vault, AWS Secrets Manager)",
                "Rotate credentials on a regular schedule",
                "Audit who has access to secrets",
            ],
            "reference": "Continuous Delivery, Ch. 2 - Configuration Management",
        },
        4: {
            "priority": "medium",
            "title": "Shift security left",
            "description": "Make security findings block builds; add DAST to staging.",
            "actions": [
                "Configure SAST to block merges on critical findings",
                "Add DAST scanning to staging deployments",
                "Automate dependency update PRs with SLA on patching",
            ],
            "reference": "Accelerate, Ch. 6 - Integrating Security",
        },
        5: {
            "priority": "low",
            "title": "Zero-trust security with automated compliance",
            "description": "Workload identity, automated rotation, and audit trails.",
            "actions": [
                "Implement workload identity (no long-lived credentials)",
                "Automate compliance checks and evidence collection",
                "Run chaos security exercises regularly",
            ],
            "reference": "Accelerate, Ch. 6 - Integrating Security",
        },
    },
    "configuration_management": {
        2: {
            "priority": "high",
            "title": "Version control all configuration",
            "description": "Move configuration out of manual processes and into version control.",
            "actions": [
                "Identify all configuration that is managed manually",
                "Move configuration files into the repository",
                "Establish a review process for config changes",
            ],
            "reference": "Continuous Delivery, Ch. 2 - Configuration Management",
        },
        3: {
            "priority": "medium",
            "title": "Achieve environment parity",
            "description": "Make dev, staging, and production as similar as possible.",
            "actions": [
                "Use the same provisioning tools for all environments",
                "Minimise differences to only environment-specific config values",
                "Use containers or VMs to standardise runtime environments",
            ],
            "reference": "Continuous Delivery, Ch. 11 - Managing Infrastructure",
        },
        4: {
            "priority": "medium",
            "title": "Separate configuration from application code",
            "description": "Externalise all config; inject at deployment time.",
            "actions": [
                "Use environment variables or config services for all settings",
                "Implement feature flags for runtime configuration",
                "Ensure config changes don't require a code redeploy",
            ],
            "reference": "Continuous Delivery, Ch. 2 - Configuration Management",
        },
        5: {
            "priority": "low",
            "title": "GitOps with drift detection",
            "description": "All config changes via merge to main; automated drift detection.",
            "actions": [
                "Implement GitOps workflow for configuration",
                "Add drift detection and automated reconciliation",
                "Create ephemeral environments on demand from code",
            ],
            "reference": "Continuous Delivery, Ch. 11 - Managing Infrastructure",
        },
    },
    "feedback_loops": {
        2: {
            "priority": "high",
            "title": "Start measuring DORA metrics",
            "description": "Begin tracking the four key DORA metrics to establish a baseline.",
            "actions": [
                "Instrument deployment frequency tracking",
                "Measure lead time from commit to production",
                "Track MTTR and change failure rate for each release",
            ],
            "reference": "Accelerate, Ch. 2 - Measuring Performance",
        },
        3: {
            "priority": "high",
            "title": "Reduce lead time for changes",
            "description": "Target getting changes to production within a week.",
            "actions": [
                "Identify bottlenecks in the delivery pipeline",
                "Reduce batch sizes — smaller, more frequent releases",
                "Automate manual approval steps where safe",
            ],
            "reference": "Accelerate, Ch. 2 - Measuring Performance",
        },
        4: {
            "priority": "medium",
            "title": "Improve MTTR with automated recovery",
            "description": "Target sub-hour recovery from production failures.",
            "actions": [
                "Implement automated rollback on failure detection",
                "Create runbooks for common failure scenarios",
                "Practise incident response with game days",
            ],
            "reference": "Accelerate, Ch. 2 - Measuring Performance",
        },
        5: {
            "priority": "low",
            "title": "Achieve elite DORA performance",
            "description": "Multiple deploys per day, sub-hour lead time, minutes to recover.",
            "actions": [
                "Implement continuous deployment",
                "Use progressive delivery for safe, frequent releases",
                "Drive change failure rate below 5% with pre-production testing",
            ],
            "reference": "Accelerate, Ch. 2 - Measuring Performance",
        },
    },
}


def get_recommendations(assessment):
    recs = []
    for dim, score in assessment.dimension_scores.items():
        if score and score < 5:
            next_level = score + 1
            dim_recs = RECOMMENDATIONS.get(dim, {})
            rec = dim_recs.get(next_level)
            if rec:
                recs.append({
                    "dimension": dim,
                    "current_score": score,
                    "target_level": next_level,
                    **rec,
                })
    recs.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r["priority"], 3))
    return recs


def get_next_level_guidance(dimension, current_score):
    if current_score >= 5:
        return None
    dim_recs = RECOMMENDATIONS.get(dimension, {})
    return dim_recs.get(current_score + 1)


def get_quick_wins(assessment):
    recs = get_recommendations(assessment)
    return recs[:3]
