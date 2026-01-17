#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import os
import sys
import time
import platform
import subprocess
import threading
from collections import namedtuple

# Windows特定的导入
if platform.system().lower().startswith('windows'):
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None

User = namedtuple('User', ['user_id', 'passwd', 'wechat_openid'])

# 登录校园网/寝室宽带的用户账号(学号, 登录教务处的密码, None)
#  例如： User('202912272625', '123456Abc@#$', None)

DEFAULT_OPTIONS = {
    # 认证页面的地址
    'url': "http://10.253.0.235",  # 寝室公寓http://aaa.uestc.edu.cn  http://10.253.0.235
    # 'url': "http://10.253.0.237",  # 主楼 http://10.253.0.237

    # 认证页面的地址里的参数ac_id=???
    'ac_id': '3',  # 寝室公寓acid=3
    # 'ac_id': '1',  # 主楼有线校园网acid=1

    # 网络提供商的类型
    # 'domain': '@dx-uestc',  # 电信:"@dx", 移动:"@cmcc", 校园网:"@dx-uestc"
    'domain': '@cmcc',  # 电信:"@dx", 移动:"@cmcc", 校园网:"@dx-uestc"

    # 下面的一般不用改
    'test_ip': "www.baidu.com",  # IP to test whether the Internet is connected
    'delay': 16,  # delay seconds
    'max_failed': 3,  # 连续ping失败n次, 认为断网
}

CONFIG_FILENAME = "user_config.json"


def _config_path():
    return os.path.join(os.path.dirname(__file__), CONFIG_FILENAME)


def _load_user_config():
    path = _config_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        user_id = (data.get("user_id") or "").strip()
        password = (data.get("password") or "").strip()
        if user_id and password:
            # 返回用户信息和配置选项
            config_options = {
                'url': data.get('url', DEFAULT_OPTIONS['url']),
                'ac_id': data.get('ac_id', DEFAULT_OPTIONS['ac_id']),
                'domain': data.get('domain', DEFAULT_OPTIONS['domain']),
                'test_ip': data.get('test_ip', DEFAULT_OPTIONS['test_ip']),
            }
            return user_id, password, config_options
    except Exception:
        return None
    return None


def _save_user_config(user_id, password, url=None, ac_id=None, domain=None, test_ip=None):
    path = _config_path()
    config_data = {
        "user_id": user_id,
        "password": password,
        "url": url or DEFAULT_OPTIONS['url'],
        "ac_id": ac_id or DEFAULT_OPTIONS['ac_id'],
        "domain": domain or DEFAULT_OPTIONS['domain'],
        "test_ip": test_ip or DEFAULT_OPTIONS['test_ip'],
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(config_data, file, ensure_ascii=True, indent=2)


def _check_startup_status():
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

def _toggle_startup_in_window(root, startup_var):
    """在窗口中切换开机自启状态"""
    def do_toggle():
        try:
            if not platform.system().lower().startswith('windows') or winreg is None:
                import tkinter.messagebox as mb
                mb.showwarning("提示", "开机自启功能仅在Windows系统上可用。")
                return
            
            # 获取当前exe路径
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
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
                    startup_var.set(False)
                    import tkinter.messagebox as mb
                    mb.showinfo("开机自启", "已关闭开机自启动")
                except FileNotFoundError:
                    # 如果不存在，添加（开启自启）
                    winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, exe_path)
                    winreg.CloseKey(key)
                    startup_var.set(True)
                    import tkinter.messagebox as mb
                    mb.showinfo("开机自启", "已开启开机自启动")
            except Exception as e:
                import tkinter.messagebox as mb
                mb.showerror("错误", f"设置开机自启失败：{str(e)}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("错误", f"操作失败：{str(e)}")
    
    # 在新线程中运行，避免阻塞UI
    threading.Thread(target=do_toggle, daemon=True).start()

def _debug_login_in_window(root, user_var, pass_var, url_var, ac_id_var, domain_var):
    """在窗口中执行调试登录"""
    def run_debug():
        try:
            import tkinter.messagebox as mb
            from BitSrunLogin.LoginManager import LoginManager
            
            # 检查输入
            user_id = user_var.get().strip()
            password = pass_var.get().strip()
            if not user_id or not password:
                mb.showerror("输入错误", "请先输入学号和密码")
                return
            
            # 构建登录选项
            url = url_var.get().strip()
            ac_id = ac_id_var.get().strip()
            domain = domain_var.get().strip()
            test_ip = DEFAULT_OPTIONS['test_ip']
            
            kwargs = {
                'url': url,
                'ac_id': ac_id,
                'domain': domain,
                'test_ip': test_ip,
            }
            
            # 检查网络状态
            def is_connect_internet(test_ip):
                try:
                    if platform.system().lower().startswith('windows'):
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
                except Exception:
                    return False
            
            is_online = is_connect_internet(test_ip)
            
            if is_online:
                mb.showwarning("调试提示", "当前已处于联网状态，请先断开网络连接后再进行调试。")
                return
            
            # 尝试登录3次
            success = False
            last_error = None
            
            for attempt in range(1, 4):
                try:
                    mb.showinfo("调试中", f"正在尝试第 {attempt} 次登录...")
                    
                    LoginManager(**kwargs).login(username=user_id, password=password)
                    
                    # 等待一下再检查网络
                    time.sleep(3)
                    if is_connect_internet(test_ip):
                        success = True
                        mb.showinfo("调试成功", f"第 {attempt} 次登录成功！网络已连接。")
                        break
                    else:
                        last_error = "登录成功，但网络仍未连接"
                        if attempt < 3:
                            time.sleep(10)
                except Exception as e:
                    last_error = str(e)
                    if attempt < 3:
                        time.sleep(10)
            
            if not success:
                error_msg = f"3次登录尝试均失败，网络仍未连接。\n\n"
                if last_error:
                    error_msg += f"最后错误信息：{last_error}\n\n"
                error_msg += "请检查：\n1. 学号和密码是否正确\n2. 认证地址、AC ID、网络类型是否匹配\n3. 网络连接是否正常"
                mb.showerror("调试失败", error_msg)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("调试错误", f"调试过程中发生错误：{str(e)}")
    
    # 在新线程中运行，避免阻塞UI
    threading.Thread(target=run_debug, daemon=True).start()

def _prompt_user_config():
    try:
        import tkinter as tk
        from tkinter import messagebox
    except Exception as exc:
        raise RuntimeError("无法弹出初始化界面，请手动配置学号密码") from exc

    saved = {"ok": False}
    result = {"user_id": "", "password": "", "url": "", "ac_id": "", "domain": ""}

    def on_save():
        user_id = user_var.get().strip()
        password = pass_var.get().strip()
        if not user_id or not password:
            messagebox.showerror("输入错误", "学号和密码不能为空")
            return
        
        result["user_id"] = user_id
        result["password"] = password
        result["url"] = url_var.get().strip()
        result["ac_id"] = ac_id_var.get().strip()
        result["domain"] = domain_var.get().strip()
        
        _save_user_config(
            user_id, password,
            url=result["url"],
            ac_id=result["ac_id"],
            domain=result["domain"],
            test_ip=DEFAULT_OPTIONS['test_ip']
        )
        saved["ok"] = True
        root.destroy()

    def on_close():
        root.destroy()

    root = tk.Tk()
    root.title("初始化登录信息")
    root.resizable(True, True)  # 允许调整大小
    
    # 设置窗口居中
    root.update_idletasks()
    width = 520
    height = 550
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.minsize(500, 520)  # 设置最小尺寸

    # 学号和密码
    tk.Label(root, text="学号:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="密码:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
    
    # 配置选项
    tk.Label(root, text="认证地址:").grid(row=2, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="AC ID:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="网络类型:").grid(row=4, column=0, padx=10, pady=8, sticky="e")

    user_var = tk.StringVar()
    pass_var = tk.StringVar()
    show_pass_var = tk.BooleanVar(value=False)
    url_var = tk.StringVar(value=DEFAULT_OPTIONS['url'])
    ac_id_var = tk.StringVar(value=DEFAULT_OPTIONS['ac_id'])
    domain_var = tk.StringVar(value=DEFAULT_OPTIONS['domain'])

    # 学号输入框
    tk.Entry(root, textvariable=user_var, width=35).grid(row=0, column=1, padx=10, pady=8, sticky="ew")
    
    # 密码输入框和显示密码复选框
    pass_frame = tk.Frame(root)
    pass_frame.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
    pass_entry = tk.Entry(pass_frame, textvariable=pass_var, show="*", width=30)
    pass_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def toggle_password_visibility():
        if show_pass_var.get():
            pass_entry.config(show="")
        else:
            pass_entry.config(show="*")
    
    show_pass_check = tk.Checkbutton(
        pass_frame, 
        text="显示", 
        variable=show_pass_var,
        command=toggle_password_visibility
    )
    show_pass_check.pack(side=tk.RIGHT, padx=(5, 0))
    
    # 配置列权重，使输入框可以扩展
    root.columnconfigure(1, weight=1)
    
    # URL选择
    url_frame = tk.Frame(root)
    url_frame.grid(row=2, column=1, padx=10, pady=8, sticky="w")
    url_options = [
        ("http://10.253.0.235", "寝室公寓"),
        ("http://10.253.0.237", "主楼")
    ]
    for url_val, desc in url_options:
        rb = tk.Radiobutton(url_frame, text=desc, variable=url_var, value=url_val, anchor="w")
        rb.pack(anchor="w")
    
    # AC ID选择
    ac_id_frame = tk.Frame(root)
    ac_id_frame.grid(row=3, column=1, padx=10, pady=8, sticky="w")
    ac_id_options = [("3", "寝室公寓 (ac_id=3)"), ("1", "主楼有线校园网 (ac_id=1)")]
    for ac_val, desc in ac_id_options:
        rb = tk.Radiobutton(ac_id_frame, text=desc, variable=ac_id_var, value=ac_val, anchor="w")
        rb.pack(anchor="w")
    
    # Domain选择
    domain_frame = tk.Frame(root)
    domain_frame.grid(row=4, column=1, padx=10, pady=8, sticky="w")
    domain_options = [
        ("@dx", "电信"),
        ("@cmcc", "移动"),
        ("@dx-uestc", "校园网")
    ]
    for dom_val, desc in domain_options:
        rb = tk.Radiobutton(domain_frame, text=desc, variable=domain_var, value=dom_val, anchor="w")
        rb.pack(anchor="w")

    # 添加分隔线
    separator_frame = tk.Frame(root, height=2, bg="gray", relief=tk.SUNKEN)
    separator_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    separator_frame.grid_propagate(False)

    # 开机自启开关
    startup_var = tk.BooleanVar(value=_check_startup_status())
    startup_check = tk.Checkbutton(
        root, 
        text="开机自启动", 
        variable=startup_var,
        command=lambda: _toggle_startup_in_window(root, startup_var)
    )
    startup_check.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # 调试登录按钮
    debug_button = tk.Button(
        root, 
        text="调试登录", 
        width=18,
        command=lambda: _debug_login_in_window(root, user_var, pass_var, url_var, ac_id_var, domain_var)
    )
    debug_button.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

    # 保存并开始按钮
    tk.Button(root, text="保存并开始", width=20, command=on_save).grid(
        row=8, column=0, columnspan=2, pady=15
    )
    
    # 添加一些底部间距
    tk.Label(root, text="").grid(row=9, column=0, pady=5)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

    if not saved["ok"]:
        raise SystemExit("初始化已取消")


def get_login_options():
    creds = _load_user_config()
    if not creds:
        _prompt_user_config()
        creds = _load_user_config()
        if not creds:
            raise SystemExit("未配置学号密码")

    if len(creds) == 3:
        # 新格式：包含配置选项
        user_id, password, config_options = creds
        options = dict(DEFAULT_OPTIONS)
        options.update(config_options)
        options["user"] = User(user_id, password, None)
    else:
        # 旧格式：只有用户名和密码
        user_id, password = creds
        options = dict(DEFAULT_OPTIONS)
        options["user"] = User(user_id, password, None)
    return options
