from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen
from PyQt6.QtCore import Qt, QPointF
from core.theme_manager import theme_manager

class ModernSidebarButton(QPushButton):
    """
    Style Vector Icon Button.
    Contains ALL drawing primitives for the application.
    """
    def __init__(self, icon_type, tooltip_text, parent=None, size=(64, 50)):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(size[0], size[1]) 
        self.setToolTip(tooltip_text)
        
        # UI Behavior
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFlat(True) 
        
        # Reactive Theme
        theme_manager.theme_changed.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        p = theme_manager.active_palette
        
        bg_color = Qt.GlobalColor.transparent
        icon_color = theme_manager.get_qcolor('text_muted')
        accent = theme_manager.get_qcolor('accent_main')
        
        # State Logic
        is_active = self.isChecked() or self.isDown()
        
        if is_active:
            bg_color = theme_manager.get_qcolor('bg_surface')
            icon_color = accent
            
            # Sidebar Active Indicator
            if self.width() > 50:
                painter.setBrush(accent)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(0, 8, 3, self.height() - 16, 1.5, 1.5)
            
        elif self.underMouse():
            bg_color = theme_manager.get_qcolor('bg_hover')
            icon_color = theme_manager.get_qcolor('text_primary')
            
            # Semantic Hover Colors
            if self.icon_type in ["add", "plus", "media_play"]: 
                icon_color = theme_manager.get_qcolor('success')
            elif self.icon_type in ["save", "cube_front", "cube_side", "code"]: 
                icon_color = accent
            elif self.icon_type in ["minus", "trash", "media_rec"]: 
                icon_color = theme_manager.get_qcolor('danger')
            elif self.icon_type == "debug":
                icon_color = theme_manager.get_qcolor('warning')

        # Background
        if bg_color != Qt.GlobalColor.transparent:
            painter.setBrush(bg_color)
            painter.setPen(Qt.PenStyle.NoPen)
            rect_x = 4 if (is_active and self.width() > 50) else 0
            painter.drawRoundedRect(rect_x, 2, self.width()-rect_x-2, self.height()-4, 6, 6)

        # Pen Setup
        pen = QPen(icon_color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = self.width() / 2, self.height() / 2
        
        # Dispatch Table
        draw_methods = {
            "home": self._draw_home,
            "engineer": self._draw_chip,
            "sequencer": self._draw_film,
            "docs": self._draw_book,
            "ik": self._draw_arm,
            "settings": self._draw_sliders,
            "debug": self._draw_ladybug,
            "bolt": self._draw_bolt,
            "code": self._draw_code,  # <--- Ensure this is here
            
            "save": self._draw_floppy,
            "open": self._draw_folder,
            "add": self._draw_plus,
            "refresh": self._draw_refresh,
            "trash": self._draw_trash,
            
            "plus": self._draw_plus,
            "minus": self._draw_minus,
            "cube_front": self._draw_cube_front,
            "cube_side": self._draw_cube_side,
            
            "media_rec": self._draw_media_rec,
            "media_play": self._draw_media_play,
            "media_stop": self._draw_media_stop,
        }
        
        if self.icon_type in draw_methods:
            draw_methods[self.icon_type](painter, cx, cy)

    # =========================================================
    # VECTOR DRAWING PRIMITIVES
    # =========================================================

    def _draw_code(self, p, cx, cy):
        # Draws </>
        # <
        p.drawLine(int(cx - 9), int(cy - 4), int(cx - 14), int(cy))
        p.drawLine(int(cx - 14), int(cy), int(cx - 9), int(cy + 4))
        # >
        p.drawLine(int(cx + 9), int(cy - 4), int(cx + 14), int(cy))
        p.drawLine(int(cx + 14), int(cy), int(cx + 9), int(cy + 4))
        # /
        p.drawLine(int(cx + 4), int(cy - 8), int(cx - 4), int(cy + 8))

    def _draw_home(self, p, cx, cy):
        path = QPainterPath()
        path.moveTo(cx, cy - 8); path.lineTo(cx + 9, cy); path.lineTo(cx + 9, cy + 9)
        path.lineTo(cx - 9, cy + 9); path.lineTo(cx - 9, cy); path.closeSubpath()
        p.drawPath(path)
        p.drawLine(int(cx - 9), int(cy), int(cx), int(cy - 8))
        p.drawLine(int(cx), int(cy - 8), int(cx + 9), int(cy))

    def _draw_chip(self, p, cx, cy):
        p.drawRoundedRect(int(cx - 9), int(cy - 10), 18, 20, 2, 2)
        for i in range(3):
            y_off = (i * 6) - 6
            p.drawLine(int(cx - 13), int(cy + y_off), int(cx - 9), int(cy + y_off)) 
            p.drawLine(int(cx + 9), int(cy + y_off), int(cx + 13), int(cy + y_off))

    def _draw_film(self, p, cx, cy):
        p.drawRoundedRect(int(cx - 10), int(cy - 8), 20, 16, 2, 2)
        p.drawLine(int(cx - 10), int(cy - 3), int(cx + 10), int(cy - 3))
        p.drawLine(int(cx - 10), int(cy + 3), int(cx + 10), int(cy + 3))

    def _draw_book(self, p, cx, cy):
        path = QPainterPath()
        path.moveTo(cx, cy - 8); path.lineTo(cx, cy + 8)
        path.moveTo(cx, cy - 8); path.quadTo(cx - 5, cy - 10, cx - 10, cy - 8); path.lineTo(cx - 10, cy + 8); path.quadTo(cx - 5, cy + 6, cx, cy + 8)
        path.moveTo(cx, cy - 8); path.quadTo(cx + 5, cy - 10, cx + 10, cy - 8); path.lineTo(cx + 10, cy + 8); path.quadTo(cx + 5, cy + 6, cx, cy + 8)
        p.drawPath(path)

    def _draw_arm(self, p, cx, cy):
        p.drawEllipse(QPointF(cx - 6, cy + 6), 2, 2)
        p.drawEllipse(QPointF(cx + 6, cy - 6), 2, 2)
        p.drawLine(int(cx-6), int(cy+6), int(cx), int(cy))
        p.drawLine(int(cx), int(cy), int(cx+6), int(cy-6))

    def _draw_sliders(self, p, cx, cy):
        p.drawLine(int(cx - 8), int(cy - 5), int(cx + 8), int(cy - 5))
        p.drawLine(int(cx - 8), int(cy + 5), int(cx + 8), int(cy + 5))
        p.drawEllipse(QPointF(cx - 3, cy - 5), 2, 2)
        p.drawEllipse(QPointF(cx + 3, cy + 5), 2, 2)

    def _draw_ladybug(self, p, cx, cy):
        p.drawEllipse(QPointF(cx, cy + 1), 6, 8)
        p.drawLine(int(cx), int(cy-7), int(cx), int(cy+9))
        p.drawPoint(int(cx-3), int(cy+3)); p.drawPoint(int(cx+3), int(cy-1))

    def _draw_bolt(self, p, cx, cy):
        path = QPainterPath()
        path.moveTo(cx - 2, cy - 10); path.lineTo(cx + 6, cy - 10); path.lineTo(cx - 1, cy)
        path.lineTo(cx + 5, cy); path.lineTo(cx - 6, cy + 12); path.lineTo(cx - 2, cy + 2); path.lineTo(cx - 8, cy + 2); path.closeSubpath()
        p.drawPath(path)

    def _draw_floppy(self, p, cx, cy):
        p.drawRoundedRect(int(cx - 7), int(cy - 7), 14, 14, 1, 1)
        p.drawRect(int(cx - 3), int(cy - 7), 6, 4) 
        p.drawRect(int(cx - 5), int(cy + 2), 10, 5) 

    def _draw_folder(self, p, cx, cy):
        path = QPainterPath()
        path.moveTo(cx - 8, cy - 6); path.lineTo(cx - 8, cy + 6); path.lineTo(cx + 8, cy + 6)
        path.lineTo(cx + 8, cy - 4); path.lineTo(cx, cy - 4); path.lineTo(cx - 2, cy - 6); path.closeSubpath()
        p.drawPath(path)

    def _draw_plus(self, p, cx, cy):
        p.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))
        p.drawLine(int(cx), int(cy - 5), int(cx), int(cy + 5))

    def _draw_minus(self, p, cx, cy):
        p.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))

    def _draw_refresh(self, p, cx, cy):
        path = QPainterPath()
        path.moveTo(cx - 5, cy); path.arcTo(cx - 5, cy - 5, 10, 10, 180, -135); p.drawPath(path)
        p.drawLine(int(cx + 3), int(cy - 6), int(cx + 5), int(cy - 3)); p.drawLine(int(cx + 3), int(cy - 6), int(cx + 0), int(cy - 6))
        path2 = QPainterPath()
        path2.moveTo(cx + 5, cy); path2.arcTo(cx - 5, cy - 5, 10, 10, 0, -135); p.drawPath(path2)
        p.drawLine(int(cx - 3), int(cy + 6), int(cx - 5), int(cy + 3)); p.drawLine(int(cx - 3), int(cy + 6), int(cx - 0), int(cy + 6))

    def _draw_trash(self, p, cx, cy):
        p.drawLine(int(cx - 7), int(cy - 6), int(cx + 7), int(cy - 6))
        p.drawLine(int(cx - 2), int(cy - 6), int(cx - 2), int(cy - 8)); p.drawLine(int(cx + 2), int(cy - 6), int(cx + 2), int(cy - 8))
        p.drawLine(int(cx - 5), int(cy - 6), int(cx - 4), int(cy + 7)); p.drawLine(int(cx + 5), int(cy - 6), int(cx + 4), int(cy + 7))
        p.drawLine(int(cx - 4), int(cy + 7), int(cx + 4), int(cy + 7)); p.drawLine(int(cx), int(cy - 3), int(cx), int(cy + 4))

    def _draw_cube_front(self, p, cx, cy):
        p.drawRoundedRect(int(cx - 6), int(cy - 6), 12, 12, 2, 2); p.drawPoint(int(cx), int(cy))

    def _draw_cube_side(self, p, cx, cy):
        p.drawRoundedRect(int(cx - 4), int(cy - 7), 8, 14, 2, 2); p.drawLine(int(cx + 6), int(cy), int(cx + 8), int(cy))

    def _draw_media_rec(self, p, cx, cy):
        p.setBrush(p.pen().color()); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPointF(cx, cy), 6, 6)

    def _draw_media_play(self, p, cx, cy):
        p.setBrush(p.pen().color()); p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath(); path.moveTo(cx - 4, cy - 7); path.lineTo(cx - 4, cy + 7); path.lineTo(cx + 8, cy); path.closeSubpath(); p.drawPath(path)

    def _draw_media_stop(self, p, cx, cy):
        p.setBrush(p.pen().color()); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(int(cx - 6), int(cy - 6), 12, 12, 2, 2)