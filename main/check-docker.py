#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker运行状态检查工具 (Python版本)
检查Docker是否安装、服务是否运行以及Docker功能是否正常
"""

import os
import subprocess
import sys
from pathlib import Path

# 获取项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
ROOT_DIR = SCRIPT_DIR.parent
SHARED_DIR = ROOT_DIR / "shared"

# 添加shared目录到sys.path以便导入
sys.path.append(str(ROOT_DIR))

# 导入日志模块
from shared.logger import logger, info, error, debug, warning


class DockerCheckError(Exception):
    """Docker检查过程中遇到的异常"""
    pass


def check_docker_installed():
    """
    检查Docker是否已安装
    
    Returns:
        bool: Docker已安装返回True, 否则抛出异常
        
    Raises:
        DockerCheckError: 如果Docker未安装
    """
    try:
        # 执行docker --version命令检查Docker是否已安装
        result = subprocess.run(
            ["docker", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            docker_version = result.stdout.strip()
            info(f"Docker已安装: {docker_version}")
            return True
        else:
            raise DockerCheckError("Docker未安装")
    except FileNotFoundError:
        error("Docker命令未找到，Docker可能未安装")
        raise DockerCheckError("Docker命令未找到，Docker可能未安装")
    except Exception as e:
        error(f"检查Docker安装状态时发生异常: {str(e)}")
        raise DockerCheckError(f"检查Docker安装状态时发生异常: {str(e)}")


def check_docker_running():
    """
    检查Docker服务是否正在运行
    
    Returns:
        bool: Docker服务正在运行返回True, 否则抛出异常
        
    Raises:
        DockerCheckError: 如果Docker服务未运行
    """
    try:
        # 检查Docker守护进程是否在运行
        result = subprocess.run(
            ["docker", "info"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            info("Docker服务正在运行")
            return True
        else:
            error_message = result.stderr.strip() or "无法连接到Docker守护进程"
            error(f"Docker服务未运行: {error_message}")
            raise DockerCheckError(f"Docker服务未运行: {error_message}")
    except Exception as e:
        error(f"检查Docker服务运行状态时发生异常: {str(e)}")
        raise DockerCheckError(f"检查Docker服务运行状态时发生异常: {str(e)}")


def check_docker_functional():
    """
    检查Docker是否可用(能够成功运行hello-world容器)
    
    Returns:
        bool: Docker功能正常返回True, 否则抛出异常
        
    Raises:
        DockerCheckError: 如果Docker功能异常
    """
    try:
        # 尝试运行hello-world容器来测试Docker是否正常工作
        result = subprocess.run(
            ["docker", "run", "--rm", "hello-world"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=False
        )
        
        if result.returncode == 0:
            info("Docker功能正常")
            debug(f"hello-world输出: {result.stdout.strip()}")
            return True
        else:
            error_message = result.stderr.strip()
            error(f"Docker功能测试失败: {error_message}")
            raise DockerCheckError(f"Docker功能测试失败: {error_message}")
    except Exception as e:
        error(f"检查Docker功能时发生异常: {str(e)}")
        raise DockerCheckError(f"检查Docker功能时发生异常: {str(e)}")


def check_docker():
    """
    主方法: 检查Docker的安装、运行状态和功能
    
    Returns:
        bool: 所有检查都通过返回True
        
    Raises:
        DockerCheckError: 如果任何检查失败
    """
    try:
        info("开始检查Docker状态...")
        
        # 逐个执行检查，任一检查失败都会抛出异常
        check_docker_installed()
        check_docker_running()
        check_docker_functional()
        
        info("Docker检查完成，一切正常")
        return True
    except DockerCheckError as e:
        error(f"Docker检查失败: {str(e)}")
        raise  # 重新抛出异常给调用者
    except Exception as e:
        error(f"Docker检查过程中发生未预期的异常: {str(e)}")
        raise DockerCheckError(f"Docker检查过程中发生未预期的异常: {str(e)}")


if __name__ == "__main__":
    try:
        check_docker()
        sys.exit(0)  # 检查成功，退出码为0
    except Exception as e:
        sys.exit(1)  # 检查失败，退出码为1
