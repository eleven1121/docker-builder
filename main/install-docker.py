#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装工具 (Python版本)
检查系统环境并安装Docker及相关组件
支持Linux和macOS系统
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.absolute().parent))

# 从shared包中导入所需的所有函数和类
from shared import info, error, warning, success


# 导入我们的Docker安装器工厂
from main.docker_installers import get_docker_installer
from main.docker_installers.base_installer import DockerInstallError


if __name__ == "__main__":
    try:
        # 使用工厂函数获取当前系统的Docker安装器
        docker_installer = get_docker_installer()
        
        # 调用安装器的install_docker方法执行安装
        docker_installer.install_docker()
        
        sys.exit(0)  # 安装成功，退出码为0
    except DockerInstallError as e:
        error(f"Docker安装失败: {str(e)}")
        sys.exit(1)  # 安装失败，退出码为1
    except Exception as e:
        error(f"Docker安装过程中发生未预期的异常: {str(e)}")
        sys.exit(1)  # 安装失败，退出码为1
