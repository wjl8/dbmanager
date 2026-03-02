#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL查询编辑器组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, 
    QLabel, QSplitter, QFileDialog, QMenu, QMessageBox, QComboBox, QProgressDialog,
    QTabWidget, QInputDialog, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QAction, QKeySequence, QStandardItem

# 尝试导入QScintilla，如果失败则使用QPlainTextEdit
try:
    from PyQt6.Qsci import QsciScintilla, QsciLexerSQL
    HAS_QSCINTILLA = True
except ImportError:
    HAS_QSCINTILLA = False

import pandas as pd
import time
from openpyxl import Workbook


class QueryTab(QWidget):
    """查询标签页"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._init_ui()
        self.query_history = []
        self.max_history = 50
        self.current_result = None
        self.execution_time = 0
        self.row_count = 0
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 执行按钮
        self.run_button = QPushButton("▶ 执行")
        self.run_button.clicked.connect(self._run_query)
        self.run_button.setShortcut(QKeySequence("Ctrl+Return"))
        toolbar_layout.addWidget(self.run_button)
        
        # 状态标签
        self.status_label = QLabel("状态：就绪")
        toolbar_layout.addWidget(self.status_label)
        
        # 耗时标签
        self.time_label = QLabel("耗时：0.00s")
        toolbar_layout.addWidget(self.time_label)
        
        # 行数标签
        self.rows_label = QLabel("行数：0 rows")
        toolbar_layout.addWidget(self.rows_label)
        
        # 查询历史下拉框
        toolbar_layout.addStretch()
        self.history_label = QLabel("历史查询：")
        toolbar_layout.addWidget(self.history_label)
        self.history_combo = QComboBox()
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        toolbar_layout.addWidget(self.history_combo)
        
        # 清除历史按钮
        self.clear_history_button = QPushButton("清除历史")
        self.clear_history_button.clicked.connect(self._clear_history)
        toolbar_layout.addWidget(self.clear_history_button)
        
        layout.addLayout(toolbar_layout)
        
        # 主分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 初始化编辑器
        self._init_editor()
        splitter.addWidget(self.editor)
        
        # 结果区域
        result_widget = QWidget()
        result_layout = QVBoxLayout()
        
        # 导出工具栏
        export_toolbar = QHBoxLayout()
        self.export_csv_button = QPushButton("导出 CSV")
        self.export_csv_button.clicked.connect(lambda: self._export("csv"))
        export_toolbar.addWidget(self.export_csv_button)
        
        self.export_excel_button = QPushButton("导出 Excel")
        self.export_excel_button.clicked.connect(lambda: self._export("excel"))
        export_toolbar.addWidget(self.export_excel_button)
        
        export_toolbar.addStretch()
        result_layout.addLayout(export_toolbar)
        
        # 错误信息标签
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        self.error_label.setVisible(False)
        result_layout.addWidget(self.error_label)
        
        # 结果截断提示
        self.truncated_label = QLabel()
        self.truncated_label.setStyleSheet("color: orange")
        self.truncated_label.setVisible(False)
        result_layout.addWidget(self.truncated_label)
        
        # 结果表格
        self.table_view = QTableView()
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_table_context_menu)
        result_layout.addWidget(self.table_view)
        
        result_widget.setLayout(result_layout)
        splitter.addWidget(result_widget)
        
        # 设置分割比例
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def _init_editor(self):
        """初始化编辑器"""
        if HAS_QSCINTILLA:
            # 使用QScintilla编辑器
            self.editor = QsciScintilla()
            # 设置字体
            font = QFont("Consolas", 14)
            self.editor.setFont(font)
            
            # 设置SQL语法高亮
            lexer = QsciLexerSQL()
            lexer.setFont(font)
            self.editor.setLexer(lexer)
            
            # 显示行号
            self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            self.editor.setMarginWidth(0, "00000")
            
            # 设置自动缩进
            self.editor.setAutoIndent(True)
            self.editor.setIndentationWidth(4)
            
            # 设置Tab宽度
            self.editor.setTabWidth(4)
            
            # 设置换行
            self.editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        else:
            # 使用QPlainTextEdit作为备用
            self.editor = QPlainTextEdit()
            # 设置字体
            font = QFont("Consolas", 14)
            self.editor.setFont(font)
            
            # 设置Tab宽度
            self.editor.setTabStopDistance(4 * font.pointSizeF())
            
            # 设置换行
            self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
    
    def _run_query(self):
        """执行查询"""
        # 获取SQL语句
        if HAS_QSCINTILLA:
            sql = self.editor.text()
        else:
            sql = self.editor.toPlainText()
        
        if not sql.strip():
            QMessageBox.information(self, "提示", "SQL语句为空")
            return
        
        # 禁用按钮
        self.run_button.setEnabled(False)
        self.status_label.setText("状态：执行中...")
        self.error_label.setVisible(False)
        self.truncated_label.setVisible(False)
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建执行任务
        task = QueryTask(sql, self.engine, start_time)
        task.signals.result_ready.connect(self._on_result_ready)
        task.signals.error_occurred.connect(self._on_error_occurred)
        task.signals.finished.connect(self._on_task_finished)
        
        # 提交到线程池
        QThreadPool.globalInstance().start(task)
    
    def _on_result_ready(self, result):
        """处理查询结果"""
        self.current_result = result
        
        # 处理大数据量
        total_rows = len(result)
        truncated = False
        if total_rows > 10000:
            result = result.head(1000)
            truncated = True
        
        # 更新行数标签
        self.row_count = len(result)
        self.rows_label.setText(f"行数：{self.row_count} rows")
        
        # 显示截断提示
        if truncated:
            self.truncated_label.setText(f"结果已截断，共 {total_rows} 行")
            self.truncated_label.setVisible(True)
        
        # 创建模型并设置数据
        from PyQt6.QtGui import QStandardItemModel
        model = QStandardItemModel()
        
        # 设置表头
        model.setHorizontalHeaderLabels(result.columns)
        
        # 填充数据
        for row in range(len(result)):
            items = []
            for col in range(len(result.columns)):
                item = QStandardItem(str(result.iloc[row, col]))
                items.append(item)
            model.appendRow(items)
        
        # 设置模型
        self.table_view.setModel(model)
        
        # 调整列宽
        self.table_view.resizeColumnsToContents()
        
        # 保存到历史记录
        if HAS_QSCINTILLA:
            sql = self.editor.text()
        else:
            sql = self.editor.toPlainText()
        self._add_to_history(sql)
    
    def _on_error_occurred(self, error):
        """处理错误"""
        self.error_label.setText(f"执行错误: {error}")
        self.error_label.setVisible(True)
        self.current_result = None
        self.rows_label.setText("行数：0 rows")
        
        # 清空表格
        from PyQt6.QtGui import QStandardItemModel
        self.table_view.setModel(QStandardItemModel())
    
    def _on_task_finished(self, elapsed):
        """任务完成"""
        self.run_button.setEnabled(True)
        self.status_label.setText("状态：就绪")
        self.execution_time = elapsed
        self.time_label.setText(f"耗时：{elapsed:.2f}s")
    
    def _add_to_history(self, sql):
        """添加到历史记录"""
        # 去重
        if sql in self.query_history:
            self.query_history.remove(sql)
        
        # 添加到开头
        self.query_history.insert(0, sql)
        
        # 限制历史记录数量
        if len(self.query_history) > self.max_history:
            self.query_history = self.query_history[:self.max_history]
        
        # 更新下拉框
        self._update_history_combo()
    
    def _update_history_combo(self):
        """更新历史记录下拉框"""
        self.history_combo.clear()
        for sql in self.query_history:
            # 显示前15个字符
            display_text = sql[:15] + "..." if len(sql) > 15 else sql
            self.history_combo.addItem(display_text, sql)
    
    def _on_history_selected(self, text):
        """历史记录被选择"""
        if self.history_combo.currentIndex() >= 0:
            sql = self.history_combo.currentData()
            if HAS_QSCINTILLA:
                self.editor.setText(sql)
            else:
                self.editor.setPlainText(sql)
    
    def _clear_history(self):
        """清除历史记录"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.query_history.clear()
            self._update_history_combo()
    
    def _export(self, file_type):
        """导出数据"""
        if self.current_result is None:
            QMessageBox.information(self, "提示", "无数据可导出")
            return
        
        # 选择保存路径
        if file_type == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存CSV文件", "", "CSV Files (*.csv)"
            )
            if file_path:
                self._export_to_csv(file_path)
        elif file_type == "excel":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存Excel文件", "", "Excel Files (*.xlsx)"
            )
            if file_path:
                self._export_to_excel(file_path)
    
    def _export_to_csv(self, file_path):
        """导出为CSV文件"""
        try:
            # 显示进度对话框
            progress = QProgressDialog("正在导出...", "取消", 0, 100, self)
            progress.setWindowTitle("导出CSV")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # 导出数据
            self.current_result.to_csv(file_path, index=False)
            
            progress.setValue(100)
            QMessageBox.information(self, "成功", "数据已导出为CSV文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _export_to_excel(self, file_path):
        """导出为Excel文件"""
        try:
            # 显示进度对话框
            progress = QProgressDialog("正在导出...", "取消", 0, 100, self)
            progress.setWindowTitle("导出Excel")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            # 导出数据
            self.current_result.to_excel(file_path, index=False, engine='openpyxl')
            
            progress.setValue(100)
            QMessageBox.information(self, "成功", "数据已导出为Excel文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _show_table_context_menu(self, position):
        """显示表格上下文菜单"""
        menu = QMenu()
        
        # 复制单元格
        copy_cell_action = QAction("复制单元格", self)
        copy_cell_action.triggered.connect(self._copy_cell)
        menu.addAction(copy_cell_action)
        
        # 复制整行
        copy_row_action = QAction("复制整行", self)
        copy_row_action.triggered.connect(self._copy_row)
        menu.addAction(copy_row_action)
        
        # 导出选中行
        export_selected_action = QAction("导出选中行", self)
        export_selected_action.triggered.connect(self._export_selected_rows)
        menu.addAction(export_selected_action)
        
        menu.exec(self.table_view.mapToGlobal(position))
    
    def _copy_cell(self):
        """复制选中单元格"""
        indexes = self.table_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            value = index.data()
            if value:
                from PyQt6.QtGui import QClipboard
                clipboard = self.table_view.clipboard()
                clipboard.setText(str(value))
    
    def _copy_row(self):
        """复制整行"""
        indexes = self.table_view.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            model = self.table_view.model()
            row_data = []
            for col in range(model.columnCount()):
                value = model.data(model.index(row, col))
                row_data.append(str(value) if value else "")
            
            from PyQt6.QtGui import QClipboard
            clipboard = self.table_view.clipboard()
            clipboard.setText("\t".join(row_data))
    
    def _export_selected_rows(self):
        """导出选中行"""
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            QMessageBox.information(self, "提示", "请选择要导出的行")
            return
        
        # 获取选中的行号
        rows = set()
        for index in indexes:
            rows.add(index.row())
        rows = sorted(rows)
        
        # 提取选中的行数据
        selected_data = self.current_result.iloc[rows]
        
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存选中行", "", "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    selected_data.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    selected_data.to_excel(file_path, index=False, engine='openpyxl')
                QMessageBox.information(self, "成功", "选中行已导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def get_tab_title(self):
        """获取标签页标题"""
        # 根据编辑器类型获取文本
        if HAS_QSCINTILLA:
            sql = self.editor.text()
        else:
            sql = self.editor.toPlainText()
        
        if sql:
            title = sql[:15] + "..." if len(sql) > 15 else sql
        else:
            title = "新建查询"
        return title
    
    def set_engine(self, engine):
        """设置SQLAlchemy引擎"""
        self.engine = engine


class QueryTask(QRunnable):
    """查询任务"""
    
    class Signals(QObject):
        result_ready = pyqtSignal(pd.DataFrame)
        error_occurred = pyqtSignal(str)
        finished = pyqtSignal(float)
    
    def __init__(self, sql, engine, start_time):
        super().__init__()
        self.sql = sql
        self.engine = engine
        self.start_time = start_time
        self.signals = self.Signals()
    
    def run(self):
        """运行查询"""
        try:
            if self.engine:
                # 使用SQLAlchemy引擎执行查询
                result = pd.read_sql(self.sql, self.engine)
                self.signals.result_ready.emit(result)
            else:
                self.signals.error_occurred.emit("数据库引擎未设置")
        except Exception as e:
            self.signals.error_occurred.emit(str(e))
        finally:
            # 计算执行时间
            elapsed = time.time() - self.start_time
            self.signals.finished.emit(elapsed)


class QueryEditorWidget(QWidget):
    """查询编辑器组件"""
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.connections = []  # 存储连接信息
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 连接和数据库选择工具栏
        conn_toolbar = QHBoxLayout()
        
        # 连接选择
        conn_toolbar.addWidget(QLabel("连接："))
        self.connection_combo = QComboBox()
        self.connection_combo.currentIndexChanged.connect(self._on_connection_changed)
        conn_toolbar.addWidget(self.connection_combo)
        
        # 数据库选择
        conn_toolbar.addWidget(QLabel("数据库："))
        self.database_combo = QComboBox()
        self.database_combo.currentIndexChanged.connect(self._on_database_changed)
        conn_toolbar.addWidget(self.database_combo)
        
        conn_toolbar.addStretch()
        layout.addLayout(conn_toolbar)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self._show_tab_context_menu)
        
        # 双击标签页重命名
        self.tab_widget.tabBarDoubleClicked.connect(self._rename_tab)
        
        # 添加第一个标签页
        self._add_new_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 添加标签页按钮
        self.add_tab_button = QPushButton("+ 新建查询")
        self.add_tab_button.clicked.connect(self._add_new_tab)
        layout.addWidget(self.add_tab_button)
        
        self.setLayout(layout)
    
    def set_connections(self, connections):
        """设置可用的连接列表"""
        self.connections = connections
        self._update_connection_combo()
    
    def add_connection(self, connection):
        """添加单个连接"""
        if connection not in self.connections:
            self.connections.append(connection)
            self._update_connection_combo()
    
    def _update_connection_combo(self):
        """更新连接下拉框"""
        self.connection_combo.clear()
        for conn in self.connections:
            self.connection_combo.addItem(conn["name"], conn)
        
        # 如果有连接，默认选择第一个
        if self.connections:
            self._on_connection_changed(0)
    
    def _on_connection_changed(self, index):
        """连接选择变化"""
        if index >= 0:
            connection = self.connection_combo.itemData(index)
            # 获取该连接下的数据库列表
            databases = self._get_databases(connection)
            self._update_database_combo(databases, connection)
    
    def _get_databases(self, connection):
        """获取连接下的数据库列表"""
        databases = []
        try:
            from app.services.driver_factory import DriverFactory
            driver = DriverFactory.create_driver(connection["type"])
            if driver.connect(connection):
                if connection["type"] == "mysql":
                    result = driver.execute("SHOW DATABASES")
                    if result:
                        databases = [db["Database"] for db in result]
                elif connection["type"] == "sqlite":
                    # SQLite只有一个数据库
                    databases = [connection.get("database", "")]
                driver.disconnect()
        except Exception as e:
            print(f"获取数据库列表失败: {str(e)}")
        return databases
    
    def _update_database_combo(self, databases, connection):
        """更新数据库下拉框"""
        self.database_combo.clear()
        for db in databases:
            self.database_combo.addItem(db, db)
        
        # 如果有数据库，默认选择第一个
        if databases:
            self._on_database_changed(0)
    
    def _on_database_changed(self, index):
        """数据库选择变化"""
        if index >= 0:
            connection = self.connection_combo.currentData()
            database = self.database_combo.itemData(index)
            if connection and database:
                # 创建新的引擎
                engine = self._create_engine(connection, database)
                # 更新所有标签页的引擎
                for i in range(self.tab_widget.count()):
                    tab = self.tab_widget.widget(i)
                    tab.set_engine(engine)
    
    def _create_engine(self, connection, database):
        """创建数据库引擎"""
        from sqlalchemy import create_engine
        
        if connection["type"] == "mysql":
            # MySQL连接字符串
            db_url = f"mysql+pymysql://{connection['username']}:{connection['password']}@{connection['host']}:{connection['port']}/{database}"
        elif connection["type"] == "sqlite":
            # SQLite连接字符串
            db_url = f"sqlite:///{connection['database']}"
        else:
            # 其他数据库类型
            db_url = ""
        
        # 创建引擎
        engine = None
        if db_url:
            try:
                engine = create_engine(db_url)
            except Exception as e:
                print(f"创建数据库引擎失败: {str(e)}")
        return engine
    
    def _add_new_tab(self):
        """添加新标签页"""
        tab = QueryTab(self.engine)
        tab_index = self.tab_widget.addTab(tab, tab.get_tab_title())
        self.tab_widget.setCurrentIndex(tab_index)
        
        # 连接编辑器文本变化信号
        tab.editor.textChanged.connect(lambda: self._update_tab_title(tab))
    
    def _close_tab(self, index):
        """关闭标签页"""
        if self.tab_widget.count() == 1:
            # 最后一个标签页，清空内容
            tab = self.tab_widget.widget(0)
            tab.editor.clear()
            tab.current_result = None
            tab.rows_label.setText("行数：0 rows")
            tab.time_label.setText("耗时：0.00s")
            from PyQt6.QtGui import QStandardItemModel
            tab.table_view.setModel(QStandardItemModel())
            tab.error_label.setVisible(False)
            tab.truncated_label.setVisible(False)
        else:
            self.tab_widget.removeTab(index)
    
    def _update_tab_title(self, tab):
        """更新标签页标题"""
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            self.tab_widget.setTabText(index, tab.get_tab_title())
    
    def _show_tab_context_menu(self, position):
        """显示标签页上下文菜单"""
        menu = QMenu()
        
        # 关闭
        close_action = QAction("关闭", self)
        close_action.triggered.connect(lambda: self._close_tab(self.tab_widget.currentIndex()))
        menu.addAction(close_action)
        
        # 关闭其他
        close_other_action = QAction("关闭其他", self)
        close_other_action.triggered.connect(self._close_other_tabs)
        menu.addAction(close_other_action)
        
        # 复制当前标签
        duplicate_action = QAction("复制当前标签", self)
        duplicate_action.triggered.connect(self._duplicate_tab)
        menu.addAction(duplicate_action)
        
        menu.exec(self.tab_widget.mapToGlobal(position))
    
    def _close_other_tabs(self):
        """关闭其他标签页"""
        current_index = self.tab_widget.currentIndex()
        indexes_to_remove = []
        
        for i in range(self.tab_widget.count()):
            if i != current_index:
                indexes_to_remove.append(i)
        
        # 从后往前删除
        for i in sorted(indexes_to_remove, reverse=True):
            self.tab_widget.removeTab(i)
    
    def _duplicate_tab(self):
        """复制当前标签页"""
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            new_tab = QueryTab(self.engine)
            # 根据编辑器类型获取和设置文本
            if HAS_QSCINTILLA:
                sql = current_tab.editor.text()
                new_tab.editor.setText(sql)
            else:
                sql = current_tab.editor.toPlainText()
                new_tab.editor.setPlainText(sql)
            new_tab.query_history = current_tab.query_history.copy()
            new_tab._update_history_combo()
            
            tab_index = self.tab_widget.addTab(new_tab, new_tab.get_tab_title())
            self.tab_widget.setCurrentIndex(tab_index)
            
            # 连接编辑器文本变化信号
            new_tab.editor.textChanged.connect(lambda: self._update_tab_title(new_tab))
    
    def _rename_tab(self, index):
        """重命名标签页"""
        tab = self.tab_widget.widget(index)
        if tab:
            current_title = self.tab_widget.tabText(index)
            new_title, ok = QInputDialog.getText(
                self, "重命名标签", "请输入新的标签名称:", text=current_title
            )
            if ok and new_title:
                self.tab_widget.setTabText(index, new_title)
    
    def set_engine(self, engine):
        """设置SQLAlchemy引擎"""
        self.engine = engine
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            tab.set_engine(engine)
