from pathlib import Path
import json, statistics
root=Path(__file__).resolve().parent
rows=[json.loads(line) for line in (root/'runs/campaign.jsonl').read_text().splitlines()]
measured=[r for r in rows if r['kind']=='measured']
assert len(measured)==15
assert len([r for r in rows if r['kind']=='warmup'])==3
summary={'environment':rows[0], 'performance':[], 'functional':[r for r in rows if r['kind']=='functional'], 'cold':[]}
for n in (128,512,2048):
 group=[r for r in measured if r['input_token_count']==n]
 assert len(group)==5
 assert all(r['output_token_count_including_eos']==64 and r['decode_intervals']==63 and r['first_final_logits_finite'] for r in group)
 metrics={k:{'median':statistics.median(r[k] for r in group),'min':min(r[k] for r in group),'max':max(r[k] for r in group)} for k in ['ttft_ms','decode_tokens_per_second','engine_ms','peak_active_bytes']}
 summary['performance'].append({'input_tokens':n,**metrics})
for i in range(1,4):
 cold=[json.loads(line) for line in (root/f'runs/cold-{i}.jsonl').read_text().splitlines()]
 assert len(cold)==2 and cold[1]['kind']=='cold'
 summary['cold'].append({'load_ms':cold[0]['model_load_ms'],'request':cold[1],'process':json.loads((root/f'runs/cold-{i}-process.json').read_text())})
assert len(summary['functional'])==8
(root/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'performance':summary['performance'],'functional':[(r['id'],r['passed'],r['text']) for r in summary['functional']],'cold_load_ms':[r['load_ms'] for r in summary['cold']]},indent=2))
