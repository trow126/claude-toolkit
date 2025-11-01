#!/usr/bin/env python3
"""
Convert parsed Issue tasks to TodoWrite format
"""

import json
import sys


def generate_active_form(task_text):
    """
    Generate active form of task text.

    Example:
        "API実装" -> "API実装中"
        "テスト作成" -> "テスト作成中"
        "Implement API" -> "Implementing API"
    """
    # Japanese patterns
    japanese_patterns = {
        '実装': '実装中',
        '作成': '作成中',
        '修正': '修正中',
        '更新': '更新中',
        '追加': '追加中',
        '削除': '削除中',
        '設計': '設計中',
        'テスト': 'テスト中',
        '検証': '検証中'
    }

    active = task_text
    for pattern, replacement in japanese_patterns.items():
        if pattern in task_text and not replacement in task_text:
            active = task_text.replace(pattern, replacement)
            return active

    # English patterns - convert to -ing form
    english_patterns = {
        'Implement': 'Implementing',
        'Create': 'Creating',
        'Fix': 'Fixing',
        'Update': 'Updating',
        'Add': 'Adding',
        'Delete': 'Deleting',
        'Design': 'Designing',
        'Test': 'Testing',
        'Verify': 'Verifying',
        'Build': 'Building',
        'Deploy': 'Deploying'
    }

    for pattern, replacement in english_patterns.items():
        if task_text.startswith(pattern):
            active = task_text.replace(pattern, replacement, 1)
            return active

    # Default: append "中" or "in progress"
    if any(ord(c) > 127 for c in task_text):  # Contains non-ASCII (likely Japanese)
        return f"{task_text}中"
    else:
        return f"{task_text} (in progress)"


def convert_to_todowrite(parsed_issue):
    """
    Convert parsed Issue data to TodoWrite format.

    Args:
        parsed_issue: Output from issue-parser (dict)

    Returns:
        dict: TodoWrite tasks and metadata
    """
    tasks = parsed_issue.get('tasks', [])
    issue_number = parsed_issue.get('issue_number')
    issue_title = parsed_issue.get('title', '')

    todowrite_tasks = []
    task_mapping = []

    for task in tasks:
        task_id = task.get('id')
        text = task.get('text', '')
        completed = task.get('completed', False)
        phase = task.get('phase', 'General')

        # Determine status
        status = 'completed' if completed else 'pending'

        # Generate active form
        active_form = generate_active_form(text)

        # Create TodoWrite task
        todowrite_task = {
            'content': text,
            'status': status,
            'activeForm': active_form
        }

        todowrite_tasks.append(todowrite_task)

        # Store mapping for sync
        task_mapping.append({
            'task_id': task_id,
            'phase': phase,
            'github_text': text,
            'todowrite_index': len(todowrite_tasks) - 1,
            'status': status
        })

    return {
        'issue_number': issue_number,
        'issue_title': issue_title,
        'todowrite_tasks': todowrite_tasks,
        'task_mapping': task_mapping,
        'metadata': {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.get('completed', False)),
            'pending_tasks': sum(1 for t in tasks if not t.get('completed', False))
        }
    }


def main():
    """
    Main entry point.
    Expects parsed Issue JSON from stdin.
    """
    try:
        # Read parsed Issue data
        parsed_issue = json.load(sys.stdin)

        # Convert to TodoWrite format
        result = convert_to_todowrite(parsed_issue)

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
