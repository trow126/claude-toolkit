#!/usr/bin/env python3
"""
GitHub Issue Parser
Extracts structured task data from GitHub Issue markdown.
"""

import json
import re
import sys


def parse_issue(body, title, number, url=""):
    """
    Parse GitHub Issue markdown to extract tasks and phases.

    Args:
        body: Issue markdown body
        title: Issue title
        number: Issue number
        url: Issue URL

    Returns:
        dict: Structured issue data with phases and tasks
    """
    phases = []
    tasks = []
    current_phase = None
    task_id = 1

    lines = body.split('\n') if body else []

    for line in lines:
        # Phase detection (## headings)
        if line.startswith('## '):
            current_phase = line[3:].strip()
            if current_phase and current_phase not in phases:
                phases.append(current_phase)

        # Task detection (- [ ] or - [x] checkboxes)
        match = re.match(r'- \[([ xX])\] (.+)', line.strip())
        if match:
            completed = match.group(1).lower() == 'x'
            task_text = match.group(2).strip()

            tasks.append({
                'id': task_id,
                'phase': current_phase if current_phase else 'General',
                'text': task_text,
                'completed': completed,
                'status': 'completed' if completed else 'pending'
            })
            task_id += 1

    # Calculate statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t['completed'])
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'issue_number': number,
        'title': title,
        'url': url,
        'phases': phases,
        'tasks': tasks,
        'statistics': {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': total_tasks - completed_tasks,
            'completion_percentage': round(completion_percentage, 1)
        }
    }


def main():
    """
    Main entry point.
    Expects JSON input from stdin with: body, title, number, url
    """
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)

        body = data.get('body', '')
        title = data.get('title', '')
        number = data.get('number', 0)
        url = data.get('url', '')

        # Parse issue
        result = parse_issue(body, title, number, url)

        # Output JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
