#!/usr/bin/env python3
"""Test script to verify smart question detection."""

from services.desktop_service import handle_command

tests = [
    'what is python',
    'open google.com',
    'find youtube files',
    'tell me about AI',
    'who is elon musk',
    'how do i learn coding',
    'open file C:\\Users\\test.txt',
    'explain machine learning',
]

print("Testing smart question detection:")
print("=" * 60)

for test in tests:
    result = handle_command(test)
    action = result.get("action", "none")
    print(f'Command: "{test}"')
    print(f'Action:  {action}')
    if action == "suggest_ai_draft":
        print(f'→ Will suggest AI Draft')
    print()
