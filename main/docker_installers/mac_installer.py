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
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_installer import BaseDockerInstaller, DockerInstallError


class MacDockerInstaller(BaseDockerInstaller):
    """Mac系统的Docker安装器实现"""
    
    def update_system(self):
        """
        Mac系统不需要特别的系统更新
        
        Returns:
            bool: 始终返回True
        """
        info("======== Step 1: 检查系统 ========")
        # 检查是否是支持的macOS版本
        version = platform.mac_ver()[0]
        info(f"检测到macOS版本: {version}")
        
        # 检查是否是Apple Silicon芯片
        is_apple_silicon = platform.processor() == 'arm'
        chip_info = "Apple Silicon (ARM)" if is_apple_silicon else "Intel"
        info(f"检测到Mac芯片: {chip_info}")
        
        success("系统检查完成")
        return True
    
    def install_dependencies(self):
        """
        Mac系统安装依赖项，主要是安装Homebrew
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        try:
            info("======== Step 2: 检查并安装依赖 ========")
            
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
            info("======== Step 3: 安装Docker Desktop ========")
            
            # 检查Docker Desktop是否已安装
            if os.path.exists("/Applications/Docker.app"):
                info("Docker Desktop已安装，跳过安装步骤")
                return True
            
            # 使用Homebrew安装Docker
            info("使用Homebrew安装Docker Desktop...")
            run_command("brew install --cask docker")
            
            if not os.path.exists("/Applications/Docker.app"):
                raise DockerInstallError("Docker Desktop安装失败，请手动下载并安装Docker Desktop")
            
            success("Docker Desktop安装完成")
            return True
        except CommandError as e:
            error(f"Docker Desktop安装失败: {str(e)}")
            warning("请手动下载并安装Docker Desktop，下载地址: https://www.docker.com/products/docker-desktop")
            raise DockerInstallError(f"Docker Desktop安装失败: {str(e)}")
    
    def install_docker_compose(self):
        """
        Mac系统的Docker Desktop已包含Docker Compose
        
        Returns:
            bool: 始终返回True
        """
        info("======== Step 4: 检查Docker Compose ========")
        info("Docker Desktop for Mac已包含Docker Compose，无需单独安装")
        success("Docker Compose检查完成")
        return True
    
    def configure_docker(self):
        """
        配置Docker Desktop的镜像加速等
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        try:
            info("======== Step 5: 配置Docker镜像加速 ========")
            
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
            
            # 添加腾讯云镜像
            tencent_mirror = "https://mirror.ccs.tencentyun.com"
            if tencent_mirror not in config['registryMirrors']:
                config['registryMirrors'].append(tencent_mirror)
                
                # 保存配置
                with open(config_dir, 'w') as f:
                    json.dump(config, f, indent=2)
                
                info("腾讯云镜像加速已添加，需要重启Docker Desktop使配置生效")
            else:
                info("腾讯云镜像加速已配置")
            
            success("Docker镜像加速配置完成")
            return True
        except Exception as e:
            warning(f"配置镜像加速失败，可能需要手动配置: {str(e)}")
            info("请手动在Docker Desktop的设置中添加镜像: https://mirror.ccs.tencentyun.com")
            return True  # 返回True因为这不是关键错误
    
    def start_docker_service(self):
        """
        启动Docker Desktop
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerInstallError: 如果启动失败
        """
        try:
            info("======== Step 6: 启动Docker Desktop ========")
            
            # 检查Docker Desktop是否已运行
            ps_result = run_command("pgrep -f Docker", check=False, verbose=False)
            if ps_result.returncode == 0:
                info("Docker Desktop已经在运行")
            else:
                info("正在启动Docker Desktop...")
                run_command("open /Applications/Docker.app")
                info("Docker Desktop已启动，请等待其完全初始化")
                warning("首次启动可能需要几分钟时间，请耐心等待")
                info("您可能需要输入管理员密码以授权Docker Desktop")
            
            info("请确认Docker Desktop状态栏图标显示Docker已经启动")
            success("Docker Desktop启动流程完成")
            return True
        except CommandError as e:
            error(f"启动Docker Desktop失败: {str(e)}")
            warning("请手动启动Docker Desktop应用")
            return True  # 返回True因为用户可能会手动启动
    
    def install_docker(self):
        """
        安装Docker的主方法，调用install_docker_full实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        return self.install_docker_full()
