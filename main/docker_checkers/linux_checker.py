#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux系统的Docker检查器实现
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_checker import DockerChecker, DockerCheckError


class LinuxDockerChecker(DockerChecker):
    """Linux系统的Docker检查器实现"""
    
    def check_docker_installed(self):
        """
        检查Docker是否已在Linux系统上安装
        
        Returns:
            bool: 如果Docker已安装返回True
            
        Raises:
            DockerCheckError: 如果Docker未安装
        """
        try:
            info("正在检查Docker是否已安装...")
            
            # 使用which命令检查docker命令是否存在
            result = run_command("which docker", check=False, verbose=False)
            if result.returncode != 0:
                raise DockerCheckError("Docker未安装，请先安装Docker")
                
            # 获取Docker版本以确认安装
            version_result = run_command("docker --version", verbose=True)
            success("Docker已安装")
            return True
        except CommandError as e:
            error(f"检查Docker安装失败: {str(e)}")
            raise DockerCheckError(f"检查Docker安装失败: {str(e)}")
            
    def check_docker_running(self):
        """
        检查Docker服务是否在Linux上运行
        
        Returns:
            bool: 如果Docker服务正在运行返回Truc
            
        Raises:
            DockerCheckError: 如果Docker服务未运行
        """
        try:
            info("正在检查Docker服务是否运行...")
            
            # 方法1: 直接使用docker info命令测试Docker守护进程是否响应
            # 这是最可靠的方法，因为它直接测试Docker API是否可用
            info_result = run_command("docker info", check=False, verbose=False)
            
            if info_result.returncode == 0:
                # Docker info命令成功，Docker守护进程一定运行中
                success("Docker服务正在运行")
                return True
            
            # 方法2: 如果docker info失败，尝试检查systemctl状态
            systemctl_result = run_command("sudo systemctl is-active docker", check=False, verbose=True)
            
            if systemctl_result.returncode == 0 and systemctl_result.stdout.strip() == "active":
                # systemctl显示服务活跃，但Docker守护进程可能无法响应
                error("Docker服务已启动，但无法响应请求，可能需要重启服务")
                raise DockerCheckError("Docker服务已启动，但无法响应请求，建议执行 'sudo systemctl restart docker'")
            
            # 方法3: 检查Docker进程是否存在
            ps_result = run_command("ps aux | grep -v grep | grep dockerd", check=False, verbose=False)
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                # 找到dockerd进程，但它可能处于异常状态
                error("Docker进程存在但服务无法正常响应，请重启服务")
                raise DockerCheckError("Docker进程存在但服务无法正常响应，建议执行 'sudo systemctl restart docker'")
            
            # 所有检查都失败，Docker服务未运行
            error("Docker服务未运行")
            raise DockerCheckError("Docker服务未运行，请启动Docker服务使用 'sudo systemctl start docker'")
        except CommandError as e:
            error(f"检查Docker服务状态失败: {str(e)}")
            raise DockerCheckError(f"检查Docker服务状态失败: {str(e)}")
            
    def check_docker_functional(self):
        """
        检查Docker在Linux上的基本功能
        
        Returns:
            bool: 如果Docker功能正常返回Truc
            
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
            
            success("Docker功能正常")
            return True
        except CommandError as e:
            error(f"Docker功能测试失败: {str(e)}")
            raise DockerCheckError(f"Docker功能测试失败: {str(e)}")
