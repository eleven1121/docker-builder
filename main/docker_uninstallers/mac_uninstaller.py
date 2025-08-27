#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mac系统的Docker卸载器实现
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_uninstaller import BaseDockerUninstaller, DockerUninstallError


class MacDockerUninstaller(BaseDockerUninstaller):
    """Mac系统的Docker卸载器实现"""
    
    def stop_docker_service(self):
        """
        停止Docker Desktop
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerUninstallError: 如果停止失败
        """
        try:
            info("======== Step 1: 停止Docker Desktop服务 ========")
            
            # 检查Docker Desktop是否在运行
            ps_result = run_command("pgrep -f Docker", check=False, verbose=False)
            
            if ps_result.returncode == 0:
                info("Docker Desktop正在运行，准备停止...")
                
                # 先尝试优雅关闭
                run_command("osascript -e 'quit app \"Docker\"'", check=False, verbose=False)
                
                # 确认是否已关闭
                import time
                time.sleep(2)  # 等待Docker关闭
                
                ps_check = run_command("pgrep -f Docker", check=False, verbose=False)
                if ps_check.returncode == 0:
                    # 如果仍在运行，使用强制方法
                    warning("Docker Desktop无法优雅关闭，准备强制终止进程...")
                    run_command("pkill -f Docker", check=False)
                
                success("Docker Desktop已停止")
            else:
                info("Docker Desktop未运行，跳过停止步骤")
            
            return True
        except Exception as e:
            warning(f"停止Docker Desktop失败: {str(e)}")
            # 不抛出异常，因为服务可能已经停止
            return True
    
    def remove_docker_packages(self):
        """
        卸载Docker Desktop
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载失败
        """
        try:
            info("======== Step 2: 卸载Docker Desktop ========")
            
            # 检查Docker Desktop是否已安装
            if os.path.exists("/Applications/Docker.app"):
                info("检测到Docker Desktop已安装，准备卸载...")
                
                # 使用Homebrew卸载Docker
                brew_result = run_command("brew uninstall --cask docker", check=False, verbose=False)
                
                # 如果Homebrew卸载失败，尝试手动删除
                if brew_result.returncode != 0:
                    warning("Homebrew卸载Docker Desktop失败，尝试手动删除...")
                    run_command("sudo rm -rf /Applications/Docker.app")
                
                if not os.path.exists("/Applications/Docker.app"):
                    success("Docker Desktop卸载完成")
                else:
                    warning("Docker Desktop无法完全删除，可能需要手动移除")
            else:
                info("未检测到Docker Desktop，跳过卸载")
            
            return True
        except Exception as e:
            error(f"卸载Docker Desktop失败: {str(e)}")
            raise DockerUninstallError(f"卸载Docker Desktop失败: {str(e)}")
    
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
            
            warning("即将删除所有Docker配置和数据，请确认已备份重要数据")
            
            # Docker Desktop配置目录
            docker_dirs = [
                os.path.expanduser("~/Library/Group Containers/group.com.docker"),
                os.path.expanduser("~/Library/Containers/com.docker.docker"),
                os.path.expanduser("~/Library/Application Support/Docker Desktop"),
                os.path.expanduser("~/Library/Logs/Docker Desktop"),
                os.path.expanduser("~/Library/Preferences/com.docker.docker.plist"),
                os.path.expanduser("~/Library/Saved Application State/com.docker.docker.savedState"),
            ]
            
            for directory in docker_dirs:
                if os.path.exists(directory):
                    info(f"删除目录: {directory}")
                    shutil.rmtree(directory, ignore_errors=True)
            
            success("Docker数据已清除")
            return True
        except Exception as e:
            warning(f"删除Docker数据失败: {str(e)}")
            # 部分失败可以接受，不需要中断整个卸载流程
            return True
    
    def clean_system(self):
        """
        清理系统，Mac不需要特别的清理
        
        Returns:
            bool: 始终返回True
        """
        info("======== Step 4: 清理系统 ========")
        
        try:
            # 清理Homebrew缓存
            run_command("brew cleanup", check=False, verbose=False)
        except:
            pass
        
        success("系统清理完成")
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
