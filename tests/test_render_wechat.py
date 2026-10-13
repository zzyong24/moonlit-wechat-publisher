from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from render_wechat import render_markdown  # noqa: E402
from publish import browser_document, localize_browser_images  # noqa: E402


class RenderWechatTest(unittest.TestCase):
    def test_light_editorial_semantics(self) -> None:
        markdown = """# 测试标题

这是 **关键概念**，也是 ==关键结果==。

这是普通正文。

> [!KEY] Skill 决定会做什么，记忆决定是不是同一个伙伴。

## 机制

> [!NOTE] 这是机制解释。

> [!VERDICT] 伙伴负责连续性，工作区负责隔离。
"""
        rendered, metadata = render_markdown(markdown, "MOONLIT / FIELD NOTES", None, None)

        self.assertNotIn("测试标题", rendered)
        self.assertIn("font-size: 19px", rendered)
        self.assertIn("font-size: 17px", rendered)
        self.assertIn('color: #121815; font-weight: 700;">关键概念', rendered)
        self.assertIn("border-bottom: 2px dashed #86caaa", rendered)
        self.assertIn("font-size: 20px", rendered)
        self.assertIn("background-color: #f1f7f3", rendered)
        self.assertIn("background-color: #121815", rendered)
        self.assertEqual(metadata["hero_style"], "compact")
        self.assertEqual(metadata["emphasis"]["modules"], 3)
        self.assertEqual(metadata["emphasis"]["inline_highlights"], 1)

    def test_compact_header_does_not_repeat_native_title(self) -> None:
        rendered, _ = render_markdown("# 原生标题\n\n正文。", "MOONLIT", None, None, "compact")
        self.assertNotIn("原生标题", rendered)
        self.assertIn("border-top: 3px solid #12a868", rendered)

    def test_dark_header_remains_opt_in(self) -> None:
        rendered, _ = render_markdown("# 原生标题\n\n正文。", "MOONLIT", None, None, "dark")
        self.assertIn("原生标题", rendered)
        self.assertIn("border-top: 7px solid #b7ef3f", rendered)

    def test_rejects_more_than_three_modules(self) -> None:
        markdown = """# 标题

> [!KEY] 一

> [!NOTE] 二

> [!QUESTION] 三

> [!VERDICT] 四
"""
        with self.assertRaisesRegex(ValueError, "maximum is 3"):
            render_markdown(markdown, "MOONLIT", None, None)

    def test_rejects_multiple_verdicts(self) -> None:
        markdown = """# 标题

> [!VERDICT] 一

> [!VERDICT] 二
"""
        with self.assertRaisesRegex(ValueError, "only one"):
            render_markdown(markdown, "MOONLIT", None, None)

    def test_rejects_more_than_two_highlights_per_section(self) -> None:
        markdown = """# 标题

## 章节

==一==。

==二==。

==三==。
"""
        with self.assertRaisesRegex(ValueError, "maximum is 2 per section"):
            render_markdown(markdown, "MOONLIT", None, None)

    def test_wechat_fragment_has_no_style_or_script_tags(self) -> None:
        rendered, _ = render_markdown("# 标题\n\n正文。", "MOONLIT", None, None)
        self.assertNotIn("<style", rendered)
        self.assertNotIn("<script", rendered)

    def test_browser_preview_declares_utf8_and_viewport(self) -> None:
        document = browser_document("<p>中文正文</p>", "测试标题")
        self.assertIn('<meta charset="utf-8">', document)
        self.assertIn('name="viewport"', document)
        self.assertIn("中文正文", document)

    def test_browser_preview_uses_relative_local_images(self) -> None:
        base = Path("/tmp/moonlit-preview")
        fragment = '<img src="file:///tmp/moonlit-preview/assets/%E5%9B%BE.png" />'
        localized = localize_browser_images(fragment, base, base)
        self.assertIn('src="assets/图.png"', localized)

        relative_fragment = '<img src="assets/图.png" />'
        relative_localized = localize_browser_images(relative_fragment, base, base)
        self.assertIn('src="assets/图.png"', relative_localized)

    def test_images_do_not_get_automatic_figure_labels(self) -> None:
        rendered, _ = render_markdown("# 标题\n\n![生活记录](assets/a.png)", "MOONLIT", None, None)
        self.assertNotIn("FIG.", rendered)
        self.assertNotIn("生活记录</p>", rendered)

    def test_explicit_caption_is_natural_without_figure_number(self) -> None:
        rendered, _ = render_markdown("# 标题\n\n![图注：这是必要说明](assets/a.png)", "MOONLIT", None, None)
        self.assertNotIn("FIG.", rendered)
        self.assertIn("这是必要说明", rendered)

    def test_pipe_tables_render_as_responsive_inline_style_tables(self) -> None:
        markdown = """# 表格测试

## 两种工作方式

| 任务 | 工具 | 结果 |
|---|:---:|---:|
| 单独尝试功能 | Branch | 同一目录切换分支 |
| 并行任务 | Worktree | 多一份工作目录 |

## 许可证

| 许可证 | 商业用途 | 条件 |
|---|---|---|
| MIT | 允许 | 保留版权和许可证文本 |
| GPL-3.0 | 允许 | 再分发时提供源码 |
"""
        rendered, metadata = render_markdown(markdown, "MOONLIT", None, None)

        self.assertEqual(metadata["tables"], 2)
        self.assertEqual(rendered.count("<table"), 2)
        self.assertEqual(rendered.count("</table>"), 2)
        self.assertIn("table-layout: fixed", rendered)
        self.assertNotIn("<thead", rendered)
        self.assertNotIn("<th ", rendered)
        self.assertIn("Branch", rendered)
        self.assertIn("GPL-3.0", rendered)
        self.assertNotIn("|---|", rendered)
        self.assertNotIn("| 单独尝试功能", rendered)

    def test_table_rows_with_wrong_column_count_fail_instead_of_flattening(self) -> None:
        markdown = """# 表格测试

| A | B |
|---|---|
| one |
"""
        with self.assertRaisesRegex(ValueError, "expected 2"):
            render_markdown(markdown, "MOONLIT", None, None)


if __name__ == "__main__":
    unittest.main()
