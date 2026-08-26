# Content package schema

`content-package.schema.json` is generated from the FastAPI service's strict Pydantic content
contract. Regenerate it only after an intentional schema change:

```bash
make content-schema-generate
make content-validate
```

The validation command fails when the committed schema is stale. The schema is an import contract;
it does not authorize real examination content or replace the repository provenance policy.
