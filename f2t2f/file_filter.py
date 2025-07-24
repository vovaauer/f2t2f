import fnmatch
from pathlib import Path
from typing import List, Optional, Tuple

def parse_f2t2f_list(list_path: Path) -> Optional[Tuple[str, List[str]]]:
    """
    Parses a .f2t2f file and returns a tuple of (type, patterns) or None if not found or malformed.
    """
    if not list_path.is_file():
        return None

    content = list_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    if not lines or not lines[0].lower().startswith("type:"):
        return None

    list_type = lines[0].replace("type:", "").strip().lower()
    if list_type not in ["whitelist", "blacklist"]:
        return None

    try:
        separator_index = -1
        for i, line in enumerate(lines):
            if line.strip() == "---":
                separator_index = i
                break
        if separator_index == -1:
            return None
    except ValueError:
        return None

    patterns = [
        line.strip() for line in lines[separator_index + 1:]
        if line.strip() and not line.strip().startswith("#")
    ]

    return list_type, patterns

def is_path_matched(item_path: Path, root_path: Path, patterns: List[str]) -> bool:
    """
    Checks if an item path matches any of the given patterns.
    Handles absolute paths, relative paths (with / or \), and glob patterns.
    """
    try:
        item_rel_path = item_path.relative_to(root_path)
    except ValueError:
        # This can happen if item_path is not within root_path, e.g. symlinks
        # In this case, we can only match by absolute path or name.
        item_rel_path = None

    item_abs_path_str = str(item_path.resolve())
    item_name = item_path.name

    for pattern in patterns:
        # Normalize pattern separators for consistent matching
        normalized_pattern = pattern.replace('\\', '/')

        # 1. Absolute path match
        if Path(pattern).is_absolute():
            if Path(item_abs_path_str).resolve() == Path(pattern).resolve():
                return True
            continue

        # 2. Glob match on filename only (e.g., "*.pyc", ".git")
        if fnmatch.fnmatch(item_name, normalized_pattern):
            return True

        # 3. Glob match on relative path (e.g., "build/*", "src/**/*.py")
        if item_rel_path and fnmatch.fnmatch(item_rel_path.as_posix(), normalized_pattern):
            return True

    return False