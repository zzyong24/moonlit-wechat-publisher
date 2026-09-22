#!/usr/bin/env python3
"""Validate local WeChat credentials and optionally test token access without exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_CONFIG = Path.home() / ".config" / "md2wechat" / "config.yaml"


def _unquote(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def read_simple_yaml(config_path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    section: str | None = None
    if not config_path.is_file():
        return result
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(?:#.*)?$", raw_line)
        if top:
            section = top.group(1)
            result.setdefault(section, {})
            continue
        nested = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*?)\s*$", raw_line)
        if section and nested:
            value = re.sub(r"\s+#.*$", "", nested.group(2)).strip()
            result[section][nested.group(1)] = _unquote(value)
    return result


def load_credentials(config_path: Path = DEFAULT_CONFIG) -> tuple[str, str, str]:
    config = read_simple_yaml(config_path)
    appid = os.environ.get("WECHAT_APPID") or config.get("wechat", {}).get("appid", "")
    secret = os.environ.get("WECHAT_SECRET") or config.get("wechat", {}).get("secret", "")
    source = "environment" if os.environ.get("WECHAT_APPID") or os.environ.get("WECHAT_SECRET") else str(config_path)
    return appid.strip(), secret.strip(), source


def is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return not value or lowered.startswith("your_") or "changeme" in lowered or "example" in lowered or "你的" in value


def local_check(config_path: Path = DEFAULT_CONFIG) -> dict:
    appid, secret, source = load_credentials(config_path)
    errors: list[str] = []
    if is_placeholder(appid):
        errors.append("wechat.appid is missing or still a placeholder")
    elif not re.fullmatch(r"wx[0-9A-Za-z]{16}", appid):
        errors.append("wechat.appid should match wx + 16 characters")
    if is_placeholder(secret):
        errors.append("wechat.secret is missing or still a placeholder")
    elif len(secret) < 24:
        errors.append("wechat.secret is unexpectedly short")
    return {
        "success": not errors,
        "stage": "local",
        "source": source,
        "appid_masked": f"{appid[:4]}***{appid[-4:]}" if len(appid) >= 8 else "",
        "secret_configured": bool(secret) and not is_placeholder(secret),
        "errors": errors,
    }


def live_check(config_path: Path = DEFAULT_CONFIG, timeout: int = 15) -> dict:
    local = local_check(config_path)
    if not local["success"]:
        return local
    appid, secret, source = load_credentials(config_path)
    query = urlencode({"grant_type": "client_credential", "appid": appid, "secret": secret})
    url = f"https://api.weixin.qq.com/cgi-bin/token?{query}"
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        return {"success": False, "stage": "network", "source": source, "error": str(error)}
    if payload.get("access_token"):
        return {
            "success": True,
            "stage": "live",
            "source": source,
            "appid_masked": local["appid_masked"],
            "credentials_valid": True,
            "ip_whitelist_valid": True,
        }
    errmsg = str(payload.get("errmsg", "unknown WeChat error"))
    ip_match = re.search(r"invalid ip\s+([0-9a-fA-F:.]+)", errmsg)
    result = {
        "success": False,
        "stage": "live",
        "source": source,
        "errcode": payload.get("errcode"),
        "errmsg": errmsg,
    }
    if ip_match:
        result["public_ip"] = ip_match.group(1)
        result["fix"] = "Add this IP to WeChat developer platform > 开发接口管理 > IP 白名单, wait 1–5 minutes, then retry."
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--live", action="store_true", help="Call the read-only WeChat token endpoint")
    args = parser.parse_args()
    result = live_check(args.config) if args.live else local_check(args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
