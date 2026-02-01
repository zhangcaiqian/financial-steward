"""
主程序入口
提供命令行接口执行各种功能
"""
import argparse
import sys
import logging
import logging.config
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import LOG_CONFIG, REPORTS_DIR
from src.collector import MacroDataCollector
from src.analyzer import EconomicCycleAnalyzer
from src.monitor import EconomicCycleMonitor
from src.visualizer import MacroDataVisualizer


def setup_logging():
    """配置日志系统"""
    logging.config.dictConfig(LOG_CONFIG)


def run_analysis(generate_charts=False):
    """执行单次分析"""
    print("=" * 60)
    print("经济周期分析系统")
    print("=" * 60)
    
    # 1. 采集数据
    collector = MacroDataCollector()
    data = collector.collect_all()
    
    # 2. 分析周期
    analyzer = EconomicCycleAnalyzer(data)
    report = analyzer.generate_report()
    analyzer.print_report()
    
    # 3. 保存报告
    monitor = EconomicCycleMonitor(output_dir=str(REPORTS_DIR))
    monitor.save_report(report)
    
    # 4. 生成图表（可选）
    if generate_charts:
        print("\n生成可视化图表...")
        visualizer = MacroDataVisualizer(data)
        visualizer.plot_m1_pmi_trend(save_path=str(REPORTS_DIR / 'm1_pmi_trend.png'))
        visualizer.plot_cycle_dashboard(report, save_path=str(REPORTS_DIR / 'cycle_dashboard.png'))
        visualizer.plot_all_indicators(save_path=str(REPORTS_DIR / 'all_indicators.png'))
    
    return report


def start_monitor(interval_days=7):
    """启动定时监控"""
    monitor = EconomicCycleMonitor(output_dir=str(REPORTS_DIR))
    monitor.start_monitoring(interval_days=interval_days)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='经济周期自动判断系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                    # 执行单次分析
  python main.py --charts           # 执行分析并生成图表
  python main.py --monitor          # 启动定时监控
  python main.py --monitor --interval 3  # 每3天执行一次监控
        """
    )
    
    parser.add_argument(
        '--charts',
        action='store_true',
        help='生成可视化图表'
    )
    
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='启动定时监控系统'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=7,
        help='监控间隔天数（默认7天）'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("程序启动")
    
    try:
        if args.monitor:
            # 启动监控模式
            start_monitor(interval_days=args.interval)
        else:
            # 单次分析模式
            run_analysis(generate_charts=args.charts)
            logger.info("分析完成")
    except KeyboardInterrupt:
        print("\n程序已中断")
        logger.info("程序被用户中断")
    except Exception as e:
        error_msg = f"程序执行失败: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

