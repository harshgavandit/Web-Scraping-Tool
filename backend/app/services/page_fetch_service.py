import ipaddress
import socket
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.extraction.page_extractor import ExtractedDocument, extract_public_document


USER_AGENT = "BrandChatterBot/2.0 (+public brand intelligence crawler)"


@dataclass
class PageFetchResult:
    status: str
    requested_url: str
    final_url: Optional[str] = None
    robots_allowed: Optional[bool] = None
    http_status: Optional[int] = None
    error: Optional[str] = None
    document: Optional[ExtractedDocument] = None


def is_public_http_url(url: str, resolver: Callable = socket.getaddrinfo) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        answers = resolver(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except (OSError, socket.gaierror):
        return False
    for answer in answers:
        address = answer[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return bool(answers)


class PageFetchService:
    def __init__(self, resolver: Callable = socket.getaddrinfo, max_bytes: int = 2_000_000):
        self.resolver = resolver
        self.max_bytes = max_bytes

    def _safe_get(self, client: httpx.Client, url: str, max_redirects: int = 5):
        current_url = url
        for _ in range(max_redirects + 1):
            if not is_public_http_url(current_url, self.resolver):
                return None, current_url
            response = client.get(current_url)
            if 300 <= response.status_code < 400 and response.headers.get("location"):
                next_url = urljoin(current_url, response.headers["location"])
                if not is_public_http_url(next_url, self.resolver):
                    return None, next_url
                current_url = next_url
                continue
            return response, str(response.url or current_url)
        raise httpx.TooManyRedirects("Maximum redirect count exceeded")

    def fetch(self, url: str) -> PageFetchResult:
        if not is_public_http_url(url, self.resolver):
            return PageFetchResult(status="blocked", requested_url=url, error="URL is not a public HTTP(S) target")

        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            with httpx.Client(timeout=20.0, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
                robots_response, robots_final_url = self._safe_get(client, robots_url)
                if robots_response is None:
                    return PageFetchResult(status="blocked", requested_url=url, final_url=robots_final_url, error="Robots redirect targets a non-public URL")
                robots_allowed = True
                if robots_response.status_code == 200:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(robots_response.text.splitlines())
                    robots_allowed = parser.can_fetch(USER_AGENT, url)
                elif robots_response.status_code >= 500:
                    robots_allowed = False
                if not robots_allowed:
                    return PageFetchResult(status="blocked", requested_url=url, robots_allowed=False)

                response, final_url = self._safe_get(client, url)
                if response is None:
                    return PageFetchResult(status="blocked", requested_url=url, final_url=final_url, robots_allowed=True, error="Redirected to a non-public target")
                if response.status_code != 200:
                    return PageFetchResult(status="failed", requested_url=url, final_url=final_url, robots_allowed=True, http_status=response.status_code, error=f"HTTP {response.status_code}")
                content_type = response.headers.get("content-type", "")
                if "html" not in content_type.lower():
                    return PageFetchResult(status="unsupported", requested_url=url, final_url=final_url, robots_allowed=True, http_status=200, error="Unsupported content type")
                if len(response.text.encode("utf-8")) > self.max_bytes:
                    return PageFetchResult(status="failed", requested_url=url, final_url=final_url, robots_allowed=True, http_status=200, error="Page exceeds maximum size")
                document = extract_public_document(response.text, final_url)
                return PageFetchResult(status="fetched", requested_url=url, final_url=final_url, robots_allowed=True, http_status=200, document=document)
        except httpx.HTTPError as exc:
            return PageFetchResult(status="failed", requested_url=url, error=str(exc))


page_fetch_service = PageFetchService()
