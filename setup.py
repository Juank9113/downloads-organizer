"""
Configuración del paquete Downloads Organizer
Autor: Juan Carlos Blanco Ruiz
Email: juancarlosblancoruiz@gmail.com
"""
import os
from setuptools import setup, find_packages

# Leer README.md de forma segura (si no existe, usa descripción por defecto)
this_directory = os.path.abspath(os.path.dirname(__file__))
long_description = "Organizador automático de archivos para la carpeta de Descargas"

readme_path = os.path.join(this_directory, "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="downloads-organizer",
    version="1.0.0",
    author="Juan Carlos Blanco Ruiz",
    author_email="juancarlosblancoruiz@gmail.com",
    description="Organizador automático de archivos para la carpeta de Descargas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Juank9113/downloads-organizer",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "organize-downloads=organizer:main",
        ],
    },
)