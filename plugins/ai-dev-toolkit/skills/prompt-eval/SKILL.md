---
name: prompt-eval
description: Test AI system prompts that involve tool calls by packaging them as a skill with mock callable tools, running evals inline (no extra API cost) or via model-specific subagents, and grading assertions against tool-call logs. Use this skill whenever you want to evaluate whether a system prompt causes a model to call the right tools with the right parameters — including comparing behavior across models like Haiku vs Sonnet.
---

# Prompt Eval

A methodology for testing system prompts that involve tool-calling behavior. The core idea: package the prompt as a skill with mock bash tools, run test cases, and grade whether the right tools were called with the right parameters.

**Why this approach:**
- No production side effects — mock tools log calls but touch nothing real
- No separate API cost for inline runs — you execute the evals yourself in the current session
- Model comparison is cheap — spawn a Haiku subagent to run the same evals independently
- Assertions are machine-checkable — grading is deterministic, not subjective

---

## Phase 1: Package the Prompt as a Skill

Create a skill directory for the prompt you're evaluating:

```
<project>/docs/skills/<skill-name>/
├── SKILL.md                  ← the prompt, formatted as a skill
├── scripts/
│   └── call_tool.sh          ← mock tool caller (copy from template)
└── evals/
    └── evals.json            ← test cases + assertions
```

### Writing SKILL.md for the prompt

The skill file has two jobs: (1) give the model the system prompt, and (2) tell it how to call tools using the mock script instead of real APIs.

Include in the SKILL.md:
- **Persona and context** — the full system prompt content
- **Mock context** — a fixed, realistic fake dataset (family roster, current datetime, existing records). Keep this stable across all evals so assertions are predictable.
- **Tool reference** — list all available tools with their parameter schemas
- **How to call tools** — the bash invocation using `call_tool.sh`
- **Behavioral rules** — the exact decision logic you're testing (this is what the evals will verify)
- **Output instructions** — save the natural language response to `{OUTPUTS_DIR}/response.txt`

**Tool-calling instruction to include in SKILL.md:**
```bash
bash {SKILL_DIR}/scripts/call_tool.sh <tool_name> '<compact_json>' {OUTPUTS_DIR}
```
Compact JSON means no line breaks — the grader parses one JSON object per line.

### Setting up call_tool.sh

Copy `docs/skills/prompt-eval/scripts/call_tool_template.sh` to your skill's `scripts/call_tool.sh` and add case blocks for each tool in your prompt. Make it executable: `chmod +x scripts/call_tool.sh`.

The script does two things:
1. Appends `{"tool":"...","params":{...},"timestamp":"..."}` to `tool_calls.jsonl`
2. Prints a realistic fake response so the model can continue naturally

Keep fake responses realistic enough that the model's follow-up reasoning stays on track (e.g. if `create_task` returns an `id`, the model can use it in a subsequent `schedule_reminder` call).

---

## Phase 2: Design Test Cases

Good test cases cover the behavioral rules you actually care about. Each case should exercise one distinct pattern.

Typical patterns to cover:
- **Happy path** — straightforward request, all info present
- **Assign to known member** — model must look up the right member ID
- **Unknown member** — model must handle gracefully (omit assignee, add clarification)
- **Multi-step** — single message triggers multiple tool calls
- **Vague/incomplete** — model must act first and schedule a follow-up

### evals.json format

```json
{
  "skill_name": "your-skill-name",
  "evals": [
    {
      "id": 1,
      "name": "short-kebab-case-name",
      "prompt": "The user message to process. Include outputs_dir path here.",
      "expected_output": "Human-readable description of what success looks like.",
      "expectations": [
        "create_task was called",
        "create_task assignee_id is mem-001",
        "create_task ai_context.reasoning present",
        "schedule_reminder was called",
        "schedule_reminder member_id is mem-001"
      ]
    }
  ]
}
```

### Writing good assertions

Assertions are checked by `grade_evals.py` using keyword pattern matching. Write them in this form:

| Pattern | Example |
|---|---|
| Tool was called | `"create_task was called"` |
| Tool NOT called | `"schedule_reminder NOT called"` |
| Tool called N times | `"create_task called 3 times"` |
| Field equals value | `"create_task assignee_id is mem-001"` |
| Nested field present | `"create_task ai_context.reasoning present"` |
| Field absent/null | `"create_task assignee_id absent"` |
| Time constraint | `"schedule_clarify scheduled_at is within 2h of 2026-03-28T09:00:00Z"` |

Keep assertions specific enough to fail when the model gets it wrong, but not so brittle they fail on acceptable variation (e.g. don't assert exact title text).

---

## Phase 3: Run Evals Inline (No Extra API Cost)

Running inline means you execute the evals yourself within the current session. This uses no additional API tokens beyond the current conversation.

### Setup

Create output directories for each eval:
```bash
mkdir -p docs/skills/<skill-name>-workspace/iteration-1/eval-<id>-<name>/outputs
```

### Execution

For each eval:
1. Read the test prompt from `evals.json`
2. Follow the skill's behavioral rules exactly
3. Call each tool via Bash using `call_tool.sh`
4. Write the natural language response to `outputs/response.txt`

Call tools like this (use compact single-line JSON for params):
```bash
bash docs/skills/<skill-name>/scripts/call_tool.sh create_task \
  '{"family_id":"fam-001","title":"Buy groceries","assignee_id":"mem-002","created_by_id":"mem-002","due_date":"2026-03-29","priority":"medium","ai_context":{"reasoning":"Bob needs groceries tomorrow."}}' \
  docs/skills/<skill-name>-workspace/iteration-1/eval-1-simple-task/outputs
```

---

## Phase 4: Run Evals with a Subagent (Model Comparison)

To test a different model (e.g. Haiku), spawn a subagent with the target model. The subagent reads the skill independently and executes the evals — this gives a genuine test of that model's behavior, not yours.

### Output directory convention

Use `iteration-1/<model-name>/eval-<id>-<name>/outputs/` for subagent runs so the grader can find them:
```bash
mkdir -p docs/skills/<skill-name>-workspace/iteration-1/haiku/eval-<id>-<name>/outputs
```

### Subagent prompt template

```
You are being tested with a skill. Read the skill file, then run each eval exactly as instructed.

## Skill to follow
Read: <absolute-path-to>/SKILL.md

## Evals

### Eval 1 — <name>
Outputs dir: <absolute-path>/iteration-1/haiku/eval-1-<name>/outputs
<user message>

### Eval 2 — <name>
...

Run all evals. For each: call tools via Bash, save response to response.txt.
Use compact single-line JSON for all tool params (no line breaks inside the JSON string).
```

Spawn with `model: "haiku"` (or `"sonnet"`, `"opus"`) in the Agent tool.

---

## Phase 5: Grade and Compare

Run the grading script, pointing it at the workspace and evals.json:

```bash
python3 docs/skills/prompt-eval/scripts/grade_evals.py \
  docs/skills/<skill-name>-workspace/iteration-1 \
  docs/skills/<skill-name>/evals/evals.json \
  sonnet haiku
```

The script:
1. Finds `tool_calls.jsonl` for each eval × model combination
2. Checks each assertion using keyword pattern matching
3. Prints a comparison table
4. Saves `grading_summary.json` to the workspace

**Directory lookup:** The grader looks for tool calls at:
- `<workspace>/eval-<id>-<name>/<model>/outputs/tool_calls.jsonl` (inline runs)
- `<workspace>/<model>/eval-<id>-<name>/outputs/tool_calls.jsonl` (subagent runs)

For inline runs (where you are the model), use your own name as the model directory, e.g. `sonnet`.

---

## Phase 6: Iterate on the Prompt

When assertions fail, diagnose whether the issue is:

1. **Missing rule** — the prompt doesn't mention this behavior at all → add it
2. **Rule present but weak** — the prompt mentions it but doesn't make it salient → make it imperative or add a self-check step
3. **Rule present, model too weak** — even a strong instruction doesn't help on a small model → either accept the limitation or use a stronger model for that use case

### Common fixes for weaker models (Haiku)

If a follow-up tool call (like `schedule_reminder` after `create_task`) gets dropped:
- Add an explicit post-action checklist: *"After every create_task, ask yourself: is due_date set and >3 days away? If yes, call schedule_reminder before responding."*
- Make the condition imperative rather than descriptive

After editing SKILL.md, re-run the failing evals (inline or subagent) and re-grade. Iterate until the assertions pass across your target models.

---

## Quick Reference

```bash
# Run grader
python3 docs/skills/prompt-eval/scripts/grade_evals.py \
  <workspace>/iteration-N \
  <skill>/evals/evals.json \
  sonnet haiku

# Create output dirs (inline run)
mkdir -p <workspace>/iteration-1/eval-<id>-<name>/outputs

# Create output dirs (subagent run)
mkdir -p <workspace>/iteration-1/haiku/eval-<id>-<name>/outputs

# Call a mock tool inline
bash <skill>/scripts/call_tool.sh <tool_name> '<compact_json>' <outputs_dir>
```
