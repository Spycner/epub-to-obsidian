"""Module for writing converted content to Obsidian-compatible file structure."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from .epub_parser import EPUBParser
from .markdown_converter import MarkdownConverter


class ObsidianWriter:
    """Writer for creating Obsidian vault structure from EPUB content."""

    def __init__(self, output_dir: Path):
        """Initialize writer with output directory."""
        self.output_dir = Path(output_dir)
        self.converter = MarkdownConverter()

    def write_book(self, epub_path: Path, include_images: bool = True) -> Path:
        """Convert and write entire book to Obsidian structure.

        Args:
            epub_path: Path to the EPUB file
            include_images: Whether to extract and include images

        Returns:
            Path to the created book directory
        """
        # Parse the EPUB
        parser = EPUBParser(epub_path)

        # Get book metadata and chapters
        metadata = parser.metadata
        chapters = parser.get_chapters()
        toc = parser.get_toc()

        # Create book directory
        book_dir = self._create_book_directory(metadata['title'])

        # Write images if requested
        if include_images:
            self._write_images(parser, book_dir)

        # Write index page
        index_content = self.converter.create_index_page(metadata, chapters, toc)
        self._write_file(book_dir / f"{metadata['title']} - Index.md", index_content)

        # Write info page
        info_content = self.converter.create_info_page(metadata)
        self._write_file(book_dir / f"{metadata['title']} - Info.md", info_content)

        # Write chapters
        total_chapters = len(chapters)
        for idx, chapter in enumerate(chapters):
            # Update navigation for last chapter
            if idx == total_chapters - 1:
                chapter['is_last'] = True

            # Convert chapter to markdown
            markdown_content = self.converter.convert_chapter(chapter, metadata['title'])

            # Fix navigation for edge cases
            markdown_content = self._fix_navigation(markdown_content, idx, total_chapters, chapters)

            # Create chapter filename
            chapter_filename = self._create_chapter_filename(chapter)
            chapter_path = book_dir / chapter_filename

            # Write chapter file
            self._write_file(chapter_path, markdown_content)

        return book_dir

    def _create_book_directory(self, book_title: str) -> Path:
        """Create the book directory with sanitized name."""
        # Sanitize book title for directory name
        safe_title = self._sanitize_filename(book_title)
        book_dir = self.output_dir / f"{safe_title}_obsidian"

        # Create directory if it doesn't exist
        book_dir.mkdir(parents=True, exist_ok=True)

        return book_dir

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

    def _create_chapter_filename(self, chapter: Dict[str, Any]) -> str:
        """Create a properly formatted chapter filename."""
        chapter_num = chapter.get('number', 0)
        chapter_title = chapter.get('title', f'Chapter {chapter_num}')

        # Sanitize chapter title
        safe_title = self._sanitize_filename(chapter_title)

        # Format as "01 - Chapter Title.md"
        filename = f"{chapter_num:02d} - {safe_title}.md"

        return filename

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def _write_images(self, parser: EPUBParser, book_dir: Path) -> None:
        """Extract and write images to the book directory."""
        images = parser.get_images()

        if not images:
            return

        # Create images directory
        images_dir = book_dir / "images"
        images_dir.mkdir(exist_ok=True)

        for image_name, image_content in images:
            # Sanitize image filename
            image_path = Path(image_name)
            safe_name = self._sanitize_filename(image_path.name)

            # Write image file
            image_file = images_dir / safe_name
            image_file.write_bytes(image_content)

        # Also save cover image separately if available
        cover = parser.get_cover_image()
        if cover:
            cover_name, cover_content = cover
            cover_path = book_dir / "cover.jpg"
            cover_path.write_bytes(cover_content)

    def _fix_navigation(self, content: str, chapter_idx: int, total_chapters: int,
                        chapters: List[Dict[str, Any]]) -> str:
        """Fix navigation links based on chapter position."""
        metadata = chapters[0].get('book_metadata', {}) if chapters else {}
        book_title = metadata.get('title', 'Book')

        def create_navigation(idx: int) -> str:
            """Create proper navigation based on chapter index."""
            nav_parts = []

            # Previous chapter
            if idx > 0:
                prev_chapter = chapters[idx - 1]
                prev_filename = self._create_chapter_filename(prev_chapter)
                prev_title = prev_chapter.get('title', 'Previous')
                nav_parts.append(f"⬅️ [[{prev_filename[:-3]}|Previous: {prev_title}]]")

            # Index
            nav_parts.append(f"📚 [[{book_title} - Index|Index]]")

            # Next chapter
            if idx < total_chapters - 1:
                next_chapter = chapters[idx + 1]
                next_filename = self._create_chapter_filename(next_chapter)
                next_title = next_chapter.get('title', 'Next')
                nav_parts.append(f"[[{next_filename[:-3]}|Next: {next_title}]] ➡️")

            return " | ".join(nav_parts)

        # Create new navigation
        new_nav = create_navigation(chapter_idx)

        # Find the last occurrence of --- followed by navigation
        # Split content by lines to find the navigation section
        lines = content.split('\n')

        # Find the last --- separator (should be before navigation)
        last_separator_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '---':
                last_separator_idx = i
                break

        if last_separator_idx >= 0:
            # Replace everything after the last --- with new navigation
            lines = lines[:last_separator_idx + 1] + ['', new_nav]
            content = '\n'.join(lines)

        return content