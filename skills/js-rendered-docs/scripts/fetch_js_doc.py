#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LOCAL_PYTHON_DEPS = SKILL_DIR / "python_deps"
LOCAL_PLAYWRIGHT_BROWSERS = SKILL_DIR / "playwright-browsers"

if LOCAL_PYTHON_DEPS.exists():
    sys.path.insert(0, str(LOCAL_PYTHON_DEPS))
if LOCAL_PLAYWRIGHT_BROWSERS.exists() and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(LOCAL_PLAYWRIGHT_BROWSERS)

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - exercised through runtime check
    BeautifulSoup = None

try:
    from markdownify import markdownify as html_to_markdown
except ImportError:  # pragma: no cover - exercised through runtime check
    html_to_markdown = None


MIN_CONTENT_TEXT = {
    "generic": 240,
    "genesys": 160,
}

PROFILE_SELECTORS = {
    "generic": [
        "article",
        "main article",
        "main",
        '[role="main"]',
        ".content",
        ".markdown",
    ],
    "genesys": [
        ".theme-doc-markdown",
        ".docMainContainer article",
        ".docMainContainer",
        ".markdown",
        "main article",
        "article",
        "main",
        '[role="main"]',
    ],
}

COMMON_NOISE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "aside",
    "form",
    "button[aria-label*='cookie' i]",
    '[aria-label="breadcrumb"]',
    ".breadcrumbs",
    ".breadcrumb",
    ".pagination-nav",
    ".theme-doc-toc-desktop",
    ".theme-doc-toc-mobile",
    ".table-of-contents",
    ".toc",
    ".navbar",
    ".menu",
    ".sidebar",
    '[class*="sidebar"]',
    '[class*="toc"]',
    '[class*="breadcrumb"]',
    '[class*="cookie"]',
    '[class*="consent"]',
    '[id*="cookie"]',
    '[id*="consent"]',
]

PROFILE_NOISE_SELECTORS = {
    "generic": [],
    "genesys": [
        ".docSidebarContainer",
        ".theme-doc-breadcrumbs",
        ".theme-edit-this-page",
    ],
}

LOW_VALUE_LINES = {
    "on this page",
    "table of contents",
    "cookie settings",
    "accept",
    "accept all",
    "manage cookies",
    "skip to main content",
}


@dataclass
class RenderedPage:
    source_url: str
    final_url: str
    title: str
    profile: str
    html: str
    fetched_at_utc: str


@dataclass
class ExtractedContent:
    title: str
    markdown_body: str
    content_selector: str
    content_text_length: int


@dataclass
class DirectMarkdownPage:
    source_url: str
    final_url: str
    title: str
    profile: str
    markdown_body: str
    fetched_at_utc: str
    fetch_method: str
    source_asset_url: str


@dataclass
class AssetLocalizationResult:
    markdown_body: str
    downloaded_assets: list[dict[str, str]]
    failed_assets: list[str]


IMAGE_MARKDOWN_PATTERN = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\((?P<target><[^>]+>|[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\)'
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a JavaScript-driven docs page and save a compact Markdown snapshot."
    )
    parser.add_argument("url", help="Page URL to fetch")
    parser.add_argument(
        "--out-dir",
        default="./scraped-docs",
        help="Directory for generated Markdown and metadata (default: ./scraped-docs)",
    )
    parser.add_argument(
        "--profile",
        choices=["auto", "generic", "genesys"],
        default="auto",
        help="Extraction profile to use (default: auto)",
    )
    parser.add_argument(
        "--timeout-secs",
        type=int,
        default=60,
        help="Navigation and readiness timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing snapshot for the same URL slug",
    )
    parser.add_argument(
        "--debug-dir",
        default=None,
        help="Directory for failure artifacts (default: <out-dir>/_debug)",
    )
    return parser


def ensure_browser_dependencies() -> None:
    missing = []
    if BeautifulSoup is None:
        missing.append("beautifulsoup4")
    if html_to_markdown is None:
        missing.append("markdownify")
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        missing.append("playwright")
    if missing:
        packages = " ".join(sorted(set(missing)))
        raise RuntimeError(
            "Missing Python dependencies: "
            f"{packages}. Install with: pip install {packages} && playwright install chromium"
        )


def resolve_profile(url: str, requested: str) -> str:
    if requested != "auto":
        return requested
    hostname = (urlparse(url).hostname or "").lower()
    if hostname == "developer.genesys.cloud":
        return "genesys"
    return "generic"


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [parsed.netloc, parsed.path.strip("/")]
    if parsed.query:
        parts.append(parsed.query)
    raw = "-".join(part for part in parts if part)
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug[:120] or "page"


def ensure_text(value: str | None, fallback: str) -> str:
    if value and value.strip():
        return value.strip()
    return fallback


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"
    normalized = parsed._replace(
        scheme=scheme,
        netloc=netloc,
        path=path,
        fragment="",
    )
    return normalized.geturl()


def snapshot_index_path(out_dir: Path) -> Path:
    return out_dir / "index.json"


def load_snapshot_index(out_dir: Path) -> dict[str, Any]:
    index_path = snapshot_index_path(out_dir)
    if not index_path.exists():
        return {"version": 1, "entries": {}}

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "entries": {}}

    entries = data.get("entries")
    if not isinstance(entries, dict):
        entries = {}
    return {"version": 1, "entries": entries}


def save_snapshot_index(out_dir: Path, index: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshot_index_path(out_dir).write_text(json.dumps(index, indent=2), encoding="utf-8")


def remove_snapshot_index_entry(index: dict[str, Any], url: str) -> bool:
    normalized = normalize_url(url)
    if normalized in index["entries"]:
        del index["entries"][normalized]
        return True
    return False


def build_snapshot_index_entry(
    out_dir: Path,
    markdown_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_url": metadata["source_url"],
        "final_url": metadata.get("final_url", metadata["source_url"]),
        "title": metadata.get("title", ""),
        "profile": metadata.get("profile", ""),
        "fetch_method": metadata.get("fetch_method", ""),
        "fetched_at_utc": metadata.get("fetched_at_utc", ""),
        "markdown_path": markdown_path.relative_to(out_dir).as_posix(),
        "metadata_path": metadata_path.relative_to(out_dir).as_posix(),
    }


def update_snapshot_index(
    out_dir: Path,
    index: dict[str, Any],
    markdown_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    entry = build_snapshot_index_entry(out_dir, markdown_path, metadata_path, metadata)
    aliases = {
        normalize_url(metadata["source_url"]),
        normalize_url(metadata.get("final_url", metadata["source_url"])),
    }
    for alias in aliases:
        index["entries"][alias] = entry
    save_snapshot_index(out_dir, index)
    return entry


def load_metadata_file(metadata_path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def lookup_snapshot_index_entry(index: dict[str, Any], url: str) -> dict[str, Any] | None:
    entry = index["entries"].get(normalize_url(url))
    return entry if isinstance(entry, dict) else None


def resolve_snapshot_paths(out_dir: Path, entry: dict[str, Any]) -> tuple[Path, Path]:
    return out_dir / entry["markdown_path"], out_dir / entry["metadata_path"]


def lookup_cached_snapshot(
    out_dir: Path,
    index: dict[str, Any],
    url: str,
) -> tuple[Path, Path, dict[str, Any]] | None:
    entry = lookup_snapshot_index_entry(index, url)
    if entry is None:
        return None

    markdown_path, metadata_path = resolve_snapshot_paths(out_dir, entry)
    if not markdown_path.exists() or not metadata_path.exists():
        removed = False
        for alias in [entry.get("source_url", ""), entry.get("final_url", "")]:
            if alias:
                removed = remove_snapshot_index_entry(index, alias) or removed
        if removed:
            save_snapshot_index(out_dir, index)
        return None

    metadata = load_metadata_file(metadata_path)
    if metadata is None:
        return None

    return markdown_path, metadata_path, metadata


def maybe_backfill_snapshot_index(
    out_dir: Path,
    index: dict[str, Any],
    slug: str,
    url: str,
) -> tuple[Path, Path, dict[str, Any]] | None:
    markdown_path = out_dir / f"{slug}.md"
    metadata_path = out_dir / f"{slug}.meta.json"
    if not markdown_path.exists() or not metadata_path.exists():
        return None

    metadata = load_metadata_file(metadata_path)
    if metadata is None:
        return None

    source_url = metadata.get("source_url")
    final_url = metadata.get("final_url")
    if normalize_url(url) not in {
        normalize_url(source_url) if source_url else "",
        normalize_url(final_url) if final_url else "",
    }:
        return None

    update_snapshot_index(out_dir, index, markdown_path, metadata_path, metadata)
    return markdown_path, metadata_path, metadata


def genesys_asset_url(url: str) -> str | None:
    parsed = urlparse(url)
    if (parsed.hostname or "").lower() != "developer.genesys.cloud":
        return None
    path = parsed.path.rstrip("/")
    if not path:
        return None
    return f"https://yeticms-api.genesys.cloud/assets/gc-dev-center{path}.md"


def fetch_genesys_asset(url: str, timeout_secs: int) -> DirectMarkdownPage | None:
    asset_url = genesys_asset_url(url)
    if not asset_url:
        return None

    request = Request(asset_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=max(timeout_secs, 1)) as response:
            raw_markdown = response.read().decode("utf-8")
    except (HTTPError, URLError):
        return None

    body = strip_yaml_frontmatter(raw_markdown)
    body = compact_markdown(body)
    title = extract_markdown_title(raw_markdown) or first_markdown_heading(body) or slug_from_url(url)
    if len(body.strip()) < 120:
        return None

    return DirectMarkdownPage(
        source_url=url,
        final_url=url,
        title=title,
        profile="genesys",
        markdown_body=body,
        fetched_at_utc=utc_now(),
        fetch_method="genesys-asset",
        source_asset_url=asset_url,
    )


def render_page(url: str, profile: str, timeout_secs: int, debug_dir: Path) -> RenderedPage:
    ensure_browser_dependencies()
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    timeout_ms = max(timeout_secs, 1) * 1000
    fetched_at = utc_now()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1800})
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("load", timeout=min(timeout_ms, 15000))
            except PlaywrightError:
                pass

            wait_for_content(page, profile, timeout_ms)
            strip_overlays(page)
            page.wait_for_timeout(300)

            return RenderedPage(
                source_url=url,
                final_url=page.url,
                title=ensure_text(page.title(), slug_from_url(url).replace("-", " ")),
                profile=profile,
                html=page.content(),
                fetched_at_utc=fetched_at,
            )
        except Exception:
            capture_debug_artifacts(page, debug_dir, slug_from_url(url))
            raise
        finally:
            context.close()
            browser.close()


def wait_for_content(page: Any, profile: str, timeout_ms: int) -> None:
    selectors = PROFILE_SELECTORS[profile]
    min_length = MIN_CONTENT_TEXT[profile]
    deadline = time.monotonic() + (timeout_ms / 1000)
    previous_length = -1
    stable_samples = 0

    while time.monotonic() < deadline:
        current_length = page.evaluate(
            """
            (selectors) => {
              const lengths = selectors.map((selector) => {
                const node = document.querySelector(selector);
                return node ? (node.innerText || "").trim().length : 0;
              });
              const bodyLength = document.body ? (document.body.innerText || "").trim().length : 0;
              return Math.max(bodyLength, ...lengths, 0);
            }
            """,
            selectors,
        )

        if current_length >= min_length:
            if abs(current_length - previous_length) <= 5:
                stable_samples += 1
                if stable_samples >= 2:
                    return
            else:
                stable_samples = 0
        previous_length = current_length
        page.wait_for_timeout(400)

    raise TimeoutError(
        f"Timed out waiting for rendered content with profile={profile} after {timeout_ms // 1000}s"
    )


def strip_overlays(page: Any) -> None:
    page.evaluate(
        """
        () => {
          const selectors = [
            '[role="dialog"]',
            '[aria-modal="true"]',
            '[class*="cookie"]',
            '[class*="consent"]',
            '[id*="cookie"]',
            '[id*="consent"]'
          ];
          for (const selector of selectors) {
            for (const node of document.querySelectorAll(selector)) {
              node.remove();
            }
          }
        }
        """
    )


def extract_document(rendered: RenderedPage) -> ExtractedContent:
    if BeautifulSoup is None or html_to_markdown is None:
        raise RuntimeError("Extraction dependencies are unavailable.")

    soup = BeautifulSoup(rendered.html, "html.parser")
    remove_noise(soup, rendered.profile)
    container, selector = choose_content_container(soup, rendered.profile)
    remove_noise(container, rendered.profile)

    raw_markdown = html_to_markdown(
        str(container),
        heading_style="ATX",
        bullets="-",
    )
    markdown_body = compact_markdown(raw_markdown)
    title = first_heading_text(container) or rendered.title

    if "enable javascript to run this app" in markdown_body.lower():
        raise RuntimeError("Rendered page still contains the SPA placeholder instead of article content.")
    if len(markdown_body.strip()) < 120:
        raise RuntimeError("Extracted Markdown is too short to be a useful docs snapshot.")

    return ExtractedContent(
        title=ensure_text(title, rendered.title),
        markdown_body=markdown_body,
        content_selector=selector,
        content_text_length=len(container.get_text(" ", strip=True)),
    )


def remove_noise(node: Any, profile: str) -> None:
    selectors = COMMON_NOISE_SELECTORS + PROFILE_NOISE_SELECTORS.get(profile, [])
    for selector in selectors:
        for match in node.select(selector):
            match.decompose()


def choose_content_container(soup: Any, profile: str) -> tuple[Any, str]:
    threshold = MIN_CONTENT_TEXT[profile]
    fallback: tuple[Any, str, int] | None = None

    for selector in PROFILE_SELECTORS[profile]:
        matches = soup.select(selector)
        for match in matches:
            text_length = len(match.get_text(" ", strip=True))
            if text_length >= threshold:
                return match, selector
            if fallback is None or text_length > fallback[2]:
                fallback = (match, selector, text_length)

    body = soup.body or soup
    if fallback is not None:
        return fallback[0], fallback[1]
    return body, "body"


def first_heading_text(node: Any) -> str:
    for tag_name in ("h1", "h2"):
        heading = node.find(tag_name)
        if heading:
            text = heading.get_text(" ", strip=True)
            if text:
                return text
    return ""


def first_markdown_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def extract_markdown_title(markdown: str) -> str:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", markdown, flags=re.DOTALL)
    if not match:
        return ""
    frontmatter = match.group(1)
    title_match = re.search(r"^title:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    if not title_match:
        return ""
    return title_match.group(1).strip().strip('"').strip("'")


def strip_yaml_frontmatter(markdown: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n?", "", markdown, count=1, flags=re.DOTALL)


def localize_markdown_images(
    markdown: str,
    base_url: str,
    asset_dir: Path,
    timeout_secs: int,
) -> AssetLocalizationResult:
    downloads_by_url: dict[str, str] = {}
    downloaded_assets: list[dict[str, str]] = []
    failed_assets: list[str] = []
    used_names: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        raw_target = match.group("target")
        target = unwrap_markdown_target(raw_target)
        if target.startswith("data:") or target.startswith("cid:"):
            return match.group(0)

        absolute_url = urljoin(base_url, target)
        if absolute_url in downloads_by_url:
            local_target = downloads_by_url[absolute_url]
        else:
            try:
                local_path = download_binary_resource(absolute_url, asset_dir, timeout_secs, used_names)
            except RuntimeError:
                failed_assets.append(absolute_url)
                return match.group(0)

            local_target = f"{asset_dir.name}/{local_path.name}"
            downloads_by_url[absolute_url] = local_target
            downloaded_assets.append(
                {
                    "source_url": absolute_url,
                    "local_path": local_target,
                }
            )

        alt = match.group("alt")
        title = match.group("title")
        if title:
            return f'![{alt}]({local_target} "{title}")'
        return f"![{alt}]({local_target})"

    localized = IMAGE_MARKDOWN_PATTERN.sub(replace, markdown)
    return AssetLocalizationResult(
        markdown_body=localized,
        downloaded_assets=downloaded_assets,
        failed_assets=failed_assets,
    )


def unwrap_markdown_target(target: str) -> str:
    if target.startswith("<") and target.endswith(">"):
        return target[1:-1]
    return target


def download_binary_resource(
    url: str,
    asset_dir: Path,
    timeout_secs: int,
    used_names: set[str],
) -> Path:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=max(timeout_secs, 1)) as response:
            data = response.read()
            content_type = response.headers.get_content_type()
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Failed to download asset: {url}") from exc

    asset_dir.mkdir(parents=True, exist_ok=True)
    file_name = derive_asset_file_name(url, content_type, used_names)
    output_path = asset_dir / file_name
    output_path.write_bytes(data)
    return output_path


def derive_asset_file_name(url: str, content_type: str, used_names: set[str]) -> str:
    parsed = urlparse(url)
    raw_name = Path(unquote(parsed.path)).name
    stem = Path(raw_name).stem or "asset"
    suffix = Path(raw_name).suffix

    if not suffix and content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            suffix = guessed

    if not suffix:
        suffix = ".bin"

    safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-._") or "asset"
    safe_suffix = re.sub(r"[^a-zA-Z0-9.]+", "", suffix) or ".bin"
    candidate = f"{safe_stem}{safe_suffix}"
    index = 1
    while candidate in used_names:
        candidate = f"{safe_stem}-{index}{safe_suffix}"
        index += 1

    used_names.add(candidate)
    return candidate


def compact_markdown(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").splitlines()
    compacted: list[str] = []
    in_code_block = False
    blank_pending = False

    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            compacted.append(stripped)
            blank_pending = False
            continue

        if in_code_block:
            compacted.append(line.rstrip("\n"))
            continue

        normalized = re.sub(r"\s+", " ", stripped).strip()
        if normalized.lower() in LOW_VALUE_LINES:
            continue

        if not normalized:
            if compacted and not blank_pending:
                compacted.append("")
                blank_pending = True
            continue

        compacted.append(normalized)
        blank_pending = False

    while compacted and not compacted[-1].strip():
        compacted.pop()
    return "\n".join(compacted).strip() + "\n"


def write_outputs(
    out_dir: Path,
    slug: str,
    rendered: RenderedPage,
    extracted: ExtractedContent,
    timeout_secs: int,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = out_dir / f"{slug}.md"
    metadata_path = out_dir / f"{slug}.meta.json"
    asset_dir = out_dir / f"{slug}_assets"

    asset_result = localize_markdown_images(
        extracted.markdown_body,
        rendered.final_url,
        asset_dir,
        timeout_secs,
    )

    document = build_markdown_document(rendered, extracted, asset_result.markdown_body)
    metadata = {
        "source_url": rendered.source_url,
        "final_url": rendered.final_url,
        "title": extracted.title,
        "fetched_at_utc": rendered.fetched_at_utc,
        "profile": rendered.profile,
        "fetch_method": "playwright-html",
        "content_selector": extracted.content_selector,
        "content_text_length": extracted.content_text_length,
        "html_bytes": len(rendered.html.encode("utf-8")),
        "markdown_bytes": len(document.encode("utf-8")),
        "downloaded_assets": asset_result.downloaded_assets,
        "failed_assets": asset_result.failed_assets,
    }

    markdown_path.write_text(document, encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return markdown_path, metadata_path


def build_markdown_document(
    rendered: RenderedPage,
    extracted: ExtractedContent,
    markdown_body: str,
) -> str:
    frontmatter = {
        "source_url": rendered.source_url,
        "final_url": rendered.final_url,
        "title": extracted.title,
        "fetched_at_utc": rendered.fetched_at_utc,
        "profile": rendered.profile,
    }
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        escaped = str(value).replace('"', '\\"')
        frontmatter_lines.append(f'{key}: "{escaped}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append("")
    return "\n".join(frontmatter_lines) + markdown_body


def write_direct_outputs(
    out_dir: Path,
    slug: str,
    direct: DirectMarkdownPage,
    timeout_secs: int,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = out_dir / f"{slug}.md"
    metadata_path = out_dir / f"{slug}.meta.json"
    asset_dir = out_dir / f"{slug}_assets"
    asset_result = localize_markdown_images(
        direct.markdown_body,
        direct.source_asset_url,
        asset_dir,
        timeout_secs,
    )
    document = build_direct_markdown_document(direct, asset_result.markdown_body)
    metadata = {
        "source_url": direct.source_url,
        "final_url": direct.final_url,
        "title": direct.title,
        "fetched_at_utc": direct.fetched_at_utc,
        "profile": direct.profile,
        "fetch_method": direct.fetch_method,
        "source_asset_url": direct.source_asset_url,
        "content_selector": "asset:markdown",
        "content_text_length": len(direct.markdown_body),
        "markdown_bytes": len(document.encode("utf-8")),
        "downloaded_assets": asset_result.downloaded_assets,
        "failed_assets": asset_result.failed_assets,
    }
    markdown_path.write_text(document, encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return markdown_path, metadata_path


def build_direct_markdown_document(direct: DirectMarkdownPage, markdown_body: str) -> str:
    frontmatter = {
        "source_url": direct.source_url,
        "final_url": direct.final_url,
        "title": direct.title,
        "fetched_at_utc": direct.fetched_at_utc,
        "profile": direct.profile,
        "fetch_method": direct.fetch_method,
        "source_asset_url": direct.source_asset_url,
    }
    frontmatter_lines = ["---"]
    for key, value in frontmatter.items():
        escaped = str(value).replace('"', '\\"')
        frontmatter_lines.append(f'{key}: "{escaped}"')
    frontmatter_lines.append("---")
    frontmatter_lines.append("")
    return "\n".join(frontmatter_lines) + markdown_body


def capture_debug_artifacts(page: Any, debug_dir: Path, slug: str) -> None:
    debug_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = debug_dir / f"{slug}.png"
    html_path = debug_dir / f"{slug}.html"
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except Exception:
        pass
    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    debug_dir = Path(args.debug_dir).resolve() if args.debug_dir else out_dir / "_debug"
    index = load_snapshot_index(out_dir)
    profile = resolve_profile(args.url, args.profile)
    slug = slug_from_url(args.url)
    markdown_path = out_dir / f"{slug}.md"
    metadata_path = out_dir / f"{slug}.meta.json"
    metadata: dict[str, Any] | None = None
    cache_hit = False

    if not args.overwrite:
        cached = lookup_cached_snapshot(out_dir, index, args.url)
        if cached is None:
            cached = maybe_backfill_snapshot_index(out_dir, index, slug, args.url)
        if cached is not None:
            markdown_path, metadata_path, metadata = cached
            profile = str(metadata.get("profile", profile))
            cache_hit = True

    try:
        if not cache_hit:
            if profile == "genesys":
                direct = fetch_genesys_asset(args.url, args.timeout_secs)
                if direct is not None:
                    markdown_path, metadata_path = write_direct_outputs(
                        out_dir,
                        slug,
                        direct,
                        args.timeout_secs,
                    )
                    metadata = load_metadata_file(metadata_path)
                else:
                    rendered = render_page(args.url, profile, args.timeout_secs, debug_dir)
                    extracted = extract_document(rendered)
                    markdown_path, metadata_path = write_outputs(
                        out_dir,
                        slug,
                        rendered,
                        extracted,
                        args.timeout_secs,
                    )
                    metadata = load_metadata_file(metadata_path)
            else:
                rendered = render_page(args.url, profile, args.timeout_secs, debug_dir)
                extracted = extract_document(rendered)
                markdown_path, metadata_path = write_outputs(
                    out_dir,
                    slug,
                    rendered,
                    extracted,
                    args.timeout_secs,
                )
                metadata = load_metadata_file(metadata_path)

            if metadata is None:
                raise RuntimeError(f"Failed to read metadata after writing snapshot: {metadata_path}")
            update_snapshot_index(out_dir, index, markdown_path, metadata_path, metadata)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    summary = {
        "markdown_path": str(markdown_path),
        "metadata_path": str(metadata_path),
        "profile": profile,
        "cache_hit": cache_hit,
        "index_path": str(snapshot_index_path(out_dir)),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
