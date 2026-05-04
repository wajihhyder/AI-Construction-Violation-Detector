# -*- mode: python ; coding: utf-8 -*-
# PyInstaller — single-folder output (see scripts/build_exe.ps1)

import sys
from pathlib import Path

backend_dir = Path(SPEC).resolve().parent


def _win_runtime_binaries():
    """
    Conda/Anaconda puts OpenSSL and other native deps in Library\\bin. PyInstaller
    does not always follow these, so import ssl / sqlite / ctypes fails at runtime
    with DLL load failed — bundle them explicitly.
    """
    if sys.platform != "win32":
        return []
    base = Path(sys.base_prefix)
    dirs = [base / "Library" / "bin", base / "DLLs"]
    names = [
        "libssl-3-x64.dll",
        "libcrypto-3-x64.dll",
        "libssl-1_1-x64.dll",
        "libcrypto-1_1-x64.dll",
        "libexpat.dll",
        "sqlite3.dll",
        "ffi.dll",
        "libffi-8.dll",
        "libffi-7.dll",
    ]
    out = []
    seen = set()
    for d in dirs:
        if not d.is_dir():
            continue
        for name in names:
            key = name.lower()
            if key in seen:
                continue
            p = d / name
            if p.is_file():
                out.append((str(p), "."))
                seen.add(key)
    return out


project_root = backend_dir.parent
dist_frontend = project_root / "frontend" / "dist"

block_cipher = None

datas = []
templates_dir = backend_dir / "templates"
if templates_dir.is_dir():
    datas.append((str(templates_dir), "templates"))
if dist_frontend.is_dir() and (dist_frontend / "index.html").exists():
    datas.append((str(dist_frontend), "dist"))

a = Analysis(
    [str(backend_dir / "run_desktop.py")],
    pathex=[str(backend_dir)],
    binaries=_win_runtime_binaries(),
    datas=datas,
    hiddenimports=[
        "main",
        "database",
        "models",
        "models.user",
        "models.report",
        "models.ai_result",
        "routers",
        "routers.auth",
        "routers.citizen",
        "routers.authority",
        "routers.admin",
        "routers.geocoding",
        "core.config",
        "core.security",
        "core.dependencies",
        "core.limiter",
        "core.districts",
        "services.auth_service",
        "services.image_service",
        "services.geocoding_service",
        "services.ai_service",
        "services.rule_engine",
        "services.notice_context",
        "jinja2",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "passlib.handlers.bcrypt",
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ConstructionViolationDetection",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    upx=False,
    name="ConstructionViolationDetection",
)
