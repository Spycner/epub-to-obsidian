#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "epub-to-obsidian @ git+https://github.com/Spycner/epub-to-obsidian",
# ]
# ///

"""
Example script demonstrating epub-to-obsidian usage.
Convert an EPUB file to Obsidian-compatible markdown notes.
"""

import sys
from pathlib import Path
from epub_to_obsidian.obsidian_writer import ObsidianWriter
from epub_to_obsidian.epub_parser import EPUBParser
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def main():
    # Parse command-line arguments
    if len(sys.argv) != 3:
        console.print("[red]Error:[/red] Invalid number of arguments")
        console.print("Usage: uv run scripts/example_conversion.py <input.epub> <output_dir>")
        console.print("\nExample:")
        console.print("  uv run scripts/example_conversion.py book.epub ./obsidian_vault/books")
        sys.exit(1)

    epub_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    # Validate input
    if not epub_path.exists():
        console.print(f"[red]Error:[/red] EPUB file '{epub_path}' not found.")
        sys.exit(1)

    if not epub_path.suffix.lower() == '.epub':
        console.print("[red]Error: File must be an EPUB file (.epub extension)[/red]")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold blue]📚 Converting EPUB to Obsidian format[/bold blue]")
    console.print(f"[dim]Input:[/dim] {epub_path}")
    console.print(f"[dim]Output:[/dim] {output_dir}\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Converting EPUB to Obsidian format...", total=None)

        try:
            # Parse EPUB to get metadata for display
            progress.update(task, description="[cyan]Processing book metadata...")
            parser = EPUBParser(epub_path)
            metadata = parser.metadata

            # Display book info
            console.print(f"[bold]Book:[/bold] {metadata.get('title', 'Unknown')}")
            console.print(f"[bold]Author:[/bold] {metadata.get('authors', 'Unknown')}\n")

            # Convert using ObsidianWriter
            progress.update(task, description="[cyan]Converting chapters to markdown...")
            writer = ObsidianWriter(output_dir)
            book_dir = writer.write_book(epub_path, include_images=True)

            progress.update(task, description="[green]✓ Conversion complete!")

        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)

    # Success message
    console.print()
    console.print(f"[bold green]✓ Successfully converted![/bold green]")
    console.print(f"[dim]Book saved to:[/dim] [cyan]{book_dir}[/cyan]")

    # Count files created
    md_files = list(book_dir.glob("*.md"))
    console.print(f"[dim]Created {len(md_files)} markdown files[/dim]")

    image_dir = book_dir / "images"
    if image_dir.exists():
        images = list(image_dir.glob("*"))
        if images:
            console.print(f"[dim]Extracted {len(images)} images[/dim]")

if __name__ == "__main__":
    main()