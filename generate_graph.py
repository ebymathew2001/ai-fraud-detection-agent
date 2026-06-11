"""
visualize_graph.py
==================
Generates and saves the LangGraph agent flow as a PNG image.

RUN:  python visualize_graph.py

Output: graph.png in root folder
"""

from agent.graph import build_graph

graph_image = build_graph().compile().get_graph().draw_mermaid_png()

with open("graph.png", "wb") as f:
    f.write(graph_image)

print(" Graph image saved to graph.png")