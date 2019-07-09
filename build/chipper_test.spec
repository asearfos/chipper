import os
import sys
from platform import architecture as _architecture
from ctypes.util import find_library
import soundfile
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, Tree
from PyInstaller.utils.hooks import collect_submodules
from kivy import garden
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal,\
    hookspath, runtime_hooks


if sys.platform == 'darwin':
    OS = 'MAC'
    _libname = 'libsndfile.dylib'
elif sys.platform == 'win32':
    OS = 'WINDOWS'
    _libname = 'libsndfile' + _architecture()[0] + '.dll'

    import win32timezone
    from kivy.deps import sdl2, glew

else:
    OS = 'LINUX'
    _libname = find_library('sndfile')

_path = os.path.abspath(os.path.join('..', 'chipper'))

kivy_stuff = get_deps_minimal(camera=None, spelling=None, video=None)
# 'audio', 'camera', 'clipboard', 'image', 'spelling', 'text',
#                  'video', 'window'
excludes = [
    'enchant', 'tcl', 'tk', 'PyQT5', 'PyQT4', 'tkinter',
    'cv2',
    '_tkinter', 'twisted',
    'tornado', 'gobject'
]
excludes += kivy_stuff['excludes']
excludes += ['chipper.synthetic_songs', 'chipper.tests']

hiddenimports = kivy_stuff['hiddenimports']

hiddenimports += collect_submodules('encodings')
hiddenimports += ['pywt._extensions._cwt']
sound_path = os.path.join(
    os.path.dirname(os.path.abspath(soundfile.__file__)),
    '_soundfile_data', _libname
)

# -*- mode: python -*-

block_cipher = None
win_no_prefer_redirects = False
win_private_assemblies = False

datas = [(os.path.dirname(garden.__file__), os.path.join('kivy', 'garden'))]
datas += [(_path, 'chipper')]


if OS == 'WINDOWS':
    datas += [(os.path.abspath(win32timezone.__file__), '.'), ]
    binaries = [(sound_path, '_soundfile_data')]
elif OS == 'MAC':
    binaries = [
        (sound_path, '_soundfile_data'),
        ('/usr/local/lib/libpng16.16.dylib', '.'),
        ('/usr/local/lib/libjpeg.9.dylib', '.'),
        ('/usr/local/lib/libSDL2.dylib', '.'),
        ('/usr/local/lib/libfreetype.6.dylib', '.')
    ]
else:
    binaries = [
        ('/usr/lib/libsndfile.so', '_soundfile_data'),
        ('/usr/lib/libpng16.so', '.'),
        ('/usr/lib/libjpeg.so', '.'),
        ('/usr/lib/libSDL2.dylib', '.'),
        ('/usr/lib/libfreetype.so', '.')

    ]

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

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='chipper_test',
          debug=True,
          strip=False,
          upx=True,
          console=True,
          icon=os.path.join(_path, 'SP1.ico')
          )

if OS == 'WINDOWS':
    coll = COLLECT(exe,
                   Tree(_path),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
                   strip=False,
                   upx=True,
                   name='chipper_test')

else:
    coll = COLLECT(exe,
                   Tree(_path),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='chipper_test')
