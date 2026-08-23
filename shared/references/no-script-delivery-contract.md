# No-Script Delivery Contract

This is the authoritative contract for a delivery when the deterministic
scripts cannot run. Policy, Skill, and internal-stage documents may summarize
this contract, but must link here instead of maintaining a second checklist.

Bulk customer-development Markdown layout is owned by
[`bulk-customer-development-l1-template.md`](./bulk-customer-development-l1-template.md)
for `initial_lead_list` and
[`bulk-customer-development-l2-template.md`](./bulk-customer-development-l2-template.md)
for `standard_development_list`. Do not infer the Markdown layout from workbook sheet names.

## Common boundary

The no-script path uses the same route, evidence, identity, contact, review,
audit, delivery-status, and user-visible output boundaries as the script path.
It is a fallback for execution capability, not a lower evidence standard and
not a substitute for a formal graph when a formal delivery is requested.

## Required self-check

Before a user-visible fact delivery, verify the applicable route contract:

- keep the requested product, market, customer, or company scope explicit;
- bind each fact to an actually opened source and preserve URL, visible text or
  locator, and observation time;
- keep search summaries, unknowns, conflicts, restricted sources, and items not
  executed as their own statuses;
- preserve entity resolution, contact attribution, and the L2 review chain;
- do not infer procurement intent, customer value, final classification, tax,
  certification, logistics, or market-entry conclusions without allowed
  evidence;
- for a terminal delivery, append the canonical footer and validate the complete
  response with `scripts/validate_superleads_user_visible_output.py`.

## Accurate disclosure

Use exactly one disclosure according to the executed scope:

- `本环境未运行确定性校验` means the deterministic validation chain did not
  run at all. It does not mean the host lacked one optional component.
- `本次已完成核心业务规则校验；补充结构检查未运行。` means core business
  rules ran and passed, while only the supplemental structure check was
  unavailable. Do not describe this case as validation being incomplete or
  failed.

Do not name modules, dependency files, installation commands, interpreters,
virtual environments, runtime paths, or recovery actions in user-visible text.

## Capability boundary

If the host cannot execute the required script path, do not install packages at
runtime, create a temporary dependency directory, set `PYTHONPATH`, or search
for or borrow another application's interpreter or virtual environment. Use
this contract for the manual self-check and deliver only the level supported by
the evidence actually completed. Never claim a formal file was generated when
the official exporter did not run successfully.

## Session artifact directory

Resolve file delivery in this order: first use a non-empty
`session_artifact_dir` field or `SUPERLEADS_SESSION_ARTIFACT_DIR` environment
variable when it points to an existing writable directory; otherwise use the
current writable 工作区根目录（cwd）. Only when neither level is usable should
file delivery fall back to a 对话内工作表.

Do not create or use a model-owned runtime temporary subdirectory such as
`work/`, `tmp/`, or `out/` as the delivery location. The writable workspace
root is the allowed second-level fallback. Never expose the resolved path,
manually construct a host attachment directive, or claim delivery before the
file was actually generated.

The orchestrating Agent passes the resolved directory explicitly to
`scripts/export_workbook.py --output-dir` and places the Markdown export's
`--output` inside the same directory. Exporters do not guess a destination.
