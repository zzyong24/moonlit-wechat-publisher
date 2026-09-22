![公众号排版与草稿：排好文章，再写入草稿箱](assets/readme/hero.png)

# 月明·公众号排版与草稿

把确认后的文章排成月明样式 HTML，检查素材，并按授权写入微信公众号草稿箱。

## 你会得到什么

- 保留源文的 HTML 排版预览
- 图片清单、封面与字段预检结果
- 授权写入后的草稿标识与结果文件

## 试着这样说

```text
用 moonlit-wechat-publisher。把这篇确认后的 Markdown 排成公众号预览，先做本地检查，不上传。保留已经确认的配图顺序。
```

## 安装与首次使用

将本仓库的完整目录交给支持本地 Skill 的 Agent 安装，保留 `SKILL.md` 与随附资源。已有同名版本时先检查差异；使用版本锁的工作区沿用自身升级机制。

让 Agent 安装：

```text
请安装这个 Skill：https://github.com/zzyong24/moonlit-wechat-publisher
```

也可通过 Skills CLI 安装：

```bash
npx skills add zzyong24/moonlit-wechat-publisher
```

## 配置与依赖

本地排版使用 Python 脚本，具体环境见 onboarding 参考。写草稿需 md2wechat、可用的公众号 AppID/AppSecret 与接口 IP 白名单；短视频转 GIF 还需媒体工具。文章应先完成语言和内容审读。

## 数据与使用边界

dry-run 仅做本地预览；上传与创建草稿会将文章和媒体发送给微信接口。凭据不随仓库保存。写入草稿箱不等于群发，本 Skill 不擅自改写已确认正文。

## 详细说明

执行流程与资源导航见 [SKILL.md](SKILL.md)。安装检查不代表真实业务验收；需要外部服务、账号登录或付费生成的步骤，应在使用者自己的环境中验证。

---

月明水清深 · `moonlit-wechat-publisher`

首图为 AI 生成的品牌概念插画，不是工具截图或执行结果。
