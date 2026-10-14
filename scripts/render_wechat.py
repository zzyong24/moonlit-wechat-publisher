#!/usr/bin/env python3
"""Render Markdown into the Moonlit inline-style WeChat HTML fragment."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import sys


IMAGE_RE = re.compile(r"^!\[([^]]*)\]\(([^)]+)\)\s*$")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
ORDERED_RE = re.compile(r"^\d+[.)]\s+(.+)$")
CALLOUT_RE = re.compile(r"^\[!(KEY|NOTE|VERDICT|QUESTION|COMPARE)]\s*(.+)$", re.I)
TABLE_RULE_RE = re.compile(r"^:?-{3,}:?$")


def inline(text: str, tone: str = "normal") -> str:
    value = html.escape(text.strip(), quote=True)
    strong_color = "#e0894f" if tone == "dark" else "#182b42"
    highlight_color = "#e0894f" if tone == "dark" else "#8a4426"
    highlight_border = "#c27a4f" if tone == "dark" else "#d9a07a"
    value = re.sub(
        r"\[([^]]+)]\((https?://[^)]+)\)",
        r'<a href="\2" style="color: #8a4426; text-decoration: none; border-bottom: 1px solid #d9a07a;">\1</a>',
        value,
    )
    value = re.sub(
        r"`([^`]+)`",
        r'<code style="padding: 2px 5px; background-color: #f1ede6; color: #182b42; font-family: Menlo, Consolas, monospace; font-size: 0.9em;">\1</code>',
        value,
    )
    value = re.sub(
        r"\*\*(.+?)\*\*",
        rf'<strong style="color: {strong_color}; font-weight: 700;">\1</strong>',
        value,
    )
    value = re.sub(
        r"==(.+?)==",
        rf'<span style="color: {highlight_color}; font-weight: 700; border-bottom: 2px dashed {highlight_border}; padding-bottom: 1px;">\1</span>',
        value,
    )
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def paragraph(text: str, lead: bool = False) -> str:
    if text.strip().startswith(("——", "— ")):
        return (
            '<p style="margin: 22px 0 0; color: #536176; font-size: 13px; line-height: 1.6; '
            f'letter-spacing: 0.08em; text-align: right;">{inline(text)}</p>'
        )
    if lead:
        return (
            '<p style="margin: 30px 0 22px; color: #182b42; font-size: 19px; line-height: 1.78; '
            f'font-weight: 700; letter-spacing: 0.01em;">{inline(text)}</p>'
        )
    return (
        '<p style="margin: 0 0 21px; color: #394b60; font-size: 17px; line-height: 1.95; '
        f'letter-spacing: 0.012em; text-align: justify;">{inline(text)}</p>'
    )


def split_table_row(line: str) -> list[str]:
    """Split a Markdown pipe-table row, preserving pipes inside code spans."""
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]

    cells: list[str] = []
    current: list[str] = []
    in_code = False
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value) and value[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current.clear()
        else:
            current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def is_table_delimiter(line: str) -> bool:
    cells = split_table_row(line)
    return len(cells) > 1 and all(TABLE_RULE_RE.fullmatch(cell) for cell in cells)


def table_block(header: list[str], delimiter: list[str], rows: list[list[str]]) -> str:
    if len(header) != len(delimiter):
        raise ValueError("Markdown table header and delimiter have different column counts")
    for row in rows:
        if len(row) != len(header):
            raise ValueError(
                f"Markdown table row has {len(row)} columns; expected {len(header)}"
            )

    alignments = []
    for rule in delimiter:
        alignments.append("center" if rule.startswith(":") and rule.endswith(":") else "right" if rule.endswith(":") else "left")

    table = (
        '<table border="0" cellpadding="0" cellspacing="0" width="100%" '
        'style="width: 100%; margin: 22px 0 30px; border-collapse: collapse; table-layout: fixed; '
        'font-size: 14px; line-height: 1.65; color: #394b60; word-break: break-all;"><tbody><tr>'
    )
    for cell, alignment in zip(header, alignments):
        table += (
            f'<td style="padding: 9px 7px; border: 1px solid #e4ded3; background-color: #f6f2ea; '
            f'color: #182b42; font-size: 13px; line-height: 1.55; font-weight: 700; '
            f'text-align: {alignment}; vertical-align: top;">{inline(cell)}</td>'
        )
    table += "</tr>"
    for row_index, row in enumerate(rows):
        background = "#ffffff" if row_index % 2 == 0 else "#faf8f4"
        table += "<tr>"
        for cell, alignment in zip(row, alignments):
            table += (
                f'<td style="padding: 9px 7px; border: 1px solid #e4ded3; background-color: {background}; '
                f'color: #394b60; font-size: 13px; line-height: 1.65; text-align: {alignment}; '
                f'vertical-align: top;">{inline(cell)}</td>'
            )
        table += "</tr>"
    return table + "</tbody></table>"


def heading_two(text: str, index: int) -> str:
    return (
        '<section style="margin: 54px 0 25px; padding: 0 0 12px; border-bottom: 1px solid #e4ded3;">'
        '<p style="margin: 0 0 9px; color: #9b4f2c; font-family: Georgia, \'Times New Roman\', serif; '
        f'font-size: 13px; line-height: 1; font-weight: 700; letter-spacing: 0.16em;">SECTION {index:02d}</p>'
        '<h2 style="margin: 0; padding: 0 0 0 13px; border-left: 4px solid #e0894f; '
        'color: #182b42; font-size: 23px; line-height: 1.5; '
        f'font-weight: 700; letter-spacing: 0.01em;">{inline(text)}</h2></section>'
    )


def image_block(alt: str, source: str, index: int) -> str:
    # Alt text remains available to assistive technology, but is not automatically
    # rendered as a report-like figure label. Add an explicit `图注：` prefix in
    # Markdown only when a visible caption is genuinely needed.
    caption = ""
    if alt.strip().startswith("图注："):
        caption = alt.strip()[3:].strip()
    block = (
        '<section style="margin: 34px 0 40px; padding: 0; border-bottom: 2px solid #e0894f; line-height: 0;">'
        f'<img src="{html.escape(source, quote=True)}" alt="{html.escape(alt, quote=True)}" '
        'style="display: block; width: 100%; height: auto; margin: 0; border: 0;" />'
    )
    if caption:
        block += (
            '<p style="margin: 0; padding: 10px 2px 9px; color: #536176; background-color: #ffffff; '
            f'font-size: 12px; line-height: 1.5; letter-spacing: 0.04em; text-align: left;">{html.escape(caption)}</p>'
        )
    return block + "</section>"


def callout(kind: str, text: str) -> str:
    kind = kind.upper()
    if kind == "KEY":
        return (
            '<section style="margin: 29px 0 32px; padding: 0;">'
            f'<p style="margin: 0; color: #8a4426; font-size: 20px; line-height: 1.72; font-weight: 700; letter-spacing: 0.01em;">{inline(text)}</p>'
            "</section>"
        )
    if kind == "NOTE":
        return (
            '<blockquote style="margin: 26px 0 31px; padding: 19px 19px 18px; border: 0; '
            'border-left: 5px solid #9b4f2c; background-color: #f6f2ea;">'
            f'<p style="margin: 0; color: #394b60; font-size: 16px; line-height: 1.9;">{inline(text)}</p>'
            "</blockquote>"
        )
    if kind == "COMPARE":
        left, separator, right = text.partition("||")
        if not separator:
            raise ValueError("[!COMPARE] requires: left || right")
        return (
            '<table style="width: 100%; margin: 26px 0 30px; border-collapse: collapse; table-layout: fixed;">'
            '<tbody><tr>'
            '<td style="width: 50%; padding: 18px 14px; border: 1px solid #e4ded3; background-color: #f4f1ec; '
            f'color: #182b42; font-size: 18px; line-height: 1.5; font-weight: 700; text-align: center;">{inline(left)}</td>'
            '<td style="width: 50%; padding: 18px 14px; border: 1px solid #182b42; background-color: #182b42; '
            f'color: #e0894f; font-size: 18px; line-height: 1.5; font-weight: 700; text-align: center;">{inline(right)}</td>'
            "</tr></tbody></table>"
        )
    if kind == "QUESTION":
        return (
            '<section style="margin: 38px 0 18px; padding: 20px 18px; border: 2px solid #182b42; background-color: #ffffff;">'
            '<p style="margin: 0 0 7px; color: #9b4f2c; font-family: Georgia, serif; font-size: 12px; '
            'line-height: 1.4; font-weight: 700; letter-spacing: 0.14em;">ONE QUESTION</p>'
            f'<p style="margin: 0; color: #182b42; font-size: 18px; line-height: 1.7; font-weight: 700;">{inline(text)}</p>'
            "</section>"
        )
    return (
        '<blockquote style="margin: 26px 0 30px; padding: 22px 20px; border: 0; '
        'border-left: 7px solid #e0894f; background-color: #182b42;">'
        f'<p style="margin: 0; color: #ffffff; font-size: 20px; line-height: 1.68; font-weight: 700;">{inline(text, "dark")}</p>'
        "</blockquote>"
    )


def strip_frontmatter(lines: list[str]) -> list[str]:
    if not lines or lines[0].strip() != "---":
        return lines
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[index + 1 :]
    return lines


def extract_title(markdown: str) -> str:
    for line in strip_frontmatter(markdown.splitlines()):
        match = H1_RE.match(line)
        if match:
            return match.group(1).strip()
    return ""


def render_markdown(
    markdown: str,
    kicker: str,
    hero: str | None,
    strapline: str | None,
    hero_style: str = "compact",
) -> tuple[str, dict]:
    lines = strip_frontmatter(markdown.splitlines())
    title = extract_title(markdown)
    hero_text = hero or title or "月明水清深"
    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    ordered = False
    heading_count = 0
    image_count = 0
    table_count = 0
    highlight_count = 0
    callout_counts = {kind: 0 for kind in ("KEY", "NOTE", "VERDICT", "QUESTION", "COMPARE")}
    section_highlights: dict[int, int] = {0: 0}
    first_paragraph = True
    in_code = False
    code_lines: list[str] = []

    def register_highlights(text: str) -> None:
        nonlocal highlight_count
        count = len(re.findall(r"==.+?==", text))
        highlight_count += count
        section_highlights[heading_count] = section_highlights.get(heading_count, 0) + count

    def flush_paragraph() -> None:
        nonlocal first_paragraph
        if not paragraph_lines:
            return
        text = " ".join(part.strip() for part in paragraph_lines).strip()
        paragraph_lines.clear()
        if text:
            blocks.append(paragraph(text, first_paragraph))
            first_paragraph = False

    def flush_list() -> None:
        nonlocal ordered
        if not list_items:
            return
        tag = "ol" if ordered else "ul"
        items = "".join(
            f'<li style="margin: 0 0 9px; padding-left: 2px; color: #2b3644; font-size: 16px; line-height: 1.8;">{inline(item)}</li>'
            for item in list_items
        )
        blocks.append(
            f'<{tag} style="margin: 8px 0 24px; padding-left: 24px; color: #2b3644;">{items}</{tag}>'
        )
        list_items.clear()
        ordered = False

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                code = html.escape("\n".join(code_lines))
                blocks.append(
                    '<pre style="margin: 18px 0 24px; padding: 16px; overflow-x: auto; background-color: #182b42; '
                    f'color: #f3f0e8; font-size: 13px; line-height: 1.65;"><code>{code}</code></pre>'
                )
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            line_index += 1
            continue
        if in_code:
            code_lines.append(line)
            line_index += 1
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            line_index += 1
            continue
        match = H1_RE.match(line)
        if match:
            flush_paragraph()
            flush_list()
            line_index += 1
            continue
        match = H2_RE.match(line)
        if match:
            flush_paragraph()
            flush_list()
            heading_count += 1
            section_highlights.setdefault(heading_count, 0)
            register_highlights(match.group(1))
            blocks.append(heading_two(match.group(1), heading_count))
            line_index += 1
            continue
        match = H3_RE.match(line)
        if match:
            flush_paragraph()
            flush_list()
            register_highlights(match.group(1))
            blocks.append(
                '<h3 style="margin: 30px 0 14px; padding: 0 0 7px; border-bottom: 2px solid #e0894f; '
                f'color: #182b42; font-size: 18px; line-height: 1.5; font-weight: 700;">{inline(match.group(1))}</h3>'
            )
            line_index += 1
            continue
        if line_index + 1 < len(lines) and "|" in line and is_table_delimiter(lines[line_index + 1]):
            flush_paragraph()
            flush_list()
            header = split_table_row(line)
            delimiter = split_table_row(lines[line_index + 1])
            if len(header) != len(delimiter):
                raise ValueError("Markdown table header and delimiter have different column counts")
            rows: list[list[str]] = []
            line_index += 2
            while line_index < len(lines) and "|" in lines[line_index] and lines[line_index].strip():
                rows.append(split_table_row(lines[line_index]))
                line_index += 1
            for cell in [*header, *(cell for row in rows for cell in row)]:
                register_highlights(cell)
            blocks.append(table_block(header, delimiter, rows))
            table_count += 1
            continue
        match = IMAGE_RE.match(stripped)
        if match:
            flush_paragraph()
            flush_list()
            image_count += 1
            blocks.append(image_block(match.group(1), match.group(2), image_count))
            line_index += 1
            continue
        if stripped in {"---", "***", "___"}:
            flush_paragraph()
            flush_list()
            blocks.append('<hr style="margin: 30px 0; border: 0; border-top: 1px solid #e4ded3;" />')
            line_index += 1
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            quote = stripped[1:].strip()
            register_highlights(quote)
            marker = CALLOUT_RE.match(quote)
            if marker:
                kind = marker.group(1).upper()
                callout_counts[kind] += 1
                blocks.append(callout(marker.group(1), marker.group(2)))
            else:
                blocks.append(
                    '<blockquote style="margin: 22px 0 26px; padding: 15px 17px; border-left: 4px solid #9b4f2c; '
                    f'background-color: #f4f1ec;"><p style="margin: 0; color: #2b3644; font-size: 16px; line-height: 1.8;">{inline(quote)}</p></blockquote>'
                )
            line_index += 1
            continue
        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            if ordered and list_items:
                flush_list()
            item = stripped[2:].strip()
            register_highlights(item)
            list_items.append(item)
            line_index += 1
            continue
        ordered_match = ORDERED_RE.match(stripped)
        if ordered_match:
            flush_paragraph()
            if list_items and not ordered:
                flush_list()
            ordered = True
            item = ordered_match.group(1).strip()
            register_highlights(item)
            list_items.append(item)
            line_index += 1
            continue
        flush_list()
        register_highlights(stripped)
        paragraph_lines.append(stripped)
        line_index += 1

    flush_paragraph()
    flush_list()
    if in_code:
        raise ValueError("unclosed fenced code block")

    module_count = sum(callout_counts.values())
    if module_count > 3:
        raise ValueError(f"too many emphasis modules: {module_count}; maximum is 3")
    if callout_counts["VERDICT"] > 1:
        raise ValueError("only one [!VERDICT] module is allowed")
    crowded_sections = [index for index, count in section_highlights.items() if count > 2]
    if crowded_sections:
        labels = ", ".join("导语" if index == 0 else f"SECTION {index:02d}" for index in crowded_sections)
        raise ValueError(f"too many ==highlights== in {labels}; maximum is 2 per section")

    if hero_style == "dark":
        hero_parts = [
            '<section style="margin: 0 0 28px; padding: 25px 21px 23px; border-top: 7px solid #e0894f; background-color: #182b42;">',
            '<p style="margin: 0 0 17px; color: #e0894f; font-family: Georgia, \'Times New Roman\', serif; '
            f'font-size: 12px; line-height: 1.2; font-weight: 700; letter-spacing: 0.16em;">{html.escape(kicker)}</p>',
            '<p style="margin: 0; color: #ffffff; font-size: 27px; line-height: 1.4; font-weight: 700; '
            f'letter-spacing: 0.01em;">{inline(hero_text, "dark")}</p>',
        ]
        if strapline:
            hero_parts[-1] = hero_parts[-1].replace('margin: 0;', 'margin: 0 0 17px;', 1)
            hero_parts.append(
                '<p style="margin: 0; color: #a8b3c0; font-size: 13px; line-height: 1.7; '
                f'letter-spacing: 0.05em;">{inline(strapline, "dark")}</p>'
            )
        hero_parts.append("</section>")
        hero_html = "".join(hero_parts)
    elif hero_style == "compact":
        compact_parts = [
            '<section style="margin: 0 0 29px; padding: 13px 0 12px; border-top: 3px solid #9b4f2c; border-bottom: 1px solid #e4ded3;">',
            '<p style="margin: 0; color: #8a4426; font-family: Georgia, \'Times New Roman\', serif; '
            f'font-size: 11px; line-height: 1.4; font-weight: 700; letter-spacing: 0.17em;">{html.escape(kicker)}</p>',
        ]
        if hero:
            compact_parts.append(
                '<p style="margin: 10px 0 0; color: #182b42; font-size: 18px; line-height: 1.65; font-weight: 700; '
                f'letter-spacing: 0.01em;">{inline(hero)}</p>'
            )
        if strapline:
            compact_parts.append(
                '<p style="margin: 8px 0 0; color: #536176; font-size: 13px; line-height: 1.7; '
                f'letter-spacing: 0.03em;">{inline(strapline)}</p>'
            )
        compact_parts.append("</section>")
        hero_html = "".join(compact_parts)
    elif hero_style == "none":
        hero_html = ""
    else:
        raise ValueError(f"unsupported hero_style: {hero_style}")
    output = (
        '<section style="margin: 0; padding: 0 14px 42px; background-color: #ffffff; color: #2b3644; '
        'font-family: PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif; word-break: break-word; box-sizing: border-box;">\n'
        '  <section style="max-width: 677px; margin: 0 auto; padding: 0; box-sizing: border-box;">\n'
        f"{hero_html}\n" + "\n".join(blocks) + "\n  </section>\n</section>\n"
    )
    return output, {
        "title": title,
        "headings": heading_count,
        "images": image_count,
        "tables": table_count,
        "bytes": len(output.encode()),
        "hero_style": hero_style,
        "emphasis": {
            "modules": module_count,
            "types": {kind: count for kind, count in callout_counts.items() if count},
            "inline_highlights": highlight_count,
            "highlights_by_section": section_highlights,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--kicker", default="MOONLIT / FIELD NOTES")
    parser.add_argument("--hero")
    parser.add_argument("--strapline")
    parser.add_argument("--hero-style", choices=("compact", "dark", "none"), default="compact")
    args = parser.parse_args()
    try:
        source = args.markdown.read_text(encoding="utf-8")
        rendered, metadata = render_markdown(source, args.kicker, args.hero, args.strapline, args.hero_style)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(json.dumps({"success": True, "output": str(args.output), **metadata}, ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps({"success": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
