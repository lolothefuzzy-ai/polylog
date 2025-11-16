#!/usr/bin/env python3
"""
Build FastAPI backend as single executable for Tauri sidecar
"""
import PyInstaller.__main__
import platform
import sys
from pathlib import Path

# Determine platform-specific executable name
system = platform.system()
if system == "Windows":
    exe_name = "polyform-backend.exe"
elif system == "Darwin":
    arch = platform.machine()
    exe_name = f"polyform-backend-{arch}-apple-darwin"
else:  # Linux
    exe_name = "polyform-backend-x86_64-unknown-linux-gnu"

# Get paths
project_root = Path(__file__).parent
backend_entry = project_root / "src" / "polylog6" / "api" / "main.py"
output_dir = project_root / "src-tauri" / "binaries"

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)

# PyInstaller arguments
PyInstaller.__main__.run([
    str(backend_entry),
    '--name', exe_name.replace('.exe', ''),
    '--onefile',  # Single executable
    '--distpath', str(output_dir),
    '--workpath', str(project_root / 'build' / 'work'),
    '--specpath', str(project_root / 'build'),
    '--noconfirm',
    '--clean',
    # Include hidden imports
    '--hidden-import', 'uvicorn.logging',
    '--hidden-import', 'uvicorn.loops',
    '--hidden-import', 'uvicorn.loops.auto',
    '--hidden-import', 'uvicorn.protocols',
    '--hidden-import', 'uvicorn.protocols.http',
    '--hidden-import', 'uvicorn.protocols.http.auto',
    '--hidden-import', 'uvicorn.protocols.websockets',
    '--hidden-import', 'uvicorn.protocols.websockets.auto',
    '--hidden-import', 'uvicorn.lifespan',
    '--hidden-import', 'uvicorn.lifespan.on',
])

print(f"\n✅ Sidecar executable built: {output_dir / exe_name}")
