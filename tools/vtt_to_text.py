import re,sys,io,html

def clean(path):
    raw=io.open(path,encoding='utf-8').read()
    raw=re.sub(r'<[^>]+>','',raw)
    out=[];seen=''
    for blk in raw.split('\n\n'):
        lines=[l.strip() for l in blk.strip().split('\n') if l.strip()]
        if not lines or lines[0].startswith(('WEBVTT','Kind:','Language:','NOTE')): continue
        ts=[l for l in lines if '-->' in l]
        if not ts: continue
        txt=' '.join(l for l in lines if '-->' not in l and not l.isdigit())
        txt=html.unescape(re.sub(r'\s+',' ',txt)).strip()
        if not txt or txt==seen: continue
        if seen and txt.startswith(seen): txt=txt[len(seen):].strip()
        elif seen.endswith(txt): continue
        if txt: out.append((ts[0].split(' --> ')[0][:8],txt)); seen=' '.join(lines[-1:]).strip()
    return out

if __name__=='__main__':
    r=clean(sys.argv[1])
    full=' '.join(t for _,t in r)
    full=re.sub(r'\s+',' ',full)
    io.open(sys.argv[2],'w',encoding='utf-8').write(full)
    print(f"{len(r)} реплик, {len(full.split())} слов, {len(full)} символов")
