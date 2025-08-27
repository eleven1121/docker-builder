#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装工具 (Python版本)
检查系统环境并在Linux系统上安装Docker及相关组件
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

# 获取项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
ROOT_DIR = SCRIPT_DIR.parent
SHARED_DIR = ROOT_DIR / "shared"

# 添加shared目录到sys.path以便导入
sys.path.append(str(ROOT_DIR))

# 导入日志模块和命令执行模块
from shared.logger import logger, info, error, debug, warning, success
from shared.run_command import run_command, CommandError


class DockerInstallError(Exception):
    """Docker安装过程中遇到的异常"""
    pass


def is_linux():
    """
    检查当前系统是否为Linux
    
    Returns:
        bool: 如果是Linux返回True，否则返回False
    """
    return platform.system().lower() == 'linux'


def update_system():
    """
    Step 1: 更新系统
    
    Returns:
        bool: 更新成功返回True，否则抛出异常
        
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


def install_dependencies():
    """
    Step 2: 安装Docker所需依赖
    
    Returns:
        bool: 安装依赖成功返回True，否则抛出异常
        
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


def install_docker():
    """
    Step 3: 安装Docker
    
    Returns:
        bool: 安装Docker成功返回True，否则抛出异常
        
    Raises:
        DockerInstallError: 如果安装Docker失败
    """
    try:
        info("======== Step 3: 安装Docker ========")
        
        # 检查是否已安装 docker-ce-cli
        check_result = run_command("rpm -q docker-ce-cli", check=False, verbose=False)
        
        if check_result.returncode == 0:
            info("检测到已安装 docker-ce-cli，正在卸载...")
            run_command("sudo yum remove -y docker-ce-cli")
            success("docker-ce-cli 卸载完成")
            
        run_command("sudo yum install -y docker")
        success("Docker安装完成")
        return True
    except CommandError as e:
        error(f"Docker安装失败: {str(e)}")
        raise DockerInstallError(f"Docker安装失败: {str(e)}")


def install_docker_compose():
    """
    Step 4: 安装Docker Compose插件
    
    Returns:
        bool: 安装Docker Compose成功返回True，否则抛出异常
        
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


def configure_mirror():
    """
    Step 5: 配置腾讯云镜像加速
    
    Returns:
        bool: 配置镜像加速成功返回True，否则抛出异常
        
    Raises:
        DockerInstallError: 如果配置镜像加速失败
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
        import json
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


def start_docker_service():
    """
    Step 6: 启动Docker服务
    
    Returns:
        bool: 启动Docker服务成功返回True，否则抛出异常
        
    Raises:
        DockerInstallError: 如果启动Docker服务失败
    """
    try:
        info("======== Step 6: 启动Docker服务 ========")
        run_command("sudo systemctl enable docker")
        run_command("sudo systemctl restart docker")
        
        # 验证Docker状态
        result = run_command("sudo systemctl status docker", verbose=True, preserve_color=True)
        
        if "running" in result.stdout.lower():
            success("Docker服务已成功启动并设置为开机自启")
        else:
            raise DockerInstallError("Docker服务启动失败")
            
        return True
    except CommandError as e:
        error(f"启动Docker服务失败: {str(e)}")
        raise DockerInstallError(f"启动Docker服务失败: {str(e)}")


def install_docker_full():
    """
    执行完整的Docker安装流程
    
    Returns:
        bool: 安装成功返回True，否则抛出异常
        
    Raises:
        DockerInstallError: 如果安装过程中任何步骤失败
    """
    try:
        info("开始Docker安装流程...")
        
        # 检查是否为Linux系统
        if not is_linux():
            raise DockerInstallError("当前系统不是Linux，无法安装Docker")
        
        # 逐步执行安装
        update_system()
        install_dependencies()
        install_docker()
        install_docker_compose()
        configure_mirror()
        start_docker_service()
        
        success("Docker安装成功完成！")
        return True
    except DockerInstallError as e:
        error(f"Docker安装失败: {str(e)}")
        raise  # 重新抛出异常给调用者
    except Exception as e:
        error(f"Docker安装过程中发生未预期的异常: {str(e)}")
        raise DockerInstallError(f"Docker安装过程中发生未预期的异常: {str(e)}")


if __name__ == "__main__":
    try:
        if not is_linux():
            error("错误: 当前系统不是Linux。Docker只能在Linux系统上安装。")
            sys.exit(1)
            
        install_docker_full()
        sys.exit(0)  # 安装成功，退出码为0
    except Exception as e:
        error(f"安装失败: {str(e)}")
        sys.exit(1)  # 安装失败，退出码为1
