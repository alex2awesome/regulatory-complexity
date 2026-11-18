---
pretty_name: Regulatory complexity project data
license: other
---

# Regulatory complexity: project data (private)

Data for the Stanford RegLab project on regulatory complexity and burden (Alexander Spangher, Dan Ho,
Sanmi Koyejo; rule-following work with Isabel). The code is in the private GitHub repo
`alex2awesome/regulatory-complexity`; this dataset holds everything the code reads or writes that is not
in git.

## Layout

Every top-level folder is one `.tar.gz` at the same path it has in the code repo.

| Path | What it holds |
|---|---|
| `corpus/*.tar.gz` | Gathered sources: statute texts, county records (HCD Annual Progress Report tables, grand jury reports, CalFresh, permit portals), process pages for nine real-world programs, forum pulls, third-party statute-to-code sets (SARA) |
| `benchmark/synth/worlds/*.tar.gz` | Generated synthetic worlds, including their truth (answer keys) |
| `runs/*.tar.gz` | One archive per run: inputs, model transcripts, parses, fits and results. `runs/_files.tar.gz` holds `runs/README.md` |
| `scratch/*.tar.gz` | The project's folders from the servers' shared scratch: forum censuses (Solar and ADU), procurement exports (SCPRS, CSCR), admin data pulls, Gemma triage jobs, toy-model fits |
| `MANIFEST.jsonl` | One row per archive: source folder, file count, bytes, sha256 |

## Restore

```sh
hf download alex2awesome/regulatory-complexity-data --repo-type dataset --local-dir data_download
python scripts/archive_to_hf.py restore data_download    # from the code repo
```

Local archives unpack to their original paths (`corpus/...`, `runs/...`); server archives unpack under
`scratch/`. Move or symlink the restored folders into the code repo root.

## Contents to keep in mind

- Forum text from Reddit and other forums, as collected (post text, usernames, timestamps).
- Public government records as downloaded.
- Model transcripts and LLM parses, which quote forum and government text.
- Synthetic worlds with their answer keys; sharing them ends their use as a held-out test.
- Folders were scanned for credential patterns before upload; any folder with a hit was skipped
  (listed in `runs/hf_archive_20261117/skipped.jsonl` in the code repo's run log).
