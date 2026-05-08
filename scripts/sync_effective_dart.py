#!/usr/bin/env python3

from __future__ import annotations

import re
import urllib.request
from pathlib import Path


BASE_URL = (
    "https://raw.githubusercontent.com/cfug/dart.cn/main/"
    "src/content/effective-dart"
)
SOURCE_PAGES = ["index", "style", "documentation", "usage", "design"]
OUTPUT_DIR = Path("docs/effective-dart")

SITE_VARIABLES = {
    "{{site.dart-api}}": "https://api.dart.dev",
    "{{site.pub-pkg}}": "https://pub.dev/packages",
    "{{site.repo.dart.org}}": "https://github.com/dart-lang",
}

DART_CN_PREFIXES = (
    "/tools/",
    "/language/",
    "/resources/",
    "/null-safety/",
)


def fetch_page(name: str) -> str:
    url = f"{BASE_URL}/{name}.md"
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def normalize_path(path: str) -> str:
    if path.startswith("/effective-dart"):
        return path
    if path.startswith(DART_CN_PREFIXES):
        return f"https://dart.ac.cn{path}"
    return path


def replace_root_links(line: str) -> str:
    line = re.sub(
        r"\]\((/[^)]+)\)",
        lambda match: f"]({normalize_path(match.group(1))})",
        line,
    )
    line = re.sub(
        r"(^\[[^\]]+\]:\s+)(/\S+)",
        lambda match: f"{match.group(1)}{normalize_path(match.group(2))}",
        line,
    )
    line = re.sub(
        r"(^\s*url:\s+)(/\S+)",
        lambda match: f"{match.group(1)}{normalize_path(match.group(2))}",
        line,
    )
    return line


def replace_inline_type_tags(text: str) -> str:
    parts = text.split("`")
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(
            r"<([A-Z][A-Za-z0-9_, ?.]+)>",
            r"`<\1>`",
            parts[index],
        )
    return "`".join(parts)


def normalize_filetree(lines: list[str]) -> list[str]:
    output = ["```text\n"]
    for raw_line in lines:
        if not raw_line.strip():
            continue
        match = re.match(r"(\s*)-\s+(.*)", raw_line.rstrip())
        if not match:
            continue
        indent = len(match.group(1)) // 2
        output.append(f"{'  ' * indent}{match.group(2)}\n")
    output.append("```\n")
    return output


def normalize_code_fence(line: str) -> str:
    stripped = line.strip()
    if stripped == "```":
        return "```\n"

    info = stripped[3:].strip()
    if not info:
        return "```\n"

    language = info.split()[0]
    if language == "plaintext":
        language = "text"
    return f"```{language}\n"


def format_linter_rules(rule_list: str) -> str:
    rules = [f"`{rule.strip()}`" for rule in rule_list.split(",") if rule.strip()]
    return f"> 相关 lints: {', '.join(rules)}\n"


def transform_markdown(content: str) -> str:
    lines = content.splitlines(keepends=True)
    output: list[str] = []
    in_code_block = False
    in_filetree = False
    filetree_buffer: list[str] = []
    in_admonition = False

    for line in lines:
        stripped = line.strip()

        if in_filetree:
            if stripped == "</FileTree>":
                output.extend(normalize_filetree(filetree_buffer))
                in_filetree = False
                filetree_buffer = []
            else:
                filetree_buffer.append(line)
            continue

        if in_admonition:
            if stripped == ":::":  # End of admonition block.
                in_admonition = False
            elif stripped:
                output.append(f"> {line.lstrip()}")
            else:
                output.append(">\n")
            continue

        if stripped.startswith("```"):
            output.append(normalize_code_fence(line))
            in_code_block = not in_code_block
            continue

        if in_code_block:
            output.append(line)
            continue

        if stripped.startswith("<FileTree>"):
            in_filetree = True
            continue

        if stripped.startswith(":::"):
            in_admonition = True
            output.append("> 提示\n")
            continue

        if stripped.startswith("# breadcrumb:") or stripped.startswith("breadcrumb:"):
            continue

        if stripped == "{{site.alert.end}}":
            continue

        if re.match(r"^<\?code-excerpt.*\?>$", stripped):
            continue

        if re.match(r'^<a id="[^"]+"[^>]*></a>$', stripped):
            continue

        linter_match = re.match(
            r"^\{\%\s*render 'linter-rule-mention\.md', rules:'([^']+)'\s*\%\}$",
            stripped,
        )
        if linter_match:
            output.append(format_linter_rules(linter_match.group(1)))
            continue

        if stripped == "{% render 'effective-dart-toc.md' %}":
            output.extend(
                [
                    "- [代码风格](/effective-dart/style)\n",
                    "- [文档](/effective-dart/documentation)\n",
                    "- [用法示例](/effective-dart/usage)\n",
                    "- [API 设计](/effective-dart/design)\n",
                ]
            )
            continue

        line = re.sub(r"\s+\{:#[-\w]+\}\s*$", "", line)

        for old, new in SITE_VARIABLES.items():
            line = line.replace(old, new)

        line = replace_root_links(line)
        line = replace_inline_type_tags(line)
        output.append(line)

    return "".join(output)


def write_pages() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for page in SOURCE_PAGES:
        source = fetch_page(page)
        transformed = transform_markdown(source)
        (OUTPUT_DIR / f"{page}.mdx").write_text(transformed, encoding="utf-8")


def main() -> None:
    write_pages()


if __name__ == "__main__":
    main()
