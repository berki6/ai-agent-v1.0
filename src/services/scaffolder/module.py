import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil

from src.core.base_module import BaseModule, ModuleConfig, ModuleResult
from src.core.ai_utils import AIUtils
from .template_manager import TemplateManager
from .dependency_manager import DependencyManager
from .ci_cd_manager import CICDPipelineManager
from .containerization_manager import ContainerizationManager
from .environment_manager import EnvironmentManager
from .security_manager import SecurityManager, AuthType, SecurityFeature
from .testing_manager import TestingManager, TestFramework, TestType
from .observability_manager import (
    ObservabilityManager,
    MonitoringType,
    LoggingType,
    TracingType,
    ObservabilityFeature,
)
from .database_manager import (
    DatabaseManager,
    DatabaseType,
    MigrationTool,
    ORMType,
    DatabaseFeature,
    DatabaseConfig,
)
from .api_documentation_manager import (
    APIDocumentationManager,
    DocumentationFormat,
    DocumentationTool,
    APIFramework,
    DocumentationFeature,
    APIEndpoint,
)
from .code_quality_manager import (
    CodeQualityManager,
    LinterType,
    FormatterType,
    TypeCheckerType,
    CodeQualityTool,
    QualityFeature,
    CodeQualityConfig,
)
from .project_management_manager import (
    ProjectManagementManager,
    ValidationType,
    ProjectHealth,
    DependencyCheck,
    ConfigurationValidation,
    ProjectManagementFeature,
    ProjectManagementConfig,
)


class ProjectScaffolderConfig(ModuleConfig):
    """Configuration for AI Project Scaffolder"""

    name: str = "scaffolder"
    project_name: str
    project_type: str  # web, api, cli, library, etc.
    language: str  # python, javascript, typescript, etc.
    framework: Optional[str] = None  # fastapi, react, django, etc.
    features: List[str] = []  # authentication, database, testing, etc.
    output_directory: str = "."
    initialize_git: bool = True
    create_readme: bool = True
    create_dockerfile: bool = False
    use_template: bool = True  # Whether to use predefined templates
    check_vulnerabilities: bool = (
        True  # Whether to check for dependency vulnerabilities
    )
    resolve_conflicts: bool = True  # Whether to resolve dependency conflicts
    ci_cd_platforms: List[str] = (
        []
    )  # CI/CD platforms to generate (github-actions, gitlab-ci, jenkins, circleci)
    deployment_targets: List[str] = (
        []
    )  # Deployment targets (docker, aws, kubernetes, heroku)
    containerization: bool = True  # Whether to generate containerization configs
    cloud_providers: List[str] = []  # Cloud providers (aws, gcp, azure)
    kubernetes_replicas: int = 3  # Number of Kubernetes replicas
    environment_management: bool = True  # Whether to generate environment configs
    config_formats: List[str] = [
        "env",
        "json",
    ]  # Configuration formats (env, json, yaml, toml)
    include_secrets: bool = True  # Whether to include secret management
    security_enabled: bool = True  # Whether to generate security features
    auth_type: str = "jwt"  # Authentication type (jwt, oauth2, basic, api_key, session)
    security_features: List[str] = [
        "authentication",
        "input_validation",
        "security_headers",
        "cors",
    ]  # Security features to enable
    testing_enabled: bool = True  # Whether to generate testing setup
    test_framework: str = "pytest"  # Testing framework (pytest, unittest, jest, etc.)
    test_types: List[str] = ["unit", "integration"]  # Types of tests to generate
    include_coverage: bool = True  # Whether to include test coverage
    ci_testing_integration: bool = True  # Whether to include CI testing integration
    observability_enabled: bool = True  # Whether to generate observability setup
    monitoring_type: str = (
        "prometheus"  # Monitoring type (prometheus, grafana, datadog, etc.)
    )
    logging_type: str = "elk"  # Logging type (elk, efk, loki, etc.)
    tracing_type: str = "jaeger"  # Tracing type (jaeger, zipkin, opentelemetry, etc.)
    observability_features: List[str] = [
        "monitoring",
        "logging",
        "tracing",
        "metrics",
        "health_checks",
    ]  # Observability features to enable
    database_enabled: bool = True  # Whether to generate database setup
    database_type: str = (
        "postgresql"  # Database type (postgresql, mysql, mongodb, redis, sqlite)
    )
    orm_type: str = (
        "sqlalchemy"  # ORM type (sqlalchemy, django_orm, mongoengine, pymongo, redis_py)
    )
    migration_tool: str = (
        "alembic"  # Migration tool (alembic, flyway, liquibase, mongoose)
    )
    database_features: List[str] = [
        "connection_pooling",
        "migrations",
        "seeding",
        "backup_restore",
    ]  # Database features to enable
    database_host: str = "localhost"  # Database host
    database_port: int = 5432  # Database port
    database_name: str = "myapp"  # Database name
    database_user: str = "myuser"  # Database username
    database_password: str = "mypassword"  # Database password
    api_documentation_enabled: bool = True  # Whether to generate API documentation
    api_framework: str = (
        "fastapi"  # API framework (fastapi, flask, django_rest, express, nestjs, spring_boot)
    )
    documentation_formats: List[str] = [
        "openapi_json",
        "openapi_yaml",
        "postman_collection",
    ]  # Documentation formats to generate
    documentation_tools: List[str] = [
        "swagger_ui",
        "redoc",
    ]  # Documentation tools to include
    documentation_features: List[str] = [
        "interactive_docs",
        "schema_validation",
        "authentication_docs",
        "error_responses",
        "examples",
    ]  # Documentation features to enable
    api_title: str = "API Documentation"  # API documentation title
    api_version: str = "1.0.0"  # API version
    api_description: str = (
        "API documentation generated by Scaffolder"  # API description
    )
    code_quality_enabled: bool = True  # Whether to generate code quality setup
    linters: List[str] = [
        "flake8"
    ]  # Linters to configure (flake8, pylint, eslint, etc.)
    formatters: List[str] = ["black", "isort"]  # Code formatters to configure
    type_checkers: List[str] = ["mypy"]  # Type checkers to configure
    quality_tools: List[str] = [
        "pre_commit",
        "editorconfig",
        "gitignore",
    ]  # Code quality tools to include
    quality_features: List[str] = [
        "ci_integration",
        "pre_commit_hooks",
    ]  # Code quality features to enable
    max_line_length: int = 120  # Maximum line length for code formatting
    target_python_version: str = "3.8"  # Target Python version for type checking
    strict_type_checking: bool = True  # Enable strict type checking
    include_docstring_checking: bool = True  # Include docstring checking
    auto_fix_on_commit: bool = False  # Auto-fix issues on commit
    project_management_enabled: bool = (
        True  # Whether to generate project management setup
    )
    validation_types: List[str] = [
        "structure",
        "dependencies",
        "configuration",
    ]  # Types of validation to perform
    dependency_checks: List[str] = [
        "vulnerabilities",
        "outdated",
        "conflicts",
    ]  # Dependency checking types
    config_validations: List[str] = [
        "syntax",
        "schema",
        "environment",
    ]  # Configuration validation types
    management_features: List[str] = [
        "structure_validation",
        "dependency_audit",
        "config_validation",
        "health_monitoring",
    ]  # Project management features to enable
    enable_structure_validation: bool = True  # Enable project structure validation
    enable_dependency_checking: bool = True  # Enable dependency checking
    enable_config_validation: bool = True  # Enable configuration validation
    enable_health_monitoring: bool = True  # Enable project health monitoring
    enable_compliance_checking: bool = False  # Enable compliance checking
    enable_automated_fixes: bool = False  # Enable automated fixes for issues
    max_dependency_depth: int = 3  # Maximum dependency resolution depth
    security_scan_enabled: bool = True  # Enable security scanning


class Scaffolder(BaseModule):
    """AI-powered project scaffolding module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.template_manager = TemplateManager()
        self.dependency_manager = DependencyManager()
        self.ci_cd_manager = CICDPipelineManager()
        self.containerization_manager = ContainerizationManager()
        self.environment_manager = EnvironmentManager()
        self.security_manager = SecurityManager()
        self.testing_manager = TestingManager()
        self.observability_manager = ObservabilityManager()
        self.database_manager = DatabaseManager()
        self.api_documentation_manager = APIDocumentationManager()
        self.code_quality_manager = CodeQualityManager()
        self.project_management_manager = ProjectManagementManager()
        self.description_text = "Generates complete project structures with AI-enhanced templates, intelligent dependency management, CI/CD pipelines, and containerization configs"
        self.version = "1.0.0"

    def get_description(self) -> str:
        """Get human-readable description of the module"""
        return self.description_text

    async def execute(self, input_data: Dict[str, Any]) -> ModuleResult:
        """Execute the project scaffolding"""
        try:
            # Convert input_data to config
            config = ProjectScaffolderConfig(**input_data)

            # Generate project structure using AI
            project_structure = await self._generate_project_structure(config)

            # Create the project
            await self._create_project(config, project_structure)

            # Generate CI/CD pipelines if requested
            if config.ci_cd_platforms:
                await self._generate_ci_cd_pipelines(config, project_structure)

            # Generate containerization configs if requested
            if config.containerization:
                await self._generate_containerization(config, project_structure)

            # Generate environment configs if requested
            if config.environment_management:
                await self._generate_environment_config(config, project_structure)

            # Generate security features if requested
            if config.security_enabled:
                await self._generate_security_config(config, project_structure)

            # Generate testing setup if requested
            if config.testing_enabled:
                await self._generate_testing_setup(config, project_structure)

            # Generate observability setup if requested
            if config.observability_enabled:
                await self._generate_observability_setup(config, project_structure)

            # Generate database setup if requested
            if config.database_enabled:
                await self._generate_database_setup(config, project_structure)

            # Generate API documentation if requested
            if config.api_documentation_enabled:
                await self._generate_api_documentation_setup(config, project_structure)

            # Generate code quality setup if requested
            if config.code_quality_enabled:
                await self._generate_code_quality_setup(config, project_structure)

            # Generate project management setup if requested
            if config.project_management_enabled:
                await self._generate_project_management_setup(config, project_structure)

            # Initialize git if requested
            if config.initialize_git:
                await self._initialize_git_repository(config)

            return ModuleResult(
                success=True,
                data={
                    "project_name": config.project_name,
                    "project_path": str(
                        Path(config.output_directory) / config.project_name
                    ),
                    "structure": project_structure,
                    "message": f"Successfully created {config.project_type} project '{config.project_name}'",
                },
            )

        except Exception as e:
            return ModuleResult(
                success=False, error=f"Project scaffolding failed: {str(e)}"
            )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution"""
        try:
            config = ProjectScaffolderConfig(**input_data)
            # Validate required fields
            if (
                not config.project_name
                or not config.project_type
                or not config.language
            ):
                return False

            # Validate output directory
            output_path = Path(config.output_directory) / config.project_name
            if output_path.exists():
                # Allow overwriting if directory is empty
                return len(list(output_path.iterdir())) == 0

            return True
        except Exception:
            return False

    async def _generate_project_structure(
        self, config: ProjectScaffolderConfig
    ) -> Dict[str, Any]:
        """Generate project structure using hybrid template + AI customization approach"""

        # Check if templates should be used
        if not config.use_template:
            return await self._generate_with_ai_fallback(config)

        # Try to find a suitable template first
        template = self.template_manager.get_template(
            language=config.language,
            framework=config.framework,
            project_type=config.project_type,
        )

        if template:
            # Use hybrid approach: template + AI customization
            return await self._customize_template_with_ai(template, config)
        else:
            # Fallback to pure AI generation
            return await self._generate_with_ai_fallback(config)

    async def _customize_template_with_ai(
        self, template: Dict[str, Any], config: ProjectScaffolderConfig
    ) -> Dict[str, Any]:
        """Customize a template using AI and advanced dependency management"""

        # Start with the template as base
        customized_structure = self.template_manager.customize_template(
            template, config.__dict__
        )

        # Use advanced dependency management
        resolved_deps = await self.dependency_manager.resolve_dependencies(
            language=config.language,
            framework=config.framework,
            features=config.features,
            existing_deps=customized_structure.get("dependencies", {}).get(
                "dependencies", []
            ),
        )

        # Update dependencies in the structure
        if "dependencies" not in customized_structure:
            customized_structure["dependencies"] = {}

        customized_structure["dependencies"]["dependencies"] = resolved_deps[
            "dependencies"
        ]
        customized_structure["dependencies"]["dev_dependencies"] = resolved_deps.get(
            "dev_dependencies", []
        )

        # Add dependency conflict and vulnerability information
        if resolved_deps.get("conflicts"):
            customized_structure["dependencies"]["conflicts"] = resolved_deps[
                "conflicts"
            ]

        if resolved_deps.get("vulnerabilities"):
            customized_structure["dependencies"]["vulnerabilities"] = resolved_deps[
                "vulnerabilities"
            ]

        # Use AI to enhance/customize based on specific requirements
        prompt = f"""
        You have a {config.language} {config.project_type} project template that needs customization.

        Project Details:
        - Name: {config.project_name}
        - Type: {config.project_type}
        - Language: {config.language}
        - Framework: {config.framework or 'None specified'}
        - Features: {', '.join(config.features) if config.features else 'Basic setup'}

        Current Template Structure:
        {json.dumps(customized_structure, indent=2)}

        Please enhance this template by:
        1. Adding any missing files or directories based on the requested features
        2. Modifying existing files to include feature-specific code
        3. Ensuring dependencies are properly configured (they have already been resolved)
        4. Adding any necessary scripts or build configurations
        5. Considering any dependency conflicts or vulnerabilities that were detected

        Dependency Information:
        - Resolved Dependencies: {resolved_deps['dependencies']}
        - Dev Dependencies: {resolved_deps.get('dev_dependencies', [])}
        - Conflicts: {resolved_deps.get('conflicts', [])}
        - Vulnerabilities: {resolved_deps.get('vulnerabilities', [])}

        Return the enhanced structure in the same JSON format. Focus on additions and modifications rather than replacing the entire template.
        """

        try:
            ai_response = await self.ai_utils.generate_text(prompt, max_tokens=3000)

            # Try to parse AI enhancements
            try:
                enhancements = json.loads(ai_response)

                # Merge enhancements with base template
                return self._merge_template_enhancements(
                    customized_structure, enhancements
                )

            except json.JSONDecodeError:
                # If AI doesn't return valid JSON, return the base template
                return customized_structure

        except Exception:
            # If AI fails, return the base template
            return customized_structure

    def _merge_template_enhancements(
        self, base_template: Dict[str, Any], enhancements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge AI enhancements with the base template"""

        merged = json.loads(json.dumps(base_template))  # Deep copy

        # Merge directories
        if "directories" in enhancements:
            existing_dirs = set(merged.get("directories", []))
            new_dirs = set(enhancements["directories"])
            merged["directories"] = list(existing_dirs.union(new_dirs))

        # Merge/modify files
        if "files" in enhancements:
            for file_path, file_info in enhancements["files"].items():
                if file_path in merged.get("files", {}):
                    # Merge file content if it exists
                    existing_content = merged["files"][file_path].get("content", "")
                    new_content = file_info.get("content", "")
                    # Simple merge - could be enhanced with more sophisticated logic
                    merged["files"][file_path]["content"] = (
                        new_content or existing_content
                    )
                    merged["files"][file_path]["description"] = file_info.get(
                        "description", merged["files"][file_path].get("description", "")
                    )
                else:
                    # Add new file
                    merged["files"][file_path] = file_info

        # Merge dependencies
        if "dependencies" in enhancements:
            base_deps = merged.get("dependencies", {})
            enh_deps = enhancements["dependencies"]

            for dep_type in ["dependencies", "dev_dependencies"]:
                if dep_type in enh_deps:
                    existing = set(base_deps.get(dep_type, []))
                    new_deps = set(enh_deps[dep_type])
                    base_deps[dep_type] = list(existing.union(new_deps))

        # Merge scripts
        if "scripts" in enhancements:
            base_scripts = merged.get("scripts", {})
            base_scripts.update(enhancements["scripts"])
            merged["scripts"] = base_scripts

        return merged

    async def _generate_with_ai_fallback(
        self, config: ProjectScaffolderConfig
    ) -> Dict[str, Any]:
        """Fallback to pure AI generation when no template is available"""

        prompt = f"""
        Generate a complete project structure for a {config.project_type} project.

        Project Details:
        - Name: {config.project_name}
        - Type: {config.project_type}
        - Language: {config.language}
        - Framework: {config.framework or 'None specified'}
        - Features: {', '.join(config.features) if config.features else 'Basic setup'}

        Please provide a JSON response with the following structure:
        {{
            "directories": ["list", "of", "directories", "to", "create"],
            "files": {{
                "path/to/file1.ext": {{
                    "content": "file content here",
                    "description": "what this file does"
                }},
                "path/to/file2.ext": {{
                    "content": "file content here",
                    "description": "what this file does"
                }}
            }},
            "dependencies": {{
                "package_manager": "pip/npm/etc",
                "dependencies": ["list", "of", "dependencies"],
                "dev_dependencies": ["list", "of", "dev", "dependencies"]
            }},
            "scripts": {{
                "start": "command to start the project",
                "build": "command to build the project",
                "test": "command to run tests"
            }},
            "configuration": {{
                "additional_setup_steps": ["list", "of", "setup", "instructions"]
            }}
        }}

        Make sure the structure is appropriate for a {config.language} {config.project_type} project.
        Include all necessary files for a production-ready project.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=4000)
            # Try to parse as JSON, if it fails, create a basic structure
            try:
                structure = json.loads(response)
                return structure
            except json.JSONDecodeError:
                # Fallback to basic structure if AI response isn't valid JSON
                return self._create_basic_structure(config)

        except Exception as e:
            # Fallback to basic structure if AI fails
            return self._create_basic_structure(config)

    def _create_basic_structure(
        self, config: ProjectScaffolderConfig
    ) -> Dict[str, Any]:
        """Create a basic project structure as fallback"""

        base_structure = {
            "directories": ["src", "tests", "docs"],
            "files": {
                "README.md": {
                    "content": f"# {config.project_name}\n\nA {config.project_type} project generated by CodeForge AI.\n",
                    "description": "Project README file",
                },
                ".gitignore": {
                    "content": "# Python\n__pycache__/\n*.pyc\n*.pyo\n.env\n.venv/\n",
                    "description": "Git ignore file",
                },
            },
            "dependencies": {
                "package_manager": "pip",
                "dependencies": [],
                "dev_dependencies": ["pytest", "black", "isort"],
            },
            "scripts": {"test": "pytest", "format": "black . && isort ."},
            "configuration": {
                "additional_setup_steps": [
                    "Create a virtual environment: python -m venv venv",
                    "Activate virtual environment: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)",
                    "Install dependencies: pip install -r requirements.txt",
                ]
            },
        }

        # Add language-specific files
        if config.language.lower() == "python":
            base_structure["files"]["requirements.txt"] = {
                "content": "# Add your project dependencies here\n",
                "description": "Python dependencies file",
            }
            base_structure["files"]["src/__init__.py"] = {
                "content": "",
                "description": "Python package init file",
            }
            base_structure["files"]["src/main.py"] = {
                "content": 'def main():\n    print("Hello from CodeForge AI!")\n\nif __name__ == "__main__":\n    main()\n',
                "description": "Main Python entry point",
            }

        return base_structure

    async def _create_project(
        self, config: ProjectScaffolderConfig, structure: Dict[str, Any]
    ):
        """Create the actual project files and directories"""

        project_path = Path(config.output_directory) / config.project_name
        project_path.mkdir(parents=True, exist_ok=True)

        # Create directories
        for directory in structure.get("directories", []):
            (project_path / directory).mkdir(parents=True, exist_ok=True)

        # Create files
        for file_path, file_info in structure.get("files", {}).items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_info.get("content", ""))

        # Create dependency files
        deps = structure.get("dependencies", {})
        if deps.get("package_manager") == "pip":
            req_file = project_path / "requirements.txt"
            with open(req_file, "w", encoding="utf-8") as f:
                f.write("\n".join(deps.get("dependencies", [])))
                if deps.get("dev_dependencies"):
                    f.write("\n# Development dependencies\n")
                    f.write(
                        "\n".join(
                            f"# {dep}" for dep in deps.get("dev_dependencies", [])
                        )
                    )

    async def _initialize_git_repository(self, config: ProjectScaffolderConfig):
        """Initialize a git repository for the project"""

        project_path = Path(config.output_directory) / config.project_name

        try:
            # Initialize git repo
            os.chdir(project_path)
            os.system("git init")

            # Add all files
            os.system("git add .")

            # Initial commit
            os.system(
                'git commit -m "Initial commit - Project scaffolded by CodeForge AI"'
            )

        except Exception as e:
            # Git initialization is not critical, just log the error
            pass
        finally:
            # Return to original directory
            os.chdir(Path.cwd().parent)

    async def _generate_ci_cd_pipelines(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate CI/CD pipeline configurations"""

        project_path = Path(config.output_directory) / config.project_name

        for platform in config.ci_cd_platforms:
            try:
                pipeline_config = self.ci_cd_manager.generate_pipeline(
                    platform=platform,
                    language=config.language,
                    framework=config.framework,
                    features=config.features,
                    deployment_targets=config.deployment_targets,
                )

                # Add pipeline files to project structure
                for file_path, file_info in pipeline_config.get("files", {}).items():
                    full_path = project_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(file_info.get("content", ""))

                    # Add to project structure for tracking
                    if "ci_cd_pipelines" not in project_structure:
                        project_structure["ci_cd_pipelines"] = []

                    project_structure["ci_cd_pipelines"].append(
                        {
                            "platform": platform,
                            "file": file_path,
                            "description": file_info.get("description", ""),
                        }
                    )

            except Exception as e:
                # Log error but continue with other platforms
                print(f"Failed to generate {platform} pipeline: {e}")

    async def _generate_containerization(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate containerization configurations (e.g., Dockerfile, Kubernetes manifests)"""

        project_path = Path(config.output_directory) / config.project_name

        if config.create_dockerfile:
            # Generate Dockerfile using AI
            dockerfile_content = await self._generate_dockerfile(config)

            # Save Dockerfile
            dockerfile_path = project_path / "Dockerfile"
            with open(dockerfile_path, "w", encoding="utf-8") as f:
                f.write(dockerfile_content)

            # Add to project structure for tracking
            if "containerization" not in project_structure:
                project_structure["containerization"] = {}

            project_structure["containerization"]["dockerfile"] = {
                "path": "Dockerfile",
                "description": "Dockerfile for containerizing the application",
            }

        # Generate Kubernetes manifests if required
        if "kubernetes" in config.deployment_targets:
            await self._generate_kubernetes_manifests(config, project_structure)

    async def _generate_dockerfile(self, config: ProjectScaffolderConfig) -> str:
        """Generate a Dockerfile for the project"""

        prompt = f"""
        Generate a Dockerfile for a {config.language} {config.project_type} project.

        Project Details:
        - Name: {config.project_name}
        - Type: {config.project_type}
        - Language: {config.language}
        - Framework: {config.framework or 'None specified'}
        - Features: {', '.join(config.features) if config.features else 'Basic setup'}

        Base the Dockerfile on the following requirements:
        - Use the official {config.language} image as a base
        - Set the working directory
        - Copy the project files into the container
        - Install dependencies
        - Specify the command to run the application

        Return the Dockerfile content as a plain text.

        Note: Ensure that the Dockerfile is optimized for production use.
        """

        try:
            dockerfile_content = await self.ai_utils.generate_text(
                prompt, max_tokens=1500
            )
            return dockerfile_content.strip()
        except Exception:
            return ""

    async def _generate_kubernetes_manifests(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate Kubernetes deployment and service manifests"""

        # Deployment manifest
        deployment_manifest = f"""
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: {config.project_name}-deployment
          labels:
            app: {config.project_name}
        spec:
          replicas: {config.kubernetes_replicas}
          selector:
            matchLabels:
              app: {config.project_name}
          template:
            metadata:
              labels:
                app: {config.project_name}
            spec:
              containers:
              - name: {config.project_name}
                image: {config.project_name.lower()}:latest
                ports:
                - containerPort: 80
        """

        # Service manifest
        service_manifest = f"""
        apiVersion: v1
        kind: Service
        metadata:
          name: {config.project_name}-service
        spec:
          type: LoadBalancer
          ports:
          - port: 80
            targetPort: 80
          selector:
            app: {config.project_name}
        """

        # Save manifests to project structure
        project_path = Path(config.output_directory) / config.project_name

        # Deployment manifest
        with open(project_path / "k8s-deployment.yaml", "w", encoding="utf-8") as f:
            f.write(deployment_manifest.strip())

        # Service manifest
        with open(project_path / "k8s-service.yaml", "w", encoding="utf-8") as f:
            f.write(service_manifest.strip())

        # Add to project structure for tracking
        if "containerization" not in project_structure:
            project_structure["containerization"] = {}

        project_structure["containerization"]["kubernetes_manifests"] = {
            "deployment": {
                "path": "k8s-deployment.yaml",
                "description": "Kubernetes deployment manifest",
            },
            "service": {
                "path": "k8s-service.yaml",
                "description": "Kubernetes service manifest",
            },
        }

    async def _generate_environment_config(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate environment configuration files"""

        project_path = Path(config.output_directory) / config.project_name

        # Generate environment configuration files
        env_files = await self.environment_manager.generate_environment_config(
            project_path=project_path,
            language=config.language,
            framework=config.framework,
            features=config.features,
            config_formats=config.config_formats,
            include_secrets=config.include_secrets,
        )

        # Add to project structure for tracking
        if "environment" not in project_structure:
            project_structure["environment"] = {}

        project_structure["environment"].update(env_files)

    async def _generate_security_config(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate security configuration and code"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string auth_type to AuthType enum
        try:
            auth_type = AuthType(config.auth_type.lower())
        except ValueError:
            auth_type = AuthType.JWT  # Default fallback

        # Convert string security features to SecurityFeature enum
        security_features = []
        for feature in config.security_features:
            try:
                security_features.append(SecurityFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid features

        # Generate security configuration and code
        security_files = await self.security_manager.generate_security_config(
            project_path=project_path,
            language=config.language,
            framework=config.framework,
            features=config.features,
            auth_type=auth_type,
            security_features=security_features,
        )

        # Add to project structure for tracking
        if "security" not in project_structure:
            project_structure["security"] = {}

        project_structure["security"].update(security_files)

    async def _generate_testing_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate testing setup and configuration"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string test_framework to TestFramework enum
        try:
            test_framework = TestFramework(config.test_framework.lower())
        except ValueError:
            test_framework = TestFramework.PYTEST  # Default fallback

        # Convert string test_types to TestType enum
        test_types = []
        for test_type in config.test_types:
            try:
                test_types.append(TestType(test_type.lower()))
            except ValueError:
                continue  # Skip invalid test types

        # Generate testing setup
        testing_files = await self.testing_manager.generate_testing_setup(
            project_path=project_path,
            language=config.language,
            framework=config.framework,
            features=config.features,
            test_framework=test_framework,
            test_types=test_types,
            include_coverage=config.include_coverage,
            ci_integration=config.ci_testing_integration,
        )

        # Add to project structure for tracking
        if "testing" not in project_structure:
            project_structure["testing"] = {}

        project_structure["testing"].update(testing_files)

    async def _generate_observability_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate observability setup and configuration"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string types to enum
        try:
            monitoring_type = MonitoringType(config.monitoring_type.lower())
        except ValueError:
            monitoring_type = MonitoringType.PROMETHEUS

        try:
            logging_type = LoggingType(config.logging_type.lower())
        except ValueError:
            logging_type = LoggingType.ELK

        try:
            tracing_type = TracingType(config.tracing_type.lower())
        except ValueError:
            tracing_type = TracingType.JAEGER

        # Convert string features to ObservabilityFeature enum
        observability_features = []
        for feature in config.observability_features:
            try:
                observability_features.append(ObservabilityFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid features

        # Generate observability setup
        observability_files = (
            await self.observability_manager.generate_observability_setup(
                project_path=project_path,
                language=config.language,
                framework=config.framework,
                features=config.features,
                monitoring_type=monitoring_type,
                logging_type=logging_type,
                tracing_type=tracing_type,
                observability_features=observability_features,
            )
        )

        # Add to project structure for tracking
        if "observability" not in project_structure:
            project_structure["observability"] = {}

        project_structure["observability"].update(observability_files)

    async def _generate_database_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate database setup and configuration"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string types to enum
        try:
            database_type = DatabaseType(config.database_type.lower())
        except ValueError:
            database_type = DatabaseType.POSTGRESQL

        try:
            orm_type = ORMType(config.orm_type.lower())
        except ValueError:
            orm_type = ORMType.SQLALCHEMY

        try:
            migration_tool = MigrationTool(config.migration_tool.lower())
        except ValueError:
            migration_tool = MigrationTool.ALEMBIC

        # Convert string features to DatabaseFeature enum
        database_features = []
        for feature in config.database_features:
            try:
                database_features.append(DatabaseFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid features

        # Create database config
        database_config = DatabaseConfig(
            host=config.database_host,
            port=config.database_port,
            database=config.database_name,
            username=config.database_user,
            password=config.database_password,
        )

        # Generate database setup
        database_files = await self.database_manager.generate_database_setup(
            project_path=project_path,
            language=config.language,
            framework=config.framework,
            features=config.features,
            database_type=database_type,
            orm_type=orm_type,
            migration_tool=migration_tool,
            database_features=database_features,
            database_config=database_config,
        )

        # Add to project structure for tracking
        if "database" not in project_structure:
            project_structure["database"] = {}

        project_structure["database"].update(database_files)

    async def _generate_api_documentation_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate API documentation setup and configuration"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string types to enum
        api_framework = APIFramework.FASTAPI  # Default
        if config.api_framework.lower() in [e.value for e in APIFramework]:
            api_framework = APIFramework(config.api_framework.lower())

        # Convert string formats to DocumentationFormat enum
        documentation_formats = []
        for fmt in config.documentation_formats:
            try:
                documentation_formats.append(DocumentationFormat(fmt.lower()))
            except ValueError:
                continue  # Skip invalid formats

        # Convert string tools to DocumentationTool enum
        documentation_tools = []
        for tool in config.documentation_tools:
            try:
                documentation_tools.append(DocumentationTool(tool.lower()))
            except ValueError:
                continue  # Skip invalid tools

        # Convert string features to DocumentationFeature enum
        documentation_features = []
        for feature in config.documentation_features:
            try:
                documentation_features.append(DocumentationFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid features

        # Generate API documentation setup
        documentation_files = (
            await self.api_documentation_manager.generate_api_documentation(
                project_path=project_path,
                language=config.language,
                framework=config.framework,
                features=config.features,
                api_framework=api_framework,
                documentation_formats=documentation_formats,
                documentation_tools=documentation_tools,
                documentation_features=documentation_features,
                api_title=config.api_title,
                api_version=config.api_version,
                api_description=config.api_description,
            )
        )

        # Add to project structure for tracking
        if "api_documentation" not in project_structure:
            project_structure["api_documentation"] = {}

        project_structure["api_documentation"].update(documentation_files)

    async def _generate_code_quality_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate code quality and linting setup"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string types to enum
        linters = []
        for linter in config.linters:
            try:
                linters.append(LinterType(linter.lower()))
            except ValueError:
                continue  # Skip invalid linters

        formatters = []
        for formatter in config.formatters:
            try:
                formatters.append(FormatterType(formatter.lower()))
            except ValueError:
                continue  # Skip invalid formatters

        type_checkers = []
        for checker in config.type_checkers:
            try:
                type_checkers.append(TypeCheckerType(checker.lower()))
            except ValueError:
                continue  # Skip invalid type checkers

        quality_tools = []
        for tool in config.quality_tools:
            try:
                quality_tools.append(CodeQualityTool(tool.lower()))
            except ValueError:
                continue  # Skip invalid tools

        quality_features = []
        for feature in config.quality_features:
            try:
                quality_features.append(QualityFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid features

        # Create code quality config
        quality_config = CodeQualityConfig(
            max_line_length=config.max_line_length,
            target_python_version=config.target_python_version,
            strict_type_checking=config.strict_type_checking,
            include_docstring_checking=config.include_docstring_checking,
            auto_fix_on_commit=config.auto_fix_on_commit,
        )

        # Generate code quality setup
        quality_files = await self.code_quality_manager.generate_code_quality_setup(
            project_path=project_path,
            language=config.language,
            framework=config.framework,
            features=config.features,
            linters=linters,
            formatters=formatters,
            type_checkers=type_checkers,
            quality_tools=quality_tools,
            quality_features=quality_features,
            quality_config=quality_config,
        )

        # Add to project structure for tracking
        if "code_quality" not in project_structure:
            project_structure["code_quality"] = {}

        project_structure["code_quality"].update(quality_files)

    async def _generate_project_management_setup(
        self, config: ProjectScaffolderConfig, project_structure: Dict[str, Any]
    ):
        """Generate project management and validation setup"""

        project_path = Path(config.output_directory) / config.project_name

        # Convert string types to enum
        validation_types = []
        for validation in config.validation_types:
            try:
                validation_types.append(ValidationType(validation.lower()))
            except ValueError:
                continue  # Skip invalid validation types

        dependency_checks = []
        for check in config.dependency_checks:
            try:
                dependency_checks.append(DependencyCheck(check.lower()))
            except ValueError:
                continue  # Skip invalid dependency checks

        config_validations = []
        for validation in config.config_validations:
            try:
                config_validations.append(ConfigurationValidation(validation.lower()))
            except ValueError:
                continue  # Skip invalid config validations

        management_features = []
        for feature in config.management_features:
            try:
                management_features.append(ProjectManagementFeature(feature.lower()))
            except ValueError:
                continue  # Skip invalid management features

        # Create project management config
        management_config = ProjectManagementConfig(
            enable_structure_validation=config.enable_structure_validation,
            enable_dependency_checking=config.enable_dependency_checking,
            enable_config_validation=config.enable_config_validation,
            enable_health_monitoring=config.enable_health_monitoring,
            enable_compliance_checking=config.enable_compliance_checking,
            enable_automated_fixes=config.enable_automated_fixes,
            max_dependency_depth=config.max_dependency_depth,
            security_scan_enabled=config.security_scan_enabled,
        )

        # Generate project management setup
        management_files = (
            await self.project_management_manager.generate_project_management_setup(
                project_path=project_path,
                language=config.language,
                framework=config.framework,
                features=config.features,
                validation_types=validation_types,
                dependency_checks=dependency_checks,
                config_validations=config_validations,
                management_features=management_features,
                management_config=management_config,
            )
        )

        # Add to project structure for tracking
        if "project_management" not in project_structure:
            project_structure["project_management"] = {}

        project_structure["project_management"].update(management_files)
