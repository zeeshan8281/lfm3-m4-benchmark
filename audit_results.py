"""Independent raw-results audit; does not import MLX or execute inference."""
from pathlib import Path
import hashlib,json,statistics
ROOT=Path(__file__).resolve().parent

def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def strict_score(row):
    text=row['text'].strip();expected=row['expected']
    if isinstance(expected,str): return text==expected
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise ValueError(k)
            d[k]=v
        return d
    try:v=json.loads(text,object_pairs_hook=unique)
    except ValueError:return False
    return type(v) is dict and set(v)==set(expected) and all(type(v[k]) is type(expected[k]) and v[k]==expected[k] for k in v)

def validate(rows):
    env=rows[0]; assert env['kind']=='environment'
    assert env['device']=='Device(gpu, 0)' and env['metal_available']
    assert env['harness_sha256']==hashlib.sha256((ROOT/'harness.py').read_bytes()).hexdigest()
    eos=set(env['eos_token_ids'])
    for r in rows[1:]:
        ids=r['output_token_ids']; t=r['token_completion_seconds']; n=len(ids)
        assert r['input_token_count']==len(r['input_token_ids'])
        assert n==r['output_token_count_including_eos']==len(t)
        assert t[0]>0 and all(b>a for a,b in zip(t,t[1:]))
        assert r['decode_intervals']==n-1 and abs(r['ttft_ms']-t[0]*1000)<1e-6
        assert abs(r['generation_ms']-t[-1]*1000)<1e-6
        assert abs(r['decode_ms']-(t[-1]-t[0])*1000)<1e-6
        if n>1: assert abs(r['decode_tokens_per_second']-(n-1)/(t[-1]-t[0]))<1e-6
        else: assert r['decode_tokens_per_second'] is None
        assert r['engine_ms']>=r['generation_ms']
        assert r['request_ms_including_detokenization_and_finite_check']>=r['engine_ms']
        assert r['first_final_logits_finite'] is True
        assert r['non_eos_token_count']==sum(i not in eos for i in ids)
        assert r['eos_token_count']==sum(i in eos for i in ids)
        if r['ignore_eos']: assert n==64 and r['stop_reason']=='max_tokens'
        elif r['stop_reason']=='eos': assert ids[-1] in eos
        else: assert n==64 and not any(i in eos for i in ids)
        if 'passed' in r: assert r['passed']==(r['stop_reason']=='eos' and strict_score(r))
    return env

def main():
    campaign=read(ROOT/'runs/campaign.jsonl');env=validate(campaign)
    measured=[r for r in campaign if r['kind']=='measured'];warm=[r for r in campaign if r['kind']=='warmup'];functional=[r for r in campaign if r['kind']=='functional']
    assert len(measured)==15 and len(warm)==3 and len(functional)==8
    assert len({r['id'] for r in functional})==8
    summary=[]
    for length in [128,512,2048]:
        rs=[r for r in measured if r['input_token_count']==length]
        assert len(rs)==5 and sorted(r['repetition'] for r in rs)==list(range(5))
        assert len([r for r in warm if r['input_token_count']==length])==1
        assert len({tuple(r['input_token_ids']) for r in rs})==1
        summary.append({'input_tokens':length,**{k:statistics.median(r[k] for r in rs) for k in ['ttft_ms','decode_tokens_per_second','engine_ms','peak_active_bytes']}})
    cold=[];pids={env['pid']}
    for i in range(1,4):
        rows=read(ROOT/f'runs/cold-{i}.jsonl');e=validate(rows);assert len(rows)==2 and rows[1]['kind']=='cold';pids.add(e['pid']);cold.append({'load_ms':e['model_load_ms'],'ttft_ms':rows[1]['ttft_ms'],'passed':rows[1]['passed']})
    assert len(pids)==4
    for name in ['campaign','cold-1','cold-2','cold-3']:
        p=json.loads((ROOT/f'runs/{name}-process.json').read_text());assert p['returncode']==0 and p['process_wall_seconds']>0
    published=json.loads((ROOT/'summary.json').read_text())
    for r in summary:
        q=next(x for x in published['performance'] if x['input_tokens']==r['input_tokens'])
        for key in ['ttft_ms','decode_tokens_per_second','engine_ms','peak_active_bytes']:
            vals=[x[key] for x in measured if x['input_token_count']==r['input_tokens']]
            assert q[key]=={'median':statistics.median(vals),'min':min(vals),'max':max(vals)}
    assert published['functional']==functional
    result={'summary_matches_raw':True,'summary_statistics_checked':36,'passed':True,'warmups':3,'measured':15,'functional':8,'cold_processes':3,'functional_passes':sum(r['passed'] for r in functional),'summary_recomputed':summary,'cold':cold,'limits':'Source/raw audit only; no inference run by reviewer. GPU configuration and synchronous evaluated outputs observed; not a per-kernel profiler audit.'}
    (ROOT/'evidence/results-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
