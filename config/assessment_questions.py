ASSESSMENT_DIMENSIONS = {
    "version_control": {
        "label": "Version Control",
        "description": "How effectively the team uses version control for all artefacts.",
        "questions": [
            {
                "key": "vc_all_in_vcs",
                "text": "Is all application code, configuration, and infrastructure stored in version control?",
                "guidance": {
                    1: "Some code is outside VCS; shared drives or local copies are common.",
                    2: "Application code is in VCS but config/infra scripts are not.",
                    3: "All code and config in VCS; infrastructure-as-code emerging.",
                    4: "Everything in VCS including IaC, runbooks, and database schemas.",
                    5: "Single source of truth; everything reproducible from VCS alone.",
                },
            },
            {
                "key": "vc_branching",
                "text": "Does the team follow a consistent branching strategy?",
                "guidance": {
                    1: "No agreed strategy; long-lived branches, infrequent merges.",
                    2: "Basic branching model documented but not always followed.",
                    3: "Consistent strategy (e.g. trunk-based or GitFlow) across the team.",
                    4: "Short-lived branches merged at least daily; merge conflicts rare.",
                    5: "Trunk-based development with feature flags; continuous integration.",
                },
            },
            {
                "key": "vc_history",
                "text": "Are commits atomic, well-described, and linked to work items?",
                "guidance": {
                    1: "Large, infrequent commits with vague messages.",
                    2: "Smaller commits but messages lack context.",
                    3: "Commits reference tickets; PRs reviewed before merge.",
                    4: "Atomic commits with conventional format; automated checks on messages.",
                    5: "Commit history tells the full story; bisectable and auditable.",
                },
            },
        ],
    },
    "build_process": {
        "label": "Build Process",
        "description": "Automation, speed, and reliability of the build pipeline.",
        "questions": [
            {
                "key": "bp_automated",
                "text": "Is the build fully automated and triggered on every commit?",
                "guidance": {
                    1: "Builds are manual or run on developer machines.",
                    2: "CI server exists but builds are triggered manually or nightly.",
                    3: "Every commit triggers a build automatically.",
                    4: "Build includes linting, compilation, and artefact publishing.",
                    5: "Build is hermetic, reproducible, and cached for speed.",
                },
            },
            {
                "key": "bp_speed",
                "text": "Does the build complete in under 10 minutes?",
                "guidance": {
                    1: "Builds take over 30 minutes or are unreliable.",
                    2: "Builds take 15-30 minutes.",
                    3: "Builds complete in 10-15 minutes.",
                    4: "Builds complete in under 10 minutes with parallelisation.",
                    5: "Builds complete in under 5 minutes; incremental builds used.",
                },
            },
            {
                "key": "bp_repeatable",
                "text": "Can any team member reproduce the build locally?",
                "guidance": {
                    1: "Only certain people can build; tribal knowledge required.",
                    2: "Build docs exist but are often outdated.",
                    3: "Any developer can build with documented steps.",
                    4: "One-command build that works on any supported platform.",
                    5: "Containerised build environment; identical local and CI builds.",
                },
            },
        ],
    },
    "testing": {
        "label": "Testing",
        "description": "Test coverage, automation, and the shape of the test pyramid.",
        "questions": [
            {
                "key": "t_unit",
                "text": "Is there meaningful unit test coverage?",
                "guidance": {
                    1: "No unit tests or very few.",
                    2: "Some unit tests but coverage is patchy (<30%).",
                    3: "Good coverage of critical paths (30-60%).",
                    4: "High coverage (>60%) with tests run on every commit.",
                    5: ">80% coverage; TDD practised; tests are fast and reliable.",
                },
            },
            {
                "key": "t_integration",
                "text": "Are integration and API tests automated?",
                "guidance": {
                    1: "No integration tests.",
                    2: "Some manual integration testing.",
                    3: "Automated integration tests for key flows.",
                    4: "Comprehensive integration suite run in CI.",
                    5: "Contract tests, consumer-driven contracts, or equivalent.",
                },
            },
            {
                "key": "t_acceptance",
                "text": "Are acceptance/end-to-end tests automated?",
                "guidance": {
                    1: "All testing is manual.",
                    2: "Some E2E tests but flaky or slow.",
                    3: "Stable E2E suite covering critical user journeys.",
                    4: "E2E tests run in CI with parallelisation.",
                    5: "Testing pyramid well-balanced; E2E tests are a thin top layer.",
                },
            },
            {
                "key": "t_performance",
                "text": "Is performance testing part of the pipeline?",
                "guidance": {
                    1: "No performance testing.",
                    2: "Ad-hoc load tests before major releases.",
                    3: "Regular performance tests on staging.",
                    4: "Automated performance tests in CI with thresholds.",
                    5: "Continuous performance benchmarking with trend analysis.",
                },
            },
        ],
    },
    "deployment": {
        "label": "Deployment",
        "description": "Automation, frequency, and safety of deployments.",
        "questions": [
            {
                "key": "d_automated",
                "text": "Is deployment a single-command, automated process?",
                "guidance": {
                    1: "Deployments are manual with runbook steps.",
                    2: "Partially scripted but requires manual intervention.",
                    3: "Fully automated deployment to staging; manual prod approval.",
                    4: "One-click deployment to production with rollback capability.",
                    5: "Continuous deployment; every green build goes to production.",
                },
            },
            {
                "key": "d_zero_downtime",
                "text": "Are deployments zero-downtime?",
                "guidance": {
                    1: "Deployments require scheduled downtime.",
                    2: "Maintenance windows used but downtime is brief.",
                    3: "Blue-green or rolling deployments for most services.",
                    4: "Zero-downtime deployments with automated canary analysis.",
                    5: "Progressive delivery with feature flags and traffic shifting.",
                },
            },
            {
                "key": "d_frequency",
                "text": "How frequently does the team deploy to production?",
                "guidance": {
                    1: "Monthly or less frequently.",
                    2: "Every 1-2 weeks.",
                    3: "Multiple times per week.",
                    4: "Daily deployments.",
                    5: "Multiple times per day; on-demand.",
                },
            },
        ],
    },
    "monitoring": {
        "label": "Monitoring & Observability",
        "description": "Visibility into system health, performance, and behaviour.",
        "questions": [
            {
                "key": "m_logging",
                "text": "Is structured, centralised logging in place?",
                "guidance": {
                    1: "Logs on local disk; no aggregation.",
                    2: "Logs shipped to a central system but unstructured.",
                    3: "Structured logging with search capability.",
                    4: "Correlated logs with request IDs across services.",
                    5: "Logs integrated with traces and metrics; anomaly detection.",
                },
            },
            {
                "key": "m_metrics",
                "text": "Are application and infrastructure metrics collected?",
                "guidance": {
                    1: "No metrics collection.",
                    2: "Basic infrastructure metrics (CPU, memory).",
                    3: "Application-level metrics (latency, error rates, throughput).",
                    4: "Custom business metrics with dashboards.",
                    5: "SLOs defined and tracked; error budgets drive decisions.",
                },
            },
            {
                "key": "m_alerting",
                "text": "Is there meaningful alerting with clear escalation?",
                "guidance": {
                    1: "No alerting; issues found by users.",
                    2: "Basic alerts but noisy; alert fatigue common.",
                    3: "Alerts on key metrics with defined thresholds.",
                    4: "Tiered alerting with escalation policies and runbooks.",
                    5: "Alerts based on SLOs; automated remediation for common issues.",
                },
            },
            {
                "key": "m_tracing",
                "text": "Is distributed tracing available?",
                "guidance": {
                    1: "No tracing capability.",
                    2: "Basic request logging but no trace correlation.",
                    3: "Distributed tracing for key services.",
                    4: "Full trace coverage with sampling; traces linked to logs/metrics.",
                    5: "Continuous profiling and trace-based analysis in production.",
                },
            },
        ],
    },
    "security": {
        "label": "Security",
        "description": "Security practices integrated into the development lifecycle.",
        "questions": [
            {
                "key": "s_sast",
                "text": "Is static application security testing (SAST) automated?",
                "guidance": {
                    1: "No SAST tooling.",
                    2: "Manual code reviews for security only.",
                    3: "SAST tool runs but results not consistently actioned.",
                    4: "SAST in CI pipeline; findings block merges above threshold.",
                    5: "SAST with custom rules tuned to the codebase; low false-positive rate.",
                },
            },
            {
                "key": "s_dependencies",
                "text": "Are dependencies scanned for known vulnerabilities?",
                "guidance": {
                    1: "No dependency scanning.",
                    2: "Occasional manual checks.",
                    3: "Automated scanning on a schedule.",
                    4: "Scanning in CI; critical vulnerabilities block builds.",
                    5: "Automated PRs for dependency updates; SLA on patching.",
                },
            },
            {
                "key": "s_secrets",
                "text": "How are secrets and credentials managed?",
                "guidance": {
                    1: "Secrets in code or config files.",
                    2: "Secrets in environment variables but not rotated.",
                    3: "Secrets manager used (e.g. Vault, AWS Secrets Manager).",
                    4: "Automated rotation; no long-lived credentials.",
                    5: "Zero-trust secret management; workload identity; audit trail.",
                },
            },
        ],
    },
    "configuration_management": {
        "label": "Configuration Management",
        "description": "How configuration is managed, separated from code, and kept consistent across environments.",
        "questions": [
            {
                "key": "cm_env_parity",
                "text": "How similar are development, staging, and production environments?",
                "guidance": {
                    1: "Environments are significantly different; 'works on my machine' common.",
                    2: "Some effort to align but meaningful drift exists.",
                    3: "Environments provisioned from same templates; minor differences.",
                    4: "Identical infrastructure; only config values differ per environment.",
                    5: "Ephemeral environments spun up on demand from code; full parity.",
                },
            },
            {
                "key": "cm_config_as_code",
                "text": "Is all configuration managed as code and version controlled?",
                "guidance": {
                    1: "Configuration is manual; settings changed via UIs or SSH.",
                    2: "Some config in files but not version controlled.",
                    3: "Config files in VCS; changes go through PR review.",
                    4: "Config templated and environment-specific values injected at deploy.",
                    5: "GitOps: all config changes via merge to main; drift detection in place.",
                },
            },
            {
                "key": "cm_separation",
                "text": "Is configuration cleanly separated from application code?",
                "guidance": {
                    1: "Config values hardcoded in application code.",
                    2: "Config in files bundled with the application.",
                    3: "Config externalised via environment variables or config service.",
                    4: "Feature flags and runtime config separate from deployment.",
                    5: "Dynamic config with audit trail; changes don't require redeploy.",
                },
            },
        ],
    },
    "feedback_loops": {
        "label": "Feedback Loops (DORA Metrics)",
        "description": "Speed and quality of feedback from development to production, measured via the four DORA metrics.",
        "questions": [
            {
                "key": "fl_deploy_frequency",
                "text": "Deployment Frequency: How often does your team deploy to production?",
                "guidance": {
                    1: "Less than once per month.",
                    2: "Between once per month and once per week.",
                    3: "Between once per week and once per day.",
                    4: "Daily deployments.",
                    5: "On-demand; multiple deploys per day.",
                },
            },
            {
                "key": "fl_lead_time",
                "text": "Lead Time for Changes: How long from commit to production?",
                "guidance": {
                    1: "More than 6 months.",
                    2: "1-6 months.",
                    3: "1 week to 1 month.",
                    4: "1 day to 1 week.",
                    5: "Less than 1 day (hours or minutes).",
                },
            },
            {
                "key": "fl_mttr",
                "text": "Mean Time to Restore (MTTR): How long to recover from a production failure?",
                "guidance": {
                    1: "More than 1 week.",
                    2: "1 day to 1 week.",
                    3: "Hours (same business day).",
                    4: "Less than 1 hour.",
                    5: "Minutes; automated rollback and self-healing.",
                },
            },
            {
                "key": "fl_change_failure",
                "text": "Change Failure Rate: What percentage of deployments cause a failure?",
                "guidance": {
                    1: "More than 45%.",
                    2: "31-45%.",
                    3: "16-30%.",
                    4: "1-15%.",
                    5: "0-5%; failures caught in pre-production.",
                },
            },
        ],
    },
    "ai_readiness": {
        "label": "AI Readiness",
        "description": "How well the codebase supports AI-assisted development, agentic workflows, and whether the code itself appears AI-generated or human-crafted.",
        "questions": [
            {
                "key": "ai_agent_config",
                "text": "Is the repository configured for AI coding agents?",
                "guidance": {
                    1: "No AI tooling configuration present.",
                    2: "Basic editor AI plugin (e.g. Copilot enabled) but no project-level config.",
                    3: "Project-level AI config (CLAUDE.md, .cursorrules, or copilot-instructions).",
                    4: "Detailed AI instructions with codebase conventions, architecture context, and task guidance.",
                    5: "Comprehensive AI agent setup with memory, hooks, MCP servers, and agentic workflows.",
                },
            },
            {
                "key": "ai_memory",
                "text": "Does the project have AI memory or persistent context systems?",
                "guidance": {
                    1: "No AI memory or context persistence.",
                    2: "Basic README or docs that AI can reference.",
                    3: "Structured project instructions (CLAUDE.md, AGENTS.md) with conventions.",
                    4: "AI memory system with session persistence and context recall.",
                    5: "Full AI memory with warm/hot context, cross-session learning, and team knowledge sharing.",
                },
            },
            {
                "key": "ai_generated",
                "text": "What proportion of the codebase appears to be AI-generated?",
                "guidance": {
                    1: "No evidence of AI-assisted development.",
                    2: "Occasional AI co-authorship (< 20% of commits).",
                    3: "Regular AI co-authorship (20-50% of commits).",
                    4: "Majority AI-assisted (50-80% of commits have AI co-author).",
                    5: "Primarily AI-generated codebase (> 80% AI co-authored); human role is review and direction.",
                },
            },
            {
                "key": "ai_tooling",
                "text": "Are AI/ML libraries and frameworks integrated into the project?",
                "guidance": {
                    1: "No AI/ML dependencies.",
                    2: "Basic AI SDK present (e.g. openai, anthropic client).",
                    3: "AI framework integration (LangChain, LlamaIndex, Semantic Kernel, etc.).",
                    4: "AI-powered features with structured prompts, tool use, and agent patterns.",
                    5: "Full AI platform with MCP servers, agent orchestration, RAG pipelines, or custom models.",
                },
            },
        ],
    },
}
