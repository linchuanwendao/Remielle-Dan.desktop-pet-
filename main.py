"""
小小蕾米埃尔 - 桌宠主入口
启动方式: pythonw main.py   或   双击 run.bat
"""
import sys, os

# PyInstaller 兼容
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 检查依赖
try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
    from PyQt5.QtGui import QIcon, QPixmap
    from PyQt5.QtCore import Qt
except ModuleNotFoundError as e:
    print("=" * 55)
    print("  [ERROR] PyQt5 未安装！")
    print("  请在终端运行: pip install PyQt5")
    print("  或双击 run.bat 自动安装")
    print("=" * 55)
    input("按 Enter 退出...")
    sys.exit(1)

from pet_window import DeskPetWindow, SettingsManager, SettingsDialog, AlarmDialog, ICON_FILE


def make_tray(app, pet, sm):
    """创建系统托盘"""
    if os.path.exists(ICON_FILE):
        icon = QIcon(ICON_FILE)
    else:
        icon = QIcon()

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setToolTip("小小蕾米埃尔")
    tray.setVisible(True)

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu { background:#fff5f7; border:1.5px solid #f8c0d0; border-radius:10px; padding:5px; }
        QMenu::item { padding:8px 30px 8px 20px; color:#c44569; border-radius:6px; }
        QMenu::item:selected { background:#ffe0e8; }
        QMenu::separator { height:1px; background:#f8c0d0; margin:5px 15px; }
    """)

    a_show = menu.addAction("显示/隐藏桌宠")
    a_show.triggered.connect(lambda: pet.show() if pet.isHidden() else pet.hide())

    menu.addSeparator()
    a_set = menu.addAction("设置")
    a_set.triggered.connect(lambda: _open_settings(sm, pet))
    a_alarm = menu.addAction("闹钟")
    a_alarm.triggered.connect(lambda: AlarmDialog(sm).exec_())
    menu.addSeparator()
    a_about = menu.addAction("关于")
    a_about.triggered.connect(_show_about)
    a_quit = menu.addAction("退出")
    a_quit.triggered.connect(lambda: _quit(pet, app))

    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: _on_tray(reason, pet))
    return tray


def _on_tray(reason, pet):
    if reason == QSystemTrayIcon.DoubleClick:
        pet.show() if pet.isHidden() else pet.hide()


def _open_settings(sm, pet):
    d = SettingsDialog(sm)
    if d.exec_() == SettingsDialog.Accepted:
        pet._apply_zoom()


def _show_about():
    QMessageBox.information(
        None, "关于 小小蕾米埃尔",
        "*** 小小蕾米埃尔 ***\n\n"
        "绝区零角色 · 蕾米埃尔·丹 桌宠\n\n"
        "版本: 1.0\n"
        "初代虚狩 · 达识结社 · 六翼天使\n\n"
        "[操作说明]\n"
        "  左键拖拽 = 移动桌宠\n"
        "  左键点击 = 思索互动\n"
        "  右键     = 功能菜单\n"
        "  滚轮     = 放大缩小\n"
        "  键盘打字 = 切换创作状态\n\n"
        "[状态说明]\n"
        "  键盘输入时 → 创作中\n"
        "  输入间歇   → 迷茫/思索\n"
        "  其余时间   → 待机/欣赏/张望 随机切换\n\n"
        "关闭窗口 = 隐藏到系统托盘\n"
        "托盘右键 = 退出程序"
    )


def _quit(pet, app):
    pet.cleanup()
    app.quit()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("小小蕾米埃尔")
    app.setQuitOnLastWindowClosed(False)

    sm = SettingsManager()
    pet = DeskPetWindow(sm)
    tray = make_tray(app, pet, sm)
    pet.show()

    print("小小蕾米埃尔 已启动! (关闭窗口 = 隐藏到托盘)")
    if sys.stdout:
        sys.stdout.flush()

    try:
        app.exec_()
    finally:
        pet.cleanup()


if __name__ == "__main__":
    main()
