"""
将所有组件组装成一个完整的 StateGraph。add_node 注册四个节点，add_conditional_edges 从 dispatch 节点连接到 route_to_analyses 函数。
注意这里的用法，当一个条件边函数返回 Send 列表时，LangGraph 会将其解释为并行调度指令，而不是普通的节点名称路由。add_edge 将三个审查节点各自连接到 generate_report，最后从 generate_report 连接到 END 终止

add_conditional_edges 在这里扮演了一个关键角色。它的第一个参数 "dispatch" 指定了触发条件判断的源节点，第二个参数 route_to_analyses 是一个路由函数，第三个参数 path_map 是一个字符串列表，声明了路由函数可能返回的所有目标节点名称。
当 route_to_analyses 返回 [Send("static_analysis", ...), Send("security_scan", ...), Send("style_check", ...)] 时，LangGraph 不是去匹配 path_map 中的某个值进行单一路由，而是检测到返回值是一个 Send 列表后自动切换到并行调度模式，将三个 Send 分别投递到对应的节点。path_map 在这里的作用是声明所有可能的目标节点，帮助 LangGraph 在编译时验证图结构的完整性和生成正确的可视化图表。

三个审查节点都有一条指向 generate_report 的边，意思是 generate_report 节点有三个入边。
在 LangGraph 的 Pregel 模型中，当一个节点有多个入边时，只有当所有入边的上游节点都在当前 super-step 中完成了执行，该节点才会在下一个 super-step 中被激活。这正是 fan-in 语义的体现，无论三个审查节点各自的执行耗时如何（网络延迟、模型推理时间差异等），报告汇总节点耐心等待最慢的那个完成，然后一次性拿到全部三份结果开始整合。
这种机制保证了汇总报告的完整性，不会出现只有安全检查结果而静态分析结果还为空就开始生成报告的情况。


"""

from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

from distribution_nodes import route_to_analyses, dispatch_analysis
from review_nodes import static_analysis_node, security_scan_node, style_check_node
from sink_nodes import generate_report_node
from review_state import ReviewState

# 构建工作流图
review_builder = StateGraph(ReviewState)

review_builder.add_node("dispatch",dispatch_analysis)
review_builder.add_node("static_analysis",static_analysis_node)
review_builder.add_node("security_scan",security_scan_node)
review_builder.add_node("style_check",style_check_node)
review_builder.add_node("generate_report",generate_report_node)

# 入口边 START -> dispatch
review_builder.add_edge(START,"dispatch")

# 条件边：dispatch 通过 Send 列表 → 三路并行
review_builder.add_conditional_edges(
    "dispatch",
    route_to_analyses,
)

# 三个审查节点完成后 → 报告汇总
review_builder.add_edge("static_analysis", "generate_report")
review_builder.add_edge("security_scan", "generate_report")
review_builder.add_edge("style_check", "generate_report")

# 报告汇总完成 → 结束
review_builder.add_edge("generate_report", END)

# 编译工作流
review_app = review_builder.compile()
display(Image(review_app.get_graph().draw_mermaid_png()))
