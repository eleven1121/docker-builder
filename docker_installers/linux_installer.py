#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux版Docker安装器
"""

import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.run_command import run_command, CommandError
from shared.logger import info, error, debug, warning, success

from docker_installers.base_installer import BaseDockerInstaller, DockerInstallError


class LinuxDockerInstaller(BaseDockerInstaller):
    """Linux系统的Docker安装器实现"""
    
    # Docker服务文件内容
    DOCKER_SERVICE_CONTENT = """
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/bin/dockerd
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutSec=0
RestartSec=2
Restart=always
StartLimitBurst=3
StartLimitInterval=60s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target
"""
    
    def is_docker_service_file_exists(self):
        """
        检查Docker服务文件是否存在
        
        Returns:
            bool: 如果服务文件存在返回True，否则返回False
        """
        return os.path.exists("/usr/lib/systemd/system/docker.service") or \
               os.path.exists("/etc/systemd/system/docker.service")
    
    def is_docker_installed(self):
        """
        检查Docker是否已安装
        
        Returns:
            bool: 如果Docker已安装返回True，否则返回False
        """
        try:
            # 检查Docker可执行文件是否存在
            which_result = run_command("which docker", check=False, verbose=False)
            if which_result.returncode != 0:
                debug("未找到docker可执行文件")
                return False
            
            # 检查Docker相关文件是否存在
            if not os.path.exists("/usr/bin/docker") and not os.path.exists("/usr/local/bin/docker"):
                debug("未找到Docker可执行文件")
                return False
                
            debug("Docker已安装")
            return True
        except Exception as e:
            debug(f"检查Docker安装状态时出错: {str(e)}")
            return False
    
    def is_docker_service_running(self):
        """
        检查Docker服务是否正在运行
        
        Returns:
            bool: 如果Docker服务正在运行返回True，否则返回False
        """
        try:
            result = run_command("sudo systemctl status docker", check=False, verbose=False)
            return "active (running)" in result.stdout.lower()
        except:
            return False
    
    def install_dependencies(self):
        """
        安装Docker所需依赖
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        try:
            info("======== Step 1: 安装Docker所需依赖 ========")
            
            info("安装 dnf-utils")
            run_command("sudo yum install -y dnf-utils")
            
            info("安装 device-mapper-persistent-data")
            run_command("sudo yum install -y device-mapper-persistent-data")
            
            info("安装 lvm2")
            run_command("sudo yum install -y lvm2")
            
            success("所有依赖安装完成")
            return True
        except CommandError as e:
            error(f"安装依赖失败: {str(e)}")
            raise DockerInstallError(f"安装依赖失败: {str(e)}")
    
    def install_docker_engine(self):
        """
        安装Docker引擎
        
        Returns:
            bool: 安装Docker引擎成功返回True
            
        Raises:
            DockerInstallError: 如果安装Docker引擎失败
        """
        try:
            info("======== Step 2: 安装Docker引擎 ========")
            
            # 检查是否已安装Docker
            docker_installed = False
            check_docker = run_command("rpm -q docker", check=False, verbose=False)
            check_moby = run_command("rpm -q moby", check=False, verbose=False)
            
            if check_docker.returncode == 0 or check_moby.returncode == 0:
                info("检测到Docker已安装")
                docker_installed = True
                
            # 如果Docker未安装，或需要安装/重新安装
            if not docker_installed:
                # 检查是否已安装 docker-ce-cli
                check_result = run_command("rpm -q docker-ce-cli", check=False, verbose=False)
                
                if check_result.returncode == 0:
                    info("检测到已安装 docker-ce-cli，正在卸载...")
                    run_command("sudo yum remove -y docker-ce-cli")
                    success("docker-ce-cli 卸载完成")
                    
                info("正在安装Docker，这可能需要一些时间...")
                run_command("sudo yum install -y docker", verbose=True, preserve_color=True)
                success("Docker引擎安装完成")
            else:
                info("使用现有Docker安装")
            
            # 创建Docker服务文件，如果不存在
            self.create_docker_service_file()
                
            return True
        except CommandError as e:
            error(f"Docker引擎安装失败: {str(e)}")
            raise DockerInstallError(f"Docker引擎安装失败: {str(e)}")
    
    def create_docker_service_file(self):
        """
        创建Docker服务文件
        
        Returns:
            bool: 创建成功返回True，否则返回False
        """
        try:
            # 如果服务文件已存在，则无需创建
            if self.is_docker_service_file_exists():
                info("Docker服务文件已存在，无需创建")
                return True
                
            warning("未找到Docker服务文件，正在创建...")
            
            # 创建临时文件
            with open("/tmp/docker.service", "w") as f:
                f.write(self.DOCKER_SERVICE_CONTENT)
                
            # 移动到系统目录
            run_command("sudo mkdir -p /usr/lib/systemd/system/")
            run_command("sudo mv /tmp/docker.service /usr/lib/systemd/system/docker.service")
            run_command("sudo chmod 644 /usr/lib/systemd/system/docker.service")
            
            # 重新加载systemd配置
            run_command("sudo systemctl daemon-reload")
            
            success("Docker服务文件创建完成")
            return True
        except Exception as e:
            error(f"创建Docker服务文件失败: {str(e)}")
            return False
    
    
    def configure_docker(self):
        """
        配置Docker镜像加速等
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        try:
            info("======== Step 3: 配置Docker镜像加速 ========")
            
            # 确保目录存在
            run_command("sudo mkdir -p /etc/docker")
            
            # 创建或更新配置文件
            mirror_config = {
                "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
            }
            
            # 将配置转为JSON并写入文件
            config_json = json.dumps(mirror_config, indent=2)
            
            # 使用临时文件并sudo移动到目标位置
            with open("/tmp/docker_daemon.json", "w") as f:
                f.write(config_json)
            
            run_command("sudo mv /tmp/docker_daemon.json /etc/docker/daemon.json")
            success("镜像加速配置完成")
            return True
        except Exception as e:
            error(f"配置镜像加速失败: {str(e)}")
            raise DockerInstallError(f"配置镜像加速失败: {str(e)}")
    
    
    def uninstall_docker(self):
        """
        卸载Docker
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerInstallError: 如果卸载失败
        """
        try:
            info("卸载Docker...")
            
            # 先停止Docker socket，再停止Docker服务
            info("停止Docker socket和服务...")
            run_command("sudo systemctl stop docker.socket", check=False)
            run_command("sudo systemctl stop docker", check=False)
            
            # 卸载Docker包
            run_command("sudo yum remove -y docker docker-client docker-client-latest docker-common "
                       "docker-latest docker-latest-logrotate docker-logrotate docker-engine "
                       "docker-ce docker-ce-cli containerd.io", check=False)
            
            # 清理配置和数据
            run_command("sudo rm -rf /var/lib/docker", check=False)
            run_command("sudo rm -rf /etc/docker", check=False)
            
            success("Docker已成功卸载")
            return True
        except CommandError as e:
            error(f"卸载Docker失败: {str(e)}")
            raise DockerInstallError(f"卸载Docker失败: {str(e)}")
