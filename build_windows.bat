@echo off

rem 打包数据库管理工具为Windows可执行文件

echo 开始打包数据库管理工具...

rem 安装PyInstaller
pip install pyinstaller

rem 执行打包命令
pyinstaller --name dbmanager --onefile --windowed --icon=resources/icons/app_icon.png --add-data "resources;resources" main.py

echo 打包完成！
echo 可执行文件位于 dist 目录中

pause
