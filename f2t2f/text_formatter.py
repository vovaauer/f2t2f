import json
from pathlib import Path
import re

# --- V1 Format Constants and Functions ---
F2T2F_V1_MARKER = "f2t2f_folder_structure_v1"

def serialize_to_json(folder_data: dict) -> str:
    """
    Serializes the folder structure dictionary to a V1 JSON string.
    """
    wrapper = {
        "type": F2T2F_V1_MARKER,
        "data": folder_data
    }
    return json.dumps(wrapper, indent=2)

def deserialize_from_json(json_string: str) -> dict:
    """
    Deserializes a V1 JSON string back into a folder structure dictionary.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e.msg} at line {e.lineno}, col {e.colno}.")

    if not isinstance(data, dict):
        raise ValueError("The provided text is not a valid JSON object.")
        
    if data.get("type") != F2T2F_V1_MARKER:
        raise ValueError(f"Not a V1 f2t2f structure (JSON).")
    
    if "data" not in data:
        raise ValueError("V1 f2t2f structure is missing 'data' key.")

    return data["data"]


# --- V2 Format Constants and Functions ---
F2T2F_V2_MARKER = "type: f2t2f_folder_structure_v2"
V2_SEPARATOR = "\n---\n"
V2_FILE_START_PATTERN = re.compile(r"^>>> file: (.*)$", re.MULTILINE)
V2_FILE_END_MARKER = "<<<"

def _generate_tree_string(structure: dict, prefix: str = "", is_last: bool = True) -> str:
    """Recursively generates the string for the tree view."""
    tree = []
    name = structure['name']
    
    # For the root, just print the name. For children, use connectors.
    if prefix:
        tree.append(f"{prefix}{'└── ' if is_last else '├── '}{name}")
        prefix += "    " if is_last else "│   "
    else:
        tree.append(name)
        prefix = ""

    if structure['type'] == 'folder':
        children = sorted(structure.get('children', []), key=lambda x: (x['type'], x['name']))
        for i, child in enumerate(children):
            tree.append(_generate_tree_string(child, prefix, i == len(children) - 1))
            
    return "\n".join(tree)

def _flatten_files(structure: dict, current_path: Path = Path()) -> list:
    """Recursively finds all files and their full paths."""
    files = []
    path = current_path / structure['name']
    if structure['type'] == 'file':
        files.append((path, structure.get('content', '')))
    elif structure['type'] == 'folder':
        for child in structure.get('children', []):
            files.extend(_flatten_files(child, path))
    return files

def serialize_to_v2(folder_data: dict) -> str:
    """
    Serializes the folder structure dictionary to the V2 hybrid text format.
    """
    parts = []
    
    # 1. Header and Tree
    tree_string = _generate_tree_string(folder_data)
    header = f"{F2T2F_V2_MARKER}\n---\ntree:\n{tree_string}"
    parts.append(header)

    # 2. File Content Blocks
    files = _flatten_files(folder_data)
    # Sort files by path for consistent output
    files.sort(key=lambda x: x[0])

    for path, content in files:
        # Use forward slashes for cross-platform compatibility
        posix_path = path.as_posix()
        file_block = f">>> file: {posix_path}\n{content}\n{V2_FILE_END_MARKER}"
        parts.append(file_block)

    return V2_SEPARATOR.join(parts)

def deserialize_from_v2(v2_string: str) -> dict:
    """
    Deserializes a V2 hybrid text string back into a folder structure dictionary.
    """
    if not v2_string.strip().startswith(F2T2F_V2_MARKER):
        raise ValueError("Not a V2 f2t2f structure.")

    parts = v2_string.split(V2_SEPARATOR)
    
    # The tree is for humans/AI; we can rebuild the structure from the file paths.
    # This is more robust than parsing the visual tree.
    file_content_parts = parts[1:]
    
    if not file_content_parts:
        raise ValueError("V2 format is missing file content blocks.")

    # We need to find the root folder name from the paths
    all_paths = []
    for content_part in file_content_parts:
        match = V2_FILE_START_PATTERN.search(content_part)
        if match:
            all_paths.append(Path(match.group(1)))
    
    if not all_paths: # Handle case with only empty folders
        try:
            tree_part = parts[0].split("tree:\n", 1)[1]
            root_name = tree_part.strip().split('\n')[0].replace('/', '')
            return {"name": root_name, "type": "folder", "children": []} # Simplified for now
        except IndexError:
            raise ValueError("Could not determine root from V2 format.")


    # Determine common root path
    first_path_parts = all_paths[0].parts
    root_name = first_path_parts[0]
    
    # The root structure
    root_struct = {"name": root_name, "type": "folder", "children": []}
    
    # A map to quickly find folder dictionaries
    dir_map = {Path(root_name): root_struct}
    
    for full_path_str in file_content_parts:
        match = V2_FILE_START_PATTERN.search(full_path_str)
        if not match:
            continue
            
        path_str = match.group(1)
        # Content is what's between the `>` header and the `\n<` trailer
        content = full_path_str[match.end(0):].strip().rsplit(f"\n{V2_FILE_END_MARKER}", 1)[0]
        
        full_path = Path(path_str)
        
        # Ensure all parent directories exist in the structure
        parent_path = Path(full_path.parts[0])
        for part in full_path.parts[1:-1]:
            current_path = parent_path / part
            if current_path not in dir_map:
                parent_struct = dir_map[parent_path]
                new_dir_struct = {"name": part, "type": "folder", "children": []}
                parent_struct['children'].append(new_dir_struct)
                dir_map[current_path] = new_dir_struct
            parent_path = current_path

        # Add the file
        parent_struct = dir_map[full_path.parent]
        file_struct = {"name": full_path.name, "type": "file", "content": content}
        parent_struct['children'].append(file_struct)
        
    return root_struct


# --- Universal Deserializer ---

def deserialize(text_input: str) -> dict:
    """
    Intelligently deserializes an input string, trying V1 (JSON) then V2.
    """
    stripped_input = text_input.strip()
    if not stripped_input:
        raise ValueError("Input is empty.")

    # Try V1 (JSON) first, as it's stricter
    try:
        return deserialize_from_json(stripped_input)
    except (ValueError, json.JSONDecodeError):
        # If it's not valid V1, proceed to try V2
        pass

    # Try V2
    try:
        return deserialize_from_v2(stripped_input)
    except ValueError as e:
        # Re-raise with a more generic error if both fail
        raise ValueError(f"Input is not a recognized f2t2f format. V2 parser error: {e}")

    raise ValueError("Input is not a recognized f2t2f format.")