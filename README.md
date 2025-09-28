# EPUB to Obsidian Converter

Convert EPUB books into Obsidian-compatible markdown files with proper structure, navigation, and metadata.

## Features

- **Full Content Extraction**: Preserves all chapter content, images, and metadata
- **Obsidian-Ready**: Creates wikilinks, navigation, and proper markdown formatting
- **Beautiful CLI**: Rich terminal output with progress indicators
- **Fast Conversion**: Efficient processing using MarkItDown for HTML to Markdown
- **Organized Output**: Creates structured vault with Index, Info, and Chapter files
- **Image Support**: Extracts and organizes book images
- **AI-Ready**: Perfect for use with Claude in Obsidian - ask questions about your books!

## Installation

```bash
# Clone the repository
git clone https://github.com/Spycner/epub-to-obsidian.git
cd epub-to-obsidian

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Usage

### Quick Start

```bash
# Convert an EPUB file using the example script
uv run scripts/example_conversion.py book.epub ./output/

# Or use the full CLI after installation
epub-to-obsidian convert book.epub --output ./output/
```

The example script at `scripts/example_conversion.py` provides a simple standalone converter that requires no installation and can be run directly with `uv`.


### Convert a single EPUB

```bash
epub-to-obsidian convert path/to/book.epub --output output_dir/
```

### Convert multiple EPUBs

```bash
epub-to-obsidian batch path/to/epub_directory/ --output output_dir/
```

### View EPUB information

```bash
epub-to-obsidian info path/to/book.epub
```

## Output Structure

```
Book_Name_obsidian/
 Book Name - Index.md          # Main navigation with table of contents
 Book Name - Info.md           # Book metadata and information
 01 - Chapter Title.md         # Individual chapter files
 02 - Another Chapter.md
 images/                       # Extracted images (optional)
  cover.jpg
  ...
 ...
```

## Features in Detail

### Navigation
- Each chapter includes navigation links to previous/next chapters and index
- Index page contains clickable table of contents
- All internal references use Obsidian wikilink format `[[Chapter Name]]`

### Metadata
- YAML frontmatter in each file with title, type, and tags
- Book information page with author, publisher, ISBN, etc.
- Automatic tag generation for easy organization

### CLI Options

- `--output, -o`: Specify output directory
- `--no-images`: Skip image extraction
- `--verbose, -v`: Show detailed progress information

## Requirements

- Python 3.13+
- Dependencies (automatically installed):
  - typer - CLI interface
  - rich - Terminal formatting
  - ebooklib - EPUB parsing
  - beautifulsoup4 - HTML processing
  - markitdown - HTML to Markdown conversion

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) for the CLI interface
- [MarkItDown](https://github.com/microsoft/markitdown) for HTML to Markdown conversion
- [EbookLib](https://github.com/aerkalov/ebooklib) for EPUB parsing
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output