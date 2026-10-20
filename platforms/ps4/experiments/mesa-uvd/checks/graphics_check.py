#!/usr/bin/env python3
"""Compile actual Mesa graphics functions; mock DRM query data only, no device I/O."""
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def block(text, anchor):
    start=text.index(anchor); opening=text.index('{',start)
    # Preserve offsets while ignoring braces in comments and literals.
    lex=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m:' '*len(m[0]),text,flags=re.S)
    depth=0
    for i in range(opening,len(text)):
        if lex[i]=='{': depth+=1
        if lex[i]=='}':
            depth-=1
            if not depth:return text[start:i+1]
    raise ValueError(anchor)

p=argparse.ArgumentParser(); p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--upstream',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--cc',default='clang');args=p.parse_args()
src=args.source.resolve();up=args.upstream.resolve();out=args.out.resolve();out.mkdir(exist_ok=False)
common=src/'src/amd/common'; base=up/'src/amd'; fixture=pathlib.Path(__file__).with_name('graphics_fixture.c')
text=(common/'ac_gpu_info.c').read_text();fam=(common/'amd_family.c').read_text()
for rel in ['src/amd/common/amd_family.h','src/amd/addrlib/src/amdgpu_asic_addr.h']:
    shutil.copy2(src/rel,out/pathlib.Path(rel).name)
meson=(base/'common/meson.build').read_text();lst=meson[meson.index('amd_register_files = ['):meson.index(']',meson.index('amd_register_files = ['))]
files=[(base/'common'/x).resolve() for x in re.findall(r"'([^']+\.json)'",lst)]
cmd=[sys.executable,str(base/'registers/makeregheader.py'),*map(str,files),'--sort','address','--guard','AMDGFXREGS_H']
r=subprocess.run(cmd,check=True,capture_output=True);(out/'amdgfxregs.h').write_bytes(r.stdout)
functions=[block(text,'bool\nac_identify_chip('),block(text,'int ac_get_gs_table_depth('),block(text,'void ac_get_raster_config(')]
family_source=re.sub(r'^#include[^\n]*\n','',fam,flags=re.M)
# Extract this complete original switch, not a separately implemented cache table.
cache=block(text[text.index('void\nac_fill_memory_info('):],'switch (info->family)')
rb_start=text.index('   info->max_render_backends = device_info->num_rb_pipes;');rb_end=text.index('\n\n',rb_start)
rb=text[rb_start:rb_end]
local_ranges=''.join(re.findall(r'^#define AMDGPU_[^\n]+\n',text,flags=re.M))
actual=local_ranges+'\n'+family_source+'\n\n'+'\n\n'.join(functions)+'\n\nvoid cache_class(struct radeon_info *info) {\n'+cache+'\n}\nvoid rb_class(struct radeon_info *info, const struct drm_amdgpu_info_device *device_info) {\n'+rb+'\n}\n'
(out/'actual_graphics.inc').write_text(actual);shutil.copy2(fixture,out/fixture.name)
commands=[]
for label,flags in [('o2',['-O2']),('asan-ubsan',['-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
    exe=out/label;cmd=[args.cc,'-std=c11','-Wall','-Wextra','-Werror',*flags,'-I',str(out),str(out/fixture.name),'-o',str(exe)]
    built=subprocess.run(cmd,capture_output=True,text=True);commands.append({'label':label,'args':cmd,'status':built.returncode,'stdout':built.stdout,'stderr':built.stderr})
    (out/(label+'.compile.log')).write_text(built.stdout+built.stderr)
    if built.returncode: print(built.stderr);raise SystemExit(built.returncode)
    run=subprocess.run([str(exe)],capture_output=True,text=True);commands.append({'label':label+'-run','status':run.returncode,'stdout':run.stdout,'stderr':run.stderr});(out/(label+'.run.log')).write_text(run.stdout+run.stderr);print(label,run.stdout.strip())
    if run.returncode: print(run.stderr);raise SystemExit(run.returncode)
# Targeted source mutants must fail the same actual-source fixture.
mutants={
 'generic-overwrites-console':('actual_graphics.inc','         identify_chip2(SPOOKY, KAVERI);\n','         /* moved below console tests */\n', '         identify_chip2(STARSHP, GLADIUS);','         identify_chip2(STARSHP, GLADIUS);\n         identify_chip2(SPOOKY, KAVERI);'),
 'wrong-raster':('actual_graphics.inc','      raster_config = 0x2a00161a;','      raster_config = 0x00000002;',None,None),
 'rb-clamp-console':('actual_graphics.inc','if (info->family == CHIP_KAVERI)\n      info->max_render_backends = 2;','if (info->family == CHIP_KAVERI || info->family == CHIP_LIVERPOOL)\n      info->max_render_backends = 2;',None,None),
 'wrong-gfx7-boundary':('amd_family.h','   CHIP_BONAIRE,\n   CHIP_LIVERPOOL,\n   CHIP_GLADIUS,','   CHIP_LIVERPOOL,\n   CHIP_GLADIUS,\n   CHIP_BONAIRE,',None,None),
}
mutant_results=[]
for label,(name,old,new,old2,new2) in mutants.items():
    target=out/name;orig=target.read_text()
    if old not in orig:raise SystemExit('mutant anchor absent '+label)
    changed=orig.replace(old,new,1)
    if old2:changed=changed.replace(old2,new2,1)
    target.write_text(changed)
    try:
        exe=out/('mutant-'+label); cmd=[args.cc,'-std=c11','-Wall','-Wextra','-Werror','-O2','-I',str(out),str(out/fixture.name),'-o',str(exe)]
        built=subprocess.run(cmd,capture_output=True,text=True)
        if built.returncode:raise SystemExit('mutant must compile: '+label+'\n'+built.stderr)
        run=subprocess.run([str(exe)],capture_output=True,text=True)
        mutant_results.append({'name':label,'compile_status':built.returncode,'run_status':run.returncode,'stderr':run.stderr})
        if not run.returncode:raise SystemExit('mutant survived '+label)
        print('caught',label)
    finally:target.write_text(orig)
version=subprocess.run([args.cc,'--version'],capture_output=True,text=True).stdout
inputs=[common/'ac_gpu_info.c',common/'amd_family.c',common/'amd_family.h',src/'src/amd/addrlib/src/amdgpu_asic_addr.h',pathlib.Path(__file__),fixture]
receipt={'source':str(src),'upstream':str(up),'compiler':version,'inputs':[{'path':str(x),'sha256':sha(x)} for x in inputs], 'generated':[{'path':x.name,'sha256':sha(x)} for x in [out/'actual_graphics.inc',out/'amdgfxregs.h']], 'runs':commands,'mutants':mutant_results,'boundaries':'Actual whole ac_identify_chip, amd_family.c helpers, GS and raster functions; actual complete cache switch and backend override block. Minimal host struct layouts stand in for query storage only; register macros generated from exact official databases. No real ioctl, GPU execution, installed ABI or presentation testing.'}
(out/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(out/'RESULT.json')
