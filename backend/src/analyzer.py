"""
经济周期分析器
根据宏观经济指标判断当前经济周期阶段
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class EconomicCycleAnalyzer:
    """经济周期分析器"""

    def __init__(self, data: Dict):
        self.data = data
        self.cycle_result = None

    def analyze_m1_trend(self) -> str:
        """分析M1趋势"""
        df = self.data.get('M1_M2')
        if df is None or len(df) < 3:
            logger.warning("M1数据不足，无法分析趋势")
            return "数据不足"

        try:
            recent_m1 = df['M1同比'].tail(3).values

            # 判断趋势：连续2个月上涨为上行
            if recent_m1[-1] > recent_m1[-2] and recent_m1[-2] > recent_m1[-3]:
                return "上行"
            elif recent_m1[-1] < recent_m1[-2] and recent_m1[-2] < recent_m1[-3]:
                return "下行"
            else:
                return "混沌"
        except Exception as e:
            logger.error(f"M1趋势分析失败: {e}")
            return "数据不足"

    def analyze_pmi_status(self) -> Tuple[str, float]:
        """分析PMI状态"""
        df = self.data.get('PMI')
        if df is None or len(df) < 3:
            logger.warning("PMI数据不足，无法分析状态")
            return "数据不足", 0

        try:
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
        except Exception as e:
            logger.error(f"PMI状态分析失败: {e}")
            return "数据不足", 0

    def analyze_cpi_ppi_trend(self) -> str:
        """分析CPI和PPI趋势"""
        cpi_df = self.data.get('CPI')
        ppi_df = self.data.get('PPI')

        if cpi_df is None or ppi_df is None or len(cpi_df) < 2 or len(ppi_df) < 2:
            logger.warning("CPI/PPI数据不足，无法分析趋势")
            return "数据不足"

        try:
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
        except Exception as e:
            logger.error(f"CPI/PPI趋势分析失败: {e}")
            return "数据不足"

    def analyze_shrzgm_trend(self) -> str:
        """分析社融趋势"""
        df = self.data.get('社融')
        if df is None or len(df) < 3:
            logger.warning("社融数据不足，无法分析趋势")
            return "数据不足"

        try:
            # 使用社融同比增长数据来判断趋势
            # 新接口返回的数据已经包含累计同比增长
            if '社融同比' not in df.columns:
                logger.warning("社融数据格式不正确")
                return "数据不足"
            
            recent = df['社融同比'].tail(3).values

            if recent[-1] > recent[-2] > recent[-3]:
                return "上行"
            elif recent[-1] < recent[-2] < recent[-3]:
                return "下行"
            else:
                return "混沌"
        except Exception as e:
            logger.error(f"社融趋势分析失败: {e}")
            return "数据不足"

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
        pmi_status, pmi_value = signals['PMI']
        print(f"PMI状态:    {pmi_status} (当前值: {pmi_value:.1f})")
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
        logger.info(f"生成报告完成，当前周期: {cycle}")
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
    import sys
    from pathlib import Path
    
    # 添加backend目录到路径
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    from src.collector import MacroDataCollector
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. 采集数据
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 2. 分析周期
    analyzer = EconomicCycleAnalyzer(data)

    # 3. 生成报告
    analyzer.print_report()

