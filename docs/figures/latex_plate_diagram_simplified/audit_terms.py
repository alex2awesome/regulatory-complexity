"""Check that every model node has exactly one glossary entry (stdlib only)."""
from collections import Counter
from pathlib import Path
import re

root = Path(__file__).resolve().parent
plate = (root / "plate_diagram.tex").read_text()
article = (root / "generative_model.tex").read_text()
nodes = [name for style, name in re.findall(r"\\node\[([^]]+)\]\s*\((\w+)\)", plate)
         if style in {"latent", "obs", "wide", "hyper", "derived"} and not name.startswith("legend")]
entries = re.findall(r"\\entry\{(\w+)\}", article)
assert Counter(nodes) == Counter(entries), (Counter(nodes) - Counter(entries), Counter(entries) - Counter(nodes))
assert all(n == 1 for n in Counter(nodes).values()), "Duplicate node/glossary IDs"
edges = []
for command in re.findall(r"\\draw\[ed\].*?;", plate):
    names = re.findall(r"\(([A-Za-z]\w*)(?:\.[a-z ]+)?\)", command)
    if names:
        edges.append((names[0], names[-1]))
assert all(a in nodes and b in nodes for a, b in edges), "Undefined edge endpoint"
print(f"OK: {len(nodes)} model nodes, {len(entries)} definitions, {len(edges)} edges")
