import os
from pathlib import Path
import fnmatch

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