# gpt-token-usage
Simple script that reads a conversation and calculates the number of tokens used.

Usage
-----

Set up and run using the provided helper script:

```bash
./run.sh            # uses chats/token-chat.txt by default
./run.sh file.txt   # count tokens for file.txt
./run.sh file.txt gpt-4  # pass model name as a second argument
```

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

License: see `LICENSE`
