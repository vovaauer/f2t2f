# f2t2f: Folder to Text to Folder

A CLI tool to serialize folder structures to a structured text format (JSON) and back. This is useful for sharing project structures, analyzing them with LLMs, or creating project templates.

## Features

-   **Folder to Text**: Read a folder and serialize its structure and file contents to JSON.
-   **Text to Folder**: Recreate a complete folder structure from a JSON definition.
-   **Clipboard Support**: Copy and paste structures directly from your system clipboard.
-   **File Support**: Save structures to and load them from `.txt` or `.json` files.
-   **Configurable**: Customize a list of ignored files and folders (like `__pycache__` or `.git`) via a user-specific config file.

## Installation

To install the package from its source, navigate to the project's root directory and run:

```bash
pip install .
```

For development, use editable mode:

```bash
pip install -e .
```

## Usage

### Folder to Text

**Copy structure to clipboard:**
```bash
f2t2f copy <path/to/folder>
```

**Save structure to a file:**
```bash
f2t2f save <path/to/folder> output.json
```

### Text to Folder

**Create structure from clipboard:**
```bash
f2t2f paste [destination/path]
```
(If destination path is omitted, it uses the current directory.)

**Create structure from a file:**
```bash
f2t2f load input.json [destination/path]
```

### Configuration

The tool ignores common temporary files and build artifacts by default. You can customize this list.

**Find your config file location:**
```bash
f2t2f config path
```

**Create the default config file if it doesn't exist:**
```bash
f2t2f config init
```

Once created, you can edit this JSON file to add or remove patterns from the `ignore_patterns` list.