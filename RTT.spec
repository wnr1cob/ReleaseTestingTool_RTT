# PyInstaller spec file for Release Testing Tool
# 
# Build with:  pyinstaller RTT.spec

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=collect_dynamic_libs('cryptography'),
    datas=[
        ('config', 'config'),
        ('resources', 'resources'),
        ('docs', 'docs'),
    ] + collect_data_files('cryptography'),
    hiddenimports=[
        'cryptography',
        'cryptography.hazmat.bindings._rust',
        'cryptography.hazmat.primitives.ciphers.base',
    ] + collect_submodules('cryptography') + collect_submodules('pdfminer') + collect_submodules('pdfplumber'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='ReleaseTestingTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    onedir=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
