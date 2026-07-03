"""
实现报告汇总节点。这个节点在三个审查节点的输出全部就绪后运行，负责将分散的审查结果整合为一篇完整的、有优先级排序的审查报告
generate_report_node 是工作流的最后一个业务节点，它在三个并行审查节点全部完成后执行。
函数内部将 static_result、security_result 和 style_report 三个字段的值拼接为一段完整的上下文，然后以"代码审查主管"的角色提示词要求 LLM 对三份独立的审查结果做综合处理。
LLM 在这里承担的不是审查任务，而是信息整合与优先级判断任务，它需要从三份报告各自列举的数十项发现中识别出哪些是必须立即修复的高危安全问题，哪些是影响长期可维护性的结构性问题，哪些是锦上添花的风格建议，然后按照合理的优先级重新排序。
系统提示词中明确规定了报告的五段式结构（总体评价、安全发现、结构发现、风格发现、优先级建议），这让每次生成的报告格式保持稳定，便于在 CI/CD 系统中做自动化解析或嵌入 Pull Request 评论。

"""

from langchain_core.messages import SystemMessage, HumanMessage

from model import llm
from review_state import ReviewState

REPORT_SYSTEM_PROMPT = """你是一位资深的代码审查主管。请你将以下三个维度的审查结果整合为一份完整、专业的代码审查报告。

报告应包含以下部分：
1. **总体评价**：一段简短的总结，概述代码的整体质量水平和最突出的问题。
2. **安全审查发现**（按严重程度降序）：列出安全问题、风险等级和修复方案。
3. **结构分析发现**：列出代码结构、复杂度和组织方式上的问题与建议。
4. **风格审查发现**：列出命名、格式、注释等风格问题与改进方案。
5. **改进优先级建议**：按紧急程度给出修复优先级排序。

请使用清晰的 Markdown 格式，问题引用要包含具体的行号或函数名。语言使用中文。
"""


def generate_report_node(state: ReviewState) -> dict:
    """报告汇总节点：接收三个审查结果，生成综合报告"""
    print("[报告生成] 汇总三个审查结果...")
    context = (
        f"## 静态分析结果\n\n{state['static_result']}\n\n"
        f"## 安全检查结果\n\n{state['security_result']}\n\n"
        f"## 风格审查结果\n\n{state['style_report']}"
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=REPORT_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=(
                    f"请基于以下审查发现，生成一份综合代码审查报告：\n\n{context}"
                )
            ),
        ]
    )
    print("[报告生成] 完成")
    return {"final_report": response.content}
