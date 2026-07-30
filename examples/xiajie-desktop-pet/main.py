from __future__ import annotations

import ctypes
from dataclasses import dataclass
import math
import os
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QFont,
    QFontDatabase,
    QKeyEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QWidget


APP_NAME = "霞姐桌宠"


def chinese_font() -> str:
    fonts_dir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for filename in ("msyh.ttc", "simhei.ttf"):
        font_path = fonts_dir / filename
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    available = set(QFontDatabase.families())
    for family in ("Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑", "SimHei", "Arial Unicode MS"):
        if family in available:
            return family
    return QFont().defaultFamily()


def resource_path(relative: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative


@dataclass
class Particle:
    kind: str
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: QColor


class DesktopPet(QWidget):
    MIN_SCALE = 0.48
    MAX_SCALE = 1.65
    BASE_WIDTH = 350
    BASE_HEIGHT = 520
    BUBBLE_HEIGHT = 112

    CHAT_LINES = [
        "霞姐在呢，慢慢说，我听着～",
        "今天也辛苦啦，先深呼吸一下。",
        "桌面这么大，我陪你逛一圈！",
        "给你一朵小黄花，心情要放晴哦。",
        "工作可以认真，休息也要认真呀。",
        "偷偷补充一点元气：叮——到账！",
    ]
    CLICK_LINES = [
        "呀，被你发现啦！",
        "霞姐闪亮登场～",
        "再点一下，会有不同反应哦。",
        "今天也要元气满满！",
        "嘿咻！接住这颗小星星。",
    ]
    DRAG_LINES = [
        "等等，霞姐要起飞啦！",
        "出发出发～",
        "慢一点，头发要乱啦。",
        "收到！正在高速移动！",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.font_family = chinese_font()

        self.always_on_top = True
        self._apply_window_flags()

        self.sprites = {
            name: QPixmap(str(resource_path(f"assets/{filename}")))
            for name, filename in {
                "idle": "pet.png",
                "side": "side.png",
                "back": "back.png",
                "chat": "chat.png",
                "pat": "pat.png",
                "feed": "feed.png",
                "sleep": "sleep.png",
                "walk": "walk.png",
            }.items()
        }
        missing = [name for name, pixmap in self.sprites.items() if pixmap.isNull()]
        if missing:
            raise RuntimeError(f"角色素材加载失败：{', '.join(missing)}")
        self.animation_frames = self._load_animation_frames()

        self.scale_factor = 0.80
        self.state = "idle"
        self.state_started = time.monotonic()
        self.state_duration: float | None = None
        self.smart_idle = True
        self.energy = 82.0
        self.affection = 45.0
        self.last_tick = time.monotonic()
        self.next_roam = time.monotonic() + random.uniform(12.0, 20.0)
        self.roam_target: QPoint | None = None
        self.motion_velocity = QPointF(0.0, 0.0)
        self.last_drag_time = time.monotonic()
        self.drag_velocity = QPointF(0.0, 0.0)
        self.last_notice = 0.0
        self.cursor_near = False
        self.click_index = 0
        self.dragging = False
        self.press_global = QPoint()
        self.press_window = QPoint()
        self.drag_distance = 0
        self.last_drag_x = 0
        self.facing = -1
        self.walk_direction = -1
        self.follow_enabled = False
        self.escape_was_down = False
        self.bubble_text = ""
        self.bubble_until = 0.0
        self.bubble_started = 0.0
        self.bubble_reveal = 0
        self.last_drag_bubble = 0.0
        self.last_particle_spawn = 0.0
        self.particles: list[Particle] = []
        self.next_blink = time.monotonic() + random.uniform(2.5, 5.0)
        self.blink_until = 0.0
        self.next_idle_action = time.monotonic() + random.uniform(9.0, 15.0)

        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.frame_timer.timeout.connect(self.tick)
        self.frame_timer.start(20)

        self._resize_for_scale()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 34, screen.bottom() - self.height() - 16)
        self.show_bubble("你好，我是霞姐～右键看看新动作吧！", 4.0)

    def _load_animation_frames(self) -> dict[str, list[QPixmap]]:
        frames_root = resource_path("assets/frames")
        result: dict[str, list[QPixmap]] = {}
        if not frames_root.exists():
            return result
        for action in ("idle", "walk", "wave", "pat", "feed", "sleep"):
            frames = [QPixmap(str(path)) for path in sorted(frames_root.glob(f"{action}_*.png"))]
            frames = [frame for frame in frames if not frame.isNull()]
            if len(frames) >= 2:
                result[action] = frames
        return result

    def _apply_window_flags(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        visible = self.isVisible()
        position = self.pos()
        self.setWindowFlags(flags)
        if visible:
            self.show()
            self.move(position)

    def _resize_for_scale(self) -> None:
        self.resize(
            round(self.BASE_WIDTH * self.scale_factor),
            round((self.BASE_HEIGHT + self.BUBBLE_HEIGHT) * self.scale_factor),
        )
        self.update()

    def show_bubble(self, text: str, seconds: float = 2.8) -> None:
        self.bubble_text = text
        self.bubble_started = time.monotonic()
        self.bubble_reveal = 0
        self.bubble_until = self.bubble_started + seconds
        self.update()

    def activate(self, state: str, duration: float | None = None) -> None:
        if state != self.state:
            self.particles.clear()
        self.state = state
        self.state_started = time.monotonic()
        self.state_duration = duration
        self.last_particle_spawn = 0.0
        self.update()

    def _screen_bounds(self):
        return self.screen().availableGeometry()

    def _clamped_position(self, position: QPoint) -> QPoint:
        screen = self._screen_bounds()
        return QPoint(
            max(screen.left(), min(screen.right() - self.width(), position.x())),
            max(screen.top(), min(screen.bottom() - self.height(), position.y())),
        )

    def _set_position_clamped(self, position: QPoint) -> None:
        self.move(self._clamped_position(position))

    def _start_wander(self) -> None:
        screen = self._screen_bounds()
        margin = 24
        target_x = random.randint(screen.left() + margin, max(screen.left() + margin, screen.right() - self.width() - margin))
        target_y = random.randint(screen.top() + margin, max(screen.top() + margin, screen.bottom() - self.height() - margin))
        self.roam_target = QPoint(target_x, target_y)
        self.facing = 1 if target_x > self.x() else -1
        self.activate("wander")
        if random.random() < 0.55:
            self.show_bubble(random.choice(["去附近看看～", "霞姐巡游一下。", "换个位置陪你！"]), 2.0)

    def _stop_motion(self) -> None:
        self.motion_velocity = QPointF(0.0, 0.0)
        self.roam_target = None

    def _mood_text(self) -> str:
        if self.energy < 24:
            return "有点困"
        if self.affection > 75:
            return "心情很好"
        if self.energy > 78:
            return "元气满满"
        return "悠闲陪伴中"

    def tick(self) -> None:
        now = time.monotonic()
        dt = min(0.05, max(0.001, now - self.last_tick))
        self.last_tick = now
        elapsed = now - self.state_started
        self._poll_global_escape()
        self.energy = min(100.0, max(0.0, self.energy - dt * (0.06 if self.state != "sleep" else -2.2)))
        self.affection = max(0.0, self.affection - dt * 0.015)
        if self.bubble_text:
            self.bubble_reveal = min(len(self.bubble_text), int((now - self.bubble_started) * 24) + 1)

        if self.follow_enabled and not self.dragging:
            cursor = QCursor.pos()
            target = QPoint(cursor.x() + 46, cursor.y() + 54)
            delta = target - self.pos()
            if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                self.facing = 1 if delta.x() >= 0 else -1
                follow_rate = min(1.0, dt * 9.5)
                self._set_position_clamped(self.pos() + QPoint(round(delta.x() * follow_rate), round(delta.y() * follow_rate)))
            self.state = "follow"

        if self.state == "walk":
            screen = self.screen().availableGeometry()
            x = self.x() + self.walk_direction * max(2, round(210 * dt * self.scale_factor))
            if x <= screen.left() or x + self.width() >= screen.right():
                self.walk_direction *= -1
                self.facing = self.walk_direction
                x = max(screen.left(), min(screen.right() - self.width(), x))
                self.show_bubble(random.choice(["换个方向继续～", "这里到边啦！"]), 1.8)
            self.move(x, self.y())
        elif self.state == "wander" and self.roam_target is not None:
            delta = self.roam_target - self.pos()
            distance = math.hypot(delta.x(), delta.y())
            if distance < 5:
                self._stop_motion()
                self.activate("idle")
                self.next_roam = now + random.uniform(15.0, 28.0)
            else:
                self.facing = 1 if delta.x() >= 0 else -1
                speed = min(235.0 * self.scale_factor, max(75.0, distance * 2.4))
                step = min(distance, speed * dt)
                self._set_position_clamped(self.pos() + QPoint(round(delta.x() / distance * step), round(delta.y() / distance * step)))
        elif self.state == "glide":
            old_pos = self.pos()
            proposed = old_pos + QPoint(round(self.motion_velocity.x() * dt), round(self.motion_velocity.y() * dt))
            clamped = self._clamped_position(proposed)
            if clamped.x() != proposed.x():
                self.motion_velocity.setX(-self.motion_velocity.x() * 0.42)
                self.facing = 1 if self.motion_velocity.x() > 0 else -1
            if clamped.y() != proposed.y():
                self.motion_velocity.setY(-self.motion_velocity.y() * 0.32)
            self.move(clamped)
            damping = pow(0.055, dt)
            self.motion_velocity *= damping
            if self.motion_velocity.manhattanLength() < 32:
                self._stop_motion()
                self.activate("squash", 0.62)
        elif self.state == "pat":
            self._spawn_periodic("heart", 0.72)
        elif self.state == "feed":
            self._spawn_periodic("crumb", 0.82)
        elif self.state == "sleep":
            self._spawn_periodic("sleep", 1.35)

        if self.state_duration is not None and elapsed > self.state_duration:
            self.activate("idle")

        if self.state == "idle":
            if now >= self.next_blink:
                self.blink_until = now + 0.16
                self.next_blink = now + random.uniform(3.0, 6.0)
            self._react_to_nearby_cursor(now)
            if self.smart_idle and now >= self.next_roam:
                self._automatic_idle_action()

        self._update_particles(dt)
        if self.bubble_text and now > self.bubble_until:
            self.bubble_text = ""
        self.update()

    def _react_to_nearby_cursor(self, now: float) -> None:
        cursor = QCursor.pos()
        center = self.geometry().center()
        self.cursor_near = math.hypot(cursor.x() - center.x(), cursor.y() - center.y()) < max(self.width(), self.height()) * 0.82
        if self.cursor_near and now - self.last_notice > 8.0 and random.random() < 0.04:
            self.last_notice = now
            self.activate("notice", 1.35)
            self.show_bubble(random.choice(["嗯？你在看霞姐吗？", "需要我帮忙吗？", "我在哦。"]), 2.1)

    def _poll_global_escape(self) -> None:
        if sys.platform != "win32":
            return
        pressed = bool(ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000)
        if pressed and not self.escape_was_down and self.follow_enabled:
            self.stop_follow("已停止跟随，霞姐在这里等你。")
        self.escape_was_down = pressed

    def _automatic_idle_action(self) -> None:
        now = time.monotonic()
        self.next_roam = now + random.uniform(14.0, 26.0)
        if self.energy < 20:
            self.activate("sleep")
            self.show_bubble("霞姐先眯一会儿，轻轻叫醒我哦。", 3.0)
        elif random.random() < 0.42:
            self._start_wander()
        elif random.random() < 0.66:
            self.activate("chat", 1.8)
            self.show_bubble(random.choice(self.CHAT_LINES), 2.6)
        else:
            self.activate("jump", 0.85)
            self.show_bubble(random.choice(["活动一下肩膀～", "霞姐巡逻中！", "别忘了喝口水。"]), 2.2)

    def _spawn_periodic(self, kind: str, interval: float) -> None:
        now = time.monotonic()
        if now - self.last_particle_spawn < interval:
            return
        self.last_particle_spawn = now
        scale = self.scale_factor
        if kind == "dust":
            self.spawn_particle(
                "dust",
                self.width() * 0.48,
                self.height() - 24 * scale,
                random.uniform(-18, 18),
                random.uniform(-18, -5),
                0.65,
                random.uniform(8, 14) * scale,
                QColor("#d7c5bb"),
            )
        elif kind == "heart":
            self.spawn_particle(
                "heart",
                self.width() * random.uniform(0.35, 0.68),
                self.BUBBLE_HEIGHT * scale + 78 * scale,
                random.uniform(-11, 11),
                random.uniform(-38, -24),
                1.2,
                random.uniform(10, 17) * scale,
                QColor(random.choice(["#ff6f9f", "#ff8fbd", "#f45d83"])),
            )
        elif kind == "crumb":
            self.spawn_particle(
                random.choice(["crumb", "sparkle"]),
                self.width() * 0.53,
                self.BUBBLE_HEIGHT * scale + 120 * scale,
                random.uniform(-28, 28),
                random.uniform(-8, 18),
                0.9,
                random.uniform(5, 10) * scale,
                QColor(random.choice(["#f3b94e", "#d68a36", "#ffe087"])),
            )
        elif kind == "sleep":
            self.spawn_particle(
                "z",
                self.width() * 0.68,
                self.BUBBLE_HEIGHT * scale + 100 * scale,
                random.uniform(3, 10),
                random.uniform(-30, -20),
                1.5,
                random.uniform(13, 20) * scale,
                QColor("#8064a8"),
            )
        else:
            self.spawn_particle(
                "sparkle",
                self.width() * random.uniform(0.18, 0.82),
                self.BUBBLE_HEIGHT * scale + random.uniform(45, 280) * scale,
                random.uniform(-8, 8),
                random.uniform(-22, -8),
                0.9,
                random.uniform(7, 13) * scale,
                QColor(random.choice(["#ffd95a", "#fff2a8", "#7dd8ff"])),
            )

    def spawn_particle(
        self,
        kind: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        size: float,
        color: QColor,
    ) -> None:
        self.particles.append(Particle(kind, x, y, vx, vy, life, life, size, color))
        if len(self.particles) > 90:
            self.particles = self.particles[-90:]

    def _update_particles(self, dt: float) -> None:
        alive: list[Particle] = []
        for particle in self.particles:
            particle.life -= dt
            if particle.life <= 0:
                continue
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            if particle.kind in {"dust", "crumb"}:
                particle.vy += 34 * dt
            alive.append(particle)
        self.particles = alive

    def _sprite_key(self) -> str:
        if self.state in {"walk", "follow", "drag_run", "wander", "glide"}:
            return "walk"
        return {
            "chat": "chat",
            "notice": "chat",
            "pat": "pat",
            "feed": "feed",
            "sleep": "sleep",
        }.get(self.state, "idle")

    def _animation_action(self, sprite_key: str) -> str:
        if sprite_key in {"walk", "side"}:
            return "walk"
        if sprite_key == "chat":
            return "wave"
        return sprite_key

    def _render_frames(self, sprite_key: str, elapsed: float) -> tuple[QPixmap, QPixmap | None, float]:
        action = self._animation_action(sprite_key)
        frames = self.animation_frames.get(action)
        if not frames:
            sprite = self.sprites[sprite_key]
            return sprite, None, 0.0
        # Use fixed frame holds instead of continuously cross-fading two photos.
        # Cross-fading made facial features and body edges appear to morph on
        # every paint tick, which was visually tiring and felt like unstable FPS.
        frame_ms = {
            "idle": 640,
            "walk": 170,
            "wave": 240,
            "pat": 280,
            "feed": 320,
            "sleep": 720,
        }.get(action, 260)
        index = int(max(0.0, elapsed) * 1000.0 // frame_ms) % len(frames)
        return frames[index], None, 0.0

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        now = time.monotonic()

        if self.follow_enabled:
            self._draw_follow_badge(painter)
        elif self.bubble_text and now <= self.bubble_until:
            self._draw_bubble(painter)

        sprite_key = self._sprite_key()
        sprite, next_sprite, frame_blend = self._render_frames(sprite_key, now - self.state_started)
        top = self.BUBBLE_HEIGHT * self.scale_factor
        area = QRectF(5, top, self.width() - 10, self.height() - top - 5)
        ratio = sprite.width() / sprite.height()
        draw_height = area.height()
        draw_width = draw_height * ratio
        if draw_width > area.width():
            draw_width = area.width()
            draw_height = draw_width / ratio
        base_x = area.center().x() - draw_width / 2
        base_y = area.bottom() - draw_height

        t = now - self.state_started
        offset_x = 0.0
        offset_y = 0.0
        scale_x = 1.0
        scale_y = 1.0
        rotation = 0.0
        if self.state == "jump":
            phase = min(1.0, t / 0.85)
            offset_y = -math.sin(phase * math.pi) * 42 * self.scale_factor
        elif self.state == "squash":
            phase = min(1.0, t / 0.78)
            wave = math.sin(phase * math.pi)
            scale_y = 1.0 - wave * 0.12
            scale_x = 1.0 + wave * 0.06
        elif self.state == "shake":
            phase = min(1.0, t / 0.82)
            offset_x = math.sin(phase * math.pi * 8) * (1 - phase) * 8 * self.scale_factor
        elif self.state == "notice":
            offset_y = -math.sin(min(1.0, t / 1.35) * math.pi) * 2 * self.scale_factor

        flip = -1.0 if sprite_key in {"walk", "side"} and self.facing > 0 else 1.0
        painter.save()
        center_x = base_x + draw_width / 2
        bottom_y = base_y + draw_height
        painter.translate(center_x + offset_x, bottom_y + offset_y)
        painter.rotate(rotation)
        painter.scale(flip * scale_x, scale_y)
        target = QRectF(-draw_width / 2, -draw_height, draw_width, draw_height)
        painter.setOpacity(1.0 - frame_blend if next_sprite is not None else 1.0)
        painter.drawPixmap(target, sprite, QRectF(sprite.rect()))
        if next_sprite is not None:
            painter.setOpacity(frame_blend)
            painter.drawPixmap(target, next_sprite, QRectF(next_sprite.rect()))
        painter.setOpacity(1.0)
        # The idle strip already contains its own blink frame. Do not paint a
        # second synthetic blink on top of it, which can look like a face flash.
        if sprite_key == "idle" and not self.animation_frames.get("idle") and now <= self.blink_until:
            self._draw_blink(painter, target)
        painter.restore()

        self._draw_particles(painter)
        if not self.follow_enabled and not self.bubble_text and self.state == "idle":
            self._draw_mood_chip(painter)

    def _draw_blink(self, painter: QPainter, target: QRectF) -> None:
        source = self.sprites["idle"]
        sx = target.width() / source.width()
        sy = target.height() / source.height()
        for source_x in (112, 163):
            x = target.left() + source_x * sx
            y = target.top() + 94 * sy
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#e8b99f"))
            painter.drawEllipse(QPointF(x, y), 8 * sx, 5 * sy)
            painter.setPen(QPen(QColor("#4b302d"), max(1.2, 2.2 * sx)))
            painter.drawArc(QRectF(x - 8 * sx, y - 3 * sy, 16 * sx, 8 * sy), 0, -180 * 16)

    def _draw_particles(self, painter: QPainter) -> None:
        for particle in self.particles:
            opacity = max(0.0, particle.life / particle.max_life)
            color = QColor(particle.color)
            color.setAlphaF(min(1.0, opacity))
            painter.save()
            painter.translate(particle.x, particle.y)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            size = particle.size * (0.7 + 0.3 * opacity)
            if particle.kind == "heart":
                path = QPainterPath()
                path.moveTo(0, size * 0.42)
                path.cubicTo(-size, -size * 0.15, -size * 0.56, -size, 0, -size * 0.45)
                path.cubicTo(size * 0.56, -size, size, -size * 0.15, 0, size * 0.42)
                painter.drawPath(path)
            elif particle.kind == "sparkle":
                path = QPainterPath()
                for index in range(8):
                    angle = -math.pi / 2 + index * math.pi / 4
                    radius = size if index % 2 == 0 else size * 0.28
                    point = QPointF(math.cos(angle) * radius, math.sin(angle) * radius)
                    if index == 0:
                        path.moveTo(point)
                    else:
                        path.lineTo(point)
                path.closeSubpath()
                painter.drawPath(path)
            elif particle.kind == "dust":
                painter.drawEllipse(QPointF(0, 0), size, size * 0.55)
            elif particle.kind == "crumb":
                painter.rotate((1 - opacity) * 160)
                painter.drawRoundedRect(QRectF(-size / 2, -size / 2, size, size), 2, 2)
            elif particle.kind == "z":
                painter.setPen(color)
                painter.setFont(QFont(self.font_family, max(9, round(size)), QFont.Weight.Bold))
                painter.drawText(QPointF(0, 0), "Z")
            painter.restore()

    def _bubble_rect(self) -> QRectF:
        margin = max(5, round(8 * self.scale_factor))
        return QRectF(
            margin,
            margin,
            self.width() - margin * 2,
            self.BUBBLE_HEIGHT * self.scale_factor - margin * 2 - 8,
        )

    def _draw_bubble(self, painter: QPainter) -> None:
        rect = self._bubble_rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 16, 16)
        tail_x = min(rect.right() - 30, rect.center().x() + 48)
        tail = QPainterPath()
        tail.moveTo(tail_x - 12, rect.bottom() - 1)
        tail.lineTo(tail_x + 1, rect.bottom() + 14)
        tail.lineTo(tail_x + 14, rect.bottom() - 1)
        tail.closeSubpath()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor(255, 253, 255, 247))
        gradient.setColorAt(1, QColor(255, 232, 247, 242))
        painter.setPen(QPen(QColor(177, 112, 162, 175), 1.4))
        painter.setBrush(gradient)
        painter.drawPath(path)
        painter.drawPath(tail)
        painter.setPen(QColor("#493a4a"))
        painter.setFont(QFont(self.font_family, max(9, round(11 * self.scale_factor))))
        painter.drawText(
            rect.adjusted(13, 8, -13, -8),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.bubble_text[: self.bubble_reveal],
        )

    def _draw_follow_badge(self, painter: QPainter) -> None:
        rect = self._bubble_rect()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#fff4cf"))
        gradient.setColorAt(1, QColor("#ffd8e9"))
        painter.setPen(QPen(QColor("#d78a55"), 1.5))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect, 16, 16)
        painter.setPen(QColor("#704131"))
        painter.setFont(QFont(self.font_family, max(9, round(11 * self.scale_factor)), QFont.Weight.Bold))
        painter.drawText(
            rect.adjusted(10, 6, -10, -6),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            "正在跟随鼠标\n按 Esc、左键点击或右键菜单停止",
        )

    def _draw_mood_chip(self, painter: QPainter) -> None:
        text = self._mood_text()
        rect = QRectF(self.width() - 102 * self.scale_factor, 8, 94 * self.scale_factor, 25 * self.scale_factor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 250, 255, 205))
        painter.drawRoundedRect(rect, 12, 12)
        painter.setPen(QColor("#8b6381"))
        painter.setFont(QFont(self.font_family, max(7, round(8.5 * self.scale_factor))))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.follow_enabled:
                self.stop_follow("跟随已停止，霞姐不乱跑啦。")
            self.press_global = event.globalPosition().toPoint()
            self.press_window = self.pos()
            self.drag_distance = 0
            self.last_drag_x = self.press_global.x()
            self.last_drag_time = time.monotonic()
            self.drag_velocity = QPointF(0.0, 0.0)
            self.dragging = False
            self._stop_motion()
            self.activate("idle")
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.open_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            current = event.globalPosition().toPoint()
            delta = current - self.press_global
            self.drag_distance = max(self.drag_distance, delta.manhattanLength())
            if self.drag_distance > 5:
                self.dragging = True
                now = time.monotonic()
                elapsed = max(0.001, now - self.last_drag_time)
                previous = self.pos()
                self._set_position_clamped(self.press_window + delta)
                current_pos = self.pos()
                instantaneous = QPointF((current_pos.x() - previous.x()) / elapsed, (current_pos.y() - previous.y()) / elapsed)
                self.drag_velocity = self.drag_velocity * 0.45 + instantaneous * 0.55
                self.last_drag_time = now
                direction_delta = current.x() - self.last_drag_x
                if abs(direction_delta) > 1:
                    self.facing = 1 if direction_delta > 0 else -1
                self.last_drag_x = current.x()
                if self.state != "drag_run":
                    self.activate("drag_run")
                if now - self.last_drag_bubble > 2.8 and random.random() < 0.055:
                    self.show_bubble(random.choice(self.DRAG_LINES), 2.0)
                    self.last_drag_bubble = now
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.dragging:
                interactions = [
                    ("jump", 0.85),
                    ("pat", 1.7),
                    ("squash", 0.78),
                    ("chat", 1.65),
                    ("shake", 0.82),
                ]
                state, duration = interactions[self.click_index % len(interactions)]
                self.click_index += 1
                self.activate(state, duration)
                self.show_bubble(random.choice(self.CLICK_LINES), max(1.8, duration))
            else:
                speed = math.hypot(self.drag_velocity.x(), self.drag_velocity.y())
                if speed > 140:
                    self.motion_velocity = QPointF(
                        max(-900.0, min(900.0, self.drag_velocity.x() * 0.22)),
                        max(-700.0, min(700.0, self.drag_velocity.y() * 0.22)),
                    )
                    self.activate("glide", 1.65)
                    self.show_bubble(random.choice(["接住啦！", "霞姐滑行中～", "这一下有点速度！"]), 1.7)
                else:
                    self.activate("idle")
            self.dragging = False
            event.accept()

    def wheelEvent(self, event) -> None:
        steps = event.angleDelta().y() / 120
        old_center = self.geometry().center()
        self.scale_factor = max(self.MIN_SCALE, min(self.MAX_SCALE, self.scale_factor + steps * 0.07))
        self._resize_for_scale()
        self.move(old_center - self.rect().center())
        self.show_bubble(f"霞姐现在是 {round(self.scale_factor * 100)}% 大小", 1.6)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self.follow_enabled:
            self.stop_follow("已停止跟随。")
            event.accept()
            return
        super().keyPressEvent(event)

    def open_menu(self, global_pos: QPoint) -> None:
        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu { background:#fffaff; color:#413642; border:1px solid #d8bdd6;
                    border-radius:9px; padding:6px; font-size:10pt; }
            QMenu::item { padding:8px 28px 8px 13px; border-radius:6px; }
            QMenu::item:selected { background:#f2dff0; }
            QMenu::separator { height:1px; background:#eaddea; margin:5px 8px; }
            """
        )
        title = menu.addAction("霞姐桌宠")
        title.setEnabled(False)
        menu.addSeparator()
        menu.addAction("陪我聊聊天", self.chat)
        menu.addAction("摸摸头", self.pet_head)
        menu.addAction("喂吃的", self.feed)
        menu.addSeparator()
        menu.addAction("停止走路" if self.state == "walk" else "让她走路", self.toggle_walk)
        menu.addAction("叫醒霞姐" if self.state == "sleep" else "让她睡觉", self.toggle_sleep)

        follow_label = "停止跟随鼠标（Esc）" if self.follow_enabled else "跟随鼠标"
        follow_action = QAction(follow_label, menu)
        follow_action.setCheckable(True)
        follow_action.setChecked(self.follow_enabled)
        follow_action.triggered.connect(self.set_follow)
        menu.addAction(follow_action)

        smart_action = QAction("智能待机与巡游", menu)
        smart_action.setCheckable(True)
        smart_action.setChecked(self.smart_idle)
        smart_action.triggered.connect(self.set_smart_idle)
        menu.addAction(smart_action)
        menu.addAction("回到桌面右下角", self.return_to_corner)

        size_menu = menu.addMenu("调整大小")
        for label, value in (("60%", 0.60), ("80%", 0.80), ("100%", 1.00), ("125%", 1.25), ("150%", 1.50)):
            action = size_menu.addAction(label)
            action.triggered.connect(lambda checked=False, s=value: self.set_scale(s))

        top_action = QAction("始终置顶", menu)
        top_action.setCheckable(True)
        top_action.setChecked(self.always_on_top)
        top_action.triggered.connect(self.toggle_topmost)
        menu.addAction(top_action)
        menu.addSeparator()
        menu.addAction("退出霞姐桌宠", QApplication.instance().quit)
        menu.exec(global_pos)

    def chat(self) -> None:
        self.set_follow(False)
        self.activate("chat")
        self.show_bubble("霞姐认真听着呢……", 30.0)
        text, accepted = QInputDialog.getText(self, "陪霞姐聊聊天", "想和霞姐说什么？")
        if not accepted:
            self.activate("idle")
            self.show_bubble("没关系，想说的时候再来找我。", 2.8)
            return
        message = text.strip()
        if not message:
            reply = "不说话也没关系，霞姐陪你待一会儿。"
        elif any(word in message for word in ("累", "困", "烦", "难过")):
            reply = "辛苦啦，先休息几分钟，我替你守着桌面。"
        elif any(word in message for word in ("你好", "嗨", "早", "晚安")):
            reply = "你好呀！霞姐见到你真开心～"
        elif "吃" in message:
            reply = "说到吃的，我突然也有点馋啦……"
        elif "喜欢" in message:
            reply = "嘿嘿，霞姐也喜欢和你待在一起！"
        else:
            reply = random.choice(self.CHAT_LINES)
        self.activate("chat", 4.4)
        self.show_bubble(reply, 4.4)

    def pet_head(self) -> None:
        self.set_follow(False)
        self.affection = min(100.0, self.affection + 12.0)
        self.energy = min(100.0, self.energy + 4.0)
        self.activate("pat", 3.0)
        self.show_bubble(random.choice(["好舒服～再摸一下嘛。", "霞姐收到你的摸摸啦！", "头发可别揉乱哦～"]), 3.0)

    def feed(self) -> None:
        self.set_follow(False)
        self.energy = min(100.0, self.energy + 26.0)
        self.affection = min(100.0, self.affection + 8.0)
        self.activate("feed", 3.2)
        self.show_bubble(random.choice(["啊呜！谢谢投喂～", "好吃！幸福值上升！", "霞姐还给你留了一口。"]), 3.2)

    def toggle_walk(self) -> None:
        self.set_follow(False)
        if self.state == "walk":
            self._stop_motion()
            self.activate("idle")
            self.show_bubble("散步结束，霞姐回来陪你。", 2.4)
        else:
            self.walk_direction = self.facing
            self.activate("walk")
            self.show_bubble("走起！看看桌面那边有什么～", 2.4)

    def toggle_sleep(self) -> None:
        self.set_follow(False)
        if self.state == "sleep":
            self.activate("idle")
            self.show_bubble("霞姐醒啦，精神满满！", 2.4)
        else:
            self.activate("sleep")
            self.show_bubble("晚安……记得一会儿叫醒霞姐。", 3.0)

    def set_follow(self, enabled: bool) -> None:
        if enabled:
            self._stop_motion()
            self.follow_enabled = True
            self.activate("follow")
            self.setFocus(Qt.FocusReason.OtherFocusReason)
            self.show_bubble("", 0)
        else:
            self.stop_follow()

    def stop_follow(self, message: str | None = None) -> None:
        if not self.follow_enabled and self.state != "follow":
            return
        self.follow_enabled = False
        self.activate("idle")
        if message:
            self.show_bubble(message, 2.4)

    def set_smart_idle(self, enabled: bool) -> None:
        self.smart_idle = enabled
        self.next_roam = time.monotonic() + random.uniform(10.0, 16.0)
        self.show_bubble("智能待机已开启" if enabled else "智能待机已暂停", 2.0)

    def return_to_corner(self) -> None:
        self.stop_follow()
        self._stop_motion()
        screen = self._screen_bounds()
        self._set_position_clamped(QPoint(screen.right() - self.width() - 28, screen.bottom() - self.height() - 18))
        self.activate("idle")
        self.show_bubble("我回到右下角等你啦。", 2.2)

    def set_scale(self, scale: float) -> None:
        old_center = self.geometry().center()
        self.scale_factor = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        self._resize_for_scale()
        self.move(old_center - self.rect().center())

    def toggle_topmost(self, enabled: bool) -> None:
        self.always_on_top = enabled
        self._apply_window_flags()
        self.show_bubble("置顶已开启" if enabled else "置顶已关闭", 1.8)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(True)
    pet = DesktopPet()
    pet.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
