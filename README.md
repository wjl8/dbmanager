# 数据库管理工具

一个跨平台的数据库管理工具，对标 Navicat Premium 15 的核心功能。

## 核心功能

- **连接管理**：支持 MySQL, PostgreSQL, SQLite, SQL Server, Oracle, Redis, MongoDB
- **对象浏览**：树状结构显示数据库、表、视图、存储过程
- **SQL 编辑器**：支持语法高亮、自动补全、执行选中语句、多结果集展示
- **数据编辑**：类似 Excel 的表格编辑，支持增删改查并提交事务
- **导入导出**：支持 SQL, CSV, JSON 格式的导入导出
- **ER 图**：可视化表关系

## 技术栈

- **语言**：Python 3.10+
- **GUI 框架**：PyQt6
- **数据库驱动**：SQLAlchemy, psycopg2, pymysql, redis-py, pymongo 等
- **代码编辑器**：QScintilla
- **配置存储**：本地加密存储连接信息

## 项目结构

```
dbmanager/
├── app/
│   ├── controllers/          # 控制器
│   ├── models/               # 数据模型
│   ├── views/                # 视图
│   └── services/             # 服务
├── utils/                    # 工具
├── config/                   # 配置
├── resources/                # 资源
├── main.py                   # 主入口
├── requirements.txt          # 依赖
└── README.md                 # 说明
```

## 安装

1. 创建虚拟环境
   ```
   conda create -n dbmanager python=3.10
   conda activate dbmanager
   ```

2. 安装依赖
   ```
   pip install -r requirements.txt
   ```

3. 运行
   ```
   python main.py
   ```

## 开发计划

1. **MVP 阶段**：实现基本的连接管理、SQL 编辑和数据浏览功能
2. **功能增强**：添加导入导出、ER 图等高级功能
3. **性能优化**：优化大数据集处理和连接管理
4. **跨平台适配**：确保在 Windows、macOS 和 Linux 上正常运行
