# 经济周期自动判断系统完整方案

## 一、数据源选择与对比

### 📊 主流数据接口库对比

| 特性           | AKShare       | Tushare Pro         | 东方财富/乐咕乐股 | 国家统计局    |
| -------------- | ------------- | ------------------- | ----------------- | ------------- |
| **免费程度**   | ✅ 完全免费   | ⚠️ 需积分(部分收费) | ✅ 免费网页数据   | ✅ 完全免费   |
| **宏观数据**   | ✅ 非常全     | ✅ 全面             | ⚠️ 部分           | ✅ 最权威     |
| **易用性**     | ✅✅ 极简 API | ✅ API 标准化       | ⚠️ 需爬虫         | ⚠️ 需爬虫     |
| **更新频率**   | ✅ 实时更新   | ✅ T+1 更新         | ✅ 实时           | ⚠️ 月度       |
| **数据可靠性** | ✅ 来自权威源 | ✅✅ 最可靠         | ✅ 可靠           | ✅✅ 官方数据 |
| **限制**       | ⚠️ 频率限制   | ⚠️ 积分限制         | ⚠️ IP 限制        | -             |
| **推荐指数**   | ⭐⭐⭐⭐⭐    | ⭐⭐⭐⭐            | ⭐⭐⭐            | ⭐⭐⭐        |

### 🎯 推荐方案：**AKShare 为主 + 官方数据为辅**

**理由：**

1. AKShare 是基于 Python 的财经数据接口库，目的是实现对股票、期货、期权、基金、外汇、债券、指数、加密货币等金融产品的基本面数据、实时和历史行情数据、衍生数据从数据采集、数据清洗到数据落地的一套工具
2. 完全免费，无积分限制
3. API 简洁，每个接口都有详细文档
4. 数据来源权威（东方财富、新浪财经等）

---

## 二、环境搭建

### 1. 安装依赖

```bash
# 安装AKShare（推荐使用阿里云镜像加速）
pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com --upgrade

# 安装数据处理库
pip install pandas numpy matplotlib

# 可选：安装Tushare Pro（如需更高质量数据）
pip install tushare
```

### 2. 快速验证

```python
import akshare as ak

# 测试获取M1数据
try:
    df = ak.macro_china_m1()
    print("✅ AKShare安装成功!")
    print(df.tail())
except Exception as e:
    print(f"❌ 错误: {e}")
```

---

## 三、核心指标数据获取

### 📋 指标与接口对应表

| 指标         | AKShare 接口                 | 数据说明               | 更新频率 |
| ------------ | ---------------------------- | ---------------------- | -------- |
| **M1**       | `ak.macro_china_m1()`        | 狭义货币供应量         | 月度     |
| **M2**       | `ak.macro_china_m2()`        | 广义货币供应量         | 月度     |
| **社融**     | `ak.macro_china_shrzgm()`    | 社会融资规模存量       | 月度     |
| **PMI**      | `ak.macro_china_pmi()`       | 制造业采购经理指数     | 月度     |
| **CPI**      | `ak.macro_china_cpi()`       | 居民消费价格指数       | 月度     |
| **PPI**      | `ak.macro_china_ppi()`       | 工业生产者出厂价格指数 | 月度     |
| **GDP**      | `ak.macro_china_gdp()`       | 国内生产总值           | 季度     |
| **企业利润** | `ak.macro_china_qy_profit()` | 工业企业利润           | 月度     |

### 💻 完整数据获取代码

```python
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class MacroDataCollector:
    """宏观经济数据采集器"""

    def __init__(self):
        self.data = {}

    def get_m1_m2(self):
        """获取M1和M2数据"""
        try:
            # M1
            m1_df = ak.macro_china_m1()
            m1_df = m1_df.rename(columns={'同比': 'M1同比'})

            # M2
            m2_df = ak.macro_china_m2()
            m2_df = m2_df.rename(columns={'同比': 'M2同比'})

            # 合并
            df = pd.merge(m1_df[['月份', 'M1同比']],
                         m2_df[['月份', 'M2同比']],
                         on='月份', how='outer')

            self.data['M1_M2'] = df
            print("✅ M1/M2数据获取成功")
            return df
        except Exception as e:
            print(f"❌ M1/M2数据获取失败: {e}")
            return None

    def get_shrzgm(self):
        """获取社融数据"""
        try:
            df = ak.macro_china_shrzgm()
            # 提取存量和增量数据
            df = df[df['指标'].isin(['社会融资规模存量', '社会融资规模增量'])]
            self.data['社融'] = df
            print("✅ 社融数据获取成功")
            return df
        except Exception as e:
            print(f"❌ 社融数据获取失败: {e}")
            return None

    def get_pmi(self):
        """获取PMI数据"""
        try:
            df = ak.macro_china_pmi()
            # 制造业PMI
            df_manu = df[df['指标'] == '制造业']
            self.data['PMI'] = df_manu
            print("✅ PMI数据获取成功")
            return df_manu
        except Exception as e:
            print(f"❌ PMI数据获取失败: {e}")
            return None

    def get_cpi_ppi(self):
        """获取CPI和PPI数据"""
        try:
            # CPI
            cpi_df = ak.macro_china_cpi()
            cpi_df = cpi_df[cpi_df['指标'] == 'CPI同比']

            # PPI
            ppi_df = ak.macro_china_ppi()
            ppi_df = ppi_df[ppi_df['指标'] == 'PPI同比']

            self.data['CPI'] = cpi_df
            self.data['PPI'] = ppi_df
            print("✅ CPI/PPI数据获取成功")
            return cpi_df, ppi_df
        except Exception as e:
            print(f"❌ CPI/PPI数据获取失败: {e}")
            return None, None

    def get_gdp(self):
        """获取GDP数据"""
        try:
            df = ak.macro_china_gdp()
            self.data['GDP'] = df
            print("✅ GDP数据获取成功")
            return df
        except Exception as e:
            print(f"❌ GDP数据获取失败: {e}")
            return None

    def collect_all(self):
        """一键获取所有数据"""
        print("开始采集宏观数据...")
        print("=" * 50)

        self.get_m1_m2()
        self.get_shrzgm()
        self.get_pmi()
        self.get_cpi_ppi()
        self.get_gdp()

        print("=" * 50)
        print("✅ 数据采集完成!")
        return self.data

# 使用示例
if __name__ == "__main__":
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 查看最近3个月数据
    print("\n📊 最近3个月PMI数据:")
    print(data['PMI'].tail(3))
```

---

## 四、经济周期判断算法

### 🔍 判断逻辑实现

```python
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple

class EconomicCycleAnalyzer:
    """经济周期分析器"""

    def __init__(self, data: Dict):
        self.data = data
        self.cycle_result = None

    def analyze_m1_trend(self) -> str:
        """分析M1趋势"""
        df = self.data.get('M1_M2')
        if df is None or len(df) < 3:
            return "数据不足"

        recent_m1 = df['M1同比'].tail(3).values

        # 判断趋势：连续2个月上涨为上行
        if recent_m1[-1] > recent_m1[-2] and recent_m1[-2] > recent_m1[-3]:
            return "上行"
        elif recent_m1[-1] < recent_m1[-2] and recent_m1[-2] < recent_m1[-3]:
            return "下行"
        else:
            return "混沌"

    def analyze_pmi_status(self) -> Tuple[str, float]:
        """分析PMI状态"""
        df = self.data.get('PMI')
        if df is None or len(df) < 3:
            return "数据不足", 0

        recent_pmi = df['值'].tail(3).values
        latest_pmi = recent_pmi[-1]

        # PMI > 50为扩张，< 50为收缩
        if all(recent_pmi > 50.5):
            return "强扩张", latest_pmi
        elif all(recent_pmi > 50):
            return "扩张", latest_pmi
        elif all(recent_pmi < 50):
            return "收缩", latest_pmi
        else:
            return "混沌", latest_pmi

    def analyze_cpi_ppi_trend(self) -> str:
        """分析CPI和PPI趋势"""
        cpi_df = self.data.get('CPI')
        ppi_df = self.data.get('PPI')

        if cpi_df is None or ppi_df is None:
            return "数据不足"

        recent_cpi = cpi_df['值'].tail(3).values
        recent_ppi = ppi_df['值'].tail(3).values

        # 判断是否同步上行
        cpi_up = recent_cpi[-1] > recent_cpi[-2]
        ppi_up = recent_ppi[-1] > recent_ppi[-2]

        if cpi_up and ppi_up:
            return "同步上行"
        elif not cpi_up and not ppi_up:
            return "同步下行"
        else:
            return "分化"

    def analyze_shrzgm_trend(self) -> str:
        """分析社融趋势"""
        df = self.data.get('社融')
        if df is None:
            return "数据不足"

        # 提取存量同比数据
        存量df = df[df['指标'] == '社会融资规模存量']
        if len(存量df) < 3:
            return "数据不足"

        recent = 存量df['值'].tail(3).values

        if recent[-1] > recent[-2] > recent[-3]:
            return "上行"
        elif recent[-1] < recent[-2] < recent[-3]:
            return "下行"
        else:
            return "混沌"

    def judge_cycle(self) -> str:
        """综合判断经济周期"""

        # 收集各指标信号
        signals = {
            'M1': self.analyze_m1_trend(),
            'PMI': self.analyze_pmi_status(),
            'CPI_PPI': self.analyze_cpi_ppi_trend(),
            '社融': self.analyze_shrzgm_trend()
        }

        print("\n" + "="*60)
        print("📊 经济指标信号分析")
        print("="*60)
        print(f"M1趋势:     {signals['M1']}")
        print(f"PMI状态:    {signals['PMI'][0]} (当前值: {signals['PMI'][1]:.1f})")
        print(f"CPI/PPI:    {signals['CPI_PPI']}")
        print(f"社融趋势:   {signals['社融']}")
        print("="*60)

        # 判断逻辑
        m1 = signals['M1']
        pmi_status, pmi_value = signals['PMI']
        price = signals['CPI_PPI']
        shrzgm = signals['社融']

        # 强复苏判断
        if (m1 == "上行" and
            pmi_status in ["强扩张", "扩张"] and
            price == "同步上行" and
            shrzgm == "上行"):
            return "强复苏"

        # 强衰退判断
        if (m1 == "下行" and
            pmi_status == "收缩" and
            price == "同步下行" and
            shrzgm == "下行"):
            return "强衰退"

        # 弱复苏判断（宏观混沌但PMI扩张）
        if pmi_status in ["扩张", "强扩张"] and m1 in ["混沌", "上行"]:
            return "弱复苏"

        # 弱衰退判断（宏观混沌但PMI收缩）
        if pmi_status == "收缩" or (pmi_value < 50 and m1 in ["混沌", "下行"]):
            return "弱衰退"

        # 无法明确判断
        return "混沌期（建议均衡配置）"

    def generate_report(self) -> Dict:
        """生成完整报告"""
        cycle = self.judge_cycle()

        # 根据周期给出配置建议
        allocation_map = {
            "强复苏": {
                "股票配置": "沪深300(25%) + 消费50(8%) + 恒生科技(12%)",
                "债券配置": "减少至20%",
                "说明": "经济全面复苏，大盘核心资产和科技龙头受益"
            },
            "弱复苏": {
                "股票配置": "中证500(12%) + 中证1000(12%) + 科创50(8%)",
                "债券配置": "维持30%",
                "说明": "产业周期爆发，中小盘科技成长股表现优异"
            },
            "弱衰退": {
                "股票配置": "中证红利(25%) + 银行(8%)",
                "债券配置": "增加至35-40%",
                "说明": "高股息防御策略，债券增配"
            },
            "强衰退": {
                "股票配置": "减少股票至50%，增加现金和债券",
                "债券配置": "提升至40-50%",
                "说明": "极端防御，保留流动性"
            },
            "混沌期（建议均衡配置）": {
                "股票配置": "严格按债3股7均衡配置",
                "债券配置": "30%",
                "说明": "无法明确判断时，保持均衡是最优策略"
            }
        }

        report = {
            "判断时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "经济周期": cycle,
            "配置建议": allocation_map.get(cycle, allocation_map["混沌期（建议均衡配置）"])
        }

        self.cycle_result = report
        return report

    def print_report(self):
        """打印报告"""
        if self.cycle_result is None:
            self.generate_report()

        report = self.cycle_result

        print("\n" + "🎯"*30)
        print(f"📅 判断时间: {report['判断时间']}")
        print(f"📊 当前经济周期: 【{report['经济周期']}】")
        print("="*60)
        print("💰 资产配置建议:")
        print(f"  股票: {report['配置建议']['股票配置']}")
        print(f"  债券: {report['配置建议']['债券配置']}")
        print(f"\n💡 说明: {report['配置建议']['说明']}")
        print("🎯"*30 + "\n")

# 完整使用示例
if __name__ == "__main__":
    # 1. 采集数据
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 2. 分析周期
    analyzer = EconomicCycleAnalyzer(data)

    # 3. 生成报告
    analyzer.print_report()
```

---

## 五、自动化监控系统

### 🤖 定时监控脚本

```python
import schedule
import time
from datetime import datetime
import json
import os

class EconomicCycleMonitor:
    """经济周期自动监控系统"""

    def __init__(self, output_dir="./cycle_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.history = []

    def run_analysis(self):
        """执行分析"""
        try:
            print(f"\n⏰ 开始执行周期分析 - {datetime.now()}")

            # 1. 采集数据
            collector = MacroDataCollector()
            data = collector.collect_all()

            # 2. 分析周期
            analyzer = EconomicCycleAnalyzer(data)
            report = analyzer.generate_report()
            analyzer.print_report()

            # 3. 保存结果
            self.save_report(report)

            # 4. 检查周期变化
            self.check_cycle_change(report)

            return report

        except Exception as e:
            print(f"❌ 分析执行失败: {e}")
            return None

    def save_report(self, report):
        """保存报告到JSON"""
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_cycle_report.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"💾 报告已保存: {filepath}")
        self.history.append(report)

    def check_cycle_change(self, current_report):
        """检查周期是否发生变化"""
        if len(self.history) < 2:
            return

        last_cycle = self.history[-2]['经济周期']
        current_cycle = current_report['经济周期']

        if last_cycle != current_cycle:
            print("\n" + "🔔"*30)
            print(f"⚠️ 警告: 经济周期发生变化!")
            print(f"   {last_cycle} → {current_cycle}")
            print(f"   建议调整资产配置!")
            print("🔔"*30 + "\n")

            # 可以在这里添加邮件/微信通知
            self.send_notification(last_cycle, current_cycle)

    def send_notification(self, old_cycle, new_cycle):
        """发送通知（示例）"""
        # 这里可以集成邮件、微信、钉钉等通知方式
        message = f"""
        经济周期变化提醒

        旧周期: {old_cycle}
        新周期: {new_cycle}

        请及时调整投资组合!
        """
        print(message)
        # TODO: 实现具体的通知逻辑

    def start_monitoring(self, interval_days=7):
        """启动定时监控"""
        print(f"🚀 经济周期监控系统启动")
        print(f"⏰ 监控间隔: 每{interval_days}天")
        print(f"📁 报告保存路径: {self.output_dir}")
        print("="*60)

        # 立即执行一次
        self.run_analysis()

        # 设置定时任务（每周一次）
        schedule.every(interval_days).days.at("09:00").do(self.run_analysis)

        # 持续运行
        while True:
            schedule.run_pending()
            time.sleep(3600)  # 每小时检查一次

# 使用示例
if __name__ == "__main__":
    monitor = EconomicCycleMonitor()

    # 选择运行方式：
    # 方式1: 单次运行
    monitor.run_analysis()

    # 方式2: 启动定时监控（取消注释使用）
    # monitor.start_monitoring(interval_days=7)
```

---

## 六、数据可视化

### 📊 趋势图表生成

```python
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

# 设置中文显示
rcParams['font.sans-serif'] = ['SimHei']  # 用黑体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class MacroDataVisualizer:
    """宏观数据可视化"""

    def __init__(self, data):
        self.data = data

    def plot_m1_pmi_trend(self, save_path=None):
        """绘制M1与PMI走势图"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # M1趋势
        m1_df = self.data['M1_M2']
        ax1.plot(m1_df['月份'].tail(24), m1_df['M1同比'].tail(24),
                marker='o', label='M1同比增速', color='blue')
        ax1.axhline(y=0, color='r', linestyle='--', alpha=0.3)
        ax1.set_title('M1同比增速走势', fontsize=14, fontweight='bold')
        ax1.set_ylabel('增速(%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # PMI走势
        pmi_df = self.data['PMI']
        ax2.plot(pmi_df['月份'].tail(24), pmi_df['值'].tail(24),
                marker='s', label='制造业PMI', color='green')
        ax2.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='荣枯线')
        ax2.set_title('制造业PMI走势', fontsize=14, fontweight='bold')
        ax2.set_ylabel('PMI')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 图表已保存: {save_path}")
        else:
            plt.show()

    def plot_cycle_dashboard(self, cycle_result, save_path=None):
        """绘制经济周期仪表盘"""
        fig = plt.figure(figsize=(14, 10))

        # 周期判断结果
        ax1 = plt.subplot(3, 2, 1)
        cycle_colors = {
            '强复苏': 'red',
            '弱复苏': 'orange',
            '弱衰退': 'yellow',
            '强衰退': 'blue',
            '混沌期（建议均衡配置）': 'gray'
        }
        cycle = cycle_result['经济周期']
        ax1.text(0.5, 0.5, f'当前周期\n\n{cycle}',
                ha='center', va='center', fontsize=18, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor=cycle_colors.get(cycle, 'gray'), alpha=0.7))
        ax1.axis('off')

        # 其他子图...（可继续添加）

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

# 使用示例
if __name__ == "__main__":
    collector = MacroDataCollector()
    data = collector.collect_all()

    visualizer = MacroDataVisualizer(data)
    visualizer.plot_m1_pmi_trend(save_path='./macro_trend.png')
```

---

## 七、常见问题与解决方案

### ❓ FAQ

**Q1: AKShare 数据获取失败怎么办？**

A: 常见原因和解决方法：

```python
# 方法1: 添加延迟，避免频繁请求
import time
time.sleep(1)  # 每次请求间隔1秒

# 方法2: 添加重试机制
def get_data_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(2 ** i)  # 指数退避
            else:
                raise e
```

**Q2: 如何存储历史数据？**

A: 推荐使用 SQLite：

```python
import sqlite3
import pandas as pd

# 创建数据库
conn = sqlite3.connect('macro_data.db')

# 存储数据
df.to_sql('pmi_history', conn, if_exists='append', index=False)

# 读取数据
df = pd.read_sql('SELECT * FROM pmi_history', conn)
```

**Q3: 数据更新频率如何设置？**

A: 建议：

- **日常监控**: 每周一次（周一上午 9 点）
- **关键时期**: 每 3 天一次（数据发布后）
- **历史回测**: 手动执行

---

## 八、进阶功能

### 🚀 扩展方向

1. **数据持久化**：使用 MySQL/PostgreSQL 存储历史数据
2. **机器学习**：训练模型预测周期转换
3. **Web 可视化**：使用 Flask/Django 构建 Web 仪表盘
4. **移动端通知**：集成微信/钉钉机器人
5. **回测验证**：验证历史数据中的周期判断准确性

---

## 九、完整项目结构

```
economic_cycle_monitor/
├── data/
│   ├── raw/              # 原始数据
│   └── processed/        # 处理后数据
├── reports/              # 分析报告
├── logs/                 # 日志文件
├── src/
│   ├── collector.py      # 数据采集器
│   ├── analyzer.py       # 周期分析器
│   ├── monitor.py        # 监控系统
│   └── visualizer.py     # 可视化
├── config.py             # 配置文件
├── main.py               # 主程序
└── requirements.txt      # 依赖列表
```

---
