"""
宏观数据可视化模块
生成各类经济指标的趋势图表
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
import os
import logging

# 设置中文显示
try:
    rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']  # 用黑体
    rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except Exception as e:
    print(f"字体设置警告: {e}")

logger = logging.getLogger(__name__)


class MacroDataVisualizer:
    """宏观数据可视化"""

    def __init__(self, data):
        self.data = data

    def plot_m1_pmi_trend(self, save_path=None):
        """绘制M1与PMI走势图"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

            # M1趋势
            m1_df = self.data.get('M1_M2')
            if m1_df is not None and len(m1_df) > 0:
                m1_tail = m1_df.tail(24)
                ax1.plot(range(len(m1_tail)), m1_tail['M1同比'],
                        marker='o', label='M1同比增速', color='blue')
                ax1.axhline(y=0, color='r', linestyle='--', alpha=0.3)
                ax1.set_title('M1同比增速走势', fontsize=14, fontweight='bold')
                ax1.set_ylabel('增速(%)')
                ax1.set_xlabel('时间（最近24个月）')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

            # PMI走势
            pmi_df = self.data.get('PMI')
            if pmi_df is not None and len(pmi_df) > 0:
                pmi_tail = pmi_df.tail(24)
                ax2.plot(range(len(pmi_tail)), pmi_tail['值'],
                        marker='s', label='制造业PMI', color='green')
                ax2.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='荣枯线')
                ax2.set_title('制造业PMI走势', fontsize=14, fontweight='bold')
                ax2.set_ylabel('PMI')
                ax2.set_xlabel('时间（最近24个月）')
                ax2.legend()
                ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"📊 图表已保存: {save_path}")
                logger.info(f"图表已保存: {save_path}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            error_msg = f"绘制M1/PMI趋势图失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")

    def plot_cycle_dashboard(self, cycle_result, save_path=None):
        """绘制经济周期仪表盘"""
        try:
            fig = plt.figure(figsize=(14, 10))

            # 周期判断结果
            ax1 = plt.subplot(3, 2, 1)
            cycle_colors = {
                '强复苏': '#FF4444',  # 红色
                '弱复苏': '#FF8800',  # 橙色
                '弱衰退': '#FFDD00',  # 黄色
                '强衰退': '#4444FF',  # 蓝色
                '混沌期（建议均衡配置）': '#888888'  # 灰色
            }
            cycle = cycle_result['经济周期']
            color = cycle_colors.get(cycle, '#888888')
            
            ax1.text(0.5, 0.5, f'当前周期\n\n{cycle}',
                    ha='center', va='center', fontsize=18, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))
            ax1.set_title('经济周期判断', fontsize=16, fontweight='bold')
            ax1.axis('off')

            # 配置建议
            ax2 = plt.subplot(3, 2, 2)
            config = cycle_result['配置建议']
            config_text = f"股票配置:\n{config['股票配置']}\n\n债券配置:\n{config['债券配置']}\n\n说明:\n{config['说明']}"
            ax2.text(0.1, 0.5, config_text, ha='left', va='center', 
                    fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax2.set_title('资产配置建议', fontsize=16, fontweight='bold')
            ax2.axis('off')

            # 其他子图可以继续添加更多指标可视化
            # 例如：M1趋势、PMI趋势等

            plt.tight_layout()
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"📊 仪表盘已保存: {save_path}")
                logger.info(f"仪表盘已保存: {save_path}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            error_msg = f"绘制周期仪表盘失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")

    def plot_all_indicators(self, save_path=None):
        """绘制所有指标的综合图表"""
        try:
            fig, axes = plt.subplots(3, 2, figsize=(16, 12))
            fig.suptitle('宏观经济指标综合走势', fontsize=16, fontweight='bold')

            # M1趋势
            m1_df = self.data.get('M1_M2')
            if m1_df is not None and len(m1_df) > 0:
                ax = axes[0, 0]
                m1_tail = m1_df.tail(24)
                ax.plot(range(len(m1_tail)), m1_tail['M1同比'], 
                       marker='o', label='M1同比', color='blue')
                ax.axhline(y=0, color='r', linestyle='--', alpha=0.3)
                ax.set_title('M1同比增速')
                ax.set_ylabel('增速(%)')
                ax.legend()
                ax.grid(True, alpha=0.3)

            # PMI趋势
            pmi_df = self.data.get('PMI')
            if pmi_df is not None and len(pmi_df) > 0:
                ax = axes[0, 1]
                pmi_tail = pmi_df.tail(24)
                ax.plot(range(len(pmi_tail)), pmi_tail['值'],
                       marker='s', label='PMI', color='green')
                ax.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='荣枯线')
                ax.set_title('制造业PMI')
                ax.set_ylabel('PMI')
                ax.legend()
                ax.grid(True, alpha=0.3)

            # CPI趋势
            cpi_df = self.data.get('CPI')
            if cpi_df is not None and len(cpi_df) > 0:
                ax = axes[1, 0]
                cpi_tail = cpi_df.tail(24)
                ax.plot(range(len(cpi_tail)), cpi_tail['值'],
                       marker='^', label='CPI同比', color='red')
                ax.set_title('CPI同比')
                ax.set_ylabel('CPI(%)')
                ax.legend()
                ax.grid(True, alpha=0.3)

            # PPI趋势
            ppi_df = self.data.get('PPI')
            if ppi_df is not None and len(ppi_df) > 0:
                ax = axes[1, 1]
                ppi_tail = ppi_df.tail(24)
                ax.plot(range(len(ppi_tail)), ppi_tail['值'],
                       marker='v', label='PPI同比', color='orange')
                ax.set_title('PPI同比')
                ax.set_ylabel('PPI(%)')
                ax.legend()
                ax.grid(True, alpha=0.3)

            # 社融趋势
            shrzgm_df = self.data.get('社融')
            if shrzgm_df is not None and len(shrzgm_df) > 0:
                ax = axes[2, 0]
                # 新的API返回数据已经包含社融存量，不需要筛选
                shrzgm_tail = shrzgm_df.tail(24)
                if '社融存量' in shrzgm_df.columns:
                    ax.plot(range(len(shrzgm_tail)), shrzgm_tail['社融存量'],
                           marker='d', label='社融存量', color='purple')
                    ax.set_title('社会融资规模存量')
                    ax.set_ylabel('存量(亿元)')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                elif '社融同比' in shrzgm_df.columns:
                    # 如果没有存量数据，显示同比数据
                    ax.plot(range(len(shrzgm_tail)), shrzgm_tail['社融同比'],
                           marker='d', label='社融同比', color='purple')
                    ax.set_title('社会融资规模同比')
                    ax.set_ylabel('同比增长(%)')
                    ax.legend()
                    ax.grid(True, alpha=0.3)

            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"📊 综合图表已保存: {save_path}")
                logger.info(f"综合图表已保存: {save_path}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            error_msg = f"绘制综合图表失败: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")


# 使用示例
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 添加backend目录到路径
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    from src.collector import MacroDataCollector
    from src.analyzer import EconomicCycleAnalyzer
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = MacroDataCollector()
    data = collector.collect_all()

    visualizer = MacroDataVisualizer(data)
    visualizer.plot_m1_pmi_trend(save_path='./reports/macro_trend.png')
    
    analyzer = EconomicCycleAnalyzer(data)
    report = analyzer.generate_report()
    visualizer.plot_cycle_dashboard(report, save_path='./reports/cycle_dashboard.png')
    visualizer.plot_all_indicators(save_path='./reports/all_indicators.png')

