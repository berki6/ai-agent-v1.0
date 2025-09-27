import asyncio
import click
from typing import Optional
from core.engine import CodeForgeEngine
from core.logger import get_logger


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """CodeForge AI - Unified Modular AI Agent for Software Development"""
    # Set up context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Initialize logger
    logger = get_logger(__name__)
    if verbose:
        logger.setLevel("DEBUG")

    ctx.obj["logger"] = logger


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the CodeForge AI engine"""
    logger = ctx.obj["logger"]
    logger.info("Initializing CodeForge AI...")

    async def _init():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        if success:
            modules = engine.list_modules()
            click.echo(
                f"✅ Engine initialized successfully with {len(modules)} modules"
            )
            for module in modules:
                click.echo(f"  - {module['name']}: {module['description']}")
        else:
            click.echo("❌ Failed to initialize engine")
            return 1
        return 0

    return asyncio.run(_init())


@cli.command()
@click.pass_context
def list_modules(ctx):
    """List all available modules"""
    logger = ctx.obj["logger"]

    async def _list():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        if not success:
            click.echo("❌ Failed to initialize engine")
            return 1

        modules = engine.list_modules()
        if not modules:
            click.echo("No modules available")
            return 0

        click.echo("Available modules:")
        for module in modules:
            status = "✅" if module["enabled"] else "❌"
            click.echo(f"  {status} {module['name']} (priority: {module['priority']})")
            click.echo(f"      {module['description']}")
        return 0

    return asyncio.run(_list())


@cli.command()
@click.argument("module_name")
@click.option("--input", "-i", help="Input data as JSON string")
@click.pass_context
def run(ctx, module_name, input):
    """Run a specific module"""
    logger = ctx.obj["logger"]

    async def _run():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        if not success:
            click.echo("❌ Failed to initialize engine")
            return 1

        # Parse input (for now, simple string)
        input_data = {"input": input or "default"}

        result = await engine.execute_module(module_name, input_data)
        if result.success:
            click.echo(f"✅ Module '{module_name}' executed successfully")
            if result.data:
                click.echo("Result data:")
                click.echo(result.data)
        else:
            click.echo(f"❌ Module '{module_name}' failed: {result.error}")
            return 1
        return 0

    return asyncio.run(_run())


if __name__ == "__main__":
    cli()
