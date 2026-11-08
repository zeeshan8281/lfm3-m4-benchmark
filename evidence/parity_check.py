import json,time
from pathlib import Path
import mlx.core as mx
from mlx_vlm import load
from mlx_vlm.generate.ar import generate_step
root=Path('/Users/zeeshan/lfm3-m4-benchmark')
mx.set_default_device(mx.gpu)
m,p=load(str(root/'model'),lazy=False)
t=getattr(p,'tokenizer',p)
source=json.loads((root/'evidence/smoke-capital-template.json').read_text())
ids=source['input_ids']; eos={124900}; rows=[]
for mode in ['direct','stock_generate_step']:
 out=[]
 if mode=='direct':
  cache=m.make_cache(); x=mx.array([ids])
  for _ in range(64):
   token=mx.argmax(m.language_model(x,cache=cache).logits[:,-1,:],axis=-1)
   mx.eval(token,[c.state for c in cache]);mx.synchronize();out.append(token.item());x=token.reshape(1,1)
   if out[-1] in eos:break
 else:
  gen=generate_step(mx.array([ids]),m,None,None,max_tokens=64,temperature=0,repetition_penalty=1.0,top_p=1.0,top_k=0,prompt_cache=m.make_cache())
  for token,_ in gen:
   out.append(int(token))
   if token in eos:break
  gen.close();mx.synchronize()
 rows.append({'mode':mode,'input_ids':ids,'output_ids':out,'text':t.decode(out,skip_special_tokens=True),'raw_text':t.decode(out,skip_special_tokens=False),'stopped_eos':out[-1]in eos})
result={'created_at_unix':time.time(),'rendered_prompt':source['rendered_prompt'],'same_tokens':rows[0]['output_ids']==rows[1]['output_ids'],'rows':rows}
(root/'evidence/parity-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
