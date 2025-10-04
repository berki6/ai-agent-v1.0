import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class CICDPipelineManager:
    """Manages CI/CD pipeline templates for different platforms"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "ci_cd_templates"
        self.templates_dir.mkdir(exist_ok=True)

    def get_available_platforms(self) -> List[str]:
        """Get list of supported CI/CD platforms"""
        return ["github-actions", "gitlab-ci", "jenkins", "circleci"]

    def generate_pipeline(
        self,
        platform: str,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        deployment_targets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate CI/CD pipeline configuration for the specified platform"""

        features = features or []
        deployment_targets = deployment_targets or []

        if platform == "github-actions":
            return self._generate_github_actions(
                language, framework, features, deployment_targets
            )
        elif platform == "gitlab-ci":
            return self._generate_gitlab_ci(
                language, framework, features, deployment_targets
            )
        elif platform == "jenkins":
            return self._generate_jenkins(
                language, framework, features, deployment_targets
            )
        elif platform == "circleci":
            return self._generate_circleci(
                language, framework, features, deployment_targets
            )
        else:
            raise ValueError(f"Unsupported CI/CD platform: {platform}")

    def _generate_github_actions(
        self,
        language: str,
        framework: Optional[str],
        features: List[str],
        deployment_targets: List[str],
    ) -> Dict[str, Any]:
        """Generate GitHub Actions workflow"""

        workflow = {
            "name": "CI/CD Pipeline",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main"]},
            },
            "jobs": {},
        }

        # Test job
        test_job = {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Set up Python",
                    "uses": "actions/setup-python@v4",
                    "with": {"python-version": "3.9"},
                },
            ],
        }

        if language == "python":
            test_job["steps"].extend(
                [
                    {
                        "name": "Install dependencies",
                        "run": "pip install -r requirements.txt",
                    },
                    {"name": "Run tests", "run": "pytest --cov=. --cov-report=xml"},
                ]
            )

            if "testing" in features:
                test_job["steps"].append(
                    {
                        "name": "Upload coverage",
                        "uses": "codecov/codecov-action@v3",
                        "with": {"file": "./coverage.xml"},
                    }
                )

        elif language in ["javascript", "typescript"]:
            test_job["steps"].extend(
                [
                    {
                        "name": "Setup Node.js",
                        "uses": "actions/setup-node@v4",
                        "with": {"node-version": "18"},
                    },
                    {"name": "Install dependencies", "run": "npm ci"},
                    {"name": "Run tests", "run": "npm test"},
                ]
            )

        workflow["jobs"]["test"] = test_job

        # Lint job
        if "linting" in features or language in ["python", "javascript", "typescript"]:
            lint_job = {
                "runs-on": "ubuntu-latest",
                "steps": [{"uses": "actions/checkout@v4"}],
            }

            if language == "python":
                lint_job["steps"].extend(
                    [
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.9"},
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install black isort mypy",
                        },
                        {"name": "Run Black", "run": "black --check ."},
                        {"name": "Run isort", "run": "isort --check-only ."},
                        {"name": "Run mypy", "run": "mypy ."},
                    ]
                )
            elif language in ["javascript", "typescript"]:
                lint_job["steps"].extend(
                    [
                        {
                            "name": "Setup Node.js",
                            "uses": "actions/setup-node@v4",
                            "with": {"node-version": "18"},
                        },
                        {"name": "Install dependencies", "run": "npm ci"},
                        {"name": "Run ESLint", "run": "npm run lint"},
                    ]
                )

            workflow["jobs"]["lint"] = lint_job

        # Deployment jobs
        for target in deployment_targets:
            if target == "docker":
                deploy_job = {
                    "runs-on": "ubuntu-latest",
                    "needs": ["test"],
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Build Docker image",
                            "run": "docker build -t myapp .",
                        },
                        {"name": "Push to Docker Hub", "run": "docker push myapp"},
                    ],
                }
                workflow["jobs"]["deploy-docker"] = deploy_job

            elif target == "aws":
                deploy_job = {
                    "runs-on": "ubuntu-latest",
                    "needs": ["test"],
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {
                            "name": "Configure AWS",
                            "uses": "aws-actions/configure-aws-credentials@v4",
                        },
                        {
                            "name": "Deploy to AWS",
                            "run": "aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment",
                        },
                    ],
                }
                workflow["jobs"]["deploy-aws"] = deploy_job

        return {
            "platform": "github-actions",
            "files": {
                ".github/workflows/ci-cd.yml": {
                    "content": self._yaml_dump(workflow),
                    "description": "GitHub Actions CI/CD workflow",
                }
            },
        }

    def _generate_gitlab_ci(
        self,
        language: str,
        framework: Optional[str],
        features: List[str],
        deployment_targets: List[str],
    ) -> Dict[str, Any]:
        """Generate GitLab CI configuration"""

        pipeline = {
            "stages": ["test", "lint", "build", "deploy"],
            "variables": {"DOCKER_DRIVER": "overlay2"},
        }

        # Test job
        test_job = {
            "stage": "test",
            "image": "python:3.9" if language == "python" else "node:18",
            "script": [],
        }

        if language == "python":
            test_job["script"].extend(
                ["pip install -r requirements.txt", "pytest --cov=. --cov-report=xml"]
            )
        elif language in ["javascript", "typescript"]:
            test_job["script"].extend(["npm ci", "npm test"])

        pipeline["test"] = test_job

        # Lint job
        if "linting" in features:
            lint_job = {
                "stage": "lint",
                "image": "python:3.9" if language == "python" else "node:18",
                "script": [],
            }

            if language == "python":
                lint_job["script"].extend(
                    [
                        "pip install black isort mypy",
                        "black --check .",
                        "isort --check-only .",
                        "mypy .",
                    ]
                )
            elif language in ["javascript", "typescript"]:
                lint_job["script"].extend(["npm ci", "npm run lint"])

            pipeline["lint"] = lint_job

        # Build job
        if "docker" in deployment_targets:
            build_job = {
                "stage": "build",
                "image": "docker:latest",
                "services": ["docker:dind"],
                "script": [
                    "docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG .",
                    "docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG",
                ],
            }
            pipeline["build"] = build_job

        # Deploy jobs
        for target in deployment_targets:
            if target == "kubernetes":
                deploy_job = {
                    "stage": "deploy",
                    "image": "google/cloud-sdk:alpine",
                    "script": [
                        "echo $GCLOUD_SERVICE_KEY | base64 -d > key.json",
                        "gcloud auth activate-service-account --key-file key.json",
                        "gcloud container clusters get-credentials my-cluster",
                        "kubectl apply -f k8s/",
                    ],
                }
                pipeline["deploy:k8s"] = deploy_job

        return {
            "platform": "gitlab-ci",
            "files": {
                ".gitlab-ci.yml": {
                    "content": self._yaml_dump(pipeline),
                    "description": "GitLab CI/CD pipeline configuration",
                }
            },
        }

    def _generate_jenkins(
        self,
        language: str,
        framework: Optional[str],
        features: List[str],
        deployment_targets: List[str],
    ) -> Dict[str, Any]:
        """Generate Jenkins pipeline"""

        pipeline_script = f"""
pipeline {{
    agent any

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Test') {{
            steps {{
"""

        if language == "python":
            pipeline_script += """
                sh 'pip install -r requirements.txt'
                sh 'pytest --cov=. --cov-report=xml'
"""
        elif language in ["javascript", "typescript"]:
            pipeline_script += """
                sh 'npm ci'
                sh 'npm test'
"""

        pipeline_script += """
            }
        }
"""

        if "linting" in features:
            pipeline_script += """
        stage('Lint') {
            steps {
"""
            if language == "python":
                pipeline_script += """
                sh 'pip install black isort mypy'
                sh 'black --check .'
                sh 'isort --check-only .'
                sh 'mypy .'
"""
            elif language in ["javascript", "typescript"]:
                pipeline_script += """
                sh 'npm ci'
                sh 'npm run lint'
"""

            pipeline_script += """
            }
        }
"""

        for target in deployment_targets:
            if target == "docker":
                pipeline_script += """
        stage('Build Docker') {
            steps {
                sh 'docker build -t myapp .'
                sh 'docker push myapp'
            }
        }
"""

        pipeline_script += """
    }

    post {
        always {
            junit '**/test-results.xml'
        }
    }
}
"""

        return {
            "platform": "jenkins",
            "files": {
                "Jenkinsfile": {
                    "content": pipeline_script,
                    "description": "Jenkins pipeline configuration",
                }
            },
        }

    def _generate_circleci(
        self,
        language: str,
        framework: Optional[str],
        features: List[str],
        deployment_targets: List[str],
    ) -> Dict[str, Any]:
        """Generate CircleCI configuration"""

        config = {
            "version": 2.1,
            "jobs": {},
            "workflows": {"build_and_deploy": {"jobs": []}},
        }

        # Test job
        test_job = {
            "docker": [
                {"image": "cimg/python:3.9" if language == "python" else "cimg/node:18"}
            ],
            "steps": ["checkout", {"run": {"name": "Install dependencies"}}],
        }

        if language == "python":
            test_job["steps"][1]["run"]["command"] = "pip install -r requirements.txt"
            test_job["steps"].extend(
                [
                    {
                        "run": {
                            "name": "Run tests",
                            "command": "pytest --cov=. --cov-report=xml",
                        }
                    },
                    {"store_test_results": {"path": "test-results"}},
                    {"store_artifacts": {"path": "coverage.xml"}},
                ]
            )
        elif language in ["javascript", "typescript"]:
            test_job["steps"][1]["run"]["command"] = "npm ci"
            test_job["steps"].extend(
                [
                    {"run": {"name": "Run tests", "command": "npm test"}},
                    {"store_test_results": {"path": "test-results"}},
                    {"store_artifacts": {"path": "coverage"}},
                ]
            )

        config["jobs"]["test"] = test_job
        config["workflows"]["build_and_deploy"]["jobs"].append("test")

        # Lint job
        if "linting" in features:
            lint_job = {
                "docker": [
                    {
                        "image": (
                            "cimg/python:3.9"
                            if language == "python"
                            else "cimg/node:18"
                        )
                    }
                ],
                "steps": ["checkout"],
            }

            if language == "python":
                lint_job["steps"].extend(
                    [
                        {
                            "run": {
                                "name": "Install linting tools",
                                "command": "pip install black isort mypy",
                            }
                        },
                        {"run": {"name": "Run Black", "command": "black --check ."}},
                        {
                            "run": {
                                "name": "Run isort",
                                "command": "isort --check-only .",
                            }
                        },
                        {"run": {"name": "Run mypy", "command": "mypy ."}},
                    ]
                )
            elif language in ["javascript", "typescript"]:
                lint_job["steps"].extend(
                    [
                        {"run": {"name": "Install dependencies", "command": "npm ci"}},
                        {"run": {"name": "Run ESLint", "command": "npm run lint"}},
                    ]
                )

            config["jobs"]["lint"] = lint_job
            config["workflows"]["build_and_deploy"]["jobs"].append("lint")

        # Deployment jobs
        for target in deployment_targets:
            if target == "heroku":
                deploy_job = {
                    "docker": [{"image": "cimg/node:18"}],
                    "steps": [
                        "checkout",
                        {
                            "run": {
                                "name": "Deploy to Heroku",
                                "command": "git push heroku main",
                            }
                        },
                    ],
                }
                config["jobs"]["deploy-heroku"] = deploy_job
                config["workflows"]["build_and_deploy"]["jobs"].append(
                    {"deploy-heroku": {"requires": ["test"]}}
                )

        return {
            "platform": "circleci",
            "files": {
                ".circleci/config.yml": {
                    "content": self._yaml_dump(config),
                    "description": "CircleCI pipeline configuration",
                }
            },
        }

    def _yaml_dump(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to YAML string (simplified)"""
        # In a real implementation, use PyYAML
        return json.dumps(data, indent=2).replace('"', "").replace(",", "")
