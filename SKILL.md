---
name: moonlit-wechat-publisher
description: Use when a user wants to format a Markdown or HTML article in the 月明水清深 WeChat style, turn short video evidence into an article GIF, upload article images, create or verify a WeChat Official Account draft, or needs first-use md2wechat installation, AppID/AppSecret, and IP-whitelist guidance.
metadata:
  display_name: 月明·公众号草稿发布
  version: "1.2.0"
  updated: "2026-09-06"
---

# 月明·公众号草稿发布

把已确认的公众号文章排成月明品牌 HTML，并安全写入微信公众号草稿箱。核心边界：排版与预检可以本地执行；上传图片、创建或更新草稿必须获得用户对本次操作的明确授权。

## 路由

- 正常发布：`md2wechat` 已安装，凭据与白名单可用。不要运行 Bootstrap。
- 首次接入：缺少 CLI、配置文件、有效凭据，或出现 `40164`。先读 [references/onboarding.md](references/onboarding.md)，用户同意安装后才运行 `scripts/bootstrap.sh`。
- 只看样式：只运行 `scripts/publish.py --dry-run`，不访问微信接口。
- 录屏嵌入正文：选取能证明一个动作或结果的短片段，用 `scripts/video_to_gif.py` 转为体积受控的 GIF，再像普通图片一样插入 Markdown。不要把整段视频机械转成 GIF。
- 用户明确要求 AI 模式：先运行 `md2wechat convert ... --mode ai --json`。`action_required` 表示只生成了 AI 请求，不是 HTML 已完成；宿主 AI 生成 HTML 后，再用 `scripts/publish.py --html ...` 发布。

## 正常流程

1. 确认 Markdown、封面、标题、作者和摘要。发布前文章应已完成用户确认及 `moonlit-de-ai-perception` 检查；不要在发布阶段擅自改写正文。
2. 阅读 [references/brand-image-spec.md](references/brand-image-spec.md)。品牌长文默认检查 2 张有内容职责的 IP 场景图；若已确认方向是纯证据图或更少插图，按该方向调整最低数量，不在发布阶段补造图片。产品截图、封面和装饰图不计入品牌图数量。把全部图片登记到 `assets/visual-manifest.json`，先运行硬检查：

   ```bash
   python3 scripts/check_visuals.py \
     --markdown /abs/article.md \
     --manifest /abs/assets/visual-manifest.json \
     --min-brand-ai 2
   ```

   若原始证据是视频，先截取 3–8 秒的单一动作片段并转换：

   ```bash
   python3 scripts/video_to_gif.py /abs/source.mov /abs/assets/demo.gif \
     --start 12 --duration 6 --width 720 --fps 10 --max-bytes 5000000
   ```

   转换脚本会逐级降低帧率、色彩和宽度，直到文件小于体积上限；无法达标时直接失败，不输出超限文件。GIF 必须登记到 `visual-manifest.json`，其内容职责写成“证明某个动作或交互”，不能算作品牌 IP 场景图。

3. 阅读 [references/style-spec.md](references/style-spec.md)，保持源 Markdown 只读，在独立输出目录生成预览。默认使用 `compact` 顶部标识，避免与微信公众号原生标题重复；只有用户明确要求旧版深色题头时才传 `--hero-style dark`：

   ```bash
   python3 scripts/publish.py \
     --markdown /abs/article.md \
     --cover /abs/cover.png \
     --out-dir /abs/wechat-draft \
     --dry-run
   ```

4. 检查预览 HTML、标题长度（≤32）、摘要长度（≤128）、图片数量和封面。用户明确授权写入草稿箱后执行：

   ```bash
   python3 scripts/publish.py \
     --markdown /abs/article.md \
     --cover /abs/cover.png \
     --out-dir /abs/wechat-draft \
     --publish
   ```

5. 报告草稿 `media_id`、HTML、草稿 JSON 和结果清单路径。明确说明“写入草稿箱”不等于群发。

已有品牌 HTML 时，改用 `--html`，并显式提供 `--title`。常用个性化参数用 `--kicker`、`--hero`、`--strapline`、`--author`、`--digest`；运行 `--help` 查看完整参数。

## 共享资产交接

接收写作 Skill 已确定的图片与使用顺序。文章 assets/visual-manifest.json 从作品 production/illustrations/visual-manifest.json 导出，保留 asset_id、revision、sha256，path 按现有检查器相对文章目录解析。发布器只核验和转换平台所需格式，不生成或重画正文图；缺图回配图 Skill。线稿宇航员图只要符合身份与内容职责即可，不强制写实光影或发光灯带。

## 品牌样式不变量

- 白底正文；深炭黑 `#121815` 建立章节锚点；亮绿 `#b7ef3f` 只用于结构、结论和少量识别线。
- 默认使用轻量顶部品牌线，不在正文重复微信原生标题；章节使用 `SECTION 01` 编号；正文图片默认不显示编号或技术化图注，只有图片 alt 以 `图注：` 开头时才显示自然图注。
- 不使用整页护眼绿、渐变、阴影、外链 CSS、`<style>` 或 `<script>`。
- 视觉样式必须对应内容语义：`**普通强调**` 保持深色，`==关键结果==` 使用品牌绿虚线强调；不要用颜色代替论证。
- 每篇最多使用 3 个重点模块，且最多一个 `[!VERDICT]`。Markdown 可用 `> [!KEY]`、`> [!NOTE]`、`> [!VERDICT]`、`> [!QUESTION]`、`> [!COMPARE] 左 || 右`。
- `[!KEY]` 是不带卡片的核心金句；`[!NOTE]` 是浅色解释框；深色 `[!VERDICT]` 只用于全文最终结论。每个章节最多 2 处 `==关键结果==`。
- 品牌图最低数量沿用上游已确认方向，通过 check_visuals.py 的 --min-brand-ai 和 publish.py 的 --min-brand-images 传入同一值；纯证据图方向可以为 0。固定角色为月明宇航员，保留其身份标志；线稿不用发光灯带。
- 品牌场景图必须推进理解；产品截图只算证据图，不能用截图凑足品牌配图数量。
- 发布前必须通过 `visual-manifest.json` 检查；缺清单、缺固定 IP 标记或未达到本次已选定配图要求时停止发布。

## 首次接入与故障

- Bootstrap 只用于首次安装或修复配置，不得由正常发布脚本自动调用。
- `config validate` 只能证明 YAML 可读取；`scripts/preflight.py --live` 才会检查占位值、凭据与白名单。
- `40164`：从错误中提取公网 IP，引导用户在实际发请求的机器对应的微信开发接口管理页加入白名单，等待 1–5 分钟后重试。
- `40001` / `42001`：检查 AppID、AppSecret；重置 Secret 后同步更新本机配置。
- 不把 AppSecret、access token 或完整配置写入日志、产物、Git 或聊天回复。
- 正文图片只上传一次；封面与正文图片是同一文件时复用其 `media_id`。
- GIF 应短、静音、可循环，并只承担一个证据任务。默认优先 3–8 秒、宽度不超过 720px、10fps、5MB 硬上限；文字可读性不足时缩短片段，不通过无限降画质换体积。
- 默认创建新草稿。更新已有草稿需要用户明确指定目标 `media_id`，先回读验证目标；失效的 `media_id` 不要猜测或循环重试。
