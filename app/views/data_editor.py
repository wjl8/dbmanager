#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据编辑器组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, 
    QMessageBox, QSplitter, QLabel
)
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal
from PyQt6.QtGui import QColor
import copy


class EditableTableModel(QAbstractTableModel):
    """可编辑的表格模型"""
    
    data_changed = pyqtSignal()
    
    def __init__(self, data=None, columns=None):
        super().__init__()
        self.original_data = data or []
        self.data = copy.deepcopy(self.original_data)
        self.columns = columns or []
        self.modified_cells = set()  # 记录修改的单元格 (row, col)
        self.added_rows = set()      # 记录新增的行
        self.deleted_rows = set()    # 记录删除的行
    
    def rowCount(self, parent=None):
        return len(self.data)
    
    def columnCount(self, parent=None):
        return len(self.columns)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if row < len(self.data) and col < len(self.columns):
                return str(self.data[row].get(self.columns[col], ''))
        
        if role == Qt.ItemDataRole.BackgroundRole:
            if (row, col) in self.modified_cells:
                return QColor(255, 255, 200)  # 浅黄色标记已修改
            if row in self.added_rows:
                return QColor(200, 255, 200)  # 浅绿色标记新增行
        
        return None
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            
            if row < len(self.data) and col < len(self.columns):
                column_name = self.columns[col]
                old_value = self.data[row].get(column_name, '')
                
                if str(old_value) != str(value):
                    self.data[row][column_name] = value
                    self.modified_cells.add((row, col))
                    self.data_changed.emit()
                    self.layoutChanged.emit()
                    return True
        
        return False
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.columns):
                    return self.columns[section]
            else:
                return str(section + 1)
        return None
    
    def load_data(self, data, columns):
        """加载数据"""
        self.original_data = data
        self.data = copy.deepcopy(self.original_data)
        self.columns = columns
        self.modified_cells.clear()
        self.added_rows.clear()
        self.deleted_rows.clear()
        self.layoutChanged.emit()
    
    def add_row(self):
        """新增行"""
        new_row = {col: '' for col in self.columns}
        self.data.append(new_row)
        row_index = len(self.data) - 1
        self.added_rows.add(row_index)
        self.data_changed.emit()
        self.layoutChanged.emit()
        return row_index
    
    def delete_row(self, row):
        """删除行"""
        if 0 <= row < len(self.data):
            if row not in self.added_rows:
                self.deleted_rows.add(row)
            self.data.pop(row)
            
            # 更新修改的单元格索引
            updated_modified_cells = set()
            for r, c in self.modified_cells:
                if r < row:
                    updated_modified_cells.add((r, c))
                elif r > row:
                    updated_modified_cells.add((r-1, c))
            self.modified_cells = updated_modified_cells
            
            # 更新新增行索引
            updated_added_rows = set()
            for r in self.added_rows:
                if r < row:
                    updated_added_rows.add(r)
                elif r > row:
                    updated_added_rows.add(r-1)
            self.added_rows = updated_added_rows
            
            # 更新删除行索引
            updated_deleted_rows = set()
            for r in self.deleted_rows:
                if r < row:
                    updated_deleted_rows.add(r)
                elif r > row:
                    updated_deleted_rows.add(r-1)
            self.deleted_rows = updated_deleted_rows
            
            self.data_changed.emit()
            self.layoutChanged.emit()
    
    def submit(self, driver=None, table_name=None):
        """提交修改"""
        try:
            if not driver or not table_name:
                # 如果没有数据库连接，只更新模型状态
                self.original_data = copy.deepcopy(self.data)
                self.modified_cells.clear()
                self.added_rows.clear()
                self.deleted_rows.clear()
                self.layoutChanged.emit()
                return True
            
            # 开始事务
            driver.begin_transaction()
            
            # 处理删除操作
            for row in sorted(self.deleted_rows, reverse=True):
                if row < len(self.original_data):
                    # 生成DELETE语句
                    primary_key = self._get_primary_key()
                    if primary_key:
                        primary_value = self.original_data[row].get(primary_key)
                        if primary_value:
                            sql = f"DELETE FROM `{table_name}` WHERE `{primary_key}` = %s"
                            driver.execute(sql, [primary_value])
            
            # 处理新增操作
            for row in self.added_rows:
                if row < len(self.data):
                    # 生成INSERT语句
                    values = []
                    placeholders = []
                    for col in self.columns:
                        value = self.data[row].get(col)
                        if value is not None:
                            values.append(value)
                            placeholders.append("%")
                    
                    if values:
                        columns_str = ", ".join([f"`{col}`" for col in self.columns])
                        placeholders_str = ", ".join(placeholders)
                        sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders_str})"
                        driver.execute(sql, values)
            
            # 处理修改操作
            for row, col in self.modified_cells:
                if row < len(self.data) and row not in self.added_rows:
                    # 生成UPDATE语句
                    column_name = self.columns[col]
                    value = self.data[row].get(column_name)
                    
                    primary_key = self._get_primary_key()
                    if primary_key:
                        primary_value = self.original_data[row].get(primary_key)
                        if primary_value:
                            sql = f"UPDATE `{table_name}` SET `{column_name}` = %s WHERE `{primary_key}` = %s"
                            driver.execute(sql, [value, primary_value])
            
            # 提交事务
            driver.commit()
            
            # 更新原始数据
            self.original_data = copy.deepcopy(self.data)
            self.modified_cells.clear()
            self.added_rows.clear()
            self.deleted_rows.clear()
            self.layoutChanged.emit()
            
            return True
        except Exception as e:
            # 回滚事务
            if driver:
                driver.rollback()
            raise e
    
    def rollback(self):
        """回滚修改"""
        self.data = copy.deepcopy(self.original_data)
        self.modified_cells.clear()
        self.added_rows.clear()
        self.deleted_rows.clear()
        self.layoutChanged.emit()
    
    def _get_primary_key(self):
        """获取主键"""
        # 简单实现，假设第一个列为主键
        if self.columns:
            return self.columns[0]
        return None
    
    def has_changes(self):
        """检查是否有修改"""
        return bool(self.modified_cells or self.added_rows or self.deleted_rows)


class DataEditorWidget(QWidget):
    """数据编辑器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.connection_info = None
        self.table_name = None
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_button = QPushButton("新增行")
        self.add_button.clicked.connect(self._add_row)
        toolbar_layout.addWidget(self.add_button)
        
        self.delete_button = QPushButton("删除行")
        self.delete_button.clicked.connect(self._delete_row)
        toolbar_layout.addWidget(self.delete_button)
        
        toolbar_layout.addStretch()
        
        self.submit_button = QPushButton("提交")
        self.submit_button.clicked.connect(self._submit)
        toolbar_layout.addWidget(self.submit_button)
        
        self.rollback_button = QPushButton("回滚")
        self.rollback_button.clicked.connect(self._rollback)
        toolbar_layout.addWidget(self.rollback_button)
        
        layout.addLayout(toolbar_layout)
        
        # 表格视图
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addWidget(self.table_view)
        
        self.setLayout(layout)
        
        # 初始化模型
        self.model = EditableTableModel()
        self.table_view.setModel(self.model)
        
        # 连接信号
        self.model.data_changed.connect(self._on_data_changed)
    
    def set_model(self, model):
        """设置模型"""
        self.model = model
        self.table_view.setModel(self.model)
        self.model.data_changed.connect(self._on_data_changed)
        self._on_data_changed()
    
    def _add_row(self):
        """新增行"""
        self.model.add_row()
    
    def _delete_row(self):
        """删除行"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if selected_indexes:
            row = selected_indexes[0].row()
            self.model.delete_row(row)
    
    def _submit(self):
        """提交修改"""
        if self.model.has_changes():
            if self.connection_info and self.table_name:
                try:
                    from app.services.driver_factory import DriverFactory
                    
                    # 创建数据库驱动
                    driver = DriverFactory.create_driver(self.connection_info["type"])
                    
                    # 连接数据库
                    success = driver.connect(self.connection_info)
                    if success:
                        # 提交修改
                        self.model.submit(driver, self.table_name)
                        QMessageBox.information(self, "成功", "数据提交成功")
                        self.status_label.setText("就绪")
                        
                        # 断开连接
                        driver.disconnect()
                    else:
                        QMessageBox.critical(self, "错误", "连接数据库失败")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"提交失败: {str(e)}")
            else:
                QMessageBox.information(self, "提示", "提交功能需要数据库连接，暂未实现")
                self.status_label.setText("就绪")
        else:
            QMessageBox.information(self, "提示", "没有需要提交的修改")
    
    def _rollback(self):
        """回滚修改"""
        if self.model.has_changes():
            self.model.rollback()
            QMessageBox.information(self, "成功", "修改已回滚")
            self.status_label.setText("就绪")
        else:
            QMessageBox.information(self, "提示", "没有需要回滚的修改")
    
    def _on_data_changed(self):
        """数据变化时更新状态"""
        if self.model.has_changes():
            self.status_label.setText("有未提交的修改")
            self.status_label.setStyleSheet("color: blue")
        else:
            self.status_label.setText("就绪")
            self.status_label.setStyleSheet("color: black")
    
    def load_data(self, data, columns):
        """加载数据"""
        self.model.load_data(data, columns)
        # 调整列宽
        self.table_view.resizeColumnsToContents()
    
    def set_connection_info(self, connection_info, table_name):
        """设置数据库连接信息和表名"""
        self.connection_info = connection_info
        self.table_name = table_name
