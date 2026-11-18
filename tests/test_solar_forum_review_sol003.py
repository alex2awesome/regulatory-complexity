from pipeline.procbench.process_structure.forum import quoted_reference
from pipeline.procbench.process_structure.solar_forum_bridge import BLOCK,ROOT
from pipeline.procbench.process_structure.solar_forum_review_sol003 import THREADS,build
def test_sol003():
 p,c=build(); assert {x['thread_id'] for x in c}==set(THREADS); assert not p['root_adopted']
 for e in p['episodes']:
  assert [r['step_id'] for r in e['readings']]==BLOCK
  for q in e['identity_context_quotes']: assert not q['json_path'].startswith('$.post.comments'); quoted_reference(q,ROOT)
  for r in e['readings']:
   assert r['detected']==bool(r['quotes'])
   for q in r['quotes']: assert not q['json_path'].startswith('$.post.comments'); quoted_reference(q,ROOT)
 for t in p['timing_records']:
  for q in t['source_refs']: assert not q['json_path'].startswith('$.post.comments'); quoted_reference(q,ROOT)
