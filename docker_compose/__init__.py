#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
docker_compose包
提供Docker Compose管理功能，包括安装、检查状态、重新安装和使用Compose启动服务
"""

from docker_compose.compose_manager import (
    install_compose,
    is_compose_running,
    reinstall_compose,
    start_service_by_compose
)

__all__ = [
    'install_compose',
    'is_compose_running',
    'reinstall_compose',
    'start_service_by_compose'
]
