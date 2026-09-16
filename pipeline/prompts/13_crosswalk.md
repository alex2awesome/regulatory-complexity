# Cross-jurisdiction condition crosswalk

You are given two jurisdictions' food-safety inspection violation items: New York City's and San Diego County's. They regulate the same underlying domain but carve it up differently — one jurisdiction's single item may correspond to several of the other's, or to none.

Map each NY item to the SD item(s) that test **the same underlying violation construct** — the same real-world condition an inspector would be citing. Judge by substance (what condition of the establishment is being flagged), never by list position, code similarity, or point value.

Rules:

- Many-to-many is allowed and expected (e.g., several specific NY items may all map to one broader SD item, and vice versa).
- Map only where the substantive overlap is real. If a NY item has no genuine SD counterpart, put it in `no_counterpart` — do not force a match.
- Some item names are terse; interpret them as a food-safety professional would (e.g., "vermin proof" concerns rodent/insect exclusion of the premises).
- Do not invent items; use only the codes given.

Output JSON:

```json
{"pairs": [{"ny": "10F", "sd": "33", "why": "3-8 words"}, ...],
 "no_counterpart": ["NYcode", ...]}
```
