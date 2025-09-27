import importlib
import inspect
from typing import Dict, List, Type, Optional
from pathlib import Path
from .base_module import BaseModule, ModuleConfig
from .logger import get_logger


class ModuleLoader:
    """Plugin loader for CodeForge AI modules"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.loaded_modules: Dict[str, Type[BaseModule]] = {}
        self.module_instances: Dict[str, BaseModule] = {}

    def discover_modules(self, module_paths: List[str]) -> Dict[str, Type[BaseModule]]:
        """Discover and load modules from specified paths"""
        discovered = {}

        for module_path in module_paths:
            try:
                # Try importing the module.py file directly
                module_name = module_path + ".module"
                module = importlib.import_module(module_name)

                # Find classes that inherit from BaseModule
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseModule)
                        and obj != BaseModule
                    ):
                        discovered[module_path] = obj
                        self.logger.debug(
                            f"Discovered module: {name} from {module_path}"
                        )

            except ImportError as e:
                self.logger.warning(f"Failed to import module from {module_path}: {e}")
            except Exception as e:
                self.logger.error(f"Error discovering modules from {module_path}: {e}")

        self.logger.info(f"Discovered {len(discovered)} module classes")
        self.loaded_modules.update(discovered)
        return discovered

    def instantiate_module(
        self, module_class: Type[BaseModule], config: ModuleConfig
    ) -> Optional[BaseModule]:
        """Create an instance of a module"""
        try:
            instance = module_class(config)
            self.module_instances[config.name] = instance
            self.logger.debug(f"Instantiated module: {config.name}")
            return instance
        except Exception as e:
            self.logger.error(
                f"Failed to instantiate module {module_class.__name__}: {e}"
            )
            return None

    def get_module(self, name: str) -> Optional[BaseModule]:
        """Get an instantiated module by name"""
        return self.module_instances.get(name)

    def list_available_modules(self) -> List[str]:
        """List names of loaded module classes"""
        return list(self.loaded_modules.keys())

    def list_active_modules(self) -> List[str]:
        """List names of instantiated modules"""
        return list(self.module_instances.keys())
