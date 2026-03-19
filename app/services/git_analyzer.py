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
        """Clone the repo and run all dimension checks.

        Returns dict with:
            "dimensions": {dimension -> {score, evidence}}
            "classification": {type, confidence, signals}
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self.repo_path = Path(tmpdir) / "repo"
            self._clone()
            return {
                "dimensions": {
                    "version_control": self._check_version_control(),
                    "build_process": self._check_build_process(),
                    "testing": self._check_testing(),
                    "deployment": self._check_deployment(),
                    "monitoring": self._check_monitoring(),
                    "security": self._check_security(),
                    "configuration_management": self._check_configuration_management(),
                    "feedback_loops": self._check_feedback_loops(),
                    "ai_readiness": self._check_ai_readiness(),
                },
                "classification": self._classify_application(),
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
        gitignore = self._file_exists(r"\.gitignore$")
        if gitignore:
            evidence.append({"check": "gitignore", "found": True, "detail": ".gitignore present", "path": gitignore})
            score = max(score, 2)
        else:
            evidence.append({"check": "gitignore", "found": False, "detail": "No .gitignore found"})

        # README
        readme = self._file_exists(r"README(\.\w+)?$")
        if readme:
            evidence.append({"check": "readme", "found": True, "detail": f"Found {readme}", "path": readme})
            score = max(score, 2)
        else:
            evidence.append({"check": "readme", "found": False, "detail": "No README found"})

        # CODEOWNERS
        codeowners = self._file_exists(r"(\.github/)?CODEOWNERS$", r"docs/CODEOWNERS$")
        if codeowners:
            evidence.append({"check": "codeowners", "found": True, "detail": f"Found {codeowners}", "path": codeowners})
            score = max(score, 3)

        # Infrastructure as code
        iac_dir = self._dir_exists("terraform", "pulumi", "cloudformation", "ansible", "infrastructure", "infra")
        tf_file = self._file_exists(r".*\.tf$")
        if iac_dir or tf_file:
            detail = iac_dir or tf_file
            evidence.append({"check": "iac", "found": True, "detail": f"Infrastructure as code: {detail}", "path": tf_file or iac_dir})
            score = max(score, 4)
        else:
            evidence.append({"check": "iac", "found": False, "detail": "No infrastructure-as-code files found"})

        # Commit message quality
        log = self._git("log", "--oneline", "-50", "--format=%s")
        commits = [line.strip() for line in log.strip().splitlines() if line.strip()]
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
        branch_count = len([line for line in branch_output.strip().splitlines() if line.strip()])
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
                evidence.append({"check": "ci_config", "found": True, "detail": f"{name}: {path}", "path": path})
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
                evidence.append({"check": "build_tool", "found": True, "detail": f"Build tool: {name}", "path": match})
                score = max(score, 2)
                break

        # Containerised build
        dockerfile = self._file_exists(r"Dockerfile$", r"Dockerfile\.\w+$")
        if dockerfile:
            evidence.append({"check": "containerised_build", "found": True, "detail": f"Dockerfile: {dockerfile}", "path": dockerfile})
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
                evidence.append({"check": "dependency_pinning", "found": True, "detail": f"Dependencies pinned via {name}", "path": match})
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
            evidence.append({"check": "test_directory", "found": True, "detail": f"Test directory: {test_dir}/", "path": test_dir})
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
            evidence.append({"check": "coverage_config", "found": True, "detail": f"Coverage configured: {cov_file}", "path": cov_file})
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
            evidence.append({"check": "e2e_tests", "found": True, "detail": f"E2E testing: {detail}", "path": e2e_dir})
            score = max(score, 4)

        # Performance testing
        perf_tools = {"k6", "locust", "artillery", "gatling", "jmeter"}
        found_perf = deps & perf_tools
        perf_dir = self._dir_exists("k6", "performance", "perf", "load-tests")
        perf_file = self._file_exists(r"locustfile\.py$", r"artillery\.ya?ml$")
        if found_perf or perf_dir or perf_file:
            detail = ", ".join(found_perf) if found_perf else (perf_dir or perf_file)
            evidence.append({"check": "performance_tests", "found": True, "detail": f"Performance testing: {detail}", "path": perf_dir or perf_file})
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
            evidence.append({"check": "dockerfile", "found": True, "detail": f"Containerised: {dockerfile}", "path": dockerfile})
            score = max(score, 2)
        else:
            evidence.append({"check": "dockerfile", "found": False, "detail": "No Dockerfile found"})

        # Docker Compose
        compose = self._file_exists(r"docker-compose\.ya?ml$", r"compose\.ya?ml$")
        if compose:
            evidence.append({"check": "docker_compose", "found": True, "detail": f"Docker Compose: {compose}", "path": compose})
            score = max(score, 2)

        # Kubernetes / Helm
        k8s_dir = self._dir_exists("k8s", "kubernetes", "deploy", "deployment", "helm", "charts")
        kustomize = self._file_exists(r"kustomization\.ya?ml$")
        helm_chart = self._file_exists(r"Chart\.ya?ml$")
        if k8s_dir or kustomize or helm_chart:
            detail = k8s_dir or kustomize or helm_chart
            evidence.append({"check": "k8s", "found": True, "detail": f"Kubernetes/Helm: {detail}", "path": k8s_dir or kustomize or helm_chart})
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
                evidence.append({"check": "deploy_platform", "found": True, "detail": f"Platform: {name}", "path": match})
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
        tags = [line for line in tag_output.strip().splitlines() if line.strip() and "^{}" not in line]
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
                evidence.append({"check": "monitoring_config", "found": True, "detail": f"Monitoring config: {name}", "path": match})
                score = max(score, 3)
                break

        # Alerting config
        alert_files = self._file_exists(r"alertmanager\.ya?ml$", r"alerts?\.ya?ml$", r"pagerduty\.ya?ml$")
        if alert_files:
            evidence.append({"check": "alerting_config", "found": True, "detail": f"Alerting: {alert_files}", "path": alert_files})
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
        security_md = self._file_exists(r"SECURITY\.md$")
        if security_md:
            evidence.append({"check": "security_policy", "found": True, "detail": "SECURITY.md present", "path": security_md})
            score = max(score, 2)

        # Dependency scanning (Dependabot, Renovate, Snyk)
        dependabot = self._file_exists(r"\.github/dependabot\.ya?ml$")
        renovate = self._file_exists(r"renovate\.json5?$", r"\.renovaterc(\.json)?$")
        snyk = self._file_exists(r"\.snyk$")
        if dependabot:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Dependabot: {dependabot}", "path": dependabot})
            score = max(score, 3)
        elif renovate:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Renovate: {renovate}", "path": renovate})
            score = max(score, 3)
        elif snyk:
            evidence.append({"check": "dependency_scanning", "found": True, "detail": f"Snyk: {snyk}", "path": snyk})
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
                evidence.append({"check": "sast_config", "found": True, "detail": f"SAST: {name}", "path": match})
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
            evidence.append({"check": "pre_commit", "found": True, "detail": "Pre-commit hooks configured", "path": pre_commit})
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
            evidence.append({"check": "env_template", "found": True, "detail": f"Environment template: {env_example}", "path": env_example})
            score = max(score, 2)

        # Config directory
        config_dir = self._dir_exists("config", "conf", "settings", "cfg")
        if config_dir:
            evidence.append({"check": "config_directory", "found": True, "detail": f"Configuration directory: {config_dir}/", "path": config_dir})
            score = max(score, 2)

        # Docker for environment parity
        dockerfile = self._file_exists(r"Dockerfile$")
        compose = self._file_exists(r"docker-compose\.ya?ml$", r"compose\.ya?ml$")
        devcontainer = self._file_exists(r"\.devcontainer/devcontainer\.json$", r"\.devcontainer\.json$")
        if dockerfile:
            evidence.append({"check": "container_parity", "found": True, "detail": "Dockerfile enables environment parity", "path": dockerfile})
            score = max(score, 3)
        if compose:
            evidence.append({"check": "compose_parity", "found": True, "detail": f"Docker Compose for local environment: {compose}", "path": compose})
            score = max(score, 3)
        if devcontainer:
            evidence.append({
                "check": "devcontainer", "found": True,
                "detail": "Dev container configured for consistent dev environments", "path": devcontainer,
            })
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
            evidence.append({"check": "config_as_code", "found": True, "detail": f"Configuration as code: {iac_dir}/", "path": iac_dir})
            score = max(score, 4)

        # GitOps indicators
        gitops_files = self._file_exists(r"argocd/", r"flux/", r"fluxcd/")
        gitops_dir = self._dir_exists("argocd", "flux", "fluxcd", "gitops")
        if gitops_files or gitops_dir:
            evidence.append({"check": "gitops", "found": True, "detail": f"GitOps: {gitops_files or gitops_dir}", "path": gitops_files or gitops_dir})
            score = max(score, 5)

        # EditorConfig
        editorconfig = self._file_exists(r"\.editorconfig$")
        if editorconfig:
            evidence.append({"check": "editorconfig", "found": True, "detail": "EditorConfig for consistent coding styles", "path": editorconfig})
            score = max(score, 2)

        if not any(e["found"] for e in evidence):
            evidence.append({"check": "config_management", "found": False, "detail": "No configuration management patterns detected"})

        return {"score": min(score, 5), "evidence": evidence}

    def _check_feedback_loops(self):
        evidence = []
        score = 1

        # Release tag frequency
        tag_output = self._git("for-each-ref", "--sort=-creatordate", "--format=%(creatordate:iso8601)", "refs/tags")
        tag_dates = [line.strip() for line in tag_output.strip().splitlines() if line.strip()]

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
        commit_dates = [line.strip() for line in log.strip().splitlines() if line.strip()]
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

    def _check_ai_readiness(self):
        evidence = []
        score = 1
        deps = self._get_dependencies()

        # ── AI agent configuration files ─────────────────────────────────

        claude_md = self._file_exists(r"CLAUDE\.md$", r"claude\.md$")
        if claude_md:
            content = self._read_file(claude_md)
            evidence.append({"check": "claude_md", "found": True, "detail": f"Claude Code config: {claude_md} ({len(content)} chars)", "path": claude_md})
            score = max(score, 3)
            if len(content) > 500:
                evidence.append({"check": "claude_md_detailed", "found": True, "detail": "Detailed AI agent instructions (>500 chars)"})
                score = max(score, 4)
        else:
            evidence.append({"check": "claude_md", "found": False, "detail": "No CLAUDE.md found"})

        cursor_rules = self._file_exists(r"\.cursorrules$", r"\.cursor/rules$", r"\.cursor/.*\.mdc$")
        if cursor_rules:
            evidence.append({"check": "cursor_rules", "found": True, "detail": f"Cursor AI config: {cursor_rules}", "path": cursor_rules})
            score = max(score, 3)

        copilot_instructions = self._file_exists(
            r"\.github/copilot-instructions\.md$",
            r"\.github/copilot\.yml$",
        )
        if copilot_instructions:
            evidence.append({
                "check": "copilot_config", "found": True,
                "detail": f"GitHub Copilot config: {copilot_instructions}", "path": copilot_instructions,
            })
            score = max(score, 3)

        aider_config = self._file_exists(r"\.aider\.conf\.yml$", r"\.aiderignore$")
        if aider_config:
            evidence.append({"check": "aider_config", "found": True, "detail": f"Aider config: {aider_config}", "path": aider_config})
            score = max(score, 3)

        coderabbit = self._file_exists(r"\.coderabbit\.ya?ml$")
        if coderabbit:
            evidence.append({"check": "coderabbit_config", "found": True, "detail": f"CodeRabbit AI review: {coderabbit}", "path": coderabbit})
            score = max(score, 3)

        # ── AI memory and context systems ────────────────────────────────

        claude_dir = self._dir_exists(".claude")
        if claude_dir:
            evidence.append({"check": "claude_memory", "found": True, "detail": ".claude/ directory (AI memory/settings)", "path": claude_dir})
            score = max(score, 4)
            memory_files = self._files_matching(r"\.claude/.*\.md$", r"\.claude/.*\.json$")
            if len(memory_files) > 2:
                evidence.append({"check": "claude_memory_rich", "found": True, "detail": f"{len(memory_files)} AI memory/config files in .claude/"})
                score = max(score, 5)

        agents_md = self._file_exists(r"AGENTS\.md$", r"agents\.md$")
        if agents_md:
            evidence.append({"check": "agents_md", "found": True, "detail": f"Agent instructions: {agents_md}", "path": agents_md})
            score = max(score, 4)

        # ── MCP server configuration ────────────────────────────────────

        mcp_config = self._file_exists(
            r"\.claude/mcp.*\.json$",
            r"mcp\.json$",
            r"\.mcp\.json$",
            r"mcp-servers\.json$",
        )
        if mcp_config:
            evidence.append({"check": "mcp_servers", "found": True, "detail": f"MCP server config: {mcp_config}", "path": mcp_config})
            score = max(score, 5)

        # ── AI co-authorship in commits (AI-built vs human-built) ────────

        log_full = self._git("log", "--format=%s%n%b", "-100").lower()
        ai_coauthor_patterns = [
            "co-authored-by: claude",
            "co-authored-by: github copilot",
            "co-authored-by: cursor",
            "co-authored-by: aider",
            "co-authored-by: codeium",
            "co-authored-by: amazon q",
            "generated with claude",
            "generated by copilot",
        ]
        ai_mention_count = sum(log_full.count(p) for p in ai_coauthor_patterns)

        if ai_mention_count > 0:
            total_output = self._git("log", "--oneline", "-100")
            total_commits = len([line for line in total_output.strip().splitlines() if line.strip()])

            if total_commits > 0:
                pct = min((ai_mention_count / total_commits) * 100, 100)
                if pct > 80:
                    evidence.append({"check": "ai_coauthored", "found": True, "detail": f"~{pct:.0f}% of commits AI co-authored (primarily AI-built)"})
                    score = max(score, 5)
                elif pct > 50:
                    evidence.append({"check": "ai_coauthored", "found": True, "detail": f"~{pct:.0f}% of commits AI co-authored (majority AI-assisted)"})
                    score = max(score, 4)
                elif pct > 20:
                    evidence.append({"check": "ai_coauthored", "found": True, "detail": f"~{pct:.0f}% of commits AI co-authored (regular AI use)"})
                    score = max(score, 3)
                else:
                    evidence.append({"check": "ai_coauthored", "found": True, "detail": f"~{pct:.0f}% of commits AI co-authored (occasional AI use)"})
                    score = max(score, 2)
        else:
            evidence.append({"check": "ai_coauthored", "found": False, "detail": "No AI co-authorship detected in commits"})

        # ── AI/ML libraries in dependencies ──────────────────────────────

        ai_sdks = {
            "openai", "anthropic", "google-generativeai", "cohere",
            "mistralai", "groq", "replicate", "together",
        }
        found_sdks = deps & ai_sdks
        if found_sdks:
            evidence.append({"check": "ai_sdk", "found": True, "detail": f"AI SDK: {', '.join(found_sdks)}"})
            score = max(score, 2)

        ai_frameworks = {
            "langchain", "langchain-core", "langchain-community",
            "llama-index", "llama_index", "llamaindex",
            "semantic-kernel",
            "autogen", "crewai", "agency-swarm",
            "haystack", "dspy", "instructor",
            "transformers", "torch", "tensorflow",
            "sentence-transformers", "chromadb", "pinecone-client",
            "weaviate-client", "qdrant-client", "pgvector",
        }
        found_frameworks = deps & ai_frameworks
        if found_frameworks:
            evidence.append({"check": "ai_framework", "found": True, "detail": f"AI framework: {', '.join(found_frameworks)}"})
            score = max(score, 3)

        # Agent/tool-use patterns in code
        agent_patterns = [
            "tool_use", "tool_call", "function_calling",
            "create_agent", "agent_executor", "agentic",
            "rag_pipeline", "retrieval_chain",
        ]
        for f in self._files_matching(r".*\.(py|js|ts)$"):
            content = self._read_file(f).lower()
            found_patterns = [p for p in agent_patterns if p in content]
            if found_patterns:
                evidence.append({"check": "agent_patterns", "found": True, "detail": f"Agent/tool-use patterns in code: {', '.join(found_patterns[:3])}"})
                score = max(score, 4)
                break

        # ── Claude Code hooks ────────────────────────────────────────────

        hooks_config = self._file_exists(r"\.claude/settings\.json$", r"\.claude/hooks\.json$")
        if hooks_config:
            content = self._read_file(hooks_config).lower()
            if "hook" in content:
                evidence.append({"check": "claude_hooks", "found": True, "detail": "Claude Code hooks configured", "path": hooks_config})
                score = max(score, 5)

        if not any(e["found"] for e in evidence):
            evidence.append({"check": "ai_readiness", "found": False, "detail": "No AI tooling or configuration detected"})

        return {"score": min(score, 5), "evidence": evidence}

    # ── application classification ───────────────────────────────────────

    APPLICATION_TYPES = {
        "web_app": "Web Application",
        "api_service": "API Service",
        "library": "Library / Package",
        "cli_tool": "CLI Tool",
        "infrastructure": "Infrastructure / IaC",
        "data_pipeline": "Data Pipeline",
        "ml_ai": "ML / AI Application",
        "mobile_app": "Mobile Application",
        "static_site": "Static Site",
        "desktop_app": "Desktop Application",
        "monorepo": "Monorepo",
        "unknown": "Unknown",
    }

    def _classify_application(self):
        deps = self._get_dependencies()
        signals = []
        scores = {}  # type -> weighted score

        # ── Web Application ──────────────────────────────────────────────
        web_frameworks = {
            "flask", "django", "fastapi", "starlette",
            "express", "koa", "hapi", "next", "nuxt", "remix",
            "rails", "sinatra",
            "spring-boot", "spring-web",
            "gin", "echo", "fiber",
            "actix-web", "rocket", "axum",
            "laravel", "symfony",
            "phoenix",
        }
        found_web = deps & web_frameworks
        if found_web:
            signals.append(f"Web framework: {', '.join(found_web)}")
            scores["web_app"] = scores.get("web_app", 0) + 5

        templates_dir = self._dir_exists("templates", "views", "pages")
        if templates_dir:
            signals.append(f"Templates directory: {templates_dir}/")
            scores["web_app"] = scores.get("web_app", 0) + 3

        static_dir = self._dir_exists("static", "public", "assets")
        if static_dir:
            signals.append(f"Static assets: {static_dir}/")
            scores["web_app"] = scores.get("web_app", 0) + 1

        # ── API Service ──────────────────────────────────────────────────
        api_frameworks = {"fastapi", "starlette", "connexion", "graphene", "strawberry", "ariadne"}
        found_api = deps & api_frameworks
        if found_api:
            signals.append(f"API framework: {', '.join(found_api)}")
            scores["api_service"] = scores.get("api_service", 0) + 5

        openapi = self._file_exists(r"openapi\.ya?ml$", r"swagger\.ya?ml$", r"swagger\.json$", r"openapi\.json$")
        if openapi:
            signals.append(f"API spec: {openapi}")
            scores["api_service"] = scores.get("api_service", 0) + 4

        graphql_schema = self._file_exists(r".*\.graphql$", r"schema\.gql$")
        if graphql_schema:
            signals.append(f"GraphQL schema: {graphql_schema}")
            scores["api_service"] = scores.get("api_service", 0) + 4

        # Web frameworks without templates lean toward API
        if found_web and not templates_dir:
            scores["api_service"] = scores.get("api_service", 0) + 3

        # ── Library / Package ────────────────────────────────────────────
        pyproject = self._read_file("pyproject.toml")
        if "[build-system]" in pyproject:
            signals.append("Python build-system in pyproject.toml")
            scores["library"] = scores.get("library", 0) + 3

        setup_py = self._file_exists(r"setup\.py$", r"setup\.cfg$")
        if setup_py:
            signals.append(f"Package setup: {setup_py}")
            scores["library"] = scores.get("library", 0) + 3

        pkg_json = self._read_file("package.json")
        if pkg_json:
            import json as _json
            try:
                pkg = _json.loads(pkg_json)
                if "main" in pkg or "exports" in pkg or "module" in pkg:
                    signals.append("package.json with main/exports (library)")
                    scores["library"] = scores.get("library", 0) + 4
                if pkg.get("private") is True:
                    scores["library"] = scores.get("library", 0) - 3
            except (ValueError, _json.JSONDecodeError):
                pass

        cargo_toml = self._read_file("Cargo.toml")
        if "[lib]" in cargo_toml:
            signals.append("Rust library crate")
            scores["library"] = scores.get("library", 0) + 4

        gemspec = self._file_exists(r".*\.gemspec$")
        if gemspec:
            signals.append(f"Ruby gem: {gemspec}")
            scores["library"] = scores.get("library", 0) + 5

        # ── CLI Tool ─────────────────────────────────────────────────────
        cli_libs = {
            "click", "typer", "argparse", "fire",
            "commander", "yargs", "inquirer", "oclif",
            "cobra", "urfave-cli",
            "clap", "structopt",
            "thor", "gli",
        }
        found_cli = deps & cli_libs
        if found_cli:
            signals.append(f"CLI library: {', '.join(found_cli)}")
            scores["cli_tool"] = scores.get("cli_tool", 0) + 4

        if "console_scripts" in pyproject or "console_scripts" in self._read_file("setup.cfg"):
            signals.append("console_scripts entry point defined")
            scores["cli_tool"] = scores.get("cli_tool", 0) + 5

        if pkg_json:
            try:
                pkg = _json.loads(pkg_json)
                if "bin" in pkg:
                    signals.append("package.json bin entry (CLI)")
                    scores["cli_tool"] = scores.get("cli_tool", 0) + 5
            except (ValueError, _json.JSONDecodeError):
                pass

        # ── Infrastructure / IaC ─────────────────────────────────────────
        iac_dir = self._dir_exists("terraform", "pulumi", "cloudformation", "ansible", "infrastructure", "cdk")
        tf_files = self._files_matching(r".*\.tf$")
        if iac_dir or tf_files:
            signals.append(f"Infrastructure as code: {iac_dir or 'Terraform files'}")
            scores["infrastructure"] = scores.get("infrastructure", 0) + 6

        helm_dir = self._dir_exists("helm", "charts")
        kustomize = self._file_exists(r"kustomization\.ya?ml$")
        if helm_dir or kustomize:
            signals.append(f"Kubernetes config: {helm_dir or kustomize}")
            scores["infrastructure"] = scores.get("infrastructure", 0) + 4

        # ── Data Pipeline ────────────────────────────────────────────────
        data_deps = {
            "airflow", "apache-airflow", "prefect", "dagster", "luigi",
            "dbt-core", "dbt",
            "pyspark", "apache-spark",
            "pandas", "polars",
            "great-expectations", "great_expectations",
        }
        found_data = deps & data_deps
        if found_data:
            signals.append(f"Data tools: {', '.join(found_data)}")
            scores["data_pipeline"] = scores.get("data_pipeline", 0) + 4

        dags_dir = self._dir_exists("dags", "pipelines", "etl")
        dbt_dir = self._dir_exists("models", "dbt")
        if dags_dir:
            signals.append(f"Pipeline directory: {dags_dir}/")
            scores["data_pipeline"] = scores.get("data_pipeline", 0) + 4
        if dbt_dir and self._file_exists(r"dbt_project\.yml$"):
            signals.append("dbt project")
            scores["data_pipeline"] = scores.get("data_pipeline", 0) + 5

        # ── ML / AI Application ──────────────────────────────────────────
        ml_deps = {
            "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
            "transformers", "torch", "pytorch", "tensorflow", "keras", "jax",
            "mlflow", "wandb", "optuna", "ray",
            "sentence-transformers", "huggingface-hub",
        }
        found_ml = deps & ml_deps
        if found_ml:
            signals.append(f"ML/AI libraries: {', '.join(found_ml)}")
            scores["ml_ai"] = scores.get("ml_ai", 0) + 5

        notebooks = self._files_matching(r".*\.ipynb$")
        if notebooks:
            signals.append(f"{len(notebooks)} Jupyter notebook(s)")
            scores["ml_ai"] = scores.get("ml_ai", 0) + 2

        model_dir = self._dir_exists("models", "model", "checkpoints", "weights")
        if model_dir and found_ml:
            signals.append(f"Model directory: {model_dir}/")
            scores["ml_ai"] = scores.get("ml_ai", 0) + 2

        # ── Mobile Application ───────────────────────────────────────────
        mobile_deps = {"react-native", "expo", "flutter", "@ionic/core", "capacitor"}
        found_mobile = deps & mobile_deps
        if found_mobile:
            signals.append(f"Mobile framework: {', '.join(found_mobile)}")
            scores["mobile_app"] = scores.get("mobile_app", 0) + 6

        ios_dir = self._dir_exists("ios", "macos")
        android_dir = self._dir_exists("android")
        if ios_dir or android_dir:
            signals.append(f"Mobile platforms: {', '.join(filter(None, [ios_dir, android_dir]))}")
            scores["mobile_app"] = scores.get("mobile_app", 0) + 4

        flutter = self._file_exists(r"pubspec\.ya?ml$")
        if flutter:
            signals.append("Flutter project (pubspec.yaml)")
            scores["mobile_app"] = scores.get("mobile_app", 0) + 6

        # ── Static Site ──────────────────────────────────────────────────
        static_generators = {
            "gatsby", "hugo", "jekyll", "eleventy", "@11ty/eleventy",
            "astro", "vitepress", "docusaurus", "mkdocs",
        }
        found_static = deps & static_generators
        if found_static:
            signals.append(f"Static site generator: {', '.join(found_static)}")
            scores["static_site"] = scores.get("static_site", 0) + 6

        jekyll_config = self._file_exists(r"_config\.ya?ml$")
        hugo_config = self._file_exists(r"hugo\.(toml|yaml|json)$")
        mkdocs_config = self._file_exists(r"mkdocs\.ya?ml$")
        if jekyll_config or hugo_config or mkdocs_config:
            signals.append(f"Static site config: {jekyll_config or hugo_config or mkdocs_config}")
            scores["static_site"] = scores.get("static_site", 0) + 5

        # ── Desktop Application ──────────────────────────────────────────
        desktop_deps = {
            "electron", "tauri", "pyqt5", "pyqt6", "pyside6",
            "tkinter", "wxpython", "kivy", "flet",
        }
        found_desktop = deps & desktop_deps
        if found_desktop:
            signals.append(f"Desktop framework: {', '.join(found_desktop)}")
            scores["desktop_app"] = scores.get("desktop_app", 0) + 6

        electron_config = self._file_exists(r"electron\.js$", r"electron-builder\.ya?ml$")
        tauri_config = self._file_exists(r"tauri\.conf\.json$")
        if electron_config or tauri_config:
            signals.append(f"Desktop config: {electron_config or tauri_config}")
            scores["desktop_app"] = scores.get("desktop_app", 0) + 4

        # ── Monorepo ─────────────────────────────────────────────────────
        monorepo_markers = {
            "lerna", "nx", "@nrwl/workspace", "turborepo",
        }
        found_mono = deps & monorepo_markers
        if found_mono:
            signals.append(f"Monorepo tool: {', '.join(found_mono)}")
            scores["monorepo"] = scores.get("monorepo", 0) + 6

        workspaces_dir = self._dir_exists("packages", "apps", "services", "libs")
        lerna_json = self._file_exists(r"lerna\.json$", r"nx\.json$", r"turbo\.json$", r"pnpm-workspace\.yaml$")
        if lerna_json:
            signals.append(f"Monorepo config: {lerna_json}")
            scores["monorepo"] = scores.get("monorepo", 0) + 5
        elif workspaces_dir:
            # Only count if there's evidence of multiple sub-projects
            sub_pkg = self._files_matching(r"(packages|apps|services)/[^/]+/package\.json$")
            sub_pyproject = self._files_matching(r"(packages|apps|services)/[^/]+/pyproject\.toml$")
            if len(sub_pkg) + len(sub_pyproject) >= 2:
                signals.append(f"Multiple sub-projects in {workspaces_dir}/")
                scores["monorepo"] = scores.get("monorepo", 0) + 4

        # ── Determine primary type ───────────────────────────────────────
        if not scores:
            return {
                "primary_type": "unknown",
                "primary_label": self.APPLICATION_TYPES["unknown"],
                "confidence": 0,
                "all_types": [],
                "signals": signals or ["No recognisable application patterns detected"],
            }

        max_score = max(scores.values())
        primary = max(scores, key=scores.get)

        # Calculate confidence as ratio of top score to total
        total = sum(scores.values())
        confidence = round((max_score / total) * 100) if total > 0 else 0

        # Build ranked list of all detected types
        all_types = sorted(
            [
                {"type": t, "label": self.APPLICATION_TYPES.get(t, t), "score": s}
                for t, s in scores.items()
                if s > 0
            ],
            key=lambda x: x["score"],
            reverse=True,
        )

        return {
            "primary_type": primary,
            "primary_label": self.APPLICATION_TYPES.get(primary, primary),
            "confidence": confidence,
            "all_types": all_types,
            "signals": signals,
        }
