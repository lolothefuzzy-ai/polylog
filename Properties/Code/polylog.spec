# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Polylog Desktop Application
Build command: pyinstaller polylog.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Collect all data files
datas = [
    ('data/scalers.json', 'data'),
    ('data/symmetries.json', 'data'),
]

# Hidden imports for dependencies that PyInstaller might miss
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'pyqtgraph.opengl',
    'pyqtgraph.opengl.GLViewWidget',
    'pyqtgraph.opengl.GLGridItem',
    'pyqtgraph.opengl.GLLinePlotItem',
    'pyqtgraph.opengl.GLMeshItem',
    'numpy',
    'numpy.core',
    'numpy.core.multiarray',
    'fastapi',
    'uvicorn',
    'pydantic',
    'pydantic.types',
    'pydantic_core',
    'psutil',
    # Project modules
    'automated_placement_engine',
    'continuous_exploration_engine',
    'managers',
    'stable_library',
    'polyform_library',
    'canonical_estimator',
    'polygon_utils',
    'interaction_manager',
    'constraint_solver',
    'hinge_slider_ui',
    'polygon_range_slider',
    'theme_manager',
    'hinge_manager',
    'collision_validator',
    'physics_simulator',
    'bvh3d',
    # Performance monitoring modules
    'performance_monitor',
    'performance_integration',
    'visual_tracking',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude if not used
        'PIL',
        'tkinter',
    ],
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
    name='Polylog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI-only, True for console + GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: icon='polylog.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Polylog',
)
