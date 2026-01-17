# UESTC 电子科技大学网络认证脚本 - 托盘增强版
------------------------------
### 搞这干啥？
- 教研室、机房每次断电启动电脑，都需要人来进行配网，所以想着省时间
- 寝室有时候忘记交电费，一断电，重启电脑，恰好又没有人在，又没有网络
- **新增功能**：添加了系统托盘图标，可以实时查看网络状态，再也不用担心程序是否在运行了！

### 新增托盘功能
- 🟢 绿色图标：网络在线
- 🔴 红色图标：网络离线
- 🟠 橙色图标：程序启动中

### 怎么用？
#### 托盘版本（推荐）
1. 安装依赖：`pip install pystray pillow pyinstaller`
2. 修改 `config.py` 配置文件
3. 运行托盘版本：`python always_online.py`
4. 打包成exe：运行 `build.bat` 或手动执行 `pyinstaller --noconsole --onefile always_online.py`

#### 传统版本
- 支持登录以下类型的网络（我都试过的）：
```angular2html
- 校园网有线接入+学号认证（在主楼做的测试，至今可用）
- 移动、电信寝室宽带有线接入+学号认证（类似于硕丰6、7、8组团那种插网线直接弹出认证页面的，至今可用）
```
只需修改config.py就行。然后手动注销断网，输入：
```angular2html
python login_once.py
```
如果能联网，那说明配置没问题。
之后一直运行always_online.py就行了。
```angular2html
python always_online.py
```

#### 主要借鉴项目
- **本项目主要借鉴自**: [AutoLoginUESTC](https://github.com/b71db892/AutoLoginUESTC)
  - 感谢原作者提供的UESTC网络认证解决方案
  - 在此基础上增加了系统托盘功能和更好的用户体验


感谢所有开源贡献者的无私分享！🎉
