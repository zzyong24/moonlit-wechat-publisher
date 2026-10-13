---
name: moonlit-wechat-publisher
description: Use when a user wants to format a Markdown or HTML article in the 月明水清深 WeChat style, turn short video evidence into an article GIF, upload article images, create or verify a WeChat Official Account draft, or needs first-use md2wechat installation, AppID/AppSecret, and IP-whitelist guidance.
metadata:
  display_name: 月明·公众号草稿发布
  version: "1.5.2"
  updated: "2026-10-12"
---

# 月明·公众号草稿发布

把已确认的公众号文章排成月明品牌 HTML，并安全写入微信公众号草稿箱。核心边界：排版与预检可以本地执行；上传图片、创建或更新草稿必须获得用户对本次操作的明确授权。

## 发布前必需审核

内容进入发布准备，先按名称解析当前激活 `moonlit-content-engine`，读取其 `references/publish-review.md`，并实际运行依赖 `guoshen`。通读正文或独立语音/字幕及全画面，审核目标平台的当前规则、封面、渠道文案和发布设置；完成上传前内容报告与版本绑定回执，通过content门禁才上传未发布草稿；实际原生设置与裁切在草稿中核对，final门禁通过才进入READY或最终提交。API草稿成功仅证明入草稿，不冒充原生AI声明、所有封面裁切或群发已完成。修复、换平台、文案/媒体/设置变化后重审；审核缺失、未完成或不通过不能继续外发。手工浏览器路径、续发、恢复和直接CLI也遵守同一门禁；本地排版/只读检查可先执行。上游不支持的公众号、X等按合同补充对应平台审核，不能套用视频号结论。

执行发布命令前，按激活目录设置 `MOONLIT_GUOSHEN_GATE`、`MOONLIT_GUOSHEN_DIR`、`MOONLIT_GUOSHEN_RECEIPT`。共享门禁只验证回执，不能替代实际语义审核；通过也不代替本次发布授权。

## 路由

- 正常发布：`md2wechat` 已安装，凭据与白名单可用。不要运行 Bootstrap。
- 首次接入：缺少 CLI、配置文件、有效凭据，或出现 `40164`。先读 [references/onboarding.md](references/onboarding.md)，用户同意安装后才运行 `scripts/bootstrap.sh`。
- 只看样式：只运行 `scripts/publish.py --dry-run`，不访问微信接口。
- 录屏嵌入正文：选取能证明一个动作或结果的短片段，用 `scripts/video_to_gif.py` 转为体积受控的 GIF，再像普通图片一样插入 Markdown。不要把整段视频机械转成 GIF。
- 用户明确要求 AI 模式：先运行 `md2wechat convert ... --mode ai --json`。`action_required` 表示只生成了 AI 请求，不是 HTML 已完成；宿主 AI 生成 HTML 后，再用 `scripts/publish.py --html ...` 发布。

## 正常流程

1. 确认 Markdown、封面、标题、作者和摘要。发布前文章应已完成用户确认及 `moonlit-de-ai-perception` 检查；不要在发布阶段擅自改写正文。
   - 按实际展示范围判断采用：`article.browser.html` 是正文预览，默认不包含封面。用户指定该预览准备发布，可以采用对应正文，不能据此把封面清单里的 `pending` 改成已确认。先读当前封面记录和实际图，展示/确认本期封面及其入口；确认品牌语言、人物原图或其他平台封面，不等于确认新生成的公众号横幅。已明确展示并被本次发布指令采用的完整包无需逐项重复确认。
   - 封面和正文图先遵守当前工程 AGENTS、已确认品牌规范及本期明确方向，不由发布器固定切回宇航员。**微信公众号文章封面不使用作者真人照片或真人 IP**；用与文章命题相关的关系图、证据素材或产品画面承载主题。视频封面的真人品牌规则不套用到公众号文章封面。复用已确认素材，公众号封面按入口重新排版；不要直接裁切复用视频封面，也不在发布阶段重画正文图。
   - 公众号消息列表封面按 **2.35:1** 制作；使用横向构图为文章标题及主题关系图、证据或概念视觉留出清晰空间，不沿用视频封面的 4:3 或 3:4 画幅。其他公众号入口如有不同规格，按对应入口重新排版并记录尺寸依据。
   - 先从文章的核心命题、论点和证据中提炼一个与主题紧密相关、缩略图也能辨认的视觉概念，再决定主视觉与标题如何配合。封面应有完整的编辑设计：清楚的视觉主次、字体层级、留白、构图和材质语言；不能只做到“没有真人”或“没有霓虹”就算完成。
   - 对个人 AI、数据主权、个人上下文等观念型文章，使用有审美的编辑式视觉隐喻或经过设计的概念画面，让读者看出文章具体在谈什么；可以用生活上下文、个人记忆与 AI 的关系作为视觉线索。避免廉价流程图、临时拼贴、私人手账/旅行相册感和与命题脱节的装饰性抽象图；只有文章核心本身是机制或流程时，才把关系图作为封面主视觉。
   - 允许用准确排版的简洁大字号中文标题或标签，标题须明确点出主题（如 Personal AI）及文章问题；不让图像模型生成文字，不放小字或密集说明。封面要直观、大气，同时保留高级、克制的审美；避免浓重 AI 科技风、脱离生活的抽象网络、粒子或全息界面。
2. 阅读 [references/brand-image-spec.md](references/brand-image-spec.md)。未另定方向的宇航员长文模板检查 2 张有内容职责的 IP 场景图；已确认其他人物风格、纯证据图或更少插图时，在发布包记录真实素材类型、方向依据和最低数量，两处检查参数保持一致。非宇航员解释图不伪造固定 IP 标志，可以按本期已确认方向将最低品牌图数量设为 0；这不免除全图登记、源文件与实际上传检查，也不能用来掩盖缺图。发布器不补造图片。产品截图、封面和装饰图不计入品牌图数量。把全部图片登记到 `assets/visual-manifest.json`，先运行硬检查：

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

4. 检查预览 HTML、标题长度（≤32）、摘要长度（≤128）、图片数量和封面。发布前先解析所有正文图片，逐项核实本地路径存在，并预检图片格式是否能被当前上传工具和公众号接口接受；不要等顺序上传开始后再发现格式错误。若出现不兼容格式（例如 WebP 被当前接口拒绝），在本次版本化发布输出目录中转换为兼容的 PNG 或 JPEG 副本，只改发布用 HTML 对应的图片地址，不改文章 Markdown、原始图片或 visual-manifest。转换后重跑 dry-run，并确认图片总数不变、全部本地文件可读、仅目标图片地址变化；记录源图与转换副本的路径及 SHA-256，再开始任何网络上传。若文章含 Markdown 表格，确认每张表都成为真实 `<table>`，不能残留在 `<p>` 里；用手机宽度打开预览并截图检查单元格文字、边框和横向溢出。核对后，用户明确授权写入草稿箱才执行：

   ```bash
   python3 scripts/publish.py \
     --markdown /abs/article.md \
     --cover /abs/cover.png \
     --out-dir /abs/wechat-draft \
     --publish
   ```

5. 报告草稿 `media_id`、HTML、草稿 JSON 和结果清单路径。明确说明“写入草稿箱”不等于群发。

### API 草稿与浏览器核验

`publish.py --publish` 的正常路径是上传正文图片、上传封面，再通过 `md2wechat create_draft` 创建草稿；公众号后台浏览器页面只作可选的人工核验。`publish-result.json` 返回 `success: true`、`status: published_to_draft` 和新 `media_id` 时，已完成的是 API 入草稿，不需要再打开后台网页才能承认该结果。

遇到浏览器访问被拒，先定位被拒的具体操作及时间：查看后台失败不能倒推此前的 API 创建草稿失败，也不能笼统宣称微信 API 不可用。遵守拒绝信息对该浏览器操作及其替代操作的限制；不要用另一浏览器或接口绕过被拒的查看动作。用户另行授权创建新版本草稿时，先核对新版本尚无成功的 `publish-result.json`，再按正常 API 流程处理。

同一标题的 v06、v07 等版本不能靠标题辨认。每次 API 创建新草稿都保留对应源文、输出目录、结果清单和 `media_id`，在作品分发记录中标明当前版本与旧版本。结果不明时先回读已有清单及草稿身份，避免重复创建；本地 dry-run 的 `remoteEffects: false` 只描述那次预览，不能覆盖后续成功上传的事实。

`thumb_media_id` 与上传记录一致只证明资源关联，不能证明选图正确、用户认可或实际裁切合格。相关结论分别依据实际源图与选择记录、用户反馈、实际封面/裁切预览。用户纠正封面时先保留原上传包、撤回错误认可范围并标明待修正，再定位具体问题；原草稿无法回读时保留历史成功与当前未知，不猜测删除/发布原因，不自动重建。

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
- 品牌图最低数量沿用上游已确认方向，通过 check_visuals.py 的 --min-brand-ai 和 publish.py 的 --min-brand-images 传入同一值；已确认非宇航员或纯证据图方向可以为 0。只有实际选用宇航员品牌图时才按对应身份标志核验；其他已确认解释图按真实类型登记，不计入该数量。线稿不用发光灯带。
- 品牌场景图必须推进理解；产品截图只算证据图，不能用截图凑足品牌配图数量。
- 发布前必须通过 `visual-manifest.json` 检查；缺清单、缺固定 IP 标记或未达到本次已选定配图要求时停止发布。

## 首次接入与故障

- Bootstrap 只用于首次安装或修复配置，不得由正常发布脚本自动调用。
- `config validate` 只能证明 YAML 可读取；`scripts/preflight.py --live` 才会检查占位值、凭据与白名单。
- `40164`：先记录这一次 API 错误中的公网 IP 与时间，再在实际发请求的机器运行 `scripts/preflight.py --live`。若用户表示白名单已配置，先用实时预检验证凭据和当前出口；预检通过就继续发布，不重复要求加白名单。只有实时预检失败或本次错误 IP 与当前出口 IP 不一致时，才说明具体差异并引导用户核对真正调用机器的白名单；不能把旧错误 IP 当作当前出口，也不能在没有对照证据时断言 IP 一直未变。家庭/公司网络、代理/VPN及云环境的出口可能变化；无法从证据确定变化来源时明确说未知。
- `40001` / `42001`：检查 AppID、AppSecret；重置 Secret 后同步更新本机配置。
- 不把 AppSecret、access token 或完整配置写入日志、产物、Git 或聊天回复。
- 正文图片只上传一次；封面与正文图片是同一文件时复用其 `media_id`。
- GIF 应短、静音、可循环，并只承担一个证据任务。默认优先 3–8 秒、宽度不超过 720px、10fps、5MB 硬上限；文字可读性不足时缩短片段，不通过无限降画质换体积。
- 默认创建新草稿。更新已有草稿需要用户明确指定目标 `media_id`，先回读验证目标；失效的 `media_id` 不要猜测或循环重试。
