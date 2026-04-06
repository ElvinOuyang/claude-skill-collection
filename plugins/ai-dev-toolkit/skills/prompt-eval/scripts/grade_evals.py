#!/usr/bin/env python3
"""
grade_evals.py — Grade tool-call assertions against a tool_calls.jsonl log.

Usage:
  python3 grade_evals.py <workspace_dir> <evals_json>

The workspace_dir should contain subdirectories named eval-<id>-<name>/<model>/outputs/
Each outputs/ dir must contain tool_calls.jsonl written by call_tool.sh.

Produces a grading_summary.json at workspace_dir root and prints a comparison table.
"""

import json, sys, os
from pathlib import Path


def load_calls(jsonl_path: str) -> list[dict]:
    """Parse a tool_calls.jsonl where entries may span multiple lines."""
    content = Path(jsonl_path).read_text()
    decoder = json.JSONDecoder()
    calls = []
    idx = 0
    while idx < len(content):
        idx = next((i for i in range(idx, len(content)) if content[i] == '{'), None)
        if idx is None:
            break
        try:
            obj, end = decoder.raw_decode(content, idx)
            calls.append(obj)
            idx += end - idx
        except json.JSONDecodeError:
            idx += 1
    return calls


def check_assertion(assertion: str, calls: list[dict], response_text: str = '') -> tuple[bool, str]:
    """
    Evaluate a natural-language assertion against the tool call log and/or response text.
    Returns (passed, evidence).

    Assertions are strings describing expected tool-call behavior. This function
    does keyword-based matching — keep assertions concrete and phrased consistently:

      "create_task was called"
      "create_task assignee_id is mem-001"
      "create_task ai_context.reasoning present"
      "create_task called 3 times"
      "schedule_reminder was called"
      "schedule_reminder NOT called"
      "schedule_clarify scheduled_at is within 2h of <ISO>"
      "create_task clarifications_needed present"
      "create_task due_date is set"
      "create_task assignee_id absent"
      "response does not contain UUID"
      "response contains <text>"

    For custom assertions beyond these patterns, extend this function.
    """
    # Response text assertions
    if assertion.lower().startswith('response '):
        import re
        a_lower = assertion.lower()
        if 'does not contain uuid' in a_lower:
            uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
            matches = re.findall(uuid_pattern, response_text, re.IGNORECASE)
            if matches:
                return False, f"Response contains UUID(s): {matches[:3]}"
            return True, "No UUIDs found in response"
        if 'does not contain' in a_lower:
            forbidden = assertion.split('does not contain', 1)[1].strip().strip('"').strip("'")
            if forbidden.lower() in response_text.lower():
                return False, f"Response contains forbidden text: {forbidden!r}"
            return True, f"Response does not contain {forbidden!r}"
        if 'contains' in a_lower:
            required = assertion.split('contains', 1)[1].strip().strip('"').strip("'")
            if required.lower() in response_text.lower():
                return True, f"Response contains {required!r}"
            return False, f"Response does not contain {required!r}"
    # Filter to only entries with a 'tool' key (skip fake response objects from call_tool.sh)
    calls = [c for c in calls if 'tool' in c]
    tools = [c['tool'] for c in calls]
    a = assertion.lower()

    # Extract the primary tool name from the assertion
    primary_tool = next((t for t in [
        'create_task', 'update_task', 'complete_task', 'assign_task', 'list_tasks',
        'schedule_reminder', 'schedule_clarify', 'cancel_nudge',
        'get_family_roster', 'get_member', 'update_profile', 'save_context',
        'recall_context', 'search_history', 'get_recent_tasks', 'log_pattern', 'get_patterns',
    ] if t in a), None)

    matching_calls = [c for c in calls if c['tool'] == primary_tool] if primary_tool else []

    # "NOT called" check
    if 'not called' in a or 'not be called' in a:
        passed = primary_tool not in tools
        return passed, f"Tools called: {tools}"

    # "called N times" check
    if 'called 3 times' in a:
        passed = len(matching_calls) == 3
        return passed, f"{primary_tool} called {len(matching_calls)} time(s)"
    if 'called 2 times' in a:
        passed = len(matching_calls) == 2
        return passed, f"{primary_tool} called {len(matching_calls)} time(s)"

    # "was called" check
    if 'was called' in a or 'called' in a:
        if not matching_calls:
            return False, f"{primary_tool} not found in tool calls: {tools}"

    # "is set" — field exists and is non-empty
    if ' is set' in a and matching_calls:
        field_part = a.replace(primary_tool, '').replace('is set', '').strip()
        keys = field_part.split('.')
        for call in matching_calls:
            val = call['params']
            try:
                for k in keys:
                    val = val[k]
                if val not in [None, '', [], {}]:
                    return True, f"{field_part}={val!r}"
            except (KeyError, TypeError):
                pass
        return False, f"Field {field_part!r} missing or empty in {primary_tool} calls"

    # "within <N>h of <ISO>" — check before lowercasing destroys the ISO timestamp
    if 'within' in a and 'scheduled_at' in a and matching_calls:
        import re
        iso_match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', assertion)  # use original case
        hours_match = re.search(r'within (\d+)h', a)
        if iso_match and hours_match:
            base_time = iso_match.group()
            hours = int(hours_match.group(1))
            from datetime import datetime, timedelta
            base_dt = datetime.fromisoformat(base_time.replace('Z', '+00:00'))
            deadline = (base_dt + timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
            for call in matching_calls:
                sched = call['params'].get('scheduled_at', '')
                if sched and sched <= deadline:
                    return True, f"scheduled_at={sched!r} is within {hours}h of {base_time}"
            return False, f"No {primary_tool} call has scheduled_at within {hours}h of {base_time}"

    # Field value checks: "<tool> <field> is <value>"
    if ' is ' in a and matching_calls:
        parts = a.split(' is ', 1)
        field_part = parts[0].replace(primary_tool, '').strip()
        expected_val = parts[1].strip()

        for call in matching_calls:
            # Handle nested fields like "ai_context.reasoning"
            keys = field_part.split('.')
            val = call['params']
            try:
                for k in keys:
                    val = val[k]
                if str(val).lower() == expected_val:
                    return True, f"Found {field_part}={val!r}"
                # Partial match for dates/ranges
                if expected_val in str(val).lower():
                    return True, f"Found {field_part}={val!r} (contains '{expected_val}')"
            except (KeyError, TypeError):
                pass
        return False, f"Field {field_part!r} not matching {expected_val!r} in any {primary_tool} call. Params: {[c['params'] for c in matching_calls]}"

    # "absent" or "absent/null" checks
    if 'absent' in a or 'absent/null' in a:
        field_part = a.replace(primary_tool, '').replace('absent/null', '').replace('absent', '').strip()
        field_key = field_part.strip()
        for call in matching_calls:
            val = call['params'].get(field_key)
            if val not in [None, '', []]:
                return False, f"{field_key}={val!r} — expected absent/null"
        return True, f"{field_key} is absent or null in all {primary_tool} calls"

    # "present" checks (field exists and is non-empty)
    if 'present' in a and matching_calls:
        field_part = a.replace(primary_tool, '').replace('present', '').strip()
        # Handle dotted paths
        keys = field_part.split('.')
        for call in matching_calls:
            val = call['params']
            try:
                for k in keys:
                    val = val[k]
                if val:
                    return True, f"{field_part}={val!r}"
            except (KeyError, TypeError):
                pass
        return False, f"Field {field_part!r} not found or empty in {primary_tool} calls"

    # Default: tool was called
    if matching_calls:
        return True, f"{primary_tool} called {len(matching_calls)} time(s)"
    return False, f"{primary_tool} not found in tool calls: {tools}"


def grade_model(workspace_dir: str, evals: list[dict], model_name: str) -> dict:
    """Grade all evals for a given model directory name."""
    results = {}
    for ev in evals:
        eval_name = ev.get('name', f"eval-{ev['id']}")
        # Try both naming conventions
        candidates = [
            f"{workspace_dir}/eval-{ev['id']}-{eval_name}/{model_name}/outputs/tool_calls.jsonl",
            f"{workspace_dir}/{model_name}/eval-{ev['id']}-{eval_name}/outputs/tool_calls.jsonl",
        ]
        jsonl_path = next((p for p in candidates if os.path.exists(p)), None)

        # Determine outputs dir for response.txt lookup
        if jsonl_path:
            outputs_dir = os.path.dirname(jsonl_path)
            calls = load_calls(jsonl_path)
        else:
            # No tool_calls.jsonl — model made no tool calls. Grade with empty call list.
            outputs_dir_candidates = [
                f"{workspace_dir}/eval-{ev['id']}-{eval_name}/{model_name}/outputs",
                f"{workspace_dir}/{model_name}/eval-{ev['id']}-{eval_name}/outputs",
            ]
            outputs_dir = next((p for p in outputs_dir_candidates if os.path.isdir(p)), None)
            if not outputs_dir:
                results[eval_name] = {'error': f"No outputs dir found for {eval_name}/{model_name}"}
                continue
            calls = []

        # Load response text if available
        response_path = os.path.join(outputs_dir, 'response.txt')
        response_text = Path(response_path).read_text() if os.path.exists(response_path) else ''
        assertion_results = []
        for assertion in ev.get('expectations', []):
            passed, evidence = check_assertion(assertion, calls, response_text)
            assertion_results.append({'text': assertion, 'passed': passed, 'evidence': evidence})

        passed_count = sum(1 for r in assertion_results if r['passed'])
        total = len(assertion_results)
        results[eval_name] = {
            'passed': passed_count,
            'total': total,
            'pass_rate': passed_count / total if total else 0,
            'assertions': assertion_results,
        }
    return results


def print_comparison(models: dict[str, dict], eval_names: list[str]):
    """Print a side-by-side comparison table."""
    model_names = list(models.keys())
    col_w = 10

    header = f"{'Eval':<40}" + "".join(f"{m:>{col_w}}" for m in model_names)
    print(header)
    print("─" * (40 + col_w * len(model_names)))

    totals = {m: [0, 0] for m in model_names}
    for ename in eval_names:
        row = f"{ename:<40}"
        for m in model_names:
            r = models[m].get(ename, {})
            if 'error' in r:
                row += f"{'N/A':>{col_w}}"
            else:
                cell = f"{r['passed']}/{r['total']}"
                row += f"{cell:>{col_w}}"
                totals[m][0] += r['passed']
                totals[m][1] += r['total']
        print(row)

    print("─" * (40 + col_w * len(model_names)))
    total_row = f"{'TOTAL':<40}"
    for m in model_names:
        cell = f"{totals[m][0]}/{totals[m][1]}"
        total_row += f"{cell:>{col_w}}"
    print(total_row)

    # Failures
    print("\n=== Failures by model ===")
    for m in model_names:
        failures = []
        for ename in eval_names:
            r = models[m].get(ename, {})
            for a in r.get('assertions', []):
                if not a['passed']:
                    failures.append(f"  [{ename}] {a['text']}\n    → {a['evidence']}")
        if failures:
            print(f"\n{m}:")
            print("\n".join(failures))
        else:
            print(f"\n{m}: all passed ✓")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 grade_evals.py <workspace_dir> <evals_json> [model1 model2 ...]")
        sys.exit(1)

    workspace_dir = sys.argv[1]
    evals_json = sys.argv[2]
    model_list = sys.argv[3:] if len(sys.argv) > 3 else ['sonnet', 'haiku']

    evals = json.loads(Path(evals_json).read_text())['evals']
    eval_names = [ev.get('name', f"eval-{ev['id']}") for ev in evals]

    models = {}
    for model in model_list:
        models[model] = grade_model(workspace_dir, evals, model)

    print_comparison(models, eval_names)

    summary = {'models': models, 'eval_names': eval_names}
    out_path = os.path.join(workspace_dir, 'grading_summary.json')
    Path(out_path).write_text(json.dumps(summary, indent=2))
    print(f"\nFull results saved to {out_path}")
