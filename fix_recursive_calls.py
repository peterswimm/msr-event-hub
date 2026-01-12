#!/usr/bin/env python3
"""Fix recursive calls in helper functions."""

from pathlib import Path

for test_file in ['tests/test_repository.py', 'tests/test_validators.py', 'tests/test_storage.py', 'tests/test_workflows_and_api.py']:
    path = Path(test_file)
    if path.exists():
        content = path.read_text()
        # Fix the recursive call issue
        content = content.replace('return create_project(**kwargs)', 'return ProjectDefinition(**kwargs)')
        path.write_text(content)
        print(f'Fixed {test_file}')
