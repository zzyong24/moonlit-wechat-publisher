#!/usr/bin/env python3
"""Safely write WeChat AppID and AppSecret into md2wechat config."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import sys
import tempfile


DEFAULT_CONFIG = Path.home() / ".config" / "md2wechat" / "config.yaml"


def validate(appid: str, secret: str) -> None:
    if not re.fullmatch(r"wx[0-9A-Za-z]{16}", appid):
        raise ValueError("AppID should match wx + 16 characters")
    if len(secret) < 24 or secret.lower().startswith("your_"):
        raise ValueError("AppSecret is missing, still a placeholder, or unexpectedly short")


def update_wechat_section(content: str, appid: str, secret: str) -> str:
    lines = content.splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"^wechat:\s*(?:#.*)?$", line)), None)
    replacement = [f"  appid: {json.dumps(appid)}", f"  secret: {json.dumps(secret)}"]
    if start is None:
        prefix = lines + ([""] if lines and lines[-1].strip() else [])
        return "\n".join(prefix + ["wechat:", *replacement]) + "\n"
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index] and not lines[index][0].isspace() and re.match(r"^[A-Za-z0-9_-]+:", lines[index]):
            end = index
            break
    section = lines[start + 1 : end]
    kept = [line for line in section if not re.match(r"^\s+(appid|secret):", line)]
    new_lines = lines[: start + 1] + replacement + kept + lines[end:]
    return "\n".join(new_lines) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix="config.", suffix=".yaml", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--appid", help="Prefer WECHAT_APPID for non-interactive use")
    parser.add_argument("--secret-stdin", action="store_true", help="Read AppSecret from stdin without echo")
    args = parser.parse_args()
    appid = args.appid or os.environ.get("WECHAT_APPID")
    if not appid:
        appid = input("WECHAT APPID: ").strip()
    secret = os.environ.get("WECHAT_SECRET")
    if args.secret_stdin:
        secret = sys.stdin.readline().rstrip("\r\n")
    elif not secret:
        secret = getpass.getpass("WECHAT APPSECRET（输入不会显示）: ").strip()
    try:
        validate(appid, secret or "")
        existing = args.config.read_text(encoding="utf-8") if args.config.is_file() else ""
        atomic_write(args.config, update_wechat_section(existing, appid, secret or ""))
        print(
            json.dumps(
                {
                    "success": True,
                    "config": str(args.config),
                    "appid_masked": f"{appid[:4]}***{appid[-4:]}",
                    "secret_configured": True,
                    "mode": "0600",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
