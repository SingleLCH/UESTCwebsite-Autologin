# UESTC 校园网自动登录工具 - 托盘增强版

基于 [AutoLoginUESTC](https://github.com/b71db892/AutoLoginUESTC) 项目开发的增强版本，新增系统托盘、图形化配置界面、开机自启等功能。

## 功能特性

### GUI界面
<img width="522" height="582" alt="image" src="https://github.com/user-attachments/assets/025683e3-db7e-44a1-8658-a6df62b083ff" />

- **信息测试** 手动测试登录功能一次保存后，会生成JSON文件，用户密码进行加密处理
- **开机自启动** 支持开机自启


### 系统托盘状态指示
- 🟢 **绿色** - 网络在线
- 🔴 **红色** - 网络离线
- 🟠 **橙色** - 程序启动中

### 托盘菜单
- **显示状态** - 查看运行时间、网络状态、登录次数等详细信息
- **开机自启** - 一键设置/取消开机自动启动
- **退出程序** - 安全退出


### 图形化配置
首次运行自动弹出配置窗口，支持：
- 学号/密码输入
- 认证地址选择（寝室公寓/主楼）
- AC ID 选择
- 网络类型选择（电信/移动/校园网）

## 支持的网络类型

| 网络类型 | 认证地址 | AC ID | Domain |
|---------|---------|-------|--------|
| 寝室公寓（电信/移动） | http://10.253.0.235 | 3 | @dx / @cmcc |
| 主楼有线校园网 | http://10.253.0.237 | 1 | @dx-uestc |

## 快速开始

### 方式一：直接运行（推荐）

1. 安装依赖：
```bash
pip install requests pystray pillow
```

2. 运行程序：
```bash
python always_online.py
```

3. 首次运行会弹出配置窗口，填写学号密码后点击"保存并开始"

### 方式二：运行已经打包好的 exe

直接下载release下的 .exe文件，则会显示出GUI界面

## 开源文件说明

```
├── always_online.py      # 主程序（托盘版）
├── login_once.py         # 单次登录脚本
├── config.py             # 配置管理
├── logger.py             # 日志模块
├── BitSrunLogin/         # 登录核心模块
│   ├── LoginManager.py   # 登录管理器
│   ├── encryption/       # 加密算法
│   └── _decorators.py    # 装饰器
├── logs/                 # 日志目录
├── user_config.json      # 用户配置文件（自动生成）
├── build.bat             # 打包脚本
└── always_online.spec    # PyInstaller 配置
```

## 故障排除


### 登录失败
1. 使用托盘菜单中的"调试登录"功能测试
2. 检查 `logs` 目录下的日志文件
3. 确认学号、密码、网络类型是否正确

### 其他问题
请提交issue进行反馈

## 致谢

本项目基于以下开源项目开发，特别感谢原作者的贡献：

- **[AutoLoginUESTC](https://github.com/b71db892/AutoLoginUESTC)** - UESTC 校园网认证登录核心实现
- **[BIT-srun-login-script](https://github.com/coffeehat/BIT-srun-login-script)** - 深澜认证协议参考

## License

MIT License
