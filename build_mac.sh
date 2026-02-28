#!/bin/bash

# 打包数据库管理工具为Mac可执行文件

echo "开始打包数据库管理工具..."

# 安装PyInstaller
pip install pyinstaller

# 执行打包命令
pyinstaller --name dbmanager --onefile --windowed --icon=resources/icons/app_icon.png --add-data "resources:resources" main.py

echo "打包完成！"
echo "可执行文件位于 dist 目录中"
