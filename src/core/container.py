from dependency_injector import containers, providers
from .config import settings
from .logger import get_logger
from .module_loader import ModuleLoader
from .ai_utils import AIUtils


class CoreContainer(containers.DeclarativeContainer):
    """Dependency injection container for core components"""

    # Configuration provider
    config = providers.Object(settings)

    # Logger provider
    logger = providers.Factory(get_logger)

    # Module loader provider
    module_loader = providers.Singleton(ModuleLoader)

    # AI utilities provider
    ai_utils = providers.Singleton(AIUtils)
