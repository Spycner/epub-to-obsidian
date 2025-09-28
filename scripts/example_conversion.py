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
from epub_to_obsidian.models import Book
from epub_to_obsidian.converters import ObsidianConverter

def main():
    # Parse command-line arguments
    if len(sys.argv) != 3:
        print("Usage: uv run scripts/example_conversion.py <input.epub> <output_dir>")
        print("\nExample:")
        print("  uv run scripts/example_conversion.py book.epub ./obsidian_vault/books")
        sys.exit(1)

    epub_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not epub_path.exists():
        print(f"Error: EPUB file '{epub_path}' not found.")
        sys.exit(1)

    if not epub_path.suffix.lower() == '.epub':
        print(f"Warning: File '{epub_path}' doesn't have .epub extension")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    print(f"📚 Loading EPUB: {epub_path}")

    # Load the EPUB as a Book object
    book = Book.from_epub(epub_path)

    print(f"📖 Book loaded: {book.title} by {book.author}")
    print(f"   Chapters: {len(book.chapters)}")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Convert to Obsidian format
    converter = ObsidianConverter()

    print(f"✍️  Converting to Obsidian format...")

    # Convert each chapter
    for i, chapter in enumerate(book.chapters, 1):
        markdown_content = converter.convert_chapter(chapter)

        # Save to file
        chapter_file = output_dir / f"Chapter_{i:02d}.md"
        chapter_file.write_text(markdown_content, encoding='utf-8')

        print(f"   ✓ Chapter {i}: {chapter.title} -> {chapter_file.name}")

    # Create index/TOC file
    toc_content = f"# {book.title}\n\nBy {book.author}\n\n## Chapters\n\n"
    for i, chapter in enumerate(book.chapters, 1):
        toc_content += f"- [[Chapter_{i:02d}|{chapter.title}]]\n"

    toc_file = output_dir / "index.md"
    toc_file.write_text(toc_content, encoding='utf-8')

    print(f"\n✅ Conversion complete!")
    print(f"   Output directory: {output_dir.absolute()}")
    print(f"   Total files created: {len(book.chapters) + 1}")

if __name__ == "__main__":
    main()