from typing import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.constants import END, START
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache #是langgraph中的,⽽不是langchain中的。


class InputState(TypedDict):
    user_id: str
    number: int

def node1(state: InputState, config: RunnableConfig) -> InputState:
    user_id = config["configurable"]["user_id"]
    return {"number":state["number"] + 1, "user_id":user_id}

graph = (StateGraph(InputState)
        .add_node("node1", node1, cache_policy=CachePolicy(ttl=5))    # 添加节点1，Node缓存5秒
        .add_edge(START, "node1")    # 补充：起始节点 -> node1
        .add_edge("node1", END)    # node1 -> 结束节点
        .compile(cache=InMemoryCache())    # 编译状态图，不加cache=InMemoryCache()则缓存无效
)
if __name__ == "__main__":
    initial_state = {"user_id": "user_01", "number": 5}

    final_state = graph.invoke(
        input=initial_state,
        config={"configurable": {"user_id": "user_02"}}
    )
    print(f"final_state的值：{final_state}")
    # final_state的值：{'user_id': 'user_02', 'number': 6}
