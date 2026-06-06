# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Thu thập toàn bộ dữ liệu, binaries và hiddenimports cho torch và ultralytics
datas_torch, binaries_torch, hidden_torch = collect_all('torch')
datas_ultra, binaries_ultra, hidden_ultra = collect_all('ultralytics')

block_cipher = None

added_files = [
    ('assets', 'assets'),
    ('libs', 'libs'),
    ('widgets', 'widgets'),
    ('dialog', 'dialog'),
    ('gui', 'gui'),
    ('logic', 'logic'),
]

# Gộp tất cả lại
all_datas = added_files + datas_torch + datas_ultra
all_binaries = binaries_torch + binaries_ultra
all_hidden = hidden_torch + hidden_ultra + [
    'libs.edit_lib', 'libs.file_lib', 'libs.help_lib', 'libs.view_lib',
    'widgets.image_canvas', 'dialog.dialog_lib', 'dialog.loading_dialog',
    'dialog.new_label_dialog', 'dialog.select_label_dialog',
    'gui.logger', 'gui.main_window', 'logic.auto_label_logic', 'logic.auto_label_worker'
]

a = Analysis(
    ['TPLabel.py'],
    pathex=['.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test_labelImg.py', 'tplabel.log', '.vscode'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TPLabel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Tạm thời để True để debug xem còn lỗi gì không
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TPLabel_App',
)