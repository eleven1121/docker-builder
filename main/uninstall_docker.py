#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker卸载工具 (Python版本)
卸载Docker及相关组件并清理系统
支持Linux和macOS系统
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.absolute().parent))

# 从shared包中导入所需的所有函数和类
from shared import info, error, warning, success

# 导入我们的Docker卸载器工厂
from main.docker_uninstallers import get_docker_uninstaller
from main.docker_uninstallers.base_uninstaller import DockerUninstallError


if __name__ == "__main__":
    try:
        # 使用工厂函数获取当前系统的Docker卸载器
        docker_uninstaller = get_docker_uninstaller()
        
        # 显示警告，确认卸载操作
        warning("警告: 此操作将完全卸载Docker及其所有数据!")
        warning("所有容器、镜像和卷数据将被删除，请确保已备份重要数据")
        
        # 提示用户确认
        confirm = input("确认要卸载Docker吗? (y/N): ").lower()
        if confirm != 'y':
            info("操作已取消")
            sys.exit(0)
        
        # 调用卸载器的uninstall_docker方法执行卸载
        docker_uninstaller.uninstall_docker()
        
        sys.exit(0)  # 卸载成功，退出码为0
    except DockerUninstallError as e:
        error(f"Docker卸载失败: {str(e)}")
        sys.exit(1)  # 卸载失败，退出码为1
    except Exception as e:
        error(f"Docker卸载过程中发生未预期的异常: {str(e)}")
        sys.exit(1)  # 卸载失败，退出码为1
