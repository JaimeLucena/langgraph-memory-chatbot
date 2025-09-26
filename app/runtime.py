from __future__ import annotations
from .graph import build_graph

# Compiled instances; reused across HTTP calls
graphs = {
    "temporary": build_graph("temporary"),
    "persistent": build_graph("persistent"),
}
