# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# Locate Streamlit package to bundle its static assets
import streamlit
streamlit_lib_path = os.path.dirname(streamlit.__file__)

block_cipher = None

a = Analysis(
    ['src\\launcher.py'],  # Entry point
    pathex=[],
    binaries=[],
    datas=[
        # Bundle Streamlit's internal static files (frontend)
        (os.path.join(streamlit_lib_path, 'static'), 'streamlit/static'),
        (os.path.join(streamlit_lib_path, 'runtime'), 'streamlit/runtime'),
        
        # Bundle Application Source & Config
        ('src', 'src'),
        ('config', 'config'),
        ('assets', 'assets'),
        ('VERSION_README.txt', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'altair',
        'pydeck',
        'watchdog',
        'win32ctypes', 
        'win32ctypes.core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect metadata for packages that use entry points (like streamlit)
a.datas += copy_metadata('streamlit')
a.datas += copy_metadata('tqdm')
a.datas += copy_metadata('regex')
a.datas += copy_metadata('requests')
a.datas += copy_metadata('packaging')
a.datas += copy_metadata('filelock')
a.datas += copy_metadata('numpy')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Hyper-RMA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Set to False to hide console window, but True is better for debugging initially
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Hyper-RMA',
)
