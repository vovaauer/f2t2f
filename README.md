# f2t2f

A simple CLI tool to convert entire folder structures, including file content, to and from a single, portable text file.

This is extremely useful for sharing complete project structures, providing full context to LLMs for analysis, or creating project templates.

## Installation

```bash
pip install f2t2f
```

## Usage

### Folder to Text

**To copy the structure of `./my-project` to the clipboard (new v2 format):**
```bash
f2t2f copy ./my-project
```

**To save it to a file instead:**
```bash
f2t2f save ./my-project structure.txt
```

**To use the old JSON format:**
```bash
f2t2f save ./my-project structure.json --format json
```

### Text to Folder

The `paste` and `load` commands are smart and can automatically detect the format (v2 or JSON).

**To create a folder structure from your clipboard into the current directory:**
```bash
f2t2f paste
```

**To create it from a file into a specific destination:**
```bash
f2t2f load structure.txt ./output-folder
```

## The `v2` Format (Default)

`f2t2f` uses a highly readable and efficient hybrid format. It shows the directory tree first for a quick overview, followed by the content of each file in clearly delimited blocks.

For a folder structure like this:
```
my_app/
├── main.py
└── data/
    └── config.txt
```

Running `f2t2f copy ./my_app` produces this text:

```text
type: f2t2f_folder_structure_v2
---
tree:
my_app
├── data
│   └── config.txt
└── main.py
---
>>> file: my_app/data/config.txt
setting=True
<<<
---
>>> file: my_app/main.py
print("Hello, World!")
<<<
```

## Interacting with AI

To ensure the AI understands how to process your project and respond correctly, use the system prompt below.

### AI System Prompt

> You are an expert programmer and a helpful coding assistant. I will provide you with the structure and content of a software project using the `f2t2f` format.
>
> The format begins with a tree view, followed by file content blocks. Each file block starts with `>>> file: [path]` and ends with `<<<`.
>
> Your task is to analyze the code and provide modifications. When you respond, you MUST use the exact `f2t2f` format.
>
> **RULES FOR YOUR RESPONSE:**
> 1.  **Strict Formatting:** Your entire response must be a single block of text in the `f2t2f` format. Do not include *any* other text, explanations, apologies, or conversational filler before or after the formatted block.
> 2.  **Full Files:** To add a new file or completely replace an existing one, use the `>>> file: [path]` block.
> 3.  **Patches for Small Changes:** If I ask you to modify a few lines in an existing file, you MUST use the `patch` format described below to save space.
> 4.  **Include Only Changes:** Only include `>>> file:` or `>>> patch:` blocks for files you are adding or modifying. Do not repeat the entire project structure.
>
> **The `patch` format is as follows:**
> ```text
> >>> patch: path/to/the/file_to_modify.py
> action: replace_lines
> lines: 21-23
> ---
> This is the new line 21.
> This is the new line 22.
> This is the new line 23.
> <<<
> ```
> - The `lines` field is inclusive.
> - The content for the patch goes after a `---` separator.
>
> By following these rules, your response can be directly used by my tools.

### Example AI Interaction

**User:**
> Using the project I provided, please modify lines 10-11 in `f2t2f/cli.py` to add a greeting.

**Correct AI Response:**
```text
>>> patch: f2t2f/cli.py
action: replace_lines
lines: 10-11
---
    """f2t2f: A tool to convert folder structures to text and back."""
    click.echo("Welcome to f2t2f!")
<<<
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