import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil

from src.core.base_module import BaseModule, ModuleConfig, ModuleResult
from src.core.ai_utils import AIUtils


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


class Scaffolder(BaseModule):
    """AI-powered project scaffolding module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.description_text = (
            "Generates complete project structures using AI analysis"
        )
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
        """Use AI to generate the project structure based on requirements"""

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
