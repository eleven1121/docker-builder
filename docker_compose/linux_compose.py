#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux系统Docker Compose管理器
提供在Linux系统上安装、重新安装和管理Docker Compose的功能
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command, CommandError
from docker_compose.compose_manager import ComposeError
from docker_compose.base_compose_manager import BaseComposeManager


class LinuxComposeManager(BaseComposeManager):
    """Linux系统下的Docker Compose管理器"""
    
    def install_compose(self, version=None):
        """
        在Linux上安装Docker Compose
        
        Args:
            version: 指定要安装的版本，如果为None则安装最新版本
            
        Returns:
            bool: 安装成功返回True
            
        Raises:
            ComposeError: 安装失败时抛出异常
        """
        info("在Linux上安装Docker Compose...")
        
        # 尝试使用包管理器安装
        try:
            # 检查是哪种Linux发行版
            if os.path.exists("/usr/bin/apt-get"):  # Debian/Ubuntu
                run_command("sudo apt-get update", verbose=True)
                run_command("sudo apt-get install -y docker-compose", verbose=True)
            elif os.path.exists("/usr/bin/yum"):  # CentOS/RHEL
                run_command("sudo yum install -y docker-compose", verbose=True)
            else:
                # 如果包管理器安装不可用，使用pip安装
                run_command("sudo pip3 install docker-compose", verbose=True)
    
            return True
        except Exception as e:
            warning(f"使用包管理器安装失败: {str(e)}，尝试使用pip安装...")
            
            # 尝试使用pip安装
            try:
                run_command("sudo pip3 install docker-compose", verbose=True)
                success("Docker Compose已通过pip成功安装")
                return True
            except Exception as pip_error:
                error(f"使用pip安装Docker Compose失败: {str(pip_error)}")
                raise ComposeError(f"在Linux上安装Docker Compose失败: {str(pip_error)}")
    
    def reinstall_compose(self, version=None):
        """
        在Linux上重新安装Docker Compose
        
        Args:
            version: 指定要安装的版本，如果为None则安装最新版本
            
        Returns:
            bool: 安装成功返回True
            
        Raises:
            ComposeError: 安装失败时抛出异常
        """
        info("在Linux上重新安装Docker Compose...")
        
        # 首先尝试卸载现有的Docker Compose
        try:
            if os.path.exists("/usr/local/bin/docker-compose"):
                run_command("sudo rm /usr/local/bin/docker-compose", check=False, verbose=True)
            
            # 尝试使用pip卸载
            run_command("sudo pip3 uninstall -y docker-compose", check=False, verbose=True)
            
            # 尝试使用包管理器卸载
            if os.path.exists("/usr/bin/apt-get"):
                run_command("sudo apt-get remove -y docker-compose", check=False, verbose=True)
            elif os.path.exists("/usr/bin/yum"):
                run_command("sudo yum remove -y docker-compose", check=False, verbose=True)
        except Exception as e:
            warning(f"卸载Docker Compose时出现警告（这可能不是问题）: {str(e)}")
        
        # 安装新版本
        info("开始安装Docker Compose...")
        return self.install_compose(version=version)
    
    def is_compose_installed(self):
        """
        检查Docker Compose是否已安装
        
        Returns:
            bool: 如果Docker Compose已安装返回True，否则返回False
        """
        try:
            # 尝试执行Docker Compose命令
            result = run_command("docker-compose --version", check=False, verbose=False)
            if result.returncode == 0:
                return True
                
            # 尝试执行新版Docker Compose命令
            result = run_command("docker compose version", check=False, verbose=False)
            return result.returncode == 0
            
        except Exception as e:
            debug(f"检查Docker Compose是否安装时出错: {str(e)}")
            return False
    
    def get_compose_version(self):
        """
        获取Docker Compose版本
        
        Returns:
            str: Docker Compose版本号，如果未安装则返回None
        """
        try:
            compose_cmd = self.get_compose_cmd()
            version_cmd = f"{compose_cmd} version"
            
            result = run_command(version_cmd, check=False, verbose=False)
            if result.returncode != 0:
                return None
            
            # 解析版本号
            version_output = result.stdout.lower()
            if "version" in version_output:
                # 提取版本号
                version_match = re.search(r"version\s+v?([0-9.]+)", version_output)
                if version_match:
                    return version_match.group(1)
            
            return "未知版本"
        except Exception as e:
            debug(f"获取Docker Compose版本时出错: {str(e)}")
            return None
    
    def get_compose_cmd(self):
        """
        获取docker-compose命令
        
        Returns:
            str: docker-compose命令
        """
        try:
            # 首先尝试旧版命令
            result = run_command("docker-compose --version", check=False, verbose=False)
            if result.returncode == 0:
                return "docker-compose"
            
            # 尝试新版命令格式
            result = run_command("docker compose version", check=False, verbose=False)
            if result.returncode == 0:
                return "docker compose"
            
            # 如果都不可用，则返回默认的新版命令格式
            return "docker compose"
        except Exception as e:
            debug(f"获取docker-compose命令时出错: {str(e)}")
            return "docker compose"  # 默认使用新版命令格式
