#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
驱动工厂类
"""

from app.services.database_driver import DatabaseDriver
from app.services.mysql_driver import MySQLDriver
from app.services.sqlite_driver import SQLiteDriver


class DriverFactory:
    """驱动工厂类"""
    
    @staticmethod
    def create_driver(db_type):
        """创建驱动实例
        
        Args:
            db_type: 数据库类型
            
        Returns:
            DatabaseDriver: 数据库驱动实例
        """
        if db_type == "mysql":
            return MySQLDriver()
        elif db_type == "sqlite":
            return SQLiteDriver()
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
