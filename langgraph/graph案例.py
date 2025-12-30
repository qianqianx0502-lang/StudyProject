from typing import TypedDict
from langgraph.constants import END, START
from langgraph.graph import StateGraph

class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class GraphState(TypedDict):
    user_input: str
    graph_output: str

def node1(state: InputState) -> OutputState:
    return {"graph_output": state["user_input"] + "这个是节点1"}

# 构件图
builder = StateGraph(GraphState)

# 1. 添加节点到状态图（指定节点名称和对应的处理函数）
builder.add_node("node1", node1)

# 2. 添加起始节点到node1的边（START -> node1）
builder.add_edge(START, "node1")

# 3. 添加node1到结束节点的边（node1 -> END）
builder.add_edge("node1", END)

# 4. 编译状态图，生成可运行的图实例
graph = builder.compile()

if __name__ == "__main__":
    initial_state = {"user_input": "测试输入："}

    # 运行图（两种方式：stream流式输出 / invoke直接获取最终结果）
    # 方式1：invoke直接获取最终状态
    final_state = graph.invoke(initial_state)
    print(f"final_state的值：{final_state}")

    # 方式2：stream流式遍历执行过程
    for step in graph.stream(initial_state):
        for node_name, node_output in step.items():
            print(f"节点名称：{node_name}， 节点输出：{node_output}")

    graph_structure = graph.get_graph()

    png_data = graph_structure.draw_mermaid_png()
    # 保存到本地文件
    with open("langgraph_flow.png", "wb") as f:
        f.write(png_data)