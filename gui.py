import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QTextEdit, 
                             QRadioButton, QLabel, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from pdf_parser import pdf_to_images
from llm_processor import process_images_to_json, process_text_to_json
from ocr_processor import OCRProcessor

class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, pdf_path, mode):
        super().__init__()
        self.pdf_path = pdf_path
        self.mode = mode

    def run(self):
        try:
            temp_dir = "./temp_images"
            self.log.emit(f"1. PDF 이미지 변환 중... ({self.pdf_path})")
            image_paths = pdf_to_images(self.pdf_path, output_dir=temp_dir, dpi=300)
            self.log.emit(f"   - {len(image_paths)} 페이지 변환 완료.")

            if self.mode == "AI (Gemini Vision)":
                self.log.emit("2. Gemini Multimodal 분석 중 (이 작업은 수십 초가 소요될 수 있습니다)...")
                structured_data = process_images_to_json(image_paths)
            else:
                self.log.emit("2. EasyOCR 텍스트 추출 중...")
                ocr = OCRProcessor()
                raw_text = ocr.extract_text_from_images(image_paths)
                self.log.emit("3. 추출된 텍스트 Gemini로 구조화 중...")
                structured_data = process_text_to_json(raw_text)

            self.finished.emit(structured_data)
        except Exception as e:
            self.error.emit(str(e))

class ExamParserGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Nova.ai Exam Parser (Phase 1)")
        self.setGeometry(100, 100, 600, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # File Selection
        file_layout = QHBoxLayout()
        self.btn_open = QPushButton("시험지 PDF 불러오기")
        self.btn_open.clicked.connect(self.openFileDialog)
        self.lbl_filename = QLabel("선택된 파일 없음")
        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.lbl_filename)
        layout.addLayout(file_layout)

        # Mode Selection
        mode_group = QGroupBox("분석 모드 선택")
        mode_layout = QHBoxLayout()
        self.radio_ai = QRadioButton("AI (Gemini Vision)")
        self.radio_ocr = QRadioButton("OCR + AI (Hybrid)")
        self.radio_ai.setChecked(True)
        mode_layout.addWidget(self.radio_ai)
        mode_layout.addWidget(self.radio_ocr)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Run Button
        self.btn_run = QPushButton("파싱 시작")
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        self.btn_run.clicked.connect(self.runParsing)
        layout.addWidget(self.btn_run)

        # Log Display
        layout.addWidget(QLabel("진행 상태:"))
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log)

        self.selected_pdf = None

    def openFileDialog(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "PDF 파일 선택", "", "PDF Files (*.pdf)", options=options)
        if file_name:
            self.selected_pdf = file_name
            self.lbl_filename.setText(os.path.basename(file_name))

    def runParsing(self):
        if not self.selected_pdf:
            QMessageBox.warning(self, "오류", "먼저 PDF 파일을 선택해 주세요.")
            return

        mode = "AI (Gemini Vision)" if self.radio_ai.isChecked() else "OCR + AI (Hybrid)"
        self.btn_run.setEnabled(False)
        self.txt_log.append(f"\n--- 파싱 시작: {mode} ---")

        self.thread = WorkerThread(self.selected_pdf, mode)
        self.thread.log.connect(self.updateLog)
        self.thread.finished.connect(self.onFinished)
        self.thread.error.connect(self.onError)
        self.thread.start()

    def updateLog(self, msg):
        self.txt_log.append(msg)

    def onFinished(self, data):
        import json
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.txt_log.append("\n✅ 파싱 완료! result.json 파일이 생성되었습니다.")
        self.btn_run.setEnabled(True)
        QMessageBox.information(self, "완료", "파싱이 성공적으로 완료되었습니다.")

    def onError(self, err_msg):
        self.txt_log.append(f"\n❌ 오류 발생: {err_msg}")
        self.btn_run.setEnabled(True)
        QMessageBox.critical(self, "오류", f"작업 중 오류가 발생했습니다:\n{err_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ExamParserGUI()
    ex.show()
    sys.exit(app.exec_())
