"""Markdown conversion module using MarkItDown for HTML to Markdown conversion."""

from pathlib import Path
from typing import Optional, Dict, Any
import re
from markitdown import MarkItDown
from bs4 import BeautifulSoup


class MarkdownConverter:
    """Converter for HTML content to Obsidian-compatible Markdown."""

    def __init__(self):
        """Initialize the MarkItDown converter."""
        self.converter = MarkItDown()

    def convert_chapter(self, chapter_data: Dict[str, Any], book_title: str) -> str:
        """Convert chapter HTML to Markdown with Obsidian features.

        Args:
            chapter_data: Dictionary containing chapter information
            book_title: Title of the book for internal links

        Returns:
            Markdown formatted chapter content
        """
        html_content = chapter_data.get('content_html', '')
        chapter_title = chapter_data.get('title', '')
        chapter_num = chapter_data.get('number', 0)

        # Convert HTML to Markdown using MarkItDown
        markdown_content = self._html_to_markdown(html_content)

        # Post-process the markdown
        markdown_content = self._post_process_markdown(markdown_content, book_title)

        # Add frontmatter
        frontmatter = self._create_frontmatter(chapter_data, book_title)

        # Add navigation links
        navigation = self._create_navigation(chapter_num, book_title)

        # Combine all parts
        final_content = f"{frontmatter}\n\n"

        # Add chapter title if not already in content
        if chapter_title and not self._title_in_content(markdown_content, chapter_title):
            final_content += f"# {chapter_title}\n\n"

        final_content += f"{markdown_content}\n\n---\n\n{navigation}"

        return final_content

    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to Markdown using MarkItDown."""
        try:
            # Write HTML to a temporary file since MarkItDown needs a file path
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name

            try:
                result = self.converter.convert(temp_path)
                markdown_text = result.text_content or ""

                # If MarkItDown returns empty content, fall back to basic converter
                if not markdown_text.strip():
                    print(f"MarkItDown returned empty content, using fallback converter")
                    return self._basic_html_to_markdown(html_content)

                return markdown_text
            finally:
                # Clean up temp file
                import os
                os.unlink(temp_path)
        except Exception as e:
            print(f"Error converting HTML to Markdown: {e}")
            # Fallback to basic conversion
            return self._basic_html_to_markdown(html_content)

    def _basic_html_to_markdown(self, html_content: str) -> str:
        """Basic HTML to Markdown conversion as fallback."""
        soup = BeautifulSoup(html_content, 'html.parser')

        def convert_element(element):
            """Recursively convert HTML elements to markdown."""
            if element.name is None:
                # Text node
                return str(element)

            # Get text content for simple conversions
            text = element.get_text()

            # Handle different tags
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                return f"\n{'#' * level} {text}\n"

            elif element.name == 'p':
                return f"\n{text}\n"

            elif element.name == 'strong' or element.name == 'b':
                return f"**{text}**"

            elif element.name == 'em' or element.name == 'i':
                return f"*{text}*"

            elif element.name == 'code':
                return f"`{text}`"

            elif element.name == 'pre':
                return f"\n```\n{text}\n```\n"

            elif element.name == 'a':
                href = element.get('href', '')
                if href:
                    return f"[{text}]({href})"
                return text

            elif element.name == 'ul':
                items = []
                for li in element.find_all('li', recursive=False):
                    items.append(f"- {li.get_text()}")
                return '\n' + '\n'.join(items) + '\n'

            elif element.name == 'ol':
                items = []
                for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                    items.append(f"{idx}. {li.get_text()}")
                return '\n' + '\n'.join(items) + '\n'

            elif element.name == 'blockquote':
                lines = text.split('\n')
                quoted = '\n'.join(f"> {line}" for line in lines if line.strip())
                return f"\n{quoted}\n"

            elif element.name == 'br':
                return '\n'

            elif element.name == 'hr':
                return '\n---\n'

            elif element.name in ['div', 'section', 'article', 'span']:
                # For container elements, process children
                result = []
                for child in element.children:
                    converted = convert_element(child)
                    if converted:
                        result.append(converted)
                return ''.join(result)

            elif element.name == 'body':
                # Process body children
                result = []
                for child in element.children:
                    converted = convert_element(child)
                    if converted:
                        result.append(converted)
                return ''.join(result)

            else:
                # For unhandled tags, just get the text
                return text

        # Start conversion from body or root
        body = soup.find('body')
        if body:
            markdown = convert_element(body)
        else:
            markdown = convert_element(soup)

        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = re.sub(r' +', ' ', markdown)

        return markdown.strip()

    def _post_process_markdown(self, content: str, book_title: str) -> str:
        """Post-process markdown for Obsidian compatibility."""
        # Remove excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        # Convert chapter references to Obsidian links
        # Pattern: Chapter 1, Chapter I, Chapter One, etc.
        chapter_pattern = r'Chapter\s+([IVX\d]+|[A-Z][a-z]+)'

        def replace_chapter_ref(match):
            chapter_ref = match.group(0)
            # Try to normalize the chapter reference
            return f"[[{chapter_ref}]]"

        content = re.sub(chapter_pattern, replace_chapter_ref, content, flags=re.IGNORECASE)

        # Handle footnotes - convert to Obsidian format
        # [^1] style footnotes
        content = re.sub(r'\[(\d+)\]', r'[^\\1]', content)

        # Clean up any HTML artifacts that might remain
        content = re.sub(r'<[^>]+>', '', content)

        # Ensure proper spacing around headers
        content = re.sub(r'(#{1,6}\s+[^\n]+)\n([^\n])', r'\\1\n\n\\2', content)

        # Fix list formatting
        content = re.sub(r'\n(-|\d+\.)\s+', r'\n\n\\1 ', content)

        return content.strip()

    def _create_frontmatter(self, chapter_data: Dict[str, Any], book_title: str) -> str:
        """Create YAML frontmatter for the chapter."""
        frontmatter = "---\n"
        frontmatter += f"title: \"{chapter_data.get('title', '')}\"\n"
        frontmatter += f"book: \"{book_title}\"\n"
        frontmatter += f"chapter: {chapter_data.get('number', 0)}\n"
        frontmatter += f"type: chapter\n"

        # Add tags
        frontmatter += "tags:\n"
        frontmatter += f"  - book/{self._sanitize_tag(book_title)}\n"
        frontmatter += f"  - chapter\n"

        frontmatter += "---"
        return frontmatter

    def _create_navigation(self, chapter_num: int, book_title: str) -> str:
        """Create navigation links for the chapter."""
        nav_parts = []

        # Previous chapter link
        if chapter_num > 1:
            nav_parts.append(f"⬅️ [[{self._format_chapter_filename(chapter_num - 1, 'Previous')}|Previous Chapter]]")

        # Index link
        nav_parts.append(f"📚 [[{book_title} - Index|Index]]")

        # Next chapter link (we'll update this in the writer when we know total chapters)
        nav_parts.append(f"[[{self._format_chapter_filename(chapter_num + 1, 'Next')}|Next Chapter]] ➡️")

        return " | ".join(nav_parts)

    def _format_chapter_filename(self, chapter_num: int, placeholder_title: str = "Chapter") -> str:
        """Format chapter filename."""
        return f"{chapter_num:02d} - {placeholder_title}"

    def _sanitize_tag(self, text: str) -> str:
        """Sanitize text for use as a tag."""
        # Remove special characters and replace spaces with hyphens
        sanitized = re.sub(r'[^\w\s-]', '', text)
        sanitized = re.sub(r'\s+', '-', sanitized)
        return sanitized.lower()

    def _title_in_content(self, content: str, title: str) -> bool:
        """Check if the title already appears as a heading in the content."""
        # Check for the title in first few lines
        lines = content.split('\n')[:5]
        title_lower = title.lower().strip()

        for line in lines:
            if line.startswith('#'):
                # Remove markdown heading syntax and compare
                heading_text = re.sub(r'^#+\s*', '', line).lower().strip()
                if heading_text == title_lower:
                    return True

        return False

    def create_index_page(self, book_metadata: Dict[str, Any], chapters: list, toc: list) -> str:
        """Create the index/navigation page for the book."""
        title = book_metadata.get('title', 'Unknown Book')
        authors = book_metadata.get('authors', ['Unknown Author'])

        content = "---\n"
        content += f"title: \"{title} - Index\"\n"
        content += f"type: index\n"
        content += "tags:\n"
        content += f"  - book/{self._sanitize_tag(title)}\n"
        content += f"  - index\n"
        content += "---\n\n"

        content += f"# {title}\n\n"
        content += f"**By {', '.join(authors)}**\n\n"

        content += "## 📖 Table of Contents\n\n"

        # If we have a structured TOC from the EPUB, use it
        if toc:
            for toc_item in toc:
                level = toc_item.get('level', 0)
                indent = "  " * level
                toc_title = toc_item.get('title', '')

                # Try to match with actual chapters
                chapter_match = None
                for chapter in chapters:
                    if self._titles_match(toc_title, chapter.get('title', '')):
                        chapter_match = chapter
                        break

                if chapter_match:
                    chapter_num = chapter_match.get('number', 0)
                    filename = f"{chapter_num:02d} - {chapter_match.get('title', '')}"
                    content += f"{indent}- [[{filename}|{toc_title}]]\n"
                else:
                    # TOC entry without corresponding chapter (might be a section header)
                    content += f"{indent}- {toc_title}\n"
        else:
            # Fallback to simple chapter list
            for chapter in chapters:
                chapter_num = chapter.get('number', 0)
                chapter_title = chapter.get('title', '')
                filename = f"{chapter_num:02d} - {chapter_title}"
                content += f"- [[{filename}|{chapter_title}]]\n"

        content += "\n---\n\n"
        content += "📚 [[{title} - Info|Book Information]]\n"

        return content

    def _titles_match(self, title1: str, title2: str) -> bool:
        """Check if two titles match (case-insensitive, ignoring punctuation)."""
        clean1 = re.sub(r'[^\w\s]', '', title1.lower()).strip()
        clean2 = re.sub(r'[^\w\s]', '', title2.lower()).strip()
        return clean1 == clean2

    def create_info_page(self, book_metadata: Dict[str, Any]) -> str:
        """Create the book information/metadata page."""
        title = book_metadata.get('title', 'Unknown Book')

        content = "---\n"
        content += f"title: \"{title} - Info\"\n"
        content += f"type: info\n"
        content += "tags:\n"
        content += f"  - book/{self._sanitize_tag(title)}\n"
        content += f"  - metadata\n"
        content += "---\n\n"

        content += f"# {title} - Book Information\n\n"

        content += "## 📖 Metadata\n\n"

        # Authors
        authors = book_metadata.get('authors', ['Unknown Author'])
        content += f"- **Authors:** {', '.join(authors)}\n"

        # Publisher
        if book_metadata.get('publisher'):
            content += f"- **Publisher:** {book_metadata['publisher']}\n"

        # Publication Date
        if book_metadata.get('publication_date'):
            content += f"- **Publication Date:** {book_metadata['publication_date']}\n"

        # ISBN
        if book_metadata.get('isbn'):
            content += f"- **ISBN:** {book_metadata['isbn']}\n"

        # Language
        if book_metadata.get('language'):
            content += f"- **Language:** {book_metadata['language']}\n"

        # Tags/Subjects
        if book_metadata.get('tags'):
            content += f"- **Subjects:** {', '.join(book_metadata['tags'])}\n"

        # Description
        if book_metadata.get('description'):
            content += f"\n## 📝 Description\n\n{book_metadata['description']}\n"

        content += "\n---\n\n"
        content += f"📚 [[{title} - Index|Back to Index]]\n"

        return content