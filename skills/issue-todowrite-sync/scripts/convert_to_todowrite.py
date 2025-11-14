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

    pending_count = sum(1 for t in tasks if not t.get('completed', False))

    # Task count warnings
    warning = None
    if pending_count >= 15:
        warning = {
            'level': 'high',
            'message': f'❌ WARNING: {pending_count} tasks detected (15+ tasks)',
            'recommendation': 'Split into multiple Issues (5-8 tasks per Issue recommended)',
            'recommended_issue_count': (pending_count + 7) // 8
        }
    elif pending_count >= 12:
        warning = {
            'level': 'medium',
            'message': f'⚠️  Note: {pending_count} tasks detected (12+ tasks)',
            'recommendation': 'Consider splitting into 2-3 Issues for better focus'
        }
    elif pending_count >= 8:
        warning = {
            'level': 'low',
            'message': f'📊 Task count: {pending_count} tasks (manageable)'
        }

    return {
        'issue_number': issue_number,
        'issue_title': issue_title,
        'todowrite_tasks': todowrite_tasks,
        'task_mapping': task_mapping,
        'phase_mode': False,
        'smart_default_applied': False,
        'warning': warning,
        'metadata': {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.get('completed', False)),
            'pending_tasks': pending_count
        }
    }


def should_use_phase_mode(parsed_issue, explicit_phase_mode=None):
    """
    Determine whether to use phase-by-phase mode (Smart Default).

    Args:
        parsed_issue: Output from issue-parser (dict)
        explicit_phase_mode: User's explicit choice (True/False/None)

    Returns:
        bool: Whether to use phase mode
    """
    # Explicit flag takes precedence
    if explicit_phase_mode is not None:
        return explicit_phase_mode

    # Smart Default: Auto-detect based on task count and phase info
    tasks = parsed_issue.get('tasks', [])
    phases = parsed_issue.get('phases', [])

    # Count pending (incomplete) tasks only
    pending_task_count = len([t for t in tasks if not t.get('completed', False)])

    # Enable phase mode if:
    # 1. 8+ pending tasks AND
    # 2. Multiple phases exist (>1)
    has_multiple_phases = len(phases) > 1

    return pending_task_count >= 8 and has_multiple_phases


def convert_to_todowrite_by_phase(parsed_issue, target_phase=None, phase_mode=None):
    """
    Convert parsed Issue data to TodoWrite format with Phase filtering.

    Smart Default: Automatically enables phase-by-phase mode for large Issues.

    Args:
        parsed_issue: Output from issue-parser (dict)
        target_phase: Specific phase name to filter (None = auto-select first pending phase)
        phase_mode: Explicit mode choice (True/False/None for auto-detect)

    Returns:
        dict: TodoWrite tasks and metadata with phase information
    """
    # Smart Default: Auto-detect if phase_mode not explicitly set
    use_phase_mode = should_use_phase_mode(parsed_issue, phase_mode)

    if not use_phase_mode:
        # Fallback to standard conversion
        return convert_to_todowrite(parsed_issue)

    tasks = parsed_issue.get('tasks', [])
    phases = parsed_issue.get('phases', [])
    issue_number = parsed_issue.get('issue_number')
    issue_title = parsed_issue.get('title', '')

    # Auto-select target phase if not specified
    if not target_phase and phases:
        # Find first phase with pending tasks
        for phase in phases:
            phase_tasks = [t for t in tasks if t.get('phase') == phase]
            if any(not t.get('completed', False) for t in phase_tasks):
                target_phase = phase
                break

        # If no pending tasks found, use first phase
        if not target_phase:
            target_phase = phases[0] if phases else 'General'

    if not target_phase:
        target_phase = 'General'

    # Filter tasks by target phase
    phase_tasks = [t for t in tasks if t.get('phase') == target_phase]

    todowrite_tasks = []
    task_mapping = []

    for task in phase_tasks:
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

    # Calculate phase progress
    current_phase_index = phases.index(target_phase) if target_phase in phases else 0
    phase_progress = f"{current_phase_index + 1}/{len(phases)}" if phases else "1/1"

    # Count tasks by phase
    phase_summary = {}
    for phase in phases:
        phase_tasks_count = [t for t in tasks if t.get('phase') == phase]
        completed_count = sum(1 for t in phase_tasks_count if t.get('completed', False))
        phase_summary[phase] = {
            'total': len(phase_tasks_count),
            'completed': completed_count,
            'pending': len(phase_tasks_count) - completed_count
        }

    total_pending = sum(1 for t in tasks if not t.get('completed', False))
    current_phase_pending = sum(1 for t in phase_tasks if not t.get('completed', False))

    # Task count warnings
    warning = None
    if total_pending >= 15:
        warning = {
            'level': 'high',
            'message': f'❌ WARNING: {total_pending} total tasks in Issue',
            'recommendation': 'Use --phase-by-phase to work in smaller chunks (3-5 tasks at a time)',
            'current_phase_tasks': current_phase_pending
        }
    elif current_phase_pending >= 12:
        warning = {
            'level': 'medium',
            'message': f'⚠️  Note: Creating {current_phase_pending} TodoWrite tasks',
            'recommendation': 'Consider using --phase-by-phase for better focus'
        }
    elif current_phase_pending >= 8:
        warning = {
            'level': 'low',
            'message': f'📊 Creating {current_phase_pending} tasks for current phase'
        }

    return {
        'issue_number': issue_number,
        'issue_title': issue_title,
        'todowrite_tasks': todowrite_tasks,
        'task_mapping': task_mapping,
        'phase_mode': True,
        'smart_default_applied': phase_mode is None,  # True if auto-detected
        'current_phase': target_phase,
        'all_phases': phases,
        'phase_progress': phase_progress,
        'phase_summary': phase_summary,
        'warning': warning,
        'metadata': {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for t in tasks if t.get('completed', False)),
            'pending_tasks': total_pending,
            'current_phase_tasks': len(phase_tasks),
            'current_phase_completed': sum(1 for t in phase_tasks if t.get('completed', False)),
            'current_phase_pending': current_phase_pending
        }
    }


def main():
    """
    Main entry point.
    Expects parsed Issue JSON from stdin.

    Smart Default: Automatically uses phase-by-phase mode for large Issues
    (8+ pending tasks with multiple phases).
    """
    try:
        # Read parsed Issue data
        parsed_issue = json.load(sys.stdin)

        # Use smart default conversion (auto-detects phase mode)
        result = convert_to_todowrite_by_phase(parsed_issue, phase_mode=None)

        # Display warning if present
        if result.get('warning'):
            warning = result['warning']
            print(warning['message'], file=sys.stderr)
            if 'recommendation' in warning:
                print(f"💡 {warning['recommendation']}", file=sys.stderr)

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
