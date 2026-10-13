"""Build pinned approved FCEUmm; stage only the sanitized mapper2 STB ROM."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'.sources/fceumm';revision='ac0d00a7fc01166f84c7bac01d1084ebfd2b865e'
if not source.exists():subprocess.run(['git','clone','https://github.com/libretro/libretro-fceumm',str(source)],check=True)
changes=subprocess.check_output(['git','-C',str(source),'status','--porcelain'],text=True).splitlines()
if any(s not in ('?? obj/','?? libs/') for s in changes):raise SystemExit('Preserve changed FCEUmm tree.')
subprocess.run(['git','-C',str(source),'checkout','--detach',revision],check=True)
subprocess.run([str(Path(os.environ['ANDROID_NDK_ROOT'])/'ndk-build'),'NDK_PROJECT_PATH='+str(source),'APP_BUILD_SCRIPT='+str(source/'jni/Android.mk'),'APP_ABI=arm64-v8a','APP_PLATFORM=android-23','-j6'],cwd=source,check=True)
rom=ROOT/'.sources/super-tilt-bro/tilt_no_network_unrom_(E).nes'
if hashlib.sha256(rom.read_bytes()).hexdigest()!='b03e0166e565ce24019386fd9ee560d3b8b1c8310e17e63912b173cbdb635106':
    raise SystemExit('STB ROM differs from verified sanitized build; no content staged.')
engine=ROOT/'.sources/retroarch/pkg/android'
shutil.copy2(source/'libs/arm64-v8a/libretro.so',engine/'phoenix-common/libs/arm64-v8a/libfceumm_libretro_android.so')
shutil.copy2(rom,engine/'phoenix/assets/joyorbit/stb.nes')
(ROOT/'theme/licenses/FCEUmm-GPL2.txt').write_text((source/'Copying').read_text()+'\nIncluded NTSC filter notice:\n'+(source/'src/ntsc/license.txt').read_text())
print('FCEUmm and sanitized STB staged; embed the engine.')
