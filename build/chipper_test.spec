import os
import sys
from platform import architecture as _architecture
from ctypes.util import find_library
import soundfile
from PyInstaller.compat import is_win, is_darwin, is_linux
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, Tree
from PyInstaller.utils.hooks import collect_submodules, get_package_paths
from kivy import garden
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal,\
    hookspath, runtime_hooks

_path = os.path.abspath(os.path.join('..', 'chipper'))

# add chipper folder and kivy garden folders to build folder
datas = [(os.path.dirname(garden.__file__), os.path.join('kivy', 'garden'))]
datas += [(_path, 'chipper')]

# get path of soundfile
sfp = get_package_paths('soundfile')
path = None
if is_win:
    from kivy_deps import sdl2, glew, gstreamer
    import win32timezone
    datas += [(os.path.abspath(win32timezone.__file__), '.'), ]
    path = os.path.join(sfp[0], '_soundfile_data')
elif is_darwin:
    path = os.path.join(sfp[0], '_soundfile_data', 'libsndfile.dylib')

libs = ['sndfile', 'jpeg', 'png', 'SDL2', 'freetype']

if path is not None and os.path.exists(path):
    binaries = [(path, "_soundfile_data")]
else:
    binaries = []


if is_darwin:
    for i in libs:
        if find_library(i) is not None:
            lib_path = find_library(i)
            if os.path.exists(lib_path):
                binaries.append([lib_path, '.'])
elif is_linux:
    binaries = []
    libs = ['sndfile', 'jpeg', 'png', 'SDL2', 'freetype']
    prefix = '/usr/lib/x86_64-linux-gnu'
    for i in libs:
        if find_library(i) is not None:
            lib_path = os.path.join(prefix, find_library(i))
            print(find_library(i), lib_path)
            if os.path.exists(lib_path):
                binaries.append([lib_path, '.'])

# To make the smallest build possible, this code is supposed
# to find the minimal dependencies
kivy_stuff = get_deps_minimal(camera=None, spelling=None, video=None,
                              exclude_ignored=True)
# 'audio', 'camera', 'clipboard', 'image', 'spelling', 'text',
#                  'video', 'window'

# not needed in the app so we exclude them from the build
excludes = [
    'enchant', 'tcl', 'tk', 'PyQT5', 'PyQT4', 'tkinter',
    'cv2', '_tkinter', 'twisted', 'tornado', 'gobject'
]
excludes += kivy_stuff['excludes']

# add missing files that pyinstaller has missed in the past
hiddenimports = kivy_stuff['hiddenimports']

hiddenimports += collect_submodules('encodings')
hiddenimports += ['pywt._extensions._cwt']

# -*- mode: python -*-

block_cipher = None
win_no_prefer_redirects = False
win_private_assemblies = True

a = Analysis([os.path.join(_path, 'run_chipper.py')],
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
exe_name = 'start_chipper'
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=exe_name,
          debug=True,
          strip=False,
          upx=True,
          console=True,
          icon=os.path.join(_path, 'SP1.ico')
          )

if is_win:

    coll = COLLECT(exe,
                   Tree(_path),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   *[Tree(p) for p in
                     (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],
                   strip=False,
                   upx=True,
                   name=exe_name)

else:
    coll = COLLECT(exe,
                   Tree(_path),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name=exe_name)
