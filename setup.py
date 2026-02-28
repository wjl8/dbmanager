#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理工具打包配置
"""

from setuptools import setup, find_packages

setup(
    name="dbmanager",
    version="1.0.0",
    description="跨平台数据库管理工具",
    long_description="一个跨平台的数据库管理工具，对标 Navicat Premium 15 的核心功能",
    author="Developer",
    author_email="developer@example.com",
    url="https://github.com/developer/dbmanager",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['resources/**/*'],
    },
    install_requires=[
        'PyQt6==6.6.1',
        'PyQt6-Qt6==6.6.1',
        'PyQt6-sip==13.6.0',
        'SQLAlchemy==2.0.23',
        'pymysql==1.1.0',
        'psycopg2-binary==2.9.9',
        'pyodbc==5.0.1',
        'redis==5.0.1',
        'pymongo==4.5.0',
        'QScintilla==2.14.1',
        'pycryptodome==3.19.0',
        'pyyaml==6.0.1',
        'numpy==1.26.2',
        'pandas==2.1.4',
        'openpyxl==3.1.2',
        'graphviz==0.20.1',
    ],
    entry_points={
        'console_scripts': [
            'dbmanager=main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
