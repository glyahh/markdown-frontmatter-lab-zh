"""Reproduce original tutorial fixtures without modifying them."""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def main():
    inputs = sorted((ROOT/'examples').rglob('*.md'))
    before = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    results=[]
    with tempfile.TemporaryDirectory(prefix='markdown-tutorial-') as tmp:
        for name, count, failed, code, errors in [('before',1,1,1,2),('after',1,0,0,0),('duplicate',2,2,1,2)]:
            output=Path(tmp)/name
            cmd=[sys.executable,str(ROOT/'content_check.py'),str(ROOT/'examples'/name),'--output',str(output)]
            proc=subprocess.run(cmd,capture_output=True,text=True)
            report=json.loads((output/'report.json').read_text(encoding='utf-8'))
            actual=(report['files'],report['failed'],proc.returncode,sum(len(r['errors']) for r in report['records']))
            if actual != (count,failed,code,errors): raise AssertionError((name,actual))
            if not (output/'report.html').is_file():raise AssertionError('Missing HTML')
            repeat=subprocess.run(cmd,capture_output=True,text=True)
            if repeat.returncode != 2: raise AssertionError('Overwrite not blocked')
            results.append({'case':name,'files':count,'failed':failed,'exit':code,'errors':errors,'overwrite_blocked':True})
        empty=Path(tmp)/'empty';empty.mkdir()
        p=subprocess.run([sys.executable,str(ROOT/'content_check.py'),str(empty),'--output',str(Path(tmp)/'empty-report')],capture_output=True,text=True)
        if p.returncode != 1: raise AssertionError('Empty input false pass')
    after={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    if before!=after:raise AssertionError('Input changed')
    print(json.dumps({'cases':results,'input_unchanged':True,'empty_exit':p.returncode},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
