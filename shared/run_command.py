#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行执行工具模块
提供执行 shell 命令的函数
"""

import subprocess
import sys
import os
import pty
import shlex
import select
import fcntl
import termios
import struct
import signal
from pathlib import Path

# 获取项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
ROOT_DIR = SCRIPT_DIR.parent

# 添加shared目录到sys.path以便导入
sys.path.append(str(ROOT_DIR))

# 导入日志模块
from shared.logger import logger, info, error, debug, warning, success


class CommandError(Exception):
    """命令执行过程中遇到的异常"""
    pass


def run_command_with_pty(cmd, cwd=None, env=None, timeout=None):
    """
    使用伪终端(PTY)执行命令以保留颜色输出
    
    Args:
        cmd: 要执行的命令(字符串)
        cwd: 执行命令的目录
        env: 环境变量字典
        timeout: 命令执行超时时间（秒）
        
    Returns:
        dict: 包含stdout, stderr和returncode的结果字典
    """
    # 确保工作目录
    if cwd:
        old_cwd = os.getcwd()
        os.chdir(cwd)
    
    # 准备环境变量
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    
    # 强制启用颜色
    command_env['TERM'] = 'xterm-256color'
    command_env['FORCE_COLOR'] = '1'
    command_env['SYSTEMD_COLORS'] = '1'  # systemctl特有的颜色控制
    command_env['PYTHONIOENCODING'] = 'utf-8'
    
    # 分割命令为列表
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = cmd
    
    # 创建伪终端
    master_fd, slave_fd = pty.openpty()
    
    # 设置终端大小为宽一些以避免折行
    term_size = struct.pack('HHHH', 40, 120, 0, 0)
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, term_size)
    
    # 启动进程
    process = subprocess.Popen(
        cmd_list,
        preexec_fn=os.setsid,
        stdin=slave_fd,
        stdout=slave_fd, 
        stderr=slave_fd,
        universal_newlines=True,
        env=command_env,
        shell=False
    )
    
    # 关闭子进程一端的文件描述符
    os.close(slave_fd)
    
    # 读取输出
    output = b''
    timeout_count = 0
    read_timeout = 0.1  # 100ms
    max_idle_time = 2  # 2秒内没有输出认为完成
    idle_count = 0
    
    try:
        # 先给进程一些时间启动
        import time
        time.sleep(0.1)
        
        # 特殊处理systemctl status命令，使用短的超时
        cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)
        is_systemctl_status = 'systemctl status' in cmd_str
        
        while True:
            # 检查命令超时
            if timeout and timeout_count >= timeout / read_timeout:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                break
            
            # 使用select非阻塞地检查是否有数据可读
            r, _, _ = select.select([master_fd], [], [], read_timeout)
            
            if master_fd in r:
                # 有数据可读
                try:
                    data = os.read(master_fd, 4096)
                    if data:
                        output += data
                        idle_count = 0  # 重置空闲计数
                    else:
                        # 没有数据了，可能是结束了
                        idle_count += 1
                except OSError:
                    # 读取错误，可能是pty已关闭
                    break
            else:
                # 超时了，没有数据可读
                # 检查进程是否还在运行
                if process.poll() is not None:
                    break
                    
                idle_count += 1
                timeout_count += 1
                
            # 对于systemctl status命令特殊处理，不要等待太久
            if is_systemctl_status and idle_count >= max_idle_time / read_timeout:
                # 强制结束进程
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except:
                    pass
                break
                
            # 如果长时间没有输出，认为完成
            if idle_count >= max_idle_time / read_timeout:
                break
        
        # 等待进程结束
        returncode = process.wait()
        
    except Exception as e:
        # 确保进程被终止
        try:
            process.kill()
        except:
            pass
        returncode = -1
    finally:
        # 关闭主进程一端的文件描述符
        os.close(master_fd)
        
        # 恢复工作目录
        if cwd:
            os.chdir(old_cwd)
    
    # 解码输出
    try:
        stdout_str = output.decode('utf-8')
        stderr_str = ""  # 在PTY模式下，stderr与stdout合并
    except UnicodeDecodeError:
        stdout_str = output.decode('utf-8', errors='replace')
        stderr_str = ""
    
    # 创建类似CompletedProcess的结果
    return {
        'stdout': stdout_str,
        'stderr': stderr_str,
        'returncode': returncode
    }


def run_command(cmd, shell=True, cwd=None, check=True, verbose=True, env=None, timeout=None, preserve_color=False):
    """
    执行shell命令并返回结果
    
    Args:
        cmd: 要执行的命令(列表或字符串)
        shell: 是否使用shell执行，如果为True，cmd应该是字符串
        cwd: 执行命令的目录
        check: 是否在命令失败时抛出异常
        verbose: 是否显示详细输出
        env: 环境变量字典
        timeout: 命令执行超时时间（秒）
        preserve_color: 是否保留输出中的颜色代码
        
    Returns:
        subprocess.CompletedProcess: 命令执行结果
        
    Raises:
        CommandError: 如果命令执行失败且check=True
    """
    if verbose:
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        info(f"执行命令: {cmd_str}")
    
    # 合并环境变量
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    
    # 使用PTY模式来保留颜色输出
    if preserve_color:
        try:
            import signal  # 当启用PTY模式时需要导入
            
            # 检查是否是常见需要保留颜色的命令
            cmd_str = cmd if isinstance(cmd, str) else ' '.join(cmd)
            is_color_cmd = any(keyword in cmd_str for keyword in ['systemctl', 'ls --color', 'docker', 'journalctl'])
            
            if is_color_cmd or 'status' in cmd_str or preserve_color:
                pty_result = run_command_with_pty(cmd, cwd=cwd, env=command_env, timeout=timeout)
                
                # 创建结果对象
                result = subprocess.CompletedProcess(
                    args=cmd,
                    returncode=pty_result['returncode'],
                    stdout=pty_result['stdout'],
                    stderr=pty_result['stderr']
                )
                
                # 如果要显示详细输出，直接打印结果
                if verbose and result.stdout:
                    print(result.stdout)
                if verbose and result.stderr:
                    warning(f"标准错误:\n{result.stderr}")
                
                # 早期返回，不使用普通的Popen方式
                return result
        except Exception as e:
            # 如果PTY方式失败，回退到标准方法
            warning(f"PTY模式失败，切换到标准模式: {str(e)}")
    
    try:
        # 添加基本的颜色环境变量
        command_env['TERM'] = 'xterm-256color'
        command_env['FORCE_COLOR'] = '1'
        command_env['SYSTEMD_COLORS'] = '1'  # systemctl特有的颜色控制
        
        process = subprocess.Popen(
            cmd, 
            shell=shell, 
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=command_env
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise
        
        # 创建一个类似CompletedProcess的结果对象
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        # 如果命令执行成功且verbose=True，打印输出
        if verbose:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                warning(f"标准错误:\n{result.stderr}")
        
        # 如果check=True且命令执行失败，抛出异常
        if check and result.returncode != 0:
            error(f"命令执行失败: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            error(f"错误输出: {result.stderr}")
            error(f"返回码: {result.returncode}")
            raise CommandError(f"命令执行失败，返回码: {result.returncode}")
        
        return result
        
    except subprocess.TimeoutExpired as e:
        error(f"命令执行超时: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        error(f"超时设置: {timeout}秒")
        if check:
            raise CommandError(f"命令执行超时: {str(e)}")
        # 创建一个模拟的CompletedProcess，带有错误信息
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,  # 使用超时的标准退出码
            stdout="",
            stderr=f"命令执行超时 ({timeout}秒)"
        )
        
    except subprocess.SubprocessError as e:
        error(f"命令执行失败: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        error(f"错误信息: {str(e)}")
        if check:
            raise CommandError(f"命令执行失败: {str(e)}")
        # 创建一个模拟的CompletedProcess，带有错误信息
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr=f"命令执行异常: {str(e)}"
        )


def run_command_with_input(cmd, input_data=None, **kwargs):
    """
    执行命令并提供输入数据
    
    Args:
        cmd: 要执行的命令(列表或字符串)
        input_data: 提供给命令的输入数据(字符串)
        **kwargs: 传递给run_command的其他参数
        
    Returns:
        subprocess.CompletedProcess: 命令执行结果
    """
    verbose = kwargs.pop('verbose', False)
    if verbose:
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        info(f"执行命令(带输入): {cmd_str}")
        
    # 合并环境变量
    command_env = os.environ.copy()
    env = kwargs.pop('env', None)
    if env:
        command_env.update(env)
    
    try:
        # 从 kwargs 中提取相关参数
        shell = kwargs.get('shell', True)
        cwd = kwargs.get('cwd', None)
        check = kwargs.get('check', True)
        timeout = kwargs.get('timeout', None)
        
        process = subprocess.Popen(
            cmd,
            shell=shell if 'shell' in kwargs else isinstance(cmd, str),
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            env=command_env
        )
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=timeout)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise
        
        # 创建一个类似CompletedProcess的结果对象
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        # 如果命令执行成功且verbose=True，打印输出
        if verbose:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                warning(f"标准错误:\n{result.stderr}")
        
        # 如果check=True且命令执行失败，抛出异常
        if check and result.returncode != 0:
            error(f"命令执行失败: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
            error(f"错误输出: {result.stderr}")
            error(f"返回码: {result.returncode}")
            raise CommandError(f"命令执行失败，返回码: {result.returncode}")
            
        return result
    except Exception as e:
        error(f"命令执行失败: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        error(f"错误信息: {str(e)}")
        check = kwargs.get('check', True)
        if check:
            raise CommandError(f"命令执行失败: {str(e)}")
        # 创建一个模拟的CompletedProcess，带有错误信息
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout="",
            stderr=f"命令执行异常: {str(e)}"
        )


def run_piped_commands(commands, **kwargs):
    """
    执行管道命令(模拟 cmd1 | cmd2 | cmd3 的效果)
    
    Args:
        commands: 命令列表，每个命令可以是列表或字符串
        **kwargs: 传递给subprocess.run的参数
        
    Returns:
        subprocess.CompletedProcess: 最后一个命令的执行结果
    """
    verbose = kwargs.pop('verbose', False)
    if verbose:
        cmd_str = " | ".join([' '.join(cmd) if isinstance(cmd, list) else cmd for cmd in commands])
        info(f"执行管道命令: {cmd_str}")
    
    # 如果没有命令要执行
    if not commands:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    
    # 如果只有一个命令，直接执行它
    if len(commands) == 1:
        return run_command(commands[0], **kwargs)
    
    try:
        # 执行第一个命令
        previous_process = subprocess.Popen(
            commands[0], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 执行中间命令
        for cmd in commands[1:-1]:
            current_process = subprocess.Popen(
                cmd,
                stdin=previous_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            previous_process.stdout.close()  # 允许前一个进程在当前进程读完所有数据时接收SIGPIPE
            previous_process = current_process
        
        # 执行最后一个命令并等待结果
        final_process = subprocess.Popen(
            commands[-1],
            stdin=previous_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        previous_process.stdout.close()  # 确保关闭
        
        # 从 kwargs 中提取timeout参数
        timeout = kwargs.get('timeout', None)
        
        try:
            stdout, stderr = final_process.communicate(timeout=timeout)
            returncode = final_process.returncode
        except subprocess.TimeoutExpired:
            final_process.kill()
            stdout, stderr = final_process.communicate()
            raise
        
        # 创建结果对象
        final_result = subprocess.CompletedProcess(
            args=commands[-1],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        # 如果命令执行成功且verbose=True，打印输出
        if verbose:
            if final_result.stdout:
                debug(f"标准输出:\n{final_result.stdout}")
            if final_result.stderr:
                warning(f"标准错误:\n{final_result.stderr}")
        
        # 如果check=True且命令执行失败，抛出异常
        check = kwargs.get('check', True)
        if check and final_result.returncode != 0:
            cmd_str = " | ".join([' '.join(cmd) if isinstance(cmd, list) else cmd for cmd in commands])
            error(f"管道命令执行失败: {cmd_str}")
            error(f"错误输出: {final_result.stderr}")
            error(f"返回码: {final_result.returncode}")
            raise CommandError(f"管道命令执行失败，返回码: {final_result.returncode}")
            
        return final_result
    except Exception as e:
        cmd_str = " | ".join([' '.join(cmd) if isinstance(cmd, list) else cmd for cmd in commands])
        error(f"管道命令执行失败: {cmd_str}")
        error(f"错误信息: {str(e)}")
        check = kwargs.get('check', True)
        if check:
            raise CommandError(f"管道命令执行失败: {str(e)}")
        # 创建一个模拟的CompletedProcess，带有错误信息
        return subprocess.CompletedProcess(
            args=commands[-1],
            returncode=1,
            stdout="",
            stderr=f"管道命令执行异常: {str(e)}"
        )


def run_background_command(cmd, output_file=None):
    """
    在后台执行命令，不等待其完成
    
    Args:
        cmd: 要执行的命令(列表或字符串)
        output_file: 输出重定向到的文件路径
        
    Returns:
        subprocess.Popen: 进程对象
    """
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
    info(f"在后台执行命令: {cmd_str}")
    
    try:
        # 准备输出重定向
        if output_file:
            output_fd = open(output_file, 'w')
            stdout = output_fd
            stderr = output_fd
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        
        # 使用Popen启动进程，不等待
        process = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, str),
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True  # 使进程独立于父进程
        )
        
        info(f"后台命令已启动，PID: {process.pid}")
        return process
    except Exception as e:
        error(f"启动后台命令失败: {cmd_str}")
        error(f"错误信息: {str(e)}")
        raise CommandError(f"启动后台命令失败: {str(e)}")


# 示例用法
if __name__ == "__main__":
    # 简单命令执行示例
    info("=== 简单命令执行示例 ===")
    result = run_command(["echo", "Hello, World!"], verbose=True)
    success(f"命令执行成功，返回码: {result.returncode}")
    
    # 管道命令示例
    info("\n=== 管道命令示例 ===")
    pipe_result = run_piped_commands([
        ["echo", "Hello, World!"], 
        ["grep", "Hello"],
        ["wc", "-w"]
    ], verbose=True)
    success(f"管道命令执行成功，返回码:   {pipe_result.returncode}, 结果: {pipe_result.stdout.strip()}")
    
    # 执行带输入的命令
    info("\n=== 带输入的命令示例 ===")
    input_result = run_command_with_input(
        ["grep", "test"],
        input_data="this is a test\nno match here\ntest again",
        verbose=True
    )
    success(f"带输入的命令执行成功，返回码: {input_result.returncode}")
