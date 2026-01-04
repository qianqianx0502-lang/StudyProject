from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph


class InputState(TypedDict):
    user_input: str
    list_input: Annotated[list[int], add]    # Annotated：为原始类型附加任意元数据，不改变类型本身的本质

def node1(state: InputState):
    return {"list_input": [123], "user_input": "node1"}

def node2(state: InputState):
    return {"user_input": "node2"}

graph = (StateGraph(InputState)
        .add_node("node1", node1)    # 添加节点1
        .add_node("node2", node2)    # 添加节点2
        .set_entry_point("node1")
        .add_edge("node1", "node2")
        .compile()    # 编译状态图
)
if __name__ == "__main__":
    initial_state = {"user_input": "测试输入：", "list_input": [1, 2, ]}

    final_state = graph.invoke(initial_state)
    print(f"final_state的值：{final_state}")

    graph_structure = graph.get_graph()

    png_data = graph_structure.draw_mermaid_png()
    # 保存到本地文件
    with open("langgraph_flow3.png", "wb") as f:
        f.write(png_data)