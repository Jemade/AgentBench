# Interface decisions

AgentBench uses a workspace style suited to inspecting engineering evidence. The interface is implemented in HTML/CSS/React rather than exported from a generated mockup.

| Element | Choice |
| --- | --- |
| Sidebar | Solid forest, #202923 |
| Primary action | Forest green, #285746 |
| Logo accent | Muted amber, #e9bc64 |
| Background | Near-white, #f7f8f4 |
| Panels | White with thin grey-green borders |
| Type | Local system sans-serif and monospace for code |
| Icons | Consistent Lucide strokes; only functional navigation/action icons |
| Motion | Short background-colour changes |

No gradients, neon, glowing decoration, animated counters, fabricated model rankings, or promotional success metrics. The small original SVG logo combines measured bars with a check mark and remains legible at navigation size.

Workspace shows actual recorded counts. Evaluation reports distinguish partial scores, unknown cost and runner errors. Provider availability follows server configuration. Baselines are labelled at selection, in history and on reports. Comparison uses real recorded scores and native progress indicators.

Dialog elements support focus management and Escape through the browser. Forms use labels. Tables scroll inside their panels on narrow screens while the page stays within the viewport. The mobile navigation closes after selecting a screen.

Actual running-product screenshots are stored under `docs/screenshots`: workspace, evaluation report, comparison, task library and mobile library. They show authored-baseline executions, not external model-performance evidence.
