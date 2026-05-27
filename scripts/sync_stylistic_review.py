#!/usr/bin/env python3

from __future__ import annotations

import csv
import html
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
OUTPUT_HTML = Path("docs/assets/stylistic-review.html")

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


def category_specificity(category_label: str) -> tuple[int, int]:
    return (category_label.count("/"), len(category_label))


def merge_candidates(items: list[RuleCandidate]) -> RuleCandidate:
    preferred_category = max(items, key=lambda item: category_specificity(item.category_label))
    description = max((item.description for item in items), key=len)
    quick_fix = any(item.quick_fix for item in items)
    opposing_rule = next((item.opposing_rule for item in items if item.opposing_rule), "")
    review_bucket = classify_rule(preferred_category.rule, opposing_rule, quick_fix)
    bad_example = next((item.bad_example for item in items if item.bad_example), "")
    good_example = next((item.good_example for item in items if item.good_example), "")

    return RuleCandidate(
        section=preferred_category.section,
        subsection=preferred_category.subsection,
        category_label=preferred_category.category_label,
        rule=preferred_category.rule,
        description=description,
        gloss=preferred_category.gloss,
        quick_fix=quick_fix,
        opposing_rule=opposing_rule,
        review_bucket=review_bucket,
        discussion_suggestion=discussion_suggestion(review_bucket),
        source_url=preferred_category.source_url,
        bad_example=bad_example,
        good_example=good_example,
    )


def deduplicate_candidates(candidates: list[RuleCandidate]) -> list[RuleCandidate]:
    grouped: dict[str, list[RuleCandidate]] = {}
    order: list[str] = []
    for candidate in candidates:
        if candidate.rule not in grouped:
            grouped[candidate.rule] = []
            order.append(candidate.rule)
        grouped[candidate.rule].append(candidate)

    return [merge_candidates(grouped[rule]) for rule in order]


def format_code_snippet(snippet: str) -> str:
    collapsed = " ".join(line.strip() for line in snippet.splitlines() if line.strip())
    collapsed = re.sub(r"\s+", " ", collapsed).strip()
    if len(collapsed) > 110:
        return collapsed[:107].rstrip() + "..."
    return collapsed


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

    return deduplicate_candidates(candidates)


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


def render_pair_list(pairs: list[tuple[RuleCandidate, RuleCandidate]]) -> list[str]:
    lines: list[str] = []
    for left, right in pairs:
        lines.extend(
            [
                f"### `{left.rule}` vs `{right.rule}`\n\n",
                f"- 分类：{left.category_label}\n",
                f"- 方案 A：[`{left.rule}`]({left.source_url})\n",
                f"- 方案 B：[`{right.rule}`]({right.source_url})\n",
                f"- 中文释义：A 为“{left.gloss}” B 为“{right.gloss}”\n",
                f"- 上游取舍点：{left.description} / {right.description}\n",
                "- 会议结论：`待定`\n",
                "- 备注：待填写\n\n",
            ]
        )
        if left.bad_example or left.good_example:
            lines.append("**参考示例**\n\n")
            lines.extend(render_example_blocks(left))
        else:
            lines.append("> 参考示例：上游文档未提供，讨论时可结合项目代码补充。\n\n")
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
            lines.append(f"### `{candidate.rule}`\n\n")
            lines.append(f"- 中文释义：{candidate.gloss}\n")
            lines.append(f"- 上游说明：{candidate.description}\n")
            lines.append("- 当前状态：`待评审`\n")
            lines.append(f"- 初筛分组：`{candidate.review_bucket}`\n")
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

    return "".join(
        [
            "---\n",
            "title: 团队规范：风格候选规则评审\n",
            "description: 使用独立 HTML 页面进行逐条评审，评审完成后再沉淀为正式团队规范。\n",
            "prevpage:\n",
            "  url: /team-guidelines/figma-dev-mode\n",
            "  title: Figma 开发操作\n",
            "---\n\n",
            "<!-- 由 scripts/sync_stylistic_review.py 自动生成。 -->\n\n",
            "# 团队规范：风格候选规则评审\n\n",
            "这部分改为使用独立 HTML 页面进行逐条评审，避免 `docs.page` 的 MDX bundling 对复杂评审结构产生限制。\n\n",
            f"- 打开 HTML 评审页：[风格候选规则评审 HTML](/assets/stylistic-review.html)\n",
            f"- 下载 CSV：[stylistic-rule-review.csv](/assets/stylistic-rule-review.csv)\n",
            f"- 上游来源：[saropa_lints / README_STYLISTIC.md]({SOURCE_BLOB_URL})\n",
            f"- 最近一次同步日期：`{generated_at}`\n\n",
            "## 当前统计\n\n",
            f"- 总候选规则：`{len(candidates)}`\n",
            f"- 二选一规则：`{counts['二选一']}` 条，对应 `{len(pairs)}` 组冲突项\n",
            f"- 低成本候选：`{counts['低成本候选']}` 条\n",
            f"- 通用候选：`{counts['通用候选']}` 条\n",
            f"- 项目/业务相关：`{counts['项目/业务相关']}` 条\n",
            f"- 版本前提：`{counts['版本前提']}` 条\n\n",
            "## 评审建议\n\n",
            "1. 会前在 HTML 页面里逐条记录 `采纳 / 不采纳 / 试运行 / 暂缓` 倾向。\n",
            "2. 会议中优先讨论 `二选一` 冲突规则和高争议规则。\n",
            "3. 评审结束后，再把最终结论整理回正式的 `docs.page` 规范页。\n",
        ]
    )


def render_html_review(candidates: list[RuleCandidate]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    counts = bucket_counts(candidates)
    pairs = unique_opposing_pairs(candidates)
    grouped: dict[str, list[RuleCandidate]] = {}
    order: list[str] = []
    for candidate in candidates:
        if candidate.category_label not in grouped:
            grouped[candidate.category_label] = []
            order.append(candidate.category_label)
        grouped[candidate.category_label].append(candidate)

    nav_items = []
    for category in order:
        nav_items.append(f'<li><a href="#{html.escape(category)}">{html.escape(category)}</a></li>')

    pair_blocks: list[str] = []
    for left, right in pairs:
        example_html = ""
        if left.bad_example or left.good_example:
            blocks = []
            if left.bad_example:
                blocks.append(
                    "<div class='example-block'><div class='example-title'>BAD</div><pre><code>"
                    + html.escape(left.bad_example.rstrip())
                    + "</code></pre></div>"
                )
            if left.good_example:
                blocks.append(
                    "<div class='example-block'><div class='example-title'>GOOD</div><pre><code>"
                    + html.escape(left.good_example.rstrip())
                    + "</code></pre></div>"
                )
            example_html = "<div class='examples'>" + "".join(blocks) + "</div>"
        else:
            example_html = "<p class='muted'>上游文档未提供示例，建议会议中结合项目代码补充。</p>"

        pair_blocks.append(
            f"""
            <section class="pair-card">
              <h3>{html.escape(left.rule)} vs {html.escape(right.rule)}</h3>
              <ul>
                <li><strong>分类：</strong>{html.escape(left.category_label)}</li>
                <li><strong>方案 A：</strong><a href="{html.escape(left.source_url)}">{html.escape(left.rule)}</a></li>
                <li><strong>方案 B：</strong><a href="{html.escape(right.source_url)}">{html.escape(right.rule)}</a></li>
                <li><strong>中文释义：</strong>A 为“{html.escape(left.gloss)}” B 为“{html.escape(right.gloss)}”</li>
                <li><strong>上游取舍点：</strong>{html.escape(left.description)} / {html.escape(right.description)}</li>
                <li><strong>会议结论：</strong><span class="decision">待定</span></li>
                <li><strong>备注：</strong>待填写</li>
              </ul>
              {example_html}
            </section>
            """
        )

    category_blocks: list[str] = []
    for category in order:
        cards: list[str] = []
        category_rules = sorted(grouped[category], key=lambda item: (MEETING_BUCKET_ORDER[item.review_bucket], item.rule))
        for candidate in category_rules:
            if candidate.bad_example or candidate.good_example:
                example_parts = []
                if candidate.bad_example:
                    example_parts.append(
                        "<div class='example-block'><div class='example-title'>BAD</div><pre><code>"
                        + html.escape(candidate.bad_example.rstrip())
                        + "</code></pre></div>"
                    )
                if candidate.good_example:
                    example_parts.append(
                        "<div class='example-block'><div class='example-title'>GOOD</div><pre><code>"
                        + html.escape(candidate.good_example.rstrip())
                        + "</code></pre></div>"
                    )
                example_html = "<div class='examples'>" + "".join(example_parts) + "</div>"
            else:
                example_html = "<p class='muted'>上游文档未提供示例，建议会议中结合项目代码补充。</p>"

            opposing_html = (
                f"<li><strong>对立规则：</strong><a href='#{html.escape(candidate.opposing_rule)}'>{html.escape(candidate.opposing_rule)}</a></li>"
                if candidate.opposing_rule
                else ""
            )
            cards.append(
                f"""
                <article class="rule-card" id="{html.escape(candidate.rule)}">
                  <div class="card-head">
                    <h3>{html.escape(candidate.rule)}</h3>
                    <div class="meta">
                      <span class="bucket bucket-{html.escape(candidate.review_bucket)}">{html.escape(candidate.review_bucket)}</span>
                      <span class="decision">待评审</span>
                    </div>
                  </div>
                  <ul>
                    <li><strong>中文释义：</strong>{html.escape(candidate.gloss)}</li>
                    <li><strong>上游说明：</strong>{html.escape(candidate.description)}</li>
                    <li><strong>快速修复：</strong>{'是' if candidate.quick_fix else '否'}</li>
                    <li><strong>建议讨论方式：</strong>{html.escape(candidate.discussion_suggestion)}</li>
                    <li><strong>上游链接：</strong><a href="{html.escape(candidate.source_url)}">查看原始规则</a></li>
                    {opposing_html}
                  </ul>
                  <div class="decision-block">
                    <div><strong>评审记录模板</strong></div>
                    <ul>
                      <li>当前结论：待评审</li>
                      <li>会议决定：采纳 / 不采纳 / 试运行 / 暂缓</li>
                      <li>结论理由：待填写</li>
                      <li>负责人：待填写</li>
                      <li>后续动作：待填写</li>
                    </ul>
                  </div>
                  {example_html}
                </article>
                """
            )

        category_blocks.append(
            f"""
            <section class="category" id="{html.escape(category)}">
              <h2>{html.escape(category)}</h2>
              <p class="muted">本分类共 {len(category_rules)} 条规则，建议按“二选一 -> 低成本候选 -> 其他”的顺序讨论。</p>
              {''.join(cards)}
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>团队规范：风格候选规则评审</title>
    <style>
      :root {{
        --bg: #f4f1ea;
        --panel: #fffdf8;
        --ink: #1f2937;
        --muted: #6b7280;
        --line: #e5ddd0;
        --accent: #1d4ed8;
        --good: #15803d;
        --warn: #b45309;
        --bad: #b91c1c;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "PingFang SC", "Noto Sans SC", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(29, 78, 216, 0.08), transparent 28%),
          linear-gradient(180deg, #f7f3eb 0%, #f2eee6 100%);
      }}
      a {{ color: var(--accent); text-decoration: none; }}
      a:hover {{ text-decoration: underline; }}
      .page {{
        max-width: 1160px;
        margin: 0 auto;
        padding: 32px 20px 80px;
      }}
      .hero, .summary, .nav, .pairs, .category {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: 0 18px 50px rgba(31, 41, 55, 0.06);
        padding: 24px;
        margin-bottom: 20px;
      }}
      .hero h1 {{ margin: 0 0 12px; font-size: 32px; }}
      .hero p, .muted {{ color: var(--muted); }}
      .summary-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
      }}
      .summary-item {{
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        background: #fffaf2;
      }}
      .summary-item strong {{
        display: block;
        font-size: 24px;
        margin-top: 8px;
      }}
      .nav ul {{ margin: 0; padding-left: 18px; columns: 2; }}
      .nav li {{ margin: 6px 0; }}
      .pair-card, .rule-card {{
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
        background: #fffefb;
        margin-top: 16px;
      }}
      .card-head {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }}
      .card-head h3, .pair-card h3 {{ margin: 0; }}
      .meta {{ display: flex; gap: 8px; flex-wrap: wrap; }}
      .bucket, .decision {{
        display: inline-block;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 700;
      }}
      .bucket-二选一 {{ background: rgba(239, 68, 68, 0.12); color: var(--bad); }}
      .bucket-低成本候选 {{ background: rgba(59, 130, 246, 0.12); color: var(--accent); }}
      .bucket-通用候选 {{ background: rgba(34, 197, 94, 0.12); color: var(--good); }}
      .bucket-项目\/业务相关 {{ background: rgba(245, 158, 11, 0.14); color: var(--warn); }}
      .bucket-版本前提 {{ background: rgba(20, 184, 166, 0.12); color: #0f766e; }}
      .decision {{ background: rgba(107, 114, 128, 0.14); color: #4b5563; }}
      ul {{ margin: 12px 0 0; padding-left: 18px; }}
      li {{ margin: 6px 0; }}
      .decision-block {{
        margin-top: 14px;
        border-top: 1px dashed var(--line);
        padding-top: 14px;
      }}
      .examples {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
        margin-top: 16px;
      }}
      .example-block {{
        border: 1px solid var(--line);
        border-radius: 16px;
        background: #faf6ef;
        overflow: hidden;
      }}
      .example-title {{
        padding: 10px 14px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.04em;
        border-bottom: 1px solid var(--line);
        background: #fff8ec;
      }}
      pre {{
        margin: 0;
        padding: 14px;
        overflow: auto;
        font-size: 13px;
        line-height: 1.55;
      }}
      code {{ font-family: "SFMono-Regular", "JetBrains Mono", monospace; }}
      @media (max-width: 720px) {{
        .nav ul {{ columns: 1; }}
        .page {{ padding: 20px 14px 60px; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="hero">
        <h1>团队规范：风格候选规则评审</h1>
        <p>这份 HTML 页面用于团队会前预读和会议逐条评审，规则名称与上游 lint id 保持一致，评审结束后再整理为正式的 docs.page 规范页面。</p>
        <p>
          <a href="{html.escape(SOURCE_BLOB_URL)}">查看上游 README</a>
          · <a href="/assets/stylistic-rule-review.csv">下载 CSV</a>
          · 最近同步：{generated_at}
        </p>
      </section>
      <section class="summary">
        <h2>初筛统计</h2>
        <div class="summary-grid">
          <div class="summary-item">总候选规则<strong>{len(candidates)}</strong></div>
          <div class="summary-item">二选一规则<strong>{counts['二选一']}</strong></div>
          <div class="summary-item">冲突组数<strong>{len(pairs)}</strong></div>
          <div class="summary-item">低成本候选<strong>{counts['低成本候选']}</strong></div>
          <div class="summary-item">通用候选<strong>{counts['通用候选']}</strong></div>
          <div class="summary-item">项目/业务相关<strong>{counts['项目/业务相关']}</strong></div>
          <div class="summary-item">版本前提<strong>{counts['版本前提']}</strong></div>
        </div>
      </section>
      <section class="nav">
        <h2>快速导航</h2>
        <ul>{''.join(nav_items)}</ul>
      </section>
      <section class="pairs">
        <h2>二选一冲突规则</h2>
        <p class="muted">会议中优先讨论这些必须成对取舍的规则。</p>
        {''.join(pair_blocks)}
      </section>
      {''.join(category_blocks)}
    </main>
  </body>
</html>
"""


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
    OUTPUT_HTML.write_text(render_html_review(candidates), encoding="utf-8")
    write_csv(candidates)


def main() -> None:
    candidates = parse_candidates(fetch_source())
    write_outputs(candidates)


if __name__ == "__main__":
    main()
