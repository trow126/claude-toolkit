#!/usr/bin/env python3
"""
Progress Tracker - Automatic GitHub Issue Synchronization

Monitors TodoWrite completion and automatically:
- Posts progress comments to GitHub Issues
- Auto-closes Issues when all tasks are complete
"""

import json
import sys
import subprocess
from pathlib import Path
import os
from typing import Dict, List, Optional


class ProgressSync:
    def __init__(self):
        self.issue_number = os.environ.get('CURRENT_ISSUE_NUMBER')
        self.session_dir = Path.home() / '.claude' / '.session'
        self.mapping_file = self.session_dir / 'issue_mapping.json'

        # Ensure session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def check_gh_cli(self):
        """Verify gh CLI is available"""
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("gh CLI is not available. Install from https://cli.github.com/")

    def load_todowrite_state(self) -> List[Dict]:
        """Load current TodoWrite state from stdin"""
        try:
            stdin_data = sys.stdin.read().strip()
            if not stdin_data:
                return []
            return json.loads(stdin_data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

    def load_mapping(self) -> Optional[Dict]:
        """Load Issue-TodoWrite mapping from session"""
        if not self.mapping_file.exists():
            print(f"Warning: Mapping file not found: {self.mapping_file}", file=sys.stderr)
            return None

        try:
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid mapping file: {e}", file=sys.stderr)
            return None

    def save_mapping(self, mapping: Dict):
        """Save updated mapping to session"""
        with open(self.mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)

    def calculate_progress(self, todowrite_state: List[Dict], mapping: Dict) -> Dict:
        """Calculate progress metrics"""
        total_tasks = len(mapping['task_mapping'])

        # Count completed tasks
        completed_count = 0
        completed_indices = []

        for i, task in enumerate(todowrite_state):
            if task.get('status') == 'completed':
                completed_count += 1
                completed_indices.append(i)

        completion_pct = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

        return {
            'total': total_tasks,
            'completed': completed_count,
            'percentage': completion_pct,
            'completed_indices': completed_indices
        }

    def has_new_completions(self, current_progress: Dict, mapping: Dict) -> bool:
        """Check if there are new completions since last sync"""
        last_synced = mapping.get('last_synced_completed', 0)
        return current_progress['completed'] > last_synced

    def get_newly_completed_tasks(self,
                                   todowrite_state: List[Dict],
                                   mapping: Dict,
                                   current_progress: Dict) -> List[str]:
        """Get list of newly completed task texts"""
        last_completed_indices = set(mapping.get('completed_indices', []))
        current_completed_indices = set(current_progress['completed_indices'])

        new_indices = current_completed_indices - last_completed_indices

        newly_completed = []
        for idx in new_indices:
            if idx < len(todowrite_state):
                task = todowrite_state[idx]
                # Try to find task text from mapping
                for map_entry in mapping['task_mapping']:
                    if map_entry.get('todowrite_index') == idx:
                        newly_completed.append(map_entry['task_text'])
                        break
                else:
                    # Fallback to content from TodoWrite
                    newly_completed.append(task.get('content', f'Task #{idx+1}'))

        return newly_completed

    def post_progress_comment(self, task_text: str, progress: Dict):
        """Post progress update to GitHub Issue"""
        comment_body = f"""✅ **Task Completed**: {task_text}

**Progress**: {progress['completed']}/{progress['total']} tasks ({progress['percentage']:.1f}%)

---
_Updated automatically by progress-tracker skill_"""

        try:
            subprocess.run(
                ['gh', 'issue', 'comment', str(self.issue_number), '--body', comment_body],
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            print(f"Posted progress comment for task: {task_text}")
        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout posting comment, retrying once...", file=sys.stderr)
            # Retry once
            try:
                subprocess.run(
                    ['gh', 'issue', 'comment', str(self.issue_number), '--body', comment_body],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                print(f"Posted progress comment for task: {task_text} (retry succeeded)")
            except Exception as e:
                print(f"Error: Failed to post comment after retry: {e}", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to post comment: {e.stderr}", file=sys.stderr)

    def close_issue(self):
        """Close GitHub Issue with completion comment"""
        completion_body = """🎉 **All tasks completed!**

This Issue has been automatically closed because all tasks are done.

---
_Closed automatically by progress-tracker skill_"""

        try:
            # Post completion comment
            subprocess.run(
                ['gh', 'issue', 'comment', str(self.issue_number), '--body', completion_body],
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Close Issue
            subprocess.run(
                ['gh', 'issue', 'close', str(self.issue_number), '--reason', 'completed'],
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            print(f"Issue #{self.issue_number} automatically closed")
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to close Issue: {e.stderr}", file=sys.stderr)

    def run(self):
        """Main execution flow"""
        try:
            # Validate environment
            if not self.issue_number:
                print("Warning: CURRENT_ISSUE_NUMBER not set, skipping sync", file=sys.stderr)
                return

            # Check gh CLI
            self.check_gh_cli()

            # Load data
            todowrite_state = self.load_todowrite_state()
            mapping = self.load_mapping()

            if not mapping:
                print("No mapping found, skipping sync")
                return

            # Calculate progress
            current_progress = self.calculate_progress(todowrite_state, mapping)

            # Check for new completions
            if not self.has_new_completions(current_progress, mapping):
                print("No new completions, skipping sync")
                return

            # Get newly completed tasks
            newly_completed = self.get_newly_completed_tasks(
                todowrite_state,
                mapping,
                current_progress
            )

            # Post updates for each newly completed task
            for task_text in newly_completed:
                self.post_progress_comment(task_text, current_progress)

            # Update mapping
            mapping['last_synced_completed'] = current_progress['completed']
            mapping['completed_indices'] = current_progress['completed_indices']
            self.save_mapping(mapping)

            # Check for auto-close
            auto_close = mapping.get('auto_close', True)
            all_complete = current_progress['completed'] == current_progress['total']

            if auto_close and all_complete:
                self.close_issue()

        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    sync = ProgressSync()
    sync.run()
