# CalcFlow Calculator Backend

第一次作业的独立后端仓库。对应[老师发布的作业要求](https://bbs.csdn.net/topics/620530837)。

配套项目：[前端仓库](https://github.com/grrrced/calculator_frontend)。

后端提供 HTTP JSON API，负责输入校验、表达式解析、计算、错误处理和 SQLite 历史持久化。前端通过 HTTP 调用接口，不直接访问数据库。

## 环境与启动

- Python 3.9+，macOS、Linux 或 Windows 均可。
- 仅使用 Python 标准库，不需要安装第三方包或单独安装数据库服务。

下载或克隆本仓库后，在**本仓库根目录**（可以看到 `server.py`、`calculator.py` 的目录）执行：

```bash
python3 server.py
```

默认监听 `http://127.0.0.1:8000`。首次启动会自动创建 `data/` 目录、`data/calculator.sqlite3` 文件和 `calculation_history` 表，无需手动导入数据库。保留数据库文件即可在服务重启后保留历史。按 `Ctrl+C` 停止服务。

## 配置

| 环境变量 | 默认值 | 用途 |
| --- | --- | --- |
| `CALCULATOR_HOST` | `127.0.0.1` | 监听地址；需要外部访问时设为 `0.0.0.0` |
| `CALCULATOR_PORT` | `8000` | HTTP 监听端口 |
| `CALCULATOR_DB_PATH` | 本仓库下的 `data/calculator.sqlite3` | SQLite 数据库路径；所在目录需可写 |

macOS/Linux 示例，在仓库根目录执行：

```bash
CALCULATOR_HOST=0.0.0.0 CALCULATOR_PORT=8000 CALCULATOR_DB_PATH=./data/calculator.sqlite3 python3 server.py
```

相对数据库路径相对于启动命令的当前目录解析；线上建议使用持久卷中的绝对路径。云平台如提供 `PORT` 环境变量，需要在启动命令中将它映射到 `CALCULATOR_PORT`：

```bash
CALCULATOR_HOST=0.0.0.0 CALCULATOR_PORT="$PORT" python3 server.py
```

仅在平台确实提供 `PORT` 时使用上述命令。`0.0.0.0` 用于监听，实际访问时应使用服务器 IP 或部署平台分配的域名。

## API

所有响应均为 JSON。当前实现支持 CORS，允许前端从不同来源调用，并处理 `OPTIONS` 预检请求。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/calculate` | 计算表达式，成功后写入 SQLite |
| `GET` | `/api/history?limit=100` | 按最新优先查询；默认 100 条，数量限制在 1–500 条 |
| `DELETE` | `/api/history/{id}` | 删除指定历史记录 |
| `DELETE` | `/api/history` | 清空全部历史记录 |

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

返回：

```json
{"success": true, "service": "calculator-backend"}
```

提交计算：

```bash
curl -X POST http://127.0.0.1:8000/api/calculate \
  -H 'Content-Type: application/json' \
  -d '{"expression":"(1+2)*3"}'
```

成功返回 HTTP `201`，字段为 `success`、`id`、`expression`、`result`、`createdAt`；本例的 `result` 为 `9`，`id` 和 UTC 时间戳由后端生成。

历史查询返回 `{"success":true,"items":[...]}`，每条记录包含 `id`、`expression`、`result`、`createdAt`。非法表达式、除零、无效 JSON 或不合规参数返回 HTTP `400`，格式为 `{"success":false,"message":"错误说明"}`。不存在的接口或记录返回 HTTP `404`。

## 数据与部署

SQLite 数据文件、运行缓存和本地环境配置由 `.gitignore` 排除，不提交到 GitHub。新克隆的仓库会在启动时自动生成空数据库。

线上部署必须把 `CALCULATOR_DB_PATH` 指向可写的**持久卷或持久磁盘**，才能在平台重启、重建或重新部署后保存历史。平台的临时文件系统不能保证保留 SQLite 数据；GitHub 仓库也不会替代数据库存储。

前端部署后，在其 `index.html` 中加载 `app.js` 之前设置 `window.CALCULATOR_API_BASE` 为实际后端地址加 `/api`。HTTPS 前端应使用 HTTPS 后端，可由部署平台或反向代理提供 HTTPS。本仓库的 `server.py` 提供 HTTP 服务。

本项目是课程演示应用，历史记录共用一张表，接口未实现用户登录和权限隔离。部署后的调用者可读取和删除共享历史。

## 测试

在本仓库根目录执行：

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖优先级、括号、小数、一元正负号、非法表达式和除零。可另用上述 `curl` 命令检查实际 HTTP 服务。

## 目录与设计

```text
.
├── .gitignore
├── README.md
├── codestyle.md           # 代码规范
├── server.py              # HTTP 路由、JSON 和 CORS
├── calculator.py          # 表达式解析与计算
├── database.py            # SQLite 初始化和历史 CRUD
├── tests/
│   └── test_calculator.py # 计算逻辑单元测试
└── data/                  # 运行时自动生成，不提交
    └── calculator.sqlite3
```

`calculator.py` 使用递归下降语法 `expression → term → unary → primary`，由语法结构处理优先级、括号和一元正负号，不使用 `eval` 或 `exec`。`database.py` 使用参数化 SQL 存取表达式、结果和 UTC 创建时间。
