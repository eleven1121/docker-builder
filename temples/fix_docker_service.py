#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker服务修复脚本
用于解决Docker服务启动失败和"Start request repeated too quickly"错误
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command


def check_journalctl_logs():
    """
    获取Docker日志的详细信息，找出启动失败的根本原因
    """
    info("获取Docker服务的详细日志...")
    exit_code, stdout, stderr = run_command("journalctl -u docker.service --no-pager -n 50")
    
    if stdout:
        info("Docker详细日志:")
        print(stdout)
    
    return exit_code


def check_docker_config():
    """
    检查Docker配置文件是否存在语法问题
    """
    info("检查Docker配置文件...")
    config_path = "/etc/docker/daemon.json"
    
    # 检查配置文件是否存在
    exit_code, stdout, stderr = run_command(f"test -f {config_path} && echo '存在' || echo '不存在'")
    if "不存在" in stdout:
        warning(f"配置文件 {config_path} 不存在")
        return
    
    # 查看配置文件内容
    exit_code, stdout, stderr = run_command(f"cat {config_path}")
    if stdout:
        info(f"{config_path} 内容:")
        print(stdout)
    
    # 验证JSON格式
    exit_code, stdout, stderr = run_command(f"python3 -c \"import json; json.load(open('{config_path}'))\" 2>&1")
    if exit_code != 0:
        error(f"配置文件JSON格式错误: {stderr}")
        return False
    else:
        success("配置文件JSON格式正确")
        return True


def reset_systemd_start_limit():
    """
    重置systemd的启动限制，解决"Start request repeated too quickly"错误
    """
    info("重置systemd启动限制...")
    commands = [
        "sudo systemctl reset-failed docker.service",
        "sudo systemctl stop docker.socket",
        "sudo systemctl stop docker.service",
        "sudo systemctl daemon-reload"
    ]
    
    for cmd in commands:
        info(f"执行: {cmd}")
        exit_code, stdout, stderr = run_command(cmd)
        if exit_code != 0:
            warning(f"命令执行可能有问题: {stderr}")


def fix_docker_daemon_config():
    """
    备份并修复Docker daemon配置文件
    """
    info("修复Docker配置文件...")
    config_path = "/etc/docker/daemon.json"
    
    # 备份现有配置
    if os.path.exists(config_path):
        backup_cmd = f"sudo cp {config_path} {config_path}.bak.$(date +%Y%m%d_%H%M%S)"
        exit_code, stdout, stderr = run_command(backup_cmd)
        if exit_code == 0:
            success(f"已备份配置文件到 {config_path}.bak.YYYYMMDD_HHMMSS")
        
        # 如果配置文件有JSON格式错误，尝试修复
        if not check_docker_config():
            info("尝试修复配置文件...")
            # 读取内容并尝试修复基本的JSON语法问题
            exit_code, stdout, stderr = run_command(f"cat {config_path}")
            if stdout:
                try:
                    import json
                    fixed_content = stdout
                    # 尝试添加缺失的引号、逗号等
                    # 这里是简单的修复尝试，可能不适用于所有情况
                    fixed_content = fixed_content.replace("'", "\"")
                    # 创建一个临时文件
                    with open("/tmp/docker_daemon_fixed.json", "w") as f:
                        f.write(fixed_content)
                    
                    # 验证修复后的JSON
                    try:
                        with open("/tmp/docker_daemon_fixed.json") as f:
                            json.load(f)
                        # 如果成功解析，替换原配置
                        exit_code, stdout, stderr = run_command(f"sudo cp /tmp/docker_daemon_fixed.json {config_path}")
                        if exit_code == 0:
                            success("配置文件已修复")
                    except json.JSONDecodeError:
                        error("自动修复失败，建议手动编辑配置文件")
                        # 提供一个最小可用的配置
                        info("以下是一个基本可用的Docker配置模板:")
                        print('''{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com"],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}''')
                except Exception as e:
                    error(f"修复过程出错: {str(e)}")


def reset_docker_service():
    """
    完全重置Docker服务
    """
    info("尝试完全重置Docker服务...")
    commands = [
        "sudo systemctl stop docker.socket docker.service",
        "sudo rm -rf /var/lib/docker/runtimes",  # 删除运行时文件，但保留镜像等数据
        "sudo systemctl daemon-reload",
        "sudo systemctl start docker"
    ]
    
    for cmd in commands:
        info(f"执行: {cmd}")
        exit_code, stdout, stderr = run_command(cmd)
        if exit_code != 0 and "docker.socket" in cmd:
            # 如果停止服务失败，不要中断流程
            warning(f"警告: {stderr}")
        elif exit_code != 0 and "start docker" in cmd:
            error(f"启动Docker失败: {stderr}")
            return False
    
    # 验证Docker是否正常启动
    exit_code, stdout, stderr = run_command("sudo systemctl status docker")
    if "Active: active (running)" in stdout:
        success("Docker服务已成功启动!")
        return True
    else:
        warning("Docker服务可能仍然有问题，请查看状态:")
        print(stdout)
        return False


def main():
    """
    主函数，执行Docker服务修复
    
    Returns:
        int: 执行结果，0表示成功，非0表示失败
    """
    info("=== Docker服务修复工具 ===")
    
    try:
        # 检查是否为root用户
        if os.geteuid() != 0:
            error("此脚本需要root权限才能执行")
            error("请使用sudo重新运行此脚本")
            return 1
        
        # 获取详细日志
        check_journalctl_logs()
        
        # 检查配置
        check_docker_config()
        
        # 重置systemd启动限制
        reset_systemd_start_limit()
        
        # 修复配置文件
        fix_docker_daemon_config()
        
        # 提示用户
        info("\n=== 修复操作完成 ===")
        info("现在尝试重启Docker服务:")
        print("sudo systemctl start docker")
        print("\n或者使用完全重置功能(可能会删除部分Docker数据):")
        print("选项 1: 继续完全重置 [y/N]")
        
        # 获取用户确认
        confirm = input("是否继续进行完全重置? [y/N]: ").lower()
        if confirm == 'y':
            if reset_docker_service():
                success("Docker修复完成")
                return 0
            else:
                error("Docker服务仍然无法启动，请尝试重启系统")
                return 1
        else:
            info("已跳过完全重置，请手动执行必要的命令")
            return 0
        
    except Exception as e:
        error(f"修复过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
