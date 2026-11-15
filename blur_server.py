import json,os,socket,threading,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
PORT=8000
D=os.path.dirname(os.path.abspath(__file__))
R={}
LK=threading.Lock()
def fresh():
    R.clear()
    R.update(host=0,cl={},start=None,started=0,snap='{}',ins={},evs=[])
fresh()
def ips():
    out=set()
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('10.255.255.255',1));out.add(s.getsockname()[0]);s.close()
    except Exception:pass
    try:out.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except Exception:pass
    out.discard('127.0.0.1')
    return sorted(out)
def handle(ep,raw):
    if ep=='ping':return json.dumps({'ok':1,'ips':ips(),'port':PORT})
    if ep=='h':
        R['snap']=raw;now=time.time()
        ins={k:v[0] for k,v in R['ins'].items() if now-v[1]<1.5}
        ev=R['evs'];R['evs']=[]
        return json.dumps({'ins':ins,'ev':ev})
    try:d=json.loads(raw or '{}')
    except Exception:d={}
    if ep=='c':
        i=str(d.get('id'));R['ins'][i]=(d.get('inp',{}),time.time())
        for j in d.get('ev',[]):R['evs'].append({'id':int(i),'j':j})
        return R['snap']
    if ep=='host':
        fresh();R['host']=1;return '{"ok":1}'
    if ep=='join':
        if not R['host'] or R['started']:return json.dumps({'err':'بازی‌ای ساخته نشده یا شروع شده'},ensure_ascii=False)
        if len(R['cl'])>=3:return json.dumps({'err':'ظرفیت پر است'},ensure_ascii=False)
        i=len(R['cl'])+1;R['cl'][i]={'car':d.get('car',0),'col':d.get('col',0)}
        return json.dumps({'id':i})
    if ep=='lobby':return json.dumps({'host':R['host'],'started':R['started'],'cl':R['cl'],'start':R['start']})
    if ep=='start':
        R['start']=d;R['started']=1;return '{"ok":1}'
    return '{}'
class Hd(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def setup(self):
        super().setup()
        try:self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        except Exception:pass
    def log_message(self,*a):pass
    def reply(self,body,ct='application/json'):
        b=body if isinstance(body,bytes) else body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type',ct+'; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        p=os.path.join(D,'blur-racing.html')
        if self.path.split('?')[0] in ('/','/index.html') and os.path.exists(p):
            self.reply(open(p,'rb').read(),'text/html')
        else:
            self.reply('blur-racing.html must be next to this file','text/plain')
    def do_POST(self):
        n=int(self.headers.get('Content-Length') or 0)
        raw=self.rfile.read(n).decode('utf-8','ignore')
        with LK:out=handle(self.path.rsplit('/',1)[-1],raw)
        self.reply(out)
if __name__=='__main__':
    ThreadingHTTPServer.daemon_threads=True
    s=ThreadingHTTPServer(('0.0.0.0',PORT),Hd)
    print('Blur Racing server running')
    print('On this device open: http://localhost:%d'%PORT)
    for ip in ips():print('Other devices open: http://%s:%d'%(ip,PORT))
    print('If no IP is shown, use your hotspot IP (often 192.168.43.1)')
    s.serve_forever()
