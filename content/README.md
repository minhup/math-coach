# Versioned content packages

Milestone 2 content lives in one self-contained `content/packages/<slug>/package.yaml` or
`package.json` file per directory. `make content-validate` rejects unknown files, duplicate mapping
keys, unknown schema fields, unresolved references, unsafe geometry, invalid scoring/hints, and stale
generated schema output before a database connection is opened.

Only clearly original synthetic fixtures are approved. Schema version `1.0.0` deliberately accepts
only `original_synthetic` source records with `synthetic_only` publication status. Real examination
selection and rights/provenance vocabulary remain `DECISION REQUIRED`; do not add real or third-party
content until the project owner records those decisions and the schema is reviewed.

Run:

```bash
make content-validate
make migrate
make seed
```

Imports run in deterministic path order and one transaction per package. Re-importing identical
package bytes is a no-op. Reusing a package ID/version for different validated content or conflicting
with an immutable database row fails without leaving partial content.

The committed synthetic corpus is incremental:

- `synthetic-m2-foundations-v1` owns the shared invented exams, cycles, skills, first scene, and
  first problem.
- `synthetic-m4-geometry-v1` reuses those explicit multi-exam and shared-skill identities while
  adding a new immutable all-primitives scene/problem with every approved typed action.

Every released scene version's `fallbackImageAssetId` resolves to a repository-owned SVG at
`apps/student-web/public/fixtures/<asset-id>.svg`. Content integration tests enforce that
convention. SVG files are application assets, not content fields: packages cannot provide SVG,
HTML, Markdown, scripts, functions, expressions, or event handlers.
