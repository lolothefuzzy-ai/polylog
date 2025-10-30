# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller OPTIMIZED spec file for Polylog Desktop Application
Build command: pyinstaller polylog-optimized.spec

OPTIMIZATIONS:
- Excludes scipy/optuna (API-only features, saves ~100MB)
- Excludes unused Qt modules (saves ~20MB)
- Optimized OpenGL imports (saves ~10MB)
- Total savings: ~130MB (300-400MB → 200-270MB)
"""

import sys
from pathlib import Path

block_cipher = None

# Collect only essential data files
datas = [
    ('data/scalers.json', 'data'),
    ('data/symmetries.json', 'data'),
]

# OPTIMIZED: Hidden imports - only GUI essentials
hiddenimports = [
    # PySide6 - Core Qt modules only
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    
    # PyQtGraph OpenGL
    'pyqtgraph',
    'pyqtgraph.opengl',
    'pyqtgraph.opengl.GLViewWidget',
    'pyqtgraph.opengl.GLGridItem',
    'pyqtgraph.opengl.GLLinePlotItem',
    'pyqtgraph.opengl.GLMeshItem',
    'pyqtgraph.opengl.shaders',
    
    # NumPy - core only
    'numpy',
    'numpy.core',
    'numpy.core.multiarray',
    
    # System monitoring
    'psutil',
    
    # Essential project modules (GUI-focused)
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

# OPTIMIZED: Aggressive exclusions
excludes = [
    # Heavy scientific packages (API-only features)
    'scipy',
    'scipy.optimize',
    'optuna',
    
    # FastAPI/Uvicorn (API mode not needed for standalone)
    'fastapi',
    'uvicorn',
    'starlette',
    'pydantic',
    
    # Unused visualization
    'matplotlib',
    'PIL',
    'pillow',
    
    # Unused UI frameworks
    'tkinter',
    'wx',
    'PyQt5',
    'PyQt6',
    
    # Unused Qt modules
    'PySide6.QtNetwork',
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtMultimedia',
    'PySide6.QtSql',
    'PySide6.QtTest',
    'PySide6.QtXml',
    
    # Development tools
    'pytest',
    'unittest',
    'doctest',
    'pdb',
    'ipython',
    'jupyter',
    
    # Build tools
    'setuptools',
    'pip',
    'wheel',
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
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out debug/test files
a.datas = [x for x in a.datas if not x[0].startswith('test')]
a.binaries = [x for x in a.binaries if not any(excl in x[0].lower() for excl in ['test', 'debug'])]

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
    upx=True,  # Enable UPX compression
    console=False,  # GUI-only (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon: icon='polylog.ico'
    version_file=None,  # Add version: version_file='version.txt'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,  # Compress DLLs
    upx_exclude=[
        'vcruntime140.dll',  # Don't compress system DLLs
        'python*.dll',
    ],
    name='Polylog',
)
