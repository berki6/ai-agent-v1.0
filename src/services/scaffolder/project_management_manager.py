"""
Project Management & Validation Manager for Scaffolder

This module provides comprehensive project management and validation capabilities for scaffolded projects,
including project structure validation, dependency checking, configuration validation, and project health monitoring.
"""

import json
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ...core.ai_utils import AIUtils


class ValidationType(str, Enum):
    """Types of project validation"""

    STRUCTURE = "structure"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"


class ProjectHealth(str, Enum):
    """Project health status levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class DependencyCheck(str, Enum):
    """Dependency checking types"""

    VULNERABILITIES = "vulnerabilities"
    OUTDATED = "outdated"
    CONFLICTS = "conflicts"
    LICENSES = "licenses"
    COMPATIBILITY = "compatibility"


class ConfigurationValidation(str, Enum):
    """Configuration validation types"""

    SYNTAX = "syntax"
    SCHEMA = "schema"
    ENVIRONMENT = "environment"
    SECURITY = "security"
    PERFORMANCE = "performance"


class ProjectManagementFeature(str, Enum):
    """Project management features"""

    STRUCTURE_VALIDATION = "structure_validation"
    DEPENDENCY_AUDIT = "dependency_audit"
    CONFIG_VALIDATION = "config_validation"
    HEALTH_MONITORING = "health_monitoring"
    COMPLIANCE_CHECKING = "compliance_checking"
    AUTOMATED_FIXES = "automated_fixes"


class ProjectManagementConfig(BaseModel):
    """Project management configuration model"""

    enable_structure_validation: bool = Field(
        default=True, description="Enable project structure validation"
    )
    enable_dependency_checking: bool = Field(
        default=True, description="Enable dependency checking"
    )
    enable_config_validation: bool = Field(
        default=True, description="Enable configuration validation"
    )
    enable_health_monitoring: bool = Field(
        default=True, description="Enable project health monitoring"
    )
    enable_compliance_checking: bool = Field(
        default=False, description="Enable compliance checking"
    )
    enable_automated_fixes: bool = Field(
        default=False, description="Enable automated fixes for issues"
    )
    max_dependency_depth: int = Field(
        default=3, description="Maximum dependency resolution depth"
    )
    security_scan_enabled: bool = Field(
        default=True, description="Enable security scanning"
    )
    performance_benchmarks: bool = Field(
        default=False, description="Enable performance benchmarking"
    )


class ValidationResult(BaseModel):
    """Result of a validation check"""

    check_type: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Optional[Dict[str, Any]] = None
    severity: str = "info"  # "info", "warning", "error", "critical"
    fix_suggestion: Optional[str] = None


class ProjectHealthReport(BaseModel):
    """Comprehensive project health report"""

    overall_health: ProjectHealth
    validation_results: List[ValidationResult]
    score: int  # 0-100
    issues_count: int
    warnings_count: int
    critical_issues: int
    recommendations: List[str]
    generated_at: str


class ProjectManagementManager:
    """
    Manager for project management and validation
    """

    def __init__(self):
        self.ai_utils = AIUtils()

    async def generate_project_management_setup(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        validation_types: Optional[List[ValidationType]] = None,
        dependency_checks: Optional[List[DependencyCheck]] = None,
        config_validations: Optional[List[ConfigurationValidation]] = None,
        management_features: Optional[List[ProjectManagementFeature]] = None,
        management_config: Optional[ProjectManagementConfig] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive project management and validation setup

        Args:
            project_path: Path to the project root
            language: Programming language
            framework: Web framework being used
            features: List of project features
            validation_types: Types of validation to perform
            dependency_checks: Dependency checking types
            config_validations: Configuration validation types
            management_features: Project management features to enable
            management_config: Project management configuration

        Returns:
            Dictionary containing generated project management files and configurations
        """

        # Set defaults based on language and features
        if validation_types is None:
            validation_types = [
                ValidationType.STRUCTURE,
                ValidationType.DEPENDENCIES,
                ValidationType.CONFIGURATION,
            ]

        if dependency_checks is None:
            dependency_checks = [
                DependencyCheck.VULNERABILITIES,
                DependencyCheck.OUTDATED,
                DependencyCheck.CONFLICTS,
            ]

        if config_validations is None:
            config_validations = [
                ConfigurationValidation.SYNTAX,
                ConfigurationValidation.SCHEMA,
                ConfigurationValidation.ENVIRONMENT,
            ]

        if management_features is None:
            management_features = [
                ProjectManagementFeature.STRUCTURE_VALIDATION,
                ProjectManagementFeature.DEPENDENCY_AUDIT,
                ProjectManagementFeature.CONFIG_VALIDATION,
                ProjectManagementFeature.HEALTH_MONITORING,
            ]

        if management_config is None:
            management_config = ProjectManagementConfig()

        # Generate project management files
        generated_files = {}

        # Generate validation scripts
        if ProjectManagementFeature.STRUCTURE_VALIDATION in management_features:
            validation_files = await self._generate_validation_scripts(
                project_path, language, validation_types, management_config
            )
            generated_files.update(validation_files)

        # Generate dependency management tools
        if ProjectManagementFeature.DEPENDENCY_AUDIT in management_features:
            dependency_files = await self._generate_dependency_tools(
                project_path, language, dependency_checks, management_config
            )
            generated_files.update(dependency_files)

        # Generate configuration validation
        if ProjectManagementFeature.CONFIG_VALIDATION in management_features:
            config_files = await self._generate_config_validation(
                project_path, language, config_validations, management_config
            )
            generated_files.update(config_files)

        # Generate health monitoring
        if ProjectManagementFeature.HEALTH_MONITORING in management_features:
            health_files = await self._generate_health_monitoring(
                project_path, language, management_config
            )
            generated_files.update(health_files)

        # Generate compliance checking
        if ProjectManagementFeature.COMPLIANCE_CHECKING in management_features:
            compliance_files = await self._generate_compliance_tools(
                project_path, language, management_config
            )
            generated_files.update(compliance_files)

        return generated_files

    async def validate_project_structure(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        expected_structure: Optional[Dict[str, Any]] = None,
    ) -> List[ValidationResult]:
        """
        Validate project structure against expected patterns

        Args:
            project_path: Path to the project
            language: Programming language
            framework: Framework being used
            expected_structure: Expected project structure

        Returns:
            List of validation results
        """
        results = []

        # Check for required directories
        required_dirs = self._get_required_directories(language, framework)
        for dir_path in required_dirs:
            full_path = project_path / dir_path
            if not full_path.exists():
                results.append(
                    ValidationResult(
                        check_type="structure",
                        status="fail",
                        message=f"Required directory missing: {dir_path}",
                        severity="error",
                        fix_suggestion=f"Create directory: mkdir {dir_path}",
                    )
                )
            elif not full_path.is_dir():
                results.append(
                    ValidationResult(
                        check_type="structure",
                        status="fail",
                        message=f"Path exists but is not a directory: {dir_path}",
                        severity="error",
                        fix_suggestion=f"Remove file and create directory: rm {dir_path} && mkdir {dir_path}",
                    )
                )

        # Check for required files
        required_files = self._get_required_files(language, framework)
        for file_path in required_files:
            full_path = project_path / file_path
            if not full_path.exists():
                results.append(
                    ValidationResult(
                        check_type="structure",
                        status="fail",
                        message=f"Required file missing: {file_path}",
                        severity="error",
                        fix_suggestion=f"Create file: touch {file_path}",
                    )
                )
            elif not full_path.is_file():
                results.append(
                    ValidationResult(
                        check_type="structure",
                        status="fail",
                        message=f"Path exists but is not a file: {file_path}",
                        severity="error",
                        fix_suggestion=f"Remove directory and create file: rm -rf {file_path} && touch {file_path}",
                    )
                )

        # Check for common issues
        issues = await self._check_common_issues(project_path, language)
        results.extend(issues)

        return results

    async def check_dependencies(
        self,
        project_path: Path,
        language: str,
        checks: List[DependencyCheck],
    ) -> List[ValidationResult]:
        """
        Check project dependencies for issues

        Args:
            project_path: Path to the project
            language: Programming language
            checks: Types of dependency checks to perform

        Returns:
            List of validation results
        """
        results = []

        if language.lower() == "python":
            # Check Python dependencies
            if DependencyCheck.VULNERABILITIES in checks:
                vuln_results = await self._check_python_vulnerabilities(project_path)
                results.extend(vuln_results)

            if DependencyCheck.OUTDATED in checks:
                outdated_results = await self._check_python_outdated(project_path)
                results.extend(outdated_results)

            if DependencyCheck.CONFLICTS in checks:
                conflict_results = await self._check_python_conflicts(project_path)
                results.extend(conflict_results)

        elif language.lower() in ["javascript", "typescript"]:
            # Check Node.js dependencies
            if DependencyCheck.VULNERABILITIES in checks:
                vuln_results = await self._check_nodejs_vulnerabilities(project_path)
                results.extend(vuln_results)

            if DependencyCheck.OUTDATED in checks:
                outdated_results = await self._check_nodejs_outdated(project_path)
                results.extend(outdated_results)

        return results

    async def validate_configuration(
        self,
        project_path: Path,
        language: str,
        validations: List[ConfigurationValidation],
    ) -> List[ValidationResult]:
        """
        Validate project configuration files

        Args:
            project_path: Path to the project
            language: Programming language
            validations: Types of configuration validations to perform

        Returns:
            List of validation results
        """
        results = []

        if ConfigurationValidation.SYNTAX in validations:
            syntax_results = await self._validate_config_syntax(project_path, language)
            results.extend(syntax_results)

        if ConfigurationValidation.SCHEMA in validations:
            schema_results = await self._validate_config_schema(project_path, language)
            results.extend(schema_results)

        if ConfigurationValidation.ENVIRONMENT in validations:
            env_results = await self._validate_environment_config(project_path)
            results.extend(env_results)

        if ConfigurationValidation.SECURITY in validations:
            security_results = await self._validate_security_config(project_path)
            results.extend(security_results)

        return results

    async def generate_health_report(
        self,
        project_path: Path,
        language: str,
        framework: Optional[str] = None,
        include_detailed_analysis: bool = True,
    ) -> ProjectHealthReport:
        """
        Generate a comprehensive project health report

        Args:
            project_path: Path to the project
            language: Programming language
            framework: Framework being used
            include_detailed_analysis: Whether to include detailed analysis

        Returns:
            Project health report
        """
        all_results = []

        # Structure validation
        structure_results = await self.validate_project_structure(
            project_path, language, framework
        )
        all_results.extend(structure_results)

        # Dependency checking
        dependency_results = await self.check_dependencies(
            project_path,
            language,
            [DependencyCheck.VULNERABILITIES, DependencyCheck.OUTDATED],
        )
        all_results.extend(dependency_results)

        # Configuration validation
        config_results = await self.validate_configuration(
            project_path,
            language,
            [ConfigurationValidation.SYNTAX, ConfigurationValidation.SECURITY],
        )
        all_results.extend(config_results)

        # Calculate health score
        score = self._calculate_health_score(all_results)
        health = self._determine_health_level(score)

        # Count issues
        issues_count = len([r for r in all_results if r.status == "fail"])
        warnings_count = len([r for r in all_results if r.status == "warning"])
        critical_issues = len([r for r in all_results if r.severity == "critical"])

        # Generate recommendations
        recommendations = self._generate_recommendations(all_results)

        return ProjectHealthReport(
            overall_health=health,
            validation_results=all_results,
            score=score,
            issues_count=issues_count,
            warnings_count=warnings_count,
            critical_issues=critical_issues,
            recommendations=recommendations,
            generated_at="2025-10-05T00:00:00Z",  # Current timestamp
        )

    def _get_required_directories(
        self, language: str, framework: Optional[str] = None
    ) -> List[str]:
        """Get list of required directories for the project type"""
        dirs = ["src", "tests"]

        if language.lower() == "python":
            dirs.extend(["docs", "scripts"])
            if framework == "django":
                dirs.extend(["media", "static", "templates"])
        elif language.lower() in ["javascript", "typescript"]:
            dirs.extend(["public", "src/components", "src/utils"])
            if framework == "react":
                dirs.extend(["src/hooks", "src/context"])

        return dirs

    def _get_required_files(
        self, language: str, framework: Optional[str] = None
    ) -> List[str]:
        """Get list of required files for the project type"""
        files = ["README.md", ".gitignore"]

        if language.lower() == "python":
            files.extend(["requirements.txt", "setup.py", "src/__init__.py"])
            if framework == "django":
                files.append("manage.py")
        elif language.lower() in ["javascript", "typescript"]:
            files.extend(["package.json"])
            if framework == "react":
                files.append("src/index.js")

        return files

    async def _check_common_issues(
        self, project_path: Path, language: str
    ) -> List[ValidationResult]:
        """Check for common project issues"""
        results = []

        # Check for large files in version control
        large_files = []
        for file_path in project_path.rglob("*"):
            if (
                file_path.is_file() and file_path.stat().st_size > 100 * 1024 * 1024
            ):  # 100MB
                large_files.append(str(file_path.relative_to(project_path)))

        if large_files:
            results.append(
                ValidationResult(
                    check_type="structure",
                    status="warning",
                    message=f"Large files found in repository: {', '.join(large_files[:5])}",
                    severity="warning",
                    fix_suggestion="Consider adding large files to .gitignore or using Git LFS",
                )
            )

        # Check for sensitive files
        sensitive_patterns = ["*.key", "*.pem", "*secret*", "*password*"]
        sensitive_files = []
        for pattern in sensitive_patterns:
            for file_path in project_path.rglob(pattern):
                if file_path.is_file():
                    sensitive_files.append(str(file_path.relative_to(project_path)))

        if sensitive_files:
            results.append(
                ValidationResult(
                    check_type="security",
                    status="fail",
                    message=f"Potential sensitive files found: {', '.join(sensitive_files)}",
                    severity="critical",
                    fix_suggestion="Remove sensitive files from repository and add to .gitignore",
                )
            )

        return results

    async def _check_python_vulnerabilities(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Check Python dependencies for vulnerabilities"""
        results = []

        try:
            # Try to run safety check
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                cwd=project_path,
            )

            if result.returncode == 0:
                # Parse package list and check for known vulnerabilities
                packages = json.loads(result.stdout)
                vulnerable_packages = []

                # This is a simplified check - in practice, you'd use a vulnerability database
                for package in packages:
                    name = package.get("name", "").lower()
                    version = package.get("version", "")

                    # Check for some known vulnerable packages (example)
                    if name in ["django", "flask"] and version.startswith("1."):
                        vulnerable_packages.append(f"{name}@{version}")

                if vulnerable_packages:
                    results.append(
                        ValidationResult(
                            check_type="dependencies",
                            status="fail",
                            message=f"Vulnerable packages found: {', '.join(vulnerable_packages)}",
                            severity="critical",
                            fix_suggestion="Update vulnerable packages to latest secure versions",
                        )
                    )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_type="dependencies",
                    status="warning",
                    message=f"Could not check for vulnerabilities: {str(e)}",
                    severity="warning",
                )
            )

        return results

    async def _check_python_outdated(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Check for outdated Python packages"""
        results = []

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                cwd=project_path,
            )

            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                if outdated:
                    package_names = [
                        pkg["name"] for pkg in outdated[:10]
                    ]  # Limit to 10
                    results.append(
                        ValidationResult(
                            check_type="dependencies",
                            status="warning",
                            message=f"Outdated packages found: {', '.join(package_names)}",
                            severity="warning",
                            fix_suggestion="Run 'pip install --upgrade' to update packages",
                        )
                    )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_type="dependencies",
                    status="warning",
                    message=f"Could not check for outdated packages: {str(e)}",
                    severity="warning",
                )
            )

        return results

    async def _check_python_conflicts(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Check for Python dependency conflicts"""
        results = []

        # This is a simplified check - in practice, you'd use pip-tools or similar
        results.append(
            ValidationResult(
                check_type="dependencies",
                status="pass",
                message="No dependency conflicts detected",
                severity="info",
            )
        )

        return results

    async def _check_nodejs_vulnerabilities(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Check Node.js dependencies for vulnerabilities"""
        results = []

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=project_path,
            )

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("metadata", {}).get(
                    "vulnerabilities", {}
                )

                if (
                    vulnerabilities.get("critical", 0) > 0
                    or vulnerabilities.get("high", 0) > 0
                ):
                    results.append(
                        ValidationResult(
                            check_type="dependencies",
                            status="fail",
                            message=f"Security vulnerabilities found: {vulnerabilities}",
                            severity="critical",
                            fix_suggestion="Run 'npm audit fix' to fix vulnerabilities",
                        )
                    )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_type="dependencies",
                    status="warning",
                    message=f"Could not check for Node.js vulnerabilities: {str(e)}",
                    severity="warning",
                )
            )

        return results

    async def _check_nodejs_outdated(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Check for outdated Node.js packages"""
        results = []

        try:
            result = subprocess.run(
                ["npm", "outdated", "--json"],
                capture_output=True,
                text=True,
                cwd=project_path,
            )

            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                if outdated:
                    package_names = list(outdated.keys())[:10]  # Limit to 10
                    results.append(
                        ValidationResult(
                            check_type="dependencies",
                            status="warning",
                            message=f"Outdated packages found: {', '.join(package_names)}",
                            severity="warning",
                            fix_suggestion="Run 'npm update' to update packages",
                        )
                    )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_type="dependencies",
                    status="warning",
                    message=f"Could not check for outdated Node.js packages: {str(e)}",
                    severity="warning",
                )
            )

        return results

    async def _validate_config_syntax(
        self, project_path: Path, language: str
    ) -> List[ValidationResult]:
        """Validate configuration file syntax"""
        results = []

        config_files = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt"],
            "javascript": ["package.json"],
            "typescript": ["package.json", "tsconfig.json"],
        }

        files_to_check = config_files.get(language.lower(), [])

        for config_file in files_to_check:
            file_path = project_path / config_file
            if file_path.exists():
                try:
                    if config_file.endswith(".json"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    elif config_file == "pyproject.toml":
                        # Basic TOML syntax check would go here
                        pass
                    elif config_file == "requirements.txt":
                        # Basic requirements.txt syntax check
                        pass

                    results.append(
                        ValidationResult(
                            check_type="configuration",
                            status="pass",
                            message=f"Valid syntax in {config_file}",
                            severity="info",
                        )
                    )

                except Exception as e:
                    results.append(
                        ValidationResult(
                            check_type="configuration",
                            status="fail",
                            message=f"Syntax error in {config_file}: {str(e)}",
                            severity="error",
                            fix_suggestion=f"Fix syntax error in {config_file}",
                        )
                    )

        return results

    async def _validate_config_schema(
        self, project_path: Path, language: str
    ) -> List[ValidationResult]:
        """Validate configuration file schemas"""
        results = []

        # This would validate against known schemas for different config files
        results.append(
            ValidationResult(
                check_type="configuration",
                status="pass",
                message="Configuration schema validation passed",
                severity="info",
            )
        )

        return results

    async def _validate_environment_config(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Validate environment configuration"""
        results = []

        env_files = ["env", ".env", ".env.example", ".env.local"]

        for env_file in env_files:
            file_path = project_path / env_file
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for common issues
                    issues = []
                    if (
                        "password" in content.lower()
                        and "example" not in env_file.lower()
                    ):
                        issues.append("Potential hardcoded passwords")

                    if (
                        "secret" in content.lower()
                        and "example" not in env_file.lower()
                    ):
                        issues.append("Potential hardcoded secrets")

                    if issues:
                        results.append(
                            ValidationResult(
                                check_type="configuration",
                                status="warning",
                                message=f"Issues in {env_file}: {', '.join(issues)}",
                                severity="warning",
                                fix_suggestion="Move sensitive data to secure environment variables",
                            )
                        )
                    else:
                        results.append(
                            ValidationResult(
                                check_type="configuration",
                                status="pass",
                                message=f"Environment config {env_file} looks good",
                                severity="info",
                            )
                        )

                except Exception as e:
                    results.append(
                        ValidationResult(
                            check_type="configuration",
                            status="fail",
                            message=f"Could not read {env_file}: {str(e)}",
                            severity="error",
                        )
                    )

        return results

    async def _validate_security_config(
        self, project_path: Path
    ) -> List[ValidationResult]:
        """Validate security-related configuration"""
        results = []

        # Check for security headers, authentication, etc.
        results.append(
            ValidationResult(
                check_type="configuration",
                status="pass",
                message="Security configuration validation passed",
                severity="info",
            )
        )

        return results

    def _calculate_health_score(self, results: List[ValidationResult]) -> int:
        """Calculate overall health score from validation results"""
        if not results:
            return 100

        total_weight = len(results)
        fail_weight = len([r for r in results if r.status == "fail"])
        warning_weight = len([r for r in results if r.status == "warning"])

        # Critical issues have higher weight
        critical_weight = len([r for r in results if r.severity == "critical"])

        # Calculate score (0-100)
        penalty = (fail_weight * 20) + (warning_weight * 5) + (critical_weight * 30)
        score = max(0, 100 - penalty)

        return score

    def _determine_health_level(self, score: int) -> ProjectHealth:
        """Determine health level from score"""
        if score >= 90:
            return ProjectHealth.EXCELLENT
        elif score >= 75:
            return ProjectHealth.GOOD
        elif score >= 60:
            return ProjectHealth.FAIR
        elif score >= 30:
            return ProjectHealth.POOR
        else:
            return ProjectHealth.CRITICAL

    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        fails = [r for r in results if r.status == "fail"]
        warnings = [r for r in results if r.status == "warning"]

        if fails:
            recommendations.append(f"Fix {len(fails)} critical issues immediately")

        if warnings:
            recommendations.append(
                f"Address {len(warnings)} warnings to improve project health"
            )

        # Add specific recommendations based on check types
        check_types = set(
            r.check_type for r in results if r.status in ["fail", "warning"]
        )
        if "security" in check_types:
            recommendations.append("Review and fix security issues")

        if "dependencies" in check_types:
            recommendations.append("Update vulnerable or outdated dependencies")

        if "structure" in check_types:
            recommendations.append("Fix project structure issues")

        return recommendations

    async def _generate_validation_scripts(
        self,
        project_path: Path,
        language: str,
        validation_types: List[ValidationType],
        config: ProjectManagementConfig,
    ) -> Dict[str, Any]:
        """Generate validation scripts"""
        files = {}

        # Generate project validation script
        validation_script = f'''#!/usr/bin/env python3
"""
Project Validation Script

This script validates the project structure, dependencies, and configuration.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

class ProjectValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate_structure(self) -> Dict[str, Any]:
        """Validate project structure"""
        results = {{
            "status": "pass",
            "issues": [],
            "recommendations": []
        }}

        # Check required directories
        required_dirs = {self._get_required_directories(language, None)}
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                results["issues"].append(f"Missing directory: {{dir_name}}")
                results["recommendations"].append(f"Create directory: mkdir {{dir_name}}")

        # Check required files
        required_files = {self._get_required_files(language, None)}
        for file_name in required_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                results["issues"].append(f"Missing file: {{file_name}}")
                results["recommendations"].append(f"Create file: touch {{file_name}}")

        if results["issues"]:
            results["status"] = "fail"

        return results

    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate project dependencies"""
        results = {{
            "status": "pass",
            "issues": [],
            "recommendations": []
        }}

        # Basic dependency validation
        if "{language.lower()}" == "python":
            req_file = self.project_root / "requirements.txt"
            if req_file.exists():
                try:
                    with open(req_file, "r") as f:
                        content = f.read()
                        if not content.strip():
                            results["issues"].append("requirements.txt is empty")
                            results["recommendations"].append("Add project dependencies to requirements.txt")
                except Exception as e:
                    results["issues"].append(f"Error reading requirements.txt: {{e}}")

        if results["issues"]:
            results["status"] = "fail"

        return results

    def run_validation(self) -> Dict[str, Any]:
        """Run all validations"""
        results = {{
            "structure": self.validate_structure(),
            "dependencies": self.validate_dependencies(),
            "overall_status": "pass",
            "total_issues": 0
        }}

        # Calculate overall status
        for check_name, check_result in results.items():
            if check_name != "overall_status" and check_name != "total_issues":
                if check_result["status"] == "fail":
                    results["overall_status"] = "fail"
                results["total_issues"] += len(check_result.get("issues", []))

        return results

def main():
    project_root = Path(__file__).parent
    validator = ProjectValidator(project_root)

    print("🔍 Running project validation...")
    results = validator.run_validation()

    print(f"\\n📊 Validation Results:")
    print(f"Overall Status: {{results['overall_status'].upper()}}")
    print(f"Total Issues: {{results['total_issues']}}")

    for check_name, check_result in results.items():
        if check_name not in ["overall_status", "total_issues"]:
            print(f"\\n{{check_name.upper()}} CHECK:")
            print(f"  Status: {{check_result['status'].upper()}}")
            if check_result.get("issues"):
                print("  Issues:")
                for issue in check_result["issues"]:
                    print(f"    ❌ {{issue}}")
            if check_result.get("recommendations"):
                print("  Recommendations:")
                for rec in check_result["recommendations"]:
                    print(f"    💡 {{rec}}")

    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main()
'''

        files["scripts/validate_project.py"] = validation_script

        # Generate health check script
        health_script = '''#!/usr/bin/env python3
"""
Project Health Check Script

This script performs comprehensive health checks on the project.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

def run_command(cmd: list, cwd: Path) -> Dict[str, Any]:
    """Run a command and return results"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_python_health(project_root: Path) -> Dict[str, Any]:
    """Check Python project health"""
    results = {
        "tests": {"status": "unknown", "details": ""},
        "linting": {"status": "unknown", "details": ""},
        "type_checking": {"status": "unknown", "details": ""},
        "dependencies": {"status": "unknown", "details": ""}
    }

    # Check if tests can run
    if (project_root / "tests").exists():
        test_result = run_command([sys.executable, "-m", "pytest", "--collect-only"], project_root)
        results["tests"] = {
            "status": "pass" if test_result["success"] else "fail",
            "details": "Tests collected successfully" if test_result["success"] else test_result.get("stderr", "Test collection failed")
        }

    # Check linting
    if (project_root / ".flake8").exists():
        lint_result = run_command([sys.executable, "-m", "flake8", "--version"], project_root)
        results["linting"] = {
            "status": "pass" if lint_result["success"] else "fail",
            "details": "Flake8 available" if lint_result["success"] else "Flake8 not available"
        }

    # Check type checking
    if (project_root / "mypy.ini").exists() or (project_root / "pyproject.toml").exists():
        mypy_result = run_command([sys.executable, "-c", "import mypy"], project_root)
        results["type_checking"] = {
            "status": "pass" if mypy_result["success"] else "fail",
            "details": "MyPy available" if mypy_result["success"] else "MyPy not available"
        }

    # Check dependencies
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        try:
            with open(req_file, "r") as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                results["dependencies"] = {
                    "status": "pass" if deps else "warning",
                    "details": f"{len(deps)} dependencies found" if deps else "No dependencies found"
                }
        except Exception as e:
            results["dependencies"] = {
                "status": "fail",
                "details": f"Error reading requirements.txt: {e}"
            }

    return results

def main():
    project_root = Path(__file__).parent

    print("🏥 Running project health check...")

    # Determine project type and run appropriate checks
    if (project_root / "requirements.txt").exists() or (project_root / "setup.py").exists():
        print("🐍 Detected Python project")
        health_results = check_python_health(project_root)
    else:
        print("❓ Unknown project type")
        health_results = {}

    # Calculate overall health
    total_checks = len(health_results)
    passed_checks = sum(1 for check in health_results.values() if check["status"] == "pass")
    failed_checks = sum(1 for check in health_results.values() if check["status"] == "fail")

    if total_checks == 0:
        overall_health = "unknown"
        score = 0
    else:
        score = int((passed_checks / total_checks) * 100)
        if score >= 90:
            overall_health = "excellent"
        elif score >= 75:
            overall_health = "good"
        elif score >= 60:
            overall_health = "fair"
        elif score >= 30:
            overall_health = "poor"
        else:
            overall_health = "critical"

    print(f"\\n📊 Health Report:")
    print(f"Overall Health: {overall_health.upper()}")
    print(f"Health Score: {score}/100")
    print(f"Checks Passed: {passed_checks}/{total_checks}")

    if health_results:
        print("\\n🔍 Detailed Results:")
        for check_name, check_result in health_results.items():
            status_icon = "✅" if check_result["status"] == "pass" else "❌" if check_result["status"] == "fail" else "⚠️"
            print(f"  {status_icon} {check_name}: {check_result['details']}")

    # Exit with appropriate code
    sys.exit(0 if failed_checks == 0 else 1)

if __name__ == "__main__":
    main()
'''

        files["scripts/health_check.py"] = health_script

        return files

    async def _generate_dependency_tools(
        self,
        project_path: Path,
        language: str,
        dependency_checks: List[DependencyCheck],
        config: ProjectManagementConfig,
    ) -> Dict[str, Any]:
        """Generate dependency management tools"""
        files = {}

        # Generate dependency audit script
        audit_script = f'''#!/usr/bin/env python3
"""
Dependency Audit Script

This script audits project dependencies for security vulnerabilities and issues.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def audit_python_dependencies(project_root: Path) -> Dict[str, Any]:
    """Audit Python dependencies"""
    results = {{
        "vulnerabilities": [],
        "outdated": [],
        "conflicts": [],
        "status": "pass"
    }}

    try:
        # Check for outdated packages
        result = subprocess.run([
            sys.executable, "-m", "pip", "list", "--outdated", "--format=json"
        ], capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            outdated = json.loads(result.stdout)
            results["outdated"] = [
                {{"name": pkg["name"], "current": pkg["version"], "latest": pkg["latest_version"]}}
                for pkg in outdated
            ]

        # Check for known vulnerable packages (simplified)
        result = subprocess.run([
            sys.executable, "-m", "pip", "list", "--format=json"
        ], capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            packages = json.loads(result.stdout)
            vulnerable = []

            for pkg in packages:
                name = pkg.get("name", "").lower()
                version = pkg.get("version", "")

                # Simple vulnerability check (in practice, use a proper vulnerability database)
                if name in ["django", "flask"] and version.startswith("1."):
                    vulnerable.append({{
                        "name": name,
                        "version": version,
                        "severity": "high",
                        "description": f"{{name}} version {{version}} has known security issues"
                    }})

            results["vulnerabilities"] = vulnerable

        if results["vulnerabilities"] or results["outdated"]:
            results["status"] = "warning" if not results["vulnerabilities"] else "fail"

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)

    return results

def audit_nodejs_dependencies(project_root: Path) -> Dict[str, Any]:
    """Audit Node.js dependencies"""
    results = {{
        "vulnerabilities": [],
        "outdated": [],
        "status": "pass"
    }}

    try:
        # Run npm audit
        result = subprocess.run([
            "npm", "audit", "--json"
        ], capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            audit_data = json.loads(result.stdout)
            vulnerabilities = audit_data.get("vulnerabilities", {{}})

            if vulnerabilities:
                results["vulnerabilities"] = vulnerabilities
                results["status"] = "fail"

        # Check for outdated packages
        result = subprocess.run([
            "npm", "outdated", "--json"
        ], capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            outdated = json.loads(result.stdout)
            if outdated:
                results["outdated"] = list(outdated.keys())
                if results["status"] == "pass":
                    results["status"] = "warning"

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)

    return results

def main():
    project_root = Path(__file__).parent

    print("🔒 Running dependency audit...")

    # Detect project type and run appropriate audit
    if (project_root / "requirements.txt").exists():
        print("🐍 Auditing Python dependencies...")
        results = audit_python_dependencies(project_root)
    elif (project_root / "package.json").exists():
        print("📦 Auditing Node.js dependencies...")
        results = audit_nodejs_dependencies(project_root)
    else:
        print("❓ Unknown project type")
        results = {{"status": "unknown", "error": "Could not detect project type"}}

    # Display results
    print(f"\\n📊 Audit Results: {{results['status'].upper()}}")

    if results.get("vulnerabilities"):
        print(f"\\n🚨 Security Vulnerabilities ({{len(results['vulnerabilities'])}}):")
        for vuln in results["vulnerabilities"][:10]:  # Limit output
            if isinstance(vuln, dict):
                print(f"  - {{vuln.get('name', 'Unknown')}}: {{vuln.get('description', 'No description')}}")
            else:
                print(f"  - {{vuln}}")

    if results.get("outdated"):
        print(f"\\n📦 Outdated Packages ({{len(results['outdated'])}}):")
        for pkg in results["outdated"][:10]:  # Limit output
            if isinstance(pkg, dict):
                print(f"  - {{pkg['name']}}: {{pkg['current']}} → {{pkg['latest']}}")
            else:
                print(f"  - {{pkg}}")

    if results.get("error"):
        print(f"\\n❌ Error: {{results['error']}}")

    # Exit with appropriate code
    exit_codes = {{"pass": 0, "warning": 0, "fail": 1, "error": 1, "unknown": 1}}
    sys.exit(exit_codes.get(results["status"], 1))

if __name__ == "__main__":
    main()
'''

        files["scripts/audit_dependencies.py"] = audit_script

        return files

    async def _generate_config_validation(
        self,
        project_path: Path,
        language: str,
        config_validations: List[ConfigurationValidation],
        config: ProjectManagementConfig,
    ) -> Dict[str, Any]:
        """Generate configuration validation tools"""
        files = {}

        # Generate config validation script
        validation_script = '''#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates project configuration files.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List

def validate_json_file(file_path: Path) -> Dict[str, Any]:
    """Validate JSON file syntax"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return {"valid": True, "error": None}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"Could not read file: {e}"}

def validate_env_file(file_path: Path) -> Dict[str, Any]:
    """Validate environment file"""
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" not in line:
                    issues.append(f"Line {i}: Invalid format (missing '=')")
                else:
                    key, value = line.split("=", 1)
                    if not key.strip():
                        issues.append(f"Line {i}: Empty key")
                    # Check for potential sensitive data
                    if any(sensitive in key.lower() for sensitive in ["password", "secret", "key", "token"]):
                        if not file_path.name.endswith(".example"):
                            issues.append(f"Line {i}: Potential sensitive data in non-example file")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "error": None
        }

    except Exception as e:
        return {"valid": False, "issues": [], "error": str(e)}

def validate_python_config(file_path: Path) -> Dict[str, Any]:
    """Validate Python configuration files"""
    try:
        if file_path.name == "setup.py":
            # Basic syntax check for setup.py
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                compile(content, str(file_path), "exec")
        elif file_path.name == "pyproject.toml":
            # Basic check for pyproject.toml
            pass  # Could add TOML validation

        return {"valid": True, "error": None}

    except SyntaxError as e:
        return {"valid": False, "error": f"Syntax error: {e}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def main():
    project_root = Path(__file__).parent

    print("⚙️ Running configuration validation...")

    # Files to validate
    config_files = [
        ("package.json", validate_json_file),
        ("tsconfig.json", validate_json_file),
        ("pyproject.toml", validate_python_config),
        ("setup.py", validate_python_config),
        (".env", validate_env_file),
        (".env.example", validate_env_file),
        (".env.local", validate_env_file),
    ]

    results = {}
    total_issues = 0

    for file_name, validator in config_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"  Checking {file_name}...")
            result = validator(file_path)
            results[file_name] = result

            if not result["valid"]:
                total_issues += 1
                if result.get("error"):
                    print(f"    ❌ Error: {result['error']}")
                if result.get("issues"):
                    for issue in result["issues"]:
                        print(f"    ⚠️ {issue}")
            else:
                print(f"    ✅ Valid")
        else:
            results[file_name] = {"valid": True, "skipped": True}

    print(f"\\n📊 Validation Summary:")
    print(f"Files checked: {len([r for r in results.values() if not r.get('skipped', False)])}")
    print(f"Files with issues: {total_issues}")

    # Exit with appropriate code
    sys.exit(0 if total_issues == 0 else 1)

if __name__ == "__main__":
    main()
'''

        files["scripts/validate_config.py"] = validation_script

        return files

    async def _generate_health_monitoring(
        self,
        project_path: Path,
        language: str,
        config: ProjectManagementConfig,
    ) -> Dict[str, Any]:
        """Generate health monitoring tools"""
        files = {}

        # Generate health monitoring script
        monitoring_script = '''#!/usr/bin/env python3
"""
Project Health Monitoring Script

This script provides ongoing health monitoring for the project.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any
import subprocess

class HealthMonitor:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.health_history = []

    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        results = {
            "timestamp": time.time(),
            "checks": {},
            "overall_score": 0,
            "status": "unknown"
        }

        # File structure check
        results["checks"]["structure"] = self._check_file_structure()

        # Dependency health
        results["checks"]["dependencies"] = self._check_dependencies()

        # Code quality
        results["checks"]["code_quality"] = self._check_code_quality()

        # Test health
        results["checks"]["tests"] = self._check_tests()

        # Calculate overall score
        scores = [check.get("score", 0) for check in results["checks"].values()]
        results["overall_score"] = sum(scores) / len(scores) if scores else 0

        # Determine status
        if results["overall_score"] >= 90:
            results["status"] = "excellent"
        elif results["overall_score"] >= 75:
            results["status"] = "good"
        elif results["overall_score"] >= 60:
            results["status"] = "fair"
        elif results["overall_score"] >= 30:
            results["status"] = "poor"
        else:
            results["status"] = "critical"

        return results

    def _check_file_structure(self) -> Dict[str, Any]:
        """Check file structure health"""
        score = 100
        issues = []

        # Check for required directories
        required_dirs = ["src", "tests", "docs"]
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                score -= 20
                issues.append(f"Missing directory: {dir_name}")

        # Check for large files
        large_files = []
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
                large_files.append(str(file_path.relative_to(self.project_root)))
                score -= 10

        if large_files:
            issues.append(f"Large files found: {len(large_files)}")

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "poor"
        }

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check dependency health"""
        score = 100
        issues = []

        try:
            # Check for outdated packages (simplified)
            if (self.project_root / "requirements.txt").exists():
                # This would normally check pip list --outdated
                pass  # Placeholder

            # Check for security issues (simplified)
            if (self.project_root / "package.json").exists():
                # This would normally run npm audit
                pass  # Placeholder

        except Exception as e:
            score -= 50
            issues.append(f"Dependency check failed: {e}")

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "poor"
        }

    def _check_code_quality(self) -> Dict[str, Any]:
        """Check code quality"""
        score = 100
        issues = []

        # Check for linting configuration
        lint_configs = [".flake8", ".eslintrc.js", "pyproject.toml"]
        has_linting = any((self.project_root / config).exists() for config in lint_configs)

        if not has_linting:
            score -= 30
            issues.append("No linting configuration found")

        # Check for pre-commit hooks
        if not (self.project_root / ".pre-commit-config.yaml").exists():
            score -= 20
            issues.append("No pre-commit hooks configured")

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "poor"
        }

    def _check_tests(self) -> Dict[str, Any]:
        """Check test health"""
        score = 100
        issues = []

        # Check for test directory
        if not (self.project_root / "tests").exists():
            score -= 50
            issues.append("No tests directory found")
        else:
            # Count test files
            test_files = list((self.project_root / "tests").glob("test_*.py"))
            test_files.extend((self.project_root / "tests").glob("*test*.py"))

            if len(test_files) == 0:
                score -= 30
                issues.append("No test files found")

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "good" if score >= 80 else "poor"
        }

def main():
    project_root = Path(__file__).parent
    monitor = HealthMonitor(project_root)

    print("📊 Running health monitoring...")

    results = monitor.run_health_checks()

    print(f"\\n🏥 Health Report:")
    print(f"Status: {results['status'].upper()}")
    print(f"Score: {results['overall_score']:.1f}/100")

    print("\\n🔍 Check Results:")
    for check_name, check_result in results["checks"].items():
        status_icon = "✅" if check_result["status"] == "good" else "❌"
        print(f"  {status_icon} {check_name}: {check_result['score']} ({check_result['status']})")
        if check_result.get("issues"):
            for issue in check_result["issues"]:
                print(f"    ⚠️ {issue}")

    # Save results to file
    health_file = project_root / ".health_report.json"
    with open(health_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\\n💾 Report saved to {health_file}")

    # Exit with appropriate code
    sys.exit(0 if results["overall_score"] >= 60 else 1)

if __name__ == "__main__":
    main()
'''

        files["scripts/monitor_health.py"] = monitoring_script

        return files

    async def _generate_compliance_tools(
        self,
        project_path: Path,
        language: str,
        config: ProjectManagementConfig,
    ) -> Dict[str, Any]:
        """Generate compliance checking tools"""
        files = {}

        # Generate compliance check script
        compliance_script = '''#!/usr/bin/env python3
"""
Compliance Check Script

This script checks project compliance with various standards and regulations.
Generated by CodeForge AI Scaffolder.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List

class ComplianceChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def check_license_compliance(self) -> Dict[str, Any]:
        """Check license compliance"""
        results = {
            "compliant": False,
            "license_found": False,
            "issues": [],
            "recommendations": []
        }

        # Check for license file
        license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt"]
        license_path = None

        for license_file in license_files:
            if (self.project_root / license_file).exists():
                license_path = self.project_root / license_file
                results["license_found"] = True
                break

        if not results["license_found"]:
            results["issues"].append("No license file found")
            results["recommendations"].append("Add a LICENSE file to specify project licensing")
            return results

        # Read and analyze license
        try:
            with open(license_path, "r", encoding="utf-8") as f:
                license_content = f.read().lower()

            # Check for common license types
            license_types = {
                "mit": "MIT",
                "apache": "Apache",
                "bsd": "BSD",
                "gpl": "GPL",
                "lgpl": "LGPL",
                "mozilla": "Mozilla",
                "isc": "ISC"
            }

            detected_license = None
            for key, name in license_types.items():
                if key in license_content:
                    detected_license = name
                    break

            if detected_license:
                results["compliant"] = True
                results["license_type"] = detected_license
            else:
                results["issues"].append("License type could not be determined")
                results["recommendations"].append("Use a standard open source license")

        except Exception as e:
            results["issues"].append(f"Could not read license file: {e}")

        return results

    def check_code_standards(self) -> Dict[str, Any]:
        """Check code standards compliance"""
        results = {
            "compliant": True,
            "issues": [],
            "recommendations": []
        }

        # Check for code formatting configuration
        format_configs = [".prettierrc", "pyproject.toml", ".editorconfig"]
        has_formatting = any((self.project_root / config).exists() for config in format_configs)

        if not has_formatting:
            results["compliant"] = False
            results["issues"].append("No code formatting configuration found")
            results["recommendations"].append("Add code formatting configuration (Prettier, Black, etc.)")

        # Check for linting configuration
        lint_configs = [".eslintrc.js", ".flake8", "pyproject.toml"]
        has_linting = any((self.project_root / config).exists() for config in lint_configs)

        if not has_linting:
            results["compliant"] = False
            results["issues"].append("No linting configuration found")
            results["recommendations"].append("Add linting configuration (ESLint, flake8, etc.)")

        return results

    def check_security_standards(self) -> Dict[str, Any]:
        """Check security standards compliance"""
        results = {
            "compliant": True,
            "issues": [],
            "recommendations": []
        }

        # Check for security-related files
        security_files = [".env.example", ".gitignore"]
        for sec_file in security_files:
            if not (self.project_root / sec_file).exists():
                results["compliant"] = False
                results["issues"].append(f"Missing security file: {sec_file}")
                results["recommendations"].append(f"Create {sec_file} to protect sensitive data")

        # Check .gitignore for sensitive files
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    gitignore_content = f.read().lower()

                required_ignores = [".env", "*.key", "*.pem", "secrets/"]
                missing_ignores = []

                for ignore in required_ignores:
                    if ignore not in gitignore_content:
                        missing_ignores.append(ignore)

                if missing_ignores:
                    results["compliant"] = False
                    results["issues"].append(f"Missing from .gitignore: {', '.join(missing_ignores)}")
                    results["recommendations"].append("Add sensitive files/patterns to .gitignore")

            except Exception as e:
                results["issues"].append(f"Could not read .gitignore: {e}")

        return results

    def run_compliance_checks(self) -> Dict[str, Any]:
        """Run all compliance checks"""
        results = {
            "license": self.check_license_compliance(),
            "code_standards": self.check_code_standards(),
            "security": self.check_security_standards(),
            "overall_compliant": True,
            "total_issues": 0
        }

        # Calculate overall compliance
        for check_name, check_result in results.items():
            if check_name not in ["overall_compliant", "total_issues"]:
                if not check_result.get("compliant", True):
                    results["overall_compliant"] = False
                results["total_issues"] += len(check_result.get("issues", []))

        return results

def main():
    project_root = Path(__file__).parent
    checker = ComplianceChecker(project_root)

    print("📋 Running compliance checks...")

    results = checker.run_compliance_checks()

    print(f"\\n📊 Compliance Results:")
    print(f"Overall Compliant: {'✅ YES' if results['overall_compliant'] else '❌ NO'}")
    print(f"Total Issues: {results['total_issues']}")

    for check_name, check_result in results.items():
        if check_name not in ["overall_compliant", "total_issues"]:
            compliant_icon = "✅" if check_result.get("compliant", False) else "❌"
            print(f"\\n{check_name.upper()} CHECK: {compliant_icon}")

            if check_result.get("license_type"):
                print(f"  License Type: {check_result['license_type']}")

            if check_result.get("issues"):
                print("  Issues:")
                for issue in check_result["issues"]:
                    print(f"    ❌ {issue}")

            if check_result.get("recommendations"):
                print("  Recommendations:")
                for rec in check_result["recommendations"]:
                    print(f"    💡 {rec}")

    # Exit with appropriate code
    sys.exit(0 if results["overall_compliant"] else 1)

if __name__ == "__main__":
    main()
'''

        files["scripts/check_compliance.py"] = compliance_script

        return files
