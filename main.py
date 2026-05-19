import sys
import traceback
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    try:
        from src.presentation.ui_assets import app_logo_icon
        from src.presentation.main_window import MainWindow
        app.setWindowIcon(app_logo_icon(32))
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"\n--- EXCEPTION ---")
        traceback.print_exc()
        input("Press Enter to close...")

if __name__ == "__main__":
    main()