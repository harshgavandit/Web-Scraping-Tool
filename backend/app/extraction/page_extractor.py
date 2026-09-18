import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass
class ExtractedDocument:
    canonical_url: str
    title: str
    main_text: str
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_type: str = "article"
    language: Optional[str] = None
    product_data: Dict[str, Any] = field(default_factory=dict)
    structured_data: List[Dict[str, Any]] = field(default_factory=list)


def _meta(soup: BeautifulSoup, *keys: str) -> Optional[str]:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return None


def _json_ld_nodes(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        nodes: List[Dict[str, Any]] = []
        for item in value:
            nodes.extend(_json_ld_nodes(item))
        return nodes
    if not isinstance(value, dict):
        return []
    nodes = [value]
    if "@graph" in value:
        nodes.extend(_json_ld_nodes(value["@graph"]))
    return nodes


def _has_schema_type(node: Dict[str, Any], expected: str) -> bool:
    """Schema.org permits @type to be a string or an array of strings."""
    value = node.get("@type")
    return value == expected or (isinstance(value, list) and expected in value)


def _product_data(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    product = next((node for node in nodes if _has_schema_type(node, "Product")), None)
    review = next((node for node in nodes if _has_schema_type(node, "Review")), None)
    if product and isinstance(product.get("review"), dict):
        review = product["review"]
    if not product and not review:
        return {}
    rating = (product or {}).get("aggregateRating") or {}
    try:
        rating_value = float(rating.get("ratingValue")) if rating.get("ratingValue") is not None else None
    except (TypeError, ValueError):
        rating_value = None
    try:
        review_count = int(rating.get("reviewCount") or rating.get("ratingCount")) if (rating.get("reviewCount") or rating.get("ratingCount")) is not None else None
    except (TypeError, ValueError):
        review_count = None
    return {
        "name": (product or {}).get("name"),
        "sku": (product or {}).get("sku"),
        "gtin": (product or {}).get("gtin") or (product or {}).get("gtin13"),
        "rating_value": rating_value,
        "review_count": review_count,
        "review_body": (review or {}).get("reviewBody"),
    }


def extract_public_document(html: str, source_url: str) -> ExtractedDocument:
    soup = BeautifulSoup(html, "html.parser")
    nodes: List[Dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            nodes.extend(_json_ld_nodes(json.loads(script.string or script.get_text())))
        except (json.JSONDecodeError, TypeError):
            continue

    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = urljoin(source_url, canonical_tag.get("href")) if canonical_tag and canonical_tag.get("href") else source_url
    article_node = next((
        node for node in nodes
        if any(_has_schema_type(node, schema_type) for schema_type in ("Article", "NewsArticle", "BlogPosting"))
    ), {})
    title = (
        _meta(soup, "og:title", "twitter:title")
        or article_node.get("headline")
        or (soup.title.get_text(" ", strip=True) if soup.title else "")
    )
    publisher_value = article_node.get("publisher")
    if isinstance(publisher_value, dict):
        publisher_value = publisher_value.get("name")
    author_value = article_node.get("author")
    if isinstance(author_value, dict):
        author_value = author_value.get("name")

    container = soup.find("article") or soup.find("main") or soup.body or soup
    for tag in container.find_all(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()
    main_text = "\n".join(
        line for line in (part.strip() for part in container.get_text("\n").splitlines()) if line
    )
    product_data = _product_data(nodes)
    return ExtractedDocument(
        canonical_url=canonical,
        title=title,
        main_text=main_text,
        publisher=_meta(soup, "og:site_name", "application-name") or publisher_value,
        author=_meta(soup, "author", "article:author") or author_value,
        published_at=_date(_meta(soup, "article:published_time", "datePublished") or article_node.get("datePublished")),
        updated_at=_date(_meta(soup, "article:modified_time", "dateModified") or article_node.get("dateModified")),
        source_type="product_review" if product_data else ("news" if _has_schema_type(article_node, "NewsArticle") else "article"),
        language=(soup.html.get("lang") if soup.html else None),
        product_data=product_data,
        structured_data=nodes,
    )
