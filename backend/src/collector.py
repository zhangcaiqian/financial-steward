"""
宏观经济数据采集器
使用AKShare获取各类宏观经济指标数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime
import time
import warnings
import logging

warnings.filterwarnings('ignore')

# 配置日志
logger = logging.getLogger(__name__)


class MacroDataCollector:
    """宏观经济数据采集器"""

    def __init__(self):
        self.data = {}

    def _get_data_with_retry(self, func, max_retries=3, delay=1):
        """
        带重试机制的数据获取
        
        Args:
            func: 数据获取函数
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
        
        Returns:
            获取到的数据或None
        """
        for i in range(max_retries):
            try:
                time.sleep(delay)  # 避免频繁请求
                return func()
            except Exception as e:
                if i < max_retries - 1:
                    wait_time = delay * (2 ** i)  # 指数退避
                    logger.warning(f"数据获取失败，{wait_time}秒后重试 ({i+1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"数据获取最终失败: {e}")
                    return None
        return None

    def get_m1_m2(self):
        """获取M1和M2数据（从货币供应量接口）"""
        try:
            # 使用新的货币供应量接口，包含M0、M1、M2数据
            df = self._get_data_with_retry(lambda: ak.macro_china_money_supply())
            if df is None:
                logger.error("货币供应量数据获取失败")
                return None
            
            # 提取需要的列并重命名
            # 列名: ['月份', '货币和准货币(M2)-数量(亿元)', '货币和准货币(M2)-同比增长', '货币和准货币(M2)-环比增长', 
            #       '货币(M1)-数量(亿元)', '货币(M1)-同比增长', '货币(M1)-环比增长', ...]
            df = df.rename(columns={
                '货币(M1)-同比增长': 'M1同比',
                '货币和准货币(M2)-同比增长': 'M2同比'
            })
            
            # 只保留需要的列
            df = df[['月份', 'M1同比', 'M2同比']]

            self.data['M1_M2'] = df
            logger.info("✅ M1/M2数据获取成功")
            return df
        except Exception as e:
            logger.error(f"❌ M1/M2数据获取失败: {e}")
            return None

    def get_shrzgm(self):
        """获取社融数据（新增信贷）"""
        try:
            df = self._get_data_with_retry(lambda: ak.macro_china_new_financial_credit())
            if df is None:
                logger.error("社融数据获取失败")
                return None
            
            # 新接口返回的列名: ['月份', '当月', '当月-同比增长', '当月-环比增长', '累计', '累计-同比增长']
            # 将累计同比增长作为社融趋势的参考指标
            df = df.rename(columns={
                '累计-同比增长': '社融同比',
                '累计': '社融存量'
            })
            
            self.data['社融'] = df
            logger.info("✅ 社融数据获取成功")
            return df
        except Exception as e:
            logger.error(f"❌ 社融数据获取失败: {e}")
            return None

    def get_pmi(self):
        """获取PMI数据"""
        try:
            df = self._get_data_with_retry(lambda: ak.macro_china_pmi())
            if df is None:
                logger.error("PMI数据获取失败")
                return None
            
            # 新接口返回的列名: ['月份', '制造业-指数', '制造业-同比增长', '非制造业-指数', '非制造业-同比增长']
            # 提取制造业PMI数据并重命名
            df = df.rename(columns={
                '制造业-指数': '值',
                '制造业-同比增长': '同比增长'
            })
            
            self.data['PMI'] = df
            logger.info("✅ PMI数据获取成功")
            return df
        except Exception as e:
            logger.error(f"❌ PMI数据获取失败: {e}")
            return None

    def get_cpi_ppi(self):
        """获取CPI和PPI数据"""
        try:
            # CPI - 使用年率数据（同比）
            cpi_df = self._get_data_with_retry(lambda: ak.macro_china_cpi_yearly())
            if cpi_df is None:
                logger.error("CPI数据获取失败")
                return None, None
            
            # 新接口返回的列名: ['商品', '日期', '今值', '预测值', '前值']
            # 将'今值'重命名为'值'，'日期'重命名为'月份'
            cpi_df = cpi_df.rename(columns={
                '日期': '月份',
                '今值': '值'
            })
            # 只保留需要的列
            cpi_df = cpi_df[['月份', '值']]

            # PPI - 使用年率数据（同比）
            ppi_df = self._get_data_with_retry(lambda: ak.macro_china_ppi_yearly())
            if ppi_df is None:
                logger.error("PPI数据获取失败")
                return None, None
            
            ppi_df = ppi_df.rename(columns={
                '日期': '月份',
                '今值': '值'
            })
            ppi_df = ppi_df[['月份', '值']]

            self.data['CPI'] = cpi_df
            self.data['PPI'] = ppi_df
            logger.info("✅ CPI/PPI数据获取成功")
            return cpi_df, ppi_df
        except Exception as e:
            logger.error(f"❌ CPI/PPI数据获取失败: {e}")
            return None, None

    def get_gdp(self):
        """获取GDP数据"""
        try:
            df = self._get_data_with_retry(lambda: ak.macro_china_gdp())
            if df is None:
                logger.error("GDP数据获取失败")
                return None
            
            self.data['GDP'] = df
            logger.info("✅ GDP数据获取成功")
            return df
        except Exception as e:
            logger.error(f"❌ GDP数据获取失败: {e}")
            return None

    def collect_all(self):
        """一键获取所有数据"""
        logger.info("开始采集宏观数据...")
        print("开始采集宏观数据...")
        print("=" * 50)

        self.get_m1_m2()
        self.get_shrzgm()
        self.get_pmi()
        self.get_cpi_ppi()
        self.get_gdp()

        print("=" * 50)
        print("✅ 数据采集完成!")
        logger.info("数据采集完成")
        return self.data


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = MacroDataCollector()
    data = collector.collect_all()

    # 查看最近3个月数据
    if 'PMI' in data and data['PMI'] is not None:
        print("\n📊 最近3个月PMI数据:")
        print(data['PMI'].tail(3))

