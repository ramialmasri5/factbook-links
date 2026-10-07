#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, urllib.parse, urllib.request, urllib.error
GRAPH_VERSION=os.getenv('META_GRAPH_VERSION','v26.0')
TOKEN=os.getenv('META_ACCESS_TOKEN','').strip()
BASE=f'https://graph.facebook.com/{GRAPH_VERSION}'
def request(method,path,params=None):
    params=dict(params or {}); params['access_token']=params.get('access_token') or TOKEN
    data=None; url=f'{BASE}/{path.lstrip("/")}'
    if method in {'POST','DELETE'}: data=urllib.parse.urlencode(params).encode()
    else: url += '?' + urllib.parse.urlencode(params)
    req=urllib.request.Request(url,data=data,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as resp: return resp.status,json.loads(resp.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors='replace')
        try: payload=json.loads(body)
        except Exception: payload={'raw':body}
        return e.code,payload
def pages():
    status,data=request('GET','me/accounts',{'fields':'id,name,access_token','limit':100})
    if status>=300: raise RuntimeError(f'pages_http_{status}:{data}')
    return data.get('data') or []
def page_by_name(name):
    for p in pages():
        if str(p.get('name','')).strip().lower()==name.strip().lower(): return p
    raise RuntimeError(f'page_not_found:{name}')
def publish(page_name,message,link):
    p=page_by_name(page_name)
    status,data=request('POST',f'{p["id"]}/feed',{'message':message,'link':link,'access_token':p['access_token']})
    if status>=300: raise RuntimeError(f'publish_http_{status}:{data}')
    post_id=data.get('id')
    status,rb=request('GET',post_id,{'fields':'id,message,created_time,permalink_url,full_picture,attachments{title,description,url,unshimmed_url,media_type}','access_token':p['access_token']})
    if status>=300: raise RuntimeError(f'readback_http_{status}:{rb}')
    attachments=((rb.get('attachments') or {}).get('data') or [])
    verified=any(str(a.get('unshimmed_url') or '').rstrip('/')==link.rstrip('/') for a in attachments if isinstance(a,dict))
    print(json.dumps({'status':'PASS' if verified else 'FAIL','page':page_name,'post_id':post_id,'link_verified':verified,'readback':rb},ensure_ascii=False))
    if not verified: raise SystemExit(4)
def delete(page_name,post_id):
    p=page_by_name(page_name)
    status,data=request('DELETE',post_id,{'access_token':p['access_token']})
    ok=status<300 and bool(data.get('success'))
    print(json.dumps({'status':'PASS' if ok else 'FAIL','page':page_name,'post_id':post_id,'meta':data},ensure_ascii=False))
    if not ok: raise SystemExit(5)
def main():
    if not TOKEN: raise SystemExit('META_ACCESS_TOKEN missing')
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('publish'); p.add_argument('--page',required=True); p.add_argument('--message',required=True); p.add_argument('--link',required=True)
    d=sub.add_parser('delete'); d.add_argument('--page',required=True); d.add_argument('--post-id',required=True)
    a=ap.parse_args(); publish(a.page,a.message,a.link) if a.cmd=='publish' else delete(a.page,a.post_id)
if __name__=='__main__': main()
