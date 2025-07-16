import os
from pathlib import Path
import fnmatch
import click

from .config import load_config

def read_directory_structure(path: Path) -> dict:
    """
    Recursively reads a directory structure and its file contents.
    Returns a dictionary representing the structure, ignoring specified patterns.
    """
    config = load_config()
    ignore_patterns = config.get("ignore_patterns", [])
    return _read_directory_recursive(path, ignore_patterns)

def _read_directory_recursive(path: Path, ignore_patterns: list) -> dict:
    """Internal recursive helper function."""
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
            
            child_structure = _read_directory_recursive(item, ignore_patterns)
            if child_structure:
                children.append(child_structure)

        return {"name": path.name, "type": "folder", "children": children}
    
    return {}

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

def apply_patch(patch_data: dict, base_path: Path):
    """
    Applies a patch to a single file.
    
    Args:
        patch_data: A dictionary with 'path', 'action', 'lines', and 'content'.
        base_path: The root directory where the patch should be applied.
    """
    target_file = base_path / patch_data['path']
    action = patch_data['action']
    
    if not target_file.exists():
        raise FileNotFoundError(f"Cannot apply patch. File not found: {target_file}")

    if action == "replace_lines":
        start_line, end_line = patch_data['lines']
        
        # Human-readable lines (1-indexed) to 0-indexed list
        start_index = start_line - 1
        end_index = end_line # The slice will go up to, but not including, this index

        original_lines = target_file.read_text(encoding='utf-8').splitlines()

        if start_index < 0 or end_index > len(original_lines):
            raise ValueError(f"Line numbers [{start_line}-{end_line}] are out of bounds for file {target_file} which has {len(original_lines)} lines.")
        
        new_content_lines = patch_data['content'].splitlines()
        
        # Reconstruct the file
        final_lines = original_lines[:start_index] + new_content_lines + original_lines[end_index:]
        
        # Write back, ensuring a trailing newline for POSIX compatibility
        target_file.write_text('\n'.join(final_lines) + '\n', encoding='utf-8')
        click.secho(f"  -> Patched lines {start_line}-{end_line} in '{target_file.name}'", fg="cyan")
    else:
        raise ValueError(f"Unknown patch action: {action}")