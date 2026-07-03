"""
分发节点是整个并行机制的核心。它在读取用户代码后，不直接执行任何审查逻辑，而是返回三个 Send 对象，每个对象都指定了目标节点名称和该节点所需的专属状态。LangGraph 的运行时接收到这三个 Send 后，会在同一个 super-step 中将它们并行调度出去。

route_to_analyses 函数的返回值类型是 list[Send]，这是 LangGraph 识别并行分发的关键标记。当函数返回一个 Send 列表时，LangGraph 不会像处理普通字典返回值那样尝试将结果合并到全局状态，而是将列表中的每个 Send 视为一个独立的调度指令。
每个 Send 构造函数接收两个参数，第一个参数 "static_analysis"（或 "security_scan"、"style_check"）是之前通过 add_node 注册的节点名称，第二个参数 {"code": code} 是一个部分状态字典，
这个字典会在目标节点开始执行前被合并到该节点可见的状态视图中。这意味着三个审查节点各自都会看到 state["code"] 的值，但它们互相之间看不到彼此的中间输出，直到所有节点执行完毕并将结果写回全局状态后，下
一阶段的报告汇总节点才能同时读到三份审查结果。

"""

from langgraph.types import Send

from review_state import ReviewState


def dispatch_analysis(state: ReviewState) -> dict:
    """分发节点：打印分发信息，实际路由在 conditional_edges 中处理"""
    print(f"[分发] 代码长度 {len(state['code'])} 字符，开始并行分发...")
    return {}

def route_to_analyses(state: ReviewState) -> list[Send]:
    """路由函数：通过 Send 将代码并行派发到三个审查节点"""
    code = state["code"]
    return [
        Send("static_analysis", {"code": code}),
        Send("security_scan", {"code": code}),
        Send("style_check", {"code": code}),
    ]
