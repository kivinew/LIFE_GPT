#!/usr/bin/env python3
"""Set up, compile, and run the Cython sim_core module."""
import sys
import os

# Ensure project dir is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Build Cython
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

ext = Extension("sim_core", sources=["sim_core.pyx"],
                include_dirs=[np.get_include()])

setup(
    name="sim_core",
    script_args=["build_ext", "--inplace"],
    ext_modules=cythonize([ext], language_level="3"),
)

# After build, run main
os.execvp(sys.executable, [sys.executable, "main.py"] + sys.argv[1:])