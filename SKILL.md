---
name: moonlit-wechat-publisher
description: "Use when a user wants to format a Markdown or HTML article in the 月明水清深 WeChat style as a local HTML preview, check article visuals, or turn short video evidence into an article GIF（用户说“公众号排版”“排好版后检查配图和格式”“出公众号预览”“上传到公众号草稿箱”时使用）。A 段本地排版预览和预检；B 段上传图片、创建公众号后台草稿只在月明看过这一篇的预览并逐篇批准后执行（--approval 必须含本篇标题），上传后回报链接。不用于写稿、改稿或群发。"
metadata:
  display_name: 月明·公众号草稿发布
  version: "1.7.0"
  updated: "2026-10-21"
---

# 月明·公众号草稿发布

**三审必读（文案确认即触发）**：文案确认后按当前激活 `moonlit-content-engine/references/publish-review.md` 实际执行guoshen的script文本审核，不强审初稿、不等成片；音画/封面/平台设置明确未审。上传前content审完整实际包并验证script；草稿上传后final审原生设置和封面实际呈现并验证前两阶段。文案改变使相关旧证据失效；每阶段不能替代后续审核、用户授权或平台裁决。旧v1回执须实际补审，不静默升级；调用门禁必须带 `--require-chain-version 2`。


把已确认的公众号文章排成月明品牌 HTML 预览，并做配图与格式预检。本 Skill 拆成两段：

| 段 | 做什么 | 谁来跑 |
|---|---|---|
| **A 本地排版预览** | `check_visuals.py`、`video_to_gif.py`、`render_wechat.py`、`publish.py --dry-run`；产出 HTML 预览、图片清单、手机宽度截图 | 团队 Bot（国内运营专家）可以跑，不联网、不碰微信接口 |
| **B 上传到公众号后台** | `publish.py --publish`、`bootstrap.sh`、`configure_wechat.py`、`preflight.py --live` | 在持有公众号凭据且 IP 已加白名单的环境执行（目前是月明 Mac）；**每篇都要月明看过 A 段预览并明确批准**，脚本要求 `--approval "<批准记录，含本篇标题>"`，批准不能复用；上传后回报草稿/文章链接 |

**发布键在月明（团队规则 2026-10-21，优先于本文其他条款）**：本 Skill 自己不发布。成品先给月明看最终预览；月明对**这一条**明确批准后，才交给发布工具（moonlit-video-publisher / moonlit-social-publisher / 公众号上传段）发布；以前的批准、其他作品或其他平台的批准都不能复用。发布后把链接报给月明。

**凭据规则**：AppID/AppSecret 存在团队凭据库（Bitwarden），只在运行 B 段时用环境变量 `WECHAT_APPID` / `WECHAT_SECRET` 临时注入；不写进文件、日志、产物、Git 或聊天。Bot 不把 AppSecret 写进任何文件或消息。

B 段的完整步骤、API 核验与故障处理见 [B 段：审核通过后上传](references/upload-on-mac.md)。

## 发布前必需审核

A 段交接前，读取 [发布前审核合同](references/publish-review.md)（随包副本，源自 moonlit-content-engine），并实际运行依赖 `guoshen`。通读正文或独立语音/字幕及全画面，审核目标平台的当前规则、封面、渠道文案和发布设置；完成上传前内容报告与版本绑定回执，通过content门禁才上传未发布草稿；实际原生设置与裁切在草稿中核对，final门禁通过才进入READY或最终提交。API草稿成功仅证明入草稿，不冒充原生AI声明、所有封面裁切或群发已完成。修复、换平台、文案/媒体/设置变化后重审；审核缺失、未完成或不通过不能继续外发。手工浏览器路径、续发、恢复和直接CLI也遵守同一门禁；本地排版/只读检查可先执行。上游不支持的公众号、X等按合同补充对应平台审核，不能套用视频号结论。

执行发布命令前，按激活目录设置 `MOONLIT_GUOSHEN_GATE`、`MOONLIT_GUOSHEN_DIR`、`MOONLIT_GUOSHEN_RECEIPT`。共享门禁只验证回执，不能替代实际语义审核；通过也不代替本次发布授权。

## 路由

- 团队 Bot 的默认路线：A 段，只运行 `scripts/publish.py --dry-run`，不访问微信接口；交付 HTML 预览和交接清单给月明。
- 月明要上传：把 A 段产物和 [B 段说明](references/upload-on-mac.md) 交给月明，由他在 Mac 上执行。
- 首次接入（只在月明 Mac）：缺少 CLI、配置文件、有效凭据，或出现 `40164`。先读 [references/onboarding.md](references/onboarding.md)，月明同意安装后才运行 `scripts/bootstrap.sh`。
- 录屏嵌入正文：选取能证明一个动作或结果的短片段，用 `scripts/video_to_gif.py` 转为体积受控的 GIF，再像普通图片一样插入 Markdown。不要把整段视频机械转成 GIF。
- 用户明确要求 AI 模式：先运行 `md2wechat convert ... --mode ai --json`。`action_required` 表示只生成了 AI 请求，不是 HTML 已完成；宿主 AI 生成 HTML 后，再用 `scripts/publish.py --html ... --dry-run` 出预览。

## 正常流程

1. 确认 Markdown、封面、标题、作者和摘要。发布前文章应已完成用户确认及 `moonlit-de-ai-perception` 检查；不要在发布阶段擅自改写正文。
   - 按实际展示范围判断采用：`article.browser.html` 是正文预览，默认不包含封面。用户指定该预览准备发布，可以采用对应正文，不能据此把封面清单里的 `pending` 改成已确认。先读当前封面记录和实际图，展示/确认本期封面及其入口；确认品牌语言、人物原图或其他平台封面，不等于确认新生成的公众号横幅。已明确展示并被本次发布指令采用的完整包无需逐项重复确认。
   - 封面和正文图先遵守当前工程 AGENTS、已确认品牌规范及本期明确方向，不由发布器固定切回宇航员。**微信公众号文章封面不使用作者真人照片或真人 IP**；用与文章命题相关的关系图、证据素材或产品画面承载主题。视频封面的真人品牌规则不套用到公众号文章封面。复用已确认素材，公众号封面按入口重新排版；不要直接裁切复用视频封面，也不在发布阶段重画正文图。
   - 公众号消息列表封面按 **2.35:1** 制作；使用横向构图为文章标题及主题关系图、证据或概念视觉留出清晰空间，不沿用视频封面的 4:3 或 3:4 画幅。其他公众号入口如有不同规格，按对应入口重新排版并记录尺寸依据。
   - 先从文章的核心命题、论点和证据中提炼一个与主题紧密相关、缩略图也能辨认的视觉概念，再决定主视觉与标题如何配合。封面应有完整的编辑设计：清楚的视觉主次、字体层级、留白、构图和材质语言；不能只做到“没有真人”或“没有霓虹”就算完成。
   - 对个人 AI、数据主权、个人上下文等观念型文章，使用有审美的编辑式视觉隐喻或经过设计的概念画面，让读者看出文章具体在谈什么；可以用生活上下文、个人记忆与 AI 的关系作为视觉线索。避免廉价流程图、临时拼贴、私人手账/旅行相册感和与命题脱节的装饰性抽象图；只有文章核心本身是机制或流程时，才把关系图作为封面主视觉。
   - 允许用准确排版的简洁大字号中文标题或标签，标题须明确点出主题（如 Personal AI）及文章问题；不让图像模型生成文字，不放小字或密集说明。封面要直观、大气，同时保留高级、克制的审美；避免浓重 AI 科技风、脱离生活的抽象网络、粒子或全息界面。
2. 阅读 [references/brand-image-spec.md](references/brand-image-spec.md)。未另定方向的宇航员长文模板检查 2 张有内容职责的 IP 场景图；已确认其他人物风格、纯证据图或更少插图时，在发布包记录真实素材类型、方向依据和最低数量，两处检查参数保持一致。非宇航员解释图不伪造固定 IP 标志，可以按本期已确认方向将最低品牌图数量设为 0；这不免除全图登记、源文件与实际上传检查，也不能用来掩盖缺图。发布器不补造图片。产品截图、封面和装饰图不计入品牌图数量。把全部图片登记到 `<文章目录>/assets/visual-manifest.json`（运行时产物），先运行硬检查：

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

4. 检查预览 HTML、标题长度（≤32）、摘要长度（≤128）、图片数量和封面。发布前先解析所有正文图片，逐项核实本地路径存在，并预检图片格式是否能被当前上传工具和公众号接口接受；不要等顺序上传开始后再发现格式错误。若出现不兼容格式（例如 WebP 被当前接口拒绝），在本次版本化发布输出目录中转换为兼容的 PNG 或 JPEG 副本，只改发布用 HTML 对应的图片地址，不改文章 Markdown、原始图片或 visual-manifest。转换后重跑 dry-run，并确认图片总数不变、全部本地文件可读、仅目标图片地址变化；记录源图与转换副本的路径及 SHA-256，再开始任何网络上传。若文章含 Markdown 表格，确认每张表都成为真实 `<table>`，不能残留在 `<p>` 里；用手机宽度打开预览并截图检查单元格文字、边框和横向溢出。核对完成后，A 段到此结束：把预览 HTML、图片清单（含 SHA-256）、封面、标题、摘要和检查结果整理成交接清单，交给月明。上传到公众号后台是 B 段，只由月明在 Mac 上执行（见 [upload-on-mac.md](references/upload-on-mac.md)）。

5. 报告预览 HTML、交接清单和检查结果路径，状态写“A 段完成，待月明上传”。

已有品牌 HTML 时，改用 `--html`，并显式提供 `--title`。常用个性化参数用 `--kicker`、`--hero`、`--strapline`、`--author`、`--digest`；运行 `--help` 查看完整参数。

## 共享资产交接

接收写作 Skill 已确定的图片与使用顺序。文章 assets/visual-manifest.json 从作品 production/illustrations/visual-manifest.json 导出，保留 asset_id、revision、sha256，path 按现有检查器相对文章目录解析。发布器只核验和转换平台所需格式，不生成或重画正文图；缺图回配图 Skill。线稿宇航员图只要符合身份与内容职责即可，不强制写实光影或发光灯带。

## 品牌样式不变量

- 白底正文；深墨蓝 `#182b42` 建立章节锚点；铜橙 `#9b4f2c`/亮铜 `#e0894f` 只用于结构、结论和少量识别线（色值以 [品牌令牌](references/brand-tokens.md) 纸面主题为准，随包副本）。
- 默认使用轻量顶部品牌线，不在正文重复微信原生标题；章节使用 `SECTION 01` 编号；正文图片默认不显示编号或技术化图注，只有图片 alt 以 `图注：` 开头时才显示自然图注。
- 不使用整页底色、渐变、阴影、外链 CSS、`<style>` 或 `<script>`。
- 视觉样式必须对应内容语义：`**普通强调**` 保持深色，`==关键结果==` 使用品牌铜橙虚线强调；不要用颜色代替论证。
- 每篇最多使用 3 个重点模块，且最多一个 `[!VERDICT]`。Markdown 可用 `> [!KEY]`、`> [!NOTE]`、`> [!VERDICT]`、`> [!QUESTION]`、`> [!COMPARE] 左 || 右`。
- `[!KEY]` 是不带卡片的核心金句；`[!NOTE]` 是浅色解释框；深色 `[!VERDICT]` 只用于全文最终结论。每个章节最多 2 处 `==关键结果==`。
- 品牌图最低数量沿用上游已确认方向，通过 check_visuals.py 的 --min-brand-ai 和 publish.py 的 --min-brand-images 传入同一值；已确认非宇航员或纯证据图方向可以为 0。只有实际选用宇航员品牌图时才按对应身份标志核验；其他已确认解释图按真实类型登记，不计入该数量。线稿不用发光灯带。
- 品牌场景图必须推进理解；产品截图只算证据图，不能用截图凑足品牌配图数量。
- 交接前必须通过 `visual-manifest.json` 检查；缺清单、缺固定 IP 标记或未达到本次已选定配图要求时停止交接。

## 首次接入与故障

都属于 B 段，只在月明 Mac 上处理，见 [upload-on-mac.md](references/upload-on-mac.md)。A 段不需要凭据、白名单或 Bootstrap。
