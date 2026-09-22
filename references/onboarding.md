# 首次接入 md2wechat

仅在 CLI 或有效微信配置缺失时读取。正常发布不运行 Bootstrap。

## 用户需要准备

- 已认证并具备开发接口权限的微信公众号。
- 管理员微信，可完成扫码验证。
- 实际执行发布命令的电脑或服务器。

## AppID 与 AppSecret

1. 打开 `https://developers.weixin.qq.com/platform`，由公众号管理员扫码登录。
2. 选择目标公众号，进入“开发接口管理”。后台文案可能调整，目标页面应能看到“开发者 ID（AppID）”“开发者密码（AppSecret）”和“IP 白名单”。
3. 复制 AppID。AppSecret 通常需要点击“重置”并完成管理员验证；重置后旧 Secret 立即失效。
4. 不要把 AppSecret 发到聊天、提交到 Git 或写进文章目录。若已经暴露，先在后台重置。

## Bootstrap

用户明确同意执行第三方安装脚本后运行：

```bash
bash scripts/bootstrap.sh
```

脚本只在首次接入时执行以下动作：

- 安装匹配版本的 `md2wechat` CLI 与上游 Skill。
- 将 `~/.local/bin` 加入当前进程 PATH。
- 只在配置文件不存在时运行 `md2wechat config init`，不会覆盖现有配置。
- 通过隐藏输入写入 AppSecret，并把配置权限设为 `600`。
- 显示当前公网 IPv4，等待用户配置白名单。
- 运行本地校验和只读的 live preflight；不会上传图片或创建草稿。

自动化环境可预先设置 `WECHAT_APPID`、`WECHAT_SECRET`，然后运行：

```bash
bash scripts/bootstrap.sh --non-interactive
```

## IP 白名单

白名单必须填写“真正发起微信 API 请求的机器”的公网 IPv4。本地电脑、云服务器和 CI 的出口 IP 可能不同。

Bootstrap 会尝试运行：

```bash
curl -4 -fsSL https://api.ipify.org
```

把输出加入微信开发接口管理页的“IP 白名单”，保存后等待 1–5 分钟，再运行：

```bash
python3 scripts/preflight.py --live
```

家庭宽带、公司网络和部分 CI 的公网 IP 会变化。出现 `40164 invalid ip ... not in whitelist` 时，以报错中的 IP 为准更新白名单。

## 最小验证

```bash
md2wechat version --json
md2wechat config validate --json
md2wechat capabilities --json
python3 scripts/preflight.py --live
```

`config validate` 返回成功不代表占位凭据可用；只有 live preflight 成功，才说明 AppID、AppSecret 与当前出口 IP 可以取得 access token。

