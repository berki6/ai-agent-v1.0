import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class ContainerizationManager:
    """Manages containerization and deployment configurations"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "deployment_templates"
        self.templates_dir.mkdir(exist_ok=True)

    def generate_docker_config(
        self,
        language: str,
        framework: Optional[str] = None,
        project_name: str = "app",
        port: int = 8000,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate Docker and docker-compose configurations"""

        features = features or []

        dockerfile = self._generate_dockerfile(language, framework, features)
        docker_compose = self._generate_docker_compose(project_name, port, features)

        return {
            "docker": {
                "Dockerfile": {
                    "content": dockerfile,
                    "description": "Docker container configuration",
                },
                "docker-compose.yml": {
                    "content": docker_compose,
                    "description": "Docker Compose orchestration",
                },
            }
        }

    def generate_kubernetes_manifests(
        self,
        project_name: str,
        port: int = 8000,
        replicas: int = 3,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate Kubernetes deployment manifests"""

        features = features or []

        deployment = self._generate_k8s_deployment(
            project_name, port, replicas, features
        )
        service = self._generate_k8s_service(project_name, port)
        ingress = self._generate_k8s_ingress(project_name)

        return {
            "kubernetes": {
                "k8s/deployment.yml": {
                    "content": deployment,
                    "description": "Kubernetes deployment manifest",
                },
                "k8s/service.yml": {
                    "content": service,
                    "description": "Kubernetes service manifest",
                },
                "k8s/ingress.yml": {
                    "content": ingress,
                    "description": "Kubernetes ingress configuration",
                },
            }
        }

    def generate_cloud_deployment(
        self,
        cloud_provider: str,
        project_name: str,
        region: str = "us-east-1",
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate cloud-specific deployment configurations"""

        features = features or []

        if cloud_provider == "aws":
            return self._generate_aws_deployment(project_name, region, features)
        elif cloud_provider == "gcp":
            return self._generate_gcp_deployment(project_name, region, features)
        elif cloud_provider == "azure":
            return self._generate_azure_deployment(project_name, region, features)
        else:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")

    def _generate_dockerfile(
        self, language: str, framework: Optional[str], features: List[str]
    ) -> str:
        """Generate Dockerfile based on language and framework"""

        if language == "python":
            return self._generate_python_dockerfile(framework, features)
        elif language in ["javascript", "typescript"]:
            return self._generate_nodejs_dockerfile(framework, features)
        else:
            return self._generate_generic_dockerfile(language)

    def _generate_python_dockerfile(
        self, framework: Optional[str], features: List[str]
    ) -> str:
        """Generate Python-specific Dockerfile"""

        dockerfile = """# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
"""

        if "database" in features:
            dockerfile += """
# Install database dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*
"""

        dockerfile += """
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
"""

        if framework == "fastapi":
            dockerfile += (
                'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'
            )
        elif framework == "django":
            dockerfile += 'CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]'
        else:
            dockerfile += 'CMD ["python", "main.py"]'

        return dockerfile

    def _generate_nodejs_dockerfile(
        self, framework: Optional[str], features: List[str]
    ) -> str:
        """Generate Node.js-specific Dockerfile"""

        dockerfile = """# Use Node.js LTS image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache git

# Copy package files first for better caching
COPY package*.json ./
"""

        if "database" in features:
            dockerfile += """
# Install database dependencies
RUN apk add --no-cache postgresql-client
"""

        dockerfile += """
# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:3000/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

# Run application
"""

        if framework == "react":
            dockerfile += 'CMD ["npm", "start"]'
        elif framework == "express":
            dockerfile += 'CMD ["node", "server.js"]'
        else:
            dockerfile += 'CMD ["node", "index.js"]'

        return dockerfile

    def _generate_generic_dockerfile(self, language: str) -> str:
        """Generate generic Dockerfile for unsupported languages"""
        return f"""# Generic Dockerfile for {language}
FROM ubuntu:20.04

# Install {language} runtime
# NOTE: Please customize this Dockerfile for your specific {language} setup

WORKDIR /app
COPY . /app

# Add your runtime command here
CMD ["echo", "Please customize Dockerfile for {language}"]
"""

    def _generate_docker_compose(
        self, project_name: str, port: int, features: List[str]
    ) -> str:
        """Generate docker-compose.yml"""

        compose = {
            "version": "3.8",
            "services": {
                "app": {
                    "build": ".",
                    "ports": [f"{port}:{port}"],
                    "environment": ["NODE_ENV=production", "PORT=8000"],
                    "restart": "unless-stopped",
                }
            },
        }

        # Add database service if needed
        if "database" in features:
            compose["services"]["db"] = {
                "image": "postgres:15-alpine",
                "environment": [
                    "POSTGRES_DB=${POSTGRES_DB:-app}",
                    "POSTGRES_USER=${POSTGRES_USER:-user}",
                    "POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}",
                ],
                "volumes": ["postgres_data:/var/lib/postgresql/data"],
                "restart": "unless-stopped",
            }

            # Add database dependency to app
            compose["services"]["app"]["depends_on"] = ["db"]
            compose["services"]["app"]["environment"].extend(
                ["DATABASE_URL=postgresql://user:password@db:5432/app"]
            )

        # Add Redis if caching is needed
        if "redis" in features or "caching" in features:
            compose["services"]["redis"] = {
                "image": "redis:7-alpine",
                "restart": "unless-stopped",
            }
            compose["services"]["app"]["depends_on"] = compose["services"]["app"].get(
                "depends_on", []
            ) + ["redis"]

        # Add volumes
        if "database" in features:
            compose["volumes"] = {"postgres_data": {}}

        # Add networks if multiple services
        if len(compose["services"]) > 1:
            compose["networks"] = {"default": {"driver": "bridge"}}

        return self._yaml_dump(compose)

    def _generate_k8s_deployment(
        self, project_name: str, port: int, replicas: int, features: List[str]
    ) -> str:
        """Generate Kubernetes deployment manifest"""

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": project_name, "labels": {"app": project_name}},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": project_name}},
                "template": {
                    "metadata": {"labels": {"app": project_name}},
                    "spec": {
                        "containers": [
                            {
                                "name": project_name,
                                "image": f"{project_name}:latest",
                                "ports": [{"containerPort": port}],
                                "env": [
                                    {"name": "PORT", "value": str(port)},
                                    {"name": "NODE_ENV", "value": "production"},
                                ],
                                "resources": {
                                    "requests": {"memory": "128Mi", "cpu": "100m"},
                                    "limits": {"memory": "512Mi", "cpu": "500m"},
                                },
                                "livenessProbe": {
                                    "httpGet": {"path": "/health", "port": port},
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/health", "port": port},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5,
                                },
                            }
                        ]
                    },
                },
            },
        }

        # Add database environment variables
        if "database" in features:
            deployment["spec"]["template"]["spec"]["containers"][0]["env"].extend(
                [
                    {
                        "name": "DATABASE_URL",
                        "valueFrom": {
                            "secretKeyRef": {
                                "name": f"{project_name}-db-secret",
                                "key": "database_url",
                            }
                        },
                    }
                ]
            )

        return self._yaml_dump(deployment)

    def _generate_k8s_service(self, project_name: str, port: int) -> str:
        """Generate Kubernetes service manifest"""

        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{project_name}-service",
                "labels": {"app": project_name},
            },
            "spec": {
                "selector": {"app": project_name},
                "ports": [
                    {
                        "name": "http",
                        "port": port,
                        "targetPort": port,
                        "protocol": "TCP",
                    }
                ],
                "type": "ClusterIP",
            },
        }

        return self._yaml_dump(service)

    def _generate_k8s_ingress(self, project_name: str) -> str:
        """Generate Kubernetes ingress configuration"""

        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{project_name}-ingress",
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                },
            },
            "spec": {
                "tls": [
                    {
                        "hosts": [f"{project_name}.example.com"],
                        "secretName": f"{project_name}-tls",
                    }
                ],
                "rules": [
                    {
                        "host": f"{project_name}.example.com",
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": f"{project_name}-service",
                                            "port": {"number": 80},
                                        }
                                    },
                                }
                            ]
                        },
                    }
                ],
            },
        }

        return self._yaml_dump(ingress)

    def _generate_aws_deployment(
        self, project_name: str, region: str, features: List[str]
    ) -> Dict[str, Any]:
        """Generate AWS deployment configurations"""

        files = {}

        # ECS Task Definition
        task_def = {
            "family": f"{project_name}-task",
            "taskRoleArn": f"arn:aws:iam::{self._get_account_id()}:role/{project_name}-task-role",
            "executionRoleArn": f"arn:aws:iam::{self._get_account_id()}:role/{project_name}-execution-role",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "256",
            "memory": "512",
            "containerDefinitions": [
                {
                    "name": project_name,
                    "image": f"{self._get_account_id()}.dkr.ecr.{region}.amazonaws.com/{project_name}:latest",
                    "essential": True,
                    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
                    "environment": [{"name": "NODE_ENV", "value": "production"}],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{project_name}",
                            "awslogs-region": region,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                }
            ],
        }

        files["aws/ecs-task-definition.json"] = {
            "content": json.dumps(task_def, indent=2),
            "description": "AWS ECS Task Definition",
        }

        # CloudFormation template
        cf_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"CloudFormation template for {project_name}",
            "Parameters": {
                "VpcId": {"Type": "AWS::EC2::VPC::Id", "Description": "VPC ID"},
                "SubnetIds": {
                    "Type": "CommaDelimitedList",
                    "Description": "Subnet IDs",
                },
            },
            "Resources": {
                "ECSCluster": {
                    "Type": "AWS::ECS::Cluster",
                    "Properties": {"ClusterName": f"{project_name}-cluster"},
                },
                "ECSTaskDefinition": {
                    "Type": "AWS::ECS::TaskDefinition",
                    "Properties": task_def,
                },
            },
        }

        files["aws/cloudformation.yml"] = {
            "content": self._yaml_dump(cf_template),
            "description": "AWS CloudFormation template",
        }

        return {"aws": files}

    def _generate_gcp_deployment(
        self, project_name: str, region: str, features: List[str]
    ) -> Dict[str, Any]:
        """Generate GCP deployment configurations"""

        files = {}

        # Cloud Run service
        cloud_run = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": project_name,
                "annotations": {"run.googleapis.com/ingress": "all"},
            },
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "autoscaling.knative.dev/maxScale": "10",
                            "run.googleapis.com/cpu-throttling": "false",
                            "run.googleapis.com/startup-cpu-boost": "true",
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "image": f"gcr.io/{project_name}/{project_name}:latest",
                                "ports": [{"containerPort": 8000}],
                                "resources": {
                                    "limits": {"cpu": "1000m", "memory": "512Mi"}
                                },
                                "env": [{"name": "NODE_ENV", "value": "production"}],
                            }
                        ]
                    },
                }
            },
        }

        files["gcp/cloud-run.yml"] = {
            "content": self._yaml_dump(cloud_run),
            "description": "Google Cloud Run service configuration",
        }

        # Cloud Build configuration
        cloud_build = {
            "steps": [
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "build",
                        "-t",
                        f"gcr.io/$PROJECT_ID/{project_name}:$COMMIT_SHA",
                        ".",
                    ],
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["push", f"gcr.io/$PROJECT_ID/{project_name}:$COMMIT_SHA"],
                },
                {
                    "name": "gcr.io/google.com/cloudsdktool/cloud-sdk",
                    "args": [
                        "run",
                        "deploy",
                        project_name,
                        "--image",
                        f"gcr.io/$PROJECT_ID/{project_name}:$COMMIT_SHA",
                        "--region",
                        region,
                        "--platform",
                        "managed",
                        "--allow-unauthenticated",
                    ],
                },
            ]
        }

        files["gcp/cloudbuild.yml"] = {
            "content": self._yaml_dump(cloud_build),
            "description": "Google Cloud Build configuration",
        }

        return {"gcp": files}

    def _generate_azure_deployment(
        self, project_name: str, region: str, features: List[str]
    ) -> Dict[str, Any]:
        """Generate Azure deployment configurations"""

        files = {}

        # Azure Container Apps
        container_app = {
            "location": region,
            "properties": {
                "configuration": {
                    "activeRevisionsMode": "Single",
                    "ingress": {
                        "external": True,
                        "targetPort": 8000,
                        "transport": "Auto",
                    },
                },
                "template": {
                    "containers": [
                        {
                            "image": f"{project_name}:latest",
                            "name": project_name,
                            "resources": {"cpu": 0.5, "memory": "1Gi"},
                        }
                    ],
                    "scale": {"minReplicas": 1, "maxReplicas": 10},
                },
            },
        }

        files["azure/container-app.yml"] = {
            "content": self._yaml_dump(container_app),
            "description": "Azure Container App configuration",
        }

        # Azure DevOps pipeline
        azure_pipeline = {
            "trigger": {"branches": {"include": ["main"]}},
            "pool": {"vmImage": "ubuntu-latest"},
            "steps": [
                {
                    "task": "Docker@2",
                    "inputs": {
                        "command": "build",
                        "repository": f"{project_name}",
                        "tags": "$(Build.BuildId)",
                    },
                },
                {
                    "task": "Docker@2",
                    "inputs": {
                        "command": "push",
                        "repository": f"{project_name}",
                        "tags": "$(Build.BuildId)",
                    },
                },
                {
                    "task": "AzureContainerApps@1",
                    "inputs": {
                        "appSourcePath": "$(System.DefaultWorkingDirectory)",
                        "azureSubscription": "azure-subscription",
                        "containerAppName": project_name,
                        "resourceGroup": f"{project_name}-rg",
                        "imageToDeploy": f"{project_name}:(Build.BuildId)",
                    },
                },
            ],
        }

        files["azure/azure-pipelines.yml"] = {
            "content": self._yaml_dump(azure_pipeline),
            "description": "Azure DevOps pipeline configuration",
        }

        return {"azure": files}

    def _get_account_id(self) -> str:
        """Get AWS account ID (placeholder)"""
        return "${AWS::Account}"

    def _yaml_dump(self, data: Dict[str, Any]) -> str:
        """Convert dictionary to YAML string (simplified)"""
        # In a real implementation, use PyYAML
        return json.dumps(data, indent=2).replace('"', "").replace(",", "")
