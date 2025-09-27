import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from src.core.base_module import BaseModule, ModuleConfig, ModuleResult
from src.core.ai_utils import AIUtils


class DocumentationAlchemistConfig(ModuleConfig):
    """Configuration for Documentation Alchemist"""

    name: str = "alchemist"
    source_path: str
    output_path: str = "docs"
    doc_format: str = "markdown"  # markdown, html, rst
    include_private: bool = False
    generate_api_docs: bool = True
    generate_readme: bool = True
    generate_examples: bool = False
    max_file_size: int = 50000  # Maximum file size to analyze (in characters)


class Alchemist(BaseModule):
    """AI-powered documentation generation module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.description_text = (
            "Generates comprehensive documentation using AI analysis"
        )
        self.version = "1.0.0"

        # Documentation templates
        self.templates = {
            "function": """
### {name}

**Signature:** `{signature}`

**Description:**
{description}

**Parameters:**
{parameters}

**Returns:**
{returns}

**Example:**
```python
{example}
```

**Notes:**
{notes}
""",
            "class": """
## {name}

**Description:**
{description}

**Attributes:**
{attributes}

**Methods:**
{methods}

**Example:**
```python
{example}
```

**Notes:**
{notes}
""",
            "module": """
# {name} Module

## Overview

{description}

## Contents

{toc}

## API Reference

{api_reference}

## Usage Examples

{examples}

## Notes

{notes}
""",
        }

    def get_description(self) -> str:
        """Get human-readable description of the module"""
        return self.description_text

    async def execute(self, input_data: Dict[str, Any]) -> ModuleResult:
        """Execute the documentation generation"""
        try:
            # Convert input_data to config
            config = DocumentationAlchemistConfig(**input_data)

            # Analyze the codebase
            analysis = await self._analyze_codebase(config)

            # Generate documentation
            docs = await self._generate_documentation(analysis, config)

            # Write documentation files
            await self._write_documentation(docs, config)

            return ModuleResult(
                success=True,
                data={
                    "source_path": config.source_path,
                    "output_path": config.output_path,
                    "files_generated": len(docs),
                    "documentation": docs,
                    "message": f"Documentation generated successfully. Created {len(docs)} files.",
                },
            )

        except Exception as e:
            return ModuleResult(
                success=False, error=f"Documentation generation failed: {str(e)}"
            )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution"""
        try:
            config = DocumentationAlchemistConfig(**input_data)
            # Validate source path exists
            source_path = Path(config.source_path)
            return source_path.exists() and source_path.is_dir()
        except Exception:
            return False

    async def _analyze_codebase(
        self, config: DocumentationAlchemistConfig
    ) -> Dict[str, Any]:
        """Analyze the codebase structure and content"""
        source_path = Path(config.source_path)
        analysis = {
            "modules": [],
            "classes": [],
            "functions": [],
            "files": [],
            "structure": {},
        }

        # Get all Python files
        python_files = self._get_python_files(source_path, config)

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Limit file size
                if len(content) > config.max_file_size:
                    content = content[: config.max_file_size] + "\n... (truncated)"

                # Parse the file
                file_analysis = await self._analyze_file(file_path, content, config)
                analysis["files"].append(file_analysis)

                # Extract components
                analysis["modules"].extend(file_analysis.get("modules", []))
                analysis["classes"].extend(file_analysis.get("classes", []))
                analysis["functions"].extend(file_analysis.get("functions", []))

            except Exception as e:
                # Skip files that can't be analyzed
                continue

        return analysis

    async def _analyze_file(
        self, file_path: Path, content: str, config: DocumentationAlchemistConfig
    ) -> Dict[str, Any]:
        """Analyze a single file using AI"""

        prompt = f"""
        Analyze the following Python file and extract documentation information.
        Focus on public APIs, classes, functions, and modules.

        File: {file_path.name}
        Path: {file_path}

        Code:
        ```python
        {content}
        ```

        Provide a JSON response with the following structure:
        {{
            "modules": [
                {{
                    "name": "module_name",
                    "description": "Brief description of the module",
                    "classes": ["list", "of", "class", "names"],
                    "functions": ["list", "of", "function", "names"]
                }}
            ],
            "classes": [
                {{
                    "name": "ClassName",
                    "description": "Brief description",
                    "methods": ["list", "of", "method", "names"],
                    "attributes": ["list", "of", "attribute", "names"],
                    "signature": "class ClassName(...):"
                }}
            ],
            "functions": [
                {{
                    "name": "function_name",
                    "description": "Brief description",
                    "signature": "def function_name(...):",
                    "parameters": ["param1: type", "param2: type"],
                    "returns": "return type description"
                }}
            ],
            "dependencies": ["list", "of", "imports"],
            "overview": "Brief overview of what this file does"
        }}

        Only include public APIs (no leading underscore unless include_private is True).
        Be concise but informative.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=2000)

            try:
                file_analysis = json.loads(response)
                file_analysis["file_path"] = str(file_path)
                return file_analysis
            except json.JSONDecodeError:
                # Fallback to basic analysis
                return self._basic_file_analysis(file_path, content, config)

        except Exception:
            # Fallback to basic analysis
            return self._basic_file_analysis(file_path, content, config)

    def _basic_file_analysis(
        self, file_path: Path, content: str, config: DocumentationAlchemistConfig
    ) -> Dict[str, Any]:
        """Basic static analysis fallback"""
        analysis = {
            "file_path": str(file_path),
            "modules": [],
            "classes": [],
            "functions": [],
            "dependencies": [],
            "overview": f"Python module: {file_path.name}",
        }

        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            # Find imports
            if line.startswith("import ") or line.startswith("from "):
                analysis["dependencies"].append(line)

            # Find classes
            class_match = re.match(r"class\s+(\w+)", line)
            if class_match and (
                config.include_private or not class_match.group(1).startswith("_")
            ):
                analysis["classes"].append(
                    {
                        "name": class_match.group(1),
                        "description": "Class definition",
                        "methods": [],
                        "attributes": [],
                        "signature": line,
                    }
                )

            # Find functions
            func_match = re.match(r"def\s+(\w+)", line)
            if func_match and (
                config.include_private or not func_match.group(1).startswith("_")
            ):
                analysis["functions"].append(
                    {
                        "name": func_match.group(1),
                        "description": "Function definition",
                        "signature": line,
                        "parameters": [],
                        "returns": "Unknown",
                    }
                )

        return analysis

    async def _generate_documentation(
        self, analysis: Dict[str, Any], config: DocumentationAlchemistConfig
    ) -> Dict[str, Any]:
        """Generate documentation files"""
        docs = {}

        # Generate README
        if config.generate_readme:
            docs["README.md"] = await self._generate_readme(analysis, config)

        # Generate API documentation
        if config.generate_api_docs:
            docs["api.md"] = await self._generate_api_docs(analysis, config)

        # Generate module-specific documentation
        for module_info in analysis.get("modules", []):
            module_name = module_info["name"]
            docs[f"{module_name}.md"] = await self._generate_module_docs(
                module_info, analysis, config
            )

        return docs

    async def _generate_readme(
        self, analysis: Dict[str, Any], config: DocumentationAlchemistConfig
    ) -> str:
        """Generate a README file"""

        prompt = f"""
        Generate a comprehensive README.md file for a Python project based on the following analysis:

        Project Structure:
        - Files analyzed: {len(analysis.get('files', []))}
        - Classes found: {len(analysis.get('classes', []))}
        - Functions found: {len(analysis.get('functions', []))}

        Key Components:
        {json.dumps(analysis, indent=2)}

        Generate a professional README.md with:
        1. Project title and description
        2. Installation instructions
        3. Usage examples
        4. API overview
        5. Project structure
        6. Contributing guidelines

        Make it informative and well-structured.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=3000)
            return response
        except Exception:
            return self._basic_readme(analysis, config)

    def _basic_readme(
        self, analysis: Dict[str, Any], config: DocumentationAlchemistConfig
    ) -> str:
        """Basic README fallback"""
        return f"""# Project Documentation

This documentation was automatically generated by CodeForge AI.

## Overview

This project contains {len(analysis.get('files', []))} Python files with {len(analysis.get('classes', []))} classes and {len(analysis.get('functions', []))} functions.

## Project Structure

{self._generate_structure_overview(analysis)}

## API Reference

See `api.md` for detailed API documentation.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
# Example usage
import your_module

# Use the documented classes and functions
```
"""

    async def _generate_api_docs(
        self, analysis: Dict[str, Any], config: DocumentationAlchemistConfig
    ) -> str:
        """Generate API documentation"""

        prompt = f"""
        Generate comprehensive API documentation in Markdown format based on the following code analysis:

        Analysis Data:
        {json.dumps(analysis, indent=2)}

        Create detailed API documentation including:
        1. Module descriptions
        2. Class documentation with methods and attributes
        3. Function documentation with parameters and return values
        4. Usage examples where appropriate

        Use proper Markdown formatting with headers, code blocks, and lists.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=4000)
            return response
        except Exception:
            return self._basic_api_docs(analysis, config)

    def _basic_api_docs(
        self, analysis: Dict[str, Any], config: DocumentationAlchemistConfig
    ) -> str:
        """Basic API docs fallback"""
        content = "# API Reference\n\n"

        # Classes
        if analysis.get("classes"):
            content += "## Classes\n\n"
            for cls in analysis["classes"]:
                content += f"### {cls['name']}\n\n"
                content += f"{cls.get('description', 'No description available')}\n\n"

        # Functions
        if analysis.get("functions"):
            content += "## Functions\n\n"
            for func in analysis["functions"]:
                content += f"### {func['name']}\n\n"
                content += f"{func.get('description', 'No description available')}\n\n"
                if func.get("signature"):
                    content += f"**Signature:** `{func['signature']}`\n\n"

        return content

    async def _generate_module_docs(
        self,
        module_info: Dict[str, Any],
        analysis: Dict[str, Any],
        config: DocumentationAlchemistConfig,
    ) -> str:
        """Generate documentation for a specific module"""

        prompt = f"""
        Generate detailed documentation for the module: {module_info['name']}

        Module Info:
        {json.dumps(module_info, indent=2)}

        Related Analysis:
        {json.dumps(analysis, indent=2)}

        Create comprehensive module documentation including:
        1. Module overview and purpose
        2. Key classes and their usage
        3. Important functions and their parameters
        4. Usage examples
        5. Dependencies and requirements

        Format as Markdown with proper structure.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=2500)
            return response
        except Exception:
            return f"# {module_info['name']} Module\n\n{module_info.get('description', 'No description available')}"

    def _generate_structure_overview(self, analysis: Dict[str, Any]) -> str:
        """Generate a project structure overview"""
        structure = "## Project Structure\n\n"

        for file_info in analysis.get("files", []):
            file_path = file_info.get("file_path", "")
            if file_path:
                structure += f"- `{file_path}`\n"

        return structure

    def _get_python_files(
        self, source_path: Path, config: DocumentationAlchemistConfig
    ) -> List[Path]:
        """Get all Python files to analyze"""
        python_files = []

        for root, dirs, files in os.walk(source_path):
            # Skip common exclude directories
            dirs[:] = [
                d
                for d in dirs
                if d not in ["__pycache__", ".git", "venv", ".env", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    async def _write_documentation(
        self, docs: Dict[str, Any], config: DocumentationAlchemistConfig
    ):
        """Write documentation files to disk"""
        output_path = Path(config.output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        for filename, content in docs.items():
            file_path = output_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
