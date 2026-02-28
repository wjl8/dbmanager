#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite驱动类
"""

import sqlite3
from app.services.database_driver import DatabaseDriver
from typing import Dict, List, Any, Optional


class SQLiteDriver(DatabaseDriver):
    """SQLite驱动类"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """连接数据库
        
        Args:
            connection_params: 连接参数
            
        Returns:
            bool: 连接是否成功
        """
        try:
            db_file = connection_params.get("database", ":memory:")
            self.connection = sqlite3.connect(db_file)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"SQLite连接失败: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            bool: 断开连接是否成功
        """
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            return True
        except Exception as e:
            print(f"SQLite断开连接失败: {str(e)}")
            return False
    
    def execute(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
            
        Returns:
            Any: 执行结果
        """
        if not self.connection:
            raise Exception("未连接数据库")
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # 如果是查询语句，返回结果
            if sql.strip().lower().startswith("select"):
                result = [dict(row) for row in cursor.fetchall()]
                cursor.close()
                return result
            else:
                self.connection.commit()
                rowcount = cursor.rowcount
                cursor.close()
                return rowcount
        except Exception as e:
            self.connection.rollback()
            raise e
    
    def get_tables(self, database: Optional[str] = None) -> List[str]:
        """获取表列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 表名列表
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        result = self.execute(sql)
        tables = [item["name"] for item in result]
        return tables
    
    def get_views(self, database: Optional[str] = None) -> List[str]:
        """获取视图列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 视图名列表
        """
        sql = "SELECT name FROM sqlite_master WHERE type='view'"
        result = self.execute(sql)
        views = [item["name"] for item in result]
        return views
    
    def get_procedures(self, database: Optional[str] = None) -> List[str]:
        """获取存储过程列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 存储过程名列表
        """
        # SQLite不支持存储过程
        return []
    
    def get_table_structure(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表结构
        
        Args:
            table_name: 表名
            database: 数据库名称
            
        Returns:
            List[Dict[str, Any]]: 表结构信息
        """
        sql = f"PRAGMA table_info({table_name})"
        result = self.execute(sql)
        return result
    
    def begin_transaction(self) -> bool:
        """开始事务
        
        Returns:
            bool: 是否成功
        """
        try:
            if self.connection:
                self.connection.execute("BEGIN TRANSACTION")
            return True
        except Exception as e:
            print(f"开始事务失败: {str(e)}")
            return False
    
    def commit(self) -> bool:
        """提交事务
        
        Returns:
            bool: 是否成功
        """
        try:
            if self.connection:
                self.connection.commit()
            return True
        except Exception as e:
            print(f"提交事务失败: {str(e)}")
            return False
    
    def rollback(self) -> bool:
        """回滚事务
        
        Returns:
            bool: 是否成功
        """
        try:
            if self.connection:
                self.connection.rollback()
            return True
        except Exception as e:
            print(f"回滚事务失败: {str(e)}")
            return False
