import ast
from _ast import Module

from langchain.tools import tool




@tool
def check_syntax(code: str) -> dict[str, bool | None | dict[str, str | int | None]] | dict[str, bool | Module | None]:
    """对给定的 Python 代码执行语法检查。使用 ast.parse 检查代码语法

    Args:
        code: 待扫描的 Python 源代码字符串
    """
    try:
        tree = ast.parse(code)
        return {"is_valid": True, "tree": tree, "error": None}
    except SyntaxError as e:
        return {
            "is_valid": False,
            "tree": None,
            "error": {
                "message": e.msg,
                "line": e.lineno,
                "offset": e.offset
            }
        }
