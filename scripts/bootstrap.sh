#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
md2wechat_version="${MD2WECHAT_VERSION:-v2.0.4}"
non_interactive=0
if [[ "${1:-}" == "--non-interactive" ]]; then
  non_interactive=1
fi

echo "[1/7] 检查 md2wechat CLI"
if ! command -v md2wechat >/dev/null 2>&1; then
  echo "将安装 md2wechat ${md2wechat_version}（第三方 GitHub Release）"
  curl -fsSL "https://github.com/geekjourneyx/md2wechat-skill/releases/download/${md2wechat_version}/install.sh" | bash
fi
export PATH="${HOME}/.local/bin:${PATH}"
md2wechat version --json

echo "[2/7] 安装匹配版本的上游 md2wechat Skill"
if command -v npx >/dev/null 2>&1; then
  npx --yes skills add "https://github.com/geekjourneyx/md2wechat-skill/tree/${md2wechat_version}" \
    --skill md2wechat --global --yes
else
  echo "未找到 npx，跳过可选的上游 Skill 安装。CLI 与 moonlit-wechat-publisher 仍可使用。"
  echo "如需安装上游 Skill，请先安装 Node.js：https://nodejs.org/"
fi

echo "[3/7] 初始化配置（已有配置不会覆盖）"
config_file="${HOME}/.config/md2wechat/config.yaml"
if [[ ! -f "$config_file" ]]; then
  md2wechat config init
else
  echo "保留已有配置：$config_file"
fi

echo "[4/7] 写入微信公众号凭据"
if [[ "$non_interactive" -eq 1 ]]; then
  if [[ -z "${WECHAT_APPID:-}" || -z "${WECHAT_SECRET:-}" ]]; then
    echo "--non-interactive 需要 WECHAT_APPID 和 WECHAT_SECRET 环境变量" >&2
    exit 2
  fi
fi
python3 "$script_dir/configure_wechat.py"
md2wechat config validate --json

echo "[5/7] 核对 CLI 能力"
md2wechat capabilities --json

echo "[6/7] 配置微信 IP 白名单"
public_ip="$(curl -4 -fsSL https://api.ipify.org || true)"
if [[ -n "$public_ip" ]]; then
  echo "当前执行机公网 IPv4：$public_ip"
else
  echo "未能自动取得公网 IPv4。请在实际运行发布命令的机器上查询出口 IP。"
fi
echo "登录 https://developers.weixin.qq.com/platform"
echo "选择公众号 → 开发接口管理 → IP 白名单 → 添加上面的公网 IP。"
echo "保存后等待 1–5 分钟。"
if [[ "$non_interactive" -eq 0 ]]; then
  read -r -p "完成白名单配置后按回车继续：" _
fi

echo "[7/7] 只读连通性验证"
python3 "$script_dir/preflight.py" --live

echo "Bootstrap 完成。正常发布不需要再次运行本脚本。"
