#!/usr/bin/env python3
"""Build the process-model page for AB 2533 from pipeline artifacts.

  python3 dashboard/build_process.py   ->  dashboard/out/ab2533_process.html
"""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from common import load

P = ROOT / "examples" / "ab2533" / "process"
C = ROOT / "corpus" / "ab2533" / "process"

def statute(path, secnum):
    raw = pathlib.Path(path).read_text()
    m = re.search(rf"^{re.escape(secnum)}\.\s*$", raw, re.M)
    return raw[m.start():].strip() if m else raw.strip()

declared = load(C / "declared_processes.json")
juris = declared["jurisdictions"]
models = {}
for f in sorted(P.glob("declared_*.json")):
    m = load(f); models[m["jurisdiction"]] = m
report = load(P / "process_report.json")
data = {
    "statute": statute(ROOT / "corpus/ab2533/gov-66311.7.txt", "66311.7"),
    "skeleton": load(P / "skeleton.json"),
    "declared": juris,
    "models": [models[j["jurisdiction"]] for j in juris if j["jurisdiction"] in models],
    "report": report,
    "hayward": load(C / "hayward" / "designed_process.json"),
    "observations": declared.get("cross_jurisdiction_observations", []),
}
blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
tpl = (ROOT / "dashboard" / "process_template.html").read_text()
assert "__DATA_JSON__" in tpl
out = ROOT / "dashboard" / "out" / "ab2533_process.html"
out.parent.mkdir(parents=True, exist_ok=True)
toy = (ROOT / "dashboard" / "_toy_process_snippet.html").read_text()
out.write_text(tpl.replace("__DATA_JSON__", blob).replace("__TOY__", toy))
print(f"built {out} ({out.stat().st_size/1024:.0f} KB): {len(data['models'])} declared models, "
      f"skeleton {len(data['skeleton']['activities'])} acts, hayward {len(data['hayward']['activities'])} acts")
