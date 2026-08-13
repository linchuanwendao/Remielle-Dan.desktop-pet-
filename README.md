# 小小蕾米埃尔

> 绝区零角色「蕾米埃尔·丹」的 Windows 桌面宠物
> 初代虚狩 · 达识结社

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-41CD52?logo=qt&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)

## 📥 使用方式

### 方式一：直接下载 exe（推荐，无需 Python）

前往 [Releases](../../releases) 下载 `小小蕾米埃尔.zip`，解压后双击 `小小蕾米埃尔.exe` 即可。

### 方式二：源码运行

bash
# 1. 安装依赖
pip install PyQt5

# 2. 启动
python main.py
# 或双击 run.bat（自动装依赖 + 无控制台启动）
```

### 方式三：自己打包 exe

双击 `build_exe.bat`，产物在 `dist\小小蕾米埃尔\`。

说明
 待机   leimiaier3   默认状态，拿着羽毛笔等待 
 创作中  leimiaier1 键盘有输入时立即切换（松键后保持约 1.2 秒） 
 迷茫/思索  leimiaier6 / leimiaier4  输入间隔（停止打字后 4~10 秒，随机二选一）
 欣赏作品  leimiaier5 普通模式随机切换（每 5~15 秒在待机/欣赏/张望间随机） 
 四处张望  leimiaier2  同上 


键盘按下? ──是──→ 创作中
    │否
    ▼
刚松开 (<1.2s)? ──是──→ 保持创作中
    │否
    ▼
进入间歇 ──→ 迷茫/思索 (4~10秒后恢复)
    │
    ▼
每 5~15 秒随机: 待机 ↔ 欣赏 ↔ 张望

操作说明

 操作  效果 
 左键拖拽  移动桌宠 
 左键点击  切换思索状态 
 滚轮  放大缩小 (50% ~ 200%) 
 键盘打字  自动切换创作形态 

项目结构

```
├── main.py              # 程序入口（托盘、菜单）
├── pet_window.py        # 核心：窗口、状态机、设置、闹钟
├── leimiaier1~6.gif     # 六种形态动画
├── tubiao.jpg           # 图标
├── run.bat              # 一键启动脚本
├── run.pyw              # 双击无控制台启动
├── build_exe.bat        # PyInstaller 打包脚本
└── requirements.txt     # 依赖列表
```

角色版权归米哈游《绝区零》所有，本项目仅供学习交流。
