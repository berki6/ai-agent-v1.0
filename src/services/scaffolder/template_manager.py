import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from functools import lru_cache
from collections import OrderedDict


class LRUCache:
    """Thread-safe LRU cache with time-based expiration"""

    def __init__(self, capacity: int = 100, ttl_seconds: int = 3600):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = False  # Simple lock for thread safety

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache if it exists and hasn't expired"""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]

        # Check if expired
        if time.time() - timestamp > self.ttl:
            self.cache.pop(key)
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return value

    def put(self, key: str, value: Any) -> None:
        """Put item in cache"""
        timestamp = time.time()

        if key in self.cache:
            # Update existing
            self.cache[key] = (value, timestamp)
            self.cache.move_to_end(key)
        else:
            # Add new
            self.cache[key] = (value, timestamp)

            # Remove oldest if over capacity
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Remove specific key from cache"""
        self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def cleanup_expired(self) -> int:
        """Remove expired entries, return number removed"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]

        for key in expired_keys:
            self.cache.pop(key, None)

        return len(expired_keys)


class TemplateManager:
    """Manages predefined project templates for hybrid scaffolding"""

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        cache_capacity: int = 50,
        cache_ttl: int = 1800,
        lazy_loading: bool = True,
    ):
        if templates_dir is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            self.templates_dir = current_dir / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        # Advanced LRU cache with TTL
        self._templates_cache = LRUCache(capacity=cache_capacity, ttl_seconds=cache_ttl)
        self._available_templates_cache: Optional[
            Tuple[List[Dict[str, Any]], float]
        ] = None
        self._available_templates_ttl = 300  # 5 minutes for available templates list

        # Memory optimization settings
        self._max_template_size = 10 * 1024 * 1024  # 10MB max template size
        self._chunk_size = 1024 * 1024  # 1MB chunks for streaming

        # Lazy loading settings
        self._lazy_loading = lazy_loading
        self._template_index: Optional[Dict[str, Path]] = (
            None  # Maps template keys to paths
        )

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of all available templates with caching and lazy loading support"""
        current_time = time.time()

        # Check if we have cached available templates and they're still valid
        if (
            self._available_templates_cache is not None
            and current_time - self._available_templates_cache[1]
            < self._available_templates_ttl
        ):
            return self._available_templates_cache[0]

        if self._lazy_loading:
            # Lazy loading mode: build index and return lightweight template info
            return self._get_available_templates_lazy()
        else:
            # Eager loading mode: load all templates
            return self._get_available_templates_eager()

    def _get_available_templates_eager(self) -> List[Dict[str, Any]]:
        """Eager loading: Load all templates immediately"""
        current_time = time.time()
        templates = []

        if not self.templates_dir.exists():
            # Cache empty result
            self._available_templates_cache = (templates, current_time)
            return templates

        # Scan for template.json files and load them
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

        # Cache the result
        self._available_templates_cache = (templates, current_time)
        return templates

    def _get_available_templates_lazy(self) -> List[Dict[str, Any]]:
        """Lazy loading: Build index of templates without loading them"""
        current_time = time.time()

        if self._template_index is None:
            self._build_template_index()

        templates = []

        if not self.templates_dir.exists():
            # Cache empty result
            self._available_templates_cache = (templates, current_time)
            return templates

        # Return lightweight template info from index
        if self._template_index:
            for template_key, template_path in self._template_index.items():
                try:
                    # Load only minimal info for listing (language, framework, etc.)
                    minimal_info = self._load_template_metadata(template_path)
                    if minimal_info:
                        templates.append(minimal_info)
                except Exception:
                    continue

        # Cache the result
        self._available_templates_cache = (templates, current_time)
        return templates

    def _build_template_index(self) -> None:
        """Build an index of template paths for lazy loading"""
        self._template_index = {}

        if not self.templates_dir.exists():
            return

        for template_json in self.templates_dir.rglob("template.json"):
            template_key = self._get_template_key(template_json)
            self._template_index[template_key] = template_json

    def _load_template_metadata(self, template_path: Path) -> Optional[Dict[str, Any]]:
        """Load only essential metadata from a template for lazy loading"""
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)

            # Return only essential metadata to keep memory usage low
            metadata = {
                "template_path": str(template_path.parent),
                "template_key": self._get_template_key(template_path),
                "language": template_data.get("language"),
                "framework": template_data.get("framework"),
                "project_type": template_data.get("project_type"),
                "name": template_data.get("name", "Unknown Template"),
                "description": template_data.get("description", ""),
                # Don't load files, directories, etc. until actually needed
            }

            return metadata
        except Exception:
            return None

    def get_template(
        self,
        language: str,
        framework: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific template by criteria with advanced caching and lazy loading"""
        cache_key = f"{language}_{framework}_{project_type}"

        # Check cache first
        cached_template = self._templates_cache.get(cache_key)
        if cached_template is not None:
            return cached_template

        # Find matching template
        if self._lazy_loading:
            template = self._find_template_lazy(language, framework, project_type)
        else:
            templates = self.get_available_templates()
            template = self._find_template_from_list(
                templates, language, framework, project_type
            )

        if template:
            self._templates_cache.put(cache_key, template)
            return template

        return None

    def _find_template_lazy(
        self,
        language: str,
        framework: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find and load a template using lazy loading approach"""
        if self._template_index is None:
            self._build_template_index()

        if not self._template_index:
            return None

        # Look for exact match first
        for template_path in self._template_index.values():
            try:
                # Load full template to check criteria
                full_template = self.load_template_from_path(str(template_path.parent))
                if (
                    full_template
                    and full_template.get("language") == language
                    and full_template.get("framework") == framework
                    and full_template.get("project_type") == project_type
                ):
                    return full_template
            except Exception:
                continue

        # Try fallback matching
        for template_path in self._template_index.values():
            try:
                full_template = self.load_template_from_path(str(template_path.parent))
                if not full_template:
                    continue

                # Language + framework fallback
                if (
                    framework
                    and full_template.get("language") == language
                    and full_template.get("framework") == framework
                ):
                    return full_template

                # Language-only fallback
                if full_template.get("language") == language:
                    return full_template
            except Exception:
                continue

        return None

    def _find_template_from_list(
        self,
        templates: List[Dict[str, Any]],
        language: str,
        framework: Optional[str] = None,
        project_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find template from pre-loaded template list (eager loading)"""
        for template in templates:
            if (
                template.get("language") == language
                and template.get("framework") == framework
                and template.get("project_type") == project_type
            ):
                return template

        # Try fallback matching (language + framework only)
        if framework:
            for template in templates:
                if (
                    template.get("language") == language
                    and template.get("framework") == framework
                ):
                    return template

        # Try language-only fallback
        for template in templates:
            if template.get("language") == language:
                return template

        return None

    def load_template_from_path(self, template_path: str) -> Optional[Dict[str, Any]]:
        """Load a template from a specific path with memory optimization"""
        template_json = Path(template_path) / "template.json"

        if not template_json.exists():
            return None

        # Check file size for memory optimization
        file_size = template_json.stat().st_size
        if file_size > self._max_template_size:
            # Use streaming approach for large templates
            return self._load_large_template(template_json)
        else:
            # Use standard loading for smaller templates
            return self._load_standard_template(template_json)

    def _load_standard_template(self, template_json: Path) -> Optional[Dict[str, Any]]:
        """Load a standard-sized template"""
        try:
            with open(template_json, "r", encoding="utf-8") as f:
                template_data = json.load(f)
            template_data["template_path"] = str(template_json.parent)
            return template_data
        except Exception:
            return None

    def _load_large_template(self, template_json: Path) -> Optional[Dict[str, Any]]:
        """Load a large template with streaming and chunked processing"""
        try:
            template_data = {"template_path": str(template_json.parent)}

            with open(template_json, "r", encoding="utf-8") as f:
                # Read file in chunks to avoid memory issues
                content = ""
                while True:
                    chunk = f.read(self._chunk_size)
                    if not chunk:
                        break
                    content += chunk

                    # Check if content is getting too large
                    if len(content) > self._max_template_size:
                        raise MemoryError("Template file too large to process")

                # Parse JSON from accumulated content
                parsed_data = json.loads(content)
                template_data.update(parsed_data)

            return template_data
        except (MemoryError, json.JSONDecodeError, Exception):
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

    def invalidate_template_cache(
        self, language: Optional[str] = None, framework: Optional[str] = None
    ) -> None:
        """Invalidate specific or all template caches"""
        if language is None:
            # Clear all caches
            self._templates_cache.clear()
            self._available_templates_cache = None
            return

        # Invalidate specific language/framework combinations
        keys_to_remove = []
        for key in self._templates_cache.cache.keys():
            if key.startswith(f"{language}_"):
                if framework is None or f"_{framework}_" in key:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            self._templates_cache.invalidate(key)

        # Also clear available templates cache to force refresh
        self._available_templates_cache = None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return {
            "template_cache_size": self._templates_cache.size(),
            "template_cache_capacity": self._templates_cache.capacity,
            "template_cache_ttl": self._templates_cache.ttl,
            "available_templates_cached": self._available_templates_cache is not None,
            "available_templates_ttl": self._available_templates_ttl,
        }

    def cleanup_expired_cache(self) -> Dict[str, int]:
        """Clean up expired cache entries and return stats"""
        template_expired = self._templates_cache.cleanup_expired()

        # Check available templates cache
        available_expired = 0
        if (
            self._available_templates_cache is not None
            and time.time() - self._available_templates_cache[1]
            > self._available_templates_ttl
        ):
            self._available_templates_cache = None
            available_expired = 1

        return {
            "template_cache_expired": template_expired,
            "available_templates_expired": available_expired,
        }
