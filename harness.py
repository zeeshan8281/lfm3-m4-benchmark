"""Instrumented synchronous greedy MLX inference; no stock iterator lookahead."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

PROMPTS = [
    ('ready', 'Reply with exactly READY and nothing else.', 'READY'),
    ('arithmetic', 'What is 17 + 26? Reply with only the integer.', '43'),
    ('subtraction', 'What is 13 - 8? Reply with only the integer.', '5'),
    ('extract', 'Extract the tracking code from this sentence: Your package AB-204 arrives tomorrow. Reply with only the code.', 'AB-204'),
    ('sort', 'Sort these integers in ascending order: 3, 1, 2. Reply with only the sorted integers separated by commas, with no spaces.', '1,2,3'),
    ('json', 'Return only a JSON object with exactly these fields: name is the string Ada; age is the integer 27.', {'name': 'Ada', 'age': 27}),
    ('classification', 'Classify the sentiment of this review as POSITIVE or NEGATIVE: I loved this book and would read it again. Reply with only the label.', 'POSITIVE'),
    ('negation', 'Read this record: Maya lives in Lisbon. Her brother lives in Porto. Where does Maya live? Reply with only the city name.', 'Lisbon'),
]


def score(text, expected):
    if isinstance(expected, str):
        return text.strip() == expected
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('duplicate key')
            out[key] = value
        return out
    try:
        value = json.loads(text.strip(), object_pairs_hook=unique)
        return (isinstance(value, dict) and value == expected
                and type(value.get('age')) is int and type(value.get('name')) is str)
    except (ValueError, TypeError):
        return False


def timing_metrics(times):
    assert times and times[0] > 0 and all(b > a for a, b in zip(times, times[1:]))
    intervals = len(times) - 1
    elapsed = times[-1] - times[0]
    return {'ttft_ms': times[0] * 1000, 'generation_ms': times[-1] * 1000,
            'decode_intervals': intervals, 'decode_ms': elapsed * 1000,
            'decode_tokens_per_second': intervals / elapsed if intervals else None}


def selfcheck():
    assert score('{"age":27,"name":"Ada"}', {'name': 'Ada', 'age': 27})
    for bad in ['{"age":27.0,"name":"Ada"}', '{"age":27,"age":27,"name":"Ada"}',
                '{"age":true,"name":"Ada"}', '```json\n{"age":27,"name":"Ada"}\n```']:
        assert not score(bad, {'name': 'Ada', 'age': 27})
    m = timing_metrics([0.1, 0.2, 0.3])
    assert m['decode_intervals'] == 2 and abs(m['decode_tokens_per_second'] - 10) < 1e-8
    assert timing_metrics([0.1])['decode_tokens_per_second'] is None
    print('Scoring and interval accounting self-check passed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=str(Path(__file__).parent / 'model'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mode', choices=['campaign', 'cold', 'smoke', 'smoke-capital', 'selfcheck'], required=True)
    args = parser.parse_args()
    if args.mode == 'selfcheck':
        selfcheck()
        return
    if args.output is None:
        parser.error('--output required')
    import mlx.core as mx
    from mlx_vlm import load
    mx.set_default_device(mx.gpu)
    assert mx.metal.is_available(), 'Real Metal device required'
    mx.synchronize()
    started = time.perf_counter()
    model, processor = load(args.model, lazy=False)
    mx.eval(model.parameters())
    mx.synchronize()
    load_ms = (time.perf_counter() - started) * 1000
    tokenizer = getattr(processor, 'tokenizer', processor)
    cfg = json.loads((Path(args.model) / 'config.json').read_text())
    eos_ids = cfg['eos_token_id']
    eos_ids = {eos_ids} if isinstance(eos_ids, int) else set(eos_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as out:
        def emit(row):
            out.write(json.dumps(row, ensure_ascii=False) + '\n')
            out.flush()
        emit({'kind': 'environment', 'pid': os.getpid(), 'mode': args.mode,
              'timestamp_unix': time.time(), 'device': str(mx.default_device()),
              'metal_available': mx.metal.is_available(), 'model_load_ms': load_ms,
              'model': args.model, 'versions': {p: importlib.metadata.version(p) for p in ['mlx', 'mlx-vlm', 'transformers']},
              'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'resident_active_bytes': mx.get_active_memory(), 'eos_token_ids': sorted(eos_ids),
              'sampling': 'argmax; no penalties; thinking disabled in template',
              'engine': 'direct official language_model forward; synchronous; no lookahead; unchunked prefill',
              'memory_scope': 'MLX peak active allocation including model and request, reset before request; not process RSS',
              'timing_scope': 'pretokenized IDs and fresh cache setup excluded; evaluated logits/argmax, host iteration and synchronization included; text decoding excluded'})

        def prepare(prompt):
            rendered = tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            assert rendered.endswith('<think></think>'), 'Thinking-off template changed'
            return rendered, tokenizer.encode(rendered, add_special_tokens=False)

        def run(ids, rendered, name, kind, ignore_eos=False, expected=None, repetition=0):
            cache = model.make_cache()
            inputs = mx.array([ids], dtype=mx.int32)
            mx.eval(inputs)
            mx.synchronize()
            mx.reset_peak_memory()
            token_ids, times = [], []
            epoch = time.time()
            start = time.perf_counter()
            first_logits = None
            for index in range(64):
                logits = model.language_model(inputs, cache=cache).logits[:, -1, :]
                token = mx.argmax(logits, axis=-1)
                mx.eval(token, [c.state for c in cache])
                mx.synchronize()
                token_id = int(token.item())
                times.append(time.perf_counter() - start)
                token_ids.append(token_id)
                if first_logits is None:
                    first_logits = logits
                if not ignore_eos and token_id in eos_ids:
                    break
                inputs = token.reshape(1, 1)
            mx.synchronize()
            engine_ms = (time.perf_counter() - start) * 1000
            peak_bytes = mx.get_peak_memory()
            finite = bool(mx.all(mx.isfinite(first_logits)).item() and mx.all(mx.isfinite(logits)).item())
            assert finite, 'Non-finite first/final logits'
            text = tokenizer.decode(token_ids, skip_special_tokens=True)
            request_ms = (time.perf_counter() - start) * 1000
            stopped_eos = not ignore_eos and token_ids[-1] in eos_ids
            row = {'kind': kind, 'id': name, 'repetition': repetition, 'timestamp_unix': epoch,
                   'input_token_count': len(ids), 'input_token_ids': ids, 'rendered_prompt': rendered,
                   'output_token_count_including_eos': len(token_ids), 'output_token_ids': token_ids,
                   'non_eos_token_count': sum(t not in eos_ids for t in token_ids),
                   'eos_token_count': sum(t in eos_ids for t in token_ids), 'text': text,
                   'ignore_eos': ignore_eos, 'stop_reason': 'eos' if stopped_eos else 'max_tokens',
                   'token_completion_seconds': times, 'engine_ms': engine_ms,
                   'request_ms_including_detokenization_and_finite_check': request_ms,
                   'peak_active_bytes': peak_bytes, 'first_final_logits_finite': finite,
                   **timing_metrics(times)}
            if expected is not None:
                row.update(expected=expected, passed=stopped_eos and score(text, expected))
            if ignore_eos:
                assert len(token_ids) == 64 and row['decode_intervals'] == 63
            emit(row)
            print(f'{kind} {name}: {len(ids)} inputs, {len(token_ids)} outputs, {engine_ms:.1f}ms', flush=True)

        if args.mode in ('smoke', 'cold', 'smoke-capital'):
            name, prompt, expected = (('capital', 'What is the capital of Australia?', 'Canberra')
                                      if args.mode == 'smoke-capital' else PROMPTS[0])
            rendered, ids = prepare(prompt)
            run(ids, rendered, name, args.mode, expected=expected)
            return
        # Keep the real assistant/thinking-off suffix; insert repeated ordinary tokens into user content.
        marker = 'BENCHMARK_PAYLOAD_MARKER'
        rendered, _ = prepare(marker)
        before, after = rendered.split(marker)
        prefix = tokenizer.encode(before, add_special_tokens=False)
        suffix = tokenizer.encode(after, add_special_tokens=False)
        repeat_id = tokenizer.encode(' data', add_special_tokens=False)[0]
        assert repeat_id not in tokenizer.all_special_ids
        workloads = {}
        for length in (128, 512, 2048):
            ids = prefix + [repeat_id] * (length - len(prefix) - len(suffix)) + suffix
            assert len(ids) == length
            workloads[length] = (ids, tokenizer.decode(ids, skip_special_tokens=False))
            run(*workloads[length], f'length_{length}', 'warmup', ignore_eos=True)
        for repetition in range(5):
            order = (128, 512, 2048) if repetition % 2 == 0 else (2048, 512, 128)
            for length in order:
                run(*workloads[length], f'length_{length}', 'measured', ignore_eos=True, repetition=repetition)
        for name, prompt, expected in PROMPTS:
            rendered, ids = prepare(prompt)
            run(ids, rendered, name, 'functional', expected=expected)


if __name__ == '__main__':
    main()
