#!/usr/bin/env python3
"""Validate that a Moonlit article contains semantic personal-brand visuals."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse


MARKDOWN_IMAGE_RE = re.compile(r"!\[[^]]*]\(([^)]+)\)")
REQUIRED_IP_MARKERS = {"moonlit-astronaut", "green-crescent-visor"}


class VisualCheckError(RuntimeError):
    pass


def resolve_reference(reference: str, base: Path) -> str:
    value = html.unescape(reference.strip()).split(maxsplit=1)[0].strip("<>")
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("file://"):
        return str(Path(unquote(urlparse(value).path)).resolve())
    return str((base / value).resolve())


def check_visual_manifest(markdown: Path, manifest: Path, min_brand_ai: int = 2) -> dict:
    markdown = markdown.resolve()
    manifest = manifest.resolve()
    if not markdown.is_file():
        raise VisualCheckError(f"文章不存在：{markdown}")
    if not manifest.is_file():
        raise VisualCheckError(
            f"缺少品牌配图清单：{manifest}。先生成正文场景图并创建 assets/visual-manifest.json。"
        )

    source = markdown.read_text(encoding="utf-8")
    references = [resolve_reference(item, markdown.parent) for item in MARKDOWN_IMAGE_RE.findall(source)]
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise VisualCheckError(f"品牌配图清单不是有效 JSON：{error}") from error

    if payload.get("brand") != "月明水清深":
        raise VisualCheckError("visual-manifest.json 的 brand 必须是“月明水清深”")
    images = payload.get("images")
    if not isinstance(images, list):
        raise VisualCheckError("visual-manifest.json 缺少 images 数组")

    registered = []
    for entry in images:
        if not isinstance(entry, dict) or not entry.get("path"):
            raise VisualCheckError("配图清单中的每一项都必须包含 path")
        resolved = resolve_reference(str(entry["path"]), markdown.parent)
        item = dict(entry)
        item["resolved_path"] = resolved
        registered.append(item)

    registered_paths = {item["resolved_path"] for item in registered}
    unregistered = [reference for reference in references if reference not in registered_paths]
    if unregistered:
        raise VisualCheckError("文章存在未登记配图：" + "；".join(unregistered))

    brand_images = []
    for item in registered:
        if item.get("type") != "brand-ai" or item["resolved_path"] not in references:
            continue
        meaning = str(item.get("meaning") or "").strip()
        markers = set(item.get("ip_markers") or [])
        if len(meaning) < 8:
            raise VisualCheckError(f"品牌正文图缺少明确的内容作用：{item['path']}")
        if not REQUIRED_IP_MARKERS.issubset(markers):
            raise VisualCheckError(
                f"品牌正文图缺少固定 IP 标志 moonlit-astronaut / green-crescent-visor：{item['path']}"
            )
        local_path = Path(item["resolved_path"])
        if not local_path.is_file():
            raise VisualCheckError(f"品牌正文图文件不存在：{local_path}")
        brand_images.append(item)

    if len(brand_images) < min_brand_ai:
        raise VisualCheckError(
            f"公众号正文至少需要 {min_brand_ai} 张品牌 IP 场景图；当前只有 {len(brand_images)} 张。"
            "产品截图、封面和装饰图不计入。"
        )

    return {
        "success": True,
        "brand": payload["brand"],
        "article_image_count": len(references),
        "brand_ai_count": len(brand_images),
        "minimum_brand_ai": min_brand_ai,
        "manifest": str(manifest),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--min-brand-ai", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = check_visual_manifest(args.markdown, args.manifest, args.min_brand_ai)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
