"""Command-line interface for EPUB to Obsidian converter using Typer."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from .obsidian_writer import ObsidianWriter
from .epub_parser import EPUBParser

app = typer.Typer(
    name="epub-to-obsidian",
    help="Convert EPUB books to Obsidian-compatible markdown files",
    add_completion=False
)
console = Console()


@app.command()
def convert(
    epub_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the EPUB file to convert"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        file_okay=False,
        dir_okay=True,
        help="Output directory for the converted files (default: current directory)"
    ),
    no_images: bool = typer.Option(
        False,
        "--no-images",
        help="Skip extracting and including images"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed progress information"
    )
):
    """Convert an EPUB file to Obsidian markdown format."""
    # Validate EPUB file
    if not epub_path.suffix.lower() == '.epub':
        console.print("[red]Error: File must be an EPUB file (.epub extension)[/red]")
        raise typer.Exit(1)

    # Set default output directory if not provided
    if output_dir is None:
        output_dir = Path.cwd()

    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Start conversion
        task = progress.add_task("[cyan]Converting EPUB to Obsidian format...", total=None)

        try:
            # Parse EPUB to get metadata
            if verbose:
                console.print(f"[dim]Parsing EPUB: {epub_path}[/dim]")

            parser = EPUBParser(epub_path)
            metadata = parser.metadata

            # Show book information
            progress.update(task, description="[cyan]Processing book metadata...")

            if verbose:
                _display_book_info(metadata)

            # Create writer and convert
            progress.update(task, description="[cyan]Converting chapters to markdown...")
            writer = ObsidianWriter(output_dir)
            book_dir = writer.write_book(epub_path, include_images=not no_images)

            progress.update(task, description="[green]✓ Conversion complete!")

            # Success message
            console.print()
            console.print(f"[bold green]✓ Successfully converted![/bold green]")
            console.print(f"[dim]Book saved to:[/dim] [cyan]{book_dir}[/cyan]")

            # Count files created
            md_files = list(book_dir.glob("*.md"))
            console.print(f"[dim]Created {len(md_files)} markdown files[/dim]")

            if not no_images:
                image_dir = book_dir / "images"
                if image_dir.exists():
                    images = list(image_dir.glob("*"))
                    if images:
                        console.print(f"[dim]Extracted {len(images)} images[/dim]")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory containing EPUB files to convert"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for converted files (default: current directory)"
    ),
    no_images: bool = typer.Option(
        False,
        "--no-images",
        help="Skip extracting and including images"
    )
):
    """Convert multiple EPUB files from a directory."""
    # Find all EPUB files
    epub_files = list(input_dir.glob("*.epub"))

    if not epub_files:
        console.print(f"[yellow]No EPUB files found in {input_dir}[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Found {len(epub_files)} EPUB files to convert[/cyan]")

    # Set default output directory
    if output_dir is None:
        output_dir = Path.cwd()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert each file
    successful = 0
    failed = []

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Converting EPUBs...", total=len(epub_files))

        for epub_path in epub_files:
            try:
                progress.update(task, description=f"[cyan]Converting: {epub_path.name}")

                writer = ObsidianWriter(output_dir)
                writer.write_book(epub_path, include_images=not no_images)

                successful += 1
                progress.advance(task)

            except Exception as e:
                failed.append((epub_path.name, str(e)))
                progress.advance(task)
                continue

    # Show results
    console.print()
    console.print(f"[bold green]✓ Conversion complete![/bold green]")
    console.print(f"[green]Successfully converted: {successful}/{len(epub_files)}[/green]")

    if failed:
        console.print(f"[red]Failed conversions:[/red]")
        for filename, error in failed:
            console.print(f"  [dim]- {filename}: {error}[/dim]")


@app.command()
def info(
    epub_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the EPUB file"
    )
):
    """Display information about an EPUB file without converting it."""
    if not epub_path.suffix.lower() == '.epub':
        console.print("[red]Error: File must be an EPUB file (.epub extension)[/red]")
        raise typer.Exit(1)

    try:
        parser = EPUBParser(epub_path)
        metadata = parser.metadata
        chapters = parser.get_chapters()

        # Display detailed book information
        _display_book_info(metadata)

        # Display chapter information
        console.print()
        console.print(f"[bold]Chapters:[/bold] {len(chapters)}")

        if chapters:
            table = Table(title="Chapter List")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Title", style="white")
            table.add_column("Characters", style="dim", justify="right")

            for chapter in chapters[:10]:  # Show first 10 chapters
                table.add_row(
                    str(chapter['number']),
                    chapter['title'][:50] + ("..." if len(chapter['title']) > 50 else ""),
                    f"{len(chapter.get('content', ''))}"
                )

            if len(chapters) > 10:
                table.add_row("...", f"... and {len(chapters) - 10} more chapters", "...")

            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error reading EPUB:[/bold red] {str(e)}")
        raise typer.Exit(1)


def _display_book_info(metadata: dict):
    """Display book metadata in a formatted table."""
    table = Table(title="Book Information", show_header=False)
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")

    # Add metadata rows
    table.add_row("Title", metadata.get('title', 'Unknown'))
    table.add_row("Author(s)", ", ".join(metadata.get('authors', ['Unknown'])))

    if metadata.get('publisher'):
        table.add_row("Publisher", metadata['publisher'])

    if metadata.get('publication_date'):
        table.add_row("Publication Date", str(metadata['publication_date']))

    if metadata.get('isbn'):
        table.add_row("ISBN", metadata['isbn'])

    if metadata.get('language'):
        table.add_row("Language", metadata['language'])

    if metadata.get('tags'):
        table.add_row("Tags", ", ".join(metadata['tags'][:5]))

    console.print(table)


@app.callback()
def callback():
    """EPUB to Obsidian Converter - Transform your digital library into a knowledge vault."""
    pass


def main():
    """Entry point for the CLI."""
    app()