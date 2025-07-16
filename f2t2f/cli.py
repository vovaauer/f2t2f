import click
import pyperclip
from pathlib import Path
import re

from .folder_ops import read_directory_structure, create_directory_from_structure, apply_patch
from .text_formatter import serialize_to_json, serialize_to_v2, deserialize
from .config import get_config_path, save_default_config

# --- New Helper Function to process input ---
def _process_input(text_input: str, destination_path: Path):
    """
    Parses a f2t2f input string (v2 or mixed) and applies changes.
    Can handle full file creation and patches.
    """
    # Regex to find file or patch blocks
    block_pattern = re.compile(r">>> (file|patch): (.*?)\n(.*?)\n<<<", re.DOTALL)
    
    # Check if this is a classic V1 or full V2 format first
    try:
        structure_data = deserialize(text_input)
        click.echo("Detected a complete folder structure. Creating from scratch...")
        
        base_creation_path = destination_path
        if destination_path.name == structure_data.get('name'):
            click.secho(f"Destination '{destination_path.name}' matches structure root. Overwriting contents.", fg="yellow")
            base_creation_path = destination_path.parent
        
        create_directory_from_structure(structure_data, base_creation_path)
        click.secho("Folder structure created successfully.", fg='green')
        return
    except ValueError:
        # Not a classic format, so we assume it's a set of file/patch blocks
        click.echo("Detected file/patch blocks. Applying changes...")

    for match in block_pattern.finditer(text_input):
        block_type, path_str, content_with_meta = match.groups()
        target_path = Path(path_str.strip())
        
        if block_type == "file":
            full_path = destination_path / target_path
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content_with_meta, encoding='utf-8')
            click.secho(f"  -> Created/Replaced file '{target_path}'", fg="green")

        elif block_type == "patch":
            meta, patch_content = content_with_meta.split("\n---\n", 1)
            lines_match = re.search(r"lines: (\d+)-(\d+)", meta)
            
            if not lines_match:
                raise ValueError(f"Invalid patch for '{target_path}': missing 'lines' field.")
            
            start_line = int(lines_match.group(1))
            end_line = int(lines_match.group(2))

            patch_data = {
                "path": target_path,
                "action": "replace_lines",
                "lines": (start_line, end_line),
                "content": patch_content
            }
            apply_patch(patch_data, destination_path)
    
    click.secho("All operations completed.", fg="bright_green")


# --- CLI Commands ---

@click.group()
def cli():
    """f2t2f: A tool to convert folder structures to text and back."""
    pass

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--format', 'output_format', type=click.Choice(['json', 'v2'], case_sensitive=False), default='v2', help='The output format. V2 is more readable and efficient.')
def copy(folder_path, output_format):
    """Serialize a folder structure to the clipboard."""
    try:
        path = Path(folder_path)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)
        
        if output_format == 'v2':
            output_text = serialize_to_v2(structure)
        else:
            output_text = serialize_to_json(structure)

        pyperclip.copy(output_text)
        click.secho(f"Successfully copied structure of '{path.name}' to clipboard in {output_format.upper()} format.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red')

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.argument('output_file', type=click.Path(dir_okay=False, writable=True))
@click.option('--format', 'output_format', type=click.Choice(['json', 'v2'], case_sensitive=False), default='v2', help='The output format. V2 is more readable and efficient.')
def save(folder_path, output_file, output_format):
    """Save a folder structure to a text file."""
    try:
        path = Path(folder_path)
        output = Path(output_file)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)

        if output_format == 'v2':
            output_text = serialize_to_v2(structure)
        else:
            output_text = serialize_to_json(structure)
        
        output.write_text(output_text, encoding='utf-8')
        click.secho(f"Successfully saved structure to '{output}' in {output_format.upper()} format.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red')

@cli.command()
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def paste(destination_path):
    """Create or patch folder structure from text in the clipboard."""
    try:
        dest_path = Path(destination_path)
        dest_path.mkdir(exist_ok=True)
        
        text_input = pyperclip.paste()
        if not text_input or not text_input.strip():
            raise ValueError("Clipboard is empty or does not contain usable text.")

        _process_input(text_input, dest_path)

    except (ValueError, FileNotFoundError) as e:
        click.secho(f"Error: {e}", fg='red')
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg='red')


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def load(input_file, destination_path):
    """Create or patch folder structure from a text file."""
    try:
        input_path = Path(input_file)
        dest_path = Path(destination_path)
        dest_path.mkdir(exist_ok=True)

        text_input = input_path.read_text(encoding='utf-8')
        if not text_input or not text_input.strip():
            raise ValueError(f"Input file '{input_path}' is empty.")
        
        _process_input(text_input, dest_path)

    except (ValueError, FileNotFoundError) as e:
        click.secho(f"Error: {e}", fg='red')
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg='red')


@cli.group()
def config():
    """Manage the f2t2f configuration."""
    pass

@config.command()
def path():
    """Prints the path to the configuration file."""
    config_path = get_config_path()
    click.echo(f"Your configuration file is located at:")
    click.secho(str(config_path), fg="green")

@config.command()
@click.option('--force', is_flag=True, help="Overwrite an existing configuration file.")
def init(force):
    """Creates a default configuration file for you to edit."""
    config_path = get_config_path()
    if config_path.exists() and not force:
        click.secho("Configuration file already exists.", fg="yellow")
        click.echo(f"To overwrite it, run: f2t2f config init --force")
        click.echo(f"To see its location, run: f2t2f config path")
        return
    
    save_default_config()
    click.secho(f"Default configuration file created at:", fg="green")
    click.echo(str(config_path))
    click.echo("You can now edit this file to customize the ignored folders and files.")

if __name__ == '__main__':
    cli()