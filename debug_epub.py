#!/usr/bin/env python3
"""Debug script to check EPUB content extraction."""

from pathlib import Path
from src.epub_to_obsidian.epub_parser import EPUBParser

epub_path = Path("data/AI_Engineering.epub")
parser = EPUBParser(epub_path)

chapters = parser.get_chapters()

print(f"Total chapters: {len(chapters)}")
print("\nFirst 3 chapters:")
for i, chapter in enumerate(chapters[:3]):
    print(f"\n--- Chapter {i+1}: {chapter['title']} ---")
    print(f"File: {chapter['file_name']}")
    print(f"HTML content length: {len(chapter.get('content_html', ''))}")
    print(f"Plain text length: {len(chapter.get('content', ''))}")

    # Show first 500 chars of HTML
    html = chapter.get('content_html', '')[:500]
    print(f"HTML preview: {html}")

    # Show first 500 chars of plain text
    text = chapter.get('content', '')[:500]
    print(f"Text preview: {text}")