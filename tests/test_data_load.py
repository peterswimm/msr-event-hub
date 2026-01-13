#!/usr/bin/env python
from storage.event_data import get_event_data

data = get_event_data()
print(f'Data loaded: {bool(data)}')
print(f'Keys: {list(data.keys())}')
projects = data.get('projects', [])
print(f'Projects count: {len(projects)}')
if projects:
    proj = projects[0]
    print(f'First project: {proj.get("name")}')
    team = proj.get('team', [])
    print(f'Team members: {[m.get("displayName") for m in team]}')
    print(f'Full first project keys: {list(proj.keys())}')
