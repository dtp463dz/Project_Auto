# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

project_dir = SPECPATH
package_datas = []
package_binaries = []
package_hiddenimports = []

for package in ('torch', 'ultralytics'):
    datas, binaries, hiddenimports = collect_all(package)
    package_datas.extend(datas)
    package_binaries.extend(binaries)
    package_hiddenimports.extend(hiddenimports)

package_hiddenimports.extend(collect_submodules('send2trash.win'))

hiddenimports = package_hiddenimports + [
    'libs.edit_lib', 'libs.file_lib', 'libs.help_lib', 'libs.view_lib',
    'widgets.image_canvas', 'dialog.dialog_lib', 'dialog.loading_dialog',
    'dialog.new_label_dialog', 'dialog.select_label_dialog',
    'dialog.auto_label_confirm_dialog', 'dialog.photoshop_dialog',
    'gui.logger', 'gui.main_window', 'gui.theme',
    'logic.auto_label_logic', 'logic.auto_label_logic_v5',
    'logic.auto_label_worker', 'logic.composite_logic',
]

a = Analysis(
    [os.path.join(project_dir, 'TPLabel.py')],
    pathex=[project_dir],
    binaries=package_binaries,
    datas=[
        (os.path.join(project_dir, 'assets'), 'assets'),
        *package_datas,
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test_labelImg.py', 'tplabel.log', '.vscode'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TPLabel',
    icon=os.path.join(project_dir, 'assets', 'eye.ico'),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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