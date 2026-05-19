import csv
import os
from PyQt5.QtWidgets import (
    QTextEdit, QMessageBox, QFileDialog, QWidget, QVBoxLayout,
)

from src.core.preferences import AppPreferences
from src.core.design_tokens import DESIGN


class TerminalView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.apply_preferences()

    def apply_preferences(self, prefs: AppPreferences = None):
        prefs = prefs or AppPreferences.load()
        theme = prefs.theme
        if theme == "light":
            bg, fg = "#fafafa", "#1a472a"
        elif theme == "black":
            bg, fg = "#0d0d0d", "#a8a8a8"
        else:
            bg, fg = DESIGN["workspace_bg"], DESIGN["terminal_text"]
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; "
            f"font-family: Consolas, monospace; font-size: {prefs.terminal_font_size}pt; "
            f"border: none;"
        )

    def append_text(self, text: str):
        self.append(text)

    def set_status(self, status: str):
        self.append(f">>> SYSTEM STATUS: {status}")


class TerminalPanel(QWidget):
    """Terminal dock body — title comes from the dock header bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TerminalPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.view = TerminalView()
        layout.addWidget(self.view, stretch=1)

    def apply_preferences(self, prefs: AppPreferences = None):
        self.view.apply_preferences(prefs)

    def append_text(self, text: str):
        self.view.append_text(text)

    def set_status(self, status: str):
        self.view.set_status(status)


class ErrorNotificationWindow:
    @staticmethod
    def show_error(parent, title: str, message: str):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()


class ExportHandler:
    @staticmethod
    def export_results(parent, text: str, energy_result=None):
        prefs = AppPreferences.load()
        fmt = prefs.export_format

        if fmt == "csv" and energy_result is not None:
            ExportHandler._export_csv(parent, energy_result)
        elif fmt == "report" and energy_result is not None:
            ExportHandler._export_report(parent, text, energy_result)
        else:
            ExportHandler._export_txt(parent, text)

    @staticmethod
    def _export_txt(parent, text: str):
        path, _ = QFileDialog.getSaveFileName(
            parent, "Save Results", "", "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            ErrorNotificationWindow.show_error(parent, "Export Error", str(e))

    @staticmethod
    def _export_csv(parent, energy_result):
        path, _ = QFileDialog.getSaveFileName(
            parent, "Save Results", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "power_w", "soc_wh"])
                for row in energy_result.hourly_production:
                    writer.writerow([
                        row["timestamp"], row["power_w"], row["soc"],
                    ])
        except Exception as e:
            ErrorNotificationWindow.show_error(parent, "Export Error", str(e))

    @staticmethod
    def _export_report(parent, text: str, energy_result):
        folder = QFileDialog.getExistingDirectory(parent, "Select Report Folder")
        if not folder:
            return
        try:
            summary_path = os.path.join(folder, "summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(text)
            csv_path = os.path.join(folder, "hourly_data.csv")
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "power_w", "soc_wh"])
                for row in energy_result.hourly_production:
                    writer.writerow([
                        row["timestamp"], row["power_w"], row["soc"],
                    ])
            QMessageBox.information(
                parent, "Export Complete",
                f"Report saved to:\n{folder}\n\n(summary.txt, hourly_data.csv)",
            )
        except Exception as e:
            ErrorNotificationWindow.show_error(parent, "Export Error", str(e))
