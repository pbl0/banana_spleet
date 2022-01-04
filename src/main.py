import sys
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileDialog,
    QTableWidgetItem, QPushButton, QHeaderView)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from spleeter.separator import Separator


class Worker(QObject):
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)

    def __init__(self, input_arr, output_path, parts_to_separate):
        self.input_arr = input_arr
        self.output_path = output_path
        self.parts_to_separate = parts_to_separate

        super().__init__()

    def run(self):
        """Long-running task."""
        count = 0
        for i, item in enumerate(self.input_arr):
            if (item[1] != 'Finished'):
                separator = Separator(
                    f'spleeter:{self.parts_to_separate}stems')
                separator.separate_to_file(
                    item[0],
                    self.output_path if self.output_path != '' else'output'
                )
                item[1] = 'Finished'
                count += 1
                self.progress.emit(count)
        self.finished.emit(count)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("src/ui/gui_app.ui", self)
        self.parts_to_separate = 0
        self.input_path = []
        self.output_path = ''
        self.thread = {}
        self.connect_buttons()
        self.setTableHeaderBehaviour()
        self.enable_button(self.spleet_button, False)
        self.setWindowIcon(QIcon('src/icon/logo.png'))
        self.setWindowTitle('Banana Spleet')

    def connect_buttons(self):
        """ Connect buttons with events
        """
        self.browse_button.clicked.connect(self.browse_clic)
        self.save_button.clicked.connect(self.save_browse_clic)
        self.button2.clicked.connect(lambda: self.parts(2))
        self.button4.clicked.connect(lambda: self.parts(4))
        self.button5.clicked.connect(lambda: self.parts(5))
        self.spleet_button.clicked.connect(self.spleet)

    def setTableHeaderBehaviour(self):
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def populate_table(self):
        self.tableWidget.setRowCount(0)
        for i, item in enumerate(self.input_path, 0):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(
                i, 0, QTableWidgetItem(item[0][item[0].rfind('/') + 1:])
            )
            self.tableWidget.setItem(
                i, 1, QTableWidgetItem(item[1])
            )
            del_btn = QPushButton(self.tableWidget)
            del_btn.setIcon(QIcon('src/icon/edit-delete.png'))
            del_btn.setGeometry(32, 32, 0, 0)
            del_btn.clicked.connect(lambda: self.del_row(i))
            self.tableWidget.setCellWidget(i, 2, del_btn)

    def browse_clic(self):
        """File browse button click event (input)
        """
        path = QFileDialog.getOpenFileNames(
            self, 'Open a song file', '',
            '.mp3 (*.mp3);; .wav (*.wav);; All files(*.*)')
        if path != ([], ''):
            # .replace('file:///', '')
            for item in path[0]:
                self.input_path.append([item, 'Pending'])
            self.populate_table()
            self.enable_button(self.spleet_button, self.can_be_enabled())

    def save_browse_clic(self):
        """File browse button click event (output)
        """
        path = QFileDialog.getExistingDirectory(
            self, 'Open folder', options=QFileDialog.ShowDirsOnly)
        if path != '':
            self.output_path = path.replace('file:///', '')
            self.save_input.setPlainText(self.output_path)
            self.enable_button(self.spleet_button, self.can_be_enabled())

    def del_row(self, index):
        self.input_path.pop(index)
        self.populate_table()

    def parts(self, parts):
        """Buttons (2,4,5) click to set parts_to_separate value

        Args:
            parts (int): parts to separate (2,4,5)
        """
        self.parts_to_separate = parts
        self.button2.setEnabled(True)
        self.button4.setEnabled(True)
        self.button5.setEnabled(True)
        # Accesing class property with string name
        getattr(self, f'button{self.parts_to_separate}').setEnabled(False)
        self.enable_button(self.spleet_button, self.can_be_enabled())

    def spleet(self):
        """Spleet button event, will launch spleeter separator
        """
        if self.input_path != []:
            self.runLongTask()

    def enable_button(self, button, enable):
        """Enable or disable button

        Args:
            button (QPushButton): button
            enable (boolean): enable or disable
        """
        button.setEnabled(enable)

    def can_be_enabled(self):
        """Check if spleet button can be enabled.

        Returns:
            boolean: True if both self.input_path and self.parts_to_separate
            have been changed.
        """
        return self.input_path != [] and self.parts_to_separate != 0

    def runLongTask(self):
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker(
            self.input_path,
            self.output_path,
            self.parts_to_separate
        )
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.finishedProgress)
        self.worker.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        self.spleet_button.setEnabled(False)
        self.spleet_button.setText('Wait')
        self.progress_label.setText('Progress...')
        self.thread.start()

        # Final resets
        self.thread.finished.connect(
            lambda: self.spleet_button.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.spleet_button.setText('Spleet')
        )

    def reportProgress(self, n):
        self.progress_label.setText(f"Progress: {n} files spleeted...")
        self.populate_table()

    def finishedProgress(self, n):
        self.progress_label.setText(f"Finished: {n} files spleeted.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    GUI = App()
    GUI.show()
    sys.exit(app.exec())
