# 经济周期自动判断系统

基于宏观经济指标的智能周期判断与资产配置建议系统。

## 📋 项目简介

本系统通过采集和分析多个宏观经济指标（M1、M2、PMI、CPI、PPI、社融等），自动判断当前经济周期阶段，并提供相应的资产配置建议。

## ✨ 主要功能

- ✅ **自动数据采集**：从AKShare获取最新宏观经济数据
- ✅ **智能周期判断**：基于多指标综合判断（强复苏、弱复苏、弱衰退、强衰退、混沌期）
- ✅ **配置建议**：根据周期自动生成资产配置建议
- ✅ **定时监控**：支持自动定时执行分析任务
- ✅ **数据可视化**：生成各类经济指标趋势图表
- ✅ **报告生成**：自动生成JSON格式分析报告

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd business-cycle-conf
```

### 2. 安装环境

```bash
cd backend

# macOS/Linux 使用自动安装脚本
./setup.sh

# Windows 使用批处理脚本
setup.bat
```

### 3. 运行示例

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate.bat  # Windows

# 运行快速示例
python example.py

# 执行单次分析
python main.py
```

详细使用说明请查看：[快速开始指南](backend/QUICKSTART.md)

### 资产配置管理前端

```bash
cd frontend
pnpm install
pnpm run dev
```

默认前端代理 `http://localhost:8000` 的 API。

### 资产配置管理 API

```bash
cd backend
uvicorn src.api.main:app --reload --port 8000
```

## 📂 项目结构

```
business-cycle-conf/
├── docs/                           # 文档目录
│   └── auto-cycle-judge.md        # 设计文档
├── backend/                        # 后端目录
│   ├── src/                       # 核心模块
│   │   ├── collector.py           # 数据采集器
│   │   ├── analyzer.py            # 周期分析器
│   │   ├── monitor.py             # 监控系统
│   │   └── visualizer.py          # 可视化模块
│   ├── data/                      # 数据目录
│   │   ├── raw/                   # 原始数据
│   │   └── processed/             # 处理后数据
│   ├── reports/                   # 分析报告
│   ├── logs/                      # 日志文件
│   ├── config.py                  # 配置文件
│   ├── main.py                    # 主程序入口
│   ├── example.py                 # 使用示例
│   ├── test_env.py                # 环境测试
│   ├── setup.sh                   # Linux/macOS安装脚本
│   ├── setup.bat                  # Windows安装脚本
│   ├── requirements.txt           # 依赖列表
│   ├── README.md                  # 后端说明
│   └── QUICKSTART.md              # 快速开始指南
└── README.md                      # 项目说明（本文件）
```

## 📊 周期判断逻辑

系统综合以下指标进行判断：

| 指标 | 说明 | 数据源 |
|------|------|--------|
| **M1** | 狭义货币供应量 | 央行数据 |
| **M2** | 广义货币供应量 | 央行数据 |
| **PMI** | 制造业采购经理指数 | 国家统计局 |
| **CPI** | 居民消费价格指数 | 国家统计局 |
| **PPI** | 工业生产者出厂价格指数 | 国家统计局 |
| **社融** | 社会融资规模 | 央行数据 |

**判断结果：**
- **强复苏**：M1上行 + PMI扩张 + CPI/PPI同步上行 + 社融上行
- **弱复苏**：PMI扩张 + M1混沌/上行
- **弱衰退**：PMI收缩或混沌 + M1混沌/下行
- **强衰退**：M1下行 + PMI收缩 + CPI/PPI同步下行 + 社融下行
- **混沌期**：无法明确判断

## 💡 使用场景

1. **个人投资者**：定期了解经济周期，调整资产配置
2. **金融机构**：辅助投资决策，提供宏观分析参考
3. **研究机构**：宏观经济研究，历史数据回测
4. **自动化交易**：作为量化策略的信号源之一

## 🛠️ 技术栈

- **数据采集**：AKShare
- **数据处理**：Pandas、NumPy
- **可视化**：Matplotlib
- **定时任务**：Schedule
- **语言**：Python 3.8+

## 📖 文档

- [后端说明](backend/README.md) - 详细的后端使用文档
- [快速开始](backend/QUICKSTART.md) - 5分钟快速上手指南
- [设计文档](docs/auto-cycle-judge.md) - 完整的系统设计方案

## 🔧 环境要求

- Python 3.8 或更高版本
- 稳定的网络连接（用于获取数据）
- 推荐使用虚拟环境

## 📝 示例输出

```
============================================================
📊 经济指标信号分析
============================================================
M1趋势:     上行
PMI状态:    扩张 (当前值: 51.2)
CPI/PPI:    同步上行
社融趋势:   上行
============================================================

🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
📅 判断时间: 2024-01-15 10:30:00
📊 当前经济周期: 【弱复苏】
============================================================
💰 资产配置建议:
  股票: 中证500(12%) + 中证1000(12%) + 科创50(8%)
  债券: 维持30%

💡 说明: 产业周期爆发，中小盘科技成长股表现优异
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
```

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，决策需谨慎。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

- [经济周期判断理论](docs/cycle-theory.md) - **为什么这个方法有效？核心原理是什么？**
- [设计文档](docs/auto-cycle-judge.md) - 完整的系统设计方案
- [API 更新说明](backend/API_UPDATE.md) - AKShare API 变更记录
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [Pandas 文档](https://pandas.pydata.org/)
- [Matplotlib 文档](https://matplotlib.org/)

---

**开始使用：** `cd backend && ./setup.sh && python example.py`
