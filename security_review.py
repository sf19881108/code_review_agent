import re
from langchain.tools import tool


"""
安全检查工具关注代码中可能存在的安全漏洞。在 Web 应用开发中，SQL 注入和跨站脚本攻击（XSS）是最常见的安全威胁，而硬编码的密钥、密码和令牌则是配置管理中的高危反模式。
这个工具的检测逻辑基于正则模式匹配，虽然在完整性上不如专业的 SAST（静态应用安全测试）工具，但它捕捉的是最普遍、后果最严重的那一类问题。
"""

SQL_INJECTION_PATTERNS = [
    r"(?:execute|cursor)\(\s*[\"'].*%(?:s|d|\(",
    r"(?:execute|cursor)\(\s*f[\"'].*\{",
    r"\.format\(.*\)",
    r"\+.*\"\s*(?:WHERE|SET|VALUES|INTO)",
]

HARDCODED_SECRET_PATTERNS = [
    r"(?:password|passwd|secret|api_key|apikey|token|auth_token)\s*=\s*[\"'][^\"']+[\"']",
    r"(?:private_key|privatekey)\s*=\s*[\"']-{5}BEGIN",
    r"(?:access_key|secret_key)\s*=\s*[\"'][A-Za-z0-9+/]{20,}[\"']",
]

DANGEROUS_FUNCTIONS = ["eval", "exec", "compile", "__import__",
                       "pickle.loads", "yaml.load", "subprocess.call"]


@tool
def security_scan(code: str) -> str:
    """对给定的 Python 代码执行安全漏洞扫描。检测内容包括：SQL 注入风险、
    硬编码的密码/密钥/令牌、危险函数调用（eval/exec/pickle 等）。
    当需要评估代码的安全性时调用此工具。

    Args:
        code: 待扫描的 Python 源代码字符串
    """
    issues = []

    for lineno, line in enumerate(code.splitlines(), start=1):
        # 检测 SQL 注入模式
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    f"[高危] 第 {lineno} 行可能存在 SQL 注入风险："
                    f"`{line.strip()[:60]}...`"
                )
                break
        # 检测硬编码密钥
        for pattern in HARDCODED_SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(
                    f"[高危] 第 {lineno} 行可能存在硬编码密钥："
                    f"`{line.strip()[:60]}...`"
                )
                break
        # 检测危险函数调用
        for func in DANGEROUS_FUNCTIONS:
            if func in line:
                issues.append(
                    f"[高危] 第 {lineno} 行存在危险函数调用："
                    f"`{line.strip()[:60]}...`"
                )
                break

    if issues:
        return (
            f"安全扫描报告\n{'=' * 40}\n"
            f"发现 {len(issues)} 个安全问题：\n" +
            "\n".join(issues)
        )
    return "安全扫描报告\n" + "=" * 40 + "\n未发现明显的安全漏洞。"
