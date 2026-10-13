"""Build only the sanitized, no-network Super Tilt Bro 2.6 ROM on an ARM Mac.
Prerequisites: clang/make, Homebrew cc65/gmp/mpfr/libmpc, Python with Pillow.
Generated source trees must be fresh; changed trees are never reset.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import PIL.Image
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'.sources'
def run(args,cwd=None,env=None):subprocess.run(args,cwd=cwd,env=env,check=True)
def source(name,repo,revision):
    p=SOURCES/name
    if p.exists():raise SystemExit('Preserve '+str(p)+'; use a fresh build checkout.')
    p.mkdir(parents=True)
    run(['git','init',str(p)]);run(['git','-C',str(p),'remote','add','origin','https://github.com/'+repo])
    run(['git','-C',str(p),'fetch','--depth','1','origin',revision])
    run(['git','-C',str(p),'checkout','--detach','FETCH_HEAD'])
    return p
stb=source('super-tilt-bro','sgadrat/super-tilt-bro','a0b25e56ec8bde7bea623573b76343fdd3d584bc')
xa=source('xa65-stb','sgadrat/xa65-stb','a75f76dc9aee5b892facecb0436725d368f41102')
huff=source('huffmunch','bbbradsmith/huffmunch','dfc0804925f6a3a0309440ec5531e966ef8d7f2c')
gcc=source('gcc-6502-bits','itszor/gcc-6502-bits','15b26ddf7863e8a5d17678c6c11bac9cbe353138')
# Avoid downloading all GCC history while preserving the exact submodule source.
gcc_source=gcc/'gcc-src';gcc_source.mkdir(exist_ok=True)
run(['git','init',str(gcc_source)]);run(['git','-C',str(gcc_source),'remote','add','origin','https://github.com/itszor/gcc-6502'])
run(['git','-C',str(gcc_source),'fetch','--depth','1','origin','e3328194b187d5d5e6800f0320c8066a027d2462'])
run(['git','-C',str(gcc_source),'checkout','--detach','FETCH_HEAD'])
p=gcc_source/'zlib/zutil.h';p.write_text(p.read_text().replace('#if defined(MACOS) || defined(TARGET_OS_MAC)','#if (defined(MACOS) || defined(TARGET_OS_MAC)) && !defined(__APPLE__)'))
build=gcc/'gcc-build';build.mkdir()
run([str(gcc_source/'configure'),'--prefix='+str(gcc/'prefix'),'--target=6502','--enable-languages=c','--with-as=/opt/homebrew/bin/ca65','--with-ld=/opt/homebrew/bin/ld65','--without-headers','--with-newlib','--disable-nls','--disable-decimal-float','--disable-libssp','--disable-threads','--disable-libatomic','--disable-libitm','--disable-libsanitizer','--disable-libquadmath','--disable-lto','--disable-bootstrap','--disable-werror','--without-isl','--with-gmp=/opt/homebrew/opt/gmp','--with-mpfr=/opt/homebrew/opt/mpfr','--with-mpc=/opt/homebrew/opt/libmpc'],cwd=build)
# Build compiler prerequisites, then cc1/xgcc without the unused gcov utilities.
run(['make','-j6','all-build-libiberty','all-build-libcpp','all-libiberty','all-libcpp','all-libdecnumber','all-libbacktrace','all-zlib','configure-gcc','CFLAGS=-O2 -std=gnu11','CXXFLAGS=-O2 -std=gnu++11'],cwd=build)
run(['make','-C','gcc','-j6','cc1','xgcc','host_hook_obj=host-default.o','CFLAGS=-O2 -std=gnu11','CXXFLAGS=-O2 -std=gnu++11'],cwd=build)
run(['make','-j6'],cwd=xa/'xa')
p=huff/'huffmunch.cpp';p.write_text(p.read_text().replace('Fixup f = { output.size(), suffix };','Fixup f = { static_cast<uint>(output.size()), suffix };'))
run(['make','-j6','CPPFLAGS=-std=c++11'],cwd=huff)
bin=ROOT/'build/retro-tools/bin';bin.mkdir(parents=True,exist_ok=True)
cc=bin/'6502-gcc';cc.write_text('#!/bin/sh\nexec "'+str(build/'gcc/xgcc')+'" -B "'+str(build/'gcc')+'/" -I "'+str(gcc/'libtinyc/include')+'" -isystem "'+str(gcc_source/'gcc/ginclude')+'" "$@"\n');cc.chmod(0o755)
python=bin/'python';python.write_text('#!/bin/sh\nexec "'+sys.executable+'" "$@"\n');python.chmod(0o755)
p=stb/'build.sh';p.write_text(p.read_text().replace('root_dir=`readlink -f $(dirname "$0")`','root_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)').replace('\t\tpython -c','\t\tpython3 -c'))
# No licence grant is stated for A Sagely Concerto in the pinned source.
# Remove its compiled bytes and use the explicitly CC BY 4.0 Fusolis instead.
(stb/'game/data/music/theme_sagely_concerto.asm').write_text('+music_sagely_concerto_bank = music_fusolis_bank\n+music_sagely_concerto_info = music_fusolis_info\n')
p=stb/'game/logic/game_states/jukebox_screen/jukebox_screen_extra_logic.asm';p.write_text(p.read_text().replace('A Sagely Concerto ','Fusolis Reprise   '))
env=dict(os.environ,PATH=str(bin)+':'+os.environ['PATH'],XA_BIN=str(xa/'xa/xa'),CC_BIN=str(cc),HUFFMUNCH_BIN=str(huff/'huffmunch'),SKIP_RESCUE_IMG='2')
run(['bash','build.sh'],cwd=stb,env=env)
rom=stb/'tilt_no_network_unrom_(E).nes';data=rom.read_bytes()
if data[:4]!=b'NES\x1a' or (data[6]>>4 | data[7]&240)!=2:raise SystemExit('Wrong mapper; no ROM staged.')
engine=ROOT/'.sources/retroarch/pkg/android'
shutil.copy2(rom,engine/'phoenix/assets/joyorbit/stb.nes')
print('Sanitized mapper2 no-network ROM staged. Build FCEUmm then embed the engine.')
