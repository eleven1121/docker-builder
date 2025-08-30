#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mac系统的Docker安装器实现
"""

import sys
import os
import json
import platform
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.run_command import run_command, CommandError
from shared.logger import info, error, debug, warning, success

from docker_installers.base_installer import BaseDockerInstaller, DockerInstallError


class MacDockerInstaller(BaseDockerInstaller):
    """Mac系统的Docker安装器实现"""
    
    def is_docker_installed(self):
        """
        检查Docker是否已安装
        
        Returns:
            bool: 如果Docker已安装返回True，否则返回False
        """
        try:
            # 检查Docker.app是否存在
            if not os.path.exists("/Applications/Docker.app"):
                debug("Docker.app不存在于应用程序文件夹")
                return False
                
            # 检查Docker命令行工具是否存在
            which_result = run_command("which docker", check=False, verbose=False)
            if which_result.returncode != 0:
                debug("未找到docker命令行工具")
                return False
                
            debug("Docker已安装")
            return True
        except Exception as e:
            debug(f"检查Docker安装状态时出错: {str(e)}")
            return False
    
    def install_dependencies(self):
        """
        Mac系统安装依赖项，主要是安装Homebrew
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        try:
            info("======== Step 1: 检查并安装依赖 ========")
            
            # 检查Homebrew是否已安装
            brew_check = run_command("which brew", check=False, verbose=False)
            
            if brew_check.returncode != 0:
                info("Homebrew未安装，需要先安装Homebrew")
                warning("请手动安装Homebrew，执行以下命令:")
                info('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
                raise DockerInstallError("请先安装Homebrew，然后再次运行此安装程序")
            
            success("依赖检查完成")
            return True
        except CommandError as e:
            error(f"依赖检查失败: {str(e)}")
            raise DockerInstallError(f"依赖检查失败: {str(e)}")
    
    def install_docker_engine(self):
        """
        Mac系统安装Docker Desktop
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        try:
            info("======== Step 2: 安装Docker Desktop ========")
            
            # 检查Docker Desktop是否已安装
            if os.path.exists("/Applications/Docker.app"):
                info("Docker Desktop已安装，跳过安装步骤")
                return True
                
            # 询问用户选择安装方式
            info("请选择Docker Desktop安装方式:")
            info("1. 使用Homebrew安装 (推荐)")
            info("2. 手动下载安装")
            choice = input("请选择 [1/2] 默认为1: ")
            
            # 默认选择Homebrew安装
            choice = choice.strip() if choice.strip() else "1"
            
            if choice == "1":
                # 使用Homebrew安装Docker
                return self._install_with_homebrew()
            else:
                # 手动安装Docker
                return self._install_manually()
                
        except CommandError as e:
            error(f"Docker Desktop安装失败: {str(e)}")
            warning("请手动下载并安装Docker Desktop")
            return self._install_manually()
        except Exception as e:
            error(f"Docker Desktop安装过程中发生未预期的异常: {str(e)}")
            warning("请手动下载并安装Docker Desktop")
            return self._install_manually()
    
    def _install_with_homebrew(self):
        """
        使用Homebrew安装Docker Desktop
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        try:
            info("使用Homebrew安装Docker Desktop...")
            info("这可能需要几分钟时间，请耐心等待")
            
            run_command("brew install --cask docker", verbose=True)
            
            # 检查安装是否成功
            if not os.path.exists("/Applications/Docker.app"):
                warning("Homebrew安装完成，但Docker Desktop未找到")
                return self._install_manually()
                
            success("Docker Desktop安装完成")
            return True
            
        except Exception as e:
            warning(f"Homebrew安装失败: {str(e)}")
            return self._install_manually()
    
    def _install_manually(self):
        """
        指导用户手动安装Docker Desktop
        
        Returns:
            bool: 如果用户确认完成安装返回True
        """
        docker_arm_url = "https://desktop.docker.com/mac/main/arm64/Docker.dmg"
        docker_intel_url = "https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        
        # 检测Mac芯片类型
        is_apple_silicon = platform.processor() == 'arm'
        download_url = docker_arm_url if is_apple_silicon else docker_intel_url
        
        info("请按照以下步骤手动安装Docker Desktop:")
        info(f"1. 下载Docker Desktop DMG文件: {download_url}")
        info("2. 打开下载的DMG文件")
        info("3. 将Docker图标拖到Applications文件夹")
        info("4. 从应用程序文件夹启动Docker Desktop")
        
        # 尝试自动打开下载链接
        try:
            info("正在打开下载链接...")
            run_command(f"open {download_url}", check=False)
        except:
            pass
            
        # 等待用户确认完成安装
        confirm = input("安装完成后，请输入'y'继续: ").lower()
        
        if confirm == 'y':
            # 再次检查安装
            if os.path.exists("/Applications/Docker.app"):
                success("Docker Desktop已成功安装")
                return True
            else:
                warning("未检测到Docker Desktop，请确保已正确安装")
                return True  # 用户确认安装了，即使我们没有检测到
        else:
            warning("取消安装Docker Desktop")
            raise DockerInstallError("用户取消安装Docker Desktop")
    
    
    def configure_docker(self):
        """
        配置Docker Desktop的镜像加速等
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        try:
            info("======== Step 3: 配置Docker镜像加速 ========")
            
            # Docker Desktop配置文件路径
            config_dir = os.path.expanduser("~/Library/Group Containers/group.com.docker/settings.json")
            
            if not os.path.exists(os.path.dirname(config_dir)):
                warning("Docker Desktop配置目录不存在，请先启动Docker Desktop一次")
                info("请启动Docker Desktop后再运行此脚本进行配置")
                return True
            
            # 读取现有配置
            try:
                if os.path.exists(config_dir):
                    with open(config_dir, 'r') as f:
                        config = json.load(f)
                else:
                    config = {}
            except Exception:
                config = {}
            
            # 添加或更新镜像配置
            if 'registryMirrors' not in config:
                config['registryMirrors'] = []
            
            # 添加镜像
            mirrors = ["https://mirror.ccs.tencentyun.com", "https://docker.mirrors.ustc.edu.cn"]
            changed = False
            
            for mirror in mirrors:
                if mirror not in config['registryMirrors']:
                    config['registryMirrors'].append(mirror)
                    changed = True
                
            if changed:
                # 保存配置
                with open(config_dir, 'w') as f:
                    json.dump(config, f, indent=2)
                
                info("镜像加速已添加，需要重启Docker Desktop使配置生效")
            else:
                info("镜像加速已配置")
            
            success("Docker镜像加速配置完成")
            return True
        except Exception as e:
            warning(f"配置镜像加速失败，可能需要手动配置: {str(e)}")
            info("请手动在Docker Desktop的设置中添加镜像")
            return True  # 返回True因为这不是关键错误
    
    
    def uninstall_docker(self):
        """
        卸载Docker Desktop
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerInstallError: 如果卸载失败
        """
        try:
            info("卸载Docker Desktop...")
            
            # 检查Docker Desktop是否已安装
            if not os.path.exists("/Applications/Docker.app"):
                info("Docker Desktop未安装，无需卸载")
                return True
            
            # 关闭Docker Desktop
            info("关闭Docker Desktop...")
            run_command("pkill -f Docker", check=False)
            
            # 卸载Docker Desktop
            info("删除Docker Desktop应用...")
            run_command("rm -rf /Applications/Docker.app", check=False)
            
            # 清理Docker Desktop相关文件
            info("清理Docker Desktop配置文件...")
            paths_to_remove = [
                "~/Library/Group Containers/group.com.docker",
                "~/Library/Containers/com.docker.docker",
                "~/Library/Application Support/Docker Desktop",
                "~/Library/Logs/Docker Desktop",
                "~/Library/Preferences/com.docker.docker.plist",
                "~/Library/Saved Application State/com.electron.docker-frontend.savedState",
            ]
            
            for path in paths_to_remove:
                full_path = os.path.expanduser(path)
                run_command(f"rm -rf '{full_path}'", check=False)
            
            success("Docker Desktop已成功卸载")
            return True
        except Exception as e:
            error(f"卸载Docker Desktop失败: {str(e)}")
            warning("请尝试手动卸载Docker Desktop")
            return False
