# {{PROJECT_NAME}} -- System Design

{{ONE_SENTENCE_ARCHITECTURE_SUMMARY}}

## System Topology

```
+------------------+     +------------------+
| {{CLIENT_1}}     |     | {{CLIENT_2}}     |
+--------+---------+     +--------+---------+
         |                        |
         +------------+-----------+
                      |
           +----------v-----------+
           |   {{API_LAYER}}      |
           +----------+-----------+
                      |
           +----------v-----------+
           |   {{DATABASE}}       |
           +----------------------+
```

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | {{FRAMEWORK}} | {{NOTES}} |
| API | {{FRAMEWORK}} | {{NOTES}} |
| Database | {{DATABASE}} | {{NOTES}} |
| Auth | {{PROVIDER}} | {{NOTES}} |
| Hosting | {{PROVIDER}} | {{NOTES}} |

## Database

### Core Tables

| Table | Key Columns | Notes |
|-------|------------|-------|
| `{{table_name}}` | id, name, created_at | {{PURPOSE}} |

## Authentication

{{AUTH_DESCRIPTION}}

## Key Services

| Service | File | Purpose |
|---------|------|---------|
| {{ServiceName}} | `{{path}}` | {{PURPOSE}} |

## Data Flow

1. {{STEP_1}}
2. {{STEP_2}}
3. {{STEP_3}}

## Known Limitations

- **{{Limitation title}}:** {{DESCRIPTION}}
