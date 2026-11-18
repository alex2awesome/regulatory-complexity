"""Compare the current visit likelihood with a fully frozen reference package.

Used both for computational optimization and disabled-extension compatibility.
Never import a changed current dependency into the supposedly frozen reference.
"""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import importlib
import json
import pathlib
import sys
import time
import types

import numpy as np

from .bayes_trace_hierarchy import Config,VisitHierarchy
from .infra.manifest import digest, write


def frozen_reference(root,manifest):
    root=pathlib.Path(root)
    for filename,expected in manifest['source_sha256'].items():
        if digest((root/'source'/filename).read_bytes())!=expected:
            raise ValueError('Saved reference source changed: '+filename)
    # A distinct package forces every relative import into the saved directory,
    # including compact traces and schedule kernels, not the working tree.
    name='pipeline.procbench._frozen_visit_'+digest(
        str(root.resolve())+json.dumps(manifest['source_sha256'],sort_keys=True))[:16]
    if name not in sys.modules:
        package=types.ModuleType(name)
        package.__path__=[str(root/'source')]
        package.__package__=name
        sys.modules[name]=package
    return importlib.import_module(name+'.bayes_trace_hierarchy')


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',required=True)
    ap.add_argument('--reference-states',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    root,out=pathlib.Path(args.run),pathlib.Path(args.out)
    if out.exists():
        raise ValueError('Preserve previous diagnostics; choose a fresh directory')
    manifest=json.loads((root/'manifest.json').read_text())
    source=pathlib.Path(__file__).parent
    for path,expected in manifest['input_sha256'].items():
        if digest(pathlib.Path(path).read_bytes())!=expected:
            raise ValueError('Input changed since the original run')
    data=json.loads((root/'data.json').read_text())
    module=frozen_reference(root,manifest)
    reference=module.VisitHierarchy(data,module.Config(**manifest['config']))
    current=VisitHierarchy(data,Config(**manifest['config']))
    if current.layout.slices.keys()!=reference.layout.slices.keys() or any(
            not np.array_equal(current.layout.slices[k],reference.layout.slices[k]) for k in current.layout.slices):
        raise ValueError('Parameter layout changed')
    raw=np.load(args.reference_states)
    states=raw['z'].reshape(-1,current.layout.size)
    routes=raw['structures'].reshape(-1,len(current.programs))
    ids=np.linspace(0,len(states)-1,min(100,len(states)),dtype=int)
    rng=np.random.default_rng(2026092019)
    states=np.concatenate((states[ids],rng.normal(size=(100,current.layout.size))))
    routes=np.concatenate((routes[ids],np.column_stack([
        rng.integers(len(p['routes']),size=100) for p in current.programs])))
    values,timings={},{}
    for label,model in [('reference',reference),('current',current)]:
        start=time.perf_counter()
        values[label]=np.array([model.log_likelihood(z,s) for z,s in zip(states,routes)])
        timings[label]=time.perf_counter()-start
    difference=np.abs(values['current']-values['reference'])
    acceptable=bool(np.isfinite(difference).all() and np.max(difference)<1e-7)
    result=dict(completed_utc=datetime.now(timezone.utc).isoformat(),reference_run=str(root),
        original_run_may_still_be_running=not bool(manifest.get('completed_utc')),config=asdict(current.cfg),
        n_states=len(states),max_absolute_likelihood_difference=float(np.max(difference)),
        acceptable=acceptable,seconds=timings,observed_speedup=timings['reference']/timings['current'],
        original_source_sha256=manifest['source_sha256']['bayes_trace_hierarchy.py'],
        current_source_sha256=digest((source/'bayes_trace_hierarchy.py').read_bytes()),
        frozen_dependency_imports=True,
        current_dependency_sha256={name:digest((source/name).read_bytes())
                                  for name in manifest['source_sha256']},
        reference_states_sha256=digest(pathlib.Path(args.reference_states).read_bytes()),
        data_sha256=digest((root/'data.json').read_bytes()),
        scope='Computation/target check only; no truth read or accuracy comparison')
    write(out/'audit.json',result)
    np.savez_compressed(out/'checks.npz',states=states,structures=routes,reference=values['reference'],current=values['current'])
    (out/'audit_source.py').write_bytes(pathlib.Path(__file__).read_bytes())
    print(json.dumps(result),flush=True)
    if not acceptable:
        raise ValueError('Likelihood target changed; do not replace or extend the fit')


if __name__=='__main__':
    main()
