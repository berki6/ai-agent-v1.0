import pytest
from src.core.engine import CodeForgeEngine
from src.core.base_module import ModuleConfig


@pytest.mark.asyncio
async def test_engine_initialization():
    """Test that the engine can be initialized"""
    engine = CodeForgeEngine()

    # Should initialize even with no modules
    success = await engine.initialize()
    assert success is True

    # Should have no modules initially
    modules = engine.list_modules()
    assert isinstance(modules, list)
    assert len(modules) == 0  # No modules implemented yet

    # Cleanup
    await engine.shutdown()


@pytest.mark.asyncio
async def test_engine_module_execution_failure():
    """Test that executing non-existent module fails gracefully"""
    engine = CodeForgeEngine()
    await engine.initialize()

    result = await engine.execute_module("nonexistent", {"test": "data"})

    assert result.success is False
    assert result.error is not None and "not found" in result.error

    await engine.shutdown()


def test_engine_module_info():
    """Test getting module info for non-existent module"""
    engine = CodeForgeEngine()

    info = engine.get_module_info("nonexistent")
    assert info is None
