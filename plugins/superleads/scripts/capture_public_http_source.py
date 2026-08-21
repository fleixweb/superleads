#!/usr/bin/env python3
"""Capture public HTTP(S) sources with read-only curl GET requests.

This helper opens a URL supplied by the caller. It never searches, follows
credentials, or turns fetched text into Claims, EvidenceCards, or MatrixRows.
The emitted adapter report is intentionally compatible with the existing
``codex_cli_shell_http_source_open`` capability contract.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from _superleads_common import has_text, is_safe_public_http_url


ROUTE = "product_outbound_market_analysis_public_http_capture"
ADAPTER_ID = "codex_cli_shell_http_source_open"
ADAPTER_VERSION = "1"
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_EXCERPT_CHARS = 1000
PUBLIC_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain", "application/json")


def _issue(code: str, message: str, path: str = "") -> dict[str, str]:
    item = {"severity": "critical", "code": code, "message": message}
    if path:
        item["path"] = path
    return item


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._title_depth = 0
        self._hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered == "title":
            self._title_depth += 1
        if lowered in {"script", "style", "noscript", "template", "svg"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered == "title" and self._title_depth:
            self._title_depth -= 1
        if lowered in {"script", "style", "noscript", "template", "svg"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._title_depth:
            self.title_parts.append(data)
        if not self._title_depth and not self._hidden_depth and data.strip():
            self.text_parts.append(data)


def _normalize_text(parts: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _parse_body(body: bytes, content_type: str, explicit_title: str | None) -> tuple[str | None, str | None]:
    text = body.decode("utf-8", errors="replace")
    parser = _VisibleTextParser()
    if "html" in content_type.casefold() or "xhtml" in content_type.casefold():
        try:
            parser.feed(text)
            parser.close()
        except Exception:  # noqa: BLE001 - malformed HTML still may have visible text
            pass
        title = _normalize_text(parser.title_parts) or explicit_title
        visible = _normalize_text(parser.text_parts)
    else:
        title = explicit_title
        visible = _normalize_text([text])
    return title, visible[:MAX_EXCERPT_CHARS] if visible else None


def _stable_source_suffix(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def _base_result(url: str, run_id: str, captured_at: str) -> dict[str, Any]:
    return {
        "ok": False,
        "route": ROUTE,
        "run_id": run_id,
        "captured_at": captured_at,
        "execution_level": "public_http_source_capture",
        "not_evidence": True,
        "does_not_search_web": True,
        "does_not_create_search_logs": True,
        "does_not_create_claims": True,
        "does_not_create_evidence_cards": True,
        "does_not_create_matrix_rows": True,
        "allowed_output": "source_observation_and_source_open_adapter_only",
        "requested_url": url,
        "issues": [],
        "capability_adapter_reports": [],
        "sources": [],
        "observations": [],
        "guardrails": [
            "只执行公开 HTTP(S) URL 的 curl GET，不执行搜索。",
            "不携带 Cookie、Authorization、token、密码或其他凭证。",
            "Source / Observation 只是后续 EvidenceCard 的输入，不是事实结论。",
            "失败、非 2xx、无标题或无可见正文时不生成来源记录。",
        ],
    }


def _public_resolution(url: str) -> tuple[str, int, str] | None:
    """Resolve a URL once and return an ASCII hostname plus a global IP.

    ``curl --resolve`` pins the selected address for this request. Redirects
    are deliberately handled by the caller so every destination repeats this
    check rather than inheriting curl's resolver state.
    """
    parsed = urlsplit(url)
    host = parsed.hostname
    if not host:
        return None
    try:
        ascii_host = host.encode("idna").decode("ascii")
        port = parsed.port or (443 if parsed.scheme.casefold() == "https" else 80)
        answers = socket.getaddrinfo(ascii_host, port, type=socket.SOCK_STREAM)
    except (UnicodeError, ValueError, OSError):
        return None
    for _, _, _, _, sockaddr in answers:
        try:
            address = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            continue
        if address.is_global:
            return ascii_host, port, str(address)
    return None


def _header_location(raw_headers: bytes) -> str | None:
    """Read Location from the last response block without trusting its URL."""
    blocks = re.split(br"\r?\n\r?\n", raw_headers)
    for block in reversed(blocks):
        if not block.lstrip().startswith(b"HTTP/"):
            continue
        for line in block.splitlines()[1:]:
            if line.lower().startswith(b"location:"):
                return line.split(b":", 1)[1].decode("utf-8", errors="replace").strip()
        return None
    return None


def _run_curl_once(url: str) -> tuple[int, str, str, bytes, str | None] | tuple[None, None, None, None, None, str]:
    resolution = _public_resolution(url)
    if resolution is None:
        return (None, None, None, None, None, "URL hostname did not resolve to a public global address")
    hostname, port, address = resolution
    with tempfile.TemporaryDirectory(prefix="superleads-http-") as directory:
        body_path = Path(directory) / "body"
        headers_path = Path(directory) / "headers"
        command = [
            "curl",
            "--disable",
            "--silent",
            "--show-error",
            "--noproxy",
            "*",
            "--connect-timeout",
            "10",
            "--max-time",
            "30",
            "--proto",
            "=http,https",
            "--max-filesize",
            str(MAX_BODY_BYTES),
            "--request",
            "GET",
            "--resolve",
            f"{hostname}:{port}:[{address}]" if ":" in address else f"{hostname}:{port}:{address}",
            "--dump-header",
            str(headers_path),
            "--output",
            str(body_path),
            "--write-out",
            "%{http_code}\\t%{url_effective}\\t%{content_type}",
            "--url",
            url,
        ]
        try:
            proc = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=35)
        except FileNotFoundError:
            return (None, None, None, None, None, "curl executable is unavailable")
        except subprocess.TimeoutExpired:
            return (None, None, None, None, None, "curl request timed out")
        if proc.returncode != 0:
            detail = proc.stderr.decode("utf-8", errors="replace").strip()[:300]
            return (None, None, None, None, None, f"curl failed: {detail or 'unknown curl error'}")
        fields = proc.stdout.decode("utf-8", errors="replace").split("\t", 2)
        if len(fields) != 3:
            return (None, None, None, None, None, "curl did not return status, final URL, and content type")
        try:
            status = int(fields[0])
        except ValueError:
            return (None, None, None, None, None, "curl returned an invalid HTTP status")
        if not body_path.exists():
            return (None, None, None, None, None, "curl did not produce a response body")
        body = body_path.read_bytes()[:MAX_BODY_BYTES]
        headers = headers_path.read_bytes() if headers_path.exists() else b""
        return status, fields[1], fields[2], body, _header_location(headers)


def _run_curl(url: str) -> tuple[int, str, str, bytes] | tuple[None, None, None, None, str]:
    current_url = url
    for _ in range(6):
        fetched = _run_curl_once(current_url)
        if len(fetched) == 6:
            return (None, None, None, None, fetched[5])
        status, effective_url, content_type, body, location = fetched
        if not isinstance(status, int) or not 300 <= status < 400:
            return status, effective_url, content_type, body
        if not has_text(location):
            return status, effective_url, content_type, body
        next_url = urljoin(current_url, str(location))
        if not is_safe_public_http_url(next_url):
            return (None, None, None, None, "redirect target is not a public credential-free HTTP(S) URL")
        current_url = next_url
    return (None, None, None, None, "redirect limit exceeded")


def capture(urls: str | list[str], *, run_id: str = "public-http-capture-run", explicit_title: str | None = None) -> dict[str, Any]:
    requested_urls = [urls] if isinstance(urls, str) else list(urls)
    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    result = _base_result(requested_urls[0] if requested_urls else "", run_id, captured_at)
    result["requested_urls"] = requested_urls
    if not requested_urls:
        result["issues"].append(_issue("capture_urls_missing", "at least one public HTTP(S) URL is required", "requested_urls"))
        return result
    if len(set(requested_urls)) != len(requested_urls):
        result["issues"].append(_issue("capture_duplicate_url", "a capture batch cannot contain the same URL more than once", "requested_urls"))
        return result

    captures: list[dict[str, Any]] = []
    for index, url in enumerate(requested_urls, start=1):
        path = f"requested_urls[{index - 1}]"
        if not is_safe_public_http_url(url):
            result["issues"].append(_issue("capture_url_not_public", "URL must be a public credential-free HTTP(S) URL", path))
            return result
        fetched = _run_curl(url)
        if len(fetched) == 5:
            result["issues"].append(_issue("capture_curl_failed", fetched[4], path))
            return result
        status, final_url, content_type, body = fetched
        if not isinstance(final_url, str) or not is_safe_public_http_url(final_url):
            result["issues"].append(_issue("capture_final_url_not_public", "curl final URL must remain a public credential-free HTTP(S) URL", path))
            return result
        if not isinstance(status, int) or not 200 <= status < 300:
            result["issues"].append(_issue("capture_http_status_not_success", "curl source capture requires a 2xx HTTP response", path))
            return result
        content_type = str(content_type or "").split(";", 1)[0].strip().casefold()
        if content_type and content_type not in PUBLIC_CONTENT_TYPES:
            result["issues"].append(_issue("capture_content_type_unsupported", "source capture requires an HTML, text, or JSON response", path))
            return result
        title, excerpt = _parse_body(body, content_type, explicit_title)
        if not has_text(title):
            result["issues"].append(_issue("capture_title_missing", "opened source must have an HTML title or explicit title", path))
            return result
        if not has_text(excerpt):
            result["issues"].append(_issue("capture_excerpt_missing", "opened source must have a non-empty visible-text excerpt", path))
            return result
        captures.append({
            "source_id": f"source-http-{_stable_source_suffix(url)}",
            "observation_id": f"observation-http-{_stable_source_suffix(url)}",
            "original_url": url,
            "final_url": final_url,
            "http_status": status,
            "title": title,
            "excerpt": excerpt,
        })

    operations = [{
        "status": "verified",
        "request_method": "GET",
        "original_url": item["original_url"],
        "final_url": item["final_url"],
        "source_id": item["source_id"],
        "observation_id": item["observation_id"],
        "http_status": item["http_status"],
        "source_title": item["title"],
        "raw_excerpt": item["excerpt"],
        "excerpt_locator": "html.body.visible_text",
    } for item in captures]
    result["capability_adapter_reports"] = [{
        "platform": "codex_cli",
        "adapter": {"adapter_id": ADAPTER_ID, "adapter_version": ADAPTER_VERSION},
        "detected_at": captured_at,
        "detection": "explicit curl GET public source capture",
        "host_tools": {
            "shell_http": {
                "status": "available",
                "allowed_concrete_tools": ["curl"],
                "operations": {"open_source": operations},
            }
        },
        "canonical_capabilities": {"source.open": "available"},
    }]
    result["sources"] = [{
        "source_id": item["source_id"],
        "canonical_url": item["original_url"],
        "final_url": item["final_url"],
        "publisher_relation": "unknown",
        "provenance": "discovered_public",
        "medium": "website",
        "access_boundary": "curl_public_get",
        "owner_hint": urlsplit(item["final_url"]).hostname or "public-source",
        "material_role": "published_source_copy",
    } for item in captures]
    result["observations"] = [{
        "observation_id": item["observation_id"],
        "run_id": run_id,
        "source_id": item["source_id"],
        "capability": "source.open",
        "concrete_tool": "curl",
        "observed_at": captured_at,
        "access_status": "opened",
        "http_status": item["http_status"],
        "title": item["title"],
        "raw_excerpt": item["excerpt"],
        "page_or_dom_locator": "html.body.visible_text",
        "extraction_method": "curl_get_html_visible_text",
        "language": "unknown",
        "translation_status": "not_translated",
    } for item in captures]
    result["ok"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", required=True, help="Public HTTP(S) URL to open; repeat for an atomic batch")
    parser.add_argument("--title", help="Explicit source title for non-HTML or title-less pages")
    parser.add_argument("--run-id", default="public-http-capture-run")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()
    result = capture(args.url, run_id=args.run_id, explicit_title=args.title)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
