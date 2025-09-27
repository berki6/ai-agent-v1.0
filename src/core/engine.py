from typing import Dict, List, Any, Optional
from .container import CoreContainer
from .base_module import BaseModule, ModuleConfig, ModuleResult
from .logger import get_logger


class CodeForgeEngine:
    """Core engine for CodeForge AI"""

    def __init__(self):
        self.container = CoreContainer()
        self.logger = self.container.logger()
        self.module_loader = self.container.module_loader()
        self.ai_utils = self.container.ai_utils()
        self.modules: Dict[str, BaseModule] = {}

    async def initialize(self) -> bool:
        """Initialize the engine and all modules"""
        try:
            self.logger.info("Initializing CodeForge AI Engine")

            # Discover modules from predefined paths
            module_paths = [
                "src.services.scaffolder",
                "src.services.sentinel",
                "src.services.alchemist",
                "src.services.architect",
            ]

            discovered = self.module_loader.discover_modules(module_paths)
            self.logger.info(f"Discovered {len(discovered)} module classes")

            # For now, create placeholder configs (will be loaded from config later)
            for name, module_class in discovered.items():
                config = ModuleConfig(name=name, enabled=True, priority=0)
                instance = self.module_loader.instantiate_module(module_class, config)
                if instance:
                    success = await instance.initialize()
                    if success:
                        self.modules[name] = instance
                        self.logger.info(f"Initialized module: {name}")
                    else:
                        self.logger.warning(f"Failed to initialize module: {name}")

            self.logger.info(
                f"Engine initialized with {len(self.modules)} active modules"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize engine: {e}")
            return False

    async def execute_module(
        self, module_name: str, input_data: Dict[str, Any]
    ) -> ModuleResult:
        """Execute a specific module"""
        module = self.modules.get(module_name)
        if not module:
            return ModuleResult(
                success=False,
                error=f"Module '{module_name}' not found or not initialized",
            )

        if not module.validate_input(input_data):
            return ModuleResult(
                success=False, error=f"Invalid input for module '{module_name}'"
            )

        try:
            result = await module.execute(input_data)
            return result
        except Exception as e:
            self.logger.error(f"Error executing module {module_name}: {e}")
            return ModuleResult(success=False, error=f"Execution failed: {str(e)}")

    def list_modules(self) -> List[Dict[str, Any]]:
        """List all available modules with their info"""
        return [module.get_info() for module in self.modules.values()]

    def get_module_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific module"""
        module = self.modules.get(name)
        return module.get_info() if module else None

    async def shutdown(self) -> bool:
        """Shutdown the engine and cleanup modules"""
        try:
            self.logger.info("Shutting down CodeForge AI Engine")

            for name, module in self.modules.items():
                try:
                    await module.cleanup()
                    self.logger.info(f"Cleaned up module: {name}")
                except Exception as e:
                    self.logger.warning(f"Error cleaning up module {name}: {e}")

            self.logger.info("Engine shutdown complete")
            return True

        except Exception as e:
            self.logger.error(f"Error during engine shutdown: {e}")
            return False
