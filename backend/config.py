"""
配置文件
定义系统运行的各种配置参数
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 报告目录
REPORTS_DIR = BASE_DIR / "reports"

# 日志目录
LOGS_DIR = BASE_DIR / "logs"

# 创建必要的目录
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 日志配置
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# 数据采集配置
DATA_COLLECTION_CONFIG = {
    'retry_times': 3,  # 重试次数
    'retry_delay': 1,  # 重试延迟（秒）
    'request_delay': 1,  # 请求间隔（秒）
}

# 监控配置
MONITOR_CONFIG = {
    'interval_days': 7,  # 监控间隔（天）
    'schedule_time': '09:00',  # 定时执行时间
    'check_interval': 3600,  # 检查间隔（秒）
}

# 可视化配置
VISUALIZATION_CONFIG = {
    'figure_dpi': 300,  # 图表分辨率
    'figure_size': (12, 8),  # 默认图表尺寸
    'font_family': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],  # 字体
}

# 经济周期判断阈值配置
CYCLE_THRESHOLDS = {
    'pmi_strong_expansion': 50.5,  # PMI强扩张阈值
    'pmi_expansion': 50.0,  # PMI扩张阈值
    'trend_months': 3,  # 趋势判断所需月数
}

# 资产配置系统数据库配置
PORTFOLIO_DB = {
    'url': os.getenv('DATABASE_URL', os.getenv('PORTFOLIO_DB_URL', '')),
    'host': os.getenv('PORTFOLIO_DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('PORTFOLIO_DB_PORT', '3306')),
    'user': os.getenv('PORTFOLIO_DB_USER', 'root'),
    'password': os.getenv('PORTFOLIO_DB_PASSWORD', ''),
    'database': os.getenv('PORTFOLIO_DB_NAME', 'financial_steward'),
}

# 资产配置系统默认参数
PORTFOLIO_DEFAULTS = {
    'rebalance_frequency_days': 180,
    'rebalance_threshold_ratio': 0.05,
    'cash_target_ratio': 0.05,
    'dca_batches': 4,
}
