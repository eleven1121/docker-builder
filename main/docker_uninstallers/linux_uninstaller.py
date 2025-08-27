#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux系统的Docker卸载器实现
"""

import sys
import os
import shutil
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_uninstaller import BaseDockerUninstaller, DockerUninstallError


class LinuxDockerUninstaller(BaseDockerUninstaller):
    """Linux系统的Docker卸载器实现"""
    
    def stop_docker_service(self):
        """
        停止Docker服务
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerUninstallError: 如果停止失败
        """
        try:
            info("======== Step 1: 停止Docker服务 ========")
            
            # 检查Docker服务是否在运行
            status_result = run_command("sudo systemctl status docker", check=False, verbose=False)
            
            if "active (running)" in status_result.stdout.lower():
                info("Docker服务正在运行，准备停止...")
                run_command("sudo systemctl stop docker")
                run_command("sudo systemctl disable docker")
                success("Docker服务已停止并禁用自启")
            else:
                info("Docker服务未运行，跳过停止步骤")
            
            return True
        except CommandError as e:
            warning(f"停止Docker服务失败: {str(e)}")
            # 不抛出异常，因为服务可能已经停止
            return True
    
    def remove_docker_packages(self):
        """
        卸载Docker包
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载失败
        """
        try:
            info("======== Step 2: 卸载Docker包 ========")
            
            # 检查是否安装了Docker
            check_docker = run_command("rpm -q docker", check=False, verbose=False)
            
            if check_docker.returncode == 0:
                info("检测到Docker已安装，准备卸载...")
                run_command("sudo yum remove -y docker")
                success("Docker包卸载完成")
            else:
                info("未检测到Docker包，跳过卸载Docker")
            
            # 检查是否安装了docker-ce
            check_docker_ce = run_command("rpm -q docker-ce", check=False, verbose=False)
            
            if check_docker_ce.returncode == 0:
                info("检测到Docker CE已安装，准备卸载...")
                run_command("sudo yum remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras")
                success("Docker CE包卸载完成")
            else:
                info("未检测到Docker CE包，跳过卸载Docker CE")
                
            # 卸载Docker Compose
            check_compose = run_command("rpm -q docker-compose", check=False, verbose=False)
            
            if check_compose.returncode == 0:
                info("检测到Docker Compose已安装，准备卸载...")
                run_command("sudo yum remove -y docker-compose")
                success("Docker Compose包卸载完成")
            else:
                info("未检测到Docker Compose包，跳过卸载Docker Compose")
            
            return True
        except CommandError as e:
            error(f"卸载Docker包失败: {str(e)}")
            raise DockerUninstallError(f"卸载Docker包失败: {str(e)}")
    
    def remove_docker_data(self):
        """
        移除Docker数据
        
        Returns:
            bool: 移除成功返回True
            
        Raises:
            DockerUninstallError: 如果移除失败
        """
        try:
            info("======== Step 3: 移除Docker数据 ========")
            
            warning("即将删除所有Docker镜像、容器和数据，请确认已备份重要数据")
            
            # 删除Docker配置目录
            if os.path.exists("/etc/docker"):
                info("删除Docker配置目录...")
                run_command("sudo rm -rf /etc/docker")
            
            # 删除Docker数据目录
            if os.path.exists("/var/lib/docker"):
                info("删除Docker数据目录...")
                run_command("sudo rm -rf /var/lib/docker")
            
            # 删除Docker运行时目录
            if os.path.exists("/var/run/docker"):
                info("删除Docker运行时目录...")
                run_command("sudo rm -rf /var/run/docker")
            
            # 删除Docker网络配置
            if os.path.exists("/var/run/docker.sock"):
                info("删除Docker套接字文件...")
                run_command("sudo rm -f /var/run/docker.sock")
            
            # 删除systemd服务文件
            systemd_files = [
                "/usr/lib/systemd/system/docker.service", 
                "/usr/lib/systemd/system/docker.socket",
                "/etc/systemd/system/docker.service",
                "/etc/systemd/system/docker.socket"
            ]
            
            for file_path in systemd_files:
                if os.path.exists(file_path):
                    info(f"删除系统服务文件: {file_path}")
                    run_command(f"sudo rm -f {file_path}")
            
            success("Docker数据已清除")
            return True
        except CommandError as e:
            error(f"删除Docker数据失败: {str(e)}")
            raise DockerUninstallError(f"删除Docker数据失败: {str(e)}")
    
    def clean_system(self):
        """
        清理系统
        
        Returns:
            bool: 清理成功返回True
            
        Raises:
            DockerUninstallError: 如果清理失败
        """
        try:
            info("======== Step 4: 清理系统 ========")
            
            # 刷新systemd
            run_command("sudo systemctl daemon-reload")
            
            # 清理yum缓存
            run_command("sudo yum clean all")
            
            success("系统清理完成")
            return True
        except CommandError as e:
            warning(f"系统清理失败: {str(e)}")
            # 不抛出异常，因为清理步骤不是关键步骤
            return True
    
    def uninstall_docker(self):
        """
        卸载Docker的主方法，调用uninstall_docker_full实现
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载失败
        """
        return self.uninstall_docker_full()
