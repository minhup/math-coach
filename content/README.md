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
