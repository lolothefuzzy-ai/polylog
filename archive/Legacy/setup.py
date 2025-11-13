"""
Polylog Installation Script
"""

import os

from setuptools import find_packages, setup

# Read version from code/__init__.py
with open(os.path.join('code', '__init__.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip("'").strip('"')
            break

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Core dependencies required for all installations
CORE_REQUIREMENTS = [
    'numpy>=1.20.0',
    'PyOpenGL>=3.1.0',
    'PyOpenGL-accelerate>=3.1.0',
]

# GUI dependencies - PyQt5 focused since it works with Python 3.13
GUI_REQUIREMENTS = [
    'PyQt5>=5.15.0',
    'PyQt5-Qt5>=5.15.0',
    'PyQt5-sip>=12.13.0',
]

# API server dependencies
API_REQUIREMENTS = [
    'fastapi>=0.70.0',
    'uvicorn>=0.15.0',
    'python-jose[cryptography]>=3.3.0',
    'python-multipart>=0.0.5',
]

# Development dependencies
DEV_REQUIREMENTS = [
    'pytest>=7.0.0',
    'pytest-cov>=3.0.0',
    'black>=22.0.0',
    'flake8>=4.0.0',
    'mypy>=0.900',
    'sphinx>=4.0.0',
]

setup(
    name='polylog',
    version=version,
    description='Interactive Polyform Design & Exploration System',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Polylog Team',
    author_email='team@polylog.dev',
    url='https://github.com/yourusername/polylog',
    
    # Package configuration
    package_dir={'polylog': 'code'},
    packages=find_packages(where='.', exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    
    # Python version requirement
    python_requires='>=3.11',
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'polylog=polylog.main:main',
        ],
    },
    
    # Dependencies
    install_requires=CORE_REQUIREMENTS,
    extras_require={
        'gui': GUI_REQUIREMENTS,
        'api': API_REQUIREMENTS,
        'dev': DEV_REQUIREMENTS,
        'all': GUI_REQUIREMENTS + API_REQUIREMENTS + DEV_REQUIREMENTS,
    },
    
    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
    
    # Keywords for PyPI search
    keywords='polyform,3D,visualization,geometry,simulation',
)