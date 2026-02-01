# 经济周期自动判断系统 - 后端

## 项目简介

这是一个基于Python的宏观经济周期自动判断系统，通过采集和分析多个宏观经济指标（M1、M2、PMI、CPI、PPI、社融等），自动判断当前经济周期阶段，并提供相应的资产配置建议。

同时提供 **资产配置管理模块（Portfolio）**，用于录入持仓、同步基金/ETF净值（T-1）、计算目标权重与再平衡建议。

## 功能特性

- ✅ **数据采集**：自动从AKShare获取宏观经济数据
- ✅ **周期分析**：基于多指标综合判断经济周期（强复苏、弱复苏、弱衰退、强衰退、混沌期）
- ✅ **自动监控**：支持定时任务，自动执行分析
- ✅ **数据可视化**：生成各类经济指标的趋势图表
- ✅ **报告生成**：自动生成JSON格式的分析报告
- ✅ **错误处理**：完善的错误处理和重试机制
- ✅ **资产配置管理**：MySQL持仓管理 + AKShare T-1净值同步 + 再平衡建议

## 项目结构

```
backend/
├── src/
│   ├── collector.py      # 数据采集器
│   ├── analyzer.py       # 周期分析器
│   ├── monitor.py        # 监控系统
│   └── visualizer.py     # 可视化模块
│   └── portfolio/        # 资产配置模块
├── data/
│   ├── raw/              # 原始数据
│   └── processed/        # 处理后数据
├── reports/              # 分析报告
├── logs/                 # 日志文件
├── config.py             # 配置文件
├── main.py               # 主程序入口
├── requirements.txt      # 依赖列表
├── portfolio_cli.py      # 资产配置CLI入口
└── README.md             # 说明文档
```

## 环境搭建

### 方法一：使用自动安装脚本（推荐）

**macOS/Linux:**
```bash
cd backend
./setup.sh
```

**Windows:**
```bash
cd backend
setup.bat
```

### 方法二：手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装依赖（推荐使用阿里云镜像加速）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

## 使用方法

**⚠️ 注意：运行前请先激活虚拟环境**

```bash
# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat
```

### 1. 单次分析

```bash
# 执行单次分析
python main.py

# 执行分析并生成图表
python main.py --charts
```

### 2. 定时监控

```bash
# 启动定时监控（默认每7天执行一次）
python main.py --monitor

# 自定义监控间隔（每3天执行一次）
python main.py --monitor --interval 3
```

### 3. 运行示例代码

```bash
# 运行快速开始示例
python example.py
```

### 4. 作为模块使用

```python
from src.collector import MacroDataCollector
from src.analyzer import EconomicCycleAnalyzer

# 采集数据
collector = MacroDataCollector()
data = collector.collect_all()

# 分析周期
analyzer = EconomicCycleAnalyzer(data)
report = analyzer.generate_report()
analyzer.print_report()
```

### 5. 退出虚拟环境

```bash
deactivate
```

## 资产配置管理（Portfolio）

### 1. 数据库配置

通过环境变量配置 MySQL 连接：

```
PORTFOLIO_DB_HOST=127.0.0.1
PORTFOLIO_DB_PORT=3306
PORTFOLIO_DB_USER=root
PORTFOLIO_DB_PASSWORD=your_password
PORTFOLIO_DB_NAME=financial_steward
```

系统会按 `ENVIRONMENT` 变量加载 `.env.{ENVIRONMENT}`，若不存在则加载 `.env`。
已提供示例：`.env.development`、`.env.production`、`.env.example`（可按需复制修改）。

可选环境变量：

```
PORTFOLIO_DB_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
PORTFOLIO_CORS_ORIGINS=http://localhost:5173
PORTFOLIO_SCHEDULER_ENABLED=true
PORTFOLIO_SCHEDULER_INTERVAL=60
```

### 2. 初始化表结构

```bash
python portfolio_cli.py init-db
```

### 3. 同步基金/ETF T-1 净值

```bash
python portfolio_cli.py sync-nav
```

### 4. 生成再平衡建议（含分批买入）

```bash
python portfolio_cli.py rebalance
```

说明：
- ETF 使用 T-1 收盘价近似净值
- 买入侧按 4 批等分执行（可配置），卖出侧一次性执行

### 5. 启动 API 服务（FastAPI）

```bash
uvicorn src.api.main:app --reload --port 8000
```

启动时会自动检测并创建资产配置相关表结构。

### 6. 聊天录入（LLM 信息抽取）

支持 OpenAI / DeepSeek / Kimi / MiniMax 等 OpenAI 兼容模型。
需要配置 LLM 环境变量：

```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key
LLM_ENABLE_RESPONSE_FORMAT=false
```

说明：
- `LLM_PROVIDER=openai` 使用 Responses API + JSON Schema
- 其他 provider 使用 `POST /chat/completions`（OpenAI 兼容）
- 如果你的模型支持 JSON mode，可设置 `LLM_ENABLE_RESPONSE_FORMAT=true`

示例（OpenAI 兼容）：

```
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

# 自定义 OpenAI 兼容服务
LLM_PROVIDER=openai_compatible
LLM_MODEL=your_model_id
LLM_BASE_URL=https://your-openai-compatible-domain/v1
```

## 配置说明

主要配置在 `config.py` 文件中：

- `DATA_COLLECTION_CONFIG`: 数据采集配置（重试次数、延迟等）
- `MONITOR_CONFIG`: 监控配置（间隔时间、执行时间等）
- `VISUALIZATION_CONFIG`: 可视化配置（图表分辨率、字体等）
- `CYCLE_THRESHOLDS`: 周期判断阈值配置

## 输出说明

### 报告文件

分析报告保存在 `reports/` 目录下，文件名格式：`YYYYMMDD_HHMMSS_cycle_report.json`

报告内容示例：
```json
{
  "判断时间": "2024-01-15 10:30:00",
  "经济周期": "弱复苏",
  "配置建议": {
    "股票配置": "中证500(12%) + 中证1000(12%) + 科创50(8%)",
    "债券配置": "维持30%",
    "说明": "产业周期爆发，中小盘科技成长股表现优异"
  }
}
```

### 图表文件

如果使用 `--charts` 参数，会生成以下图表：
- `m1_pmi_trend.png`: M1和PMI趋势图
- `cycle_dashboard.png`: 经济周期仪表盘
- `all_indicators.png`: 所有指标综合图表

## 日志说明

日志文件保存在 `logs/` 目录下：
- `app.log`: 应用主日志
- `monitor.log`: 监控系统日志（如果使用监控功能）

## 注意事项

1. **网络连接**：需要稳定的网络连接访问AKShare数据源
2. **数据更新频率**：宏观经济数据通常按月更新，建议监控间隔设置为7天或更长
3. **字体问题**：如果图表中文显示异常，请安装中文字体或修改 `config.py` 中的字体配置
4. **API限制**：AKShare可能有频率限制，系统已内置重试和延迟机制
5. **API版本**：本项目已适配 AKShare 1.18.8+，如遇到API错误，请查看 [API_UPDATE.md](API_UPDATE.md)

## 常见问题

### Q1: 数据获取失败怎么办？

A: 系统已内置重试机制，如果仍然失败，请检查：
- 网络连接是否正常
- AKShare服务是否可用
- 是否需要更新AKShare版本

### Q2: 如何修改判断逻辑？

A: 修改 `src/analyzer.py` 中的 `judge_cycle()` 方法，调整各指标的判断条件。

### Q3: 如何添加新的数据源？

A: 在 `src/collector.py` 中添加新的数据获取方法，然后在 `collect_all()` 中调用。

## 理论基础

想了解为什么这个方法能判断经济周期？请阅读：
- 📚 [经济周期判断理论](../docs/cycle-theory.md) - 详细解释核心原理和理论依据

## 后续扩展

- [ ] Web API接口（Flask/FastAPI）
- [ ] 机器学习预测模型
- [ ] 微信/邮件通知功能
- [ ] 历史回测功能

## 许可证

MIT License
