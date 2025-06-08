# QR Code Reader Desktop Application

## English

A desktop application for easily reading QR codes from your screen.

### Features
- Select any area on your screen to read a QR code
- Modern and user-friendly GUI
- QR code detection and decoding
- Display and copy the decoded result
- Open decoded URLs in your browser with a click

### Requirements
- Windows 10/11
- Python 3.8 or later (for source execution)

### How to Use (EXE version)
1. Go to the `dist` folder and double-click `QRCodeReader.exe` to launch the app.
2. (Optional) Right-click `QRCodeReader.exe` and select "Create shortcut" to place a shortcut on your Desktop or pin it to the taskbar for quick access.
3. Click the "Capture Screen" button, select the area containing a QR code, and the result will be displayed.
4. If the result is a URL, you can click it to open in your browser.

### How to Use (Python source version)
1. Clone or download this repository.
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python src/main.py
   ```

---

# QRコードリーダー デスクトップアプリケーション

画面上のQRコードを簡単に読み取ることができるデスクトップアプリケーションです。

## 機能
- 画面上の任意の領域を選択してQRコードを読み取り
- モダンで使いやすいGUIインターフェース
- QRコードの検出とデコード
- 読み取った結果の表示とコピー機能
- 結果がURLの場合はクリックでブラウザを開く

## 必要条件
- Windows 10/11
- Python 3.8以上（ソースから実行する場合）

## EXE版の使い方
1. `dist`フォルダ内の `QRCodeReader.exe` をダブルクリックして起動します。
2. 必要に応じて、`QRCodeReader.exe` を右クリックし「ショートカットの作成」を選び、デスクトップやタスクバーに配置すると便利です。
3. 「画面をキャプチャ」ボタンをクリックし、QRコードを含む領域をドラッグして選択します。
4. QRコードが自動的に検出され、結果が表示されます。URLの場合はクリックでブラウザが開きます。

## ソース版の使い方
1. リポジトリをクローンまたはダウンロードします。
2. 必要なパッケージをインストールします：
   ```bash
   pip install -r requirements.txt
   ```
3. アプリケーションを起動します：
   ```bash
   python src/main.py
   ```
