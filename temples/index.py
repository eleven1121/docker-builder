#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装和启动入口脚本
提供一键安装Docker和启动Docker服务的功能
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from docker_installers.main_installer import DockerInstaller, DockerInstallError
from docker_starter.main_starter import DockerStarter, DockerStartError


def main():
    """
    主函数，执行Docker安装和启动流程
    
    Returns:
        int: 执行结果，0表示成功，非0表示失败
    """
    info("=== Docker安装与启动工具 ===")
    
    try:
        # 创建Docker安装器
        info("初始化Docker安装器...")
        installer = DockerInstaller()
        
        # 安装Docker完整流程
        info("开始安装Docker...")
        if not installer.install_docker_full():
            error("Docker安装失败")
            return 1
        
        # 给Docker服务一点启动时间
        info("Docker安装成功，等待服务初始化...")
        time.sleep(3)
        
        # 创建Docker启动器
        info("初始化Docker启动器...")
        starter = DockerStarter()
        
        # 启动Docker服务
        if not starter.start_docker():
            error("Docker服务启动失败")
            return 1
        
        return 0
        
    except DockerInstallError as e:
        error(f"Docker安装过程出错: {str(e)}")
        return 1
    except DockerStartError as e:
        error(f"Docker启动过程出错: {str(e)}")
        return 1
    except Exception as e:
        error(f"发生未预期的错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
