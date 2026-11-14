# guoshen 三阶段审核合同

编排归 moonlit-content-engine；guoshen 是第三方原子审核能力，不在其 fork 写入本公司编排。每次按名称读取当前激活 guoshen/SKILL.md，实际执行语义审核，再保存证据与回执。门禁只检查完整性、版本、时效与输入绑定，不替代语义判断。

## 触发与三阶段

1. **script：文案确认后立即审文本**。母稿、口播或平台文案已获当前任务确认时就运行，不强审初稿，不等待成片、封面或上传页面。审已确认版本的正文、标题、事实宣称与引语等已有文字；报告明确音频、画面、封面、平台原生设置/裁切尚未审。script通过只允许继续当前已授权制作，不意味着内容包或平台页面通过。平台未选定时先做通用文本审核，明确平台规则待选；目标平台确定后补相应文本适用性核验并登记该平台script结论，不因缺成片延后文本审查。
2. **content：上传前审完整实际内容包**。联合实际正文/独立语音、字幕、全画面OCR和原帧语义、图片、封面文件、标题/简介/话题及声明意图。审核与script绑定的确认文本及所有实际上传输入；不能仅查字幕、敏感词或单张抽帧。仅未出现的原生设置和平台封面槽位裁切可明确延期，不能把音画、正文、版权或封面文件列作延期。通过后才可按已有授权上传未发布草稿/填表。
3. **final：上传草稿后审真实页面**。核对平台原生声明/设置、真实封面呈现与裁切以及实际草稿内容，保存页面证据并绑定文件hash；final通过后才可READY或按本次明确授权提交。API草稿成功不证明页面合规。最终提交与平台回读另行记录，审核中只能记submitted。

每阶段均不得替代后两阶段、用户授权或平台裁决。任一必要阶段未跑、需复核、材料未检查或有阻断风险，先修复并实际重审。改变文案使相关script及其下游审核失效；媒体/封面/渠道包改变使content及final失效；原生设置/裁切改变至少重做final。若修复改变作者原意，按当前授权处理，不能为了审核擅改观点或加入规避性小字。

目标平台明确后只审所选平台。小红书、抖音、B站、视频号用上游适用规则；公众号、X、朋友圈补读当前官方条款，不能冒用视频号结论。严格零网址、国外AI推广等只有用户明确选择时启用；普通技术名词与真实复盘不机械判违规。审核不保证平台通过。

## 证据与v2回执

产物放作品 production/publish-review/<版本>/，不上传到fork或外部仓库。每阶段各有实际审核时间、语义报告、规则上下文、提取证据与本阶段inputs；输入及产物均写path和sha256，相对回执定位。`coverage: complete`仅指该阶段范围：script文本完整并明确其他媒体未审，绝非全片已审。候选扫描不得自动产生通过回执。

顶层字段：`schemaVersion: 2`、`skill: guoshen`、`skillTreeSha256`（当前激活目录的tree_sha）、`skillFiles`（SKILL.md与resources/VERSION的实际hash）、`platforms.<平台ID>.stages`。每阶段结构如下（占位符不是可用证据）：

```json
{
  "reviewedAt": "实际审核时间，含时区",
  "decision": "未发现明显问题",
  "blockingFindings": 0,
  "coverage": "complete",
  "semanticReview": true,
  "officialSourcesReviewed": true,
  "inputs": [{"path": "实际阶段输入", "sha256": "实际hash"}],
  "report": [{"path": "本阶段语义报告", "sha256": "实际hash"}],
  "ruleContext": [{"path": "本阶段规则上下文", "sha256": "实际hash"}],
  "evidence": [{"path": "本阶段提取证据", "sha256": "实际hash"}]
}
```

- script增加 `unreviewed: ["audio", "visuals", "cover", "nativeSettings", "platformCoverCrop"]`，不要求这些产物存在。只有文本实际确认后才执行，确认版本及来源写本阶段报告；未确定平台的通用文本报告不伪称已审平台规则。
- content增加 `previousStageSha256`，值为同平台script对象经本门禁 `stage_sha()` 计算的hash；inputs包含script所有输入及完整上传包。`deferredChecks`仅可含nativeSettings、platformCoverCrop。
- final同样绑定content对象的stage_sha，inputs包含content全部输入及实际页面证据；增加 `nativeSettingsEvidence`、`platformCoverEvidence` 两个path/hash记录，且同时列入本阶段inputs，不能保留deferredChecks。
- 注册表外平台各阶段增加 `supplementalPlatformReview: true`，报告指向实际补读来源。所有阶段时间顺序递增，24小时后、上游版本或规则变化后重审。新发布请求重新语义复核；同请求恢复只复用未变且仍有效的证据。

**旧回执兼容边界**：v1仅保留作历史证据，不能用于任何v2阶段放行。门禁显式拒绝，实际补齐三阶段后生成v2；不能只改schemaVersion、把一个旧结论复制成三份或自动映射通过。没有跳过审核开关。

## 调用与单独入口

从工程激活名称解析本Skill及guoshen，不拼物理兄弟目录。生产主入口在文案确认后运行script；单独调用发布器、直接CLI、手工浏览器、恢复、重发和跨平台复用均执行同一合同。若直接收到成片而缺script，先审对应已确认文本，不能用成片或final倒替script。

```text
python3 <moonlit-content-engine>/scripts/publish_review_gate.py \
  --require-chain-version 2 --stage script \
  --guoshen-dir <当前激活guoshen> --receipt <v2回执> \
  --platform <目标平台> --file <已确认文本>
```

content和final调用同一命令，换stage并对每个实际输入重复--file；默认final。content递归验证script，final递归验证script和content，包括输入、证据及前阶段hash；脚本独立通过不要求不存在的媒体。调用方必须传 `--require-chain-version 2`，误指旧门禁时旧脚本将因未知参数退出，不能降级绕三审。

发布依赖显式注入：MOONLIT_GUOSHEN_GATE指本Skill门禁，MOONLIT_GUOSHEN_DIR指当前原子审核能力，MOONLIT_GUOSHEN_RECEIPT指当前包回执。上传前调用content，READY/最终提交前调用final；不允许本地格式校验冒充风险审核。规则缺失或失败时停止外部上传/提交，继续本地修复；已有授权不因切换Skill反复索取。
