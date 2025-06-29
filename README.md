# f2t2f

A simple CLI tool to convert folder structures to and from a structured text format (JSON).

This is useful for sharing project structures, analyzing them with LLMs, or creating project templates.

## Installation

```bash
pip install f2t2f
```

## Usage

### Folder to Text

**To serialize the structure of `./my-project` to the clipboard:**
```bash
f2t2f copy ./my-project
```

**To save it to a file instead:**
```bash
f2t2f save ./my-project structure.json
```

### Text to Folder

**To create a folder structure from your clipboard into the current directory:**
```bash
f2t2f paste
```

**To create it from a file into a specific destination:**
```bash
f2t2f load structure.json ./output-folder
```

## Example Format

`f2t2f` uses a clear JSON format. For a folder structure like this:

```
my_app/
├── main.py
└── data/
    └── config.txt
```

Running `f2t2f copy ./my_app` would produce the following JSON:

```json
{
  "type": "f2t2f_folder_structure_v1",
  "data": {
    "name": "my_app",
    "type": "folder",
    "children": [
      {
        "name": "data",
        "type": "folder",
        "children": [
          {
            "name": "config.txt",
            "type": "file",
            "content": "setting=True\n"
          }
        ]
      },
      {
        "name": "main.py",
        "type": "file",
        "content": "print(\"Hello, World!\")\n"
      }
    ]
  }
}
```

## Configuration (Optional)

By default, `f2t2f` ignores common files like `__pycache__` and `.git`. To customize this, you can create a configuration file.

1.  **Create the default config file:**
    ```bash
    f2t2f config init
    ```

2.  **Find its location and edit it:**
    ```bash
    f2t2f config path
    ```
    You can then add or remove patterns from the `ignore_patterns` list in that JSON file.

## License

MIT License © Vova Auer