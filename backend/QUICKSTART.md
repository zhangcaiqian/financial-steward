# 快速开始指南

## 🚀 5分钟快速上手

### 步骤1：创建并激活虚拟环境

**macOS/Linux:**
```bash
cd backend

# 使用自动安装脚本（推荐）
./setup.sh

# 或手动安装
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

**Windows:**
```bash
cd backend

# 使用自动安装脚本（推荐）
setup.bat

# 或手动安装
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
```

### 步骤2：运行示例

```bash
# 确保虚拟环境已激活（提示符前会显示 (venv)）

# 运行快速示例
python example.py
```

### 步骤3：执行分析

```bash
# 执行单次分析
python main.py

# 执行分析并生成图表
python main.py --charts

# 启动定时监控（每7天执行一次）
python main.py --monitor
```

## 📊 输出结果

### 控制台输出
运行后会在控制台显示：
- 数据采集进度
- 各指标分析结果
- 经济周期判断
- 资产配置建议

示例输出：
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

### 文件输出

**报告文件** (`reports/` 目录)：
- `YYYYMMDD_HHMMSS_cycle_report.json` - JSON格式的分析报告

**图表文件** (使用 `--charts` 参数时)：
- `m1_pmi_trend.png` - M1和PMI趋势图
- `cycle_dashboard.png` - 经济周期仪表盘
- `all_indicators.png` - 所有指标综合图表

**日志文件** (`logs/` 目录)：
- `app.log` - 应用运行日志
- `monitor.log` - 监控系统日志

## 🔧 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# 查看帮助
python main.py --help

# 单次分析
python main.py

# 生成图表
python main.py --charts

# 启动监控
python main.py --monitor

# 自定义监控间隔（每3天）
python main.py --monitor --interval 3

# 退出虚拟环境
deactivate
```

## 💡 使用技巧

### 1. 定期执行
建议每周执行一次分析，宏观数据通常按月更新。

### 2. 保存历史报告
所有报告都会自动保存在 `reports/` 目录，可用于回溯分析。

### 3. 自定义分析
修改 `src/analyzer.py` 中的判断逻辑，调整阈值和权重。

### 4. 添加数据源
在 `src/collector.py` 中添加新的数据获取方法。

## ⚠️ 常见问题

### Q1: 虚拟环境激活失败？
```bash
# 确保在 backend 目录下
cd backend

# 重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

### Q2: 数据获取失败？
- 检查网络连接
- 等待1-2分钟后重试（可能是频率限制）
- 更新 AKShare: `pip install akshare --upgrade`

### Q3: 中文显示乱码？
- 安装中文字体
- 修改 `config.py` 中的字体配置

### Q4: 如何更新依赖？
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## 📚 更多信息

- 详细文档：[README.md](README.md)
- 设计文档：[../docs/auto-cycle-judge.md](../docs/auto-cycle-judge.md)
- 代码示例：[example.py](example.py)

## 🎉 开始使用

现在你已经准备好了！运行 `python example.py` 开始你的第一次经济周期分析吧！

