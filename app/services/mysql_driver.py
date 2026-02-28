#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL驱动类
"""

import pymysql
from app.services.database_driver import DatabaseDriver
from typing import Dict, List, Any, Optional


class MySQLDriver(DatabaseDriver):
    """MySQL驱动类"""
    
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
            self.connection = pymysql.connect(
                host=connection_params.get("host", "localhost"),
                port=int(connection_params.get("port", 3306)),
                user=connection_params.get("username", "root"),
                password=connection_params.get("password", ""),
                database=connection_params.get("database", ""),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"MySQL连接失败: {str(e)}")
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
            print(f"MySQL断开连接失败: {str(e)}")
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
            with self.connection.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # 如果是查询语句，返回结果
                sql_lower = sql.strip().lower()
                if sql_lower.startswith("select") or sql_lower.startswith("show"):
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return cursor.rowcount
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
        if database:
            sql = f"SHOW TABLES FROM `{database}`"
        else:
            sql = "SHOW TABLES"
        
        result = self.execute(sql)
        tables = [list(item.values())[0] for item in result]
        return tables
    
    def get_views(self, database: Optional[str] = None) -> List[str]:
        """获取视图列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 视图名列表
        """
        if database:
            sql = f"SHOW VIEWS FROM `{database}`"
        else:
            sql = "SHOW VIEWS"
        
        result = self.execute(sql)
        views = [list(item.values())[0] for item in result]
        return views
    
    def get_procedures(self, database: Optional[str] = None) -> List[str]:
        """获取存储过程列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 存储过程名列表
        """
        if database:
            sql = f"SHOW PROCEDURE STATUS WHERE Db = '{database}'"
        else:
            sql = "SHOW PROCEDURE STATUS"
        
        result = self.execute(sql)
        procedures = [item["Name"] for item in result]
        return procedures
    
    def get_table_structure(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表结构
        
        Args:
            table_name: 表名
            database: 数据库名称
            
        Returns:
            List[Dict[str, Any]]: 表结构信息
        """
        if database:
            sql = f"DESCRIBE `{database}`.`{table_name}`"
        else:
            sql = f"DESCRIBE `{table_name}`"
        
        result = self.execute(sql)
        return result
    
    def begin_transaction(self) -> bool:
        """开始事务
        
        Returns:
            bool: 是否成功
        """
        try:
            if self.connection:
                self.connection.begin()
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
    
    def get_databases(self) -> List[str]:
        """获取数据库列表
        
        Returns:
            List[str]: 数据库名列表
        """
        sql = "SHOW DATABASES"
        result = self.execute(sql)
        databases = [list(item.values())[0] for item in result]
        return databases
