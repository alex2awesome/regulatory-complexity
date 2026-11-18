#!/usr/bin/env python3
"""Mechanically partition captured independent-forum posts; no semantic labeling."""
from __future__ import annotations
import argparse, hashlib, html, json, re
from html.parser import HTMLParser
from pathlib import Path

class Posts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.stack=[]; self.cur=None; self.body_depth=0; self.author_depth=0; self.author=[]; self.out=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); cls=a.get('class','') or ''
        if (tag=='li' and 'b-post' in cls.split()) or (tag=='article' and 'message' in cls.split() and a.get('data-content')):
            if self.cur: self.out.append(self.cur)
            ident=a.get('data-node-id') or (a.get('data-content','').removeprefix('post-'))
            self.cur={'post_id':ident,'author':None,'created_at':None,'post_number':None,'body_parts':[],'depth':0}
        if not self.cur: return
        self.stack.append(tag); self.cur['depth']+=1
        if tag in ('div','article') and ('js-post__content-text' in cls.split() or 'message-body' in cls.split()): self.body_depth=self.cur['depth']
        if tag=='span' and a.get('itemprop')=='name': self.author_depth=self.cur['depth']; self.author=[]
        if tag=='time' and (a.get('itemprop') in ('dateCreated','datePublished') or a.get('datetime')): self.cur['created_at']=a.get('datetime')
        if tag=='a' and a.get('href','').find('#post')>=0: self.cur['post_number']=a['href'].rsplit('#post',1)[-1]
    def handle_endtag(self, tag):
        if not self.cur: return
        if self.author_depth==self.cur['depth'] and tag=='span': self.cur['author']=''.join(self.author).strip(); self.author_depth=0
        if self.body_depth and self.cur['depth']==self.body_depth and tag in ('div','article'): self.body_depth=0
        self.cur['depth']=max(0,self.cur['depth']-1)
        if self.stack: self.stack.pop()
        if self.cur['depth']==0:
            self.out.append(self.cur); self.cur=None
    def handle_data(self,data):
        if not self.cur: return
        if self.author_depth: self.author.append(data)
        if self.body_depth: self.cur['body_parts'].append(data)
    def close(self):
        super().close()
        if self.cur: self.out.append(self.cur); self.cur=None

def span(side, body):
    clean=' '.join(body.split())
    if not clean: return None,None
    first=' '.join(clean.split()[:12]); last=' '.join(clean.split()[-12:])
    def rx(s): return re.compile(r'\s+'.join(re.escape(x) for x in s.split()),re.I)
    m=rx(first).search(side)
    if not m: return None,None
    n=rx(last).search(side,m.end())
    return m.start(), (n.end() if n else m.end())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--spec',nargs='+',required=True); ap.add_argument('--out',required=True); args=ap.parse_args(); rows=[]
    for spec in args.spec:
        raw,text=map(Path,spec.split('=',1)); b=raw.read_bytes(); s=b.decode('utf-8',errors='replace'); side=text.read_bytes().decode('utf-8')
        p=Posts(); p.feed(s); p.close()
        for i,x in enumerate(p.out,1):
            body=''.join(x.pop('body_parts')).strip(); st,en=span(side,body)
            rows.append({'source':str(raw),'source_sha256':hashlib.sha256(b).hexdigest(),'text_path':str(text),'post_id':x.get('post_id'),'post_number':x.get('post_number') or str(i),'author':x.get('author'),'created_at':x.get('created_at'),'body':body,'text_char_start':st,'text_char_end':en,'body_words':len(body.split()),'body_chars':len(body)})
    Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(json.dumps({'schema_version':1,'posts':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'partitioned {len(rows)} posts')
if __name__=='__main__': main()
