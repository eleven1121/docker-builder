#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mac系统的Docker启动器实现
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.run_command import run_command, CommandError
from shared.logger import info, error, debug, warning, success

from docker_starter.base_starter import BaseDockerStarter, DockerStartError


class MacDockerStarter(BaseDockerStarter):
    """Mac系统的Docker启动器实现"""
    
    def is_docker_running(self):
        """
        检查Docker是否正在运行
        
        Returns:
            bool: 如果Docker正在运行返回True，否则返回False
        """
        try:
            # 检查Docker Desktop进程是否在运行
            ps_result = run_command("pgrep -f Docker", check=False, verbose=False)
            if ps_result.returncode != 0:
                debug("Docker Desktop进程未运行")
                return False
                
            # 检查Docker命令行工具是否可用
            result = run_command("docker info", check=False, verbose=False)
            if result.returncode != 0:
                debug("docker info命令失败，服务可能未正常运行")
                return False
                
            debug("Docker已经在运行")
            return True
        except Exception as e:
            debug(f"检查Docker运行状态时出错: {str(e)}")
            return False
    
    def get_docker_status(self):
        """
        获取Docker服务状态
        
        Returns:
            str: Docker服务状态描述
        """
        try:
            if not self.is_docker_installed():
                return "not_installed"
                
            # 检查Docker Desktop进程
            ps_result = run_command("pgrep -f Docker", check=False, verbose=False)
            if ps_result.returncode != 0:
                return "stopped"
            
            # 检查Docker API是否可用
            result = run_command("docker info", check=False, verbose=False)
            if result.returncode == 0:
                return "running"
            else:
                # Docker Desktop进程存在但API不可用，可能正在启动
                return "starting"
                
        except Exception as e:
            error(f"获取Docker状态时出错: {str(e)}")
            return "unknown"
    
    def is_docker_installed(self):
        """
        检查Docker Desktop是否已安装
        
        Returns:
            bool: 如果Docker Desktop已安装返回True，否则返回False
        """
        return os.path.exists("/Applications/Docker.app")
    
    def start_docker(self):
        """
        启动Docker Desktop
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerStartError: 如果启动失败
        """
        try:
            info("正在启动Docker Desktop...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                error("Docker Desktop未安装，无法启动")
                raise DockerStartError("Docker Desktop未安装，请先安装Docker")
                
            # 检查Docker是否已运行
            if self.is_docker_running():
                info("Docker Desktop已经在运行")
                return True
            
            # 启动Docker.app
            info("正在启动Docker Desktop...")
            run_command("open -a Docker", verbose=True)
            
            # 等待Docker启动完成
            info("等待Docker Desktop完全启动，这可能需要一些时间...")
            success_msg_shown = False
            
            for i in range(60):  # 等待最多60秒
                if self.is_docker_running():
                    if not success_msg_shown:
                        success("Docker Desktop已成功启动")
                        success_msg_shown = True
                    return True
                    
                if i % 5 == 0:  # 每5秒显示一次等待信息
                    info(f"正在等待Docker Desktop启动...({i}秒)")
                    
                time.sleep(1)
            
            warning("Docker Desktop启动超时，但进程似乎已启动")
            warning("请检查Docker Desktop状态栏图标确认是否已启动")
            
            # 最后再检查一次
            if self.is_docker_running():
                success("Docker Desktop已成功启动")
                return True
            else:
                error("Docker Desktop启动失败")
                raise DockerStartError("Docker Desktop启动失败或超时")
                
        except CommandError as e:
            error(f"启动Docker Desktop失败: {str(e)}")
            raise DockerStartError(f"启动Docker Desktop失败: {str(e)}")
    
    def stop_docker(self):
        """
        停止Docker Desktop
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerStartError: 如果停止失败
        """
        try:
            info("正在停止Docker Desktop...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                warning("Docker Desktop未安装，无需停止")
                return True
                
            # 检查Docker是否已运行
            if not self.is_docker_running():
                info("Docker Desktop未在运行，无需停止")
                return True
            
            # 通过osascript停止Docker Desktop
            info("正在关闭Docker Desktop...")
            script = """
            osascript -e 'quit app "Docker"'
            """
            run_command(script, verbose=True, shell=True)
            
            # 等待Docker停止完成
            info("等待Docker Desktop完全停止...")
            for i in range(30):  # 等待最多30秒
                if not self.is_docker_running():
                    success("Docker Desktop已成功停止")
                    return True
                    
                if i % 5 == 0 and i > 0:  # 每5秒显示一次等待信息
                    info(f"正在等待Docker Desktop停止...({i}秒)")
                    
                time.sleep(1)
            
            # 如果正常停止失败，尝试强制终止进程
            warning("正常停止Docker Desktop超时，尝试强制终止进程...")
            run_command("pkill -9 -f Docker", check=False, verbose=True)
            time.sleep(2)
            
            # 最终检查
            if not self.is_docker_running():
                success("Docker Desktop已成功停止")
                return True
            else:
                error("Docker Desktop停止失败")
                raise DockerStartError("Docker Desktop停止失败，请手动关闭应用")
                
        except CommandError as e:
            error(f"停止Docker Desktop失败: {str(e)}")
            raise DockerStartError(f"停止Docker Desktop失败: {str(e)}")
    
    def restart_docker(self):
        """
        重启Docker Desktop
        
        Returns:
            bool: 重启成功返回True
            
        Raises:
            DockerStartError: 如果重启失败
        """
        try:
            info("正在重启Docker Desktop...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                error("Docker Desktop未安装，无法重启")
                raise DockerStartError("Docker Desktop未安装，请先安装Docker")
                
            # 先停止Docker
            try:
                self.stop_docker()
                # 等待一段时间
                time.sleep(2)
            except DockerStartError as e:
                warning(f"停止Docker Desktop时出现问题: {str(e)}")
                warning("尝试继续启动Docker Desktop...")
                
            # 启动Docker
            return self.start_docker()
                
        except Exception as e:
            error(f"重启Docker Desktop失败: {str(e)}")
            raise DockerStartError(f"重启Docker Desktop失败: {str(e)}")
