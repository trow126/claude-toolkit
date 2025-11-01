#!/usr/bin/env python3
"""
Sync TodoWrite progress back to GitHub Issue
"""

import json
import sys
import subprocess
from datetime import datetime


def generate_progress_comment(task_text, completed_count, total_count):
    """
    Generate progress comment for GitHub Issue.

    Args:
        task_text: The completed task text
        completed_count: Number of completed tasks
        total_count: Total number of tasks

    Returns:
        str: Formatted comment text
    """
    percentage = (completed_count / total_count * 100) if total_count > 0 else 0

    comment = f"""✅ **Task Completed**: {task_text}

**Progress**: {completed_count}/{total_count} tasks ({percentage:.1f}%)

---
_Updated automatically by issue-todowrite-sync skill_
"""
    return comment


def post_issue_comment(issue_number, comment_body):
    """
    Post comment to GitHub Issue using gh CLI.

    Args:
        issue_number: Issue number
        comment_body: Comment text

    Returns:
        bool: Success status
    """
    try:
        result = subprocess.run(
            ['gh', 'issue', 'comment', str(issue_number), '--body', comment_body],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error posting comment: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: gh CLI not found", file=sys.stderr)
        return False


def should_close_issue(completed_count, total_count):
    """
    Determine if Issue should be auto-closed.

    Args:
        completed_count: Number of completed tasks
        total_count: Total number of tasks

    Returns:
        bool: True if all tasks completed
    """
    return total_count > 0 and completed_count == total_count


def close_issue(issue_number):
    """
    Close GitHub Issue.

    Args:
        issue_number: Issue number

    Returns:
        bool: Success status
    """
    completion_comment = f"""🎉 **All tasks completed!**

This Issue has been automatically closed as all tasks are now complete.

---
_Closed automatically by issue-todowrite-sync skill_
_Closed at: {datetime.now().isoformat()}_
"""

    try:
        # Post completion comment
        subprocess.run(
            ['gh', 'issue', 'comment', str(issue_number), '--body', completion_comment],
            capture_output=True,
            text=True,
            check=True
        )

        # Close issue
        subprocess.run(
            ['gh', 'issue', 'close', str(issue_number), '--reason', 'completed'],
            capture_output=True,
            text=True,
            check=True
        )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {e.stderr}", file=sys.stderr)
        return False


def sync_progress(sync_data):
    """
    Sync TodoWrite progress to GitHub Issue.

    Args:
        sync_data: dict with issue_number, completed_task, progress info

    Returns:
        dict: Sync result
    """
    issue_number = sync_data.get('issue_number')
    completed_task = sync_data.get('completed_task', {})
    completed_count = sync_data.get('completed_count', 0)
    total_count = sync_data.get('total_count', 0)
    auto_close = sync_data.get('auto_close', True)

    task_text = completed_task.get('content', 'Unknown task')

    # Generate and post progress comment
    comment = generate_progress_comment(task_text, completed_count, total_count)
    comment_posted = post_issue_comment(issue_number, comment)

    result = {
        'issue_number': issue_number,
        'comment_posted': comment_posted,
        'completed_count': completed_count,
        'total_count': total_count,
        'completion_percentage': (completed_count / total_count * 100) if total_count > 0 else 0,
        'issue_closed': False
    }

    # Auto-close if all tasks completed
    if auto_close and should_close_issue(completed_count, total_count):
        issue_closed = close_issue(issue_number)
        result['issue_closed'] = issue_closed

    return result


def main():
    """
    Main entry point.
    Expects sync data JSON from stdin.
    """
    try:
        # Read sync data
        sync_data = json.load(sys.stdin)

        # Sync progress
        result = sync_progress(sync_data)

        # Output result
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
