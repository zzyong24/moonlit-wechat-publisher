#!/usr/bin/env python3
"""Render and optionally publish a Moonlit-styled article to WeChat drafts."""

from __future__ import annotations

import argparse
from datetime import datetime
import html as html_module
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlparse

from check_visuals import check_visual_manifest
from preflight import DEFAULT_CONFIG, local_check
from render_wechat import extract_title, render_markdown


IMAGE_SRC_RE = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.I)


class PublishError(RuntimeError):
    pass


def plain_digest(markdown: str, limit: int = 120) -> str:
    text = re.sub(r"^---[\s\S]*?^---\s*", "", markdown, count=1, flags=re.M)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"!\[[^]]*]\([^)]+\)", "", text)
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def parse_cli_json(stdout: str) -> dict:
    value = stdout.strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(value):
            if char != "{":
                continue
            try:
                payload, end = decoder.raw_decode(value[index:])
                if not value[index + end :].strip():
                    return payload
            except json.JSONDecodeError:
                continue
    raise PublishError("md2wechat did not return valid JSON")


def run_md2wechat(arguments: list[str]) -> dict:
    process = subprocess.run(
        ["md2wechat", *arguments, "--json"],
        text=True,
        capture_output=True,
    )
    combined = "\n".join(part for part in [process.stdout, process.stderr] if part).strip()
    try:
        payload = parse_cli_json(process.stdout)
    except PublishError:
        raise PublishError(combined or f"md2wechat exited with {process.returncode}")
    if process.returncode != 0 or not payload.get("success", False):
        message = str(payload.get("error") or payload.get("message") or combined)
        if "40164" in message or "not in whitelist" in message:
            match = re.search(r"invalid ip\s+([0-9a-fA-F:.]+)", message)
            ip = match.group(1) if match else "<微信错误中显示的 IP>"
            raise PublishError(
                f"微信 IP 白名单未生效（40164）。把 {ip} 加入微信开发接口管理页的 IP 白名单，等待 1–5 分钟后重试。"
            )
        raise PublishError(message)
    return payload


def resolve_image(source: str, base: Path) -> tuple[str, Path | None]:
    if source.startswith(("http://", "https://")):
        return "remote", None
    if source.startswith("file://"):
        return "local", Path(unquote(urlparse(source).path)).resolve()
    return "local", (base / html_module.unescape(source)).resolve()


def upload_source(source: str, base: Path) -> tuple[str, str, str | None]:
    kind, local_path = resolve_image(source, base)
    if kind == "remote":
        if "mmbiz.qpic.cn" in source:
            return source, "", None
        response = run_md2wechat(["download_and_upload", source])
        cache_key = source
    else:
        if not local_path or not local_path.is_file():
            raise PublishError(f"local image not found: {local_path}")
        response = run_md2wechat(["upload_image", str(local_path)])
        cache_key = str(local_path)
    data = response.get("data") or {}
    wechat_url = data.get("wechat_url")
    media_id = data.get("media_id") or ""
    if not wechat_url:
        raise PublishError(f"image upload returned no wechat_url: {source}")
    return str(wechat_url), str(media_id), cache_key


def upload_html_images(content: str, base: Path) -> tuple[str, dict[str, dict], int]:
    uploaded: dict[str, dict] = {}
    replaced = 0

    def replace(match: re.Match) -> str:
        nonlocal replaced
        source = html_module.unescape(match.group(2))
        if "mmbiz.qpic.cn" in source:
            return match.group(0)
        kind, local_path = resolve_image(source, base)
        key = source if kind == "remote" else str(local_path)
        if key not in uploaded:
            wechat_url, media_id, _ = upload_source(source, base)
            uploaded[key] = {"wechat_url": wechat_url, "media_id": media_id}
        replaced += 1
        return f'{match.group(1)}{uploaded[key]["wechat_url"]}{match.group(3)}'

    return IMAGE_SRC_RE.sub(replace, content), uploaded, replaced


def absolutize_local_images(content: str, base: Path) -> str:
    def replace(match: re.Match) -> str:
        source = html_module.unescape(match.group(2))
        if source.startswith(("http://", "https://", "file://")):
            return match.group(0)
        absolute = (base / source).resolve()
        return f'{match.group(1)}{absolute.as_uri()}{match.group(3)}'

    return IMAGE_SRC_RE.sub(replace, content)


def localize_browser_images(content: str, asset_base: Path, browser_base: Path) -> str:
    def replace(match: re.Match) -> str:
        source = html_module.unescape(match.group(2))
        if source.startswith(("http://", "https://")):
            return match.group(0)
        if source.startswith("file://"):
            local_path = Path(unquote(urlparse(source).path))
        else:
            local_path = asset_base / source
        relative = os.path.relpath(local_path.absolute(), browser_base.absolute())
        return f'{match.group(1)}{html_module.escape(relative, quote=True)}{match.group(3)}'

    return IMAGE_SRC_RE.sub(replace, content)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def browser_document(fragment: str, title: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html_module.escape(title)}</title></head>"
        '<body style="margin: 0 auto; max-width: 677px; background: #ffffff;">'
        f"{fragment}</body></html>\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--markdown", type=Path)
    source.add_argument("--html", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Render only; no WeChat calls")
    mode.add_argument("--publish", action="store_true", help="Upload images and create a new WeChat draft")
    parser.add_argument("--cover", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--title")
    parser.add_argument("--author", default="月明水清深")
    parser.add_argument("--digest")
    parser.add_argument("--kicker", default="MOONLIT / FIELD NOTES")
    parser.add_argument("--hero")
    parser.add_argument("--strapline")
    parser.add_argument(
        "--hero-style",
        choices=("compact", "dark", "none"),
        default="compact",
        help="compact avoids repeating the WeChat native title; dark keeps the legacy title card",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--visual-manifest",
        type=Path,
        help="Brand-image manifest; defaults to <article-dir>/assets/visual-manifest.json for Markdown",
    )
    parser.add_argument("--min-brand-images", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        source_path = (args.markdown or args.html).resolve()
        cover = args.cover.resolve()
        if not source_path.is_file():
            raise PublishError(f"source file not found: {source_path}")
        if not cover.is_file():
            raise PublishError(f"cover image not found: {cover}")
        args.out_dir.mkdir(parents=True, exist_ok=True)

        if args.markdown:
            markdown = source_path.read_text(encoding="utf-8")
            visual_manifest = args.visual_manifest or source_path.parent / "assets" / "visual-manifest.json"
            visual_check = check_visual_manifest(source_path, visual_manifest, args.min_brand_images)
            title = args.title or extract_title(markdown)
            content, render_meta = render_markdown(
                markdown,
                args.kicker,
                args.hero,
                args.strapline,
                args.hero_style,
            )
            digest = args.digest or plain_digest(markdown)
            asset_base = source_path.parent
        else:
            if not args.title:
                raise PublishError("--title is required with --html")
            title = args.title
            content = source_path.read_text(encoding="utf-8")
            digest = args.digest or ""
            render_meta = {"headings": len(re.findall(r"<h2\b", content, re.I)), "images": len(IMAGE_SRC_RE.findall(content))}
            asset_base = source_path.parent
            visual_check = {
                "success": True,
                "status": "not_checked_for_html_source",
                "note": "HTML 直发前应由其源 Markdown 通过品牌配图检查",
            }

        browser_source_content = content
        content = absolutize_local_images(content, asset_base)

        if not title:
            raise PublishError("article title is missing; add an H1 or pass --title")
        if len(title) > 32:
            raise PublishError(f"title has {len(title)} characters; WeChat limit is 32. Pass a shorter --title.")
        if len(args.author) > 16:
            raise PublishError(f"author has {len(args.author)} characters; WeChat limit is 16")
        if len(digest) > 128:
            raise PublishError(f"digest has {len(digest)} characters; WeChat limit is 128")
        if re.search(r"<(style|script)\b", content, re.I):
            raise PublishError("HTML contains <style> or <script>; WeChat output must use safe inline styles")

        preview_file = args.out_dir / "article.preview.html"
        preview_file.write_text(content, encoding="utf-8")
        browser_preview_file = args.out_dir / "article.browser.html"
        browser_content = localize_browser_images(browser_source_content, asset_base, args.out_dir)
        browser_preview_file.write_text(browser_document(browser_content, title), encoding="utf-8")
        if args.dry_run:
            result = {
                "success": True,
                "status": "ready",
                "remote_effects": False,
                "title": title,
                "digest_length": len(digest),
                "preview_html": str(preview_file),
                "browser_preview_html": str(browser_preview_file),
                "image_count": len(IMAGE_SRC_RE.findall(content)),
                "render": render_meta,
                "brand_visuals": visual_check,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if not shutil.which("md2wechat"):
            raise PublishError("md2wechat is not installed. Run scripts/bootstrap.sh after user approval.")
        credential_check = local_check(args.config)
        if not credential_check["success"]:
            raise PublishError("; ".join(credential_check["errors"]) + ". Run scripts/bootstrap.sh for first-use setup.")

        wechat_html, uploaded, replaced = upload_html_images(content, asset_base)
        cover_key = str(cover)
        cover_upload = uploaded.get(cover_key)
        if cover_upload and cover_upload.get("media_id"):
            cover_media_id = cover_upload["media_id"]
            cover_reused = True
        else:
            cover_url, cover_media_id, _ = upload_source(str(cover), Path("/"))
            del cover_url
            cover_reused = False
        if not cover_media_id:
            raise PublishError("cover upload returned no media_id")

        wechat_file = args.out_dir / "article.wechat.html"
        wechat_file.write_text(wechat_html, encoding="utf-8")
        draft = {
            "articles": [
                {
                    "title": title,
                    "author": args.author,
                    "digest": digest,
                    "content": wechat_html,
                    "thumb_media_id": cover_media_id,
                    "show_cover_pic": 0,
                }
            ]
        }
        draft_file = args.out_dir / "draft.json"
        write_json(draft_file, draft)
        response = run_md2wechat(["create_draft", str(draft_file)])
        media_id = str((response.get("data") or {}).get("media_id") or "")
        if not media_id:
            raise PublishError("draft creation returned no media_id")
        result = {
            "success": True,
            "status": "published_to_draft",
            "remote_effects": True,
            "created_at": datetime.now().astimezone().isoformat(),
            "media_id": media_id,
            "title": title,
            "preview_html": str(preview_file),
            "browser_preview_html": str(browser_preview_file),
            "wechat_html": str(wechat_file),
            "draft_json": str(draft_file),
            "uploaded_image_count": len(uploaded),
            "replaced_image_count": replaced,
            "cover_reused_from_body": cover_reused,
            "brand_visuals": visual_check,
        }
        result_file = args.out_dir / "publish-result.json"
        write_json(result_file, result)
        result["result_file"] = str(result_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"success": False, "status": "failed", "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
