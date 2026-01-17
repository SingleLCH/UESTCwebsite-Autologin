#!/usr/bin/env python
# -*- coding:utf-8 -*-
import ctypes
import os
import sys
import time
import platform
import subprocess
import threading
from datetime import datetime

# Windows特定的导入
if platform.system().lower().startswith('windows'):
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None

try:
    import pystray
    from PIL import Image, ImageDraw
    from pystray import MenuItem as item
except ImportError:
    print("需要安装依赖：pip install pystray pillow")
    exit(1)

from logger import logger
from BitSrunLogin.LoginManager import LoginManager
from config import get_login_options

# 获取计算机名
host_name = platform.node()
try:
    #  disable the QuickEdit and Insert mode for the current console
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
except:
    pass

# 全局状态变量
class AppStatus:
    def __init__(self):
        self.is_online = False
        self.last_check_time = None
        self.failed_count = 0
        self.startup_time = datetime.now()
        self.login_attempts = 0
        self.tray_icon = None
        self.running = True

app_status = AppStatus()

def create_image(color):
    """创建托盘图标"""
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    dc = ImageDraw.Draw(image)
    dc.ellipse((width//4, height//4, width*3//4, height*3//4), fill=color)
    return image

def is_connect_internet(test_ip):
    try:
        if platform.system().lower().startswith('windows'):
            # 使用subprocess避免弹出黑色窗口
            result = subprocess.run(
                ["ping", test_ip, "-n", "1"],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower().startswith('windows') else 0
            )
        else:
            result = subprocess.run(
                ["ping", test_ip, "-c", "1"],
                capture_output=True,
                timeout=5
            )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # 如果ping命令失败，返回False表示网络不通
        return False

def update_tray_icon():
    """更新托盘图标状态"""
    if app_status.tray_icon:
        if app_status.is_online:
            app_status.tray_icon.icon = create_image('green')
            app_status.tray_icon.title = f"UESTC自动登录 - 在线 ({host_name})"
        else:
            app_status.tray_icon.icon = create_image('red')
            app_status.tray_icon.title = f"UESTC自动登录 - 离线 ({host_name})"

def show_status():
    """显示详细状态信息"""
    uptime = datetime.now() - app_status.startup_time
    uptime_str = f"{uptime.days}天 {uptime.seconds//3600}小时 {(uptime.seconds//60)%60}分钟"
    
    status_text = f"""UESTC自动登录状态信息

主机名: {host_name}
运行时间: {uptime_str}
当前状态: {'在线' if app_status.is_online else '离线'}
失败次数: {app_status.failed_count}
登录尝试: {app_status.login_attempts}
最后检查: {app_status.last_check_time.strftime('%H:%M:%S') if app_status.last_check_time else '未检查'}

程序正在后台运行..."""
    
    # 使用系统消息框，避免窗口卡死无法关闭
    # 使用MB_OK标志(0x0)确保可以正常关闭
    try:
        if platform.system().lower().startswith('windows'):
            # MessageBoxW参数: hWnd, lpText, lpCaption, uType
            # 0x40 = MB_ICONINFORMATION, 0x0 = MB_OK
            ctypes.windll.user32.MessageBoxW(None, status_text, "UESTC自动登录状态", 0x40 | 0x0)
            return
    except Exception:
        pass

    # 非 Windows 或系统消息框失败时的兜底
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 确保窗口在最前面
        messagebox.showinfo("UESTC自动登录状态", status_text)
        root.quit()
        root.destroy()
    except Exception:
        print(status_text)

def quit_app():
    """退出程序"""
    app_status.running = False
    if app_status.tray_icon:
        app_status.tray_icon.stop()

def show_message(title, message, icon_type=0x40):
    """显示系统消息框"""
    try:
        if platform.system().lower().startswith('windows'):
            ctypes.windll.user32.MessageBoxW(None, message, title, icon_type | 0x0)
            return True
    except Exception:
        pass
    
    # 兜底方案
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        if icon_type == 0x10:  # MB_ICONERROR
            messagebox.showerror(title, message)
        elif icon_type == 0x30:  # MB_ICONWARNING
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
        root.quit()
        root.destroy()
        return True
    except Exception:
        print(f"{title}: {message}")
        return False

def debug_login():
    """调试登录功能"""
    def run_debug():
        try:
            login_options = get_login_options()
            test_ip = login_options.get('test_ip', 'www.baidu.com')
            
            # 检查网络状态
            is_online = is_connect_internet(test_ip)
            
            if is_online:
                # 如果已联网，提示断开网络
                show_message(
                    "调试提示",
                    "当前已处于联网状态，请先断开网络连接后再进行调试。",
                    0x30  # MB_ICONWARNING
                )
                return
            
            # 如果不联网，尝试登录3次
            user = login_options.get('user')
            kwargs = {k: v for k, v in login_options.items() if k != 'user' and k != 'test_ip'}
            
            success = False
            last_error = None
            
            for attempt in range(1, 4):
                try:
                    show_message(
                        "调试中",
                        f"正在尝试第 {attempt} 次登录...",
                        0x40
                    )
                    
                    LoginManager(**kwargs).login(username=user.user_id, password=user.passwd)
                    
                    # 等待一下再检查网络
                    time.sleep(3)
                    if is_connect_internet(test_ip):
                        success = True
                        show_message(
                            "调试成功",
                            f"第 {attempt} 次登录成功！网络已连接。",
                            0x40
                        )
                        break
                    else:
                        # 登录成功但网络仍未连接，继续尝试
                        last_error = "登录成功，但网络仍未连接"
                        logger.warning(f"调试登录第 {attempt} 次：登录成功但网络未连接")
                        if attempt < 3:
                            time.sleep(10)  # 等待10秒
                except Exception as e:
                    logger.error(f"调试登录第 {attempt} 次失败: {e}")
                    last_error = str(e)
                    if attempt < 3:
                        time.sleep(10)  # 等待10秒
            
            if not success:
                error_msg = f"3次登录尝试均失败，网络仍未连接。\n\n"
                if last_error:
                    error_msg += f"最后错误信息：{last_error}\n\n"
                error_msg += "请检查：\n1. 学号和密码是否正确\n2. 认证地址、AC ID、网络类型是否匹配\n3. 网络连接是否正常"
                show_message(
                    "调试失败",
                    error_msg,
                    0x10  # MB_ICONERROR
                )
        except Exception as e:
            logger.error(f"调试功能出错: {e}")
            show_message(
                "调试错误",
                f"调试过程中发生错误：{str(e)}",
                0x10
            )
    
    # 在新线程中运行，避免阻塞托盘
    threading.Thread(target=run_debug, daemon=True).start()

def get_startup_status():
    """检查开机自启状态"""
    try:
        if not platform.system().lower().startswith('windows') or winreg is None:
            return False
        
        # 获取当前exe路径
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe').replace('pythonw.exe', 'pythonw.exe')
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable
            exe_path = f'"{pythonw_path}" "{os.path.abspath(__file__)}"'
        
        # 检查注册表
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "UESTC自动登录")
                winreg.CloseKey(key)
                # 比较时需要考虑路径格式
                if getattr(sys, 'frozen', False):
                    return value == exe_path
                else:
                    return value == exe_path or exe_path in value
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
    except Exception:
        return False

def toggle_startup():
    """切换开机自启状态"""
    def do_toggle():
        try:
            if not platform.system().lower().startswith('windows') or winreg is None:
                show_message("提示", "开机自启功能仅在Windows系统上可用。", 0x30)
                return
            
            # 获取当前exe路径
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                # 如果是脚本运行，使用pythonw.exe
                pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe').replace('pythonw.exe', 'pythonw.exe')
                if not os.path.exists(pythonw_path):
                    pythonw_path = sys.executable
                exe_path = f'"{pythonw_path}" "{os.path.abspath(__file__)}"'
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = "UESTC自动登录"
            
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    key_path,
                    0,
                    winreg.KEY_ALL_ACCESS
                )
                
                try:
                    # 检查是否存在
                    value, _ = winreg.QueryValueEx(key, key_name)
                    # 如果存在，删除（关闭自启）
                    winreg.DeleteValue(key, key_name)
                    winreg.CloseKey(key)
                    show_message("开机自启", "已关闭开机自启动", 0x40)
                except FileNotFoundError:
                    # 如果不存在，添加（开启自启）
                    winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, exe_path)
                    winreg.CloseKey(key)
                    show_message("开机自启", "已开启开机自启动", 0x40)
                
                # 更新菜单
                if app_status.tray_icon:
                    app_status.tray_icon.menu = create_tray_menu()
            except Exception as e:
                logger.error(f"设置开机自启失败: {e}")
                show_message("错误", f"设置开机自启失败：{str(e)}", 0x10)
        except Exception as e:
            logger.error(f"切换开机自启状态失败: {e}")
            show_message("错误", f"操作失败：{str(e)}", 0x10)
    
    # 在新线程中运行，避免阻塞
    threading.Thread(target=do_toggle, daemon=True).start()

def create_tray_menu():
    """创建托盘菜单"""
    startup_status = get_startup_status()
    startup_text = "开机自启: 已开启" if startup_status else "开机自启: 已关闭"
    
    return pystray.Menu(
        item('显示状态', show_status),
        item('调试登录', debug_login),
        item(startup_text, toggle_startup),
        pystray.Menu.SEPARATOR,
        item('退出程序', quit_app)
    )

def always_login(user=None, test_ip=None, delay=2, max_failed=3, **kwargs):
    """网络监控和自动登录主循环"""
    time_now = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    org_delay = delay
    failed = 0
    logger.info(f'[{time_now()}] [{host_name}] NetWork Monitor StartUp.')
    
    while app_status.running:
        app_status.last_check_time = datetime.now()
        
        # 检查网络连接
        is_online = is_connect_internet(test_ip)
        app_status.is_online = is_online
        
        if not is_online:
            failed += 1
            app_status.failed_count = failed
            delay = max(1., delay / 2)  # 最小延迟1秒
            
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] offline.')
                try:
                    LoginManager(**kwargs).login(username=user.user_id, password=user.passwd)
                    app_status.login_attempts += 1
                    logger.info(f'[{time_now()}] [{host_name}] login attempt #{app_status.login_attempts}')
                except Exception as e:
                    logger.error(f'[{time_now()}] [{host_name}] login failed: {e}')
        else:
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] online now.')
            failed = 0
            app_status.failed_count = 0
            delay = org_delay
        
        # 更新托盘图标
        update_tray_icon()
        
        time.sleep(delay)

def run_tray():
    """运行托盘图标"""
    try:
        # 创建初始图标
        image = create_image('orange')  # 启动时橙色
        menu = create_tray_menu()
        
        app_status.tray_icon = pystray.Icon(
            "uestc_login",
            image,
            f"UESTC自动登录 - 启动中 ({host_name})",
            menu
        )
        
        app_status.tray_icon.run()
    except Exception as e:
        logger.error(f"托盘图标启动失败: {e}")
        print(f"托盘图标启动失败: {e}")


if __name__ == "__main__":
    try:
        login_options = get_login_options()
        # 启动网络监控线程
        monitor_thread = threading.Thread(target=lambda: always_login(**login_options), daemon=True)
        monitor_thread.start()
        
        # 在主线程运行托盘图标
        run_tray()
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        app_status.running = False
    except Exception as e:
        import traceback
        error = traceback.format_exc()
        logger.error(f"程序运行错误: {error}")
        print(f"程序运行错误: {e}")
    finally:
        app_status.running = False
        if app_status.tray_icon:
            app_status.tray_icon.stop()
