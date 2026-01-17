#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import os
from collections import namedtuple

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
    root.resizable(False, False)
    
    # 设置窗口居中
    root.update_idletasks()
    width = 420
    height = 380
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # 学号和密码
    tk.Label(root, text="学号:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="密码:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
    
    # 配置选项
    tk.Label(root, text="认证地址:").grid(row=2, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="AC ID:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
    tk.Label(root, text="网络类型:").grid(row=4, column=0, padx=10, pady=8, sticky="e")

    user_var = tk.StringVar()
    pass_var = tk.StringVar()
    url_var = tk.StringVar(value=DEFAULT_OPTIONS['url'])
    ac_id_var = tk.StringVar(value=DEFAULT_OPTIONS['ac_id'])
    domain_var = tk.StringVar(value=DEFAULT_OPTIONS['domain'])

    tk.Entry(root, textvariable=user_var, width=30).grid(row=0, column=1, padx=10, pady=8, sticky="w")
    tk.Entry(root, textvariable=pass_var, show="*", width=30).grid(row=1, column=1, padx=10, pady=8, sticky="w")
    
    # URL选择
    url_frame = tk.Frame(root)
    url_frame.grid(row=2, column=1, padx=10, pady=8, sticky="w")
    url_options = [
        ("http://10.253.0.235", "寝室公寓"),
        ("http://10.253.0.237", "主楼"),
        ("http://aaa.uestc.edu.cn", "校园网")
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

    tk.Button(root, text="保存并开始", width=20, command=on_save).grid(
        row=5, column=0, columnspan=2, pady=15
    )

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
