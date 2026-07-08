"""
实现静态分析工具。在真实的 CI/CD 环境中，静态分析通常会对接 pylint、flake8、SonarQube 等成熟的第三方工具，
这些工具能够解析 AST、检测代码异味和计算圈复杂度。
在这个教学实现中，我们使用 Python 标准库的 ast 模块对代码进行真实的结构分析，
同时保留了对接外部工具的接口注释，方便读者在实际项目中替换为生产级方案。


优化建议：
将单一函数拆分为 5 个职责明确的小函数：

calculate_cyclomatic_complexity() - 计算圈复杂度
detect_bare_except() - 检测裸 except
analyze_functions() - 分析函数复杂度和长度
collect_classes() - 收集类名
generate_report() - 生成格式化报告
"""
import ast
from langchain.tools import tool

COMPLEXITY_THRESHOLD = 10    # 圈复杂度阈值
MAX_FUNCTION_LINES = 50      # 函数体最大行数
MAX_CODE_SIZE = 1024 * 1024  # 最大代码大小 1MB限制

@tool
def static_analysis(code: str) -> str:
    """对给定的 Python 代码执行静态结构分析。检查内容包括：函数与类的数量、
    圈复杂度估算、代码行数统计、潜在的空 except 子句和过长的函数体。
    当需要评估代码的结构质量和复杂度时调用此工具。

    Args:
        code: 待分析的 Python 源代码字符串
    """
    try:
        if len(code) > MAX_CODE_SIZE:
            return f"[静态分析] 代码过大..."

        tree = ast.parse(code)
    except SyntaxError as e:
        return f"[静态分析] 分析失败，无法继续分析."

    functions = []
    classes = []
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
            # 估算圈复杂度：统计分支节点数量
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
            if complexity > COMPLEXITY_THRESHOLD:
                issues.append(
                    f"函数 `{node.name}` 圈复杂度为 {complexity}，建议拆分"
                )
            if len(node.body) > MAX_FUNCTION_LINES:
                issues.append(
                    f"函数 `{node.name}` 体长 {len(node.body)} 行，过长"
                )
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(
                    f"第 {node.lineno} 行存在裸 except，应捕获具体异常类型"
                )
    total_lines = len(code.splitlines())
    summary = (
        f"静态分析报告\n"
        f"{'=' * 40}\n"
        f"代码总行数：{total_lines}\n"
        f"函数数量：{len(functions)}（{', '.join(functions) if functions else '无'}）\n"
        f"类数量：{len(classes)}（{', '.join(classes) if classes else '无'}）\n"
        f"发现问题：{len(issues)} 个\n"
    )
    if issues:
        summary += "\n".join(f"  - {issue}" for issue in issues)
    else:
        summary += "未发现明显的结构问题。"
    return summary
