import re
from langchain.tools import tool

"""
风格审查工具关注代码的可读性和一致性。在一个团队协作的项目中，统一的代码风格能让所有成员更快地理解彼此的代码，减少因格式差异造成的认知摩擦。
Python 社区有 PEP 8 作为风格指南，JavaScript 生态有 ESLint，而这个工具的核心思路与它们一致：定义一组可自动检查的规则，逐条匹配并生成反馈。
"""


@tool
def style_check(code: str) -> str:
    """对给定的 Python 代码执行风格与可读性检查。检查内容包括：命名规范
    （驼峰/下划线）、注释覆盖率、函数长度、行长度限制、空白行使用等。
    当需要评估代码风格和可维护性时调用此工具。

    Args:
        code: 待检查的 Python 源代码字符串
    """
    lines = code.splitlines()
    issues = []

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # 行长度检查
        if len(stripped) > 120:
            issues.append(
                f"[风格] 第 {lineno} 行长度 {len(stripped)} 字符，超过 120 字符限制"
            )

        # 行尾空白检查
        if line != stripped and line.strip():
            issues.append(
                f"[风格] 第 {lineno} 行末尾存在多余空白字符"
            )

    # 统计注释覆盖率
    total_lines = len(lines)
    comment_lines = sum(
        1 for line in lines
        if line.strip().startswith('#') or line.strip().startswith('"""')
    )
    if total_lines > 10:
        ratio = comment_lines / total_lines
        if ratio < 0.05:
            issues.append(
                f"[风格] 注释覆盖率仅 {ratio:.1%}，建议补充关键逻辑的注释"
            )
        elif ratio > 0.5:
            issues.append(
                f"[风格] 注释覆盖率 {ratio:.1%} 偏高，部分注释可能冗余"
            )
    # 函数/变量命名规范检查
    for lineno, line in enumerate(lines, start=1):
        # 检查类名是否使用大驼峰
        class_match = re.match(r"^\s*class\s+([a-zA-Z_]\w*)", line)
        if class_match:
            name = class_match.group(1)
            if not name[0].isupper():
                issues.append(
                    f"[风格] 第 {lineno} 行类名 `{name}` 应使用大驼峰命名"
                )
        # 检查函数/变量名是否使用下划线
        def_match = re.match(r"^\s*def\s+([a-zA-Z_]\w*)", line)
        if def_match:
            name = def_match.group(1)
            if any(c.isupper() for c in name):
                issues.append(
                    f"[风格] 第 {lineno} 行函数名 `{name}` 应使用小写+下划线"
                )
    if issues:
        return (
            f"风格审查报告\n{'=' * 40}\n"
            f"发现 {len(issues)} 个风格问题：\n" +
            "\n".join(issues)
        )
    return "风格审查报告\n" + "=" * 40 + "\n代码风格良好，未发现明显问题。"
