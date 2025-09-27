import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from src.core.base_module import BaseModule, ModuleConfig, ModuleResult
from src.core.ai_utils import AIUtils


class VulnerabilitySentinelConfig(ModuleConfig):
    """Configuration for Vulnerability Sentinel"""

    name: str = "sentinel"
    scan_path: str
    scan_depth: int = 3  # How many levels deep to scan
    include_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"]
    exclude_patterns: List[str] = [
        "__pycache__",
        "node_modules",
        ".git",
        "venv",
        ".env",
    ]
    severity_threshold: str = "medium"  # low, medium, high, critical
    enable_ai_analysis: bool = True


class Sentinel(BaseModule):
    """AI-powered vulnerability scanning module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.description_text = (
            "Scans codebases for security vulnerabilities using AI analysis"
        )
        self.version = "1.0.0"

        # Common vulnerability patterns
        self.vulnerability_patterns = {
            "hardcoded_secrets": {
                "pattern": r"(?i)(password|secret|key|token)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
                "severity": "high",
                "description": "Hardcoded secrets or credentials",
            },
            "sql_injection": {
                "pattern": r"(?i)(SELECT|INSERT|UPDATE|DELETE).*\+\s*.*",
                "severity": "critical",
                "description": "Potential SQL injection vulnerability",
            },
            "xss_vulnerable": {
                "pattern": r"innerHTML\s*[=]\s*.*\+.*",
                "severity": "high",
                "description": "Potential XSS vulnerability with innerHTML",
            },
            "weak_crypto": {
                "pattern": r"(?i)(md5|sha1)\(",
                "severity": "medium",
                "description": "Weak cryptographic hash functions",
            },
            "insecure_random": {
                "pattern": r"(?i)random\.",
                "severity": "low",
                "description": "Use of insecure random number generation",
            },
        }

    def get_description(self) -> str:
        """Get human-readable description of the module"""
        return self.description_text

    async def execute(self, input_data: Dict[str, Any]) -> ModuleResult:
        """Execute the vulnerability scan"""
        try:
            # Convert input_data to config
            config = VulnerabilitySentinelConfig(**input_data)

            # Perform the scan
            scan_results = await self._perform_scan(config)

            # Generate report
            report = self._generate_report(scan_results, config)

            return ModuleResult(
                success=True,
                data={
                    "scan_path": config.scan_path,
                    "vulnerabilities_found": len(scan_results),
                    "report": report,
                    "message": f"Security scan completed. Found {len(scan_results)} potential vulnerabilities.",
                },
            )

        except Exception as e:
            return ModuleResult(
                success=False, error=f"Vulnerability scan failed: {str(e)}"
            )

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution"""
        try:
            config = VulnerabilitySentinelConfig(**input_data)
            # Validate scan path exists
            scan_path = Path(config.scan_path)
            return scan_path.exists() and scan_path.is_dir()
        except Exception:
            return False

    async def _perform_scan(
        self, config: VulnerabilitySentinelConfig
    ) -> List[Dict[str, Any]]:
        """Perform the vulnerability scan"""
        vulnerabilities = []

        # First, do pattern-based scanning
        pattern_vulns = self._scan_with_patterns(config)
        vulnerabilities.extend(pattern_vulns)

        # Then, use AI for deeper analysis if enabled
        if config.enable_ai_analysis:
            ai_vulns = await self._scan_with_ai(config)
            vulnerabilities.extend(ai_vulns)

        return vulnerabilities

    def _scan_with_patterns(
        self, config: VulnerabilitySentinelConfig
    ) -> List[Dict[str, Any]]:
        """Scan using predefined vulnerability patterns"""
        vulnerabilities = []
        scan_path = Path(config.scan_path)

        for file_path in self._get_files_to_scan(config):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    for vuln_type, vuln_info in self.vulnerability_patterns.items():
                        matches = re.finditer(vuln_info["pattern"], line)
                        for match in matches:
                            if self._should_report_severity(
                                vuln_info["severity"], config.severity_threshold
                            ):
                                vulnerabilities.append(
                                    {
                                        "type": vuln_type,
                                        "severity": vuln_info["severity"],
                                        "description": vuln_info["description"],
                                        "file": str(file_path.relative_to(scan_path)),
                                        "line": line_num,
                                        "code_snippet": line.strip(),
                                        "matched_text": match.group(0),
                                        "detection_method": "pattern_matching",
                                    }
                                )

            except Exception as e:
                # Skip files that can't be read
                continue

        return vulnerabilities

    async def _scan_with_ai(
        self, config: VulnerabilitySentinelConfig
    ) -> List[Dict[str, Any]]:
        """Use AI to analyze code for vulnerabilities"""
        vulnerabilities = []
        scan_path = Path(config.scan_path)

        # Sample a few key files for AI analysis
        key_files = self._get_key_files_for_ai_analysis(config)

        for file_path in key_files[:5]:  # Limit to 5 files for AI analysis
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Limit content size for AI analysis
                if len(content) > 5000:
                    content = content[:5000] + "\n... (truncated)"

                ai_findings = await self._analyze_file_with_ai(
                    file_path, content, config
                )
                vulnerabilities.extend(ai_findings)

            except Exception as e:
                continue

        return vulnerabilities

    async def _analyze_file_with_ai(
        self, file_path: Path, content: str, config: VulnerabilitySentinelConfig
    ) -> List[Dict[str, Any]]:
        """Use AI to analyze a specific file for vulnerabilities"""

        prompt = f"""
        Analyze the following code file for security vulnerabilities. Focus on:

        1. Authentication and authorization issues
        2. Input validation problems
        3. Data exposure risks
        4. Injection vulnerabilities
        5. Cryptographic weaknesses
        6. Configuration issues

        File: {file_path.name}
        Language: {file_path.suffix}

        Code:
        ```{file_path.suffix[1:] if file_path.suffix else 'text'}
        {content}
        ```

        Provide a JSON response with any vulnerabilities found in this format:
        [
            {{
                "type": "vulnerability_type",
                "severity": "low|medium|high|critical",
                "description": "Brief description of the vulnerability",
                "line": "approximate line number or 'unknown'",
                "code_snippet": "relevant code snippet",
                "recommendation": "How to fix it"
            }}
        ]

        Only include actual vulnerabilities. If none found, return an empty array.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=2000)

            try:
                ai_vulns = json.loads(response)
                # Add metadata
                for vuln in ai_vulns:
                    vuln["file"] = str(file_path.name)
                    vuln["detection_method"] = "ai_analysis"
                    vuln["matched_text"] = vuln.get("code_snippet", "")

                return ai_vulns

            except json.JSONDecodeError:
                return []

        except Exception:
            return []

    def _get_files_to_scan(self, config: VulnerabilitySentinelConfig) -> List[Path]:
        """Get list of files to scan based on include/exclude patterns"""
        scan_path = Path(config.scan_path)
        files_to_scan = []

        def should_include_file(file_path: Path) -> bool:
            # Check exclude patterns
            for exclude in config.exclude_patterns:
                if exclude in str(file_path):
                    return False

            # Check include patterns
            for include in config.include_patterns:
                if file_path.match(include):
                    return True

            return False

        for root, dirs, files in os.walk(scan_path):
            # Respect scan depth
            rel_root = Path(root).relative_to(scan_path)
            if len(rel_root.parts) > config.scan_depth:
                continue

            # Filter directories
            dirs[:] = [
                d
                for d in dirs
                if not any(excl in d for excl in config.exclude_patterns)
            ]

            for file in files:
                file_path = Path(root) / file
                if should_include_file(file_path):
                    files_to_scan.append(file_path)

        return files_to_scan

    def _get_key_files_for_ai_analysis(
        self, config: VulnerabilitySentinelConfig
    ) -> List[Path]:
        """Get key files that should be prioritized for AI analysis"""
        files = self._get_files_to_scan(config)

        # Prioritize files that are likely to contain security-critical code
        priority_files = []
        for file_path in files:
            filename = file_path.name.lower()
            if any(
                keyword in filename
                for keyword in [
                    "config",
                    "settings",
                    "auth",
                    "security",
                    "login",
                    "password",
                    "database",
                    "api",
                    "main",
                    "app",
                    "server",
                ]
            ):
                priority_files.append(file_path)

        # If we don't have enough priority files, add others
        if len(priority_files) < 5:
            for file_path in files:
                if file_path not in priority_files:
                    priority_files.append(file_path)
                    if len(priority_files) >= 5:
                        break

        return priority_files

    def _should_report_severity(self, vuln_severity: str, threshold: str) -> bool:
        """Check if vulnerability severity meets the threshold"""
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return severity_levels.get(vuln_severity, 0) >= severity_levels.get(
            threshold, 2
        )

    def _generate_report(
        self, vulnerabilities: List[Dict[str, Any]], config: VulnerabilitySentinelConfig
    ) -> Dict[str, Any]:
        """Generate a comprehensive vulnerability report"""

        # Group vulnerabilities by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        file_counts = {}

        for vuln in vulnerabilities:
            severity_counts[vuln["severity"]] += 1
            file_counts[vuln["file"]] = file_counts.get(vuln["file"], 0) + 1

        # Group by type
        type_counts = {}
        for vuln in vulnerabilities:
            vuln_type = vuln["type"]
            type_counts[vuln_type] = type_counts.get(vuln_type, 0) + 1

        return {
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "severity_breakdown": severity_counts,
                "files_affected": len(file_counts),
                "vulnerability_types": type_counts,
            },
            "vulnerabilities": vulnerabilities,
            "scan_configuration": {
                "scan_path": config.scan_path,
                "severity_threshold": config.severity_threshold,
                "ai_analysis_enabled": config.enable_ai_analysis,
                "files_scanned": len(self._get_files_to_scan(config)),
            },
        }
