#!/usr/bin/env python3
"""Build the sim_core Cython extension only."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

ext = Extension(
    "sim_core",
    sources=["sim_core.pyx"],
    include_dirs=[np.get_include()],
)

setup(
    name="sim_core",
    py_modules=[],
    packages=[],
    ext_modules=cythonize([ext], language_level="3"),
)