"""QT GUI for Square Pig."""

import sys
from os import path
from time import sleep
from PyQt4 import QtCore, QtGui
from backpig import SquarePig, Playlist


class SquarePigThread(QtCore.QThread):

    """Worker thread."""

    error = QtCore.pyqtSignal(object)

    def __init__(self, files, destination):
        """Initialise thread."""
        QtCore.QThread.__init__(self)
        self.sargasso = SquarePig()
        self.files = files
        self.destination = destination

    def run(self):
        """Run thread."""
        try:
            self.sargasso.copy_to(self.files, self.destination)
        except SquarePig.CopyError as e:
            self.error.emit(e)


class ProgressThread(QtCore.QThread):

    """Progress update thread."""

    progress = QtCore.pyqtSignal(object)
    state = QtCore.pyqtSignal(object)

    def __init__(self, sargasso):
        """Initialise thread."""
        QtCore.QThread.__init__(self)
        self.sargasso = sargasso

    def run(self):
        """Run thread."""
        self.length = -1
        while True:
            state = self.sargasso.get_state()
            self.state.emit(state)
            if state not in ['stopped', 'done']:
                index, self.length = self.sargasso.get_progress()
                self.progress.emit(index)
            else:
                index, self.length = self.sargasso.get_progress()
                self.progress.emit(index)
                self.state.emit(state)
                break
            sleep(0.2)


class MyMainWindow(QtGui.QMainWindow):

    """Main window."""

    def __init__(self, parent=None):
        """Initialise QT GUI."""
        super(MyMainWindow, self).__init__(parent)
        self.form_widget = MainWidget(self)
        self.setCentralWidget(self.form_widget)
        self.statusBar()

        #######################################################################
        # TODO: This is ugly, either just use system theme or supply own icon
        # set.
        icons = {
            'open': 'document-open',
            'exit': 'application-exit',
            'auth': 'gtk-dialog-authentication',
        }
        #theme = QtGui.QIcon.themeName()
        for key, icon in icons.items():
            if not QtGui.QIcon.hasThemeIcon(icon):
                QtGui.QIcon.setThemeName('gnome')
        #######################################################################

        openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'),
                                   '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open playlist')
        openAction.triggered.connect(self.form_widget._open_playlist)

        exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'),
                                   '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)


class MainWidget(QtGui.QWidget):

    """Main widget."""

    def __init__(self, main_window):
        """Initialise main widget."""
        super(MainWidget, self).__init__()
        self.main_window = main_window
        self.running = False

        self.qlist = QtGui.QListWidget(self)

        self.startButton = QtGui.QPushButton("Start")
        self.startButton.clicked.connect(self._copy_files)

        openButton = QtGui.QPushButton("...")
        openButton.setMaximumWidth(30)
        openButton.setStatusTip('Open playlist')
        openButton.clicked.connect(self._open_playlist)

        openLabel = QtGui.QLabel('Playlist:')
        self.openPath = QtGui.QLineEdit()
        self.openPath.editingFinished.connect(lambda: self._load_playlist(
            self.openPath.text()))

        saveButton = QtGui.QPushButton("...")
        saveButton.setMaximumWidth(30)
        saveButton.setStatusTip('Choose destination')
        saveButton.clicked.connect(self._open_destination)

        saveLabel = QtGui.QLabel("Save to:")
        self.savePath = QtGui.QLineEdit()

        hbox = QtGui.QHBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addStretch(1)
        hbox2.addWidget(self.startButton)
        hbox1.addWidget(openLabel)
        hbox1.addWidget(self.openPath)
        hbox1.addWidget(openButton)
        hbox.addWidget(saveLabel)
        hbox.addWidget(self.savePath)
        # XXX: Benco suggested moving saveButton into statusBar. Not sure how
        # I feel about this though as it seems somewhat messy to put a button
        # into the status area.
        hbox.addWidget(saveButton)
        hbox2.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        # XXX: Benco suggested moving hbox before qlist
        vbox.addLayout(hbox1)
        vbox.addWidget(self.qlist)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

    def show_error(self, msg):
        """Display error message."""
        QtGui.QMessageBox.warning(self, "Warning", str(msg))

    def _on_progress_update(self, data):
        # FIXME: Right now this doesn't get updated anymore as soon as the
        # thread stops - this results in the progress count actually being
        # behind by one.
        self.main_window.form_widget.qlist.setCurrentRow(data)
        for i in range(0, data):
            self.main_window.form_widget.qlist.item(i).setBackground(
                QtGui.QColor(198, 233, 175))
        if self.sargasso.stop:
            self.main_window.statusBar().showMessage("Stopping...")
        else:
            self.main_window.statusBar().showMessage(
                "{index}/{length}".format(
                    index=data,
                    length=self.main_window.form_widget.qlist.count()))

    def _on_state_update(self, data):
        if data in ['stopped', 'done']:
            self.running = False
            self.startButton.setText("Start")
            if data == 'done':
                self.main_window.statusBar().showMessage("Done")
            else:
                self.main_window.statusBar().showMessage("Stopped")
        else:
            self.running = True
            self.startButton.setText("Stop")

    def _on_error(self, msg):
        self.show_error(msg)

    def _open_playlist(self):
        fname = QtGui.QFileDialog.getOpenFileName(
            self, 'Open file', path.expanduser('~'))
        if fname:
            self.openPath.setText(fname)
            self._load_playlist(fname)

    def _load_playlist(self, playlist_file):
        try:
            if playlist_file:
                self.qlist.clear()
                playlist = Playlist(playlist_file)
        except Playlist.UnknownPlaylistFormat:
            self.show_error("Unknown playlist format")
        except Playlist.UnsupportedPlaylistFormat as e:
            self.show_error("Unsupported playlist format: {0}".format(e))
        else:
            files = playlist.get_files()
            for f in files:
                self.qlist.addItem(f)

    def _open_destination(self):
        dname = QtGui.QFileDialog.getExistingDirectory(
            self, 'Save to', path.expanduser('~'))
        if dname:
            self._set_destination(dname)

    def _set_destination(self, path):
        self.savePath.setText(path)

    def _copy_files(self):
        if self.running:
            self.sargasso.stop = True
        else:
            files = []

            for index in range(0, self.qlist.count()):
                # Clear list style
                self.main_window.form_widget.qlist.item(index).setBackground(
                    QtGui.QColor('white'))
                files.append(self.qlist.item(index).text())
            destination = self.savePath.text()

            self.threads = []

            sargasso = SquarePigThread(files, destination)
            sargasso.error.connect(self._on_error)

            self.threads.append(sargasso)
            sargasso.start()

            self.sargasso = sargasso.sargasso

            progress = ProgressThread(sargasso.sargasso)
            progress.state.connect(self._on_state_update)
            progress.progress.connect(self._on_progress_update)

            self.threads.append(progress)
            progress.start()


def main():
    """Main function."""
    app = QtGui.QApplication(sys.argv)
    window = MyMainWindow()
    window.resize(640, 480)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
