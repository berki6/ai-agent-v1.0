"""
Code Quality & Linting Manager for Scaffolder

This module provides comprehensive code quality and linting capabilities for scaffolded projects,
including formatters, linters, type checkers, and pre-commit hooks for multiple programming languages.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...core.ai_utils import AIUtils


class LinterType(str, Enum):
    """Supported linting tools"""

    FLAKE8 = "flake8"
    PYLINT = "pylint"
    ESLINT = "eslint"
    TSLINT = "tslint"
    STYLELINT = "stylelint"
    GOLINT = "golint"
    RUBOCOP = "rubocop"


class FormatterType(str, Enum):
    """Supported code formatters"""

    BLACK = "black"
    ISORT = "isort"
    PRETTIER = "prettier"
    GO_FMT = "go_fmt"
    RUBOCOP_AUTO_CORRECT = "rubocop_auto_correct"


class TypeCheckerType(str, Enum):
    """Supported type checkers"""

    MYPY = "mypy"
    PYRE = "pyre"
    TYPESCRIPT = "typescript"
    FLOW = "flow"


class CodeQualityTool(str, Enum):
    """Code quality tools"""

    PRE_COMMIT = "pre_commit"
    EDITORCONFIG = "editorconfig"
    GITIGNORE = "gitignore"
    DEPENDABOT = "dependabot"
    CODEOWNERS = "codeowners"


class QualityFeature(str, Enum):
    """Code quality features"""

    AUTO_FIX = "auto_fix"
    STRICT_MODE = "strict_mode"
    CI_INTEGRATION = "ci_integration"
    PRE_COMMIT_HOOKS = "pre_commit_hooks"
    EDITOR_INTEGRATION = "editor_integration"
    DOCSTRING_CHECKING = "docstring_checking"


class CodeQualityConfig(BaseModel):
    """Code quality configuration model"""

    max_line_length: int = Field(default=120, description="Maximum line length")
    target_python_version: str = Field(
        default="3.8", description="Target Python version"
    )
    strict_type_checking: bool = Field(
        default=True, description="Enable strict type checking"
    )
    include_docstring_checking: bool = Field(
        default=True, description="Include docstring checking"
    )
    auto_fix_on_commit: bool = Field(
        default=False, description="Auto-fix issues on commit"
    )


class CodeQualityManager:
    """
    Manager for code quality and linting setup
    """

    def __init__(self):
        self.ai_utils = AIUtils()

    async def generate_code_quality_setup(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        linters: Optional[List[LinterType]] = None,
        formatters: Optional[List[FormatterType]] = None,
        type_checkers: Optional[List[TypeCheckerType]] = None,
        quality_tools: Optional[List[CodeQualityTool]] = None,
        quality_features: Optional[List[QualityFeature]] = None,
        quality_config: Optional[CodeQualityConfig] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive code quality and linting setup

        Args:
            project_path: Path to the project root
            language: Programming language (python, javascript, etc.)
            framework: Web framework being used
            features: List of project features
            linters: List of linting tools to configure
            formatters: List of code formatters to configure
            type_checkers: List of type checkers to configure
            quality_tools: List of code quality tools to include
            quality_features: List of quality features to enable
            quality_config: Code quality configuration settings

        Returns:
            Dictionary containing generated code quality files and configurations
        """

        # Set defaults based on language
        if linters is None:
            if language.lower() == "python":
                linters = [LinterType.FLAKE8]
            elif language.lower() == "javascript":
                linters = [LinterType.ESLINT]
            elif language.lower() == "typescript":
                linters = [LinterType.ESLINT]

        if formatters is None:
            if language.lower() == "python":
                formatters = [FormatterType.BLACK, FormatterType.ISORT]
            elif language.lower() in ["javascript", "typescript"]:
                formatters = [FormatterType.PRETTIER]

        if type_checkers is None:
            if language.lower() == "python":
                type_checkers = [TypeCheckerType.MYPY]
            elif language.lower() == "typescript":
                type_checkers = [TypeCheckerType.TYPESCRIPT]

        if quality_tools is None:
            quality_tools = [
                CodeQualityTool.PRE_COMMIT,
                CodeQualityTool.EDITORCONFIG,
                CodeQualityTool.GITIGNORE,
            ]

        if quality_features is None:
            quality_features = [
                QualityFeature.CI_INTEGRATION,
                QualityFeature.PRE_COMMIT_HOOKS,
            ]

        if quality_config is None:
            quality_config = CodeQualityConfig()

        # Generate code quality files
        generated_files = {}

        # Generate linter configurations
        linter_files = await self._generate_linter_configs(
            project_path, language, linters or [], quality_config
        )
        generated_files.update(linter_files)

        # Generate formatter configurations
        formatter_files = await self._generate_formatter_configs(
            project_path, language, formatters or [], quality_config
        )
        generated_files.update(formatter_files)

        # Generate type checker configurations
        type_checker_files = await self._generate_type_checker_configs(
            project_path, language, type_checkers or [], quality_config
        )
        generated_files.update(type_checker_files)

        # Generate quality tool configurations
        tool_files = await self._generate_quality_tools(
            project_path, language, quality_tools or [], quality_config
        )
        generated_files.update(tool_files)

        # Generate CI integration
        if QualityFeature.CI_INTEGRATION in quality_features:
            ci_files = await self._generate_ci_integration(
                project_path,
                language,
                linters or [],
                formatters or [],
                type_checkers or [],
            )
            generated_files.update(ci_files)

        return generated_files

    async def _generate_linter_configs(
        self,
        project_path: Path,
        language: str,
        linters: List[LinterType],
        config: CodeQualityConfig,
    ) -> Dict[str, Any]:
        """Generate linter configuration files"""
        files = {}

        if language.lower() == "python":
            for linter in linters:
                if linter == LinterType.FLAKE8:
                    flake8_config = f"""[flake8]
max-line-length = {config.max_line_length}
max-complexity = 10
ignore =
    E203,  # whitespace before ':'
    E501,  # line too long (handled by black)
    W503,  # line break before binary operator
exclude =
    .git,
    __pycache__,
    .pytest_cache,
    .mypy_cache,
    venv,
    .venv,
    env,
    .env,
    build,
    dist,
    *.egg-info,
per-file-ignores =
    __init__.py:F401  # imported but unused
"""
                    files[".flake8"] = flake8_config

        return files

    async def _generate_formatter_configs(
        self,
        project_path: Path,
        language: str,
        formatters: List[FormatterType],
        config: CodeQualityConfig,
    ) -> Dict[str, Any]:
        """Generate formatter configuration files"""
        files = {}

        if language.lower() == "python":
            for formatter in formatters:
                if formatter == FormatterType.BLACK:
                    black_config = f"""[tool.black]
line-length = {config.max_line_length}
target-version = ['py{config.target_python_version.replace(".", "")}']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
                    files["pyproject.toml"] = black_config

                elif formatter == FormatterType.ISORT:
                    isort_config = f"""[settings]
profile = black
line_length = {config.max_line_length}
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
known_first_party = src
"""
                    files[".isort.cfg"] = isort_config

        return files

    async def _generate_type_checker_configs(
        self,
        project_path: Path,
        language: str,
        type_checkers: List[TypeCheckerType],
        config: CodeQualityConfig,
    ) -> Dict[str, Any]:
        """Generate type checker configuration files"""
        files = {}

        if language.lower() == "python":
            for type_checker in type_checkers:
                if type_checker == TypeCheckerType.MYPY:
                    mypy_config = f"""[mypy]
python_version = {config.target_python_version}
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = {"True" if config.strict_type_checking else "False"}
disallow_incomplete_defs = {"True" if config.strict_type_checking else "False"}
check_untyped_defs = {"True" if config.strict_type_checking else "False"}
disallow_untyped_decorators = {"True" if config.strict_type_checking else "False"}
no_implicit_optional = {"True" if config.strict_type_checking else "False"}
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[[tool.mypy.overrides]]
module = [
    "pydantic.*",
    "fastapi.*",
    "uvicorn.*",
]
ignore_missing_imports = True

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = True
"""
                    files["mypy.ini"] = mypy_config

        return files

    async def _generate_quality_tools(
        self,
        project_path: Path,
        language: str,
        tools: List[CodeQualityTool],
        config: CodeQualityConfig,
    ) -> Dict[str, Any]:
        """Generate code quality tool configurations"""
        files = {}

        for tool in tools:
            if tool == CodeQualityTool.PRE_COMMIT:
                pre_commit_config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
"""
                files[".pre-commit-config.yaml"] = pre_commit_config

            elif tool == CodeQualityTool.EDITORCONFIG:
                editorconfig = """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{py,pyi}]
max_line_length = 120

[*.{js,jsx,ts,tsx}]
indent_size = 2

[*.{json,yml,yaml}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
"""
                files[".editorconfig"] = editorconfig

        return files

    async def _generate_ci_integration(
        self,
        project_path: Path,
        language: str,
        linters: List[LinterType],
        formatters: List[FormatterType],
        type_checkers: List[TypeCheckerType],
    ) -> Dict[str, Any]:
        """Generate CI integration for code quality checks"""
        files = {}

        if language.lower() == "python":
            github_actions_workflow = """name: Code Quality

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt

    - name: Run Black
      run: black --check --diff .

    - name: Run isort
      run: isort --check-only --diff .

    - name: Run flake8
      run: flake8 .

    - name: Run mypy
      run: mypy .

    - name: Run tests
      run: pytest --cov=src --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
"""
            files[".github/workflows/code-quality.yml"] = github_actions_workflow

        return files
