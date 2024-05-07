from setuptools import setup, Extension

setup(
    name="short",
    version="1.0",
    ext_modules=[Extension("short", ["short.cc"])],
)
