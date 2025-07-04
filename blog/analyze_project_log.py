#!/usr/bin/env python3
"""
Analyze project_log.txt to extract key timeline events and story beats
for the blog post rewrite.
"""

import re
from datetime import datetime
from collections import defaultdict

def extract_key_events(log_file_path):
    """Extract key events, decisions, and story beats from the project log."""
    
    key_events = []
    current_session = None
    
    # Patterns to identify important moments
    patterns = {
        'session_start': r'q chat',
        'initial_request': r'> I need to get files of demographic information',
        'data_discovery': r'Census|API|demographic|population',
        'script_creation': r'\.py|creating|writing|script',
        'problem_discovery': r'error|issue|problem|fix|bug',
        'consolidation': r'consolidat|cleanup|refactor|simplif',
        'principles': r'principle|framework|methodology|approach',
        'success': r'success|working|complete|finish'
    }
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_chunk = []
        chunk_size = 100
        
        for i, line in enumerate(lines):
            current_chunk.append((i+1, line.strip()))
            
            # Process chunks
            if len(current_chunk) >= chunk_size or i == len(lines) - 1:
                # Analyze this chunk
                chunk_events = analyze_chunk(current_chunk, patterns)
                key_events.extend(chunk_events)
                current_chunk = []
                
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []
    
    return key_events

def analyze_chunk(chunk, patterns):
    """Analyze a chunk of log lines for key events."""
    events = []
    
    for line_num, line in chunk:
        # Skip empty lines and pure formatting
        if not line or line.startswith('─') or line.startswith('╭') or line.startswith('│'):
            continue
            
        # Look for key patterns
        for event_type, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                events.append({
                    'line_num': line_num,
                    'type': event_type,
                    'content': line[:200],  # Truncate long lines
                    'context': get_context(chunk, line_num)
                })
                break
    
    return events

def get_context(chunk, target_line_num):
    """Get surrounding context for an event."""
    context_lines = []
    for line_num, line in chunk:
        if abs(line_num - target_line_num) <= 2 and line.strip():
            context_lines.append(line[:100])
    return context_lines[:5]  # Limit context

def categorize_events(events):
    """Categorize events into the 3-act structure."""
    
    act1_events = []  # Initial request and magic
    act2_events = []  # Problems and script sprawl
    act3_events = []  # Principles and resolution
    
    # Simple heuristic based on event types and content
    for event in events:
        content_lower = event['content'].lower()
        
        if (event['type'] in ['initial_request', 'data_discovery'] or 
            'census' in content_lower or 'demographic' in content_lower):
            act1_events.append(event)
        elif (event['type'] in ['problem_discovery', 'script_creation'] or
              'error' in content_lower or 'script' in content_lower):
            act2_events.append(event)
        elif (event['type'] in ['consolidation', 'principles', 'success'] or
              'principle' in content_lower or 'cleanup' in content_lower):
            act3_events.append(event)
    
    return {
        'act1': act1_events[:10],  # Limit to most relevant
        'act2': act2_events[:15],
        'act3': act3_events[:10]
    }

def main():
    log_path = 'project_log.txt'
    
    print("Analyzing project log for key events...")
    events = extract_key_events(log_path)
    
    print(f"\nFound {len(events)} potential key events")
    
    # Categorize into 3-act structure
    categorized = categorize_events(events)
    
    print("\n" + "="*60)
    print("ACT 1: THE MAGIC (Initial Request & Discovery)")
    print("="*60)
    for event in categorized['act1']:
        print(f"Line {event['line_num']}: {event['content']}")
        print()
    
    print("\n" + "="*60)
    print("ACT 2: THE MESS (Problems & Script Sprawl)")
    print("="*60)
    for event in categorized['act2']:
        print(f"Line {event['line_num']}: {event['content']}")
        print()
    
    print("\n" + "="*60)
    print("ACT 3: THE RESOLUTION (Principles & Success)")
    print("="*60)
    for event in categorized['act3']:
        print(f"Line {event['line_num']}: {event['content']}")
        print()

if __name__ == "__main__":
    main()
