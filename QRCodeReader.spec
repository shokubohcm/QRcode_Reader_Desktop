# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# pyzbarのDLLファイルのパスを取得
pyzbar_path = os.path.join('venv', 'Lib', 'site-packages', 'pyzbar')
dll_files = [
    (os.path.join(pyzbar_path, 'libiconv.dll'), 'pyzbar'),
    (os.path.join(pyzbar_path, 'libzbar-64.dll'), 'pyzbar'),
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=dll_files,  # DLLファイルを追加
    datas=[],
    hiddenimports=['pyzbar.pyzbar'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QRCodeReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
