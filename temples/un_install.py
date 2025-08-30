#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker卸载脚本
提供一键卸载Docker的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from docker_installers.main_installer import DockerInstaller, DockerInstallError


def main():
    """
    主函数，执行Docker卸载流程
    
    Returns:
        int: 执行结果，0表示成功，非0表示失败
    """
    info("=== Docker卸载工具 ===")
    
    try:
        # 确认卸载
        confirm = input("确定要卸载Docker? 这将删除所有Docker相关组件和配置 [y/N]: ").lower()
        if confirm != 'y':
            info("已取消卸载操作")
            return 0
        
        # 创建Docker安装器
        info("初始化Docker安装器...")
        installer = DockerInstaller()
        
        # 执行卸载流程
        info("开始卸载Docker...")
        if installer.uninstall_docker():
            return 0
        else:
            error("Docker卸载失败")
            return 1
            
    except DockerInstallError as e:
        error(f"Docker卸载过程出错: {str(e)}")
        return 1
    except Exception as e:
        error(f"发生未预期的错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
