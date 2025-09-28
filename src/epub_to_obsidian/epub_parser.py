"""EPUB parsing module for extracting book content and metadata."""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re


class EPUBParser:
    """Parser for extracting content and metadata from EPUB files."""

    def __init__(self, epub_path: Path):
        """Initialize parser with EPUB file path."""
        self.epub_path = epub_path
        self.book = epub.read_epub(str(epub_path))
        self.metadata = self._extract_metadata()

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract book metadata from EPUB."""
        metadata = {}

        # Title
        title = self.book.get_metadata('DC', 'title')
        metadata['title'] = title[0][0] if title else 'Unknown Title'

        # Author(s)
        creators = self.book.get_metadata('DC', 'creator')
        if creators:
            metadata['authors'] = [creator[0] for creator in creators]
        else:
            metadata['authors'] = ['Unknown Author']

        # Publisher
        publisher = self.book.get_metadata('DC', 'publisher')
        metadata['publisher'] = publisher[0][0] if publisher else None

        # Language
        language = self.book.get_metadata('DC', 'language')
        metadata['language'] = language[0][0] if language else 'en'

        # ISBN
        identifiers = self.book.get_metadata('DC', 'identifier')
        for identifier in identifiers or []:
            if 'isbn' in str(identifier).lower():
                metadata['isbn'] = identifier[0]
                break

        # Publication date
        date = self.book.get_metadata('DC', 'date')
        metadata['publication_date'] = date[0][0] if date else None

        # Description
        description = self.book.get_metadata('DC', 'description')
        metadata['description'] = description[0][0] if description else None

        # Subject/Tags
        subjects = self.book.get_metadata('DC', 'subject')
        if subjects:
            metadata['tags'] = [subject[0] for subject in subjects]

        return metadata

    def get_chapters(self) -> List[Dict[str, Any]]:
        """Extract all chapters with their content and metadata."""
        chapters = []

        # Get spine (reading order)
        spine_ids = [item_id for item_id, _ in self.book.spine]

        # Build a map of items
        items_map = {}
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                items_map[item.get_id()] = item

        # Process chapters in spine order
        chapter_num = 0
        for spine_id in spine_ids:
            if spine_id in items_map:
                item = items_map[spine_id]
                chapter_data = self._process_chapter(item, chapter_num)
                if chapter_data and chapter_data['content'].strip():  # Skip empty chapters
                    chapters.append(chapter_data)
                    chapter_num += 1

        return chapters

    def _process_chapter(self, item: ebooklib.epub.EpubItem, chapter_num: int) -> Optional[Dict[str, Any]]:
        """Process a single chapter item."""
        try:
            # Get HTML content
            html_content = item.get_content().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract title (try different strategies)
            title = self._extract_chapter_title(soup, item, chapter_num)

            # Clean the HTML for conversion
            self._clean_html(soup)

            # Get the body content
            body = soup.find('body')
            if body:
                content_html = str(body)
            else:
                content_html = str(soup)

            return {
                'number': chapter_num + 1,
                'title': title,
                'content_html': content_html,
                'content': soup.get_text(strip=True),  # Plain text for preview
                'item_id': item.get_id(),
                'file_name': item.get_name(),
            }
        except Exception as e:
            print(f"Error processing chapter {chapter_num}: {e}")
            return None

    def _extract_chapter_title(self, soup: BeautifulSoup, item: ebooklib.epub.EpubItem, chapter_num: int) -> str:
        """Extract chapter title from HTML content."""
        # Try to find title in common heading tags
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading and heading.get_text(strip=True):
                return heading.get_text(strip=True)

        # Try to find title in <title> tag
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)

        # Try to extract from filename
        file_name = Path(item.get_name()).stem
        if file_name and not file_name.isdigit():
            # Clean up filename to make it more readable
            title = re.sub(r'[_-]', ' ', file_name)
            title = re.sub(r'\d+$', '', title).strip()
            if title:
                return title.title()

        # Fallback to generic chapter name
        return f"Chapter {chapter_num + 1}"

    def _clean_html(self, soup: BeautifulSoup) -> None:
        """Clean HTML content for better markdown conversion."""
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()

        # Remove empty paragraphs
        for p in soup.find_all('p'):
            if not p.get_text(strip=True):
                p.decompose()

    def get_images(self) -> List[Tuple[str, bytes]]:
        """Extract all images from the EPUB."""
        images = []

        for item in self.book.get_items():
            if item.get_type() in [ebooklib.ITEM_IMAGE, ebooklib.ITEM_COVER]:
                try:
                    images.append((item.get_name(), item.get_content()))
                except Exception as e:
                    print(f"Error extracting image {item.get_name()}: {e}")

        return images

    def get_cover_image(self) -> Optional[Tuple[str, bytes]]:
        """Get the cover image if available."""
        # Try to get cover from metadata
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_COVER:
                try:
                    return (item.get_name(), item.get_content())
                except Exception:
                    pass

        # Try to find cover in images
        images = self.get_images()
        for name, content in images:
            if 'cover' in name.lower():
                return (name, content)

        return None

    def get_toc(self) -> List[Dict[str, Any]]:
        """Extract table of contents structure."""
        toc = []

        # Get the TOC from the book
        book_toc = self.book.toc

        def process_toc_item(item, level=0):
            """Recursively process TOC items."""
            if isinstance(item, tuple):
                # It's a section with children
                section, children = item
                toc_entry = {
                    'title': section.title if hasattr(section, 'title') else str(section),
                    'level': level,
                    'href': section.href if hasattr(section, 'href') else None
                }
                toc.append(toc_entry)

                for child in children:
                    process_toc_item(child, level + 1)
            else:
                # It's a simple item
                toc_entry = {
                    'title': item.title if hasattr(item, 'title') else str(item),
                    'level': level,
                    'href': item.href if hasattr(item, 'href') else None
                }
                toc.append(toc_entry)

        for item in book_toc:
            process_toc_item(item)

        return toc