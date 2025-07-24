import click
import pyperclip
from pathlib import Path
import re
from patch import fromstring as diff_fromstring

from .folder_ops import read_directory_structure, create_directory_from_structure, apply_patch, apply_diff_patch
from .text_formatter import serialize_to_json, serialize_to_v2, deserialize
from .config import get_config_path, save_default_config

def _unfence_code_block(text: str) -> str:
    """Removes markdown fencing (```) from a code block if present."""
    stripped_text = text.strip()
    lines = stripped_text.splitlines()
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text

def _process_input(text_input: str, destination_path: Path):
    """
    Parses an input string and applies changes by trying strategies in order:
    1. Complete f2t2f V1/V2 structures.
    2. A single, raw unified diff.
    3. A series of `>>>` blocks for files, patches, or diffs.
    """
    stripped_input = text_input.strip()
    if not stripped_input:
        raise ValueError("Input is empty or contains only whitespace.")

    # --- Strategy 1: Try to deserialize as a complete V1 or V2 structure ---
    try:
        structure_data = deserialize(stripped_input)
        click.echo("Detected a complete folder structure. Creating from scratch...")
        base_creation_path = destination_path
        if destination_path.name == structure_data.get('name'):
            click.secho(f"Destination '{destination_path.name}' matches structure root. Overwriting contents.", fg="yellow")
            base_creation_path = destination_path.parent
        create_directory_from_structure(structure_data, base_creation_path)
        click.secho("Folder structure created successfully.", fg='green')
        return
    except ValueError:
        pass  # Not a full structure, proceed to the next strategy.

    # --- Strategy 2: Try to parse the entire input as a single unified diff ---
    try:
        diff_content = _unfence_code_block(stripped_input)
        patch_set = diff_fromstring(diff_content.encode('utf-8'))
        if patch_set and patch_set.items:
            click.echo("Detected a unified diff format. Applying patch...")
            if patch_set.apply(root=destination_path):
                click.secho("Successfully applied diff patch to the project.", fg="cyan")
                click.secho("All operations completed.", fg="bright_green")
                return
            else:
                raise RuntimeError("Failed to apply diff. The file contents may not match the patch, or some hunks were rejected.")
    except Exception:
        pass # Not a parsable diff, or applying it failed. Fall through.

    # --- Strategy 3: Fallback to block-based parsing ---
    block_pattern = re.compile(r">>> (file|patch|diff): (.*?)\n(.*?)\n<<<", re.DOTALL)
    changes_applied = False
    for match in block_pattern.finditer(stripped_input):
        if not changes_applied:
            click.echo("No complete structure or unified diff detected. Processing as file/patch/diff blocks...")
        changes_applied = True
        block_type, path_str, content = match.groups()
        target_path = Path(path_str.strip())

        if block_type == "file":
            full_path = destination_path / target_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(_unfence_code_block(content), encoding='utf-8')
            click.secho(f"  -> Created/Replaced file '{target_path}'", fg="green")

        elif block_type == "patch":
            parts = re.split(r'\r?\n---\r?\n', content, 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid patch for '{target_path}': missing '---' separator.")
            meta, patch_content = parts
            lines_match = re.search(r"lines: (\d+)-(\d+)", meta)
            if not lines_match:
                raise ValueError(f"Invalid patch for '{target_path}': missing 'lines' field.")
            start_line, end_line = int(lines_match.group(1)), int(lines_match.group(2))
            patch_data = {"path": target_path, "action": "replace_lines", "lines": (start_line, end_line), "content": patch_content}
            apply_patch(patch_data, destination_path)

        elif block_type == "diff":
            patch_data = {"path": target_path, "diff_content": _unfence_code_block(content)}
            apply_diff_patch(patch_data, destination_path)
    
    if changes_applied:
        click.secho("All operations completed.", fg="bright_green")
        return

    # --- If all strategies fail ---
    raise ValueError("Input is not a recognized f2t2f format, a unified diff, or a block-based command.")


@click.group()
def cli():
    """f2t2f: A tool to convert folder structures to text and back."""
    pass

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--format', 'output_format', type=click.Choice(['json', 'v2'], case_sensitive=False), default='v2', help='The output format. V2 is more readable and efficient.')
def copy(folder_path, output_format):
    """Serialize a folder to clipboard. Honors .f2t2f file if present."""
    try:
        path = Path(folder_path)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)
        
        if not structure.get("children"):
            click.secho("Warning: The resulting structure is empty based on the current filters.", fg="yellow")

        output_text = serialize_to_v2(structure) if output_format == 'v2' else serialize_to_json(structure)
        pyperclip.copy(output_text)
        click.secho(f"Successfully copied structure of '{path.name}' to clipboard in {output_format.upper()} format.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red', err=True)

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.argument('output_file', type=click.Path(dir_okay=False, writable=True))
@click.option('--format', 'output_format', type=click.Choice(['json', 'v2'], case_sensitive=False), default='v2', help='The output format. V2 is more readable and efficient.')
def save(folder_path, output_file, output_format):
    """Save a folder structure to a file. Honors .f2t2f file if present."""
    try:
        path = Path(folder_path)
        output = Path(output_file)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)

        if not structure.get("children"):
            click.secho("Warning: The resulting structure is empty based on the current filters.", fg="yellow")

        output_text = serialize_to_v2(structure) if output_format == 'v2' else serialize_to_json(structure)
        output.write_text(output_text, encoding='utf-8')
        click.secho(f"Successfully saved structure to '{output}' in {output_format.upper()} format.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red', err=True)

@cli.command()
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def paste(destination_path):
    """Create/patch folder from text in clipboard."""
    try:
        dest_path = Path(destination_path)
        dest_path.mkdir(exist_ok=True)
        text_input = pyperclip.paste()
        _process_input(text_input, dest_path)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        click.secho(f"Error: {e}", fg='red', err=True)
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg='red', err=True)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def load(input_file, destination_path):
    """Create/patch folder from a text file."""
    try:
        input_path, dest_path = Path(input_file), Path(destination_path)
        dest_path.mkdir(exist_ok=True)
        text_input = input_path.read_text(encoding='utf-8')
        _process_input(text_input, dest_path)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        click.secho(f"Error: {e}", fg='red', err=True)
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg='red', err=True)

@cli.group()
def config():
    """Manage the global f2t2f configuration."""
    pass

@config.command()
def path():
    """Prints the path to the configuration file."""
    config_path = get_config_path()
    click.echo(f"Your configuration file is located at:\n{config_path}")

@config.command()
@click.option('--force', is_flag=True, help="Overwrite an existing configuration file.")
def init(force):
    """Creates a default global configuration file."""
    config_path = get_config_path()
    if config_path.exists() and not force:
        click.secho(f"Config file already exists. Use --force to overwrite.", fg="yellow")
        return
    save_default_config()
    click.secho(f"Default configuration file created at:\n{config_path}", fg="green")

@cli.group()
def list():
    """Manage .f2t2f (inclusion/exclusion list) files."""
    pass

@list.command()
@click.option('--type', 'list_type', type=click.Choice(['whitelist', 'blacklist'], case_sensitive=False), default='blacklist', help='The type of list to create.')
@click.option('--force', is_flag=True, help="Overwrite an existing .f2t2f file.")
@click.argument('target_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), default='.')
def init(list_type, force, target_path):
    """Creates a sample .f2t2f file in the target directory."""
    list_file = Path(target_path) / ".f2t2f"
    if list_file.exists() and not force:
        click.secho(f".f2t2f file already exists at '{list_file}'. Use --force to overwrite.", fg="yellow")
        return

    content = f"type: {list_type}\n---\n"
    if list_type == 'blacklist':
        content += "# Add files, directories, or glob patterns to exclude.\n# Example: __pycache__/\n# Example: *.tmp\n# Example: .env\n"
    else:
        content += "# Add files, dirs, or glob patterns to include.\n# Only matching items will be included.\n# Example: src/main.py\n# Example: docs/\n"
    
    list_file.write_text(content, encoding='utf-8')
    click.secho(f"Created a sample '{list_type}' .f2t2f file at '{list_file}'.", fg="green")

if __name__ == '__main__':
    cli()