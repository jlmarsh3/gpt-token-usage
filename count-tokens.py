import sys
import os
import tiktoken


def analyze_file(filename, model_encodings):
    """Read file and heuristically split into input (prompt) and output (assistant) text.

    Returns total_tokens (using cl100k_base if available) and a dict per model with
    input_tokens and output_tokens counts.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return 0, {m: {'encoding': enc, 'input_tokens': 0, 'output_tokens': 0} for m, enc in model_encodings.items()}

    # Heuristics: look for explicit prefixes like 'User:' / 'Assistant:' or JSON role markers.
    lines = text.splitlines()
    segments = []  # list of (role, text)

    prefix_found = False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith('user:') or low.startswith('user -') or low.startswith('you:') or low.startswith('human:'):
            prefix_found = True
            segments.append(('input', s.split(':', 1)[1].strip() if ':' in s else s))
        elif low.startswith('assistant:') or low.startswith('assistant -') or low.startswith('ai:') or low.startswith('bot:'):
            prefix_found = True
            segments.append(('output', s.split(':', 1)[1].strip() if ':' in s else s))
        elif '"role"' in low and ('user' in low or 'assistant' in low):
            prefix_found = True
            if 'user' in low:
                segments.append(('input', s))
            else:
                segments.append(('output', s))

    if not prefix_found:
        # Fallback: split by blank lines into paragraphs and alternate roles
        paras = [p.strip() for p in text.split('\n\n') if p.strip()]
        role = 'input'
        for p in paras:
            segments.append((role, p))
            role = 'output' if role == 'input' else 'input'

    input_text = '\n'.join(t for r, t in segments if r == 'input')
    output_text = '\n'.join(t for r, t in segments if r == 'output')

    results = {}
    for model, encoding_name in model_encodings.items():
        try:
            enc = tiktoken.get_encoding(encoding_name)
        except Exception:
            # fallback to cl100k_base if encoding not found
            enc = tiktoken.get_encoding('cl100k_base')
        in_count = len(enc.encode(input_text)) if input_text else 0
        out_count = len(enc.encode(output_text)) if output_text else 0
        results[model] = {
            'encoding': encoding_name,
            'input_tokens': in_count,
            'output_tokens': out_count,
        }

    # default token count (total) using cl100k_base if available
    default_token_count = None
    for m, enc_name in model_encodings.items():
        if enc_name == 'cl100k_base':
            default_token_count = results[m]['input_tokens'] + results[m]['output_tokens']
            break
    if default_token_count is None:
        first = next(iter(results.values()))
        default_token_count = first['input_tokens'] + first['output_tokens']

    return default_token_count, results


def count_tokens_from_file(filename=None, debug_spaces=False):
    model_encodings = {
        'gpt-5': 'cl100k_base',
        'gpt-4': 'cl100k_base',
        'gpt-4o': 'o200k_base',
        'gpt-4o-mini': 'o200k_base',
        'gpt-3.5': 'cl100k_base',
    }

    model_prices_per_1k = {
        'gpt-5': 0.06,
        'gpt-4': 0.03,
        'gpt-4o': 0.0025,
        'gpt-4o-mini': 0.0015,
        'gpt-3.5': 0.002,
    }

    # collect files
    if filename is None:
        chats_dir = os.path.join(os.path.dirname(__file__), 'chats')
        if not os.path.isdir(chats_dir):
            print(f'chats directory not found at {chats_dir}')
            return
        files = [os.path.join(chats_dir, f) for f in sorted(os.listdir(chats_dir))
                 if os.path.isfile(os.path.join(chats_dir, f)) and not f.startswith('.')]
    else:
        files = [filename]

    # build rows (include total tokens per file)
    models = list(model_encodings.keys())
    rows = []  # (filename, total_tokens, {model: (in_cost, out_cost)})
    for path in files:
        total_tokens, res = analyze_file(path, model_encodings)
        row = {}
        for m in models:
            in_t = res[m]['input_tokens']
            out_t = res[m]['output_tokens']
            rate = model_prices_per_1k.get(m)
            in_cost = in_t / 1000.0 * rate if rate is not None else None
            out_cost = out_t / 1000.0 * rate if rate is not None else None
            row[m] = (in_cost, out_cost)
        rows.append((os.path.basename(path), total_tokens, row))

    # order models by price desc
    models_sorted = sorted(models, key=lambda m: model_prices_per_1k.get(m, 0), reverse=True)

    # compute widths
    filename_col = 'Filename'
    tokens_col = 'Tokens'
    filename_w = max(len(filename_col), *(len(r[0]) for r in rows)) if rows else len(filename_col)
    tokens_w = max(len(tokens_col), *(len(str(r[1])) for r in rows)) if rows else len(tokens_col)

    # prepare cost strings and compute column widths for Input and Output subcolumns
    pad = 2
    cost_in_examples = {}
    cost_out_examples = {}
    for _, _, row in rows:
        for m in models_sorted:
            i, o = row[m]
            if i is None:
                si = 'unknown'
            else:
                si = f'${i:.4f}'
            if o is None:
                so = 'unknown'
            else:
                so = f'${o:.4f}'
            cost_in_examples.setdefault(m, []).append(si)
            cost_out_examples.setdefault(m, []).append(so)

    cost_w_in = {}
    cost_w_out = {}
    for m in models_sorted:
        in_candidates = [len(s) for s in cost_in_examples.get(m, [])]
        out_candidates = [len(s) for s in cost_out_examples.get(m, [])]
        cost_w_in[m] = max(len('Input'), *(in_candidates if in_candidates else [0]))
        cost_w_out[m] = max(len('Output'), *(out_candidates if out_candidates else [0]))

    # build separator and two-line header (model name spans the two subcolumns)
    widths = [filename_w + pad * 2, tokens_w + pad * 2]
    for m in models_sorted:
        widths.append(cost_w_in[m] + pad * 2)
        widths.append(cost_w_out[m] + pad * 2)
    sep = '|' + '|'.join('-' * w for w in widths) + '|'

    # Print header: first line has model names spanning both subcolumns (no inner '|')
    header_line1 = '|' + filename_col.center(widths[0]) + '|' + tokens_col.center(widths[1]) + '|'
    for i, m in enumerate(models_sorted):
        left_w = widths[2 + 2 * i]
        right_w = widths[2 + 2 * i + 1]
        combined = m.center(left_w + right_w)
        header_line1 += combined + ' |'

    # Header line 2: Input / Output labels under each model (printed without inner '|' between them)
    # leave the Tokens subheader blank on the second header row
    header_line2 = '|' + ''.center(widths[0]) + '|' + ''.center(widths[1]) + '|'
    for i, m in enumerate(models_sorted):
        left = 'Input'.center(widths[2 + 2 * i])
        # add one trailing space after 'Output' while preserving total width
        out_w = widths[2 + 2 * i + 1]
        if out_w > 1:
            right = 'Output'.center(out_w) + ' '
        else:
            right = 'Output'.center(out_w)
        header_line2 += left + right + '|'

    # print a small two-column legend table (Model | Cost/1k) before the main table
    model_col = 'Model'
    cost_col = 'Cost/1k'
    # prepare cost strings
    cost_strs = {m: f"${model_prices_per_1k.get(m, 0):.4f}/1k" for m in models_sorted}
    model_w = max(len(model_col), *(len(m) for m in models_sorted))
    cost_w = max(len(cost_col), *(len(s) for s in cost_strs.values()))
    # legend column widths include padding
    legend_widths = [model_w + pad * 2, cost_w + pad * 2]
    sep_legend = '|' + '|'.join('-' * w for w in legend_widths) + '|'
    header_legend = '|' + model_col.ljust(legend_widths[0]) + '|' + cost_col.rjust(legend_widths[1]) + '|'
    print(sep_legend)
    print(header_legend)
    print(sep_legend)
    for m in models_sorted:
        s = cost_strs[m]
        line = '|' + (' ' * pad) + m.ljust(model_w) + (' ' * pad) + '|' + (' ' * pad) + s.rjust(cost_w) + (' ' * pad) + '|'
        print(line)
    print(sep_legend)
    print()
    print(sep)
    print(header_line1)
    print(header_line2)
    print(sep)

    if debug_spaces:
        # Show repr of header_line2 to make trailing spaces visible for debugging
        print('\n[DEBUG] repr(header_line2):')
        print(repr(header_line2))

    # print rows: keep Tokens column fixed; for per-file rows combine each model's
    # Input+Output subcells into a single printed cell (no '|' between them)
    totals_in = {m: 0.0 for m in models_sorted}
    totals_out = {m: 0.0 for m in models_sorted}
    for fname, total_tokens, row in rows:
        # start with filename and tokens cells (with padding)
        token_cell = (' ' * pad) + str(total_tokens).center(tokens_w) + (' ' * pad)
        if debug_spaces:
            print(f"[DEBUG] fname={fname!r}, total_tokens={total_tokens!r}, token_cell={repr(token_cell)}")
        row_str = '|' + (' ' * pad) + fname.ljust(filename_w) + (' ' * pad) + '|' + token_cell + '|'
        for m in models_sorted:
            i, o = row[m]
            if i is None:
                si = 'unknown'.center(cost_w_in[m])
            else:
                si = f'${i:.4f}'.center(cost_w_in[m])
                totals_in[m] += i
            # For the filename row, add a single trailing space after the Output
            # content while preserving the subcolumn width by centering into
            # (width-1) and appending a space. This avoids changing separators.
            if o is None:
                if cost_w_out[m] > 1:
                    so = 'unknown'.center(cost_w_out[m] - 1) + ' '
                else:
                    so = 'unknown'.center(cost_w_out[m])
            else:
                if cost_w_out[m] > 1:
                    so = f'${o:.4f}'.center(cost_w_out[m] - 1) + ' '
                else:
                    so = f'${o:.4f}'.center(cost_w_out[m])
                totals_out[m] += o
            # build left and right cells including their padding, then append
            left_cell = (' ' * pad) + si + (' ' * pad)
            right_cell = (' ' * pad) + so + (' ' * (pad-1))
            combined_cell = left_cell + '|' + right_cell
            row_str += combined_cell + '|'
        print(row_str)

    # totals row (keep as separate Input/Output subcolumns)
    print(sep)
    total_label = 'TOTAL'
    parts = [total_label.ljust(filename_w), str(sum(r[1] for r in rows)).center(tokens_w)]
    for m in models_sorted:
        si = f'${totals_in[m]:.4f}'.center(cost_w_in[m])
        so = f'${totals_out[m]:.4f}'.center(cost_w_out[m])
        parts.append(si)
        parts.append(so)
    # Build padded parts; for the Output subcolumns (every second col after
    # the first two), shift left by one space to align with per-file combined
    # cells which don't have an inner '|'.
    padded_parts = []
    for idx, p in enumerate(parts):
        if idx >= 2 and ((idx - 2) % 2) == 1:
            # This is an Output subcolumn (shift left by one)
            left_pad = ' ' * (pad - 1 if pad > 0 else 0)
            padded_parts.append(left_pad + p + (' ' * pad) + ' ')
        else:
            padded_parts.append((' ' * pad) + p + (' ' * pad))
    print('|' + '|'.join(padded_parts) + '|')
    print(sep)

    # grand total per model (sum of input+output cost in each model column) - print
    # as a single combined cell per model (no inner '|') so it's visually centered
    grand_label = 'GRAND TOTAL'
    grand_row = '|' + ('  ' + grand_label).ljust(widths[0]) + '|' + ''.center(widths[1]) + '|'
    for i, m in enumerate(models_sorted):
        total_cost = totals_in[m] + totals_out[m]
        left_w = widths[2 + 2 * i]
        right_w = widths[2 + 2 * i + 1]
        s = f'${total_cost:.4f}'
        # Add a trailing space after the grand total value while keeping the
        # printed width equal to left_w+right_w. Center into (width-1) and
        # append a space when possible to avoid splitting digits at the border.
        if (left_w + right_w) > 1:
            combined = s.center(left_w + right_w - 1) + ' '
        else:
            combined = s.center(left_w + right_w)
        grand_row += combined + ' |'
    print(grand_row)
    print(sep)

    if debug_spaces:
        print('\n[DEBUG] repr(grand_row):')
        print(repr(grand_row))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Count tokens and estimate costs for chat files')
    parser.add_argument('filename', nargs='?', help='Path to a chat file (optional). If omitted, scans the chats/ directory')
    parser.add_argument('--debug-spaces', action='store_true', help='Print repr() of header and grand total rows to show trailing spaces')
    args = parser.parse_args()

    count_tokens_from_file(args.filename, debug_spaces=args.debug_spaces)
