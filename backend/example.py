"""
快速开始示例
演示如何使用经济周期判断系统的各个模块
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.collector import MacroDataCollector
from src.analyzer import EconomicCycleAnalyzer
from src.visualizer import MacroDataVisualizer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def example_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("示例1: 基础使用 - 数据采集和周期分析")
    print("=" * 60)

    # 1. 创建数据采集器并获取数据
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 2. 创建分析器并生成报告
    analyzer = EconomicCycleAnalyzer(data)
    report = analyzer.generate_report()

    # 3. 打印报告
    analyzer.print_report()

    return data, report


def example_with_visualization():
    """带可视化的示例"""
    print("\n" + "=" * 60)
    print("示例2: 数据可视化")
    print("=" * 60)

    # 获取数据
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 创建可视化器
    visualizer = MacroDataVisualizer(data)

    # 生成图表
    print("正在生成图表...")
    visualizer.plot_m1_pmi_trend(save_path="./reports/example_m1_pmi.png")
    visualizer.plot_all_indicators(save_path="./reports/example_all_indicators.png")

    # 生成周期仪表盘
    analyzer = EconomicCycleAnalyzer(data)
    report = analyzer.generate_report()
    visualizer.plot_cycle_dashboard(report, save_path="./reports/example_dashboard.png")

    print("图表已保存到 reports/ 目录")


def example_custom_analysis():
    """自定义分析示例"""
    print("\n" + "=" * 60)
    print("示例3: 自定义分析 - 查看各指标详情")
    print("=" * 60)

    collector = MacroDataCollector()
    data = collector.collect_all()

    analyzer = EconomicCycleAnalyzer(data)

    # 查看各指标分析结果
    print("\n各指标分析结果:")
    print(f"M1趋势: {analyzer.analyze_m1_trend()}")

    pmi_status, pmi_value = analyzer.analyze_pmi_status()
    print(f"PMI状态: {pmi_status}, 当前值: {pmi_value:.2f}")

    print(f"CPI/PPI趋势: {analyzer.analyze_cpi_ppi_trend()}")
    print(f"社融趋势: {analyzer.analyze_shrzgm_trend()}")

    # 查看最近数据
    if "PMI" in data and data["PMI"] is not None:
        print("\n最近3个月PMI数据:")
        print(data["PMI"].tail(3))

    if "M1_M2" in data and data["M1_M2"] is not None:
        print("\n最近3个月M1/M2数据:")
        print(data["M1_M2"].tail(3))


if __name__ == "__main__":
    try:
        # 运行基础示例
        data, report = example_basic_usage()

        # 运行可视化示例（可选，取消注释以启用）
        example_with_visualization()

        # 运行自定义分析示例
        # example_custom_analysis()

        print("\n" + "=" * 60)
        print("✅ 所有示例执行完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback

        traceback.print_exc()
