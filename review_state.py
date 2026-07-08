"""
LangGraph 并行审查工作流：Send API 驱动的四路并发
将四个审查工具串联执行虽然简单，但会浪费大量的等待时间，安全扫描等待静态分析完成，风格审查又等待安全扫描完成，端到端的延迟是四者耗时之和。
在 LangGraph 的 Graph API 中，实现并行的核心机制是 Send API，它的设计灵感来源于 Google Pregel 系统中的消息传递模型。
当一个节点返回一个 Send 对象列表时，每个 Send 对象都携带了目标节点名称和一份专属的状态数据，LangGraph 的运行时会在同一个 super-step 中将这些 Send 并发调度到各自的目标节点上执行，所有目标节点执行完毕后状态被合并，然后进入下一个 super-step。
这种 fan-out → fan-in 模式天然适合代码审查场景，因为我们预先知道需要检查哪些维度，且每个维度之间完全独立。

在定义工作流之前，首先要定义状态结构。LangGraph 中使用 TypedDict 描述状态的 schema，每个字段可以指定一个 reducer 函数来控制新值如何与旧值合并。
对于字符串类型的审查结果字段，我们不希望在多次更新中丢失之前的数据，因此需要谨慎选择 reducer。在实际使用中，由于静态分析、安全检查和风格审查各自写入不同的字段（static_result、security_result、style_report），不存在两个节点争抢同一个字段的情况，使用默认的覆盖 reducer 即可。

ReviewState 中定义了六个字段。messages 字段使用 add_messages 作为 reducer，这是 LangGraph 为消息列表预置的归并函数，它不仅会将新消息追加到现有列表末尾，还会根据消息 ID 去重和更新已有消息，确保在并行节点同时返回消息时不会产生重复或冲突。
code 字段存储用户提交的待审查代码，在分发节点中被读取后分发给四个审查节点。checksyntax_result、static_result、security_result 和 style_report 分别接收四个审查节点的输出。最后 final_report 存储汇总生成的完整审查报告。

"""
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class ReviewState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    code: str
    checksyntax_result: str
    static_result: str
    security_result: str
    style_result: str
    final_report: str
