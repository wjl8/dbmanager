#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理工具主入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from app.views.main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
