# Component Registry

Inventory of every reusable view, service, utility, and hook in the {{PROJECT_NAME}} codebase.

---

## {{PLATFORM_OR_LAYER}} ({{FRAMEWORK}})

### Components - {{DOMAIN}}

| Name | Path | Description | Used By |
|------|------|-------------|---------|
| {{ComponentName}} | `{{path/to/file}}` | {{ONE_LINE_DESCRIPTION}} | {{ParentComponent}} |

### Services

| Name | Path | Description | Used By |
|------|------|-------------|---------|
| {{ServiceName}} | `{{path/to/file}}` | {{ONE_LINE_DESCRIPTION}} | {{Consumers}} |

### Hooks

| Name | Path | Description | Used By |
|------|------|-------------|---------|
| {{useHookName}} | `{{path/to/file}}` | {{ONE_LINE_DESCRIPTION}} | {{Components}} |

### Utilities

| Name | Path | Description | Used By |
|------|------|-------------|---------|
| {{utilName}} | `{{path/to/file}}` | {{ONE_LINE_DESCRIPTION}} | {{Consumers}} |

---

## Conventions

- Group by platform/layer first, then by domain.
- Every entry must have a file path and at least one consumer listed.
- If a component is test-only or unused, note it in the Description.
