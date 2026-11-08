import React from 'react';
import {AbsoluteFill,Composition,registerRoot,useCurrentFrame,interpolate,Easing} from 'remotion';
import d from './data.json';
const blue='#344af6',gray='#737b8b',colors=['#344af6','#009d92','#a25ae3'];
const grow=f=>interpolate(f,[0,90],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.out(Easing.cubic)});
const Card=({x,y,w,h,children})=><div style={{position:'absolute',left:x,top:y,width:w,height:h,padding:30,boxSizing:'border-box',borderRadius:26,border:'1px solid #e3e7ed',background:'#fff',boxShadow:'0 8px 30px #23335a09',overflow:'hidden'}}>{children}</div>;
const Title=({children})=><div style={{fontSize:28,fontWeight:700,letterSpacing:-.7,lineHeight:1.15}}>{children}</div>;
const Sub=({children})=><div style={{fontSize:20,color:gray,lineHeight:1.35,marginTop:8}}>{children}</div>;
const Foot=({children})=><div style={{position:'absolute',left:30,right:30,bottom:26,borderTop:'1px solid #e2e6ec',paddingTop:16,fontSize:19,color:gray,lineHeight:1.35}}>{children}</div>;
const Line=({points,color=blue,progress=1,width=3})=><path d={points.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' ')} fill="none" stroke={color} strokeWidth={width} strokeLinejoin="round" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-progress}/>;
const Trend=({metric,max,unit,width=375,color=blue,scale=1})=>{const f=useCurrentFrame(),p=grow(f-30),l=45,r=width-25,top=25,bottom=215;const pts=d.performance.map(v=>[l+(v.input_tokens-128)/1920*(r-l),bottom-v[metric].median/scale/max*(bottom-top)]);return <svg width={width} height="250" viewBox={`0 0 ${width} 270`} style={{marginTop:19,overflow:'visible'}}>
{[0,.5,1].map(t=><g key={t}><line x1={l} x2={r} y1={bottom-t*(bottom-top)} y2={bottom-t*(bottom-top)} stroke="#e8ecf2"/><text x={l-12} y={bottom-t*(bottom-top)+6} textAnchor="end" fill={gray} fontSize="16">{(t*max).toLocaleString('en-US',{maximumFractionDigits:2})}</text></g>)}
<text x="0" y="8" fill={gray} fontSize="16">{unit}</text><Line points={pts} color={color} progress={p} width={4}/>
{pts.map(([x,y],i)=><g key={i} opacity={grow(f-35-i*25)}><circle cx={x} cy={y} r="6" fill={color} stroke="white" strokeWidth="2"/><text x={x} y={y-15} textAnchor="middle" fill="#182030" fontSize="21" fontWeight="700">{(d.performance[i][metric].median/scale).toFixed(2)}</text></g>)}
{d.performance.map((v,i)=><text key={i} x={pts[i][0]} y="244" textAnchor="middle" fontSize="17" fill={gray}>{v.input_tokens}</text>)}<text x={(l+r)/2} y="269" textAnchor="middle" fontSize="16" fill={gray}>Input tokens</text></svg>};
const Film=()=>{const f=useCurrentFrame(),elapsed=f<36?0:(f/60-.6)%4,count=d.trace.times.filter(t=>t<=elapsed).length,end=d.trace.times.at(-1),shown=Math.min(elapsed,end);const latencyMax=Math.ceil(Math.max(...d.intervals_ms)/5)*5;return <AbsoluteFill style={{background:'#f2f4f8',fontFamily:'Arial, sans-serif',color:'#172031'}}>
<Card x={20} y={20} w={620} h={560}>
<div style={{fontSize:18,letterSpacing:3,color:gray}}>LOCAL INFERENCE / M4 AIR</div><div style={{fontSize:65,fontWeight:750,letterSpacing:-3,marginTop:19}}>LFM3-1.7B</div><Sub>MLX 4-bit · 16 GB · 973 MB weights</Sub>
<div style={{display:'flex',alignItems:'baseline',gap:14,marginTop:18}}><strong style={{fontSize:59,letterSpacing:-2,color:blue}}>74–77</strong><span style={{fontSize:22,color:gray}}>median tok/s</span></div>
<div style={{display:'flex',justifyContent:'space-between',fontSize:20,marginTop:16}}><strong>Individual decode steps</strong><span style={{color:gray}}>milliseconds</span></div>
<svg width="560" height="130" viewBox="0 0 560 150" style={{marginTop:7}}>{[0,.5,1].map(t=><g key={t}><line x1="35" x2="540" y1={122-t*105} y2={122-t*105} stroke="#e8ecf2"/><text x="27" y={128-t*105} fill={gray} fontSize="14" textAnchor="end">{Math.round(t*latencyMax)}</text></g>)}<Line points={d.intervals_ms.map((v,i)=>[35+i/62*505,122-v/latencyMax*105])} progress={grow(f-30)} width={2.5}/>{count>1&&<g><line x1={35+Math.min(count-2,62)/62*505} x2={35+Math.min(count-2,62)/62*505} y1="17" y2="122" stroke={blue} strokeDasharray="3 4" opacity=".35"/><circle cx={35+Math.min(count-2,62)/62*505} cy={122-d.intervals_ms[Math.min(count-2,62)]/latencyMax*105} r="4" fill={blue}/></g>}<text x="35" y="146" fontSize="14" fill={gray}>Step 1</text><text x="540" y="146" textAnchor="end" fontSize="14" fill={gray}>Step 63</text></svg>
<Foot>One recorded 128-token-input run · no smoothing<br/>Battery power · November 8, 2026</Foot>
</Card>
<Card x={660} y={20} w={740} h={560}>
<Title>Decode speed, run by run</Title><Sub>All 15 measurements · 3 prompt lengths · no samples removed</Sub>
<div style={{display:'flex',gap:27,marginTop:24}}>{d.performance.map((v,i)=><div key={i} style={{fontSize:19,color:colors[i]}}><span style={{display:'inline-block',width:20,height:4,background:colors[i],marginRight:8,verticalAlign:'middle'}}/>{v.input_tokens} tokens <strong>{v.decode_tokens_per_second.median.toFixed(1)}</strong><span style={{fontSize:15,color:gray}}> median</span></div>)}</div>
<svg width="680" height="260" viewBox="0 0 680 310" style={{marginTop:20}}>
<rect x={48+Math.floor((f/120)%5)*146.75-12} y="30" width="24" height="225" rx="8" fill="#344af608"/><line x1={48+Math.floor((f/120)%5)*146.75} x2={48+Math.floor((f/120)%5)*146.75} y1="30" y2="255" stroke="#bfc9e7" strokeDasharray="4 5"/>{[50,60,70,80,85].map(v=><g key={v}><line x1="48" x2="635" y1={255-(v-50)/35*225} y2={255-(v-50)/35*225} stroke="#e8ecf2"/><text x="36" y={261-(v-50)/35*225} textAnchor="end" fontSize="18" fill={gray}>{v}</text></g>)}<text x="0" y="15" fontSize="16" fill={gray}>tok/s</text>
{d.performance.map((r,k)=>{const samples=d.samples.filter(v=>v.input_token_count===r.input_tokens).sort((a,b)=>a.repetition-b.repetition),pts=samples.map((v,i)=>[48+i*146.75,255-(v.decode_tokens_per_second-50)/35*225]);return <g key={k}><Line points={pts} color={colors[k]} progress={grow(f-20-k*15)} width={3.5}/>{pts.map(([x,y],i)=><circle key={i} cx={x} cy={y} r={Math.floor((f/120)%5)===i?8:5} fill={colors[k]} stroke="white" strokeWidth="2" opacity={grow(f-20-i*18-k*12)}/>)}<text x="650" y={pts[4][1]+(k===1?-5:k===2?13:5)} fill={colors[k]} fontSize="17" fontWeight="700" opacity={grow(f-115)}>{samples[4].decode_tokens_per_second.toFixed(1)}</text></g>})}
{[1,2,3,4,5].map((v,i)=><text key={v} x={48+i*146.75} y="285" textAnchor="middle" fontSize="19" fill={gray}>{v}</text>)}<text x="340" y="308" textAnchor="middle" fontSize="16" fill={gray}>Repetition · alternating prompt-length order</text></svg>
<Foot>Observed slow runs: 63.3 and 60.5 tok/s<br/>Synchronous engine · 64 outputs / 63 decode intervals</Foot>
</Card>
<Card x={1420} y={20} w={480} h={560}>
<Title>Token arrivals over time</Title><Sub>Recorded run · original-speed replay</Sub>
<svg width="420" height="245" viewBox="0 0 420 277" style={{marginTop:22}}>
{[0,32,64].map(v=><g key={v}><line x1="38" x2="405" y1={223-v/64*195} y2={223-v/64*195} stroke="#e8ecf2"/><text x="27" y={229-v/64*195} fontSize="16" fill={gray} textAnchor="end">{v}</text></g>)}
<Line points={[[38,223],...d.trace.times.map((t,i)=>[38+t/1.1*367,223-(i+1)/64*195])]} color="#e4e8f9" width={3}/>
{count>0&&<><Line points={[[38,223],...d.trace.times.slice(0,count).map((t,i)=>[38+t/1.1*367,223-(i+1)/64*195])]} width={4}/><circle cx={38+d.trace.times[count-1]/1.1*367} cy={223-count/64*195} r="7" fill={blue}/></>}
{[0,.5,1].map(t=><text key={t} x={38+t/1.1*367} y="250" textAnchor="middle" fontSize="17" fill={gray}>{t.toFixed(1)}</text>)}<text x="218" y="275" textAnchor="middle" fontSize="16" fill={gray}>Elapsed seconds · from request start</text></svg>
<div style={{display:'flex',gap:12,alignItems:'baseline',marginTop:4}}><strong style={{fontSize:53,color:blue}}>{count}</strong><span style={{fontSize:22,color:gray}}>tokens / {shown.toFixed(2)} s</span></div>
<Foot>128-token prompt · 64 sampled tokens<br/>Measured replay, not live inference</Foot>
</Card>
<Card x={20} y={600} w={435} h={460}>
<Title>First-token latency</Title><Sub>Medians across prompt lengths</Sub><Trend metric="ttft_ms" max={3.5} unit="seconds" scale={1000}/><Foot>191 ms → 3.09 s · unchunked prefill</Foot>
</Card>
<Card x={475} y={600} w={495} h={460}>
<Title>Memory vs prompt length</Title><Sub>Peak MLX active allocation · medians</Sub><Trend metric="peak_active_bytes" max={2.5} unit="GB" scale={1e9} width={435} color="#009d92"/><Foot>Model included · not total system RAM</Foot>
</Card>
<Card x={990} y={600} w={470} h={460}>
<Title>Instruction checks</Title><Sub>strict format compliance · natural EOS</Sub><div style={{display:'flex',alignItems:'baseline',gap:12,marginTop:14}}><strong style={{fontSize:45,letterSpacing:-1}}>4 / 8</strong><span style={{fontSize:21,color:gray}}>passed</span></div><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px 20px',marginTop:19}}>{d.functional.map((r,i)=><div key={r.id} style={{display:'flex',gap:9,alignItems:'center',fontSize:20,opacity:grow((f-90-i*8)*3)}}><span style={{display:'inline-flex',alignItems:'center',justifyContent:'center',width:23,height:23,borderRadius:5,background:r.passed?'#e8edff':'#fbe7e4',color:r.passed?blue:'#df6259',fontWeight:700}}>{r.passed?'✓':'×'}</span>{['READY','Addition','Subtraction','Extraction','Sorting','JSON','Sentiment','City only'][i]}</div>)}</div><Foot>Extra text, spaces, thinking tags<br/>Small checks, not general accuracy</Foot>
</Card>
<Card x={1480} y={600} w={420} h={460}>
<Title>Speed ≠ correctness</Title><Sub>Australia’s capital · city name only</Sub><div style={{marginTop:26,padding:'19px 16px',background:'#fcf0ee',border:'1px solid #efd5d1',borderRadius:12,fontFamily:'monospace',fontSize:24,color:'#b64438',lineHeight:1.4,opacity:grow((f-160)*2)}}>Sydney.&lt;/think&gt;<br/>Sydney.</div><div style={{marginTop:20,fontSize:22,lineHeight:1.4}}>Same 10 output tokens<br/>in both execution paths.</div><Foot>Correct answer: Canberra<br/>One probe · cause unresolved</Foot>
</Card>
</AbsoluteFill>};
registerRoot(()=> <Composition id="LFM3Bento" component={Film} width={1920} height={1080} fps={60} durationInFrames={960}/>);
