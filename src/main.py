import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QWidget, QLabel, QTextEdit)
from PySide6.QtCore import Qt, QRect, Signal, QBuffer, QByteArray, QUrl
from PySide6.QtGui import QScreen, QPixmap, QPainter, QPen, QColor, QClipboard, QDesktopServices
import pyautogui
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pyzbar.pyzbar import decode, ZBarSymbol
import numpy as np
import io
import cv2
import re

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
        self.result_text.setMouseTracking(True)  # マウスイベントを有効化
        self.result_text.mousePressEvent = self.handle_result_click  # クリックイベントをオーバーライド
        layout.addWidget(self.result_text)

        # コピーボタン
        self.copy_btn = QPushButton('結果をコピー', self)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)  # 初期状態は無効
        layout.addWidget(self.copy_btn)

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

    def find_qr_code(self, image):
        """QRコードの位置検出パターンを探して、より正確にQRコードを特定"""
        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 二値化（複数の閾値で試行）
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 輪郭検出
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # QRコードの候補を探す
        qr_candidates = []
        for contour in contours:
            # 輪郭の面積が小さすぎる場合はスキップ
            if cv2.contourArea(contour) < 100:
                continue
                
            # 輪郭を近似
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            
            # 四角形の場合
            if len(approx) == 4:
                # アスペクト比を計算
                rect = cv2.minAreaRect(contour)
                width = rect[1][0]
                height = rect[1][1]
                aspect_ratio = max(width, height) / (min(width, height) + 1e-6)
                
                # QRコードは通常、ほぼ正方形（アスペクト比が1に近い）
                if 0.8 <= aspect_ratio <= 1.2:
                    qr_candidates.append((contour, cv2.contourArea(contour)))
        
        # 面積でソート
        qr_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return qr_candidates[0][0] if qr_candidates else None

    def preprocess_image(self, image):
        """画像の前処理を行い、最適な結果を返す"""
        # 画像の品質を評価する関数
        def evaluate_quality(img):
            # エッジの鮮明さを評価
            edges = cv2.Canny(img, 100, 200)
            edge_score = np.sum(edges) / (img.shape[0] * img.shape[1])
            
            # コントラストを評価
            contrast = np.std(img)
            
            # ノイズを評価（局所的な分散）
            noise = cv2.Laplacian(img, cv2.CV_64F).var()
            
            return edge_score * contrast / (noise + 1e-6)

        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 画像の品質を改善する処理を順番に適用
        best_quality = 0
        best_image = gray.copy()
        
        # 1. ガウシアンブラーでノイズ除去
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        quality = evaluate_quality(blurred)
        if quality > best_quality:
            best_quality = quality
            best_image = blurred

        # 2. アンシャープマスクでエッジ強調
        gaussian = cv2.GaussianBlur(gray, (0, 0), 3)
        unsharp = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        quality = evaluate_quality(unsharp)
        if quality > best_quality:
            best_quality = quality
            best_image = unsharp

        # 3. 適応的二値化
        binary = cv2.adaptiveThreshold(
            best_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        quality = evaluate_quality(binary)
        if quality > best_quality:
            best_quality = quality
            best_image = binary

        return best_image

    def copy_to_clipboard(self):
        """結果をクリップボードにコピー"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_text.toPlainText())
        self.status_label.setText('クリップボードにコピーしました')

    def is_valid_url(self, text):
        """URLかどうかを判定する"""
        # URLのパターン（http://, https://, ftp://で始まる文字列）
        url_pattern = re.compile(
            r'^(https?|ftp)://'  # http://, https://, ftp://
            r'([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+'  # ドメイン
            r'[a-zA-Z]{2,}'  # TLD
            r'(/[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]*)?$'  # パス、クエリ、フラグメント
        )
        return bool(url_pattern.match(text))

    def handle_result_click(self, event):
        """結果テキストがクリックされたときの処理"""
        text = self.result_text.toPlainText()
        if text and self.is_valid_url(text):
            # URLをブラウザで開く
            QDesktopServices.openUrl(QUrl(text))
            self.status_label.setText('ブラウザでURLを開きました')
        else:
            # URLでない場合は通常のクリックイベントを処理
            super().mousePressEvent(event)

    def process_capture(self, rect):
        if rect:
            # 結果をクリア（新しいキャプチャの開始時に必ずクリア）
            self.result_text.clear()
            self.copy_btn.setEnabled(False)  # コピーボタンを無効化
            
            # 選択された領域の画像を取得
            cropped = self.screenshot.copy(rect)
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            cropped.save(buffer, 'PNG')
            pil_image = Image.open(io.BytesIO(byte_array.data()))
            np_image = np.array(pil_image.convert('RGB'))
            
            # QRコードの位置を特定
            qr_contour = self.find_qr_code(np_image)
            
            decoded_result = None  # 結果を保持する変数
            
            if qr_contour is not None:
                # QRコードの領域を取得
                x, y, w, h = cv2.boundingRect(qr_contour)
                # 余白を追加（20%）
                padding = int(max(w, h) * 0.2)
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(np_image.shape[1] - x, w + 2 * padding)
                h = min(np_image.shape[0] - y, h + 2 * padding)
                
                # 領域を切り出し
                qr_region = np_image[y:y+h, x:x+w]
                
                # 画像の前処理
                processed_image = self.preprocess_image(qr_region)
                
                # 回転補正
                rect = cv2.minAreaRect(qr_contour)
                angle = rect[2]
                if angle < -45:
                    angle += 90
                
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated_image = cv2.warpAffine(processed_image, rotation_matrix, 
                                             (w, h), flags=cv2.INTER_CUBIC)
                
                # QRコードの読み取りを試行
                pil_image = Image.fromarray(rotated_image)
                decoded_objects = decode(pil_image, symbols=[ZBarSymbol.QRCODE])
                
                if decoded_objects:
                    decoded_result = decoded_objects[0].data.decode('utf-8')
                else:
                    # 読み取りに失敗した場合、元の画像全体でも試行
                    pil_image = Image.fromarray(np_image)
                    decoded_objects = decode(pil_image, symbols=[ZBarSymbol.QRCODE])
                    if decoded_objects:
                        decoded_result = decoded_objects[0].data.decode('utf-8')
            
            else:
                # QRコードの位置が特定できない場合、元の画像全体で試行
                pil_image = Image.fromarray(np_image)
                decoded_objects = decode(pil_image, symbols=[ZBarSymbol.QRCODE])
                if decoded_objects:
                    decoded_result = decoded_objects[0].data.decode('utf-8')
            
            # 最終的な結果の表示
            if decoded_result:
                self.result_text.setText(decoded_result)
                if self.is_valid_url(decoded_result):
                    self.status_label.setText('QRコードを検出しました（URLをクリックで開けます）')
                else:
                    self.status_label.setText('QRコードを検出しました')
                self.copy_btn.setEnabled(True)  # コピーボタンを有効化
            else:
                self.status_label.setText('QRコードが見つかりませんでした')
                self.copy_btn.setEnabled(False)  # コピーボタンを無効化
        
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