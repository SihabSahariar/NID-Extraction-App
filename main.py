import sys
import cv2
import numpy as np
import pytesseract
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QFileDialog, QSpacerItem, QSizePolicy, QProgressBar, QCheckBox, QMessageBox, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QImage,QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class RecognitionThread(QThread):
    update_progress = pyqtSignal(int)  # Signal to update the progress bar
    recognition_done = pyqtSignal(str, QImage, np.ndarray)  # Signal when recognition is done

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        # Load image using OpenCV
        img = cv2.imread(self.image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.update_progress.emit(20)  # Update progress bar

        # Use pytesseract to detect the text from the image for NID recognition
        nid_number = self.extract_nid_number(gray, img)
        self.update_progress.emit(50)  # Update progress bar

        # Use OpenCV's face detection
        face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_img = img[y:y+h, x:x+w]
            face_qimage = self.convert_cv_qt(face_img)

            self.update_progress.emit(100)  # Update progress bar
            # Emit recognition done signal
            self.recognition_done.emit(nid_number,face_qimage, face_img)
        else:
            face_qimage = None
            face_img = None
        


    def convert_cv_qt(self, cv_img):
        """Convert from an OpenCV image to QImage"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return convert_to_qt_format

    def extract_nid_number(self, gray,im2):
        """Extract the NID number from the given image using pytesseract."""

        # Performing OTSU threshold
        ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        # Specify structure shape and kernel size.
        # Kernel size increases or decreases the area
        # of the rectangle to be detected.
        # A smaller value like (10, 10) will detect
        # each word instead of a sentence.
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18, 18))

        # Appplying dilation on the threshold image
        dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

        # Finding contours
        contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_NONE)

        # Creating a copy of image
        # im2 = img.copy()

        # Looping through the identified contours
        # Then rectangular part is cropped and passed on
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            # Drawing a rectangle on copied image
            rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # cv2.imshow("frame",rect)
            # Cropping the text block for giving input to OCR
            cropped = im2[y:y + h, x:x + w]
            # cv2.imshow("frame1",cropped)
            # Apply OCR on the cropped image
            text = pytesseract.image_to_string(cropped)

            text = text.strip()

            # print(text)

            for lines in text.split("\n"):
                main_text = lines.strip()
                lower_text = main_text.lower()
                possible_int = ''.join(c for c in lower_text if c.isdigit())
                # print(main_text)
                if len(possible_int) == 10 or len(possible_int) == 13 or len(possible_int) == 15 or len(possible_int) == 17:
                    # Print the possible NID number
                    print("NID",possible_int)
                    return possible_int
        
        return "Not Recognized"


class NIDRecognitionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NID Extraction App")
        self.setGeometry(200, 100, 800, 600)

        # Set app icon
        self.setWindowIcon(QIcon("icons8_Identification_Card_32.png"))

        # Initialize widgets
        self.left_image_label = QLabel("Select an Image")
        self.left_image_label.setStyleSheet("background-color:rgb(2,50,100);")
        self.right_face_label = QLabel("Detected Face",alignment=Qt.AlignCenter)
        self.right_face_label.setStyleSheet("background-color:rgb(2,50,80);border: 1px solid black;color:white;")
        self.right_face_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.right_nid_label = QLabel("NID Number: Not Recognized")
        self.right_nid_label.setStyleSheet("background-color:rgb(80,50,80);border: 1px solid black;color:white; font-size: 20; font-weight: bold;")

        self.start_button = QPushButton("Start")
        self.reset_button = QPushButton("Reset")
        self.save_checkbox = QCheckBox("Save Data")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        self.start_button.setEnabled(False)

        # Set alignment for labels
        self.left_image_label.setAlignment(Qt.AlignCenter)
        self.right_face_label.setAlignment(Qt.AlignCenter)
        self.right_nid_label.setAlignment(Qt.AlignCenter)

        # Set default minimum size for image labels
        self.left_image_label.setMinimumSize(300, 400)
        self.right_face_label.setMinimumSize(150, 150)
        self.right_face_label.setMaximumSize(150, 150)
        self.right_nid_label.setMinimumSize(200, 50)

        # Create layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.left_image_label)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.right_face_label, alignment=Qt.AlignCenter)
        right_layout.addWidget(self.right_nid_label)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)


        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)


        # Toggle dark theme checkbox
        self.theme_checkbox = QCheckBox("Dark Theme")
        self.theme_checkbox.stateChanged.connect(self.apply_dark_theme)
        self.theme_checkbox.setCheckState(Qt.Checked)

        self.about_action = QPushButton("About")
        self.about_action.clicked.connect(self.about)


        button_layout = QVBoxLayout()
        button_layout.addSpacerItem(spacer)
        button_layout.addWidget(self.save_checkbox)
        button_layout.addWidget(self.theme_checkbox)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addSpacerItem(spacer)
        button_layout.addWidget(self.progress_bar)
        button_layout.addSpacerItem(spacer)
        button_layout.addWidget(self.about_action)

        
        
        right_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connect signals
        self.start_button.clicked.connect(self.start_recognition)
        self.reset_button.clicked.connect(self.reset_application)
        self.create_menu()

        self.image_path = None
        self.thread = None

    def create_menu(self):
        open_action = QPushButton("Open Image", self)
        open_action.clicked.connect(self.open_image)
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setContentsMargins(10, 10, 10, 10)
        
        self.menu_layout.addWidget(open_action)
        
        self.setMenuWidget(open_action)

    def about(self):
        QMessageBox.about(self, "About", "Developed by: Sihab Sahariar\nEmail: sihabsahariarcse@gmail.com")


    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select an Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_name:
            self.image_path = file_name
            pixmap = QPixmap(self.image_path)
            self.left_image_label.setPixmap(pixmap.scaled(self.left_image_label.size(), Qt.KeepAspectRatio))
            self.start_button.setEnabled(True)

    def start_recognition(self):
        if not self.image_path:
            return

        # Start the recognition in a separate thread
        self.thread = RecognitionThread(self.image_path)
        self.thread.update_progress.connect(self.update_progress_bar)
        self.thread.recognition_done.connect(self.on_recognition_done)
        
        self.progress_bar.setVisible(True)
        self.thread.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def on_recognition_done(self, nid_number, face_qimage, face_img):
        self.right_nid_label.setText(f"NID Number: {nid_number}")
        if face_qimage:
            self.right_face_label.setPixmap(QPixmap.fromImage(face_qimage))
            if self.save_checkbox.isChecked() and nid_number != "Not Recognized":
                face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                self.save_detected_face(nid_number, face_img_rgb)
        else:
            self.right_face_label.setText("No Face Detected")

        # Hide progress bar when done
        self.progress_bar.setVisible(False)

    def save_detected_face(self, nid_number, face_img_rgb):
        try:
            save_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save Image")
            if save_path:
                file_path = f"{save_path}/{nid_number}.jpg"
                cv2.imwrite(file_path, face_img_rgb)
                QMessageBox.information(self, "Saved", f"Face image saved at: {file_path}")
        except Exception as e:
            print(f"Error saving image: {e}")
            QMessageBox.warning(self, "Error", "Error saving image")

    def reset_application(self):
        self.left_image_label.setText("Select an Image")
        self.right_face_label.setText("Detected Face")
        self.right_nid_label.setText("NID Number: Not Recognized")
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.image_path = None


    def apply_dark_theme(self):
        """Toggle between light and dark theme"""
        dark_theme = """
            QMainWindow {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #4F4F4F;
                color: #FFFFFF;
            }
            QProgressBar {
                background-color: #4F4F4F;
                color: #FFFFFF;
                border: 1px solid #1A1A1A;
                text-align: center;
            }
            QCheckBox {
                color: #FFFFFF;
            }

            QMessageBox {
                background-color: #2E2E2E; color: #FFFFFF;
                }
        """
        light_theme = """
            QMainWindow {
                background-color: #F0F0F0;
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QPushButton {
                background-color: #E0E0E0;
                color: #000000;
            }
            QProgressBar {
                background-color: #E0E0E0;
                color: #000000;
                border: 1px solid #C0C0C0;
                text-align: center;
            }
            QCheckBox {
                color: #000000;
            }

        """
        
        current_theme = self.styleSheet()
        if current_theme == dark_theme:
            self.setStyleSheet(light_theme)
        else:
            self.setStyleSheet(dark_theme)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NIDRecognitionApp()
    window.show()
    sys.exit(app.exec_())
