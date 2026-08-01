---
name: python-to-cython
description: Accelerates Python hot loops to Cython with MSVC on Windows. Use when user asks "можно ли написать часть кода на языке низкого уровня", "ускорить Python", "Cython", or mentions low-level performance. NOT for simple one-liners or non-hot-path code.
version: 1.0.0
license: MIT
platforms: [windows]
---

# Python to Cython Refactoring

## Instructions

### Step 1: Identify the hot loop
Look for per-tick computations: sensor scans, physics, combat, neighbor lookups. NOT rendering or I/O-bound code.

### Step 2: Set up toolchain (Windows + MSVC)
```powershell
pip install Cython
winget install Microsoft.VisualStudio.2022.BuildTools --add Microsoft.VisualStudio.Workload.VCTools
```
setuptools auto-finds `cl.exe` — no vcvars needed.

### Step 3: Create sim_core.pyx
Extract numeric kernel into typed Cython. Use numpy memoryviews (`double[:]`) for zero-copy arrays. Bake in constants (FIELD_W, FIELD_H, CELL_SIZE) to avoid Python attribute lookups.

### Step 4: Critical MSVC bug to avoid
`rand()` returns 0..`RAND_MAX`(=32767), NOT 2147483647. Always divide by `<double>RAND_MAX`:
```cython
cdef extern from "stdlib.h":
    int rand, RAND_MAX
# ...
angle = rand() / <double>RAND_MAX * 2*M_PI
```

### Step 5: Graceful fallback in pure Python
```python
try:
    from sim_core import simulate_step
    _HAVE_CY = True
except ImportError:
    _HAVE_CY = False
```
Run hot path only if `_HAVE_CY`.

### Step 6: Build
```powershell
# Kill python.exe if it holds the .pyd (access denied)
taskkill /F /IM python.exe 2>NUL
Remove-Item sim_core.cp312-win_amd64.pyd -Force -ErrorAction SilentlyContinue
python setup.py build_ext --inplace
```

### Step 7: Verify speedup
Measure cell-steps/sec before/after. Expect 10-20x on tight loops.

## Troubleshooting

**.pyd "Отказано в доступе"** → python.exe holds the compiled module. Kill and rebuild.

**All cells drift right** → MSVC RAND_MAX bug. Divide by `<double>RAND_MAX`, not 2147483647.0.

**No performance gain** → Bottleneck is NOT in the kernel (check rendering with `SDL_VIDEODRIVER=dummy`).