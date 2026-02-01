"""
环境测试脚本
验证所有依赖是否正确安装
"""
import sys

def test_imports():
    """测试所有必要的包是否可以导入"""
    print("="*60)
    print("测试环境依赖...")
    print("="*60)
    
    packages = [
        ('akshare', 'AKShare'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
        ('matplotlib', 'Matplotlib'),
        ('schedule', 'Schedule'),
    ]
    
    failed = []
    
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"✅ {display_name:15s} - 已安装")
        except ImportError as e:
            print(f"❌ {display_name:15s} - 未安装")
            failed.append(display_name)
    
    print("="*60)
    
    if failed:
        print(f"\n❌ 以下包未安装: {', '.join(failed)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ 所有依赖包都已正确安装！")
        return True


def test_modules():
    """测试项目模块是否可以导入"""
    print("\n" + "="*60)
    print("测试项目模块...")
    print("="*60)
    
    modules = [
        ('src.collector', 'MacroDataCollector', '数据采集器'),
        ('src.analyzer', 'EconomicCycleAnalyzer', '周期分析器'),
        ('src.monitor', 'EconomicCycleMonitor', '监控系统'),
        ('src.visualizer', 'MacroDataVisualizer', '可视化模块'),
        ('config', 'BASE_DIR', '配置模块'),
    ]
    
    failed = []
    
    for module_name, class_name, display_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {display_name:15s} - 正常")
        except Exception as e:
            print(f"❌ {display_name:15s} - 错误: {e}")
            failed.append(display_name)
    
    print("="*60)
    
    if failed:
        print(f"\n❌ 以下模块有问题: {', '.join(failed)}")
        return False
    else:
        print("\n✅ 所有项目模块都正常！")
        return True


def test_directories():
    """测试必要的目录是否存在"""
    print("\n" + "="*60)
    print("测试目录结构...")
    print("="*60)
    
    from pathlib import Path
    
    base_dir = Path(__file__).parent
    
    directories = [
        ('data/raw', '原始数据目录'),
        ('data/processed', '处理数据目录'),
        ('reports', '报告目录'),
        ('logs', '日志目录'),
        ('src', '源代码目录'),
    ]
    
    failed = []
    
    for dir_path, display_name in directories:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"✅ {display_name:15s} - 存在")
        else:
            print(f"❌ {display_name:15s} - 不存在")
            failed.append(display_name)
    
    print("="*60)
    
    if failed:
        print(f"\n❌ 以下目录不存在: {', '.join(failed)}")
        return False
    else:
        print("\n✅ 所有必要目录都存在！")
        return True


def main():
    """主函数"""
    print("\n🔍 经济周期判断系统 - 环境检测\n")
    
    # 显示Python版本
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}\n")
    
    # 执行测试
    result1 = test_imports()
    result2 = test_modules()
    result3 = test_directories()
    
    print("\n" + "="*60)
    if result1 and result2 and result3:
        print("🎉 环境检测完成！所有测试通过！")
        print("\n你可以运行以下命令开始使用：")
        print("  python example.py       # 运行示例")
        print("  python main.py          # 执行分析")
        print("  python main.py --charts # 执行分析并生成图表")
    else:
        print("⚠️ 环境检测发现问题，请根据上述提示修复。")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

