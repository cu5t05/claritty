import json
import sys
from pathlib import Path

class UsageError(Exception):
    """Raised for invalid command-line arguments"""
    pass

class SelectorError(Exception):
    """Raised for invalid selector syntax or traversal errors"""
    pass

def main():
    """Main entry point with error handling"""
    exit_code = 0
    try:
        args = parse_args()
        data = load_json(args['file'])
        print("---output---")
        if args['flag'] == '-pretty':
            handle_pretty(args['file'], data)
        elif args['flag'] == '-view':
            handle_view(data, args['selector'])
    except FileNotFoundError as e:
        print(f"Error: File not found: {e.filename}")
        exit_code = 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e.msg} at line {e.lineno}")
        exit_code = 1
    except UsageError as e:
        print(f"Error: {e}")
        print("Usage: jsonize -pretty|-view <file> [selector]")
        exit_code = 1
    except SelectorError as e:
        print(f"Error: {e}")
        exit_code = 1
    except Exception as e:
        print(f"Error: {e}")
        exit_code = 1
    finally:
        sys.exit(exit_code)

def parse_args():
    if len(sys.argv) < 3:
        raise UsageError("Missing required arguments")
    flag = sys.argv[1]
    if not flag.startswith('-'):
        raise UsageError("First argument must be a flag")
    if flag not in ['-pretty', '-view']:
        raise UsageError(f"Unknown flag: {flag}")
    file_path = sys.argv[2]
    if flag == '-view':
        if len(sys.argv) < 4:
            raise UsageError("Flag -view requires selector")
        selector = sys.argv[3]
    else:
        selector = None
    return {'flag': flag, 'file': file_path, 'selector': selector}

def load_json(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(file_path)
    if not path.is_file():
        raise UsageError(f"Not a file: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def handle_pretty(file_path, data):
    path = Path(file_path)
    output = path.with_name(path.stem + "-PRETTIED.json")
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Written to {output}")

def handle_view(data, selector):
    if '++' in selector:
        handle_view_multi(data, selector)
        return
    segments = parse_selector(selector)
    results = traverse(data, segments, 0, "")
    if not results:
        print(f"Info: No results for selector: {selector}")
    else:
        for i, result in enumerate(results):
            print(json.dumps(result, indent=2))
            if i < len(results) - 1:
                print("---")

def handle_view_multi(data, selector):
    """Handle ++ multi-field selector.

    Syntax: <prefix>:<field1>++<field2>:<sub>++...
    Left side of first ++ is split at last colon into prefix + first branch.
    All ++ right-hand sides are additional branches.
    Each branch is traversed from the shared prefix node and printed labeled.

    Example:
        vulnerabilities:0-4:cve:id++descriptions:0
        prefix   = vulnerabilities:0-4:cve
        branches = [id, descriptions:0]
    """
    parts = selector.split('++')
    first_full = parts[0]
    last_colon = first_full.rfind(':')
    if last_colon == -1:
        raise SelectorError("++ selector requires at least two path segments on the left side")
    prefix = first_full[:last_colon]
    first_branch = first_full[last_colon + 1:]
    branches = [first_branch] + parts[1:]

    prefix_segments = parse_selector(prefix)
    nodes = traverse(data, prefix_segments, 0, "")

    if not nodes:
        print(f"Info: No results for prefix: {prefix}")
        return

    for i, node in enumerate(nodes):
        for branch in branches:
            branch_segments = parse_selector(branch)
            label = resolve_label(node, branch_segments)
            results = traverse(node, branch_segments, 0, "")
            value = results[0] if results else None
            if isinstance(value, str):
                print(f"{label}: {value}")
            else:
                print(f"{label}: {json.dumps(value, indent=2)}")
        if i < len(nodes) - 1:
            print("---")

def resolve_label(node, segments):
    """Derive a human-readable label from a branch by walking segments.

    Rules per segment:
      key   → use the key name as-is
      index → if node is dict, resolve to the actual key name at that position
              if node is list, use the numeric index as string
      range → not expected in a branch label context, use raw repr
    Segments joined by '_'.
    """
    parts = []
    current = node
    for seg in segments:
        if seg['type'] == 'key':
            parts.append(seg['value'])
            if isinstance(current, dict) and seg['value'] in current:
                current = current[seg['value']]
        elif seg['type'] == 'index':
            idx = seg['value']
            if isinstance(current, dict):
                keys = list(current.keys())
                if idx < len(keys):
                    parts.append(keys[idx])
                    current = current[keys[idx]]
                else:
                    parts.append(str(idx))
            elif isinstance(current, list):
                parts.append(str(idx))
                if idx < len(current):
                    current = current[idx]
            else:
                parts.append(str(idx))
        elif seg['type'] == 'range':
            end_repr = '*' if seg['end'] is None else seg['end']
            parts.append(f"{seg['start']}_{end_repr}")
    return '_'.join(parts)

def parse_selector(selector):
    """Convert selector string to traversal segments.

    Segment rules:
      "key"  → quoted string: exact key match only, never positional
      0      → unquoted integer: strictly positional on dict or list
      0-4    → numeric range: positional range on dict or list
      cve    → unquoted string: exact key match on dict only

    No fallbacks. Wrong type or missing target → SelectorError.
    """
    if not selector:
        raise SelectorError("Empty selector")
    parsed = []
    for seg in selector.split(':'):
        seg = seg.strip()

        # Quoted string — exact key, protected from numeric interpretation
        if seg.startswith('"') and seg.endswith('"') and len(seg) >= 2:
            parsed.append({'type': 'key', 'value': seg[1:-1], 'quoted': True})
            continue

        # Numeric range e.g. 0-4 or open-ended 0-*
        if '-' in seg:
            parts = seg.split('-')
            if len(parts) == 2 and parts[0].isdigit() and (parts[1].isdigit() or parts[1] == '*'):
                start = int(parts[0])
                end = None if parts[1] == '*' else int(parts[1])
                if start < 0:
                    raise SelectorError(f"Range start must be non-negative: {seg}")
                if end is not None and end < start:
                    raise SelectorError(f"Invalid range (end < start): {seg}")
                parsed.append({'type': 'range', 'start': start, 'end': end})
                continue

        # Unquoted integer — strictly positional
        if seg.isdigit():
            parsed.append({'type': 'index', 'value': int(seg)})
            continue

        # Unquoted string — exact key match
        if seg:
            parsed.append({'type': 'key', 'value': seg})
            continue

        raise SelectorError(f"Invalid selector segment: '{seg}'")

    return parsed

def traverse(data, segments, depth, path):
    """Recursively navigate JSON structure.

    Traversal rules (no fallbacks):
      index  → positional: nth key of dict, or nth item of list
      range  → positional range: keys[start:end+1] or items[start:end+1]
      key    → exact string key on dict only; error if not found or not a dict
    """
    if depth >= len(segments):
        return [data]

    segment = segments[depth]
    results = []

    if segment['type'] == 'range':
        end_repr = '*' if segment['end'] is None else segment['end']
        seg_repr = f"{segment['start']}-{end_repr}"
    elif segment['type'] == 'key' and segment.get('quoted'):
        seg_repr = f'"{segment["value"]}"'
    else:
        seg_repr = str(segment.get('value', '?'))
    current_path = f"{path}:{seg_repr}" if path else seg_repr

    if segment['type'] == 'key':
        if not isinstance(data, dict):
            raise SelectorError(f"Key '{segment['value']}' at '{current_path}' requires a dict, got {type(data).__name__}")
        key = segment['value']
        if key not in data:
            raise SelectorError(f"Key not found at '{current_path}': '{key}'")
        results = traverse(data[key], segments, depth + 1, current_path)

    elif segment['type'] == 'index':
        idx = segment['value']
        if isinstance(data, list):
            if idx >= len(data):
                raise SelectorError(f"Index {idx} out of range at '{current_path}' (list length: {len(data)})")
            results = traverse(data[idx], segments, depth + 1, current_path)
        elif isinstance(data, dict):
            keys = list(data.keys())
            if idx >= len(keys):
                raise SelectorError(f"Position {idx} out of range at '{current_path}' (dict size: {len(keys)})")
            results = traverse(data[keys[idx]], segments, depth + 1, current_path)
        else:
            raise SelectorError(f"Cannot apply index at '{current_path}' on {type(data).__name__}")

    elif segment['type'] == 'range':
        start = segment['start']
        if isinstance(data, list):
            end = len(data) - 1 if segment['end'] is None else segment['end']
            if end >= len(data):
                raise SelectorError(f"Range end {end} exceeds list length {len(data)} at '{current_path}'")
            for i in range(start, end + 1):
                results.extend(traverse(data[i], segments, depth + 1, f"{current_path}[{i}]"))
        elif isinstance(data, dict):
            keys = list(data.keys())
            end = len(keys) - 1 if segment['end'] is None else segment['end']
            if end >= len(keys):
                raise SelectorError(f"Range end {end} exceeds dict size {len(keys)} at '{current_path}'")
            for i in range(start, end + 1):
                results.extend(traverse(data[keys[i]], segments, depth + 1, f"{current_path}[{i}]"))
        else:
            raise SelectorError(f"Cannot apply range at '{current_path}' on {type(data).__name__}")

    return results

if __name__ == "__main__":
    main()