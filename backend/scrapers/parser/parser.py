"""Parser utilities for extracting structured data from HTML.

Uses Selectolax (fast C-based parser) by default with a
BeautifulSoup fallback for complex selectors that Selectolax
does not support.
"""

from typing import Any

from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser

from backend.scrapers.exceptions import ParseError


def from_html(html: str) -> HTMLParser:
    """Parse an HTML string into a Selectolax tree."""
    try:
        return HTMLParser(html)
    except Exception as exc:
        raise ParseError(f"Failed to parse HTML: {exc}", source="parser") from exc


def from_html_soup(html: str) -> BeautifulSoup:
    """Parse an HTML string into a BeautifulSoup tree (fallback path)."""
    try:
        return BeautifulSoup(html, "html.parser")
    except Exception as exc:
        raise ParseError(
            f"Failed to parse HTML with BeautifulSoup: {exc}",
            source="parser",
        ) from exc


def text(root: Any, selector: str, default: str | None = None) -> str | None:
    """Return the text content of the first element matching *selector*."""
    if isinstance(root, HTMLParser):
        node = root.css_first(selector)
        if node is not None:
            text_val = node.text(strip=True)
            return text_val if text_val else default
    elif isinstance(root, BeautifulSoup):
        tag = root.select_one(selector)
        if tag is not None:
            text_val = tag.get_text(strip=True)
            return text_val if text_val else default
    return default


def texts(root: Any, selector: str) -> list[str]:
    """Return text content of *all* elements matching *selector*."""
    if isinstance(root, HTMLParser):
        return [n.text(strip=True) for n in root.css(selector) if n.text(strip=True)]
    elif isinstance(root, BeautifulSoup):
        return [t.get_text(strip=True) for t in root.select(selector) if t.get_text(strip=True)]
    return []


def _to_str(val: object, default: str | None = None) -> str | None:
    if isinstance(val, str):
        return val.strip()
    if val is not None:
        return str(val).strip()
    return default


def attr(root: Any, selector: str, name: str, default: str | None = None) -> str | None:
    """Return the value of attribute *name* on the first match."""
    if isinstance(root, HTMLParser):
        node = root.css_first(selector)
        if node is not None:
            return _to_str(node.attributes.get(name), default)
    elif isinstance(root, BeautifulSoup):
        tag = root.select_one(selector)
        if tag is not None:
            return _to_str(tag.get(name), default)
    return default


def attrs(root: Any, selector: str, name: str) -> list[str]:
    """Return attribute *name* from every matching element."""
    if isinstance(root, HTMLParser):
        result: list[str] = []
        for n in root.css(selector):
            val = _to_str(n.attributes.get(name))
            if val is not None:
                result.append(val)
        return result
    elif isinstance(root, BeautifulSoup):
        result = []
        for t in root.select(selector):
            val = _to_str(t.get(name))
            if val is not None:
                result.append(val)
        return result
    return []
