#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mac系统的Docker检查器实现
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_checker import DockerChecker, DockerCheckError


class MacDockerChecker(DockerChecker):
    """Mac系统的Docker检查器实现"""
    
    def check_docker_installed(self):
        """
        检查Docker Desktop是否已在Mac系统上安装
        
        Returns:
            bool: 如果Docker已安装返回True
            
        Raises:
            DockerCheckError: 如果Docker未安装
        """
        try:
            info("正在检查Docker Desktop是否已安装...")
            
            # 检查Docker.app是否存在
            docker_app_path = "/Applications/Docker.app"
            if not os.path.exists(docker_app_path):
                raise DockerCheckError("Docker Desktop未安装，请先安装Docker Desktop")
                
            # 检查docker命令是否可用
            result = run_command("which docker", check=False, verbose=False)
            if result.returncode != 0:
                raise DockerCheckError("Docker命令不可用，请确保Docker Desktop已正确安装")
                
            # 获取Docker版本以确认安装
            version_result = run_command("docker --version", verbose=True)
            success("Docker Desktop已安装")
            return True
        except CommandError as e:
            error(f"检查Docker安装失败: {str(e)}")
            raise DockerCheckError(f"检查Docker安装失败: {str(e)}")
            
    def check_docker_running(self):
        """
        检查Docker Desktop是否在Mac上运行
        
        Returns:
            bool: 如果Docker服务正在运行返回True
            
        Raises:
            DockerCheckError: 如果Docker服务未运行
        """
        try:
            info("正在检查Docker Desktop是否运行...")
            
            # 检查Docker进程是否运行
            ps_result = run_command("pgrep -f Docker", check=False, verbose=False)
            if ps_result.returncode != 0:
                raise DockerCheckError("Docker Desktop未运行，请启动Docker Desktop应用")
            
            # 尝试与Docker守护进程通信
            info_result = run_command("docker info", check=False, verbose=False)
            if info_result.returncode != 0:
                raise DockerCheckError("Docker守护进程未响应，请确认Docker Desktop正常运行")
                
            success("Docker Desktop正在运行")
            return True
        except CommandError as e:
            error(f"检查Docker服务状态失败: {str(e)}")
            raise DockerCheckError(f"检查Docker服务状态失败: {str(e)}")
            
    def check_docker_functional(self):
        """
        检查Docker在Mac上的基本功能
        
        Returns:
            bool: 如果Docker功能正常返回True
            
        Raises:
            DockerCheckError: 如果Docker功能异常
        """
        try:
            info("正在测试Docker功能...")
            
            # 首先静默地检查并拉取hello-world镜像，避免显示下载警告
            try:
                run_command("docker image inspect hello-world >/dev/null 2>&1 || docker pull hello-world >/dev/null 2>&1", verbose=False)
            except CommandError:
                # 忽略镜像拉取过程中的错误，因为我们稍后会运行hello-world来测试
                pass
            
            # 运行hello-world容器测试Docker功能并展示输出
            run_command("docker run --rm hello-world", verbose=True)
            
            # 检查Docker Compose功能
            compose_result = run_command("docker compose version", check=False, verbose=True)
            if compose_result.returncode != 0:
                warning("Docker Compose可能不可用，但不影响基本功能")
            
            success("Docker功能正常")
            return True
        except CommandError as e:
            error(f"Docker功能测试失败: {str(e)}")
            raise DockerCheckError(f"Docker功能测试失败: {str(e)}")
