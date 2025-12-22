# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 필요한 데이터 파일들
datas = [
    ('금칙어 수정사항 모음.txt', '.'),
]

# 숨겨진 import들
hiddenimports = [
    'pandas',
    'openpyxl',
    'anthropic',
    're',
    'random',
    'collections',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'tkinter.ttk',
    'threading',
    'search_optimizer',
    'blog_optimizer',
]

a = Analysis(
    ['blog_optimizer_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='블로그SEO최적화',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 모드 (콘솔 창 숨김)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
