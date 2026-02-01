"""
经济周期自动监控系统
定时执行分析任务，监控经济周期变化
"""
import schedule
import time
from datetime import datetime
import json
import os
import logging
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.collector import MacroDataCollector
from src.analyzer import EconomicCycleAnalyzer

logger = logging.getLogger(__name__)


class EconomicCycleMonitor:
    """经济周期自动监控系统"""

    def __init__(self, output_dir="./reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.history = []

    def run_analysis(self):
        """执行分析"""
        try:
            logger.info(f"开始执行周期分析 - {datetime.now()}")
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
            error_msg = f"分析执行失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            return None

    def save_report(self, report):
        """保存报告到JSON"""
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_cycle_report.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"💾 报告已保存: {filepath}")
            logger.info(f"报告已保存: {filepath}")
            self.history.append(report)
        except Exception as e:
            error_msg = f"保存报告失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")

    def check_cycle_change(self, current_report):
        """检查周期是否发生变化"""
        if len(self.history) < 2:
            return

        try:
            last_cycle = self.history[-2]['经济周期']
            current_cycle = current_report['经济周期']

            if last_cycle != current_cycle:
                print("\n" + "🔔"*30)
                print(f"⚠️ 警告: 经济周期发生变化!")
                print(f"   {last_cycle} → {current_cycle}")
                print(f"   建议调整资产配置!")
                print("🔔"*30 + "\n")

                logger.warning(f"经济周期变化: {last_cycle} → {current_cycle}")

                # 可以在这里添加邮件/微信通知
                self.send_notification(last_cycle, current_cycle)
        except Exception as e:
            logger.error(f"检查周期变化失败: {e}")

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
        logger.info(f"周期变化通知: {old_cycle} → {new_cycle}")
        # TODO: 实现具体的通知逻辑

    def start_monitoring(self, interval_days=7):
        """启动定时监控"""
        print(f"🚀 经济周期监控系统启动")
        print(f"⏰ 监控间隔: 每{interval_days}天")
        print(f"📁 报告保存路径: {self.output_dir}")
        print("="*60)
        logger.info(f"监控系统启动，间隔: {interval_days}天")

        # 立即执行一次
        self.run_analysis()

        # 设置定时任务（每周一次）
        schedule.every(interval_days).days.at("09:00").do(self.run_analysis)

        # 持续运行
        try:
            while True:
                schedule.run_pending()
                time.sleep(3600)  # 每小时检查一次
        except KeyboardInterrupt:
            print("\n监控系统已停止")
            logger.info("监控系统已停止")


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/monitor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    monitor = EconomicCycleMonitor()

    # 选择运行方式：
    # 方式1: 单次运行
    monitor.run_analysis()

    # 方式2: 启动定时监控（取消注释使用）
    # monitor.start_monitoring(interval_days=7)

