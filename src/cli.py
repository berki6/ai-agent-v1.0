import asyncio
import click
import json
from typing import Optional
from rich.theme import Theme
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

from src.core.engine import CodeForgeEngine
from src.core.logger import get_logger

# Custom theme for consistent colors
custom_theme = Theme(
    {
        "bar.complete": "bright_yellow",
        "bar.finished": "bright_green",
    }
)

# Initialize Rich console with custom theme
console = Console(theme=custom_theme, force_terminal=True, color_system="standard")

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

    # Define the expected modules
    expected_modules = [
        ("scaffolder", "src.services.scaffolder"),
        ("sentinel", "src.services.sentinel"),
        ("alchemist", "src.services.alchemist"),
        ("architect", "src.services.architect"),
    ]

    # Show step-by-step initialization process
    import time

    console.print("[cyan]🚀 Starting CodeForge AI initialization...[/cyan]")
    console.print()

    # Show engine initialization progress first
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bright_green", finished_style="bright_green"),
        TimeElapsedColumn(),
    ) as progress:
        init_task = progress.add_task(
            "[green]✓ Initialized CodeForge AI engine", total=1
        )
        progress.update(init_task, completed=True)

    console.print()  # Add spacing before logging

    # Now perform the initialization (logging will appear here)
    async def _init():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        return engine, success

    engine, success = asyncio.run(_init())

    # Now show the module loading progress
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bright_green", finished_style="bright_green"),
        TimeElapsedColumn(),
    ) as progress:

        if success:
            # Step 2: Show each module loading
            modules = engine.list_modules()

            for module_name, module_path in expected_modules:
                module_task = progress.add_task(
                    f"[green]✓ Loaded module: {module_name}", total=1
                )
                progress.update(module_task, completed=True)

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

    # Define the expected modules
    expected_modules = [
        ("scaffolder", "src.services.scaffolder"),
        ("sentinel", "src.services.sentinel"),
        ("alchemist", "src.services.alchemist"),
        ("architect", "src.services.architect"),
    ]

    # Show step-by-step discovery process
    import time

    console.print("[cyan]🔍 Starting module discovery process...[/cyan]")
    console.print()

    # Show engine initialization progress first
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bright_green", finished_style="bright_green"),
        TimeElapsedColumn(),
    ) as progress:
        init_task = progress.add_task(
            "[green]✓ Initialized CodeForge AI engine", total=1
        )
        progress.update(init_task, completed=True)

    console.print()  # Add spacing before logging

    # Now perform the discovery (logging will appear here)
    async def _list():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        return engine, success

    engine, success = asyncio.run(_list())

    # Now show the module discovery progress
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="bright_green", finished_style="bright_green"),
        TimeElapsedColumn(),
    ) as progress:

        if success:
            # Step 2: Show each module discovery
            modules = engine.list_modules()
            discovered_names = {module["name"] for module in modules}

            for module_name, module_path in expected_modules:
                if module_name in discovered_names:
                    module_task = progress.add_task(
                        f"[green]✓ Discovered module: {module_name}", total=1
                    )
                    progress.update(module_task, completed=True)
                else:
                    module_task = progress.add_task(
                        f"[yellow]⚠ Module not found: {module_name}", total=1
                    )
                    progress.update(module_task, completed=True)

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
@click.option("--json", "-j", "json_input", help="Input data as JSON file path")
@click.option("--interactive", "-I", is_flag=True, help="Run in interactive mode")
@click.pass_context
def run(ctx, module_name, input, json_input, interactive):
    """Run a specific module"""
    console = ctx.obj["console"]
    logger = ctx.obj["logger"]

    # Handle different input methods
    input_data = {}

    if json_input:
        # Load from JSON file
        try:
            with open(json_input, "r") as f:
                input_data = json.load(f)
        except Exception as e:
            console.print(f"[red]Error loading JSON file: {e}[/red]")
            return 1
    elif input:
        # Try to parse as JSON
        try:
            input_data = json.loads(input)
        except json.JSONDecodeError:
            # If not JSON, treat as simple string input
            input_data = {"input": input}
    elif interactive:
        # Interactive mode - collect required fields
        input_data = _collect_interactive_input(console, module_name)
    else:
        console.print(
            "[yellow]No input provided. Use --input, --json, or --interactive[/yellow]"
        )
        return 1

    console.print(f"[cyan]🎯 Running module: {module_name}[/cyan]")
    console.print()

    # Show engine initialization progress first
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="color(11)", finished_style="color(2)"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        init_task = progress.add_task("[cyan]Initializing engine...", total=1)
        progress.update(init_task, completed=True)

    console.print()  # Add spacing before logging

    # Now perform the initialization (logging will appear here)
    async def _init():
        engine = CodeForgeEngine()
        success = await engine.initialize()
        return engine, success

    engine, success = asyncio.run(_init())

    console.print()  # Add spacing before execution

    if not success:
        error_panel = Panel.fit(
            "[red]❌ Failed to initialize engine[/red]\n\n"
            "Cannot run modules without proper initialization.",
            title="[bold red]Engine Error[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        return 1

    # Now show execution progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="color(11)", finished_style="color(2)"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        exec_task = progress.add_task(
            f"[green]Executing module '{module_name}'...", total=1
        )

        async def _exec():
            result = await engine.execute_module(module_name, input_data)
            progress.update(exec_task, completed=True)
            return result

        result = asyncio.run(_exec())

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


def _collect_interactive_input(console, module_name):
    """Collect input data interactively based on module type"""
    input_data = {}

    if module_name == "scaffolder":
        console.print("[bold cyan]🏗️  AI Project Scaffolder Configuration[/bold cyan]")
        console.print()

        # Collect required fields
        input_data["project_name"] = Prompt.ask("[green]Project name[/green]")
        input_data["project_type"] = Prompt.ask(
            "[green]Project type[/green]",
            choices=["web", "api", "cli", "library", "desktop"],
        )
        input_data["language"] = Prompt.ask(
            "[green]Programming language[/green]",
            choices=["python", "javascript", "typescript", "java", "go", "rust"],
        )

        # Optional fields
        framework = Prompt.ask("[yellow]Framework (optional)[/yellow]", default="")
        if framework:
            input_data["framework"] = framework

        features_input = Prompt.ask(
            "[yellow]Features (comma-separated, optional)[/yellow]", default=""
        )
        if features_input:
            input_data["features"] = [f.strip() for f in features_input.split(",")]

        input_data["output_directory"] = Prompt.ask(
            "[yellow]Output directory[/yellow]", default="."
        )
        input_data["initialize_git"] = Confirm.ask(
            "[yellow]Initialize Git repository?[/yellow]", default=True
        )
    elif module_name == "sentinel":
        console.print("[bold cyan]🛡️  Vulnerability Sentinel Configuration[/bold cyan]")
        console.print()

        # Collect required fields
        input_data["scan_path"] = Prompt.ask("[green]Path to scan[/green]")

        # Optional fields
        input_data["scan_depth"] = int(
            Prompt.ask("[yellow]Scan depth (levels)[/yellow]", default="3")
        )
        input_data["severity_threshold"] = Prompt.ask(
            "[yellow]Severity threshold[/yellow]",
            choices=["low", "medium", "high", "critical"],
            default="medium",
        )
        input_data["enable_ai_analysis"] = Confirm.ask(
            "[yellow]Enable AI analysis?[/yellow]", default=True
        )

        include_patterns = Prompt.ask(
            "[yellow]Include patterns (comma-separated)[/yellow]",
            default="*.py,*.js,*.ts,*.java,*.go,*.rs",
        )
        input_data["include_patterns"] = [
            p.strip() for p in include_patterns.split(",")
        ]

        exclude_patterns = Prompt.ask(
            "[yellow]Exclude patterns (comma-separated)[/yellow]",
            default="__pycache__,node_modules,.git,venv,.env",
        )
        input_data["exclude_patterns"] = [
            p.strip() for p in exclude_patterns.split(",")
        ]

    elif module_name == "alchemist":
        console.print("[bold cyan]📚 Documentation Alchemist Configuration[/bold cyan]")
        console.print()

        # Collect required fields
        input_data["source_path"] = Prompt.ask("[green]Source code path[/green]")

        # Optional fields
        input_data["output_path"] = Prompt.ask(
            "[yellow]Output documentation path[/yellow]", default="docs"
        )
        input_data["doc_format"] = Prompt.ask(
            "[yellow]Documentation format[/yellow]",
            choices=["markdown", "html", "rst"],
            default="markdown",
        )
        input_data["include_private"] = Confirm.ask(
            "[yellow]Include private members (starting with _)?[/yellow]", default=False
        )
        input_data["generate_api_docs"] = Confirm.ask(
            "[yellow]Generate API documentation?[/yellow]", default=True
        )
        input_data["generate_readme"] = Confirm.ask(
            "[yellow]Generate README file?[/yellow]", default=True
        )
        input_data["generate_examples"] = Confirm.ask(
            "[yellow]Generate usage examples?[/yellow]", default=False
        )

    elif module_name == "architect":
        console.print("[bold cyan]🏗️  Code Architect Configuration[/bold cyan]")
        console.print()

        # Collect required fields
        input_data["source_path"] = Prompt.ask("[green]Source code path[/green]")

        # Optional fields
        input_data["analysis_type"] = Prompt.ask(
            "[yellow]Analysis type[/yellow]",
            choices=["comprehensive", "refactoring", "performance", "architecture"],
            default="comprehensive",
        )

        focus_options = ["performance", "maintainability", "security", "architecture"]
        focus_input = Prompt.ask(
            "[yellow]Focus areas (comma-separated)[/yellow]",
            default="performance,maintainability,security,architecture",
        )
        input_data["focus_areas"] = [f.strip() for f in focus_input.split(",")]

        input_data["max_files"] = int(
            Prompt.ask("[yellow]Maximum files to analyze[/yellow]", default="10")
        )

        include_patterns = Prompt.ask(
            "[yellow]Include patterns (comma-separated)[/yellow]",
            default="*.py,*.js,*.ts,*.java,*.go,*.rs",
        )
        input_data["include_patterns"] = [
            p.strip() for p in include_patterns.split(",")
        ]

        exclude_patterns = Prompt.ask(
            "[yellow]Exclude patterns (comma-separated)[/yellow]",
            default="__pycache__,node_modules,.git,venv,.env",
        )
        input_data["exclude_patterns"] = [
            p.strip() for p in exclude_patterns.split(",")
        ]

    else:
        # Generic input collection
        console.print(f"[bold cyan]🎯 Running module: {module_name}[/bold cyan]")
        input_text = Prompt.ask("[green]Enter input data[/green]")
        input_data = {"input": input_text}

    return input_data


if __name__ == "__main__":
    cli()
