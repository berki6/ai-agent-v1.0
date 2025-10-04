"""
Environment and Secrets Management for Project Scaffolding

This module handles environment variable management, secrets handling,
and configuration validation with support for multiple formats (JSON, YAML, TOML).
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import yaml

try:
    import toml

    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
from enum import Enum


class ConfigFormat(Enum):
    """Supported configuration file formats"""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"


class SecretType(Enum):
    """Types of secrets that can be managed"""

    API_KEY = "api_key"
    DATABASE_URL = "database_url"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_CLIENT_ID = "oauth_client_id"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    WEBHOOK_SECRET = "webhook_secret"
    CUSTOM = "custom"


@dataclass
class EnvironmentVariable:
    """Represents an environment variable configuration"""

    name: str
    value: Optional[str] = None
    description: Optional[str] = None
    required: bool = False
    sensitive: bool = False
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None


@dataclass
class SecretConfig:
    """Represents a secret configuration"""

    name: str
    type: SecretType
    description: Optional[str] = None
    required: bool = True
    validation_pattern: Optional[str] = None
    provider: Optional[str] = None  # aws, gcp, azure, vault, etc.


class EnvironmentManager:
    """
    Manages environment variables, secrets, and configuration files
    for scaffolded projects.
    """

    def __init__(self):
        self.config_formats = {
            ConfigFormat.JSON: self._save_json_config,
            ConfigFormat.YAML: self._save_yaml_config,
            ConfigFormat.TOML: self._save_toml_config,
            ConfigFormat.ENV: self._save_env_config,
        }

    async def generate_environment_config(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        config_formats: Optional[List[str]] = None,
        include_secrets: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate environment configuration files for a project.

        Args:
            project_path: Path to the project directory
            language: Programming language (python, javascript, etc.)
            framework: Framework being used (fastapi, react, etc.)
            features: List of features to include
            config_formats: List of configuration formats to generate
            include_secrets: Whether to include secret management

        Returns:
            Dictionary containing generated configuration files and their paths
        """
        if config_formats is None:
            config_formats = ["env", "json"]

        # Determine environment variables based on language/framework/features
        env_vars = self._get_default_env_vars(language, framework, features)
        secrets = (
            self._get_default_secrets(language, framework, features)
            if include_secrets
            else []
        )

        generated_files = {}

        # Generate configuration files for each requested format
        for fmt in config_formats:
            try:
                format_enum = ConfigFormat(fmt.lower())
                if format_enum in self.config_formats:
                    files = await self.config_formats[format_enum](
                        project_path, env_vars, secrets, language, framework
                    )
                    generated_files.update(files)
            except ValueError:
                continue  # Skip invalid formats

        # Generate .env.example file
        example_env_path = project_path / ".env.example"
        with open(example_env_path, "w", encoding="utf-8") as f:
            f.write("# Environment Variables Example\n")
            f.write("# Copy this file to .env and fill in the actual values\n\n")

            for env_var in env_vars:
                if env_var.sensitive:
                    f.write(
                        f"# {env_var.name}={env_var.description or 'Sensitive value'}\n"
                    )
                else:
                    default = env_var.default_value or ""
                    f.write(f"{env_var.name}={default}\n")

            if secrets:
                f.write("\n# Secrets (store securely, not in version control)\n")
                for secret in secrets:
                    f.write(f"# {secret.name}={secret.description or 'Secret value'}\n")

        generated_files["env_example"] = {
            "path": ".env.example",
            "description": "Example environment variables file (copy to .env)",
        }

        # Generate .gitignore entry for .env
        gitignore_path = project_path / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_content = f.read()
        else:
            gitignore_content = ""

        if ".env" not in gitignore_content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Environment variables\n.env\n.env.local\n")

        return generated_files

    def _get_default_env_vars(
        self,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
    ) -> List[EnvironmentVariable]:
        """Get default environment variables for the given language/framework/features"""
        env_vars = []

        # Common environment variables
        env_vars.extend(
            [
                EnvironmentVariable(
                    name="ENVIRONMENT",
                    value="development",
                    description="Application environment (development, staging, production)",
                    required=True,
                    default_value="development",
                ),
                EnvironmentVariable(
                    name="DEBUG",
                    value="true",
                    description="Enable debug mode",
                    required=False,
                    default_value="false",
                ),
                EnvironmentVariable(
                    name="LOG_LEVEL",
                    value="INFO",
                    description="Logging level (DEBUG, INFO, WARNING, ERROR)",
                    required=False,
                    default_value="INFO",
                ),
            ]
        )

        # Language-specific variables
        if language.lower() == "python":
            env_vars.extend(
                [
                    EnvironmentVariable(
                        name="PYTHONPATH",
                        value=".",
                        description="Python path for module imports",
                        required=False,
                        default_value=".",
                    ),
                    EnvironmentVariable(
                        name="PYTHONUNBUFFERED",
                        value="1",
                        description="Disable Python output buffering",
                        required=False,
                        default_value="1",
                    ),
                ]
            )

            if framework and framework.lower() == "fastapi":
                env_vars.extend(
                    [
                        EnvironmentVariable(
                            name="HOST",
                            value="0.0.0.0",
                            description="Server host",
                            required=False,
                            default_value="0.0.0.0",
                        ),
                        EnvironmentVariable(
                            name="PORT",
                            value="8000",
                            description="Server port",
                            required=False,
                            default_value="8000",
                        ),
                    ]
                )

        elif language.lower() == "javascript":
            if framework and framework.lower() == "react":
                env_vars.extend(
                    [
                        EnvironmentVariable(
                            name="REACT_APP_API_URL",
                            description="API base URL for the React application",
                            required=False,
                        ),
                        EnvironmentVariable(
                            name="GENERATE_SOURCEMAP",
                            value="false",
                            description="Generate source maps in production",
                            required=False,
                            default_value="false",
                        ),
                    ]
                )

        # Feature-specific variables
        if features:
            if "database" in features:
                env_vars.extend(
                    [
                        EnvironmentVariable(
                            name="DATABASE_URL",
                            description="Database connection URL",
                            required=True,
                            sensitive=True,
                        ),
                        EnvironmentVariable(
                            name="DB_POOL_SIZE",
                            value="10",
                            description="Database connection pool size",
                            required=False,
                            default_value="10",
                        ),
                    ]
                )

            if "authentication" in features:
                env_vars.extend(
                    [
                        EnvironmentVariable(
                            name="JWT_SECRET_KEY",
                            description="Secret key for JWT token signing",
                            required=True,
                            sensitive=True,
                        ),
                        EnvironmentVariable(
                            name="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
                            value="30",
                            description="JWT access token expiration time in minutes",
                            required=False,
                            default_value="30",
                        ),
                    ]
                )

            if "email" in features:
                env_vars.extend(
                    [
                        EnvironmentVariable(
                            name="SMTP_SERVER",
                            description="SMTP server hostname",
                            required=False,
                        ),
                        EnvironmentVariable(
                            name="SMTP_PORT",
                            value="587",
                            description="SMTP server port",
                            required=False,
                            default_value="587",
                        ),
                        EnvironmentVariable(
                            name="SMTP_USERNAME",
                            description="SMTP authentication username",
                            required=False,
                            sensitive=True,
                        ),
                        EnvironmentVariable(
                            name="SMTP_PASSWORD",
                            description="SMTP authentication password",
                            required=False,
                            sensitive=True,
                        ),
                    ]
                )

        return env_vars

    def _get_default_secrets(
        self,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
    ) -> List[SecretConfig]:
        """Get default secrets for the given language/framework/features"""
        secrets = []

        # Common secrets
        if features:
            if "authentication" in features:
                secrets.extend(
                    [
                        SecretConfig(
                            name="JWT_SECRET_KEY",
                            type=SecretType.JWT_SECRET,
                            description="Secret key for JWT token signing and verification",
                            required=True,
                        ),
                    ]
                )

            if "database" in features:
                secrets.extend(
                    [
                        SecretConfig(
                            name="DATABASE_URL",
                            type=SecretType.DATABASE_URL,
                            description="Complete database connection URL with credentials",
                            required=True,
                        ),
                    ]
                )

            if "api" in features:
                secrets.extend(
                    [
                        SecretConfig(
                            name="API_KEY",
                            type=SecretType.API_KEY,
                            description="API key for external service authentication",
                            required=False,
                        ),
                    ]
                )

            if "oauth" in features:
                secrets.extend(
                    [
                        SecretConfig(
                            name="OAUTH_CLIENT_ID",
                            type=SecretType.OAUTH_CLIENT_ID,
                            description="OAuth 2.0 client identifier",
                            required=True,
                        ),
                        SecretConfig(
                            name="OAUTH_CLIENT_SECRET",
                            type=SecretType.OAUTH_CLIENT_SECRET,
                            description="OAuth 2.0 client secret",
                            required=True,
                        ),
                    ]
                )

            if "webhooks" in features:
                secrets.extend(
                    [
                        SecretConfig(
                            name="WEBHOOK_SECRET",
                            type=SecretType.WEBHOOK_SECRET,
                            description="Secret for webhook signature verification",
                            required=True,
                        ),
                    ]
                )

        return secrets

    async def _save_json_config(
        self,
        project_path: Path,
        env_vars: List[EnvironmentVariable],
        secrets: List[SecretConfig],
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save configuration as JSON file"""
        config_data = {
            "environment": {},
            "secrets": {},
            "metadata": {
                "language": language,
                "framework": framework,
                "generated_by": "CodeForge AI Scaffolder",
            },
        }

        # Add environment variables
        for env_var in env_vars:
            config_data["environment"][env_var.name] = {
                "value": env_var.value or env_var.default_value,
                "description": env_var.description,
                "required": env_var.required,
                "sensitive": env_var.sensitive,
            }

        # Add secrets
        for secret in secrets:
            config_data["secrets"][secret.name] = {
                "type": secret.type.value,
                "description": secret.description,
                "required": secret.required,
                "provider": secret.provider,
            }

        config_path = project_path / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        return {
            "config_json": {
                "path": "config.json",
                "description": "JSON configuration file with environment variables and secrets",
            }
        }

    async def _save_yaml_config(
        self,
        project_path: Path,
        env_vars: List[EnvironmentVariable],
        secrets: List[SecretConfig],
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save configuration as YAML file"""
        config_data = {
            "environment": {},
            "secrets": {},
            "metadata": {
                "language": language,
                "framework": framework,
                "generated_by": "CodeForge AI Scaffolder",
            },
        }

        # Add environment variables
        for env_var in env_vars:
            config_data["environment"][env_var.name] = {
                "value": env_var.value or env_var.default_value,
                "description": env_var.description,
                "required": env_var.required,
                "sensitive": env_var.sensitive,
            }

        # Add secrets
        for secret in secrets:
            config_data["secrets"][secret.name] = {
                "type": secret.type.value,
                "description": secret.description,
                "required": secret.required,
                "provider": secret.provider,
            }

        config_path = project_path / "config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

        return {
            "config_yaml": {
                "path": "config.yaml",
                "description": "YAML configuration file with environment variables and secrets",
            }
        }

    async def _save_toml_config(
        self,
        project_path: Path,
        env_vars: List[EnvironmentVariable],
        secrets: List[SecretConfig],
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save configuration as TOML file"""
        if not TOML_AVAILABLE:
            return {}  # Skip TOML if not available

        config_data = {
            "metadata": {
                "language": language,
                "framework": framework,
                "generated_by": "CodeForge AI Scaffolder",
            },
            "environment": {},
            "secrets": {},
        }

        # Add environment variables
        for env_var in env_vars:
            config_data["environment"][env_var.name] = {
                "value": env_var.value or env_var.default_value,
                "description": env_var.description,
                "required": env_var.required,
                "sensitive": env_var.sensitive,
            }

        # Add secrets
        for secret in secrets:
            config_data["secrets"][secret.name] = {
                "type": secret.type.value,
                "description": secret.description,
                "required": secret.required,
                "provider": secret.provider,
            }

        config_path = project_path / "config.toml"
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(config_data, f)

        return {
            "config_toml": {
                "path": "config.toml",
                "description": "TOML configuration file with environment variables and secrets",
            }
        }

    async def _save_env_config(
        self,
        project_path: Path,
        env_vars: List[EnvironmentVariable],
        secrets: List[SecretConfig],
        language: str,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save configuration as .env file"""
        env_path = project_path / ".env"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Environment Configuration\n")
            f.write(f"# Generated for {language}")
            if framework:
                f.write(f" {framework}")
            f.write(" project\n\n")

            for env_var in env_vars:
                if not env_var.sensitive:  # Don't put sensitive values in .env file
                    value = env_var.value or env_var.default_value or ""
                    f.write(f"{env_var.name}={value}\n")

            if secrets:
                f.write(
                    "\n# Secrets (WARNING: Store securely, consider using a secrets manager)\n"
                )
                for secret in secrets:
                    f.write(f"# {secret.name}=your_{secret.type.value}_here\n")

        return {
            "env_file": {
                "path": ".env",
                "description": "Environment variables file (add to .gitignore)",
            }
        }
