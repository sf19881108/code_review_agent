"""
接下来定义三个审查节点的入口函数。这些函数并不是直接调用前面定义的 @tool 函数，而是使用 LLM 对代码进行审查分析。
两种方式都是可行的，直接调用工具函数可以绕过模型推理环节，适用于规则明确、不需要语义理解的检查（如行长度统计），而让 LLM 执行审查则可以挖掘那些正则无法覆盖的问题，例如不合理的架构设计、潜在的性能瓶颈和不符合最佳实践的用法。
这里采用的方法是每个审查节点内部使用 LLM 进行专项分析，同时工具函数中核心的正则匹配逻辑可以按需集成进来，实现规则引擎与大模型的双重把关。

三个审查节点的结构对称而统一，每个节点都从 state["code"] 中读取同一份待审查代码，通过 SystemMessage 设定一个高度专注的角色提示词，将 LLM 的行为精准约束在对应的审查维度上。
静态分析节点的系统提示词强调了结构质量、圈复杂度、函数体长度和嵌套层次等可量化的指标，安全检查节点的提示词则列出具体的漏洞类型和危险函数名称，风格审查节点要求模型关注命名、注释、魔法数字和格式一致性。这种"同一模型、不同角色"的分工方式是 LLM 应用中的一个典型设计模式，通过变换系统提示词中设定的专家身份和分析框架，同一个模型实例可以在不同的节点中扮演完全不同的审查者角色。

三个节点的返回值分别是{"checksyntax_result"}、 {"static_result": ...}、{"security_result": ...} 和 {"style_result": ...}，每个节点只写回自己对应的状态字段，不触碰其他字段。LangGraph 的默认 reducer 会用新值直接覆盖旧值，由于四个节点写入的是不同的字段，不存在冲突，整个合并过程对开发者完全透明。


"""
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage

from model import llm
from review_state import ReviewState
from security_review import security_scan
from static_review import static_analysis
from style_review import style_check
from checksyntax_review import check_syntax




def check_syntax_node(state: ReviewState) -> dict:
    """语法检查节点：对大模型发送代码，让它检查语法错误"""
    print("[语法检查] 开始检查...")
    system_prompt = SystemMessage(
        content=(
            "你是一位资深 Python 代码语法分析师。请分析以下代码的语法问题。"
            "给出合理的修改建议。"
        ))
    agent_checksyntax = create_agent(
        model=llm,
        tools=[check_syntax],
        system_prompt=system_prompt,
    )
    response = agent_checksyntax.invoke(
        {"messages": [{"role": "user", "content": state["code"]}]}
    )
    print("[语法检查] 完成")
    return {"checksyntax_result": response}



def static_analysis_node(state: ReviewState) -> dict:
    """静态分析节点：对大模型发送代码，让它从结构和复杂度角度分析"""
    print("[静态分析] 开始分析...")
    # response = llm.invoke(
    #     [
    #         SystemMessage(
    #             content=(
    #                 "你是一位资深 Python 代码结构分析师。请分析以下代码的结构质量。"
    #                 "关注：函数和类的组织方式、圈复杂度高的函数、过长的函数体、"
    #                 "嵌套层次过深的控制流、重复代码迹象、以及缺少文档字符串的公开接口。"
    #                 "请给出具体的行号引用和可操作的改进建议。"
    #             )
    #         ),
    #         HumanMessage(content=state["code"])
    #     ]
    # )
    system_prompt = SystemMessage(
                content=(
                    "你是一位资深 Python 代码结构分析师。请分析以下代码的结构质量。"
                    "关注：函数和类的组织方式、圈复杂度高的函数、过长的函数体、"
                    "嵌套层次过深的控制流、重复代码迹象、以及缺少文档字符串的公开接口。"
                    "请给出具体的行号引用和可操作的改进建议。"
                ))
    agent_static = create_agent(
        model=llm,
        tools=[static_analysis],
        system_prompt=system_prompt,
    )
    response = agent_static.invoke(
        {"messages": [{"role": "user", "content": state["code"]}]}
    )
    print("[静态分析] 完成")
    return {"static_result": response}


def security_scan_node(state: ReviewState) -> dict:
    """安全检查节点：对大模型发送代码，让它从安全角度进行审查"""
    print("[安全检查] 开始扫描...")
    system_prompt = SystemMessage(
                content=(
                    "你是一位资深应用安全专家。请审查以下 Python 代码的安全问题。"
                    "重点检测：SQL 注入、命令注入、跨站脚本（XSS）、路径遍历、"
                    "不安全的反序列化（pickle/yaml.load）、硬编码的敏感信息、"
                    "不安全的加密算法（MD5/SHA1 用于密码哈希）、缺少权限校验的操作。"
                    "请按严重程度排序，给出具体行号和修复方案。"
                )
            )
    agent_security = create_agent(
        model=llm,
        tools=[security_scan],
        system_prompt=system_prompt,
    )
    response = agent_security.invoke(
        {"messages": [{"role": "user", "content": state["code"]}]}
    )
    print("[安全检查] 完成")
    return {"security_result": response}


def style_check_node(state: ReviewState) -> dict:
    """风格审查节点：对大模型发送代码，让它从可读性和风格角度进行审查"""
    print("[风格审查] 开始检查...")
    system_prompt = SystemMessage(
                content=(
                    "你是一位 Python 代码风格审查员。请审查以下代码的编码风格和可读性。"
                    "关注：PEP 8 合规性、命名规范（类用大驼峰、函数和变量用小写下划线）、"
                    "注释和文档字符串的质量与覆盖程度、魔法数字的使用、"
                    "过长的代码行（超过 120 字符）、不一致的缩进或引号风格。"
                    "请给出具体的行号引用和修改建议。"
                )
            )

    agent_style = create_agent(
        model=llm,
        tools=[style_check],
        system_prompt=system_prompt,
    )
    response = agent_style.invoke(
        {"messages": [{"role": "user", "content": state["code"]}]}
    )
    print("[风格审查] 完成")
    return {"style_result": response}


