#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接树组件
"""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog,
    QMessageBox, QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import json
import os
from app.services.driver_factory import DriverFactory


class ConnectionTreeWidget(QTreeWidget):
    """连接树组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("数据库连接")
        self._init_ui()
        self._load_connections()
    
    def _init_ui(self):
        """初始化UI"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 连接双击事件
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 根节点
        self.root = QTreeWidgetItem(self, ["连接"])
        self.root.setExpanded(True)
    
    def _on_item_double_clicked(self, item, column):
        """处理双击事件"""
        # 检查是否是数据表项（父节点是数据库项）
        if item.parent() and item.parent().parent():
            # 获取连接项
            connection_item = item.parent().parent()
            connection_info = connection_item.data(0, Qt.ItemDataRole.UserRole)
            
            if connection_info:
                # 获取数据库名和表名
                database_name = item.parent().text(0)
                table_name = item.text(0)
                
                # 发送信号给主窗口
                if hasattr(self, 'on_table_double_clicked'):
                    self.on_table_double_clicked(connection_info, database_name, table_name)
    
    def _show_context_menu(self, position):
        """显示上下文菜单"""
        menu = QMenu()
        
        # 新建连接
        new_connection_action = QAction("新建连接", self)
        new_connection_action.triggered.connect(self._new_connection)
        menu.addAction(new_connection_action)
        
        # 获取选中的项
        selected_items = self.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            
            # 如果选中的是连接项
            if selected_item.parent() == self.root:
                # 测试连接
                test_connection_action = QAction("测试连接", self)
                test_connection_action.triggered.connect(lambda: self._test_connection(selected_item))
                menu.addAction(test_connection_action)
                
                # 打开数据库
                open_connection_action = QAction("打开数据库", self)
                open_connection_action.triggered.connect(lambda: self._open_connection(selected_item))
                menu.addAction(open_connection_action)
                
                # 删除连接
                delete_connection_action = QAction("删除连接", self)
                delete_connection_action.triggered.connect(lambda: self._delete_connection(selected_item))
                menu.addAction(delete_connection_action)
            # 如果选中的是数据库项
            elif selected_item.parent() and selected_item.parent().parent() == self.root:
                # 打开SQL编辑器
                open_sql_editor_action = QAction("打开SQL编辑器", self)
                open_sql_editor_action.triggered.connect(lambda: self._open_sql_editor(selected_item))
                menu.addAction(open_sql_editor_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def _new_connection(self):
        """新建连接"""
        dialog = ConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            connection_info = dialog.get_connection_info()
            self._add_connection(connection_info)
            self._save_connections()
    
    def _test_connection(self, item):
        """测试连接"""
        connection_info = item.data(0, Qt.ItemDataRole.UserRole)
        if not connection_info:
            QMessageBox.warning(self, "错误", "连接信息不存在")
            return
        
        try:
            driver = DriverFactory.create_driver(connection_info["type"])
            success = driver.connect(connection_info)
            if success:
                QMessageBox.information(self, "成功", "连接测试成功")
                driver.disconnect()
            else:
                QMessageBox.warning(self, "失败", "连接测试失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接测试失败: {str(e)}")
    
    def _open_connection(self, item):
        """打开连接"""
        connection_info = item.data(0, Qt.ItemDataRole.UserRole)
        if not connection_info:
            QMessageBox.warning(self, "错误", "连接信息不存在")
            return
        
        try:
            driver = DriverFactory.create_driver(connection_info["type"])
            success = driver.connect(connection_info)
            if success:
                # 清空子节点
                while item.childCount() > 0:
                    item.removeChild(item.child(0))
                
                # 加载数据库
                if connection_info["type"] == "mysql":
                    databases = driver.get_databases()
                    for db in databases:
                        db_item = QTreeWidgetItem(item, [db])
                        # 加载表
                        tables = driver.get_tables(db)
                        for table in tables:
                            QTreeWidgetItem(db_item, [table])
                elif connection_info["type"] == "sqlite":
                    # SQLite只有一个数据库
                    db_item = QTreeWidgetItem(item, ["main"])
                    tables = driver.get_tables()
                    for table in tables:
                        QTreeWidgetItem(db_item, [table])
                
                item.setExpanded(True)
                QMessageBox.information(self, "成功", "连接已打开")
                driver.disconnect()
            else:
                QMessageBox.warning(self, "失败", "连接失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
    
    def _delete_connection(self, item):
        """删除连接"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除这个连接吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.root.removeChild(item)
            self._save_connections()
    
    def _open_sql_editor(self, item):
        """打开SQL编辑器"""
        # 获取连接项（数据库项的父项）
        connection_item = item.parent()
        if not connection_item:
            QMessageBox.warning(self, "错误", "连接信息不存在")
            return
        
        # 获取连接信息
        connection_info = connection_item.data(0, Qt.ItemDataRole.UserRole)
        if not connection_info:
            QMessageBox.warning(self, "错误", "连接信息不存在")
            return
        
        # 添加数据库名到连接信息
        connection_info_copy = connection_info.copy()
        connection_info_copy["database"] = item.text(0)
        
        # 发送信号给主窗口
        if hasattr(self, 'on_open_sql_editor'):
            self.on_open_sql_editor(connection_info_copy)
    
    def _add_connection(self, connection_info):
        """添加连接"""
        item = QTreeWidgetItem(self.root, [connection_info["name"]])
        item.setData(0, Qt.ItemDataRole.UserRole, connection_info)
        self.root.setExpanded(True)
    
    def _load_connections(self):
        """加载连接"""
        connections_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "connections.json")
        if os.path.exists(connections_file):
            try:
                with open(connections_file, "r", encoding="utf-8") as f:
                    connections = json.load(f)
                    for connection_info in connections:
                        self._add_connection(connection_info)
            except Exception as e:
                print(f"加载连接失败: {str(e)}")
    
    def _save_connections(self):
        """保存连接"""
        connections = []
        for i in range(self.root.childCount()):
            item = self.root.child(i)
            connection_info = item.data(0, Qt.ItemDataRole.UserRole)
            if connection_info:
                connections.append(connection_info)
        
        connections_file = os.path.join(os.path.dirname(__file__), "..", "..", "config", "connections.json")
        os.makedirs(os.path.dirname(connections_file), exist_ok=True)
        
        try:
            with open(connections_file, "w", encoding="utf-8") as f:
                json.dump(connections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存连接失败: {str(e)}")


class ConnectionDialog(QDialog):
    """新建连接对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建连接")
        self.setGeometry(300, 300, 400, 300)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # 连接名称
        self.name_edit = QLineEdit()
        form_layout.addRow("连接名称:", self.name_edit)
        
        # 数据库类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MySQL", "SQLite"])
        form_layout.addRow("数据库类型:", self.type_combo)
        
        # 主机
        self.host_edit = QLineEdit("localhost")
        form_layout.addRow("主机:", self.host_edit)
        
        # 端口
        self.port_edit = QLineEdit("3306")
        form_layout.addRow("端口:", self.port_edit)
        
        # 用户名
        self.username_edit = QLineEdit("root")
        form_layout.addRow("用户名:", self.username_edit)
        
        # 密码
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("密码:", self.password_edit)
        
        # 数据库名/SQLite文件
        self.database_edit = QLineEdit()
        form_layout.addRow("数据库名:", self.database_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QVBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 类型变化时的处理
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed("MySQL")
    
    def _on_type_changed(self, db_type):
        """类型变化时的处理"""
        if db_type == "SQLite":
            self.host_edit.setEnabled(False)
            self.port_edit.setEnabled(False)
            self.username_edit.setEnabled(False)
            self.password_edit.setEnabled(False)
            self.database_edit.setPlaceholderText("SQLite文件路径")
        else:
            self.host_edit.setEnabled(True)
            self.port_edit.setEnabled(True)
            self.username_edit.setEnabled(True)
            self.password_edit.setEnabled(True)
            self.database_edit.setPlaceholderText("数据库名")
    
    def get_connection_info(self):
        """获取连接信息"""
        db_type = self.type_combo.currentText().lower()
        connection_info = {
            "name": self.name_edit.text(),
            "type": db_type,
            "host": self.host_edit.text(),
            "port": self.port_edit.text(),
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "database": self.database_edit.text()
        }
        return connection_info
