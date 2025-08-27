#!/usr/bin/env python3
"""
系统环境检查工具
提供检测操作系统类型的函数
"""

import platform
import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.absolute().parent))

# 从shared包中导入所需的所有函数和类
from shared import logger, info, error, debug, warning, success


def is_linux():
    """
    检查当前系统是否为Linux
    
    Returns:
        bool: 如果是Linux返回True，否则返回False
    """
    return platform.system().lower() == 'linux'


def is_mac():
    """
    检查当前系统是否为macOS
    
    Returns:
        bool: 如果是macOS返回True，否则返回False
    """
    return platform.system().lower() == 'darwin'


def is_windows():
    """
    检查当前系统是否为Windows
    
    Returns:
        bool: 如果是Windows返回True，否则返回False
    """
    return platform.system().lower() == 'windows'


def get_os_name():
    """
    获取当前操作系统的名称
    
    Returns:
        str: 操作系统名称 ("linux", "mac", "windows" 或 "unknown")
    """
    if is_linux():
        return "linux"
    elif is_mac():
        return "mac"
    elif is_windows():
        return "windows"
    else:
        return "unknown"


def get_os_version():
    """
    获取当前操作系统的版本
    
    Returns:
        str: 操作系统版本信息
    """
    if is_linux():
        # 对于Linux，可能需要更精确的方法确定发行版本
        try:
            import distro
            return f"{distro.name()} {distro.version()}"
        except ImportError:
            # 如果未安装distro模块，尝试其他方法
            return platform.version()
    else:
        # 对于Windows和macOS，使用platform模块即可
        return platform.version()


def is_tencent_os():
    """
    检测当前操作系统是否为TencentOS
    
    Returns:
        bool: 如果是TencentOS返回True，否则返回False
    """
    if not is_linux():
        return False
        
    try:
        # 尝试读取发行版信息
        os_info = {}
        with open("/etc/os-release", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os_info[key] = value.strip('"')
        
        # 检查是否包含TencentOS字样
        return "TencentOS" in os_info.get("NAME", "")
    except Exception:
        debug("检测 TencentOS 时出错")
        return False


def get_linux_distribution():
    """
    获取Linux发行版信息
    
    Returns:
        dict: 包含发行版信息的字典，如果无法读取则返回空字典
    """
    if not is_linux():
        return {}
        
    try:
        # 尝试读取发行版信息
        os_info = {}
        with open("/etc/os-release", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os_info[key] = value.strip('"')
        return os_info
    except Exception:
        debug("无法读取Linux发行版信息")
        return {}


def print_system_info():
    """
    打印系统详细信息
    """
    info(f"操作系统类型: {get_os_name()}")
    info(f"操作系统版本: {get_os_version()}")
    info(f"Python版本: {platform.python_version()}")
    info(f"处理器架构: {platform.machine()}")


if __name__ == "__main__":
    print_system_info()
