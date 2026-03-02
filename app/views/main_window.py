#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口类
"""

from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QTabWidget, QTextEdit,
    QMenuBar, QToolBar, QStatusBar, QVBoxLayout,
    QWidget, QFileDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os
from app.views.connection_tree import ConnectionTreeWidget
from app.views.sql_editor import SQLEditorWidget
from app.views.data_editor import DataEditorWidget


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据库管理工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置应用图标
        self._set_app_icon()
        
        # 加载样式表
        self._load_style_sheet()
        
        self._init_ui()
    
    def _set_app_icon(self):
        """设置应用图标"""
        icon_file = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "app_icon.png")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
    
    def _load_style_sheet(self):
        """加载样式表"""
        style_file = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "styles", "style.qss")
        if os.path.exists(style_file):
            with open(style_file, "r", encoding="utf-8") as f:
                style_sheet = f.read()
                self.setStyleSheet(style_sheet)
    
    def _init_ui(self):
        """初始化UI"""
        # 菜单栏
        self._init_menu_bar()
        
        # 工具栏
        self._init_tool_bar()
        
        # 中央工作区
        self._init_central_widget()
        
        # 左侧连接树
        self._init_connection_dock()
        
        # 底部日志面板
        self._init_log_dock()
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def _init_menu_bar(self):
        """初始化菜单栏"""
        menu_bar = QMenuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_connection_action = QAction("新建连接", self)
        new_connection_action.triggered.connect(self._new_connection)
        file_menu.addAction(new_connection_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        # 显示/隐藏连接树
        toggle_connection_action = QAction("显示连接树", self)
        toggle_connection_action.setCheckable(True)
        toggle_connection_action.setChecked(True)
        toggle_connection_action.triggered.connect(self._toggle_connection_dock)
        view_menu.addAction(toggle_connection_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        self.setMenuBar(menu_bar)
    
    def _init_tool_bar(self):
        """初始化工具栏"""
        tool_bar = QToolBar("工具栏")
        
        new_connection_action = QAction("新建连接", self)
        tool_bar.addAction(new_connection_action)
        
        execute_action = QAction("执行", self)
        tool_bar.addAction(execute_action)
        
        self.addToolBar(tool_bar)
    
    def _init_central_widget(self):
        """初始化中央工作区"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # 启用标签页关闭功能
        self.tab_widget.tabCloseRequested.connect(self._close_tab)  # 连接关闭信号
        self.setCentralWidget(self.tab_widget)
        
        # 添加默认的SQL编辑器标签
        self._add_sql_editor_tab()
    
    def _init_connection_dock(self):
        """初始化连接树"""
        self.connection_dock = QDockWidget("连接", self)
        self.connection_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        
        tree_widget = ConnectionTreeWidget()
        
        # 设置数据表双击事件处理函数
        tree_widget.on_table_double_clicked = self._on_table_double_clicked
        
        # 设置打开SQL编辑器事件处理函数
        tree_widget.on_open_sql_editor = self._on_open_sql_editor
        
        self.connection_dock.setWidget(tree_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.connection_dock)
    
    def _on_table_double_clicked(self, connection_info, database_name, table_name):
        """处理数据表双击事件"""
        from app.services.driver_factory import DriverFactory
        
        try:
            # 创建数据库驱动
            driver = DriverFactory.create_driver(connection_info["type"])
            
            # 连接数据库
            success = driver.connect(connection_info)
            if success:
                # 获取表数据
                if connection_info["type"] == "mysql":
                    # 构建查询语句
                    sql = f"SELECT * FROM `{database_name}`.`{table_name}`"
                else:  # sqlite
                    sql = f"SELECT * FROM `{table_name}`"
                
                # 执行查询，限制结果数量
                if connection_info["type"] == "mysql":
                    # 构建查询语句，限制为前1000行
                    sql = f"SELECT * FROM `{database_name}`.`{table_name}` LIMIT 1000"
                else:  # sqlite
                    sql = f"SELECT * FROM `{table_name}` LIMIT 1000"
                
                # 执行查询
                result = driver.execute(sql)
                
                if result:
                    # 获取列名
                    columns = list(result[0].keys())
                    
                    # 添加数据编辑器标签
                    data_editor = DataEditorWidget()
                    # 创建连接信息的副本，并添加数据库名
                    connection_info_copy = connection_info.copy()
                    connection_info_copy["database"] = database_name
                    data_editor.set_connection_info(connection_info_copy, table_name)
                    data_editor.load_data(result, columns)
                    
                    # 添加到标签页
                    tab_name = f"{database_name}.{table_name}"
                    self.tab_widget.addTab(data_editor, tab_name)
                    self.tab_widget.setCurrentWidget(data_editor)
                    
                    # 显示数据量信息
                    from PyQt6.QtWidgets import QMessageBox
                    if len(result) == 1000:
                        QMessageBox.information(self, "信息", f"表数据较多，仅显示前1000行")
                    else:
                        QMessageBox.information(self, "信息", f"表中有 {len(result)} 行数据")
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(self, "信息", "表中没有数据")
                
                # 断开连接
                driver.disconnect()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", f"打开表失败: {str(e)}")
    
    def _init_log_dock(self):
        """初始化日志面板"""
        dock = QDockWidget("日志", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.append("欢迎使用数据库管理工具")
        
        dock.setWidget(log_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
    
    def _add_sql_editor_tab(self):
        """添加SQL编辑器标签"""
        sql_editor = SQLEditorWidget()
        self.tab_widget.addTab(sql_editor, "SQL编辑器")
    
    def _add_data_editor_tab(self):
        """添加数据编辑器标签"""
        data_editor = DataEditorWidget()
        # 加载示例数据
        sample_data = [
            {'id': 1, 'name': 'Alice', 'age': 25},
            {'id': 2, 'name': 'Bob', 'age': 30},
            {'id': 3, 'name': 'Charlie', 'age': 35}
        ]
        sample_columns = ['id', 'name', 'age']
        data_editor.load_data(sample_data, sample_columns)
        self.tab_widget.addTab(data_editor, "数据编辑器")
    
    def _new_connection(self):
        """新建连接"""
        # 这里将实现连接对话框
        pass
    
    def _on_open_sql_editor(self, connection_info):
        """处理打开SQL编辑器的请求"""
        # 创建SQL编辑器
        from app.views.query_editor import QueryEditorWidget
        
        # 获取所有连接信息
        connections = []
        # 从连接树中获取所有连接
        connection_tree = None
        for dock_widget in self.findChildren(QDockWidget):
            if dock_widget.windowTitle() == "连接":
                connection_tree = dock_widget.widget()
                break
        
        if connection_tree:
            # 获取根节点（ConnectionTreeWidget的root属性）
            if hasattr(connection_tree, 'root'):
                root = connection_tree.root
                # 遍历所有连接
                for i in range(root.childCount()):
                    connection_item = root.child(i)
                    conn_info = connection_item.data(0, Qt.ItemDataRole.UserRole)
                    if conn_info:
                        connections.append(conn_info)
            else:
                # 备选方案：使用invisibleRootItem
                root = connection_tree.invisibleRootItem()
                # 遍历所有子节点
                for i in range(root.childCount()):
                    child = root.child(i)
                    # 检查是否是"连接"节点
                    if child.text(0) == "连接":
                        # 遍历连接节点的子节点
                        for j in range(child.childCount()):
                            connection_item = child.child(j)
                            conn_info = connection_item.data(0, Qt.ItemDataRole.UserRole)
                            if conn_info:
                                connections.append(conn_info)
                        break
        
        # 创建查询编辑器
        query_editor = QueryEditorWidget()
        
        # 设置连接列表
        if connections:
            query_editor.set_connections(connections)
            
            # 自动选择当前连接
            found = False
            for i, conn in enumerate(connections):
                if conn["name"] == connection_info["name"]:
                    query_editor.connection_combo.setCurrentIndex(i)
                    # 自动选择当前数据库
                    if "database" in connection_info:
                        database = connection_info["database"]
                        for j in range(query_editor.database_combo.count()):
                            if query_editor.database_combo.itemData(j) == database:
                                query_editor.database_combo.setCurrentIndex(j)
                                break
                    found = True
                    break
            
            # 如果没有找到当前连接，添加它
            if not found:
                query_editor.add_connection(connection_info)
                query_editor.connection_combo.setCurrentIndex(len(connections))
                # 自动选择当前数据库
                if "database" in connection_info:
                    database = connection_info["database"]
                    for j in range(query_editor.database_combo.count()):
                        if query_editor.database_combo.itemData(j) == database:
                            query_editor.database_combo.setCurrentIndex(j)
                            break
        else:
            # 如果没有获取到任何连接，至少添加当前连接
            query_editor.add_connection(connection_info)
            query_editor.connection_combo.setCurrentIndex(0)
            # 自动选择当前数据库
            if "database" in connection_info:
                database = connection_info["database"]
                for j in range(query_editor.database_combo.count()):
                    if query_editor.database_combo.itemData(j) == database:
                        query_editor.database_combo.setCurrentIndex(j)
                        break
        
        # 添加到标签页
        tab_name = f"查询编辑器 - {connection_info['name']}"
        self.tab_widget.addTab(query_editor, tab_name)
        self.tab_widget.setCurrentWidget(query_editor)
    
    def _close_tab(self, index):
        """关闭标签页"""
        self.tab_widget.removeTab(index)
    
    def _toggle_connection_dock(self, checked):
        """切换连接树的显示/隐藏"""
        self.connection_dock.setVisible(checked)
