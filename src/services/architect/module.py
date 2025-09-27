import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import re

from src.core.base_module import BaseModule, ModuleConfig, ModuleResult
from src.core.ai_utils import AIUtils


class CodeArchitectConfig(ModuleConfig):
    """Configuration for Code Architect"""

    name: str = "architect"
    source_path: str
    analysis_type: str = (
        "comprehensive"  # comprehensive, refactoring, performance, architecture
    )
    include_patterns: List[str] = ["*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"]
    exclude_patterns: List[str] = [
        "__pycache__",
        "node_modules",
        ".git",
        "venv",
        ".env",
    ]
    max_files: int = 10  # Maximum number of files to analyze
    focus_areas: List[str] = [
        "performance",
        "maintainability",
        "security",
        "architecture",
    ]


class Architect(BaseModule):
    """AI-powered code analysis and refactoring suggestions module"""

    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.ai_utils = AIUtils()
        self.description_text = (
            "Analyzes code for improvements and provides refactoring suggestions"
        )
        self.version = "1.0.0"

        # Code quality patterns and anti-patterns
        self.code_patterns = {
            "long_functions": {
                "pattern": r"def \w+\([^)]*\):(?:\n\s+.*){30,}",  # Functions with 30+ lines
                "severity": "medium",
                "category": "maintainability",
                "description": "Function is too long and should be broken down",
            },
            "deep_nesting": {
                "pattern": r"(\s+)if.*:\n\1\s+if.*:\n\1\s+if.*:",  # 3+ levels of nesting
                "severity": "medium",
                "category": "maintainability",
                "description": "Deep nesting makes code hard to read",
            },
            "magic_numbers": {
                "pattern": r"(?<!\w)[0-9]{2,}(?!\w)",  # Numbers >= 10 not assigned to variables
                "severity": "low",
                "category": "maintainability",
                "description": "Magic numbers should be replaced with named constants",
            },
            "large_classes": {
                "pattern": r"class \w+:\n(?:\s+.*\n){100,}",  # Classes with 100+ lines
                "severity": "high",
                "category": "architecture",
                "description": "Class is too large and should be split",
            },
            "global_variables": {
                "pattern": r"^[A-Z][A-Z_]*\s*=\s*",
                "severity": "medium",
                "category": "architecture",
                "description": "Global variables can make code unpredictable",
            },
        }

    def get_description(self) -> str:
        """Get human-readable description of the module"""
        return self.description_text

    async def execute(self, input_data: Dict[str, Any]) -> ModuleResult:
        """Execute the code analysis"""
        try:
            # Convert input_data to config
            config = CodeArchitectConfig(**input_data)

            # Analyze the codebase
            analysis = await self._analyze_codebase(config)

            # Generate recommendations
            recommendations = await self._generate_recommendations(analysis, config)

            # Create report
            report = self._generate_report(analysis, recommendations, config)

            return ModuleResult(
                success=True,
                data={
                    "source_path": config.source_path,
                    "analysis_type": config.analysis_type,
                    "files_analyzed": len(analysis.get("files", [])),
                    "issues_found": len(analysis.get("issues", [])),
                    "recommendations": len(recommendations),
                    "report": report,
                    "message": f"Code analysis completed. Found {len(analysis.get('issues', []))} issues and {len(recommendations)} recommendations.",
                },
            )

        except Exception as e:
            return ModuleResult(success=False, error=f"Code analysis failed: {str(e)}")

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before execution"""
        try:
            config = CodeArchitectConfig(**input_data)
            # Validate source path exists
            source_path = Path(config.source_path)
            return source_path.exists() and source_path.is_dir()
        except Exception:
            return False

    async def _analyze_codebase(self, config: CodeArchitectConfig) -> Dict[str, Any]:
        """Analyze the codebase for issues and patterns"""
        source_path = Path(config.source_path)
        analysis = {"files": [], "issues": [], "metrics": {}, "structure": {}}

        # Get files to analyze
        files_to_analyze = self._get_files_to_analyze(config)

        for file_path in files_to_analyze[: config.max_files]:  # Limit files
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Analyze individual file
                file_analysis = await self._analyze_file(file_path, content, config)
                analysis["files"].append(file_analysis)

                # Collect issues
                analysis["issues"].extend(file_analysis.get("issues", []))

            except Exception as e:
                # Skip files that can't be analyzed
                continue

        # Calculate overall metrics
        analysis["metrics"] = self._calculate_metrics(analysis)

        return analysis

    async def _analyze_file(
        self, file_path: Path, content: str, config: CodeArchitectConfig
    ) -> Dict[str, Any]:
        """Analyze a single file"""
        issues = []

        # Pattern-based analysis
        pattern_issues = self._analyze_patterns(file_path, content, config)
        issues.extend(pattern_issues)

        # AI-based analysis
        ai_analysis = await self._analyze_with_ai(file_path, content, config)
        issues.extend(ai_analysis.get("issues", []))

        # Calculate file metrics
        metrics = self._calculate_file_metrics(content)

        return {
            "file_path": str(file_path),
            "issues": issues,
            "metrics": metrics,
            "language": self._detect_language(file_path),
            "size": len(content),
        }

    def _analyze_patterns(
        self, file_path: Path, content: str, config: CodeArchitectConfig
    ) -> List[Dict[str, Any]]:
        """Analyze code using predefined patterns"""
        issues = []
        lines = content.split("\n")

        for pattern_name, pattern_info in self.code_patterns.items():
            if pattern_info["category"] in config.focus_areas:
                matches = re.finditer(pattern_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    # Find line number
                    line_num = content[: match.start()].count("\n") + 1

                    issues.append(
                        {
                            "type": pattern_name,
                            "severity": pattern_info["severity"],
                            "category": pattern_info["category"],
                            "description": pattern_info["description"],
                            "file": str(file_path),
                            "line": line_num,
                            "code_snippet": (
                                lines[line_num - 1].strip()
                                if line_num <= len(lines)
                                else ""
                            ),
                            "detection_method": "pattern_matching",
                        }
                    )

        return issues

    async def _analyze_with_ai(
        self, file_path: Path, content: str, config: CodeArchitectConfig
    ) -> Dict[str, Any]:
        """Use AI to analyze code for improvements"""

        # Limit content for AI analysis
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"

        prompt = f"""
        Analyze the following code file for potential improvements, refactoring opportunities, and architectural issues.

        File: {file_path.name}
        Language: {self._detect_language(file_path)}
        Focus Areas: {', '.join(config.focus_areas)}

        Code:
        ```{self._detect_language(file_path)}
        {content}
        ```

        Provide a JSON response with potential issues and improvements:
        {{
            "issues": [
                {{
                    "type": "issue_type",
                    "severity": "low|medium|high|critical",
                    "category": "performance|maintainability|security|architecture",
                    "description": "Brief description of the issue",
                    "line": "approximate line number",
                    "code_snippet": "relevant code snippet",
                    "suggestion": "How to fix or improve it"
                }}
            ],
            "overall_assessment": "Brief assessment of code quality",
            "strengths": ["list", "of", "code", "strengths"],
            "weaknesses": ["list", "of", "code", "weaknesses"]
        }}

        Focus on the specified focus areas. Be constructive and provide actionable suggestions.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=2000)

            try:
                ai_analysis = json.loads(response)
                # Add metadata to issues
                for issue in ai_analysis.get("issues", []):
                    issue["file"] = str(file_path)
                    issue["detection_method"] = "ai_analysis"

                return ai_analysis

            except json.JSONDecodeError:
                return {
                    "issues": [],
                    "overall_assessment": "Analysis failed",
                    "strengths": [],
                    "weaknesses": [],
                }

        except Exception:
            return {
                "issues": [],
                "overall_assessment": "Analysis failed",
                "strengths": [],
                "weaknesses": [],
            }

    def _calculate_file_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate metrics for a single file"""
        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "complexity_estimate": len(
                re.findall(r"\b(if|for|while|def|class)\b", content)
            ),
            "comment_ratio": len(re.findall(r"#.*", content))
            / max(1, len(non_empty_lines)),
        }

    def _calculate_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall codebase metrics"""
        files = analysis.get("files", [])
        issues = analysis.get("issues", [])

        total_lines = sum(f.get("metrics", {}).get("total_lines", 0) for f in files)
        total_issues = len(issues)

        # Group issues by category and severity
        categories = {}
        severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for issue in issues:
            cat = issue.get("category", "unknown")
            sev = issue.get("severity", "low")

            categories[cat] = categories.get(cat, 0) + 1
            severities[sev] += 1

        return {
            "total_files": len(files),
            "total_lines": total_lines,
            "total_issues": total_issues,
            "issues_per_file": total_issues / max(1, len(files)),
            "issues_by_category": categories,
            "issues_by_severity": severities,
            "average_complexity": sum(
                f.get("metrics", {}).get("complexity_estimate", 0) for f in files
            )
            / max(1, len(files)),
        }

    async def _generate_recommendations(
        self, analysis: Dict[str, Any], config: CodeArchitectConfig
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""

        recommendations = []

        # Generate recommendations from issues
        for issue in analysis.get("issues", []):
            recommendation = {
                "type": (
                    "refactoring"
                    if issue["category"] == "maintainability"
                    else "improvement"
                ),
                "priority": self._calculate_priority(issue),
                "title": f"Fix {issue['type']} in {Path(issue['file']).name}",
                "description": issue["description"],
                "file": issue["file"],
                "line": issue.get("line"),
                "category": issue["category"],
                "effort": self._estimate_effort(issue),
                "impact": self._estimate_impact(issue),
                "suggestion": issue.get("suggestion", "Review and refactor this code"),
            }
            recommendations.append(recommendation)

        # Generate architectural recommendations
        if "architecture" in config.focus_areas:
            arch_recs = await self._generate_architectural_recommendations(
                analysis, config
            )
            recommendations.extend(arch_recs)

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return recommendations

    async def _generate_architectural_recommendations(
        self, analysis: Dict[str, Any], config: CodeArchitectConfig
    ) -> List[Dict[str, Any]]:
        """Generate high-level architectural recommendations"""

        prompt = f"""
        Based on the following codebase analysis, provide architectural recommendations for improvement.

        Analysis Summary:
        - Files analyzed: {len(analysis.get('files', []))}
        - Total issues: {len(analysis.get('issues', []))}
        - Metrics: {json.dumps(analysis.get('metrics', {}), indent=2)}

        Key Issues:
        {json.dumps(analysis.get('issues', [])[:10], indent=2)}  # First 10 issues

        Provide 3-5 high-level architectural recommendations in JSON format:
        [
            {{
                "title": "Recommendation title",
                "description": "Detailed description",
                "category": "architecture",
                "priority": 1-10 (10 being highest),
                "effort": "low|medium|high",
                "impact": "low|medium|high",
                "rationale": "Why this recommendation matters"
            }}
        ]

        Focus on structural improvements, design patterns, and scalability.
        """

        try:
            response = await self.ai_utils.generate_text(prompt, max_tokens=1500)

            try:
                arch_recs = json.loads(response)
                # Add metadata
                for rec in arch_recs:
                    rec["type"] = "architectural"
                    rec["file"] = (
                        None  # Architectural recommendations apply to whole codebase
                    )

                return arch_recs

            except json.JSONDecodeError:
                return []

        except Exception:
            return []

    def _calculate_priority(self, issue: Dict[str, Any]) -> int:
        """Calculate priority score for an issue (1-10)"""
        severity_scores = {"low": 1, "medium": 5, "high": 8, "critical": 10}
        category_multipliers = {
            "security": 1.5,
            "performance": 1.3,
            "architecture": 1.2,
            "maintainability": 1.0,
        }

        base_score = severity_scores.get(issue.get("severity", "low"), 1)
        multiplier = category_multipliers.get(
            issue.get("category", "maintainability"), 1.0
        )

        return min(10, int(base_score * multiplier))

    def _estimate_effort(self, issue: Dict[str, Any]) -> str:
        """Estimate implementation effort"""
        if issue.get("severity") == "critical":
            return "high"
        elif issue.get("category") == "architecture":
            return "high"
        elif issue.get("type", "").startswith(("long_", "large_")):
            return "medium"
        else:
            return "low"

    def _estimate_impact(self, issue: Dict[str, Any]) -> str:
        """Estimate impact of fixing the issue"""
        if issue.get("category") == "security":
            return "high"
        elif issue.get("severity") in ["high", "critical"]:
            return "high"
        elif issue.get("category") == "performance":
            return "medium"
        else:
            return "low"

    def _generate_report(
        self,
        analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        config: CodeArchitectConfig,
    ) -> Dict[str, Any]:
        """Generate a comprehensive analysis report"""

        return {
            "summary": {
                "analysis_type": config.analysis_type,
                "files_analyzed": len(analysis.get("files", [])),
                "total_issues": len(analysis.get("issues", [])),
                "total_recommendations": len(recommendations),
                "focus_areas": config.focus_areas,
            },
            "metrics": analysis.get("metrics", {}),
            "top_issues": analysis.get("issues", [])[:10],  # Top 10 issues
            "top_recommendations": recommendations[:10],  # Top 10 recommendations
            "issues_by_category": self._group_issues_by_category(
                analysis.get("issues", [])
            ),
            "issues_by_severity": self._group_issues_by_severity(
                analysis.get("issues", [])
            ),
            "file_summaries": [
                {
                    "file": f["file_path"],
                    "issues": len(f.get("issues", [])),
                    "metrics": f.get("metrics", {}),
                }
                for f in analysis.get("files", [])
            ],
        }

    def _group_issues_by_category(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group issues by category"""
        categories = {}
        for issue in issues:
            cat = issue.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return categories

    def _group_issues_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group issues by severity"""
        severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for issue in issues:
            sev = issue.get("severity", "low")
            severities[sev] += 1
        return severities

    def _get_files_to_analyze(self, config: CodeArchitectConfig) -> List[Path]:
        """Get list of files to analyze"""
        source_path = Path(config.source_path)
        files_to_analyze = []

        for root, dirs, files in os.walk(source_path):
            # Skip excluded directories
            dirs[:] = [
                d
                for d in dirs
                if not any(excl in d for excl in config.exclude_patterns)
            ]

            for file in files:
                file_path = Path(root) / file
                if self._should_analyze_file(file_path, config):
                    files_to_analyze.append(file_path)

        # Sort by size (smaller files first for better analysis distribution)
        files_to_analyze.sort(key=lambda x: x.stat().st_size)

        return files_to_analyze

    def _should_analyze_file(
        self, file_path: Path, config: CodeArchitectConfig
    ) -> bool:
        """Check if a file should be analyzed"""
        # Check include patterns
        for pattern in config.include_patterns:
            if file_path.match(pattern):
                return True
        return False

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".php": "php",
            ".rb": "ruby",
        }
        return language_map.get(ext, "unknown")
