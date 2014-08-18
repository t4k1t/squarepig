"""Qt GUI for Squarepig."""

from sys import argv, exit, stderr
from os import path, mkdir
from time import sleep

from xdg.BaseDirectory import xdg_cache_home
from PyQt4 import QtCore, QtGui

from squarepig.backpig import SquarePig, Playlist


class SquarepigThread(QtCore.QThread):

    """Worker thread."""

    error = QtCore.pyqtSignal(object)

    def __init__(self, files, destination):
        """Initialise thread."""
        # XXX: DEBUG output
        print("initialising squarepig thread...")
        QtCore.QThread.__init__(self)
        self.sargasso = SquarePig()
        self.files = files
        self.destination = destination

    def run(self):
        """Run thread."""
        # XXX: DEBUG output
        print("run squarepig thread")
        try:
            self.sargasso.copy_to(self.files, self.destination)
        except SquarePig.CopyError as e:
            self.error.emit(e)


class ProgressThread(QtCore.QThread):

    """Progress update thread."""

    progress = QtCore.pyqtSignal(object, object)
    state = QtCore.pyqtSignal(object)

    def __init__(self, sargasso):
        """Initialise thread."""
        # XXX: DEBUG output
        print("initialising progress thread...")
        QtCore.QThread.__init__(self)
        self.sargasso = sargasso

    def run(self):
        """Run thread."""
        # XXX: DEBUG output
        print("run progress thread")
        self.length = -1
        while True:
            state = self.sargasso.get_state()
            self.state.emit(state)
            if state not in ['stopped', 'done']:
                index, self.length = self.sargasso.get_progress()
                failed = self.sargasso.get_failed()
                self.progress.emit(index, failed)
            else:
                index, self.length = self.sargasso.get_progress()
                failed = self.sargasso.get_failed()
                # XXX: DEBUG output
                print("failed: %s" % str(failed))
                self.progress.emit(index, failed)
                self.state.emit(state)
                break
            sleep(0.2)


class MyMainWindow(QtGui.QMainWindow):

    """Main window."""

    def __init__(self, parent=None):
        """Initialise Qt GUI."""
        super(MyMainWindow, self).__init__(parent)
        self.setWindowTitle("Squarepig")
        self.form_widget = MainWidget(self)
        self.setCentralWidget(self.form_widget)
        self.statusBar()

        # icon theme fallback
        icons = {
            'open': 'document-open',
            'exit': 'application-exit',
        }
        for key, icon in icons.items():
            if not QtGui.QIcon.hasThemeIcon(icon):
                QtGui.QIcon.setThemeName('gnome')

        openText = _("&Open")
        openAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-open'),
                                   openText, self)
        openAction.setShortcut('Ctrl+O')
        openTipText = _("Open playlist")
        openAction.setStatusTip(openTipText)
        openAction.triggered.connect(self.form_widget._open_playlist)

        exitText = _("&Exit")
        exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'),
                                   exitText, self)
        exitTipText = _("Exit applictaion")
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip(exitTipText)
        exitAction.triggered.connect(QtGui.qApp.quit)

        menubar = self.menuBar()
        fileText = _("&File")
        fileMenu = menubar.addMenu(fileText)
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

        startButtonText = _("Start")
        self.startButton = QtGui.QPushButton(startButtonText)
        self.startButton.clicked.connect(self._copy_files)

        openButton = QtGui.QPushButton("...")
        openButton.setMaximumWidth(30)
        openButtonText = _("Open playlist:")
        openButton.setStatusTip(openButtonText)
        openButton.clicked.connect(self._open_playlist)

        openLabelText = _("Playlist:")
        openLabel = QtGui.QLabel(openLabelText)
        self.openPath = QtGui.QLineEdit()
        self.openPath.editingFinished.connect(lambda: self._load_playlist(
            self.openPath.text()))

        saveButton = QtGui.QPushButton("...")
        saveButton.setMaximumWidth(30)
        saveButtonText = _("Choose destination")
        saveButton.setStatusTip(saveButtonText)
        saveButton.clicked.connect(self._open_destination)

        saveLabelText = _("Save to:")
        saveLabel = QtGui.QLabel(saveLabelText)
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
        # NOTE: Benco suggested moving saveButton into statusBar. Not sure how
        # I feel about this though as it seems somewhat messy to put a button
        # into the status area.
        hbox.addWidget(saveButton)
        hbox2.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        # NOTE: Benco suggested moving hbox before qlist
        vbox.addLayout(hbox1)
        vbox.addWidget(self.qlist)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

        self.cachedir = '{0}/squarepig'.format(xdg_cache_home)
        try:
            mkdir(self.cachedir, 0o755)
        except OSError:
            # cachedir does already exist
            pass

    def show_error(self, msg):
        """Display error message."""
        QtGui.QMessageBox.warning(self, "Warning", str(msg))

    def _on_progress_update(self, data, failed):
        # FIXME: Right now this doesn't get updated anymore as soon as the
        # thread stops - this results in the progress count actually being
        # behind by one.
        # #NOTE: Above FIXME might actually be fixed now.
        # XXX: DEBUG output
        print(data)
        self.main_window.form_widget.qlist.setCurrentRow(data)
        for i in range(0, data):
            self.main_window.form_widget.qlist.item(i).setBackground(
                QtGui.QColor(198, 233, 175))
        # paint all failed ones red
        for j in failed:
            self.main_window.form_widget.qlist.item(j).setBackground(
                QtGui.QColor(211, 95, 95))
        if self.sargasso.stop:
            msg = _("Stopping...")
            self.main_window.statusBar().showMessage(msg)
        else:
            self.main_window.statusBar().showMessage(
                "{index}/{length}".format(
                    index=data,
                    length=self.main_window.form_widget.qlist.count()))

    def _on_state_update(self, data):
        if data in ['stopped', 'done']:
            self.running = False
            startButtonText = _("Start")
            self.startButton.setText(startButtonText)
            if data == 'done':
                msg = _("Done")
                self.main_window.statusBar().showMessage(msg)
            else:
                msg = _("Stopped")
                self.main_window.statusBar().showMessage(msg)
        else:
            self.running = True
            startButtonText = _("Stop")
            self.startButton.setText(startButtonText)

    def _on_error(self, msg):
        self.show_error(msg)

    def _open_playlist(self):
        pl_path = '~'
        myfile = None
        try:
            myfile = open('{0}/playlist_path'.format(self.cachedir), 'r',
                          encoding='utf-8')
        except FileNotFoundError:
            try:
                myfile = open('{0}/playlist_path'.format(self.cachedir), 'w',
                              encoding='utf-8')
            except OSError as e:
                msg = _("Unable to write to cache: {0}".format(e))
                stderr.write('{0}\n'.format(msg))
            else:
                myfile.close()
        else:
            pl_path = myfile.readline()
            myfile.close()

        fileDialogText = _("Open file")
        fname = QtGui.QFileDialog.getOpenFileName(
            self, fileDialogText, path.expanduser(pl_path))
        if fname:
            try:
                myfile = open('{0}/playlist_path'.format(self.cachedir), 'w',
                              encoding='utf-8')
            except FileNotFoundError:
                pass
            else:
                myfile.write(fname)
                myfile.close()

            self.openPath.setText(fname)
            self._load_playlist(fname)

    def _load_playlist(self, playlist_file):
        try:
            if playlist_file:
                self.qlist.clear()
                playlist = Playlist(playlist_file)
        except Playlist.UnknownPlaylistFormat:
            errorText = _("Unknown playlist format")
            self.show_error(errorText)
        except Playlist.UnsupportedPlaylistFormat as e:
            errorText = _("Unsupported playlist format: {0}".format(e))
            self.show_error(errorText)
        except (FileNotFoundError, UnicodeDecodeError):
            errorText = _("Unable to read playlist: {0}".format(playlist_file))
            self.show_error(errorText)
        else:
            files = playlist.get_files()
            for f in files:
                self.qlist.addItem(f)

    def _open_destination(self):
        dst_path = '~'
        myfile = None
        try:
            myfile = open('{0}/dest_path'.format(self.cachedir), 'r',
                          encoding='utf-8')
        except FileNotFoundError:
            try:
                myfile = open('{0}/dest_path'.format(self.cachedir), 'w',
                              encoding='utf-8')
            except OSError as e:
                msg = _("Unable to write to cache: {0}".format(e))
                stderr.write('{0}\n'.format(msg))
            else:
                myfile.close()
        else:
            dst_path = myfile.readline()
            myfile.close()

        fileDialogText = _("Save to")
        dname = QtGui.QFileDialog.getExistingDirectory(
            self, fileDialogText, path.expanduser(dst_path))
        if dname:
            try:
                myfile = open('{0}/dest_path'.format(self.cachedir), 'w',
                              encoding='utf-8')
            except FileNotFoundError:
                pass
            else:
                myfile.write(dname)
                myfile.close()

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
            if len(files) == 0:
                errorText = _("Please select a playlist first")
                self.show_error(errorText)
                return
            destination = self.savePath.text()

            self.threads = []

            sargasso = SquarepigThread(files, destination)
            sargasso.error.connect(self._on_error)

            self.threads.append(sargasso)
            # sargasso.start()

            self.sargasso = sargasso.sargasso

            progress = ProgressThread(sargasso.sargasso)
            progress.state.connect(self._on_state_update)
            progress.progress.connect(self._on_progress_update)

            self.threads.append(progress)
            # progress.start()
            # sleep(0.1)
            # for t in self.threads:
            #     t.start()

            # NOTE: Make sure sargasso thread is started before progress
            # thread, so progress thread has something to report.
            sargasso.start()
            sleep(0.1)
            progress.start()


def main():
    """Main function."""
    app = QtGui.QApplication(argv)
    window = MyMainWindow()
    window.resize(640, 480)
    window.show()
    exit(app.exec_())


if __name__ == "__main__":
    main()
