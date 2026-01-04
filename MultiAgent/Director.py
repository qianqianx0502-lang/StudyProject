from operator import add
from typing import TypedDict, Annotated

from caffe2.contrib.playground.resnetdemo.override_no_test_model_no_checkpoint import checkpoint
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from config import BAILIAN_API_KEY


nodes = ["supervisor", "joke", "travel", "couplet"]

llm = ChatTongyi(
    model="qwen-plus",
    api_key=BAILIAN_API_KEY
)

class State (TypedDict):
    messages: Annotated[list[AnyMessage], add]
    type: str


def other_code(state: State):
    print(">>> other_code")
    writer = get_stream_writer()
    writer({"node", ">>> other_code"})

    return {"messages": [HumanMessage(content="我暂时无法回答这个问题")], "type": "other"}

def supervisor_code(state: State):
    print(">>> supervisor_code")
    writer = get_stream_writer()
    writer({"node", ">>> supervisor_code"})

    # 根据用户的问题，对问题进行分类，分类结果保存到type当中
    prompt = """你是一个专业的客服助手，负责对用户的问题进行分类，并将任务分给其他Agent执行。
                    如果用户的问题是和旅游路线规划相关的，那就返回travel。
                    如果用户的问题是希望讲一个笑话，那就返回 joke 。
                    如果用户的问题是希望对一个对联，那就返回 couplet 。
                    如果是其他的问题，返回 other
                    除了这几个选项外，不要返回任何其他的内容。"""

    prompts = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": state["messages"][0]},
    ]

    if "type" in state:
        writer({"supervisor_step", f"已获得{state['type']} 智能体处理结果"})
        return {"type": END}
    else:
        response = llm.invoke(prompts)
        typeRes = response.content
        writer({"supervisor_step", f"问题分类结果：{typeRes}"})
        if typeRes in nodes:
            return {"type": typeRes}
        else:
            raise ValueError("type is not in nodes")

def joke_code(state: State):
    print(">>> joke_code")
    writer = get_stream_writer()
    writer({"node", ">>> joke_code"})

    return {"messages": [HumanMessage(content="joke_code")], "type": "joke"}

def travel_code(state: State):
    print(">>> travel_code")
    writer = get_stream_writer()
    writer({"node", ">>> travel_code"})

    return {"messages": [HumanMessage(content="travel_code")], "type": "travel"}

def couplet_code(state: State):
    print(">>> couplet_code")
    writer = get_stream_writer()
    writer({"node", ">>> couplet_code"})

    return {"messages": [HumanMessage(content="couplet_code")], "type": "couplet"}

def routing_func(state: State):
    if state["type"] == "travel":
        return "travel_code"
    elif state["type"] == "joke":
        return "joke_code"
    elif state["type"] == "couplet":
        return "couplet_code"
    elif state["type"] == END:
        return END
    else:
        return "other_code"

# 构件图
builder = StateGraph(State)

# 节点
builder.add_node(supervisor_code, "supervisor_code")
builder.add_node(other_code, "other_code")
builder.add_node(joke_code, "joke_code")
builder.add_node(travel_code, "travel_code")
builder.add_node(couplet_code, "couplet_code")

# Edge
builder.add_edge(START, "supervisor_code")
builder.add_conditional_edges("supervisor_code", routing_func, ["travel_code", "joke_code", "couplet_code", "other_code", END])
builder.add_edge("travel_code", "supervisor_code")
builder.add_edge("joke_code", "supervisor_code")
builder.add_edge("couplet_code", "supervisor_code")
builder.add_edge("other_code", "supervisor_code")

# 构建Graph
checkpoint = InMemorySaver()
graph = builder.compile(checkpointer=checkpoint)

if __name__ == "__main__":
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    # for chunk in graph.stream({
    #     "messages": ["给我讲一个郭德纲的笑话"]},
    #     config,
    #     stream_mode="values"):
    #     print(chunk)

    # res = graph.invoke({"messages": ["给我讲个对联"]},
    #                    config,
    #                    stream_mode="values")
    # print(res,res["messages"],res["messages"][-1],res["messages"][-1].content)