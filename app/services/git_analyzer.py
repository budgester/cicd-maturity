import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


class GitAnalyzer:
    """Analyzes a git repository to produce evidence-based maturity scores."""

    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.repo_path = None
        self._files_cache = None
        self._deps_cache = None

    def analyze(self):
        """Clone the repo and run all dimension checks. Returns dict of dimension -> {score, evidence}."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.repo_path = Path(tmpdir) / "repo"
            self._clone()
            return {
                "version_control": self._check_version_control(),
                "build_process": self._check_build_process(),
                "testing": self._check_testing(),
                "deployment": self._check_deployment(),
                "monitoring": self._check_monitoring(),
                "security": self._check_security(),
                "configuration_management": self._check_configuration_management(),
                "feedback_loops": self._check_feedback_loops(),
            }

    def _clone(self):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        subprocess.run(
            ["git", "clone", "--depth", "100", str(self.repo_url), str(self.repo_path)],
            timeout=120,
            capture_output=True,
            check=True,
            env=env,
        )

    # ── helpers ──────────────────────────────────────────────────────────

    def _files(self):
        if self._files_cache is None:
            self._files_cache = []
            for root, dirs, files in os.walk(self.repo_path):
                dirs[:] = [d for d in dirs if d != ".git"]
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), self.repo_path)
                    self._files_cache.append(rel)
        return self._files_cache

    def _file_exists(self, *patterns):
        for f in self._files():
            for p in patterns:
                if re.match(p, f, re.IGNORECASE):
                    return f
        return None

    def _files_matching(self, *patterns):
        matches = []
        for f in self._files():
            for p in patterns:
                if re.match(p, f, re.IGNORECASE):
                    matches.append(f)
        return matches

    def _dir_exists(self, *names):
        for name in names:
            if (self.repo_path / name).is_dir():
                return name
        return None

    def _read_file(self, path):
        try:
            return (self.repo_path / path).read_text(errors="ignore")
        except (FileNotFoundError, IsADirectoryError):
            return ""

    def _git(self, *args):
        result = subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout

    def _get_dependencies(self):
        if self._deps_cache is not None:
            return self._deps_cache

        deps = set()

        # Python requirements*.txt
        for f in self._files():
            if re.match(r"(.*[/\\])?requirements.*\.txt$", f, re.IGNORECASE):
                for line in self._read_file(f).splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        name = re.split(r"[>=<\[!;]", line)[0].strip().lower()
                        if name:
                            deps.add(name)

        # Python pyproject.toml
        pyproject = self._read_file("pyproject.toml")
        if pyproject:
            for m in re.findall(r'"([a-zA-Z0-9_-]+)', pyproject):
                deps.add(m.lower())

        # Python Pipfile
        pipfile = self._read_file("Pipfile")
        if pipfile:
            for m in re.findall(r"^([a-zA-Z0-9_-]+)\s*=", pipfile, re.MULTILINE):
                deps.add(m.lower())

        # Node package.json
        pkg_json = self._read_file("package.json")
        if pkg_json:
            try:
                pkg = json.loads(pkg_json)
                for section in ("dependencies", "devDependencies"):
                    for name in pkg.get(section, {}):
                        deps.add(name.lower())
            except (json.JSONDecodeError, ValueError):
                pass

        # Go go.mod
        go_mod = self._read_file("go.mod")
        if go_mod:
            for m in re.findall(r"^\s+(\S+)", go_mod, re.MULTILINE):
                deps.add(m.lower().split("/")[-1])

        # Ruby Gemfile
        gemfile = self._read_file("Gemfile")
        if gemfile:
            for m in re.findall(r"gem\s+['\"]([^'\"]+)", gemfile):
                deps.add(m.lower())

        self._deps_cache = deps
        return deps

    def _ci_file_contents(self):
        """Return list of (path, content) for all CI config files."""
        ci_patterns = [
            r"\.github/workflows/.*\.ya?ml$",
            r"Jenkinsfile$",
            r"\.gitlab-ci\.ya?ml$",
            r"\.circleci/config\.ya?ml$",
            r"\.travis\.ya?ml$",
            r"azure-pipelines\.ya?ml$",
            r"bitbucket-pipelines\.ya?ml$",
            r"\.buildkite/pipeline\.ya?ml$",
        ]
        results = []
        for f in self._files_matching(*ci_patterns):
            results.append((f, self._read_file(f)))
        return results

    def _ci_content_has(self, ci_files, *keywords):
        for _, content in ci_files:
            lower = content.lower()
            if any(kw in lower for kw in keywords):
                return True
        return False

    # ── dimension checks ─────────────────────────────────────────────────

    def _check_version_control(self):
        evidence = []
        score = 1

        # .gitignore
        if self._file_exists(r"\.gitignore$"):
            evidence.append({"check": "gitignore", "found": True, "detail": ".gitignore present"})
            score = max(score, 2)
        else:
            evidence.append({"check": "gitignore", "found": False, "detail": "No .gitignore found"})

        # README
        readme = self._file_exists(r"README(\.\w+)?$")
        if readme:
            evidence.append({"check": "readme", "found": True, "detail": f"Found {readme}"})
            score = max(score, 2)
        else:
            evidence.append({"check": "readme", "found": False, "detail": "No README found"})

        # CODEOWNERS
        codeowners = self._file_exists(r"(\.github/)?CODEOWNERS$", r"docs/CODEOWNERS$")
        if codeowners:
            evidence.append({"check": "codeowners", "found": True, "detail": f"Found {codeowners}"})
            score = max(score, 3)

        # Infrastructure as code
        iac_dir = self._dir_exists("terraform", "pulumi", "cloudformation", "ansible", "infrastructure", "infra")
        tf_file = self._file_exists(r".*\.tf$")
        if iac_dir or tf_file:
            detail = iac_dir or tf_file
            evidence.append({"check": "iac", "found": True, "detail": f"Infrastructure as code: {detail}"})
            score = max(score, 4)
        else:
            evidence.append({"check": "iac", "found": False, "detail": "No infrastructure-as-code files found"})

        # Commit message quality
        log = self._git("log", "--oneline", "-50", "--format=%s")
        commits = [l.strip() for l in log.strip().splitlines() if l.strip()]
        if commits:
            conventional = sum(
                1 for c in commits
                if re.match(r"^(feat|fix|chore|docs|style|refactor|test|ci|build|perf)[\(:]", c)
            )
            ticket_refs = sum(1 for c in commits if re.search(r"[A-Z]+-\d+|#\d+", c))

            if conventional > len(commits) * 0.5:
                evidence.append({
                    "check": "conventional_commits",
                    "found": True,
                    "detail": f"{conventional}/{len(commits)} commits use conventional format",
                })
                score = max(score, 4)
            elif ticket_refs > len(commits) * 0.3:
                evidence.append({
                    "check": "ticket_references",
                    "found": True,
                    "detail": f"{ticket_refs}/{len(commits)} commits reference tickets/PRs",
                })
                score = max(score, 3)
            else:
                avg_len = sum(len(c) for c in commits) / len(commits)
                if avg_len > 20:
                    evidence.append({
                        "check": "commit_messages",
                        "found": True,
                        "detail": f"Commit messages average {avg_len:.0f} chars",
                    })
                    score = max(score, 2)
                else:
                    evidence.append({
                        "check": "commit_messages",
                        "found": False,
                        "detail": f"Commit messages average only {avg_len:.0f} chars",
                    })

        # Branch count
        branch_output = self._git("ls-remote", "--heads", "origin")
        branch_count = len([l for l in branch_output.strip().splitlines() if l.strip()])
        if branch_count > 0:
            evidence.append({"check": "branches", "found": True, "detail": f"{branch_count} remote branch(es)"})
            if branch_count <= 5:
                evidence.append({
                    "check": "branch_discipline",
                    "found": True,
                    "detail": "Low branch count suggests disciplined branching",
                })
                score = max(score, 4)

        # All VCS evidence strong → level 5
        found_count = sum(1 for e in evidence if e["found"])
        if found_count >= 6:
            score = 5

        return {"score": min(score, 5), "evidence": evidence}

    def _check_build_process(self):
        evidence = []
        score = 1

        ci_files = self._ci_file_contents()
        ci_names = {
            r"\.github/workflows/": "GitHub Actions",
            r"Jenkinsfile": "Jenkins",
            r"\.gitlab-ci": "GitLab CI",
            r"\.circleci": "CircleCI",
            r"\.travis": "Travis CI",
            r"azure-pipelines": "Azure DevOps",
            r"bitbucket-pipelines": "Bitbucket Pipelines",
            r"\.buildkite": "Buildkite",
        }

        if ci_files:
            for path, _ in ci_files:
                name = "CI/CD"
                for pattern, ci_name in ci_names.items():
                    if re.search(pattern, path):
                        name = ci_name
                        break
                evidence.append({"check": "ci_config", "found": True, "detail": f"{name}: {path}"})
            score = max(score, 3)

            if self._ci_content_has(ci_files, "cache"):
                evidence.append({"check": "ci_caching", "found": True, "detail": "Build caching configured"})
                score = max(score, 4)

            if self._ci_content_has(ci_files, "parallel", "matrix", "strategy"):
                evidence.append({"check": "ci_parallel", "found": True, "detail": "Parallelisation configured"})
                score = max(score, 4)

            if self._ci_content_has(ci_files, "artifact", "upload", "publish"):
                evidence.append({"check": "ci_artifacts", "found": True, "detail": "Artefact publishing configured"})
                score = max(score, 4)

            if self._ci_content_has(ci_files, "lint", "ruff", "eslint", "flake8", "pylint", "rubocop", "golangci"):
                evidence.append({"check": "ci_linting", "found": True, "detail": "Linting in CI pipeline"})
                score = max(score, 3)
        else:
            evidence.append({"check": "ci_config", "found": False, "detail": "No CI/CD configuration found"})

        # Build tools
        build_tools = {
            r"Makefile$": "Make",
            r"build\.gradle(\.kts)?$": "Gradle",
            r"pom\.xml$": "Maven",
            r"Rakefile$": "Rake",
            r"Taskfile\.ya?ml$": "Task",
        }
        for pattern, name in build_tools.items():
            match = self._file_exists(pattern)
            if match:
                evidence.append({"check": "build_tool", "found": True, "detail": f"Build tool: {name}"})
                score = max(score, 2)
                break

        # Containerised build
        dockerfile = self._file_exists(r"Dockerfile$", r"Dockerfile\.\w+$")
        if dockerfile:
            evidence.append({"check": "containerised_build", "found": True, "detail": f"Dockerfile: {dockerfile}"})
            score = max(score, 4)
        else:
            evidence.append({"check": "containerised_build", "found": False, "detail": "No Dockerfile found"})

        # Dependency pinning (lock files)
        lock_patterns = {
            r"package-lock\.json$": "npm",
            r"yarn\.lock$": "yarn",
            r"pnpm-lock\.yaml$": "pnpm",
            r"Pipfile\.lock$": "pipenv",
            r"poetry\.lock$": "poetry",
            r"uv\.lock$": "uv",
            r"Gemfile\.lock$": "bundler",
            r"go\.sum$": "go modules",
            r"Cargo\.lock$": "cargo",
            r"composer\.lock$": "composer",
        }
        for pattern, name in lock_patterns.items():
            match = self._file_exists(pattern)
            if match:
                evidence.append({"check": "dependency_pinning", "found": True, "detail": f"Dependencies pinned via {name}"})
                score = max(score, 3)
                break

        # Level 5: containerised + multiple CI features
        ci_features = sum(1 for e in evidence if e["found"] and e["check"].startswith("ci_"))
        if ci_features >= 3 and dockerfile:
            score = 5

        return {"score": min(score, 5), "evidence": evidence}

    def _check_testing(self):
        evidence = []
        score = 1
        deps = self._get_dependencies()

        # Test directories
        test_dir = self._dir_exists("tests", "test", "spec", "__tests__", "test_suite")
        if test_dir:
            evidence.append({"check": "test_directory", "found": True, "detail": f"Test directory: {test_dir}/"})
            score = max(score, 2)
        else:
            evidence.append({"check": "test_directory", "found": False, "detail": "No test directory found"})

        # Test files
        test_files = self._files_matching(r".*test_\w+\.py$", r".*_test\.py$", r".*\.test\.\w+$", r".*\.spec\.\w+$")
        if test_files:
            evidence.append({"check": "test_files", "found": True, "detail": f"{len(test_files)} test file(s) found"})
            score = max(score, 2)

        # Test framework in dependencies
        test_frameworks = {
            "pytest", "unittest2", "nose2",
            "jest", "mocha", "jasmine", "vitest", "ava",
            "rspec", "minitest",
            "junit", "testng",
        }
        found_frameworks = deps & test_frameworks
        if found_frameworks:
            evidence.append({"check": "test_framework", "found": True, "detail": f"Test framework: {', '.join(found_frameworks)}"})
            score = max(score, 2)

        # Tests in CI
        ci_files = self._ci_file_contents()
        if self._ci_content_has(ci_files, "pytest", "npm test", "go test", "cargo test", "rspec", "jest", "vitest", "unittest"):
            evidence.append({"check": "tests_in_ci", "found": True, "detail": "Tests executed in CI pipeline"})
            score = max(score, 3)

        # Coverage config
        coverage_indicators = [
            r"\.coveragerc$",
            r"\.nycrc(\.json)?$",
            r"jest\.config\.\w+$",
            r"codecov\.ya?ml$",
        ]
        cov_file = None
        for p in coverage_indicators:
            cov_file = self._file_exists(p)
            if cov_file:
                break
        # Also check pyproject.toml/package.json for coverage config
        pyproject = self._read_file("pyproject.toml")
        if "coverage" in pyproject.lower():
            cov_file = cov_file or "pyproject.toml (coverage config)"
        if cov_file:
            evidence.append({"check": "coverage_config", "found": True, "detail": f"Coverage configured: {cov_file}"})
            score = max(score, 3)

        if self._ci_content_has(ci_files, "coverage", "codecov", "coveralls"):
            evidence.append({"check": "coverage_in_ci", "found": True, "detail": "Coverage reporting in CI"})
            score = max(score, 3)

        # E2E testing
        e2e_tools = {
            "cypress", "playwright", "@playwright/test", "selenium-webdriver",
            "puppeteer", "nightwatch", "testcafe", "capybara",
        }
        found_e2e = deps & e2e_tools
        e2e_dir = self._dir_exists("cypress", "e2e", "playwright")
        if found_e2e or e2e_dir:
            detail = ", ".join(found_e2e) if found_e2e else e2e_dir
            evidence.append({"check": "e2e_tests", "found": True, "detail": f"E2E testing: {detail}"})
            score = max(score, 4)

        # Performance testing
        perf_tools = {"k6", "locust", "artillery", "gatling", "jmeter"}
        found_perf = deps & perf_tools
        perf_dir = self._dir_exists("k6", "performance", "perf", "load-tests")
        perf_file = self._file_exists(r"locustfile\.py$", r"artillery\.ya?ml$")
        if found_perf or perf_dir or perf_file:
            detail = ", ".join(found_perf) if found_perf else (perf_dir or perf_file)
            evidence.append({"check": "performance_tests", "found": True, "detail": f"Performance testing: {detail}"})
            score = max(score, 4)

        # Level 5: comprehensive testing pyramid
        found_count = sum(1 for e in evidence if e["found"])
        if found_count >= 6:
            score = 5

        return {"score": min(score, 5), "evidence": evidence}

    def _check_deployment(self):
        evidence = []
        score = 1

        # Dockerfile
        dockerfile = self._file_exists(r"Dockerfile$", r"Dockerfile\.\w+$")
        if dockerfile:
            evidence.append({"check": "dockerfile", "found": True, "detail": f"Containerised: {dockerfile}"})
            score = max(score, 2)
        else:
            evidence.append({"check": "dockerfile", "found": False, "detail": "No Dockerfile found"})

        # Docker Compose
        compose = self._file_exists(r"docker-compose\.ya?ml$", r"compose\.ya?ml$")
        if compose:
            evidence.append({"check": "docker_compose", "found": True, "detail": f"Docker Compose: {compose}"})
            score = max(score, 2)

        # Kubernetes / Helm
        k8s_dir = self._dir_exists("k8s", "kubernetes", "deploy", "deployment", "helm", "charts")
        kustomize = self._file_exists(r"kustomization\.ya?ml$")
        helm_chart = self._file_exists(r"Chart\.ya?ml$")
        if k8s_dir or kustomize or helm_chart:
            detail = k8s_dir or kustomize or helm_chart
            evidence.append({"check": "k8s", "found": True, "detail": f"Kubernetes/Helm: {detail}"})
            score = max(score, 3)

        # Other deployment platforms
        platform_files = {
            r"Procfile$": "Heroku",
            r"app\.ya?ml$": "GCP App Engine",
            r"serverless\.ya?ml$": "Serverless Framework",
            r"fly\.toml$": "Fly.io",
            r"render\.ya?ml$": "Render",
            r"netlify\.toml$": "Netlify",
            r"vercel\.json$": "Vercel",
        }
        for pattern, name in platform_files.items():
            match = self._file_exists(pattern)
            if match:
                evidence.append({"check": "deploy_platform", "found": True, "detail": f"Platform: {name}"})
                score = max(score, 3)
                break

        # CD in CI config
        ci_files = self._ci_file_contents()
        if self._ci_content_has(ci_files, "deploy", "release", "publish", "push"):
            evidence.append({"check": "cd_pipeline", "found": True, "detail": "Deployment steps in CI/CD pipeline"})
            score = max(score, 3)

        # Deployment strategies
        all_content = " ".join(content for _, content in ci_files).lower()
        k8s_files_content = ""
        for f in self._files_matching(r".*\.ya?ml$"):
            if any(d in f for d in ["k8s", "kubernetes", "deploy", "helm"]):
                k8s_files_content += self._read_file(f).lower()

        combined = all_content + k8s_files_content
        if any(kw in combined for kw in ["rolling", "canary", "blue-green", "bluegreen", "progressive"]):
            evidence.append({"check": "deploy_strategy", "found": True, "detail": "Advanced deployment strategy detected (rolling/canary/blue-green)"})
            score = max(score, 4)

        if any(kw in combined for kw in ["feature-flag", "feature_flag", "featureflag", "launchdarkly", "unleash", "flipt"]):
            evidence.append({"check": "feature_flags", "found": True, "detail": "Feature flag usage detected"})
            score = max(score, 5)

        # Release tags
        tag_output = self._git("ls-remote", "--tags", "origin")
        tags = [l for l in tag_output.strip().splitlines() if l.strip() and "^{}" not in l]
        if tags:
            evidence.append({"check": "release_tags", "found": True, "detail": f"{len(tags)} release tag(s)"})
            score = max(score, 3)
        else:
            evidence.append({"check": "release_tags", "found": False, "detail": "No release tags found"})

        return {"score": min(score, 5), "evidence": evidence}

    def _check_monitoring(self):
        evidence = []
        score = 1
        deps = self._get_dependencies()

        # Logging libraries
        logging_libs = {
            "structlog", "python-json-logger", "loguru",
            "winston", "pino", "bunyan", "morgan",
            "zap", "logrus",
            "serilog",
            "log4j", "logback", "slf4j",
        }
        found_logging = deps & logging_libs
        if found_logging:
            evidence.append({"check": "logging_library", "found": True, "detail": f"Logging: {', '.join(found_logging)}"})
            score = max(score, 2)
            if found_logging & {"structlog", "python-json-logger", "pino", "winston", "zap"}:
                evidence.append({"check": "structured_logging", "found": True, "detail": "Structured logging library in use"})
                score = max(score, 3)
        else:
            evidence.append({"check": "logging_library", "found": False, "detail": "No dedicated logging library detected"})

        # Metrics libraries
        metrics_libs = {
            "prometheus-client", "prometheus_client", "prometheus-flask-instrumentator",
            "datadog", "ddtrace", "dd-trace",
            "statsd", "hot-shots",
            "micrometer",
            "opentelemetry-api", "opentelemetry-sdk",
            "@opentelemetry/api", "@opentelemetry/sdk-node",
        }
        found_metrics = deps & metrics_libs
        if found_metrics:
            evidence.append({"check": "metrics_library", "found": True, "detail": f"Metrics: {', '.join(found_metrics)}"})
            score = max(score, 3)
        else:
            evidence.append({"check": "metrics_library", "found": False, "detail": "No metrics library detected"})

        # Tracing
        tracing_libs = {
            "opentelemetry-sdk", "opentelemetry-api", "opentelemetry-instrumentation",
            "@opentelemetry/sdk-trace-node",
            "jaeger-client", "zipkin",
            "ddtrace", "dd-trace",
            "elastic-apm-node", "elastic-apm",
            "newrelic",
        }
        found_tracing = deps & tracing_libs
        if found_tracing:
            evidence.append({"check": "tracing_library", "found": True, "detail": f"Tracing: {', '.join(found_tracing)}"})
            score = max(score, 4)

        # Monitoring config files
        monitoring_configs = {
            r"prometheus\.ya?ml$": "Prometheus",
            r"grafana/": "Grafana",
            r"datadog\.ya?ml$": "Datadog",
            r"newrelic\.yml$": "New Relic",
            r"elastic-apm.*\.ya?ml$": "Elastic APM",
            r"otel.*\.ya?ml$": "OpenTelemetry",
        }
        for pattern, name in monitoring_configs.items():
            match = self._file_exists(pattern)
            if match:
                evidence.append({"check": "monitoring_config", "found": True, "detail": f"Monitoring config: {name}"})
                score = max(score, 3)
                break

        # Alerting config
        alert_files = self._file_exists(r"alertmanager\.ya?ml$", r"alerts?\.ya?ml$", r"pagerduty\.ya?ml$")
        if alert_files:
            evidence.append({"check": "alerting_config", "found": True, "detail": f"Alerting: {alert_files}"})
            score = max(score, 4)

        # Health check endpoints (look for common patterns in code)
        health_patterns = ["healthcheck", "health_check", "/health", "/ready", "/readiness", "/liveness"]
        for f in self._files_matching(r".*\.(py|js|ts|go|rb|java)$"):
            content = self._read_file(f).lower()
            if any(p in content for p in health_patterns):
                evidence.append({"check": "health_checks", "found": True, "detail": "Health check endpoints detected in code"})
                score = max(score, 2)
                break

        # Level 5: multiple observability pillars
        pillars = sum(1 for e in evidence if e["found"] and e["check"] in {"structured_logging", "metrics_library", "tracing_library", "alerting_config"})
        if pillars >= 3:
            score = 5

        return {"score": min(score, 5), "evidence": evidence}

    def _check_security(self):
        evidence = []
        score = 1

        # SECURITY.md
        if self._file_exists(r"SECURITY\.md$"):
            evidence.append({"check": "security_policy", "found": True, "detail": "SECURITY.md present"})
            score = max(score, 2)

        # Dependency scanning (Dependabot, Renovate, Snyk)
        dependabot = self._file_exists(r"\.github/dependabot\.ya?ml$")
        renovate = self._file_exists(r"renovate\.json5?$", r"\.renovaterc(\.json)?$")
        snyk = self._file_exists(r"\.snyk$")
        if dependabot:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Dependabot: {dependabot}"})
            score = max(score, 3)
        elif renovate:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Renovate: {renovate}"})
            score = max(score, 3)
        elif snyk:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Snyk: {snyk}"})
            score = max(score, 3)
        else:
            evidence.append({"check": "dependency_scanning", "found": False, "detail": "No dependency scanning configured (Dependabot, Renovate, or Snyk)"})

        # SAST tools
        sast_configs = {
            r"\.semgrep\.ya?ml$": "Semgrep",
            r"sonar-project\.properties$": "SonarQube",
            r"\.codeclimate\.ya?ml$": "CodeClimate",
            r"\.bandit$": "Bandit",
        }
        for pattern, name in sast_configs.items():
            match = self._file_exists(pattern)
            if match:
                evidence.append({"check": "sast_config", "found": True, "detail": f"SAST: {name}"})
                score = max(score, 3)
                break

        # Security in CI
        ci_files = self._ci_file_contents()
        security_ci_keywords = [
            "security", "sast", "dast", "bandit", "semgrep", "sonar",
            "trivy", "grype", "snyk", "codeql", "dependency-check",
        ]
        if self._ci_content_has(ci_files, *security_ci_keywords):
            evidence.append({"check": "security_in_ci", "found": True, "detail": "Security scanning in CI pipeline"})
            score = max(score, 4)

        # Pre-commit hooks
        pre_commit = self._file_exists(r"\.pre-commit-config\.ya?ml$")
        if pre_commit:
            content = self._read_file(pre_commit).lower()
            evidence.append({"check": "pre_commit", "found": True, "detail": "Pre-commit hooks configured"})
            score = max(score, 2)
            if any(kw in content for kw in ["detect-secrets", "bandit", "safety", "gitleaks", "trufflehog"]):
                evidence.append({"check": "secret_detection", "found": True, "detail": "Secret detection in pre-commit hooks"})
                score = max(score, 4)

        # .gitignore checks for sensitive files
        gitignore = self._read_file(".gitignore").lower()
        if any(p in gitignore for p in [".env", "credentials", "secret", "*.pem", "*.key"]):
            evidence.append({"check": "gitignore_secrets", "found": True, "detail": "Sensitive files excluded via .gitignore"})
            score = max(score, 2)

        # Level 5: multiple security layers
        sec_count = sum(1 for e in evidence if e["found"])
        if sec_count >= 5:
            score = 5

        return {"score": min(score, 5), "evidence": evidence}

    def _check_configuration_management(self):
        evidence = []
        score = 1

        # .env.example / .env.sample
        env_example = self._file_exists(r"\.env\.example$", r"\.env\.sample$", r"\.env\.template$")
        if env_example:
            evidence.append({"check": "env_template", "found": True, "detail": f"Environment template: {env_example}"})
            score = max(score, 2)

        # Config directory
        config_dir = self._dir_exists("config", "conf", "settings", "cfg")
        if config_dir:
            evidence.append({"check": "config_directory", "found": True, "detail": f"Configuration directory: {config_dir}/"})
            score = max(score, 2)

        # Docker for environment parity
        dockerfile = self._file_exists(r"Dockerfile$")
        compose = self._file_exists(r"docker-compose\.ya?ml$", r"compose\.ya?ml$")
        devcontainer = self._file_exists(r"\.devcontainer/devcontainer\.json$", r"\.devcontainer\.json$")
        if dockerfile:
            evidence.append({"check": "container_parity", "found": True, "detail": "Dockerfile enables environment parity"})
            score = max(score, 3)
        if compose:
            evidence.append({"check": "compose_parity", "found": True, "detail": f"Docker Compose for local environment: {compose}"})
            score = max(score, 3)
        if devcontainer:
            evidence.append({"check": "devcontainer", "found": True, "detail": "Dev container configured for consistent dev environments"})
            score = max(score, 4)

        # Environment-specific config files
        env_configs = self._files_matching(
            r".*\.(dev|development|staging|stag|prod|production|test|testing)\.\w+$",
            r".*/config\.(dev|development|staging|prod|production|test)\.\w+$",
        )
        if env_configs:
            evidence.append({"check": "env_specific_config", "found": True, "detail": f"{len(env_configs)} environment-specific config file(s)"})
            score = max(score, 3)

        # IaC (shared with version_control but relevant here for config-as-code)
        iac_dir = self._dir_exists("terraform", "pulumi", "cloudformation", "ansible")
        if iac_dir:
            evidence.append({"check": "config_as_code", "found": True, "detail": f"Configuration as code: {iac_dir}/"})
            score = max(score, 4)

        # GitOps indicators
        gitops_files = self._file_exists(r"argocd/", r"flux/", r"fluxcd/")
        gitops_dir = self._dir_exists("argocd", "flux", "fluxcd", "gitops")
        if gitops_files or gitops_dir:
            evidence.append({"check": "gitops", "found": True, "detail": f"GitOps: {gitops_files or gitops_dir}"})
            score = max(score, 5)

        # EditorConfig
        editorconfig = self._file_exists(r"\.editorconfig$")
        if editorconfig:
            evidence.append({"check": "editorconfig", "found": True, "detail": "EditorConfig for consistent coding styles"})
            score = max(score, 2)

        if not any(e["found"] for e in evidence):
            evidence.append({"check": "config_management", "found": False, "detail": "No configuration management patterns detected"})

        return {"score": min(score, 5), "evidence": evidence}

    def _check_feedback_loops(self):
        evidence = []
        score = 1

        # Release tag frequency
        tag_output = self._git("for-each-ref", "--sort=-creatordate", "--format=%(creatordate:iso8601)", "refs/tags")
        tag_dates = [l.strip() for l in tag_output.strip().splitlines() if l.strip()]

        if len(tag_dates) >= 2:
            from datetime import datetime
            try:
                dates = []
                for d in tag_dates[:20]:
                    # Parse ISO format, handle timezone
                    clean = re.sub(r"\s+[+-]\d{4}$", "", d)
                    dt = datetime.fromisoformat(clean)
                    dates.append(dt)

                if len(dates) >= 2:
                    spans = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
                    avg_days = sum(spans) / len(spans) if spans else 999

                    if avg_days <= 1:
                        evidence.append({"check": "release_frequency", "found": True, "detail": f"Releases every {avg_days:.1f} days (multiple per day)"})
                        score = max(score, 5)
                    elif avg_days <= 7:
                        evidence.append({"check": "release_frequency", "found": True, "detail": f"Releases every {avg_days:.1f} days (daily/weekly)"})
                        score = max(score, 4)
                    elif avg_days <= 30:
                        evidence.append({"check": "release_frequency", "found": True, "detail": f"Releases every {avg_days:.0f} days (weekly/monthly)"})
                        score = max(score, 3)
                    elif avg_days <= 90:
                        evidence.append({"check": "release_frequency", "found": True, "detail": f"Releases every {avg_days:.0f} days (monthly/quarterly)"})
                        score = max(score, 2)
                    else:
                        evidence.append({"check": "release_frequency", "found": True, "detail": f"Releases every {avg_days:.0f} days (infrequent)"})
            except (ValueError, IndexError):
                pass
        elif len(tag_dates) == 1:
            evidence.append({"check": "release_frequency", "found": True, "detail": "1 release tag found"})
            score = max(score, 2)
        else:
            evidence.append({"check": "release_frequency", "found": False, "detail": "No release tags found to measure deploy frequency"})

        # Commit frequency
        log = self._git("log", "--format=%aI", "-100")
        commit_dates = [l.strip() for l in log.strip().splitlines() if l.strip()]
        if len(commit_dates) >= 2:
            from datetime import datetime
            try:
                first = re.sub(r"[+-]\d{2}:\d{2}$", "", commit_dates[-1])
                last = re.sub(r"[+-]\d{2}:\d{2}$", "", commit_dates[0])
                dt_first = datetime.fromisoformat(first)
                dt_last = datetime.fromisoformat(last)
                span_days = max((dt_last - dt_first).days, 1)
                commits_per_week = (len(commit_dates) / span_days) * 7

                if commits_per_week >= 20:
                    evidence.append({"check": "commit_frequency", "found": True, "detail": f"{commits_per_week:.0f} commits/week (very active)"})
                    score = max(score, 3)
                elif commits_per_week >= 5:
                    evidence.append({"check": "commit_frequency", "found": True, "detail": f"{commits_per_week:.0f} commits/week (active)"})
                    score = max(score, 2)
                else:
                    evidence.append({"check": "commit_frequency", "found": True, "detail": f"{commits_per_week:.1f} commits/week"})
            except (ValueError, IndexError):
                pass

        # Full CI/CD pipeline (build + test + deploy)
        ci_files = self._ci_file_contents()
        has_build = self._ci_content_has(ci_files, "build", "compile", "install")
        has_test = self._ci_content_has(ci_files, "test", "pytest", "jest", "spec")
        has_deploy = self._ci_content_has(ci_files, "deploy", "release", "publish")

        if has_build and has_test and has_deploy:
            evidence.append({"check": "full_pipeline", "found": True, "detail": "Complete CI/CD pipeline: build + test + deploy"})
            score = max(score, 4)
        elif has_build and has_test:
            evidence.append({"check": "ci_pipeline", "found": True, "detail": "CI pipeline: build + test (no automated deployment)"})
            score = max(score, 3)
        elif ci_files:
            evidence.append({"check": "basic_pipeline", "found": True, "detail": "Basic CI pipeline present"})
            score = max(score, 2)
        else:
            evidence.append({"check": "no_pipeline", "found": False, "detail": "No CI/CD pipeline detected"})

        # Rollback capability
        ci_content = " ".join(c for _, c in ci_files).lower()
        if any(kw in ci_content for kw in ["rollback", "revert", "undo"]):
            evidence.append({"check": "rollback", "found": True, "detail": "Rollback capability in pipeline"})
            score = max(score, 4)

        return {"score": min(score, 5), "evidence": evidence}
