#!/usr/bin/env python3
import os

try:
    with open('.tmp.counter', 'r') as f:
        content = f.read()
        print(f"File contents: '{content}'")
        print(f"Length: {len(content)} characters")
        print(f"Contains 'done': {'done' in content}")
        print(f"Last 10 characters: '{content[-10:]}'")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error: {e}")
