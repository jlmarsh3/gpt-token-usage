import tiktoken
import sys

def count_tokens_from_file(filename, model="gpt-4o-mini"):
    # Map models to encodings
    model_encodings = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5": "cl100k_base"
    }
    
    # Pick encoding
    encoding_name = model_encodings.get(model, "cl100k_base")
    enc = tiktoken.get_encoding(encoding_name)

    # Read file
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()

    # Encode & count
    tokens = enc.encode(text)
    print(f"Model: {model}")
    print(f"Total tokens: {len(tokens)}")
    print(f"First 20 tokens: {tokens[:20]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_tokens.py <chatlog.txt> [model]")
    else:
        filename = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else "gpt-4o-mini"
        count_tokens_from_file(filename, model)
