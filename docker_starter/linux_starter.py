#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux版Docker启动器
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.run_command import run_command, CommandError
from shared.logger import info, error, debug, warning, success

from docker_starter.base_starter import BaseDockerStarter, DockerStartError


class LinuxDockerStarter(BaseDockerStarter):
    """Linux系统的Docker启动器实现"""
    
    def is_docker_service_file_exists(self):
        """
        检查Docker服务文件是否存在
        
        Returns:
            bool: 如果服务文件存在返回True，否则返回False
        """
        return os.path.exists("/usr/lib/systemd/system/docker.service") or \
               os.path.exists("/etc/systemd/system/docker.service")
    
    def is_docker_running(self):
        """
        检查Docker是否正在运行
        
        Returns:
            bool: 如果Docker正在运行返回True，否则返回False
        """
        try:
            # 检查Docker服务状态
            if self.is_systemd_available():
                result = run_command("systemctl is-active docker", check=False, verbose=False)
                if result.returncode == 0 and result.stdout.strip() == "active":
                    return True
            
            # 检查Docker进程
            ps_result = run_command("ps aux | grep -v grep | grep dockerd", check=False, verbose=False)
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                return True
                
            # 尝试运行docker命令
            docker_result = run_command("docker info", check=False, verbose=False)
            if docker_result.returncode == 0:
                return True
                
            return False
        except Exception as e:
            debug(f"检查Docker状态时出错: {str(e)}")
            return False
    
    def is_systemd_available(self):
        """
        检查系统是否使用systemd
        
        Returns:
            bool: 如果系统使用systemd返回True，否则返回False
        """
        try:
            result = run_command("which systemctl", check=False, verbose=False)
            return result.returncode == 0
        except:
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
                
            if self.is_systemd_available():
                result = run_command("systemctl status docker", check=False, verbose=False)
                if "active (running)" in result.stdout.lower():
                    return "running"
                elif "inactive (dead)" in result.stdout.lower():
                    return "stopped"
                elif "activating" in result.stdout.lower():
                    return "starting"
                else:
                    return "unknown"
            
            # 如果systemd不可用，通过ps命令检查
            ps_result = run_command("ps aux | grep -v grep | grep dockerd", check=False, verbose=False)
            if ps_result.returncode == 0 and ps_result.stdout.strip():
                return "running"
            else:
                return "stopped"
        except Exception as e:
            error(f"获取Docker状态时出错: {str(e)}")
            return "unknown"
    
    def is_docker_installed(self):
        """
        检查Docker是否已安装
        
        Returns:
            bool: 如果Docker已安装返回True，否则返回False
        """
        try:
            result = run_command("which docker", check=False, verbose=False)
            return result.returncode == 0
        except:
            return False
    
    def start_docker(self):
        """
        启动Docker服务
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerStartError: 如果启动失败
        """
        try:
            info("正在启动Docker服务...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                error("Docker未安装，无法启动")
                raise DockerStartError("Docker未安装，请先安装Docker")
                
            # 检查Docker是否已运行
            if self.is_docker_running():
                info("Docker已经在运行")
                return True
            
            # 尝试通过systemd启动
            if self.is_systemd_available():
                info("通过systemd启动Docker...")
                run_command("sudo systemctl start docker", verbose=True)
                
                # 等待启动完成
                for _ in range(10):  # 等待最多10秒
                    if self.is_docker_running():
                        return True
                    time.sleep(1)
            else:
                # 如果没有systemd，尝试直接启动dockerd
                if os.path.exists("/usr/bin/dockerd"):
                    info("通过直接运行dockerd启动Docker...")
                    
                    # 创建启动脚本
                    start_script = """
#!/bin/bash
killall dockerd 2>/dev/null || true
sleep 1
nohup /usr/bin/dockerd > /var/log/dockerd.log 2>&1 &
echo $! > /var/run/docker.pid
echo "Docker daemon started with PID: $(cat /var/run/docker.pid)"
"""
                    with open("/tmp/start-docker.sh", "w") as f:
                        f.write(start_script)
                        
                    run_command("sudo chmod +x /tmp/start-docker.sh")
                    run_command("sudo /tmp/start-docker.sh", verbose=True)
                    
                    # 等待启动完成
                    for _ in range(10):  # 等待最多10秒
                        if self.is_docker_running():
                            success("Docker服务已手动启动")
                            return True
                        time.sleep(1)
                else:
                    error("无法找到dockerd可执行文件")
                    raise DockerStartError("无法找到dockerd可执行文件")
            
            # 最终检查
            if self.is_docker_running():
                success("Docker服务已成功启动")
                return True
            else:
                error("Docker服务启动失败")
                raise DockerStartError("Docker服务启动失败，请检查系统日志")
                
        except CommandError as e:
            error(f"启动Docker服务失败: {str(e)}")
            raise DockerStartError(f"启动Docker服务失败: {str(e)}")
    
    def stop_docker(self):
        """
        停止Docker服务
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerStartError: 如果停止失败
        """
        try:
            info("正在停止Docker服务...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                warning("Docker未安装，无需停止")
                return True
                
            # 检查Docker是否已运行
            if not self.is_docker_running():
                info("Docker未在运行，无需停止")
                return True
                
            # 尝试通过systemd停止
            if self.is_systemd_available():
                info("通过systemd停止Docker socket和服务...")
                # 先停止docker.socket，再停止docker服务，避免出现"triggering units are still active"错误
                run_command("sudo systemctl stop docker.socket", check=False)
                run_command("sudo systemctl stop docker")
                
                # 等待停止完成
                for _ in range(10):  # 等待最多10秒
                    if not self.is_docker_running():
                        success("Docker服务已停止")
                        return True
                    time.sleep(1)
            else:
                # 如果没有systemd，尝试直接结束进程
                info("通过结束进程停止Docker...")
                run_command("sudo killall dockerd", check=False)
                
                # 等待停止完成
                for _ in range(5):  # 等待最多5秒
                    if not self.is_docker_running():
                        success("Docker进程已终止")
                        return True
                    time.sleep(1)
                    
                # 如果正常停止失败，使用强制停止
                warning("正常停止失败，尝试强制停止...")
                run_command("sudo killall -9 dockerd", check=False)
                time.sleep(2)
            
            # 最终检查
            if not self.is_docker_running():
                success("Docker服务已成功停止")
                return True
            else:
                error("Docker服务停止失败")
                raise DockerStartError("Docker服务停止失败")
                
        except CommandError as e:
            error(f"停止Docker服务失败: {str(e)}")
            raise DockerStartError(f"停止Docker服务失败: {str(e)}")
    
    def restart_docker(self):
        """
        重启Docker服务
        
        Returns:
            bool: 重启成功返回True
            
        Raises:
            DockerStartError: 如果重启失败
        """
        try:
            info("正在重启Docker服务...")
            
            # 检查Docker是否已安装
            if not self.is_docker_installed():
                error("Docker未安装，无法重启")
                raise DockerStartError("Docker未安装，请先安装Docker")
                
            # 先停止Docker
            self.stop_docker()
            
            # 等待一段时间
            time.sleep(2)
            
            # 启动Docker
            return self.start_docker()
                
        except DockerStartError:
            # 如果停止失败，直接尝试启动
            warning("停止Docker失败，尝试直接启动...")
            return self.start_docker()
        except Exception as e:
            error(f"重启Docker服务失败: {str(e)}")
            raise DockerStartError(f"重启Docker服务失败: {str(e)}")
