#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库驱动抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class DatabaseDriver(ABC):
    """数据库驱动抽象接口类"""
    
    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """连接数据库
        
        Args:
            connection_params: 连接参数
            
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            bool: 断开连接是否成功
        """
        pass
    
    @abstractmethod
    def execute(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    @abstractmethod
    def get_tables(self, database: Optional[str] = None) -> List[str]:
        """获取表列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 表名列表
        """
        pass
    
    @abstractmethod
    def get_views(self, database: Optional[str] = None) -> List[str]:
        """获取视图列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 视图名列表
        """
        pass
    
    @abstractmethod
    def get_procedures(self, database: Optional[str] = None) -> List[str]:
        """获取存储过程列表
        
        Args:
            database: 数据库名称
            
        Returns:
            List[str]: 存储过程名列表
        """
        pass
    
    @abstractmethod
    def get_table_structure(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表结构
        
        Args:
            table_name: 表名
            database: 数据库名称
            
        Returns:
            List[Dict[str, Any]]: 表结构信息
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> bool:
        """开始事务
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def commit(self) -> bool:
        """提交事务
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def rollback(self) -> bool:
        """回滚事务
        
        Returns:
            bool: 是否成功
        """
        pass
