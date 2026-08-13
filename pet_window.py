"""
蕾米埃尔桌宠 - 核心窗口模块 (极简稳定版)
Desktop Pet Window - Remiel (ZZZ Character)

逻辑:
  键盘输入  → 创作中 (typing)
  输入间歇  → 迷茫/思索 (confused/thinking)
  其余时间  → 待机/欣赏/张望 随机切换 (idle/admire/look_around)
  无气泡    → 避免卡死
"""
import os, sys, random, time, json, ctypes
from ctypes import wintypes

from PyQt5.QtWidgets import (
    QWidget, QLabel, QApplication, QMenu, QDialog,
    QVBoxLayout, QHBoxLayout, QPushButton, QTimeEdit,
    QListWidget, QListWidgetItem, QGroupBox,
    QMessageBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QSize, pyqtSignal, QTime
)
from PyQt5.QtGui import QIcon, QPixmap, QMovie

# ============================================================
# PyInstaller 兼容: frozen 模式下用 sys._MEIPASS
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GIF_FILES = {
    "idle":        os.path.join(BASE_DIR, "leimiaier3.gif"),
    "typing":      os.path.join(BASE_DIR, "leimiaier1.gif"),
    "admire":      os.path.join(BASE_DIR, "leimiaier5.gif"),
    "thinking":    os.path.join(BASE_DIR, "leimiaier4.gif"),
    "look_around": os.path.join(BASE_DIR, "leimiaier2.gif"),
    "confused":    os.path.join(BASE_DIR, "leimiaier6.gif"),
}
ICON_FILE      = os.path.join(BASE_DIR, "tubiao.jpg")
SETTINGS_FILE  = os.path.join(BASE_DIR, "pet_settings.json")

DEFAULT_SETTINGS = {
    "zoom": 1.0, "short_idle_time": 10, "long_idle_time": 30,
    "auto_start": False, "alarms": [], "position": {"x": -1, "y": -1},
}

# 随机切换的普通形态 (不含 typing / thinking / confused)
NORMAL_STATES = ["idle", "admire", "look_around"]

# 输入间歇形态
BREAK_STATES = ["thinking", "confused"]


# ============================================================
# ★ Win32: GetAsyncKeyState 扫描 (纯键盘, 不误触鼠标)
# ============================================================
_KEY_SCAN_RANGES = [
    (0x08, 0x09), (0x0D, 0x0D), (0x10, 0x14), (0x1B, 0x1B),
    (0x20, 0x2F), (0x30, 0x39), (0x41, 0x5A), (0x60, 0x6F),
    (0xBA, 0xC0), (0xDB, 0xDF), (0xE2, 0xE2),
]

def _is_key_down():
    """任一键盘按键按下返回 True"""
    try:
        gak = ctypes.windll.user32.GetAsyncKeyState
        for lo, hi in _KEY_SCAN_RANGES:
            for vk in range(lo, hi + 1):
                if gak(vk) & 0x8000:
                    return True
    except Exception:
        pass
    return False


# ============================================================
class SettingsManager:
    def __init__(self):
        self._s = DEFAULT_SETTINGS.copy(); self.load()
    def load(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE,'r',encoding='utf-8') as f:
                    self._s.update(json.load(f))
        except Exception: pass
    def save(self):
        try:
            with open(SETTINGS_FILE,'w',encoding='utf-8') as f:
                json.dump(self._s, f, ensure_ascii=False, indent=2)
        except Exception: pass
    def get(self, k, d=None): return self._s.get(k, d)
    def set(self, k, v): self._s[k] = v; self.save()
    @property
    def zoom(self): return self._s.get("zoom", 1.0)
    @zoom.setter
    def zoom(self, v): self._s["zoom"] = max(0.5, min(2.0, v)); self.save()
    @property
    def short_idle_time(self): return self._s.get("short_idle_time", 10)
    @short_idle_time.setter
    def short_idle_time(self, v): self._s["short_idle_time"] = max(3, v); self.save()
    @property
    def long_idle_time(self): return self._s.get("long_idle_time", 30)
    @long_idle_time.setter
    def long_idle_time(self, v): self._s["long_idle_time"] = max(10, v); self.save()
    @property
    def auto_start(self): return self._s.get("auto_start", False)
    @auto_start.setter
    def auto_start(self, v):
        self._s["auto_start"] = v; self.save()
        try:
            import winreg
            kp = r"Software\Microsoft\Windows\CurrentVersion\Run"
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_SET_VALUE)
            if v:
                cmd = f'"{sys.executable}" "{os.path.join(BASE_DIR, "main.py")}"'
                winreg.SetValueEx(k, "XiaoXiaoLeiMiAiEr", 0, winreg.REG_SZ, cmd)
            else:
                try: winreg.DeleteValue(k, "XiaoXiaoLeiMiAiEr")
                except Exception: pass
            winreg.CloseKey(k)
        except Exception: pass
    @property
    def alarms(self): return self._s.get("alarms", [])
    @alarms.setter
    def alarms(self, v): self._s["alarms"] = v; self.save()
    @property
    def position(self): return self._s.get("position", {"x":-1,"y":-1})
    @position.setter
    def position(self, v): self._s["position"] = v; self.save()


# ============================================================
class SettingsDialog(QDialog):
    def __init__(self, sm):
        super().__init__(None); self.sm = sm
        self.setWindowTitle("小小蕾米埃尔 - 设置"); self.setFixedSize(420, 380)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self._ui(); self._load()
    def _ui(self):
        self.setStyleSheet("""
            QDialog{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fff5f7,stop:1 #ffe0e8);}
            QGroupBox{font-size:13px;font-weight:bold;color:#c44569;border:1.5px solid #f8c0d0;
                border-radius:10px;margin-top:15px;padding-top:18px;background:rgba(255,255,255,0.5);}
            QGroupBox::title{subcontrol-origin:margin;left:15px;padding:0 8px;}
            QLabel{color:#c44569;font-size:12px;}
            QSpinBox{border:1px solid #f0a0b8;border-radius:6px;padding:4px 8px;background:white;color:#c44569;}
            QCheckBox{color:#c44569;font-size:12px;}
            QPushButton{border:none;border-radius:12px;padding:8px 20px;font-size:13px;font-weight:bold;}
        """)
        lo = QVBoxLayout(self); lo.setSpacing(12); lo.setContentsMargins(20,15,20,15)
        zg = QGroupBox("缩放大小"); zl = QHBoxLayout()
        zl.addWidget(QLabel("桌宠缩放 (50%~200%):"))
        self.zs = QSpinBox(); self.zs.setRange(50,200); self.zs.setSuffix("%"); self.zs.setSingleStep(10)
        zl.addWidget(self.zs); zl.addStretch(); zg.setLayout(zl); lo.addWidget(zg)
        ig = QGroupBox("空闲切换时间"); il = QVBoxLayout()
        sl = QHBoxLayout(); sl.addWidget(QLabel("短时间 -> 张望:"))
        self.ss = QSpinBox(); self.ss.setRange(3,60); self.ss.setSuffix(" 秒")
        sl.addWidget(self.ss); sl.addStretch(); il.addLayout(sl)
        ll = QHBoxLayout(); ll.addWidget(QLabel("长时间 -> 迷茫:"))
        self.ls = QSpinBox(); self.ls.setRange(10,300); self.ls.setSuffix(" 秒")
        ll.addWidget(self.ls); ll.addStretch(); il.addLayout(ll)
        ig.setLayout(il); lo.addWidget(ig)
        sg = QGroupBox("系统设置"); sgl = QVBoxLayout()
        self.ac = QCheckBox("开机自动启动 小小蕾米埃尔"); sgl.addWidget(self.ac)
        sg.setLayout(sgl); lo.addWidget(sg)
        bl = QHBoxLayout(); bl.addStretch()
        sb = QPushButton("保存设置")
        sb.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ff8faa,stop:1 #e0567a);color:white;}QPushButton:hover{background:#f06292;}")
        sb.clicked.connect(self._save); bl.addWidget(sb)
        cb = QPushButton("取消"); cb.setStyleSheet("QPushButton{background:#f0f0f0;color:#888;}QPushButton:hover{background:#e0e0e0;}")
        cb.clicked.connect(self.reject); bl.addWidget(cb); lo.addLayout(bl)
    def _load(self):
        self.zs.setValue(int(self.sm.zoom*100)); self.ss.setValue(self.sm.short_idle_time)
        self.ls.setValue(self.sm.long_idle_time); self.ac.setChecked(self.sm.auto_start)
    def _save(self):
        self.sm.zoom = self.zs.value()/100.0; self.sm.short_idle_time = self.ss.value()
        self.sm.long_idle_time = self.ls.value(); self.sm.auto_start = self.ac.isChecked()
        self.accept()


class AlarmDialog(QDialog):
    def __init__(self, sm):
        super().__init__(None); self.sm = sm
        self.setWindowTitle("小小蕾米埃尔 - 闹钟"); self.setFixedSize(380, 330)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self._ui(); self._load()
    def _ui(self):
        self.setStyleSheet("""
            QDialog{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fff5f7,stop:1 #ffe0e8);}
            QGroupBox{font-size:13px;font-weight:bold;color:#c44569;border:1.5px solid #f8c0d0;
                border-radius:10px;margin-top:15px;padding-top:18px;background:rgba(255,255,255,0.5);}
            QGroupBox::title{subcontrol-origin:margin;left:15px;padding:0 8px;}
            QLabel{color:#c44569;font-size:12px;}
            QTimeEdit{border:1px solid #f0a0b8;border-radius:6px;padding:4px 8px;background:white;color:#c44569;}
            QPushButton{border:none;border-radius:12px;padding:6px 16px;font-size:12px;font-weight:bold;}
            QListWidget{border:1px solid #f0a0b8;border-radius:8px;background:rgba(255,255,255,0.7);color:#c44569;}
        """)
        lo = QVBoxLayout(self); lo.setSpacing(10); lo.setContentsMargins(20,15,20,15)
        ag = QGroupBox("添加闹钟"); al = QHBoxLayout(); al.addWidget(QLabel("时间:"))
        self.te = QTimeEdit(); self.te.setDisplayFormat("HH:mm"); self.te.setTime(QTime.currentTime())
        al.addWidget(self.te)
        ab = QPushButton("+ 添加"); ab.setStyleSheet("QPushButton{background:#ff8faa;color:white;}QPushButton:hover{background:#f06292;}")
        ab.clicked.connect(self._add); al.addWidget(ab); ag.setLayout(al); lo.addWidget(ag)
        lg = QGroupBox("闹钟列表"); ll = QVBoxLayout()
        self.alst = QListWidget(); ll.addWidget(self.alst)
        db = QPushButton("X 删除选中"); db.setStyleSheet("QPushButton{background:#ffcdd2;color:#c62828;}QPushButton:hover{background:#ef9a9a;}")
        db.clicked.connect(self._del); ll.addWidget(db); lg.setLayout(ll); lo.addWidget(lg)
        bl = QHBoxLayout(); bl.addStretch()
        cb = QPushButton("关闭"); cb.setStyleSheet("QPushButton{background:#f0f0f0;color:#888;}QPushButton:hover{background:#e0e0e0;}")
        cb.clicked.connect(self.accept); bl.addWidget(cb); lo.addLayout(bl)
    def _load(self):
        self.alst.clear()
        for a in self.sm.alarms:
            s = "[ON] " if a.get("enabled",True) else "[OFF] "
            self.alst.addItem(QListWidgetItem(s + a["time"]))
    def _add(self):
        t = self.te.time().toString("HH:mm")
        if any(a["time"]==t for a in self.sm.alarms):
            QMessageBox.information(self, "提示", "该时间已有闹钟！"); return
        self.sm.alarms.append({"time":t,"enabled":True,"message":"蕾米埃尔提醒你啦~"}); self._load()
    def _del(self):
        r = self.alst.currentRow()
        if 0 <= r < len(self.sm.alarms): self.sm.alarms.pop(r); self._load()


# ============================================================
# ★ 主窗口 - 纯状态切换, 无气泡
# ============================================================
class DeskPetWindow(QWidget):
    def __init__(self, sm):
        super().__init__(None)
        self.sm = sm
        self._state = None
        self._current_movie = None
        self._movies = {}
        self._gif_sizes = {}
        self._gif_w, self._gif_h = 200, 200

        self._drag_press_global = None
        self._drag_window_start = None
        self._was_typing = False
        self._in_break = False          # 是否在输入间歇 (thinking/confused)
        self._break_id = 0              # 防陈旧定时器
        self._last_key_time = 0.0       # 最后一次键盘按下的时间戳

        self._last_activity = time.time()
        self._save_pending = False
        self._save_timer = QTimer(self); self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save)

        self._setup_win()
        self._preload_gifs()
        self._switch_state("idle")

        # 主循环: 每350ms 检测键盘并更新状态
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.start(350)

        # 闹钟检测
        self._alarm_timer = QTimer(self)
        self._alarm_timer.timeout.connect(self._check_alarm)
        self._alarm_timer.start(30000)

        self._apply_zoom()

        # 初始位置
        pos = self.sm.position
        if pos["x"] >= 0 and pos["y"] >= 0:
            self.move(pos["x"], pos["y"])
        else:
            sg = QApplication.primaryScreen().availableGeometry()
            self.move(sg.width() - 380, sg.height() - 400)

    # ----------------------------------------------------------
    def _setup_win(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint |
            Qt.Tool | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowTitle("小小蕾米埃尔")
        if os.path.exists(ICON_FILE): self.setWindowIcon(QIcon(ICON_FILE))
        self._label = QLabel(self); self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background:transparent;")
        self.setFixedSize(200, 200)

    # ----------------------------------------------------------
    def _preload_gifs(self):
        for state, path in GIF_FILES.items():
            if not os.path.exists(path): continue
            try:
                pix = QPixmap(path)
                if pix and not pix.isNull():
                    self._gif_sizes[state] = (pix.width(), pix.height())
                movie = QMovie(path)
                self._movies[state] = movie
                print(f"[Preload] {state}: {pix.width()}x{pix.height()}")
            except Exception as e:
                print(f"[Preload] {state}: {e}")

    # ----------------------------------------------------------
    def _switch_state(self, new_state):
        if new_state == self._state: return
        if new_state not in self._movies: return
        try:
            if self._current_movie is not None:
                self._current_movie.stop()
            self._current_movie = self._movies[new_state]
            w, h = self._gif_sizes.get(new_state, (200, 200))
            self._gif_w, self._gif_h = w, h
            self._label.setMovie(self._current_movie)
            self._label.setFixedSize(w, h); self.setFixedSize(w, h)
            self._current_movie.start()
            self._state = new_state
            self._apply_zoom()
        except Exception as e:
            print(f"[Switch] {e}")

    # ----------------------------------------------------------
    # ★ 核心状态机
    # ----------------------------------------------------------
    def _on_tick(self):
        """每350ms调用一次: 键盘检测 + 随机切换"""
        try:
            key_down = _is_key_down()

            # --- 键盘按下 → 创作中 (记录时间) ---
            if key_down:
                self._last_key_time = time.time()
                if self._state != "typing":
                    self._switch_state("typing")
                self._was_typing = True
                self._in_break = False
                self._last_activity = time.time()
                return

            # --- 键盘松开后有 1.2 秒缓冲, 避免切换生硬 ---
            if self._was_typing and (time.time() - self._last_key_time < 1.2):
                return

            # --- 缓冲结束 → 进入间歇 (迷茫/思索) ---
            if self._was_typing:
                self._was_typing = False
                self._in_break = True
                self._break_id += 1
                brk = random.choice(BREAK_STATES)
                self._switch_state(brk)
                # 间歇持续 4~10 秒后回到普通循环
                delay = random.randint(4000, 10000)
                QTimer.singleShot(delay, lambda bid=self._break_id: self._end_break(bid))
                return

            # --- 间歇中, 不打扰 ---
            if self._in_break:
                return

            # --- 普通模式: 随机切换 idle/admire/look_around ---
            elapsed = time.time() - self._last_activity
            if elapsed >= self._switch_interval:
                # 随机选一个不同于当前的状态
                choices = [s for s in NORMAL_STATES if s != self._state]
                if choices:
                    self._switch_state(random.choice(choices))
                self._switch_interval = random.randint(5, 15)
                self._last_activity = time.time()

        except Exception as e:
            print(f"[Tick] {e}")

    def _end_break(self, bid):
        """间歇结束, 回到普通循环 (陈旧定时器直接忽略)"""
        try:
            if bid != self._break_id:
                return  # 已被新的间歇覆盖
            self._in_break = False
            self._switch_state(random.choice(NORMAL_STATES))
            self._switch_interval = random.randint(5, 15)
            self._last_activity = time.time()
        except Exception as e:
            print(f"[EndBreak] {e}")

    # 初始随机切换间隔
    _switch_interval = random.randint(5, 15)

    # ----------------------------------------------------------
    # 鼠标事件
    # ----------------------------------------------------------
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                self._drag_press_global = event.globalPos()
                self._drag_window_start = self.pos()
                self._last_activity = time.time()
                event.accept()
            elif event.button() == Qt.RightButton:
                self._last_activity = time.time()
                self._show_menu(event.globalPos())
                event.accept()
        except Exception as e: print(f"[Mouse] press: {e}")

    def mouseMoveEvent(self, event):
        try:
            if event.buttons() & Qt.LeftButton and self._drag_press_global is not None:
                delta = event.globalPos() - self._drag_press_global
                self.move(self._drag_window_start + delta)
                event.accept()
        except Exception as e: print(f"[Mouse] move: {e}")

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.LeftButton and self._drag_press_global is not None:
                dist = (event.globalPos() - self._drag_press_global).manhattanLength()
                self._drag_press_global = None; self._drag_window_start = None
                if dist < 5:
                    # 点击: 切换到思索, 进入间歇
                    self._in_break = True
                    self._break_id += 1
                    self._switch_state("thinking")
                    QTimer.singleShot(random.randint(3000, 7000),
                                      lambda bid=self._break_id: self._end_break(bid))
                event.accept()
        except Exception as e:
            print(f"[Mouse] release: {e}")
            self._drag_press_global = None; self._drag_window_start = None

    def enterEvent(self, event):
        self._last_activity = time.time(); super().enterEvent(event)

    def wheelEvent(self, event):
        try:
            delta = event.angleDelta().y()
            self.sm.zoom = self.sm.zoom + (0.06 if delta > 0 else -0.06)
            self._apply_zoom()
            self._last_activity = time.time()
        except Exception as e: print(f"[Wheel] {e}")

    # ----------------------------------------------------------
    def moveEvent(self, event):
        super().moveEvent(event)
        if not self._save_pending:
            self._save_pending = True; self._save_timer.start(1000)

    def _do_save(self):
        self._save_pending = False
        try:
            p = self.pos(); self.sm.position = {"x": p.x(), "y": p.y()}
        except Exception: pass

    def closeEvent(self, event):
        self._do_save(); super().closeEvent(event)

    # ----------------------------------------------------------
    def _apply_zoom(self):
        try:
            z = self.sm.zoom
            w = max(20, int(self._gif_w * z)); h = max(20, int(self._gif_h * z))
            self._label.setFixedSize(w, h); self.setFixedSize(w, h)
            if self._current_movie:
                self._current_movie.setScaledSize(QSize(w, h))
        except Exception as e: print(f"[Zoom] {e}")

    # ----------------------------------------------------------
    def _show_menu(self, pos):
        try:
            m = QMenu()
            m.setStyleSheet("""
                QMenu{background:#fff5f7;border:1.5px solid #f8c0d0;border-radius:10px;padding:5px;}
                QMenu::item{padding:8px 30px;color:#c44569;border-radius:6px;}
                QMenu::item:selected{background:#ffe0e8;}
                QMenu::separator{height:1px;background:#f8c0d0;margin:5px 15px;}
            """)
            zm = m.addMenu("缩放大小")
            for pct in [50,75,100,125,150,200]:
                a = zm.addAction(f"{pct}%")
                a.triggered.connect(lambda checked, v=pct: self._set_zoom(v))
            m.addSeparator()
            sm_menu = m.addMenu("切换形态")
            names = {"idle":"待机","typing":"创作中","admire":"欣赏作品",
                     "thinking":"思索中","look_around":"四处张望","confused":"迷茫中"}
            for k, v in names.items():
                a = sm_menu.addAction(v)
                a.triggered.connect(lambda checked, s=k: self._switch_state(s))
            m.addSeparator()
            m.addAction("设置").triggered.connect(self._open_settings)
            m.addAction("闹钟").triggered.connect(self._open_alarm)
            m.addSeparator()
            m.addAction("隐藏到托盘").triggered.connect(self.hide)
            m.addAction("退出").triggered.connect(self._quit)
            m.exec_(pos)
        except Exception as e: print(f"[Menu] {e}")

    def _set_zoom(self, pct): self.sm.zoom = pct/100.0; self._apply_zoom()

    def _open_settings(self):
        try:
            d = SettingsDialog(self.sm)
            if d.exec_() == QDialog.Accepted: self._apply_zoom()
        except Exception as e: print(f"[Settings] {e}")

    def _open_alarm(self):
        try: AlarmDialog(self.sm).exec_()
        except Exception as e: print(f"[Alarm] {e}")

    def _check_alarm(self):
        try:
            now = QTime.currentTime().toString("HH:mm")
            for a in self.sm.alarms:
                if a.get("enabled",True) and a["time"] == now:
                    if self.isHidden(): self.show()
        except Exception: pass

    def _quit(self):
        self._do_save(); self.cleanup(); QApplication.quit()

    def cleanup(self):
        try: self._tick.stop(); self._alarm_timer.stop()
        except Exception: pass
        try: self._save_timer.stop()
        except Exception: pass
        try:
            for movie in self._movies.values(): movie.stop()
            self._movies.clear(); self._current_movie = None
        except Exception: pass
