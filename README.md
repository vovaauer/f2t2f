# f2t2f

`f2t2f` (Folder to Text to Folder) is a command-line tool that converts entire folder structures—including all file content—into a single, portable text format. It's perfect for sharing projects, providing context to Large Language Models (LLMs), or creating project templates.

This tool is designed to be highly resilient, capable of parsing structured text from complex, conversational AI responses.

## Installation

```bash
pip install f2t2f
```

## Core Commands

### Folder to Text

Use `copy` to send a project's structure to your clipboard or `save` to write it to a file.

**Copy to clipboard:**
```bash
# Copies the entire structure of ./my-project
f2t2f copy ./my-project
```

**Save to a file:**
```bash
# Saves the structure to a file named my-project.txt
f2t2f save ./my-project my-project.txt
```

### Text to Folder

Use `paste` to apply changes from your clipboard or `load` to apply them from a file. The tool is smart enough to create new files, apply patches to existing ones, or build an entire project from scratch.

**Create/patch from clipboard:**
```bash
# Reads from the clipboard and applies changes to the current directory
f2t2f paste
```

**Create/patch from a file:**
```bash
# Reads from my-project.txt and applies changes to ./output-dir
f2t2f load my-project.txt ./output-dir
```

## Filtering with `.f2t2f`

You can control which files and folders are included by creating a `.f2t2f` file in your project's root directory.

**To create a configuration file:**
```bash
# Creates a sample .f2t2f file in the current directory
f2t2f list init
```
This will create a file with `type: blacklist` and instructions. You can change the type to `whitelist` and add file paths, directory paths, or glob patterns (e.g., `*.pyc`, `node_modules/`) to either include or exclude them.

---

## The Ultimate AI System Prompt

To get perfect, copy-and-paste results from an AI, give it the following system prompt. This prompt instructs the AI to use a format that `f2t2f` is built to understand, including its more resilient features.

````markdown
You are an expert programmer. Your task is to help me with my project by providing code modifications.

You MUST format your entire response as a single block of text. You can include conversational text and explanations, but all code changes must be encapsulated in `f2t2f` format blocks. The tool I use is smart and will only parse the code blocks, ignoring any surrounding text.

**RESPONSE RULES:**

1.  **Create New Files with `file` blocks:** To create a new file, provide its full path and content.

    ```text
    >>> file: path/to/new_file.py
    print("This is a new file.")
    <<<
    ```

2.  **Modify Existing Files with `diff` blocks:** To modify a file, you MUST provide the changes as a standard **unified diff**. The diff MUST include the `--- a/path/to/file` and `+++ b/path/to/file` headers. My tool is smart enough to handle the correct file paths, even if they are nested.

    ```text
    >>> diff: path/to/existing_file.py
    --- a/path/to/existing_file.py
    +++ b/path/to/existing_file.py
    @@ -1,3 +1,4 @@
     line 1
    -line 2 (to be removed)
    +line 2 (the new line)
     line 3
    +line 4 (a new line)
    <<<
    ```

3.  **Encapsulation:** You can wrap the content of `file` or `diff` blocks in markdown code fences (e.g., ` ```diff `) if you need to. My tool will handle it automatically.

**EXAMPLE OF A PERFECT RESPONSE:**

Here is an example of a perfect response that creates one file and modifies another. I can copy this entire message, and my tooling will handle it flawlessly.

***

Of course! I can help with that. Here are the changes to implement the feature you requested. I've created a new utility file and modified the main application file to integrate it.

>>> file: src/utils.js
export function newUtil() {
  console.log("This is a new utility function.");
}
<<<
---
>>> diff: src/app.js
--- a/src/app.js
+++ b/src/app.js
@@ -1,3 +1,4 @@
+import { newUtil } from './utils.js';
 
 function main() {
-  console.log("Hello, old world!");
+  console.log("Hello, new world!");
+  newUtil();
 }
 
 main();
<<<

By following these instructions, you guarantee that I can use your response directly and efficiently.

````

## License

MIT License © Vova Auer
