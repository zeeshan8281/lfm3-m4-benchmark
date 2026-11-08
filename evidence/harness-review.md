# Independent harness source review

Reviewed actual harness.py and installed mlx_vlm/models/lfm3/{lfm3.py,language.py}, chat_template.jinja, and cache evaluation pattern in mlx_vlm/generate/ar.py. No inference ran in this review.

Reviewed harness SHA256: aa0327f81beaa8a38669f85eaf62b9974270753ccd1cebe613a0d27e2078bdd4

- Model.make_cache creates fresh convolution/recurrent and KV states for every request; state is not reused between measured prompts.
- Direct language_model forward returns documented logits; argmax implements greedy sampling without penalties. Native chat template supports enable_thinking=False and harness asserts its closed thinking suffix.
- Each sampled token and each cache state is evaluated before GPU synchronization and the timestamp. This measures actual synchronous evaluated work with host overhead, not lazy graph construction.
- Exactly64generatedtokens require oneprefillforward plus63incrementalforwards; last token is not unnecessarily fed back. Decode throughput numerator63 agrees with first-to-last timestamps.
- NaturalEOS includes terminalEOS in sampledcounts, tracks actualEOS/nonEOScounts, and only passes functionalchecks withEOSstop; forced64microbenchmarks explicitlyignoreEOS.
- JSONscorer rejectsduplicates, extrakeys, float/boolage andmarkdown. Executed scoring/accounting selfcheck only, successful.
- PeakactiveMLXallocation is resetperrequest and readbefore finite-check/detokenization; modelresidentmemory remainsincluded andthisisnotprocessRSS.
- Finitechecks coverfirst/finallogits, notallintermediateoutputs. This limitation is correctlynamed.
- Alternatinglengthorder, warmupexclusion andrawoutputs are implemented. Onlyonebackend ismeasured; no crossmodelMNNspeedup supported.

Two reviewchanges were requested and applied before campaign: realizecache.state atstepboundaries; replace misleadingforcedcontentcount with explicitEOS/nonEOScounts.

Timinglimits: inputs/tokenization/cachecreationexcluded; unchunkedprefill; syncpereverytoken mayreducethroughputversusoptimizedasyncstockiterator. request_ms includesposthocfinitechecks anddetokenization andmustnotbeadvertisedasnetwork/APIend-to-endlatency. Freshprocessload excludesPythonimports, whileexternaltime cancoverimports. GPUconfiguredandexecutedmodel stillrequiresrunreceipts; no claimofeveryoperationGPUresidency.

Source review passes for stated experiment. Rawcampaign audit pending separately.

Follow-up: reviewed additional smoke-capital mode; it changes only the exploratory prompt branch, not measured campaign engine. READY smoke JSONL contains actual outputREADY,3sampledtokensincludingEOS,2nonEOStokens and finitefirst/finallogits. Campaignrawauditstillpending.

Final smoke-capital prompt includes only-city-name instruction. Reviewed parity-check.json: identical26inputIDs and10outputIDs fordirect andstockgenerate_step, bothincorrectSydneywithstraythinkingmarker. This is narrowparityevidence, notabroadbackend-equivalenceaudit. Thinkingdisabledtemplate doesnotguarantee absenceofgeneratedthinkingmarkers.
