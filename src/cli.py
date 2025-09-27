import asyncio
import click
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, Prompt
from rich import print as rich_print
from rich.align import Align
from rich.layout import Layout

from core.engine import CodeForgeEngine
from core.logger import get_logger

# Initialize Rich console
console = Console()

# ASCII Art Banner
BANNER = """
 ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
██║     ██║   ██║██║  ██║█████╗  █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
██║     ██║   ██║██║  ██║██╔══╝  ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
╚██████╗╚██████╔╝██████╔╝███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝

                    Unified Modular AI Agent for Software Development
"""


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """CodeForge AI - Unified Modular AI Agent for Software Development"""
    # Display banner
    banner_text = Text(BANNER.strip(), style="bold cyan")
    console.print(Align.center(banner_text))
    console.print()

    # Set up context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Initialize logger
    logger = get_logger(__name__)
    if verbose:
        logger.setLevel("DEBUG")

    ctx.obj["logger"] = logger
    ctx.obj["console"] = console


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the CodeForge AI engine"""
    console = ctx.obj["console"]
    logger = ctx.obj["logger"]

    with console.status(
        "[bold green]Initializing CodeForge AI engine...", spinner="dots"
    ):
        logger.info("Initializing CodeForge AI...")

        async def _init():
            engine = CodeForgeEngine()
            success = await engine.initialize()
            return engine, success

        engine, success = asyncio.run(_init())

    if success:
        modules = engine.list_modules()

        # Create a beautiful success panel
        success_panel = Panel.fit(
            f"[green]✅ Engine initialized successfully![/green]\n\n"
            f"[blue]📦 Loaded Modules:[/blue] {len(modules)}\n"
            + "\n".join(
                [
                    f"  • [cyan]{module['name']}[/cyan]: {module['description']}"
                    for module in modules
                ]
            ),
            title="[bold green]Initialization Complete[/bold green]",
            border_style="green",
        )
        console.print(success_panel)
        return 0
    else:
        error_panel = Panel.fit(
            "[red]❌ Failed to initialize engine[/red]\n\n"
            "Please check your configuration and try again.",
            title="[bold red]Initialization Failed[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        return 1


@cli.command()
@click.pass_context
def list_modules(ctx):
    """List all available modules"""
    console = ctx.obj["console"]
    logger = ctx.obj["logger"]

    with console.status("[bold blue]Discovering available modules...", spinner="dots"):

        async def _list():
            engine = CodeForgeEngine()
            success = await engine.initialize()
            return engine, success

        engine, success = asyncio.run(_list())

    if not success:
        error_panel = Panel.fit(
            "[red]❌ Failed to initialize engine[/red]\n\n"
            "Cannot list modules without proper initialization.",
            title="[bold red]Engine Error[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        return 1

    modules = engine.list_modules()

    if not modules:
        empty_panel = Panel.fit(
            "[yellow]📭 No modules available[/yellow]\n\n"
            "Phase 2 modules (Scaffolder, Sentinel, Alchemist, Architect) are not yet implemented.\n"
            "Use [cyan]codeforge init[/cyan] to see the current status.",
            title="[bold yellow]Module Status[/bold yellow]",
            border_style="yellow",
        )
        console.print(empty_panel)
        return 0

    # Create a beautiful table for modules
    table = Table(
        title="[bold blue]🔧 Available Modules[/bold blue]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Status", style="bold", width=8)
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Priority", style="yellow", width=8, justify="center")
    table.add_column("Description", style="white")

    for module in modules:
        status = (
            "[green]✅ Active[/green]"
            if module["enabled"]
            else "[red]❌ Disabled[/red]"
        )
        table.add_row(
            status, module["name"], str(module["priority"]), module["description"]
        )

    console.print(table)

    # Summary panel
    summary_panel = Panel.fit(
        f"[blue]📊 Total Modules:[/blue] {len(modules)}\n"
        f"[green]✅ Active:[/green] {sum(1 for m in modules if m['enabled'])}\n"
        f"[red]❌ Disabled:[/red] {sum(1 for m in modules if not m['enabled'])}",
        title="[bold]Module Summary[/bold]",
        border_style="blue",
    )
    console.print(summary_panel)
    return 0


@cli.command()
@click.argument("module_name")
@click.option("--input", "-i", help="Input data as JSON string")
@click.option("--interactive", "-I", is_flag=True, help="Run in interactive mode")
@click.pass_context
def run(ctx, module_name, input, interactive):
    """Run a specific module"""
    console = ctx.obj["console"]
    logger = ctx.obj["logger"]

    # Interactive mode
    if interactive:
        console.print("[bold cyan]🎯 Interactive Mode[/bold cyan]")
        if not input:
            input = Prompt.ask("[yellow]Enter input data[/yellow]")
        if not Confirm.ask(
            f"[green]Run module '{module_name}' with input: '{input}'?[/green]"
        ):
            console.print("[yellow]Operation cancelled.[/yellow]")
            return 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        init_task = progress.add_task("[cyan]Initializing engine...", total=None)
        logger.info(f"Running module: {module_name}")

        async def _run():
            engine = CodeForgeEngine()
            success = await engine.initialize()
            progress.update(init_task, completed=True)

            if not success:
                return None, False

            run_task = progress.add_task(
                f"[green]Executing module '{module_name}'...", total=None
            )

            # Parse input (for now, simple string)
            input_data = {"input": input or "default"}

            result = await engine.execute_module(module_name, input_data)
            progress.update(run_task, completed=True)

            return result, True

        result, success = asyncio.run(_run())

    if not success:
        error_panel = Panel.fit(
            "[red]❌ Failed to initialize engine[/red]\n\n"
            "Cannot run modules without proper initialization.",
            title="[bold red]Engine Error[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        return 1

    if result is not None and getattr(result, "success", False):
        success_panel = Panel.fit(
            f"[green]✅ Module '{module_name}' executed successfully![/green]\n\n"
            f"[blue]📄 Result:[/blue]\n{result.data if getattr(result, 'data', None) else 'No output data'}",
            title="[bold green]Execution Complete[/bold green]",
            border_style="green",
        )
        console.print(success_panel)
        return 0
    else:
        error_panel = Panel.fit(
            f"[red]❌ Module '{module_name}' failed[/red]\n\n"
            f"[yellow]Error:[/yellow] {getattr(result, 'error', 'Unknown error')}",
            title="[bold red]Execution Failed[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        return 1


if __name__ == "__main__":
    cli()
