import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
import httpx

from src.core.ai_utils import AIUtils


class DependencyManager:
    """Advanced dependency management with resolution, conflict detection, and security checking"""

    def __init__(self):
        self.ai_utils = AIUtils()
        self.dependency_cache: Dict[str, Dict[str, Any]] = {}
        self.vulnerability_cache: Dict[str, List[Dict[str, Any]]] = {}

    async def resolve_dependencies(
        self,
        language: str,
        framework: Optional[str] = None,
        features: Optional[List[str]] = None,
        existing_deps: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Resolve dependencies based on project requirements"""

        features = features or []
        existing_deps = existing_deps or []

        # Get base dependencies for the framework
        base_deps = await self._get_base_dependencies(language, framework)

        # Add feature-specific dependencies
        feature_deps = await self._get_feature_dependencies(language, features)

        # Merge and resolve conflicts
        all_deps = self._merge_dependencies([base_deps, feature_deps])

        # Add existing dependencies if provided
        if existing_deps:
            all_deps["dependencies"].extend(existing_deps)

        # Remove duplicates and resolve versions
        resolved = await self._resolve_versions(language, all_deps)

        # Check for security vulnerabilities
        vulnerabilities = await self._check_vulnerabilities(
            language, resolved["dependencies"]
        )

        return {
            "dependencies": resolved["dependencies"],
            "dev_dependencies": resolved.get("dev_dependencies", []),
            "conflicts": resolved.get("conflicts", []),
            "vulnerabilities": vulnerabilities,
            "recommendations": resolved.get("recommendations", []),
        }

    async def _get_base_dependencies(
        self, language: str, framework: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get base dependencies for a language/framework combination"""

        cache_key = f"base_{language}_{framework}"

        if cache_key in self.dependency_cache:
            return self.dependency_cache[cache_key]

        if language.lower() == "python":
            deps = await self._get_python_base_deps(framework)
        elif language.lower() in ["javascript", "typescript"]:
            deps = await self._get_javascript_base_deps(framework)
        else:
            deps = {"dependencies": [], "dev_dependencies": []}

        self.dependency_cache[cache_key] = deps
        return deps

    async def _get_python_base_deps(
        self, framework: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get Python base dependencies"""

        base_deps = {
            "dependencies": [],
            "dev_dependencies": [
                "pytest>=7.0.0",
                "black>=23.0.0",
                "isort>=5.12.0",
                "mypy>=1.0.0",
            ],
        }

        if framework:
            framework = framework.lower()
            if framework == "fastapi":
                base_deps["dependencies"].extend(
                    ["fastapi>=0.100.0", "uvicorn[standard]>=0.23.0", "pydantic>=2.0.0"]
                )
            elif framework == "django":
                base_deps["dependencies"].extend(
                    [
                        "django>=4.2.0",
                        "djangorestframework>=3.14.0",
                        "psycopg2-binary>=2.9.0",
                    ]
                )
            elif framework == "flask":
                base_deps["dependencies"].extend(
                    ["flask>=2.3.0", "flask-restful>=0.3.10"]
                )

        return base_deps

    async def _get_javascript_base_deps(
        self, framework: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get JavaScript base dependencies"""

        base_deps = {
            "dependencies": [],
            "dev_dependencies": [
                "jest>=29.0.0",
                "@types/jest>=29.0.0",
                "typescript>=5.0.0",
                "@types/node>=20.0.0",
                "eslint>=8.0.0",
                "@typescript-eslint/eslint-plugin>=6.0.0",
                "@typescript-eslint/parser>=6.0.0",
            ],
        }

        if framework:
            framework = framework.lower()
            if framework == "react":
                base_deps["dependencies"].extend(
                    ["react>=18.2.0", "react-dom>=18.2.0", "react-scripts>=5.0.0"]
                )
                base_deps["dev_dependencies"].extend(
                    ["@types/react>=18.2.0", "@types/react-dom>=18.2.0"]
                )
            elif framework == "vue":
                base_deps["dependencies"].extend(["vue>=3.3.0", "@vue/cli>=5.0.0"])
            elif framework == "angular":
                base_deps["dependencies"].extend(
                    ["@angular/core>=16.0.0", "@angular/cli>=16.0.0"]
                )

        return base_deps

    async def _get_feature_dependencies(
        self, language: str, features: List[str]
    ) -> Dict[str, List[str]]:
        """Get dependencies for specific features"""

        feature_deps = {"dependencies": [], "dev_dependencies": []}

        feature_map = {
            "authentication": {
                "python": [
                    "python-jose[cryptography]>=3.3.0",
                    "passlib[bcrypt]>=1.7.0",
                    "python-multipart>=0.0.6",
                ],
                "javascript": [
                    "jsonwebtoken>=9.0.0",
                    "bcryptjs>=2.4.0",
                    "passport>=0.6.0",
                ],
            },
            "database": {
                "python": ["sqlalchemy>=2.0.0", "alembic>=1.12.0"],
                "javascript": ["mongoose>=7.0.0", "pg>=8.11.0"],
            },
            "testing": {
                "python": ["pytest-cov>=4.1.0", "pytest-asyncio>=0.21.0"],
                "javascript": [
                    "@testing-library/react>=13.0.0",
                    "@testing-library/jest-dom>=5.16.0",
                ],
            },
            "logging": {"python": ["loguru>=0.7.0"], "javascript": ["winston>=3.8.0"]},
            "api_documentation": {"python": [], "javascript": []},
        }

        for feature in features:
            feature = feature.lower()
            if feature in feature_map and language in feature_map[feature]:
                deps = feature_map[feature][language]
                feature_deps["dependencies"].extend(deps)

        return feature_deps

    def _merge_dependencies(
        self, dep_lists: List[Dict[str, List[str]]]
    ) -> Dict[str, List[str]]:
        """Merge multiple dependency lists"""

        merged = {"dependencies": [], "dev_dependencies": []}

        for dep_list in dep_lists:
            merged["dependencies"].extend(dep_list.get("dependencies", []))
            merged["dev_dependencies"].extend(dep_list.get("dev_dependencies", []))

        return merged

    async def _resolve_versions(
        self, language: str, deps: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Resolve dependency versions and detect conflicts"""

        resolved = {
            "dependencies": [],
            "dev_dependencies": [],
            "conflicts": [],
            "recommendations": [],
        }

        # Simple version resolution - in a real implementation, this would use
        # package manager APIs or dependency resolution algorithms
        for dep_type in ["dependencies", "dev_dependencies"]:
            seen_packages = {}
            conflicts = []

            for dep in deps.get(dep_type, []):
                package, version = self._parse_dependency(dep)

                if package in seen_packages:
                    existing_version = seen_packages[package]
                    if version != existing_version:
                        conflicts.append(
                            {
                                "package": package,
                                "versions": [existing_version, version],
                            }
                        )
                    # Keep the higher version
                    if self._compare_versions(version, existing_version) > 0:
                        seen_packages[package] = version
                else:
                    seen_packages[package] = version

            # Reconstruct dependency strings
            resolved[dep_type] = [f"{pkg}{ver}" for pkg, ver in seen_packages.items()]

            if conflicts:
                resolved["conflicts"].extend(conflicts)

        return resolved

    def _parse_dependency(self, dep: str) -> Tuple[str, str]:
        """Parse dependency string into package and version"""

        # Handle various version specifiers
        match = re.match(r"^([a-zA-Z0-9\-_.]+)(.*)$", dep)
        if match:
            package = match.group(1)
            version = match.group(2) or ""
            return package, version

        return dep, ""

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal"""

        # Simple version comparison - in production, use packaging.version
        def normalize_version(v):
            return [int(x) for x in re.findall(r"\d+", v)]

        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)

        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0

            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1

        return 0

    async def _check_vulnerabilities(
        self, language: str, dependencies: List[str]
    ) -> List[Dict[str, Any]]:
        """Check dependencies for known security vulnerabilities"""

        vulnerabilities = []

        # In a real implementation, this would query vulnerability databases
        # like OSV (Open Source Vulnerabilities), NVD, or package manager APIs

        # Mock vulnerability checking for demonstration
        vulnerable_packages = {"old-package": "1.0.0", "insecure-lib": "<2.0.0"}

        for dep in dependencies:
            package, version = self._parse_dependency(dep)

            for vuln_pkg, vuln_version in vulnerable_packages.items():
                if package == vuln_pkg:
                    if self._version_matches_constraint(version, vuln_version):
                        vulnerabilities.append(
                            {
                                "package": package,
                                "version": version,
                                "vulnerability": f"Known security issue in {package} {version}",
                                "severity": "HIGH",
                                "recommendation": f"Upgrade to {package} >= {self._get_next_version(version)}",
                            }
                        )

        return vulnerabilities

    def _version_matches_constraint(self, version: str, constraint: str) -> bool:
        """Check if version matches a constraint"""

        # Simple constraint checking - in production, use packaging.specifiers
        if constraint.startswith("<"):
            constraint_version = constraint[1:]
            return self._compare_versions(version, constraint_version) < 0
        elif constraint.startswith(">"):
            constraint_version = constraint[1:]
            return self._compare_versions(version, constraint_version) > 0
        else:
            return version == constraint

    def _get_next_version(self, version: str) -> str:
        """Get next higher version (simplified)"""

        # Simple version bumping - in production, use proper version handling
        parts = version.split(".")
        if len(parts) >= 2:
            parts[-2] = str(int(parts[-2]) + 1)
            parts[-1] = "0"
            return ".".join(parts)

        return version
