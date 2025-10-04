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


class Scaffolder(BaseModule):
    """AI-powered project scaffolding module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.template_manager = TemplateManager()
        self.dependency_manager = DependencyManager()
        self.ci_cd_manager = CICDPipelineManager()
        self.containerization_manager = ContainerizationManager()
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
