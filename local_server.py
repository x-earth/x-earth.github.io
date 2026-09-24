#!/usr/bin/env python3
import json,mimetypes,os,secrets,shutil,time,urllib.parse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'.local-data'; FILES=DATA/'files'; DB=DATA/'data.json'; FILES.mkdir(parents=True,exist_ok=True)
if not DB.exists(): DB.write_text(json.dumps({'notes':[],'clips':[]},ensure_ascii=False),encoding='utf-8')
def db():
 try:return json.loads(DB.read_text(encoding='utf-8'))
 except:return {'notes':[],'clips':[]}
def save(x): DB.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def out(self,x,c=200):
  b=json.dumps(x,ensure_ascii=False).encode();self.send_response(c);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  p=urllib.parse.urlparse(self.path).path
  if p=='/api/state':
   x=db();x['files']=[{'name':f.name,'size':f.stat().st_size} for f in FILES.iterdir() if f.is_file()];return self.out(x)
  if p.startswith('/api/file/'):
   f=(FILES/urllib.parse.unquote(p[10:])).resolve()
   if f.parent!=FILES.resolve() or not f.is_file():return self.out({'error':'文件不存在'},404)
   self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(f.name)[0] or 'application/octet-stream');self.send_header('Content-Disposition',f'attachment; filename="{f.name}"');self.send_header('Content-Length',str(f.stat().st_size));self.end_headers();return shutil.copyfileobj(open(f,'rb'),self.wfile)
  return super().do_GET()
 def do_POST(self):
  p=urllib.parse.urlparse(self.path).path;n=int(self.headers.get('Content-Length',0))
  if p in ('/api/text','/api/note'):
   q=json.loads(self.rfile.read(n));x=db();key='clips' if p.endswith('text') else 'notes';item={'id':secrets.token_hex(8),'text':q.get('text',''),'created':time.time()};
   if key=='notes':item['title']=q.get('title','未命名')
   x[key].insert(0,item);x[key]=x[key][:100];save(x);return self.out(item)
  if p=='/api/upload':
   raw=self.rfile.read(n);boundary=self.headers.get('Content-Type','').split('boundary=',1)[-1].encode();saved=[]
   for part in raw.split(b'--'+boundary):
    if b'filename=' not in part:continue
    head,data=part.split(b'\r\n\r\n',1);data=data.rsplit(b'\r\n',1)[0];import re;m=re.search(rb'filename="([^"]*)"',head);name=os.path.basename(m.group(1).decode('utf8','replace')) if m else 'upload';name=secrets.token_hex(4)+'-'+name;(FILES/name).write_bytes(data);saved.append(name)
   return self.out({'files':saved})
  return self.out({'error':'未知接口'},404)
 def do_DELETE(self):
  p=urllib.parse.urlparse(self.path).path
  if p.startswith('/api/file/'):
   f=(FILES/urllib.parse.unquote(p[10:])).resolve()
   if f.parent==FILES.resolve() and f.is_file():f.unlink();return self.out({'ok':True})
  return self.out({'error':'文件不存在'},404)
 def log_message(self,*a):pass
if __name__=='__main__':print('本机主页: http://127.0.0.1:8765');ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
