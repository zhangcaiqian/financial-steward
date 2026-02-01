#!/bin/bash
# 经济周期判断系统 - 环境安装脚本

echo "=================================="
echo "经济周期判断系统 - 环境安装"
echo "=================================="

# 检查 Python 版本
echo ""
echo "1. 检查 Python 版本..."
python3 --version

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo ""
    echo "2. 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo ""
    echo "2. 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "3. 激活虚拟环境并安装依赖..."
source venv/bin/activate

# 升级 pip
echo ""
echo "4. 升级 pip..."
pip install --upgrade pip

# 安装依赖（使用阿里云镜像加速）
echo ""
echo "5. 安装项目依赖..."
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

echo ""
echo "=================================="
echo "✅ 安装完成！"
echo "=================================="
echo ""
echo "使用方法："
echo "  1. 激活虚拟环境: source venv/bin/activate"
echo "  2. 运行示例: python example.py"
echo "  3. 执行分析: python main.py"
echo "  4. 退出虚拟环境: deactivate"
echo ""

