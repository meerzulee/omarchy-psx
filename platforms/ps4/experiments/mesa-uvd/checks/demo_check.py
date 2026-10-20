#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Portable host checks of demo.py; no player, sudo, debugfs or GPU calls.

Run with Python 3.10+ from any working directory. Synthetic fence text replaces
hardware evidence; process/boot boundaries are mocked for default preflight.
Actual pinned mpv option-name compatibility remains the real preflight's job.
"""
import contextlib,copy,hashlib,importlib.util,io,json,pathlib,socket,sys,tempfile,threading,types
from unittest import mock
sys.dont_write_bytecode=True
source=pathlib.Path(__file__).resolve().parents[1] / 'demo.py'
spec=importlib.util.spec_from_file_location('demo',source);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
checks=0
def check(ok):
 global checks
 checks+=1
 if not ok:raise AssertionError('Check failed')

def refuses(fn):
 global checks;checks+=1
 try:fn()
 except RuntimeError:return
 raise AssertionError('should refuse')

text='--- ring 0 (gfx) ---\nLast signaled fence 0x999\nLast emitted 0x999\n--- ring 11 (ps4_uvd) ---\nLast signaled fence 0x27d\nLast emitted 0x27d\n--- ring 12 (other) ---\nLast signaled fence 0x777\nLast emitted 0x777\n'
f=d.parse_fence(text);check(f=={'completed':0x27d,'emitted':0x27d})
refuses(lambda:d.parse_fence(text+text));refuses(lambda:d.parse_fence(''))
refuses(lambda:d.parse_fence('--- ring 11 (ps4_uvd) ---\nLast signaled fence 0x3\nLast emitted 0x2\n'))
s={'hwdec-current':'vaapi-copy','video-params':{'w':1920,'h':1080},'video-codec':'h264',
   'current-vo':'gpu','vo-configured':True,'pause':False,'duration':30.0,'time-pos':0.0,
   'frame-drop-count':0,'decoder-frame-drop-count':0}
d.gate(s);checks+=1
for key,value in [('hwdec-current','no'),('current-vo','wlshm'),('vo-configured',False),('pause',True),('duration',0),('time-pos',None),('decoder-frame-drop-count',None),('video-codec','hevc'),('video-params',{'w':1920,'h':1088})]:
 bad=copy.deepcopy(s);bad[key]=value;refuses(lambda:d.gate(bad))
initial=copy.deepcopy(s);initial['pause']=True;d.gate(initial,initial=True);checks+=1
p=d.Progress(30,0,{'completed':5,'emitted':5},0)
for t in range(1,95):
 sample=copy.deepcopy(s);sample['time-pos']=t%30
 metrics=p.update(sample,{'completed':t+5,'emitted':t+5},t)
check(p.wraps==3);check(metrics['current_pass']==4);check(abs(metrics['pts_wall_speed']-1)<1e-9);check(p.clean)
q=d.Progress(30,0,f,0);bad=copy.deepcopy(s);bad['time-pos']=1
refuses(lambda:q.update(bad,f,10));refuses(lambda:q.update(bad,{'completed':1,'emitted':1},1))
q=d.Progress(30,20,{'completed':0,'emitted':0},0);bad['time-pos']=0
refuses(lambda:q.update(bad,{'completed':1,'emitted':1},1))
q=d.Progress(30,0,{'completed':0,'emitted':0},0);bad=copy.deepcopy(s);bad['time-pos']=1;bad['frame-drop-count']=1
q.update(bad,{'completed':1,'emitted':1},1);check(not q.clean)
for line in ['Failed to end picture decode issue: 1','Error while decoding frame!','Hardware decoding failed','vaapi: operation failed','GPU reset','fatal error: dead']:
 check(d.TERMINAL.search(line) is not None)
for line in ['0 decode errors','No fatal issues','Decoded frame 100 successfully','UVD completed 777']:
 check(d.TERMINAL.search(line) is None)
# The requested decoder thread gate accepts actual singular/plural log forms only.
check(not d.single_hwdec_thread('decoder not yet initialized'))
check(d.single_hwdec_thread('[vd] Requesting 1 threads for decoding.'))
check(d.single_hwdec_thread('[vd] Requesting 1 thread for decoding.'))
check(d.single_hwdec_thread('Requesting   1  threads for decoding.'))
for bad in ('Requesting 4 threads for decoding.', 'Requesting 0 threads for decoding.',
            'Requesting 1 threads for decoding.\nRequesting 4 threads for decoding.'):
 refuses(lambda:d.single_hwdec_thread(bad))
for line in ('amdgpu: The CS has been rejected (-28), see dmesg for more information.',
             'amdgpu: CS rejected, see dmesg for more information (-28).'):
 check(d.TERMINAL.search(line) is not None)
check(d.TERMINAL.search('amdgpu: The CS has been rejected (-2), see dmesg for more information.') is None)
# Keep the demonstrated hardware-only, paused, controlled infinite-loop contract.
args=d.playback_args(pathlib.Path('/clip'),pathlib.Path('/out'))
for option in ('--hwdec-threads=1','--vd-lavc-threads=1','--hwdec=vaapi-copy',
               '--hwdec-codecs=h264','--hwdec-software-fallback=no','--pause=yes',
               '--loop-file=inf','--load-scripts=no','--input-default-bindings=no',
               '--input-builtin-bindings=no','--input-vo-keyboard=no','--input-terminal=no'):
 check(args.count(option)==1)
check(args[-2:]==['--','/clip'])

# Exercise the real RPC parser's event/reply filtering and terminal end-file path.
a,b=socket.socketpair();ipc=d.IPC.__new__(d.IPC);ipc.sock=a;a.settimeout(1);ipc.stream=a.makefile('rb');ipc.serial=0
reader=b.makefile('rb')
def server():
 req=json.loads(reader.readline());b.sendall((json.dumps({'event':'tick'})+'\n'+json.dumps({'request_id':req['request_id'],'error':'success','data':42})+'\n').encode())
 req=json.loads(reader.readline());b.sendall((json.dumps({'event':'end-file','reason':'error','file_error':'decode failed'})+'\n').encode())
t=threading.Thread(target=server,daemon=True);t.start();check(ipc.call('get_property','time-pos')==42);refuses(lambda:ipc.call('get_property','time-pos'));t.join(1);check(not t.is_alive());ipc.close();reader.close();b.close()
# Run actual default main(), with only process/boot boundaries mocked.
with tempfile.TemporaryDirectory(prefix='ps4-demo-') as tmp:
 root=pathlib.Path(tmp);clip=root/'clip.mp4';clip.write_bytes(b'fixture');mpv=root/'mpv';mpv.write_bytes(b'mpvfixture');stage=root/'mesa';stage.mkdir();out=root/'out'
 args=['demo.py','--output',str(out),'--mesa-root',str(stage),'--manifest-sha256','0'*64,'--clip',str(clip),'--clip-sha256',d.digest(clip),'--boot-id','testboot','--release','testrelease']
 options='\n'.join('--'+x.removeprefix('--').split('=')[0].removeprefix('no-')+' Flag' for x in d.playback_args(clip,out)[1:-2] if x.startswith('--'))
 def run(argv,**kw):
  if argv[:2]==[sys.executable,str(source.with_name('with-mesa.py'))] and '--verify-only' in argv:return types.SimpleNamespace(stdout='{"verified": true}')
  if argv==[str(mpv),'--no-config','--list-options']:return types.SimpleNamespace(stdout=options)
  if argv==[str(mpv),'--no-config','--list-properties']:return types.SimpleNamespace(stdout='time-pos\nhwdec-current\n')
  raise AssertionError('unexpected subprocess '+repr(argv))
 read=pathlib.Path.read_text
 def read_text(path,*a,**kw):
  if str(path)=='/proc/sys/kernel/random/boot_id':return 'testboot\n'
  if str(path).startswith(('/proc/','/sys/')):raise AssertionError('Unexpected live-resource read: '+str(path))
  return read(path,*a,**kw)
 with mock.patch.object(d.sys,'argv',args),mock.patch.object(d.sys,'platform','linux'),mock.patch.object(d.platform,'machine',return_value='x86_64'),mock.patch.object(d.platform,'release',return_value='testrelease'),mock.patch.object(d.os,'geteuid',return_value=1000),mock.patch.object(d,'MPV',mpv),mock.patch.object(d,'MPV_SHA256',d.digest(mpv)),mock.patch.object(d.subprocess,'run',side_effect=run),mock.patch.object(d.subprocess,'Popen',side_effect=AssertionError('Popen forbidden in preflight')),mock.patch.object(d,'read_fence',side_effect=AssertionError('debugfs forbidden in preflight')),mock.patch.object(pathlib.Path,'read_text',read_text):
  with contextlib.redirect_stdout(io.StringIO()):
   check(d.main()==0)
 check((out/'PREFLIGHT.json').is_file());check(not (out/'PROCESS.json').exists())
receipt={'status':'PASS','checks':checks,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Synthetic/host mocks of actual parsers, gates, progress, IPC and default preflight; no live player or hardware.'}
print(json.dumps(receipt,sort_keys=True))
