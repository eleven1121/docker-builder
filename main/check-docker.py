#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker运行状态检查工具 (Python版本)
检查Docker是否安装、服务是否运行以及Docker功能是否正常
使用工厂模式支持多种操作系统
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.absolute().parent))

# 从shared包中导入所需的所有函数和类
from shared import logger, info, error, debug, warning, success

# 导入我们的Docker检查器工厂
from main.docker_checkers import get_docker_checker
from main.docker_checkers.base_checker import DockerCheckError


if __name__ == "__main__":
    try:
        # 使用工厂函数获取当前系统的Docker检查器
        docker_checker = get_docker_checker()
        
        # 调用检查器的check_docker方法执行检查
        docker_checker.check_docker()
        
        sys.exit(0)  # 检查成功，退出码为0
    except DockerCheckError as e:
        error(f"Docker检查失败: {str(e)}")
        sys.exit(1)  # 检查失败，退出码为1
    except Exception as e:
        error(f"Docker检查过程中发生未预期的异常: {str(e)}")
        sys.exit(1)  # 检查失败，退出码为1
