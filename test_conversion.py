#!/usr/bin/env python3
"""Test conversion to see what's happening."""

from pathlib import Path
from src.epub_to_obsidian.epub_parser import EPUBParser
from src.epub_to_obsidian.markdown_converter import MarkdownConverter

epub_path = Path("data/AI_Engineering.epub")
parser = EPUBParser(epub_path)

chapters = parser.get_chapters()
converter = MarkdownConverter()

# Test on chapter 5 (Chapter 1 of the book)
chapter = chapters[4]  # 0-indexed

print(f"Chapter: {chapter['title']}")
print(f"HTML content length: {len(chapter['content_html'])}")
print(f"First 1000 chars of HTML:\n{chapter['content_html'][:1000]}\n")

# Test conversion
markdown = converter.convert_chapter(chapter, "AI Engineering")

print(f"Markdown length: {len(markdown)}")
print(f"Markdown content:\n{markdown}")