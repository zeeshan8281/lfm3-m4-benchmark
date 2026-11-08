# LFM3-1.7B on the user's M4: benchmark protocol

Prepared 2026-11-08 before measurements. This protocol measures a real pinned LFM3 model on the actual local machine. It does not substitute published speeds, synthetic output or another model for execution.

## Scope and pinning

Run the official `LiquidAI/LFM3-1.7B-MLX-4bit` checkpoint through its documented supported runtime, subject to inspection of installed source and an actual model-load smoke test. Record immutable HF revision, every required filename/byte count/hash, model config, quantization metadata, tokenizer and chat template. Record runtime versions and Git commit for any source checkout, Python/macOS/MLX versions, hardware identity and memory, power source/battery and available thermal-pressure observations before/after. Never state CPU versus GPU or native Metal execution without actual evidence of the configured device and evaluated graph/backend.

Research currently identifies MLX-VLM>=0.7.11 as the documented route; this is a candidate configuration, not a verified API or successful run. Inspect runtime code before deciding function names, prompt formatting, stop handling, seed control, evaluation and peak-memory functions. Retain the exact source locations inspected and command used. No runtime change after measured runs without rerunning affected cases and preserving the earlier results.

Primary comparison is prompt length on one fixed real backend and checkpoint. Do not add a CPU comparator or change quantization silently. Report this as LFM3 performance, not a speedup over MNN-Pocket: different models and the older MNN harness's 64 decode-forward accounting are not a matched comparison.

## Timing boundaries and deterministic sampling

Use greedy selection (temperature zero only if inspected implementation actually maps it to argmax), thinking disabled through the actual supported model/template switch, and fresh recurrent/KV state for every measured request. Save rendered prompt and exact token ids. Verify thinking suppression rather than inventing an API parameter; if no supported switch exists, document the effective template and observed behaviour.

MLX is lazy and asynchronous. Every timed interval must enclose actual evaluated work, not graph construction. Use synchronization/evaluation APIs only after confirming their signatures and semantics in the installed version. Evaluate loaded model arrays before ending model-load timing if loading is lazy. Flush prior work before a measurement, and ensure the measured output arrays are realized before stopping its clock. Do not include text formatting, scoring or JSON serialization in engine timing. Separately retain end-to-end request wall time.

Record these distinct quantities when genuinely observable:

- Process launch through exit, externally timed; separate import/model initialization/tokenization and request time where boundaries are instrumented.
- Prompt prefill elapsed time and actual prompt token count, with first next-token logits realized. If the public iterator hides this boundary, call it first-token latency rather than pretending it is pure prefill.
- TTFT from request start through the first realized generated token. Record time to first visible text separately if available, because detokenization can buffer tokens.
- Decode latency from first realized generated token to last realized generated token. For64 generated tokens this covers63 incremental token intervals; throughput is63 divided by that elapsed time. A runtime's built-in denominator may differ: retain original metrics and explicitly name its accounting.
- Total generation wall time for64 output tokens and full request wall time. EOS membership in generated token counts must be explicit.
- Runtime peak allocated/active device memory, using documented reset/read API if available, with scope recorded. Process RSS is a separate measure, never labeled GPU memory. Baseline/model-resident memory should be reported where observable; shared unified memory must not be added to RSS as though disjoint.

If split timing cannot be measured without changing model execution, prefer reliable end-to-end time and actual token counts over fabricated precision. Record clock type and units.

## Warm performance campaign

Use exactly128,512 and2048 input token ids after all templating. Prepare reproducible fixed workloads in advance, save ids and decoded text, and assert lengths before each run. Exact-token synthetic repeated-token workloads are acceptable for a clearly labeled performance microbenchmark, not quality validation. If instead using natural prose, report actual post-template lengths and do not mislabel approximate lengths as exact.

Generate exactly64 tokens with EOS stopping disabled only for the fixed-length microbenchmark. Keep all other sampling settings identical. Inspect how the real runtime disables EOS; if unsupported, report naturally stopped token counts and do not claim a fixed64-token comparison. Fresh cache/state per request, no cross-request prefix reuse.

Run at least one unreported warmup per input length, retained in raw logs. Then run five measured repetitions per input length (15measured requests). Alternate prompt lengths in a predetermined order across repetitions (e.g.128/512/2048 then2048/512/128) to reduce simple thermal-order bias. Record every result, including slow samples, failures, stop reason and timestamps. Do not run simultaneous model timing jobs. The independent reviewer must not execute inference during this campaign.

Summarize medians with min/max and all raw samples. Five samples are insufficient for meaningfulp99claims or broadstatisticalsignificance. Any rerun needs a reason and both original/replacement evidence retained. Optional extra samples only to resolve an observed failure or substantial variance.

## Fresh-process campaign

Three separate fresh processes run the same short READY probe with naturalEOS enabled and64-token cap. Include complete command/exit status and capture raw stdout/stderr. Label this process-cold, not disk-cold: file-system, shader anddrivercaches remain uncontrolled. Preserve first-ever exploratory load separately; do not discard it and claim subsequent loads represent a virgin install.

## Functional checks with natural stopping

Use a fresh request state for each; naturalEOS enabled, cap64tokens, greedy, thinkingoff. Save complete outputs, input/output tokenids and stopreason. A cap hit is a reported failure/incomplete response, never silently treated as EOS. These eight checks test narrow instruction adherence, not generalmodelaccuracy. Score once using fixedcriteria, preserving failedoutputs.

| ID | Exact user prompt | Pass criterion |
|---|---|---|
| ready | Reply with exactly READY and nothing else. | Trim outer whitespace, then exact `READY`. |
| arithmetic | What is 17 + 26? Reply with only the integer. | Trim outer whitespace, then exact `43`. |
| subtraction | What is 13 - 8? Reply with only the integer. | Trim outer whitespace, then exact `5`. |
| extract | Extract the tracking code from this sentence: Your package AB-204 arrives tomorrow. Reply with only the code. | Trim outer whitespace, then exact `AB-204`. |
| sort | Sort these integers in ascending order: 3, 1, 2. Reply with only the sorted integers separated by commas, with no spaces. | Trim outer whitespace, then exact `1,2,3`. |
| json | Return only a JSON object with exactly these fields: name is the string Ada; age is the integer 27. | Valid single JSON object, exactly keysname/age, stringAda, integer27 (notbool/float), no duplicatekeys, no markdown or trailingcontent; keyorderirrelevant. |
| classification | Classify the sentiment of this review as POSITIVE or NEGATIVE: I loved this book and would read it again. Reply with only the label. | Trim outer whitespace, then exact `POSITIVE`. |
| negation | Read this record: Maya lives in Lisbon. Her brother lives in Porto. Where does Maya live? Reply with only the city name. | Trim outer whitespace, then exact `Lisbon`. |

If any unexpected output appears, preserve it first. A small fixed follow-up (three repetitions of the failing prompt under unchanged configuration) may establish repeatability; do not select improved wording to erase the original failure. Do not infer a numerical root cause without targeted evidence.

## Evidence and completion checks

Save manifest, protocol hash, harness hash, raw per-request JSON, process logs, rendered prompts/tokenids, output text, summary and plots. Include finite checks on observed output logits where accessible without alteringtiming. No NaNs or empty outputs should pass simply because elapsedtime is positive.

Reviewer checks: actual measured counts/warmup exclusion; clock/denominator correctness; cache resets; deterministic sampler and thinking setting;64actualoutputtoken accounting; memoryscope; cold-label accuracy; outputscorers; file hashes; raw-to-summary recomputation. Review requires source inspection of the final harness, not this protocolalone.

Completion means successful real inference evidence with honestfailures, not necessarily8/8functionalpasses. Remainingunsupportedmetrics orfailedcases must be plainly reported. No publishing, fabricatedmeasurements orweightdownload required by this protocol-writing subtask.
