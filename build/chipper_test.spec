import os
import sys
from platform import architecture as _architecture

import soundfile
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, Tree
from PyInstaller.utils.hooks import collect_submodules
from kivy import garden
from kivy.deps import sdl2, glew
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, \
    runtime_hooks

if sys.platform == 'darwin':
    OS = 'MAC'
    _libname = 'libsndfile.dylib'
elif sys.platform == 'win32':
    OS = 'WINDOWS'
    _libname = 'libsndfile' + _architecture()[0] + '.dll'
    import win32timezone
else:
    print("Not MAC or WINDOWS")
    quit()

kivy_stuff = get_deps_minimal(camera=False, spelling=False, video=False)

excludes = ['enchant', 'tcl', 'tk', 'PyQT5', 'cv2', 'tkinter', '_tkinter',
            'twisted', 'kivy.lib.gstplayer',
            'tornado', 'gobject']
excludes += kivy_stuff['excludes']

hiddenimports = kivy_stuff['hiddenimports']

hiddenimports += collect_submodules('encodings')

sound_path = os.path.join(
    os.path.dirname(os.path.abspath(soundfile.__file__)),
    '_soundfile_data', _libname
)

# -*- mode: python -*-

block_cipher = None
win_no_prefer_redirects = False
win_private_assemblies = False
binaries = [
    (sound_path, '_soundfile_data')
]

datas = [
    (os.path.dirname(garden.__file__), 'kivy\\garden'),
]
if OS == 'WINDOWS':
    datas += [(os.path.abspath(win32timezone.__file__), '.'), ]

for i, d in dict(pathex=['.'],
                 binaries=binaries,
                 excludes=excludes,
                 datas=datas,
                 hookspath=hookspath(),
                 runtime_hooks=runtime_hooks(),
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 hiddenimports=hiddenimports).items():
    print(i, d)

a = Analysis(['..\\chipper\\run_chipper.py'],
             pathex=['.'],
             binaries=binaries,
             excludes=excludes,
             datas=datas,
             hookspath=hookspath(),
             runtime_hooks=runtime_hooks(),
             win_no_prefer_redirects=win_no_prefer_redirects,
             win_private_assemblies=win_private_assemblies,
             cipher=block_cipher,
             hiddenimports=hiddenimports
             )

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='chipper_test',
          debug=True,
          strip=False,
          upx=True,
          console=True,
          icon='..\\chipper\\SP1.ico'
          )

coll = COLLECT(exe,
               Tree('..\\chipper'),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='chipper_test')
