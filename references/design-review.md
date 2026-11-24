# Project-owned review contract

`design-review.json` belongs to this skill's project workflow. It needs no
external recorder or editor. Start with
[the template](../assets/design-review.template.json), edit it with normal file
tools, and preserve unrelated records.

```json
{
  "schemaVersion": 1,
  "assets": [
    {
      "path": "index.html",
      "status": "needs-review",
      "approvalEvidence": null
    }
  ]
}
```

One record per exact path relative to the design project; use forward slashes,
no absolute paths or parent traversal. Status is `draft`, `needs-review`,
`changes-requested`, or `approved`. On approval, set `approvalEvidence` to a
concise reference to the actual user instruction and reviewed version. Do not
copy sensitive chat history or invent a receipt. A nonempty string is only a
structural check, not proof that the user said it.

A revision returns to `needs-review` and clears `approvalEvidence`. Revocation
sets `changes-requested`. A preview, successful check, or praise with requested
changes is not approval. Keep historical versions in Git or separate asset paths,
not duplicate records for the same path.

For product UI, `ui-contract.json` owns state and dependency mappings; the review
file owns user approval. The surface `status` mirrors it: when you record
approval here, set the matching surface to `approved` (later `implemented`).
The implementation gate requires both, and `pfui.py check` reports a surface
that claims approval the review file does not hold. `prototype.files` must include the entry, asset and all
local CSS/JS/fonts/images/fixtures needed to reproduce the reviewed surface.
Snapshot shared design-system assets inside this design project with their source
revision. Mutable remote assets cannot be frozen by this gate; use local permitted
copies for approval or explicitly report that exact reproduction is blocked.

Run `validate_workflow.py approval` for the exact asset. After a design-only
commit, `implementation-gate` verifies current approval, ancestry, scope, contract,
content and unchanged Git blobs for every declared prototype file, including
binary assets. It rejects symlinks in that list. Production mappings may evolve;
changing prototype mappings requires review. The validator cannot discover every
runtime dependency or judge consent: audit the file list and actual user approval.

For standalone decks, system previews and visuals, this record is optional unless
approval tracking is needed. Do not fabricate UI contracts or Git commits to use
it. Record the source revision in handoff when approval exists.

## Upgrading a 2.x project

Version 3 reads approval only from `design-review.json`. Status kept elsewhere
(an older metadata file, a design tool's flag, a ticket) is historical evidence:
leave it in place, copy the relevant asset paths into the new template as
`needs-review`, and complete the UI dependency list where applicable.

An old `approved` flag alone is insufficient. Reuse prior explicit approval only
if its evidence is available and the complete deliverable is demonstrably
unchanged; otherwise obtain approval of the current version. Record the evidence
and create a new design-only commit before running the v3 gate. Existing
`ui-contract.json` schemaVersion 2 and content/source inventories remain usable.
