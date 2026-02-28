# Financial Steward 后端

## 项目简介

基于 Python 的宏观经济周期自动判断与资产配置管理系统。通过 FastAPI 提供 RESTful API 和 WebSocket 智能体服务，涵盖：

- **经济周期分析**：采集 AKShare 宏观经济数据（M1、M2、PMI、CPI、PPI、社融等），自动判断当前经济周期阶段
- **资产配置管理**：持仓管理、基金/ETF T-1 净值同步、目标权重与再平衡建议
- **智能体对话**：基于 LLM 的 WebSocket 智能体，支持持仓查询、调仓建议、周期判断、指数行情、联网搜索

## 项目结构

```
backend/
├── src/
│   ├── api/
│   │   ├── main.py            # FastAPI 应用入口 & 路由定义
│   │   └── schemas.py         # Pydantic 请求/响应模型
│   ├── agent/
│   │   ├── agent.py           # 智能体会话管理
│   │   ├── llm_client.py      # LLM 客户端
│   │   ├── strategy.py        # 智能体策略
│   │   └── tools.py           # 智能体工具集
│   ├── portfolio/
│   │   ├── models.py          # SQLAlchemy 数据模型
│   │   ├── db.py              # 数据库连接
│   │   ├── init_db.py         # 表结构初始化 & 种子数据
│   │   ├── service.py         # 业务逻辑层
│   │   ├── rebalance.py       # 再平衡计算
│   │   ├── rebalance_plan.py  # 再平衡计划管理
│   │   ├── scheduler.py       # 后台定时任务
│   │   ├── price_sync.py      # 净值同步
│   │   ├── price_provider.py  # 行情数据接口
│   │   └── price_provider_akshare.py
│   ├── collector.py           # 宏观数据采集器
│   ├── analyzer.py            # 经济周期分析器
│   ├── monitor.py             # 定时监控（CLI）
│   ├── visualizer.py          # 可视化（CLI）
│   └── env.py                 # 环境变量加载
├── config.py                  # 全局配置
├── main.py                    # 经济周期分析 CLI 入口
├── portfolio_cli.py           # 资产配置 CLI 工具
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
└── .env.development           # 开发环境配置
```

## 快速开始

### 1. 安装依赖

```bash
cd backend

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

### 2. 配置环境变量

复制 `.env.example` 并修改：

```bash
cp .env.example .env.development
```

必填项：

```
ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://user:password@host:3306/financial_steward
LLM_API_KEY=your_api_key
```

### 3. 启动服务

```bash
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

服务启动时会自动完成数据库表结构初始化和种子数据写入，并启动后台定时任务调度器。

访问 `http://localhost:8000/health` 确认服务正常运行。

## 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENVIRONMENT` | 环境名称，决定加载 `.env.{ENVIRONMENT}` | `development` |
| `DATABASE_URL` | MySQL 连接串 | — |
| `PORTFOLIO_DB_HOST` | 数据库主机（不使用 DATABASE_URL 时） | `127.0.0.1` |
| `PORTFOLIO_DB_PORT` | 数据库端口 | `3306` |
| `PORTFOLIO_DB_USER` | 数据库用户 | `root` |
| `PORTFOLIO_DB_PASSWORD` | 数据库密码 | — |
| `PORTFOLIO_DB_NAME` | 数据库名 | `financial_steward` |
| `PORTFOLIO_CORS_ORIGINS` | CORS 允许来源（逗号分隔） | `*` |
| `PORTFOLIO_SCHEDULER_ENABLED` | 启用后台调度器 | `true` |
| `PORTFOLIO_SCHEDULER_INTERVAL` | 调度器轮询间隔（秒） | `60` |
| `LLM_PROVIDER` | LLM 提供商 | `openai_compatible` |
| `LLM_MODEL` | 模型名称 | `qwen-max` |
| `LLM_BASE_URL` | LLM API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_API_KEY` | LLM API 密钥 | — |
| `LLM_ENABLE_RESPONSE_FORMAT` | 启用 JSON mode | `false` |
| `SEARCH_BASE_URL` | SearXNG 搜索服务地址 | `http://localhost:8080` |

## API 接口

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务健康检查 |

### 基金管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/funds` | 创建/更新基金（含周期权重） |
| GET | `/funds` | 获取全部基金及周期权重 |
| PUT | `/funds/{fund_id}` | 更新基金信息 |

### 持仓管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/holdings` | 创建/更新持仓（份额、成本） |

### 现金管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/cash/deposit` | 存入现金 |
| POST | `/cash/withdraw` | 取出现金 |

### 交易记录

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/transactions` | 创建交易记录 |

### 周期目标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/cycles/targets` | 获取四周期目标权重 |
| PUT | `/cycles/targets` | 更新周期目标权重 |

### 组合设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/settings` | 获取组合参数 |
| PUT | `/settings` | 更新组合参数（再平衡频率、阈值、现金比例、DCA 批次） |

### 组合总览 & 再平衡

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/portfolio/summary` | 获取组合总览（总资产、现金、周期分布、基金偏离） |
| POST | `/portfolio/rebalance` | 生成再平衡计划（可选持久化） |
| GET | `/portfolio/rebalance/{plan_id}` | 查看再平衡计划详情 |
| POST | `/portfolio/rebalance/{plan_id}/execute/{batch_no}` | 执行指定批次 |
| POST | `/portfolio/rebalance/{plan_id}/recalculate` | 重新计算剩余批次 |
| POST | `/portfolio/rebalance/mark-due` | 标记到期批次为就绪 |

### 净值同步

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/prices/sync` | 同步全部基金/ETF 的 T-1 净值 |

### Prompt 模板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/prompts/{name}` | 获取 Prompt 模板 |
| PUT | `/prompts` | 创建/更新 Prompt 模板 |

### 智能体 WebSocket

| 协议 | 路径 | 说明 |
|------|------|------|
| WS | `/ws/agent` | 智能体对话（流式消息 + 工具调用） |

智能体内置工具：

- `get_portfolio_summary` — 资产配置概览
- `get_rebalance_suggestion` — 调仓建议
- `get_cycle_targets` — 周期目标权重
- `get_settings` — 组合参数
- `get_fund_list` — 基金列表
- `get_economic_cycle` — 经济周期判断
- `get_index_data` — 指数行情查询（A股 / 港股 / 债券）
- `web_search` — 联网搜索

## 智能体 LLM 配置

默认使用 Qwen Max（OpenAI 兼容模式），支持任何 OpenAI 兼容的模型服务：

```bash
# Qwen Max（默认）
LLM_PROVIDER=openai_compatible
LLM_MODEL=qwen-max
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# DeepSeek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# Kimi (Moonshot)
LLM_PROVIDER=kimi
LLM_MODEL=your_kimi_model_id
LLM_BASE_URL=https://api.moonshot.ai/v1

# MiniMax
LLM_PROVIDER=minimax
LLM_MODEL=MiniMax-M2.1
LLM_BASE_URL=https://api.minimax.io/v1
```

若模型支持 JSON mode，可设置 `LLM_ENABLE_RESPONSE_FORMAT=true`。

## 联网搜索（SearXNG）

```bash
docker compose -f docker-compose.searxng.yml up -d
```

配置：

```
SEARCH_BASE_URL=http://localhost:8080
```

## CLI 工具

除 API 服务外，项目保留了命令行工具用于快速调试和独立运行：

### 经济周期分析

```bash
python main.py                         # 单次分析
python main.py --charts                # 分析并生成图表
python main.py --monitor               # 启动定时监控（默认每 7 天）
python main.py --monitor --interval 3  # 自定义监控间隔
```

### 资产配置管理

```bash
python portfolio_cli.py init-db     # 初始化数据库表结构
python portfolio_cli.py sync-nav    # 同步基金/ETF T-1 净值
python portfolio_cli.py rebalance   # 生成再平衡建议
```

## 配置说明

`config.py` 中的主要配置项：

| 配置组 | 说明 |
|--------|------|
| `DATA_COLLECTION_CONFIG` | 数据采集配置（重试次数、延迟） |
| `MONITOR_CONFIG` | 定时监控配置（间隔、执行时间） |
| `VISUALIZATION_CONFIG` | 可视化配置（分辨率、字体） |
| `CYCLE_THRESHOLDS` | 经济周期判断阈值 |
| `PORTFOLIO_DB` | 数据库连接配置 |
| `PORTFOLIO_DEFAULTS` | 资产配置默认参数（再平衡频率 180 天、阈值 5%、现金比例 5%、DCA 4 批） |

## 注意事项

1. **数据库**：需要 MySQL 实例，服务启动时自动建表和初始化种子数据
2. **网络连接**：需要访问 AKShare 数据源获取宏观数据和基金净值
3. **数据更新频率**：宏观经济数据按月更新，基金净值为 T-1
4. **API 限制**：AKShare 可能有频率限制，系统已内置重试和延迟机制
5. **API 版本**：已适配 AKShare 1.18.8+，如遇 API 错误请查看 [API_UPDATE.md](API_UPDATE.md)
6. **字体问题**：CLI 图表中文显示异常时，请安装中文字体或修改 `config.py` 中的字体配置

## 理论基础

- [经济周期判断理论](../docs/cycle-theory.md) — 核心原理和理论依据

## 许可证

MIT License
