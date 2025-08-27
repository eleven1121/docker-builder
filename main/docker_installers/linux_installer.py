#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux版Docker安装器
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent.parent))

from shared.run_command import run_command, CommandError
from shared.logger import info, error, debug, warning, success

from docker_installers.base_installer import BaseDockerInstaller, DockerInstallError
from check_system import is_tencent_os, get_linux_distribution


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
    
    def update_system(self):
        """
        更新Linux系统
        
        Returns:
            bool: 更新成功返回True
            
        Raises:
            DockerInstallError: 如果更新失败
        """
        try:
            info("======== Step 1: 更新系统 ========")
            run_command("sudo yum update -y")
            run_command("sudo yum clean all")
            success("系统更新完成")
            return True
        except CommandError as e:
            error(f"系统更新失败: {str(e)}")
            raise DockerInstallError(f"系统更新失败: {str(e)}")
    
    def install_dependencies(self):
        """
        安装Docker所需依赖
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        try:
            info("======== Step 2: 安装Docker所需依赖 ========")
            
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
            info("======== Step 3: 安装Docker引擎 ========")
            
            # 检查是否为TencentOS
            if is_tencent_os():
                info("检测到TencentOS Server，使用特定安装方法")
                
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
    
    def install_docker_compose(self):
        """
        安装Docker Compose插件
        
        Returns:
            bool: 安装Docker Compose成功返回True
            
        Raises:
            DockerInstallError: 如果安装Docker Compose失败
        """
        try:
            info("======== Step 4: 安装Docker Compose插件 ========")
            run_command("sudo yum install -y docker-compose")
            success("Docker Compose安装完成")
            return True
        except CommandError as e:
            error(f"Docker Compose安装失败: {str(e)}")
            raise DockerInstallError(f"Docker Compose安装失败: {str(e)}")
    
    def configure_docker(self):
        """
        配置Docker镜像加速等
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        try:
            info("======== Step 5: 配置腾讯云镜像加速 ========")
            
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
            success("腾讯云镜像加速配置完成")
            return True
        except Exception as e:
            error(f"配置镜像加速失败: {str(e)}")
            raise DockerInstallError(f"配置镜像加速失败: {str(e)}")
    
    def start_docker_service(self):
        """
        启动Docker服务
        
        Returns:
            bool: 启动Docker服务成功返回True
            
        Raises:
            DockerInstallError: 如果启动Docker服务失败
        """
        try:
            info("======== Step 6: 启动Docker服务 ========")
            
            # 确保Docker服务文件存在
            self.create_docker_service_file()
            
            # 尝试启用和启动Docker服务
            info("启用Docker服务自启...")
            enable_result = run_command("sudo systemctl enable docker", check=False, verbose=False)
            
            if enable_result.returncode != 0:
                warning(f"启用Docker服务失败: {enable_result.stderr}")
                
            info("启动Docker服务...")
            restart_result = run_command("sudo systemctl restart docker", check=False, verbose=True)
            
            # 验证Docker状态
            if self.is_docker_service_running():
                success("Docker服务已成功启动并设置为开机自启")
                return True
            else:
                warning("Docker服务启动失败，尝试替代方法")
                
                # 如果是TencentOS，尝试替代方法
                if is_tencent_os():
                    info("在TencentOS上使用替代方法启动Docker服务...")
                    
                    # 检查dockerd是否存在
                    if os.path.exists("/usr/bin/dockerd"):
                        info("使用nohup启动Docker守护进程...")
                        
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
                        
                        # 等待Docker启动
                        import time
                        info("等待Docker启动...")
                        time.sleep(5)
                        
                        # 检查Docker是否运行
                        check_result = run_command("sudo docker info", check=False, verbose=False)
                        if check_result.returncode == 0:
                            success("Docker守护进程已手动启动")
                            return True
                        else:
                            error(f"Docker守护进程无法启动: {check_result.stderr}")
                            raise DockerInstallError("Docker服务启动失败")
                    else:
                        error("无法找到dockerd可执行文件")
                        
                # 所有方法失败
                error("Docker服务启动失败，请检查系统日志")
                raise DockerInstallError("Docker服务启动失败")
                
        except CommandError as e:
            error(f"启动Docker服务失败: {str(e)}")
            raise DockerInstallError(f"启动Docker服务失败: {str(e)}")
    
    def install_docker(self):
        """
        安装Docker的主方法，调用install_docker_full实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        return self.install_docker_full()
