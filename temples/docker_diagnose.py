#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker服务诊断脚本
用于诊断Docker服务启动失败的问题并提供解决方案
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command


def check_docker_service_status():
    """
    检查Docker服务的详细状态
    """
    info("检查Docker服务状态...")
    exit_code, stdout, stderr = run_command("systemctl status docker.service")
    
    if stdout:
        info("Docker服务状态:")
        print(stdout)
    
    if stderr:
        warning("错误输出:")
        print(stderr)
    
    return exit_code


def check_docker_journal_logs():
    """
    查看Docker服务的详细日志
    """
    info("获取Docker服务详细日志...")
    exit_code, stdout, stderr = run_command("journalctl -xeu docker.service --no-pager -n 50")
    
    if stdout:
        info("Docker服务日志:")
        print(stdout)
    
    if stderr:
        warning("错误输出:")
        print(stderr)
    
    return exit_code


def check_disk_space():
    """
    检查磁盘空间
    """
    info("检查磁盘空间...")
    exit_code, stdout, stderr = run_command("df -h")
    
    if stdout:
        info("磁盘空间状态:")
        print(stdout)
    
    return exit_code


def check_docker_config():
    """
    检查Docker配置文件
    """
    info("检查Docker配置文件...")
    config_files = [
        "/etc/docker/daemon.json",
        "/lib/systemd/system/docker.service",
        "/etc/systemd/system/docker.service"
    ]
    
    for config_file in config_files:
        info(f"检查配置文件: {config_file}")
        if os.path.exists(config_file):
            exit_code, stdout, stderr = run_command(f"cat {config_file}")
            if stdout:
                print(stdout)
            success(f"{config_file} 文件存在")
        else:
            warning(f"{config_file} 文件不存在")


def analyze_common_issues():
    """
    分析常见的Docker启动失败原因
    """
    info("分析常见的Docker启动问题...")
    
    # 检查Docker是否被其他进程锁定
    exit_code, stdout, stderr = run_command("ps aux | grep -i docker | grep -v grep")
    if stdout:
        info("发现Docker相关进程:")
        print(stdout)
    
    # 检查Docker数据目录权限
    exit_code, stdout, stderr = run_command("ls -la /var/lib/docker 2>/dev/null || echo '目录不存在或无权限访问'")
    if stdout:
        info("Docker数据目录权限:")
        print(stdout)


def suggest_solutions():
    """
    提供常见解决方案建议
    """
    info("\n===== 可能的解决方案 =====")
    print("1. 重置Docker数据目录:")
    print("   sudo systemctl stop docker")
    print("   sudo rm -rf /var/lib/docker")
    print("   sudo systemctl start docker\n")
    
    print("2. 检查并修复Docker配置:")
    print("   sudo nano /etc/docker/daemon.json")
    print("   确保JSON格式正确且没有语法错误\n")
    
    print("3. 重新加载系统服务:")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl restart docker\n")
    
    print("4. 检查Docker依赖项:")
    print("   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin")
    print("   或")
    print("   sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin\n")
    
    print("5. 检查内核支持:")
    print("   lsmod | grep overlay")
    print("   如果没有输出，运行: sudo modprobe overlay\n")


def main():
    """
    主函数，执行Docker服务诊断
    
    Returns:
        int: 执行结果，0表示成功，非0表示失败
    """
    info("=== Docker服务诊断工具 ===")
    
    try:
        # 检查是否为root用户
        if os.geteuid() != 0:
            warning("建议使用root权限运行此脚本以获取完整诊断信息")
            warning("请尝试使用sudo重新运行")
        
        # 执行诊断步骤
        check_docker_service_status()
        check_docker_journal_logs()
        check_disk_space()
        check_docker_config()
        analyze_common_issues()
        suggest_solutions()
        
        success("诊断完成!")
        return 0
        
    except Exception as e:
        error(f"诊断过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
