#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SOURCE_RAW_URL = "https://raw.githubusercontent.com/saropa/saropa_lints/main/README_STYLISTIC.md"
SOURCE_BLOB_URL = "https://github.com/saropa/saropa_lints/blob/main/README_STYLISTIC.md"
OUTPUT_PAGE = Path("docs/team-guidelines/stylistic-review.mdx")
OUTPUT_CSV = Path("docs/assets/stylistic-rule-review.csv")

CATEGORY_LABELS = {
    "General Stylistic Rules": "通用风格规则",
    "Widget Preferences": "Widget 偏好",
    "Null & Collection Handling": "空值与集合处理",
    "Control Flow & Async": "控制流与异步",
    "Whitespace & Constructors": "空行与构造函数",
    "Error Handling & Testing": "异常处理与测试",
    "Additional Style Rules": "附加风格规则",
    "String Handling": "字符串处理",
    "Import Organization": "导入组织",
    "Class Structure": "类结构",
    "Type Annotations": "类型标注",
    "Naming Conventions": "命名约定",
    "Expression Style": "表达式风格",
}

PROJECT_SPECIFIC_RULES = {
    "firebase_custom",
    "avoid_generic_greeting_text",
    "prefer_kebab_tag_name",
    "require_purchase_verification",
    "purchase_completed",
    "require_save_confirmation",
    "user_clicked_button",
}

VERSION_SENSITIVE_RULES = {
    "prefer_clip_r_superellipse",
    "prefer_clip_r_superellipse_clipper",
}

RULE_GLOSSES = {
    "prefer_relative_imports": "同包内文件优先使用相对导入。",
    "prefer_one_widget_per_file": "每个文件尽量只放一个 Widget 类。",
    "prefer_arrow_functions": "单返回表达式函数优先使用箭头语法。",
    "prefer_all_named_parameters": "当位置参数较多时，优先改为命名参数。",
    "prefer_trailing_comma_always": "多行结构统一保留尾随逗号。",
    "prefer_private_underscore_prefix": "实例字段默认使用下划线私有化。",
    "prefer_widget_methods_over_classes": "小型 Widget 优先写成方法而不是单独类。",
    "prefer_class_over_record_return": "方法返回值优先用类而不是 record。",
    "prefer_inline_callbacks": "回调优先内联编写，不额外提取方法引用。",
    "prefer_single_quotes": "字符串默认使用单引号。",
    "prefer_todo_format": "TODO 注释统一采用 `TODO(author): 描述` 格式。",
    "prefer_fixme_format": "FIXME 注释统一采用 `FIXME(author): 描述` 格式。",
    "prefer_sentence_case_comments": "普通注释以句首大写风格书写。",
    "prefer_period_after_doc": "文档注释结尾补句号。",
    "prefer_screaming_case_constants": "常量使用全大写下划线命名。",
    "prefer_descriptive_bool_names": "布尔命名使用 `is/has/can` 等语义前缀。",
    "prefer_snake_case_files": "文件名统一使用 `snake_case.dart`。",
    "avoid_small_text": "文本字号避免小于 12，兼顾可访问性。",
    "prefer_doc_comments_over_regular": "公开 API 说明优先使用 `///` 文档注释。",
    "prefer_straight_apostrophe": "字符串中的撇号优先使用直引号。",
    "prefer_curly_apostrophe": "字符串中的撇号优先使用弯引号。",
    "prefer_doc_curly_apostrophe": "文档注释中的撇号优先使用弯引号。",
    "prefer_doc_straight_apostrophe": "文档注释中的撇号优先使用直引号。",
    "arguments_ordering": "命名参数按字母顺序排列。",
    "capitalize_comment": "注释以大写字母开头。",
    "firebase_custom": "Firebase 相关写法遵守团队自定义约定。",
    "avoid_generic_greeting_text": "问候语文案遵守团队统一风格。",
    "prefer_kebab_tag_name": "标签名统一使用 kebab-case。",
    "prefer_rethrow_over_throw_e": "在 catch 中优先使用 `rethrow`，避免 `throw e`。",
    "prefer_sorted_parameters": "函数参数顺序遵守团队约定。",
    "require_purchase_verification": "购买流程需遵守校验相关团队约定。",
    "purchase_completed": "购买完成逻辑遵守团队既定写法。",
    "require_save_confirmation": "保存行为需要符合确认流程约定。",
    "user_clicked_button": "按钮点击逻辑遵守团队交互约定。",
    "prefer_sizedbox_over_container": "简单尺寸占位优先使用 `SizedBox`。",
    "prefer_container_over_sizedbox": "简单布局场景也优先统一使用 `Container`。",
    "prefer_text_rich_over_richtext": "富文本优先使用 `Text.rich`。",
    "prefer_richtext_over_text_rich": "富文本优先直接使用 `RichText`。",
    "prefer_edgeinsets_symmetric": "对称边距优先使用 `EdgeInsets.symmetric`。",
    "prefer_edgeinsets_only": "边距优先显式写成 `EdgeInsets.only`。",
    "prefer_borderradius_circular": "统一圆角优先使用 `BorderRadius.circular`。",
    "prefer_expanded_over_flexible": "等分拉伸场景优先使用 `Expanded`。",
    "prefer_flexible_over_expanded": "拉伸布局优先使用 `Flexible` 表达控制意图。",
    "prefer_material_theme_colors": "颜色优先从主题中读取。",
    "prefer_explicit_colors": "颜色优先直接显式指定。",
    "prefer_clip_r_superellipse": "圆角裁剪优先使用 `ClipRSuperellipse`。",
    "prefer_clip_r_superellipse_clipper": "带自定义裁剪时也优先使用 `ClipRSuperellipse`。",
    "prefer_addall_over_spread": "集合追加元素优先使用 `addAll()`。",
    "prefer_spread_over_addall": "集合拼接优先使用展开运算符 `...`。",
    "prefer_switch_expression": "分支表达优先使用 switch expression。",
    "prefer_switch_statement": "分支表达优先使用传统 switch statement。",
    "prefer_blank_line_before_return": "return 前保留一行空行。",
    "prefer_no_blank_line_before_return": "return 前不额外插入空行。",
    "prefer_specific_exceptions": "抛错时优先使用具体异常类型。",
    "prefer_generic_exception": "抛错时统一使用通用 `Exception`。",
    "prefer_exception_suffix": "异常类命名以 `Exception` 结尾。",
    "prefer_error_suffix": "异常类命名以 `Error` 结尾。",
    "prefer_on_over_catch": "try-catch 优先使用 `on 类型` 形式。",
    "prefer_catch_over_on": "try-catch 优先使用裸 `catch (e)`。",
    "prefer_given_when_then_comments": "测试中使用 Arrange/Act/Assert 或 Given/When/Then 注释。",
    "prefer_self_documenting_tests": "测试代码依靠命名和结构自解释，不额外写结构注释。",
    "prefer_expect_over_assert_in_tests": "测试断言优先使用 `expect()`。",
    "prefer_single_expectation_per_test": "每个测试尽量只保留一个断言目标。",
    "prefer_grouped_expectations": "相关断言允许集中写在一个测试里。",
    "prefer_test_name_should_when": "测试名采用 `should ... when ...` 句式。",
    "prefer_test_name_descriptive": "测试名采用自然描述式命名。",
    "prefer_interpolation_over_concatenation": "字符串拼接优先使用插值。",
    "prefer_concatenation_over_interpolation": "字符串拼接优先使用 `+` 连接。",
    "prefer_double_quotes": "字符串默认使用双引号。",
    "prefer_absolute_imports": "导入本地包内文件优先使用 `package:` 路径。",
    "prefer_grouped_imports": "导入按 `dart / package / relative` 分组。",
    "prefer_flat_imports": "导入列表保持扁平，不做分组。",
    "prefer_named_imports": "导入时优先使用 `show` / `hide` 明确暴露内容。",
    "prefer_fields_before_methods": "类中字段定义放在方法前面。",
    "prefer_methods_before_fields": "类中方法定义放在字段前面。",
    "prefer_static_members_first": "静态成员放在实例成员前面。",
    "prefer_instance_members_first": "实例成员放在静态成员前面。",
    "prefer_public_members_first": "公开成员放在私有成员前面。",
    "prefer_private_members_first": "私有成员放在公开成员前面。",
    "prefer_object_over_dynamic": "动态场景优先使用 `Object?` 而不是 `dynamic`。",
    "prefer_dynamic_over_object": "确实需要动态行为时优先直接使用 `dynamic`。",
    "prefer_lower_camel_case_constants": "常量采用 `lowerCamelCase` 命名。",
    "prefer_camel_case_method_names": "方法名统一使用 `camelCase`。",
    "prefer_explicit_this": "字段访问显式写出 `this.`。",
    "prefer_implicit_boolean_comparison": "布尔判断优先直接写 `if (flag)`。",
    "prefer_explicit_boolean_comparison": "布尔判断显式写成与 `true/false` 的比较。",
}

SHARED_EXAMPLE_OVERRIDES = {
    "prefer_sizedbox_over_container": (
        "Container(width: 100, height: 50)",
        "SizedBox(width: 100, height: 50)",
    ),
    "prefer_container_over_sizedbox": (
        "SizedBox(width: 100, height: 50)",
        "Container(width: 100, height: 50)",
    ),
    "prefer_clip_r_superellipse": (
        "ClipRRect(borderRadius: BorderRadius.circular(10), child: Image.network('url'))",
        "ClipRSuperellipse(borderRadius: BorderRadius.circular(10), child: Image.network('url'))",
    ),
    "prefer_clip_r_superellipse_clipper": (
        "ClipRRect(borderRadius: BorderRadius.circular(10), child: Image.network('url'))",
        "ClipRSuperellipse(borderRadius: BorderRadius.circular(10), child: Image.network('url'))",
    ),
    "prefer_given_when_then_comments": (
        "test('user login', () { final user = User('test@example.com'); final result = authService.login(user); expect(result.isSuccess, true); })",
        "test('user login', () { // Arrange ... // Act ... // Assert ... })",
    ),
    "prefer_self_documenting_tests": (
        "test('user login', () { // Arrange ... // Act ... // Assert ... })",
        "test('user login', () { final user = User('test@example.com'); final result = authService.login(user); expect(result.isSuccess, true); })",
    ),
}

MEETING_BUCKET_ORDER = {
    "二选一": 0,
    "低成本候选": 1,
    "通用候选": 2,
    "项目/业务相关": 3,
    "版本前提": 4,
}

BUCKET_STYLES = {
    "二选一": {
        "bg": "rgba(239, 68, 68, 0.14)",
        "text": "#b91c1c",
        "border": "rgba(185, 28, 28, 0.24)",
    },
    "低成本候选": {
        "bg": "rgba(59, 130, 246, 0.14)",
        "text": "#1d4ed8",
        "border": "rgba(29, 78, 216, 0.24)",
    },
    "通用候选": {
        "bg": "rgba(34, 197, 94, 0.14)",
        "text": "#15803d",
        "border": "rgba(21, 128, 61, 0.24)",
    },
    "项目/业务相关": {
        "bg": "rgba(245, 158, 11, 0.18)",
        "text": "#b45309",
        "border": "rgba(180, 83, 9, 0.24)",
    },
    "版本前提": {
        "bg": "rgba(20, 184, 166, 0.14)",
        "text": "#0f766e",
        "border": "rgba(15, 118, 110, 0.24)",
    },
}

DECISION_STYLES = {
    "待评审": {
        "bg": "rgba(107, 114, 128, 0.14)",
        "text": "#4b5563",
        "border": "rgba(75, 85, 99, 0.22)",
    },
    "采纳": {
        "bg": "rgba(34, 197, 94, 0.14)",
        "text": "#15803d",
        "border": "rgba(21, 128, 61, 0.24)",
    },
    "不采纳": {
        "bg": "rgba(239, 68, 68, 0.14)",
        "text": "#b91c1c",
        "border": "rgba(185, 28, 28, 0.24)",
    },
    "试运行": {
        "bg": "rgba(59, 130, 246, 0.14)",
        "text": "#1d4ed8",
        "border": "rgba(29, 78, 216, 0.24)",
    },
    "暂缓": {
        "bg": "rgba(245, 158, 11, 0.18)",
        "text": "#b45309",
        "border": "rgba(180, 83, 9, 0.24)",
    },
}


@dataclass(frozen=True)
class RuleCandidate:
    section: str
    subsection: str | None
    category_label: str
    rule: str
    description: str
    gloss: str
    quick_fix: bool
    opposing_rule: str
    review_bucket: str
    discussion_suggestion: str
    source_url: str
    bad_example: str
    good_example: str


def fetch_source() -> str:
    with urllib.request.urlopen(SOURCE_RAW_URL) as response:
        return response.read().decode("utf-8")


def parse_rule_name(cell: str) -> str:
    match = re.search(r"`([^`]+)`", cell)
    if match:
        return match.group(1)
    return cell.strip()


def normalize_cell(cell: str) -> str:
    text = re.sub(r"\[(?:`)?([^`\]]+)(?:`)?\]\([^)]+\)", r"\1", cell)
    text = text.replace("`", "")
    return text.strip()


def combined_category(section: str, subsection: str | None) -> str:
    if section != "Additional Style Rules":
        return CATEGORY_LABELS.get(section, section)
    if not subsection:
        return CATEGORY_LABELS[section]
    return f"{CATEGORY_LABELS[section]} / {CATEGORY_LABELS.get(subsection, subsection)}"


def classify_rule(rule: str, opposing_rule: str, quick_fix: bool) -> str:
    if opposing_rule:
        return "二选一"
    if rule in PROJECT_SPECIFIC_RULES:
        return "项目/业务相关"
    if rule in VERSION_SENSITIVE_RULES:
        return "版本前提"
    if quick_fix:
        return "低成本候选"
    return "通用候选"


def discussion_suggestion(bucket: str) -> str:
    return {
        "二选一": "放入会议投票，必须和对立规则一起决策。",
        "低成本候选": "可先在分支试运行，再决定是否正式采纳。",
        "通用候选": "建议会前异步预投票，把有分歧项带入会议。",
        "项目/业务相关": "结合现有业务模块、团队习惯和适用范围讨论。",
        "版本前提": "先确认 Flutter 或 SDK 版本，再决定是否纳入候选。",
    }[bucket]


def build_badge(label: str, style: dict[str, str]) -> str:
    return (
        '<span style={{'
        'display: "inline-block", '
        'padding: "0.18rem 0.58rem", '
        'marginRight: "0.45rem", '
        'borderRadius: "999px", '
        'border: "1px solid '
        + style["border"]
        + '", '
        'background: "'
        + style["bg"]
        + '", '
        'color: "'
        + style["text"]
        + '", '
        'fontWeight: 800, '
        'fontSize: "0.78em", '
        'letterSpacing: "0.04em", '
        'lineHeight: 1.2, '
        'verticalAlign: "middle"'
        '}}>'
        + label
        + "</span>"
    )


def format_code_snippet(snippet: str) -> str:
    collapsed = " ".join(line.strip() for line in snippet.splitlines() if line.strip())
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    if len(collapsed) > 110:
        return collapsed[:107].rstrip() + "..."
    return collapsed


def render_example_cell(bad_example: str, good_example: str) -> str:
    if not bad_example and not good_example:
        return "—"
    parts = []
    if bad_example:
        parts.append(f"`BAD:` {format_code_snippet(bad_example)}")
    if good_example:
        parts.append(f"`GOOD:` {format_code_snippet(good_example)}")
    return "<br />".join(parts)


def parse_detailed_examples(content: str) -> dict[str, tuple[str, str]]:
    if "## Detailed Rule Documentation" not in content:
        return {}

    detail_content = content.split("## Detailed Rule Documentation", 1)[1]
    examples: dict[str, tuple[str, str]] = {}
    sections = re.split(r"^### ([A-Za-z0-9_]+)\s*$", detail_content, flags=re.MULTILINE)

    for index in range(1, len(sections), 2):
        rule = sections[index]
        body = sections[index + 1]
        code_match = re.search(r"```dart\n(.*?)```", body, re.DOTALL)
        if not code_match:
            continue

        bad_lines: list[str] = []
        good_lines: list[str] = []
        mode = None
        for raw_line in code_match.group(1).splitlines():
            line = raw_line.rstrip()
            if line.startswith("// BAD"):
                mode = "bad"
                continue
            if line.startswith("// GOOD"):
                mode = "good"
                continue
            if not line.strip():
                continue
            if mode == "bad":
                bad_lines.append(line)
            elif mode == "good":
                good_lines.append(line)

        if bad_lines or good_lines:
            examples[rule] = ("\n".join(bad_lines), "\n".join(good_lines))
    return examples


def parse_candidates(content: str) -> list[RuleCandidate]:
    lines = content.splitlines()
    section: str | None = None
    subsection: str | None = None
    candidates: list[RuleCandidate] = []
    index = 0
    detailed_examples = parse_detailed_examples(content)

    while index < len(lines):
        line = lines[index]

        if line.startswith("## Opposing Rules Reference"):
            break

        if line.startswith("## "):
            section = line[3:].strip()
            subsection = None
            index += 1
            continue

        if line.startswith("### "):
            subsection = line[4:].strip()
            index += 1
            continue

        if line.startswith("| Rule | Description |"):
            headers = [part.strip() for part in line.strip("|").split("|")]
            index += 2

            while index < len(lines) and lines[index].startswith("|"):
                values = [part.strip() for part in lines[index].strip("|").split("|")]
                row = dict(zip(headers, values))
                rule = parse_rule_name(row["Rule"])
                description = row["Description"].strip()
                quick_fix = row.get("Quick Fix", "").strip() == "Yes"
                opposing_rule = normalize_cell(row.get("Opposing Rule", ""))
                if opposing_rule in {"", "-", "—"}:
                    opposing_rule = ""

                bucket = classify_rule(rule, opposing_rule, quick_fix)
                bad_example, good_example = detailed_examples.get(rule, SHARED_EXAMPLE_OVERRIDES.get(rule, ("", "")))
                candidates.append(
                    RuleCandidate(
                        section=section or "",
                        subsection=subsection,
                        category_label=combined_category(section or "", subsection),
                        rule=rule,
                        description=description,
                        gloss=RULE_GLOSSES.get(rule, description),
                        quick_fix=quick_fix,
                        opposing_rule=opposing_rule,
                        review_bucket=bucket,
                        discussion_suggestion=discussion_suggestion(bucket),
                        source_url=f"{SOURCE_BLOB_URL}#{rule}",
                        bad_example=bad_example,
                        good_example=good_example,
                    )
                )
                index += 1
            continue

        index += 1

    return candidates


def unique_opposing_pairs(candidates: list[RuleCandidate]) -> list[tuple[RuleCandidate, RuleCandidate]]:
    by_rule = {candidate.rule: candidate for candidate in candidates}
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[RuleCandidate, RuleCandidate]] = []

    for candidate in candidates:
        if not candidate.opposing_rule or candidate.opposing_rule not in by_rule:
            continue
        key = tuple(sorted((candidate.rule, candidate.opposing_rule)))
        if key in seen:
            continue
        seen.add(key)
        pairs.append((by_rule[key[0]], by_rule[key[1]]))

    pairs.sort(key=lambda pair: (pair[0].category_label, pair[0].rule, pair[1].rule))
    return pairs


def bucket_counts(candidates: list[RuleCandidate]) -> Counter[str]:
    return Counter(candidate.review_bucket for candidate in candidates)


def escape_pipes(text: str) -> str:
    return text.replace("|", r"\|")


def render_pair_table(pairs: list[tuple[RuleCandidate, RuleCandidate]]) -> list[str]:
    lines = [
        "| 分类 | 方案 A | 方案 B | 中文释义 | 取舍点 | 示例 | 会议结论 | 备注 |\n",
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n",
    ]
    for left, right in pairs:
        tradeoff = f"{left.description} / {right.description}"
        example = render_example_cell(left.bad_example or right.bad_example, left.good_example or right.good_example)
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_pipes(left.category_label),
                    f"[`{left.rule}`]({left.source_url})",
                    f"[`{right.rule}`]({right.source_url})",
                    escape_pipes(f"A：{left.gloss}<br />B：{right.gloss}"),
                    escape_pipes(tradeoff),
                    example,
                    "待定",
                    "",
                ]
            )
            + " |\n"
        )
    return lines


def render_example_blocks(candidate: RuleCandidate) -> list[str]:
    lines: list[str] = []
    if candidate.bad_example:
        lines.extend(
            [
                "**BAD**\n\n",
                "```dart\n",
                candidate.bad_example.rstrip() + "\n",
                "```\n\n",
            ]
        )
    if candidate.good_example:
        lines.extend(
            [
                "**GOOD**\n\n",
                "```dart\n",
                candidate.good_example.rstrip() + "\n",
                "```\n\n",
            ]
        )
    return lines


def render_quick_index(candidates: list[RuleCandidate]) -> list[str]:
    grouped: dict[str, list[RuleCandidate]] = {}
    order: list[str] = []
    for candidate in candidates:
        if candidate.category_label not in grouped:
            grouped[candidate.category_label] = []
            order.append(candidate.category_label)
        grouped[candidate.category_label].append(candidate)

    lines: list[str] = []
    for category in order:
        lines.append(f"- [{category}](#{category.lower().replace(' / ', '-').replace(' ', '-')})\n")
        category_rules = sorted(grouped[category], key=lambda item: (MEETING_BUCKET_ORDER[item.review_bucket], item.rule))
        for candidate in category_rules:
            lines.append(f"  - [`{candidate.rule}`](#{candidate.rule})\n")
    lines.append("\n")
    return lines


def render_candidate_sections(candidates: list[RuleCandidate]) -> list[str]:
    grouped: dict[str, list[RuleCandidate]] = {}
    order: list[str] = []
    for candidate in candidates:
        if candidate.category_label not in grouped:
            grouped[candidate.category_label] = []
            order.append(candidate.category_label)
        grouped[candidate.category_label].append(candidate)

    lines: list[str] = []
    for category in order:
        lines.append(f"## {category}\n\n")
        lines.append(
            f"本分类共 `{len(grouped[category])}` 条规则，建议按 `二选一 -> 低成本候选 -> 其他` 的顺序讨论。\n\n"
        )
        for candidate in sorted(
            grouped[category],
            key=lambda item: (
                MEETING_BUCKET_ORDER[item.review_bucket],
                item.rule,
            ),
        ):
            bucket_badge = build_badge(candidate.review_bucket, BUCKET_STYLES[candidate.review_bucket])
            pending_badge = build_badge("待评审", DECISION_STYLES["待评审"])
            lines.append(f"### {bucket_badge}{pending_badge}`{candidate.rule}`\n\n")
            lines.append(f"- 中文释义：{candidate.gloss}\n")
            lines.append(f"- 上游说明：{candidate.description}\n")
            lines.append(f"- 初筛分组：{candidate.review_bucket}\n")
            lines.append(f"- 建议讨论方式：{candidate.discussion_suggestion}\n")
            lines.append(f"- 快速修复：{'是' if candidate.quick_fix else '否'}\n")
            if candidate.opposing_rule:
                lines.append(f"- 对立规则：[`{candidate.opposing_rule}`](#{candidate.opposing_rule})\n")
            lines.append(f"- 上游链接：[查看原始规则]({candidate.source_url})\n\n")

            lines.extend(
                [
                    "**评审记录模板**\n\n",
                    "- 当前结论：`待评审`\n",
                    "- 会议决定：`采纳 / 不采纳 / 试运行 / 暂缓`\n",
                    "- 结论理由：待填写\n",
                    "- 负责人：待填写\n",
                    "- 后续动作：待填写\n\n",
                ]
            )

            if candidate.bad_example or candidate.good_example:
                lines.append("**示例**\n\n")
                lines.extend(render_example_blocks(candidate))
            else:
                lines.append("> 示例：上游文档未提供，讨论时可结合项目内真实代码补充。\n\n")
        lines.append("\n")
    return lines


def render_page(candidates: list[RuleCandidate]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    counts = bucket_counts(candidates)
    pairs = unique_opposing_pairs(candidates)

    lines = [
        "---\n",
        "title: 团队规范：风格候选规则评审\n",
        "description: 基于 saropa_lints 的候选风格规则评审表，用于团队会前预读与会议取舍。\n",
        "prevpage:\n",
        "  url: /team-guidelines/figma-dev-mode\n",
        "  title: Figma 开发操作\n",
        "---\n\n",
        "<!-- 由 scripts/sync_stylistic_review.py 自动生成，请勿手工编辑规则表。 -->\n\n",
        "# 团队规范：风格候选规则评审\n\n",
        "这份评审表用于团队会议前后统一讨论 `saropa_lints` 的风格规则取舍。\n",
        "规则名称与上游 lint id 保持一致，便于直接映射到 `analysis_options.yaml`。\n\n",
        f"上游来源：[saropa_lints / README_STYLISTIC.md]({SOURCE_BLOB_URL})\n\n",
        f"配套 CSV：[下载候选规则评审表](/assets/stylistic-rule-review.csv)\n\n",
        f"最近一次同步日期：`{generated_at}`\n\n",
        "## 使用建议\n\n",
        "1. 会前先顺着本页逐条预读，在每条规则的 `评审记录模板` 里记录自己的倾向。\n",
        "2. 会议中优先讨论下面的“二选一冲突规则”，这些规则必须成对取舍。\n",
        "3. 对 `低成本候选` 可以优先试运行，再决定是否升级为团队正式规范。\n",
        "4. 对 `项目/业务相关` 或 `版本前提` 的规则，先确认适用范围，再决定是否纳入团队规范。\n\n",
        "> 说明\n",
        ">\n",
        "> 这份页面已经改成“逐条评审版”。主体部分不再依赖大表格，而是每条规则一个小节，方便在 `docs.page` 中一条条讨论、复制、记录会议结论。\n"
        "> `中文释义` 便于会前快速理解规则意图；`示例` 会优先复用上游 README 中已经提供的 BAD / GOOD 对照。\n"
        "> 没有示例的规则暂时留空，避免生成误导性的伪示例。\n\n",
        "## 初筛统计\n\n",
        f"- 总候选规则：`{len(candidates)}`\n",
        f"- 二选一规则：`{counts['二选一']}` 条，对应 `{len(pairs)}` 组冲突项\n",
        f"- 低成本候选：`{counts['低成本候选']}` 条\n",
        f"- 通用候选：`{counts['通用候选']}` 条\n",
        f"- 项目/业务相关：`{counts['项目/业务相关']}` 条\n",
        f"- 版本前提：`{counts['版本前提']}` 条\n\n",
        "## 初筛分组说明\n\n",
        "- `二选一`：存在明确对立规则，需要在会议里成对决策。\n",
        "- `低成本候选`：可自动修复或迁移成本较低，适合先试运行。\n",
        "- `通用候选`：没有明显对立项，也不强依赖具体业务，适合先异步预投票。\n",
        "- `项目/业务相关`：更像团队或业务约束，不建议脱离项目上下文直接采纳。\n",
        "- `版本前提`：依赖 Flutter 或 SDK 版本，需要先确认技术前提。\n\n",
        "## 快速导航\n\n",
    ]
    lines.extend(render_quick_index(candidates))
    lines.extend(
        [
        "## 二选一冲突规则\n\n",
        ]
    )
    lines.extend(render_pair_table(pairs))
    lines.append("\n")
    lines.extend(render_candidate_sections(candidates))
    return "".join(lines)


def write_csv(candidates: list[RuleCandidate]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "分类",
                "规则",
                "中文释义",
                "上游说明",
                "BAD 示例",
                "GOOD 示例",
                "对立规则",
                "可快速修复",
                "初筛分组",
                "建议讨论方式",
                "会议结论",
                "负责人",
                "备注",
                "来源链接",
            ]
        )
        for candidate in sorted(
            candidates,
            key=lambda item: (
                item.category_label,
                MEETING_BUCKET_ORDER[item.review_bucket],
                item.rule,
            ),
        ):
            writer.writerow(
                [
                    candidate.category_label,
                    candidate.rule,
                    candidate.gloss,
                    candidate.description,
                    candidate.bad_example,
                    candidate.good_example,
                    candidate.opposing_rule,
                    "是" if candidate.quick_fix else "否",
                    candidate.review_bucket,
                    candidate.discussion_suggestion,
                    "待定",
                    "",
                    "",
                    candidate.source_url,
                ]
            )


def write_outputs(candidates: list[RuleCandidate]) -> None:
    OUTPUT_PAGE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PAGE.write_text(render_page(candidates), encoding="utf-8")
    write_csv(candidates)


def main() -> None:
    candidates = parse_candidates(fetch_source())
    write_outputs(candidates)


if __name__ == "__main__":
    main()
