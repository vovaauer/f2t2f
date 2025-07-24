import os
from pathlib import Path
import fnmatch
from typing import Optional

import click
from patch import fromstring

from .config import load_config
from .file_filter import parse_f2t2f_list, is_path_matched


def read_directory_structure(path: Path) -> dict:
    """
    Recursively reads a directory structure and its file contents.
    Returns a dictionary representing the structure, honoring a .f2t2f file or global config.
    """
    list_file_path = path / ".f2t2f"
    list_rules = parse_f2t2f_list(list_file_path)

    if list_rules:
        list_type, list_patterns = list_rules
        click.echo(f"Found .f2t2f file. Using '{list_type}' rules.")
        # We pass the root `path` down so relative path matching works correctly
        structure = _read_directory_recursive_with_list(path, path, list_type, list_patterns)
        if not structure:
             # Return an empty structure for the root if everything is filtered out
            return {"name": path.name, "type": "folder", "children": []}
        return structure
    else:
        click.echo("No .f2t2f file found. Using global ignore patterns from config.")
        config = load_config()
        ignore_patterns = config.get("ignore_patterns", [])
        return _read_directory_recursive_with_global_ignore(path, ignore_patterns)

def _read_directory_recursive_with_global_ignore(path: Path, ignore_patterns: list) -> dict:
    """Internal recursive helper function using global ignore patterns."""
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if path.is_file():
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = "[Binary file - content not readable as text]"
        except Exception as e:
            content = f"[Error reading file: {e}]"
        return {"name": path.name, "type": "file", "content": content}

    if path.is_dir():
        children = []
        for item in sorted(path.iterdir()):
            is_ignored = any(fnmatch.fnmatch(item.name, pattern) for pattern in ignore_patterns)
            if is_ignored:
                continue
            child_structure = _read_directory_recursive_with_global_ignore(item, ignore_patterns)
            if child_structure:
                children.append(child_structure)
        return {"name": path.name, "type": "folder", "children": children}
    return {}

def _read_directory_recursive_with_list(current_path: Path, root_path: Path, list_type: str, patterns: list) -> Optional[dict]:
    """Internal recursive helper for .f2t2f whitelist/blacklist logic."""
    if not current_path.exists():
        return None

    # Always ignore the list file itself
    if current_path == root_path / ".f2t2f":
        return None

    is_matched = is_path_matched(current_path, root_path, patterns)

    if list_type == "blacklist" and is_matched:
        return None  # Skip this item and its descendants

    if current_path.is_file():
        if list_type == "whitelist" and not is_path_matched(current_path, root_path, patterns):
            return None  # File not in whitelist, skip it
        try:
            content = current_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = "[Binary file - content not readable as text]"
        except Exception as e:
            content = f"[Error reading file: {e}]"
        return {"name": current_path.name, "type": "file", "content": content}

    if current_path.is_dir():
        children = []
        for item in sorted(current_path.iterdir()):
            child_structure = _read_directory_recursive_with_list(item, root_path, list_type, patterns)
            if child_structure:
                children.append(child_structure)

        if list_type == "whitelist" and not is_matched and not children:
            return None  # Prune empty directories that weren't explicitly whitelisted

        return {"name": current_path.name, "type": "folder", "children": children}
    return None

def create_directory_from_structure(structure_data: dict, base_path: Path):
    """
    Recursively creates a directory structure and files from a dictionary.
    """
    current_path = base_path / structure_data['name']

    if structure_data['type'] == 'folder':
        current_path.mkdir(exist_ok=True)
        for child in structure_data.get('children', []):
            create_directory_from_structure(child, current_path)

    elif structure_data['type'] == 'file':
        content = structure_data.get('content', '')
        current_path.write_text(content, encoding='utf-8')

def apply_diff_patch(patch_data: dict, base_path: Path):
    """
    Applies a diff patch to a file using a unified diff format.
    """
    target_file_rel_path = patch_data['path']
    diff_content = patch_data['diff_content']

    try:
        patch_set = fromstring(diff_content.encode('utf-8'))
        if patch_set.apply(root=base_path):
            click.secho(f"  -> Applied diff to '{target_file_rel_path}'", fg="cyan")
        else:
            raise RuntimeError(f"Failed to apply diff to '{target_file_rel_path}'. The file content may not match patch.")
    except Exception as e:
        raise RuntimeError(f"Error applying diff patch to '{target_file_rel_path}': {e}")


def apply_patch(patch_data: dict, base_path: Path):
    """
    Applies a 'replace_lines' patch to a single file.
    """
    target_file = base_path / patch_data['path']
    action = patch_data['action']

    if not target_file.exists():
        raise FileNotFoundError(f"Cannot apply patch. File not found: {target_file}")

    if action == "replace_lines":
        start_line, end_line = patch_data['lines']
        start_index = start_line - 1
        end_index = end_line

        original_lines = target_file.read_text(encoding='utf-8').splitlines()

        if start_index < 0 or end_index > len(original_lines):
            raise ValueError(f"Line numbers [{start_line}-{end_line}] are out of bounds for file {target_file} which has {len(original_lines)} lines.")

        new_content_lines = patch_data['content'].splitlines()
        final_lines = original_lines[:start_index] + new_content_lines + original_lines[end_index:]
        target_file.write_text('\n'.join(final_lines) + '\n', encoding='utf-8')
        click.secho(f"  -> Patched lines {start_line}-{end_line} in '{target_file.name}'", fg="cyan")
    else:
        raise ValueError(f"Unknown patch action: {action}")