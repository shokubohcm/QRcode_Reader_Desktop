import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QWidget, QLabel, QTextEdit)
from PySide6.QtCore import Qt, QRect, Signal, QBuffer, QByteArray
from PySide6.QtGui import QScreen, QPixmap, QPainter, QPen, QColor
import pyautogui
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np
import io

class QRCodeReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.screenshot = None
        self.selection_rect = None

    def initUI(self):
        self.setWindowTitle('QRコードリーダー')
        self.setGeometry(100, 100, 600, 400)

        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # キャプチャボタン
        self.capture_btn = QPushButton('画面をキャプチャ', self)
        self.capture_btn.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_btn)

        # 結果表示用のテキストエリア
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText('QRコードの読み取り結果がここに表示されます')
        layout.addWidget(self.result_text)

        # ステータスラベル
        self.status_label = QLabel('準備完了')
        layout.addWidget(self.status_label)

    def start_capture(self):
        self.hide()  # ウィンドウを一時的に非表示
        self.status_label.setText('画面をキャプチャ中...')
        QApplication.processEvents()  # UIの更新を確実に

        # スクリーンショットを取得
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
        # キャプチャウィンドウを表示
        self.capture_window = CaptureWindow(self.screenshot)
        self.capture_window.capture_completed.connect(self.process_capture)
        self.capture_window.show()

    def process_capture(self, rect):
        if rect:
            # 選択された領域の画像を取得
            cropped = self.screenshot.copy(rect)
            # QPixmap → バイト配列（PNG形式）→ PIL.Image
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            cropped.save(buffer, 'PNG')
            pil_image = Image.open(io.BytesIO(byte_array.data()))
            # QRコードをデコード
            decoded_objects = decode(pil_image)
            
            if decoded_objects:
                # QRコードが見つかった場合
                result = decoded_objects[0].data.decode('utf-8')
                self.result_text.setText(result)
                self.status_label.setText('QRコードを検出しました')
            else:
                self.result_text.clear()
                self.status_label.setText('QRコードが見つかりませんでした')
        
        self.show()  # メインウィンドウを再表示

class CaptureWindow(QWidget):
    capture_completed = Signal(QRect)

    def __init__(self, screenshot):
        super().__init__()
        self.screenshot = screenshot
        self.initUI()
        self.start_pos = None
        self.end_pos = None
        self.is_capturing = False
        # スクリーンショットを背景として設定
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay = QPixmap(self.size())
        self.overlay.fill(Qt.transparent)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        # 背景を完全に透明に
        self.setStyleSheet("background-color: transparent;")
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        # スクリーンショットを背景として描画
        painter.drawPixmap(0, 0, self.screenshot)
        
        if self.is_capturing and self.start_pos and self.end_pos:
            # 選択範囲の外側を半透明の黒で覆う
            overlay = QPixmap(self.size())
            overlay.fill(Qt.transparent)
            overlay_painter = QPainter(overlay)
            overlay_painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
            # 選択範囲を透明に
            rect = QRect(self.start_pos, self.end_pos)
            overlay_painter.setCompositionMode(QPainter.CompositionMode_Clear)
            overlay_painter.fillRect(rect, Qt.transparent)
            overlay_painter.end()
            
            painter.drawPixmap(0, 0, overlay)
            
            # 選択範囲の枠線を描画
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.is_capturing = True

    def mouseMoveEvent(self, event):
        if self.is_capturing:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_capturing:
            self.is_capturing = False
            if self.start_pos and self.end_pos:
                rect = QRect(self.start_pos, self.end_pos)
                self.capture_completed.emit(rect)
            self.close()

def main():
    app = QApplication(sys.argv)
    ex = QRCodeReader()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 