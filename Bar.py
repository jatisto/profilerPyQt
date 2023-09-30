from PySide2.QtCore import Qt, QPoint
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton


class Bar(QWidget):
    def __init__(self, parent, title):
        super(Bar, self).__init__()
        self.parent = parent
        self.title = title

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 10, 0)
        self.title = QLabel(self.title)

        btn_size = 16

        self.btn_close = QPushButton()
        self.btn_close.setStyleSheet("""
            border-radius: 7px;
            background-color: rgb(255, 0, 4);
        """)
        self.btn_close.setText("")
        self.btn_close.clicked.connect(self.btn_close_clicked)
        self.btn_close.setFixedSize(btn_size, btn_size)

        self.btn_max = QPushButton()
        self.btn_max.setStyleSheet("""
            border-radius: 7px;
            background-color: rgb(0, 255, 0);
        """)
        self.btn_max.setText("")
        self.btn_max.clicked.connect(self.btn_max_clicked)
        self.btn_max.setFixedSize(btn_size, btn_size)

        self.btn_min = QPushButton()
        self.btn_min.setStyleSheet("""
            background-color: rgb(255, 183, 0);
            border-radius: 7px;
        """)
        self.btn_min.clicked.connect(self.btn_min_clicked)
        self.btn_min.setFixedSize(btn_size, btn_size)

        self.title.setFixedHeight(32)
        self.title.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.btn_min)
        self.layout.addWidget(self.btn_max)
        self.layout.addWidget(self.btn_close)

        self.title.setStyleSheet("""
            background-color: rgb(65, 65, 65);
            color: white;
        """)

        self.start = QPoint(0, 0)
        self.pressing = False

    def resizeEvent(self, QResizeEvent):
        super(Bar, self).resizeEvent(QResizeEvent)
        self.title.setFixedWidth(self.parent.width())

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.end = self.mapToGlobal(event.pos())
            self.movement = self.end - self.start
            self.parent.setGeometry(self.mapToGlobal(self.movement).x(),
                                    self.mapToGlobal(self.movement).y(),
                                    self.parent.width(),
                                    self.parent.height())
            self.start = self.end

    def mouseReleaseEvent(self, QMouseEvent):
        self.pressing = False

    def btn_close_clicked(self):
        self.parent.close()

    def btn_max_clicked(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def btn_min_clicked(self):
        self.parent.showMinimized()

    def maximize_window(self):
        if self.parent.isFullScreen():
            self.parent.showNormal()
        else:
            self.parent.showFullScreen()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.maximize_window()
