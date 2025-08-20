# gpt-token-usage
Simple script that reads a conversation and calculates the number of tokens used.

Usage
-----

Set up and run using the provided helper script:

```bash
./run.sh            # process all files in the chats/ directory and print an aggregated table
./run.sh file.txt   # count tokens for file.txt
```

The script prints estimated costs for all supported models (no model parameter is required).

The script will create a `venv/` virtual environment (if missing), install packages from `requirements.txt`, activate the environment, and run `count-tokens.py`.

Files
-----

- `count-tokens.py` - main script that counts tokens using `tiktoken`.
- `run.sh` - helper to set up venv, install deps, and run the script.
- `requirements.txt` - Python dependencies.

Notes
-----

If you pass `-h` or `--help` to `run.sh` it will show a short usage message. To see `count-tokens.py`'s usage directly, run:

```bash
python count-tokens.py --help
```

Cost estimation
---------------

`count-tokens.py` now prints a rough estimated USD cost for the token count using a small built-in price table (per 1,000 tokens). These are example rates and may not reflect real OpenAI/ChatGPT billing — update the rates in `count-tokens.py` to match current pricing.

Table layout
------------

The output is an ASCII table with the following features:

- Two-line header: the first header row shows each model name; the second header row contains two subheaders under each model: `Input` and `Output`.
- Each data row (one per file in `chats/`) shows the estimated cost for prompt tokens under the `Input` column and assistant tokens under the `Output` column for every model.
- A `TOTAL` row shows summed Input and Output costs per model.
- A `GRAND TOTAL` row shows the combined (Input+Output) cost per model centered across the model's two subcolumns — this visually indicates it's the sum of both columns.

Example (truncated):

| Filename |      gpt-5      |      gpt-4      |
|          | Input | Output | Input | Output |
| fileA    | $0.001| $0.002 | $0.000| $0.001 |
| TOTAL    | $0.001| $0.003 | $0.000| $0.001 |
| GRAND TOTAL |   $0.004   |   $0.001   |

If the table formatting doesn't fit your terminal width, reduce the padding in `count-tokens.py` (variable `pad`) or redirect the output into a file and view it in a wider window.

Preparing chat files
--------------------

Place plain text files with your conversations in the `chats/` directory. The script applies simple heuristics to split prompt (input) vs assistant (output) text, so files can be in several common formats:

- Simple labeled lines:

	User: Hello
	Assistant: Hi — how can I help?

- JSON role markers (single-line or pretty-printed):

	{"role": "user", "content": "What's the weather?"}
	{"role": "assistant", "content": "Sunny."}

- Plain text paragraphs: if no explicit role markers are found, the script splits on blank lines and alternates roles (first paragraph treated as input, next as output, etc.).

Filename tips
-------------

- Use descriptive filenames (e.g. `support-ticket-123.txt`) — the name appears in the table's first column.
- Files starting with `.` are ignored.

Once your files are in `chats/`, run:

```bash
./run.sh
```

The script will process all files and print the aggregated table.

License: see `LICENSE`
