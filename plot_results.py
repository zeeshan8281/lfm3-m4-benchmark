from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
s=json.loads((root/'summary.json').read_text())
rows=s['performance'];assert len(rows)==3
fig,axes=plt.subplots(1,3,figsize=(13,4.5))
for ax,key,title,label,color in zip(axes,['ttft_ms','decode_tokens_per_second','peak_active_bytes'],['First token','Decode throughput','Peak MLX active memory'],['Milliseconds','Tokens / second','GB (decimal)'],['#4f6ef7','#178e88','#d18c31']):
 scale=1e9 if key=='peak_active_bytes' else 1
 med=[r[key]['median']/scale for r in rows]
 err=[[r[key]['median']/scale-r[key]['min']/scale for r in rows],[r[key]['max']/scale-r[key]['median']/scale for r in rows]]
 bars=ax.bar(range(3),med,yerr=err,capsize=4,color=color,width=.6)
 ax.bar_label(bars,fmt='%.2f' if scale>1 else '%.1f',padding=5,fontsize=10)
 ax.set_xticks(range(3),[str(r['input_tokens']) for r in rows]);ax.set_xlabel('Input tokens');ax.set_ylabel(label);ax.set_title(title)
 ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.margins(y=.22)
fig.suptitle('LFM3-1.7B · MLX 4-bit · M4 Air 16 GB',fontsize=16)
fig.text(.5,.02,'Actual local GPU runs · medians of 5; whiskers = min/max · 64 generated tokens, 63 decode intervals\nSynchronous instrumented engine, unchunked prefill; synthetic inputs · battery power · memory includes model',ha='center',fontsize=8)
fig.tight_layout(rect=[0,.09,1,.93]);fig.savefig(root/'performance.png',dpi=180);fig.savefig(root/'performance.svg');plt.close(fig)
