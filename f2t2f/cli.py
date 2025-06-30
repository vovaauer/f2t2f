import click
import pyperclip
from pathlib import Path

from .folder_ops import read_directory_structure, create_directory_from_structure
from .text_formatter import serialize_to_json, deserialize_from_json
from .config import get_config_path, save_default_config

@click.group()
def cli():
    """f2t2f: A tool to convert folder structures to text and back."""
    pass

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def copy(folder_path):
    """Serialize a folder structure to the clipboard as JSON."""
    try:
        path = Path(folder_path)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)
        json_output = serialize_to_json(structure)
        pyperclip.copy(json_output)
        click.secho(f"Successfully copied structure of '{path.name}' to clipboard.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red')

@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.argument('output_file', type=click.Path(dir_okay=False, writable=True))
def save(folder_path, output_file):
    """Save a folder structure to a text file as JSON."""
    try:
        path = Path(folder_path)
        output = Path(output_file)
        click.echo(f"Reading structure from '{path.name}'...")
        structure = read_directory_structure(path)
        json_output = serialize_to_json(structure)
        output.write_text(json_output, encoding='utf-8')
        click.secho(f"Successfully saved structure to '{output}'.", fg='green')
    except Exception as e:
        click.secho(f"Error: {e}", fg='red')

@cli.command()
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def paste(destination_path):
    """Create a folder structure from JSON in the clipboard."""
    try:
        dest_path = Path(destination_path)
        dest_path.mkdir(exist_ok=True)
        
        json_input = pyperclip.paste()
        if not json_input:
            raise ValueError("Clipboard is empty or does not contain text.")
            
        click.echo("Reading structure from clipboard...")
        structure_data = deserialize_from_json(json_input)
        
        base_creation_path = dest_path
        if dest_path.name == structure_data['name']:
            click.secho(f"Destination '{dest_path.name}' matches structure root. Overwriting contents.", fg="yellow")
            base_creation_path = dest_path.parent

        click.echo(f"Creating structure '{structure_data['name']}' in '{base_creation_path}'...")
        create_directory_from_structure(structure_data, base_creation_path)
        click.secho("Folder structure created successfully.", fg='green')
    except ValueError as e:
        click.secho(f"Error: {e}", fg='red')
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg='red')

@cli.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('destination_path', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), default='.', required=False)
def load(input_file, destination_path):
    """Create a folder structure from a JSON text file."""
    try:
        input_path = Path(input_file)
        dest_path = Path(destination_path)
        dest_path.mkdir(exist_ok=True)

        json_input = input_path.read_text(encoding='utf-8')
        if not json_input:
            raise ValueError(f"Input file '{input_path}' is empty.")
        
        click.echo(f"Reading structure from '{input_path.name}'...")
        structure_data = deserialize_from_json(json_input)

        base_creation_path = dest_path
        if dest_path.name == structure_data['name']:
            click.secho(f"Destination '{dest_path.name}' matches structure root. Overwriting contents.", fg="yellow")
            base_creation_path = dest_path.parent

        click.echo(f"Creating structure '{structure_data['name']}' in '{base_creation_path}'...")
        create_directory_from_structure(structure_data, dest_path)
        click.secho("Folder structure created successfully.", fg='green')
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