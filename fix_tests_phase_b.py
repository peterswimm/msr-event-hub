#!/usr/bin/env python3
"""Fix test files for Phase B event-scoped ProjectDefinition."""

import re
from pathlib import Path

HELPER = '''\n\n# ===== Helper for PHASE B (Event-scoped projects) =====\ndef create_project(**kwargs):\n    """Helper to create ProjectDefinition with required Phase B fields."""\n    if 'event_id' not in kwargs:\n        kwargs['event_id'] = 'event_default'\n    if 'odata_type' not in kwargs:\n        kwargs['odata_type'] = '#microsoft.graph.project'\n    return ProjectDefinition(**kwargs)\n'''

for test_file in ['tests/test_repository.py', 'tests/test_validators.py', 'tests/test_storage.py', 'tests/test_workflows_and_api.py']:
    path = Path(test_file)
    if path.exists():
        content = path.read_text()
        
        # Add helper function if not already there
        if 'def create_project(' not in content:
            imports_end = content.find('# ===')
            if imports_end > 0:
                content = content[:imports_end] + HELPER + content[imports_end:]
        
        # Replace all ProjectDefinition( with create_project(
        new_content = re.sub(r'(\s+)ProjectDefinition\(', r'\1create_project(', content)
        
        path.write_text(new_content)
        print(f'Updated {test_file}')

print('Done!')
