import asyncio
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import concurrent.futures


class ParallelScaffolder:
    """Handles parallel file and directory operations for project scaffolding"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def create_project_structure(
        self,
        project_path: Path,
        project_structure: Dict[str, Any],
        chunk_size: int = 1024 * 1024,  # 1MB chunks for large files
    ) -> Dict[str, Any]:
        """Create project structure with parallel operations"""

        # Create directories first (sequential for dependency management)
        directories = project_structure.get("directories", [])
        await self._create_directories_parallel(project_path, directories)

        # Create files in parallel
        files = project_structure.get("files", {})
        await self._create_files_parallel(project_path, files, chunk_size)

        # Create scripts if any
        scripts = project_structure.get("scripts", {})
        await self._create_scripts(project_path, scripts)

        return {
            "created_directories": len(directories),
            "created_files": len(files),
            "created_scripts": len(scripts),
        }

    async def _create_directories_parallel(
        self, base_path: Path, directories: List[str]
    ) -> None:
        """Create directories in parallel batches"""
        if not directories:
            return

        # Group directories by depth for dependency management
        depth_groups = {}
        for directory in directories:
            depth = directory.count("/")
            if depth not in depth_groups:
                depth_groups[depth] = []
            depth_groups[depth].append(directory)

        # Create directories depth-first
        for depth in sorted(depth_groups.keys()):
            dirs_to_create = depth_groups[depth]
            tasks = [
                self._create_directory(base_path, dir_path)
                for dir_path in dirs_to_create
            ]
            await asyncio.gather(*tasks)

    async def _create_directory(self, base_path: Path, dir_path: str) -> None:
        """Create a single directory"""
        full_path = base_path / dir_path
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, full_path.mkdir, True, True)

    async def _create_files_parallel(
        self, base_path: Path, files: Dict[str, Dict[str, Any]], chunk_size: int
    ) -> None:
        """Create files in parallel with chunked writing for large files"""
        if not files:
            return

        # Separate large and small files
        large_files = {}
        small_files = {}

        for file_path, file_info in files.items():
            content = file_info.get("content", "")
            if len(content) > chunk_size:
                large_files[file_path] = file_info
            else:
                small_files[file_path] = file_info

        # Create small files in parallel
        if small_files:
            tasks = [
                self._create_file(base_path, file_path, file_info)
                for file_path, file_info in small_files.items()
            ]
            await asyncio.gather(*tasks)

        # Create large files sequentially with chunked writing
        for file_path, file_info in large_files.items():
            await self._create_large_file(base_path, file_path, file_info, chunk_size)

    async def _create_file(
        self, base_path: Path, file_path: str, file_info: Dict[str, Any]
    ) -> None:
        """Create a single file"""
        full_path = base_path / file_path
        content = file_info.get("content", "")

        # Ensure parent directory exists
        await self._ensure_parent_directory(full_path.parent)

        # Write file using thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, self._write_file_sync, full_path, content
        )

    def _write_file_sync(self, file_path: Path, content: str) -> None:
        """Synchronously write content to file"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    async def _create_large_file(
        self,
        base_path: Path,
        file_path: str,
        file_info: Dict[str, Any],
        chunk_size: int,
    ) -> None:
        """Create a large file with chunked writing"""
        full_path = base_path / file_path
        content = file_info.get("content", "")

        # Ensure parent directory exists
        await self._ensure_parent_directory(full_path.parent)

        # Write in chunks using thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, self._write_large_file_sync, full_path, content, chunk_size
        )

    def _write_large_file_sync(
        self, file_path: Path, content: str, chunk_size: int
    ) -> None:
        """Synchronously write large content to file in chunks"""
        with open(file_path, "w", encoding="utf-8") as f:
            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                f.write(chunk)

    async def _ensure_parent_directory(self, dir_path: Path) -> None:
        """Ensure parent directory exists"""
        if not dir_path.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, dir_path.mkdir, True, True)

    async def _create_scripts(self, base_path: Path, scripts: Dict[str, str]) -> None:
        """Create executable scripts"""
        if not scripts:
            return

        # Create scripts directory if it doesn't exist
        scripts_dir = base_path / "scripts"
        if not scripts_dir.exists():
            await self._create_directory(base_path, "scripts")

        # Create each script
        tasks = []
        for script_name, script_content in scripts.items():
            script_path = f"scripts/{script_name}"
            script_info = {"content": script_content, "executable": True}
            tasks.append(
                self._create_executable_file(base_path, script_path, script_info)
            )

        await asyncio.gather(*tasks)

    async def _create_executable_file(
        self, base_path: Path, file_path: str, file_info: Dict[str, Any]
    ) -> None:
        """Create an executable file"""
        full_path = base_path / file_path
        content = file_info.get("content", "")

        # Ensure parent directory exists
        await self._ensure_parent_directory(full_path.parent)

        # Write file and make executable
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, self._write_executable_file_sync, full_path, content
        )

    def _write_executable_file_sync(self, file_path: Path, content: str) -> None:
        """Synchronously write content to file and make it executable"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Make executable on Unix-like systems
        if os.name != "nt":  # Not Windows
            os.chmod(file_path, 0o755)

    async def merge_project_structures(
        self,
        base_structure: Dict[str, Any],
        additional_structures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge multiple project structures for incremental scaffolding"""
        merged = {
            "directories": set(base_structure.get("directories", [])),
            "files": dict(base_structure.get("files", {})),
            "scripts": dict(base_structure.get("scripts", {})),
        }

        for structure in additional_structures:
            # Merge directories
            merged["directories"].update(structure.get("directories", []))

            # Merge files (additional structures can override)
            merged["files"].update(structure.get("files", {}))

            # Merge scripts
            merged["scripts"].update(structure.get("scripts", {}))

        # Convert directories back to list
        merged["directories"] = list(merged["directories"])

        return merged

    async def apply_partial_template(
        self,
        project_path: Path,
        template: Dict[str, Any],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Apply only parts of a template based on include/exclude patterns"""
        filtered_structure = {
            "directories": [],
            "files": {},
            "scripts": {},
        }

        # Filter directories
        for directory in template.get("directories", []):
            if self._matches_patterns(directory, include_patterns, exclude_patterns):
                filtered_structure["directories"].append(directory)

        # Filter files
        for file_path, file_info in template.get("files", {}).items():
            if self._matches_patterns(file_path, include_patterns, exclude_patterns):
                filtered_structure["files"][file_path] = file_info

        # Filter scripts
        for script_name, script_content in template.get("scripts", {}).items():
            if self._matches_patterns(script_name, include_patterns, exclude_patterns):
                filtered_structure["scripts"][script_name] = script_content

        # Create the filtered structure
        creation_stats = await self.create_project_structure(
            project_path, filtered_structure
        )

        return {
            "applied_structure": filtered_structure,
            "creation_stats": creation_stats,
        }

    def _matches_patterns(
        self,
        path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> bool:
        """Check if a path matches include/exclude patterns"""
        import fnmatch

        # If no patterns specified, include everything
        if not include_patterns and not exclude_patterns:
            return True

        # Check exclude patterns first (exclusions take precedence)
        if exclude_patterns:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(path, pattern):
                    return False

        # Check include patterns
        if include_patterns:
            for pattern in include_patterns:
                if fnmatch.fnmatch(path, pattern):
                    return True
            return False  # If include patterns specified but none match, exclude

        return True  # If only exclude patterns and none matched, include

    async def scaffold_incrementally(
        self,
        project_path: Path,
        base_template: Dict[str, Any],
        feature_templates: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform incremental scaffolding by applying base template then features"""
        # Start with base template
        current_structure = dict(base_template)

        # Apply each feature template incrementally
        applied_features = []
        for feature_template in feature_templates:
            # Merge with current structure
            current_structure = await self.merge_project_structures(
                current_structure, [feature_template]
            )
            applied_features.append(feature_template.get("name", "unknown_feature"))

        # Apply configuration customizations
        if "project_name" in config:
            current_structure = self._apply_config_to_structure(
                current_structure, config
            )

        # Create the final structure
        creation_stats = await self.create_project_structure(
            project_path, current_structure
        )

        return {
            "final_structure": current_structure,
            "applied_features": applied_features,
            "creation_stats": creation_stats,
        }

    def _apply_config_to_structure(
        self, structure: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply configuration variables to template structure"""
        customized = json.loads(json.dumps(structure))  # Deep copy

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

        return customized

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "max_workers": self.max_workers,
            "executor_active_threads": (
                len(self.executor._threads) if hasattr(self.executor, "_threads") else 0
            ),
        }

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
