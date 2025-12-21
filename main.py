"""
PgSSR v2.0 - PostgreSQL Statistics Statements Reader

Modern desktop application for monitoring PostgreSQL query performance.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from loguru import logger

# Import app components
from src.config import app_config
from src.views import MainWindow


def setup_application() -> QApplication:
    """
    Setup Qt application with Material Design theme.

    Returns:
        Configured QApplication instance
    """
    # Enable High DPI scaling (Qt 6 handles this automatically, these attributes are deprecated)
    # QApplication.setHighDpiScaleFactorRoundingPolicy(
    #     Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    # )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(app_config.app_name)
    app.setOrganizationName(app_config.app_author)
    app.setApplicationVersion(app_config.app_version)

    # Set application icon
    icon_path = app_config.icons_dir / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Apply Material Design theme
    apply_material_theme(app)

    return app


def apply_material_theme(app: QApplication):
    """
    Apply Material Design 3 theme to application.

    Args:
        app: QApplication instance
    """
    try:
        from qt_material import apply_stylesheet, list_themes

        # Apply dark theme (Material Design 3)
        theme = 'dark_blue.xml'  # Material Design Dark Blue
        apply_stylesheet(app, theme=theme)

        # Custom stylesheet overrides
        custom_css = """
        /* Material Design 3 customizations */

        QMainWindow {
            background-color: #1e1e1e;
        }

        QToolBar {
            background-color: #2d2d2d;
            border: none;
            spacing: 8px;
            padding: 8px;
        }

        QPushButton {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
        }

        QPushButton#primaryButton {
            background-color: #1976D2;
            color: white;
        }

        QPushButton#primaryButton:hover {
            background-color: #1565C0;
        }

        QLineEdit, QSpinBox, QComboBox {
            padding: 8px;
            border-radius: 4px;
            border: 1px solid #424242;
        }

        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
            border: 2px solid #1976D2;
        }

        QTableWidget {
            gridline-color: #424242;
            border: 1px solid #424242;
            border-radius: 4px;
        }

        QTableWidget::item:selected {
            background-color: #1976D2;
            color: white;
        }

        QHeaderView::section {
            background-color: #2d2d2d;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #1976D2;
            font-weight: 600;
        }

        QTextEdit {
            border: 1px solid #424242;
            border-radius: 4px;
            padding: 8px;
            background-color: #252525;
        }

        QProgressBar {
            border: none;
            border-radius: 2px;
            background-color: #424242;
            height: 4px;
        }

        QProgressBar::chunk {
            background-color: #1976D2;
            border-radius: 2px;
        }

        QStatusBar {
            background-color: #2d2d2d;
            border-top: 1px solid #424242;
        }

        QLabel#dialogHeader {
            color: #1976D2;
            font-size: 18px;
            font-weight: bold;
        }

        /* Scrollbar styling */
        QScrollBar:vertical {
            border: none;
            background-color: #2d2d2d;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #424242;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #1976D2;
        }

        QScrollBar:horizontal {
            border: none;
            background-color: #2d2d2d;
            height: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:horizontal {
            background-color: #424242;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background-color: #1976D2;
        }
        """

        # Apply custom CSS
        app.setStyleSheet(app.styleSheet() + custom_css)

        logger.success("Material Design theme applied successfully")

    except ImportError:
        logger.warning("qt-material not installed, using default theme")

        # Fallback: basic dark theme
        app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3b3b3b;
            }

            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #1976d2;
            }

            QLineEdit, QComboBox, QSpinBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3b3b3b;
                padding: 6px;
                border-radius: 4px;
            }
        """)


def main():
    """Main application entry point."""
    try:
        # Setup application
        app = setup_application()

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.success(f"{app_config.app_name} v{app_config.app_version} started successfully")

        # Run application
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Application crash: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
