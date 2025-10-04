import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class TemplateManager:
    """Manages predefined project templates for hybrid scaffolding"""

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            self.templates_dir = current_dir / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        self._templates_cache: Dict[str, Dict[str, Any]] = {}

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of all available templates"""
        templates = []

        if not self.templates_dir.exists():
            return templates

        # Scan for template.json files
        for template_json in self.templates_dir.rglob("template.json"):
            try:
                with open(template_json, "r", encoding="utf-8") as f:
                    template_data = json.load(f)

                # Add template path info
                template_data["template_path"] = str(template_json.parent)
                template_data["template_key"] = self._get_template_key(template_json)

                templates.append(template_data)
            except Exception as e:
                # Skip invalid templates
                continue

        return templates

    def get_template(
        self,
        language: str,
        framework: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific template by criteria"""
        cache_key = f"{language}_{framework}_{project_type}"

        if cache_key in self._templates_cache:
            return self._templates_cache[cache_key]

        # Find matching template
        templates = self.get_available_templates()

        for template in templates:
            if (
                template.get("language") == language
                and template.get("framework") == framework
                and template.get("project_type") == project_type
            ):
                self._templates_cache[cache_key] = template
                return template

        # Try fallback matching (language + framework only)
        if framework:
            fallback_key = f"{language}_{framework}_None"
            if fallback_key not in self._templates_cache:
                for template in templates:
                    if (
                        template.get("language") == language
                        and template.get("framework") == framework
                    ):
                        self._templates_cache[fallback_key] = template
                        return template

        # Try language-only fallback
        lang_key = f"{language}_None_None"
        if lang_key not in self._templates_cache:
            for template in templates:
                if template.get("language") == language:
                    self._templates_cache[lang_key] = template
                    return template

        return None

    def load_template_from_path(self, template_path: str) -> Optional[Dict[str, Any]]:
        """Load a template from a specific path"""
        template_json = Path(template_path) / "template.json"

        if not template_json.exists():
            return None

        try:
            with open(template_json, "r", encoding="utf-8") as f:
                template_data = json.load(f)
            template_data["template_path"] = str(template_path)
            return template_data
        except Exception:
            return None

    def customize_template(
        self, template: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Customize template with project-specific configuration"""
        customized = json.loads(json.dumps(template))  # Deep copy

        # Replace template variables
        project_name = config.get("project_name", "")
        replacements = {
            "{{project_name}}": project_name,
            "{{PROJECT_NAME}}": project_name.upper(),
            "{{project-name}}": project_name.lower().replace(" ", "-"),
        }

        # Customize file contents
        for file_path, file_info in customized.get("files", {}).items():
            content = file_info.get("content", "")
            for placeholder, replacement in replacements.items():
                content = content.replace(placeholder, replacement)
            file_info["content"] = content

        # Update template metadata
        customized["project_name"] = project_name

        return customized

    def _get_template_key(self, template_json: Path) -> str:
        """Generate a unique key for template caching"""
        relative_path = template_json.relative_to(self.templates_dir)
        return str(relative_path.parent).replace(os.sep, "_")
