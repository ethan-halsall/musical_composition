import os

from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtWidgets import *
import sys

import midi_helper as helper
import l_system
from markov import Markov


class Worker(QRunnable):
    def __init__(self, filename, seed=1):
        super().__init__()
        self.filename = filename
        self.seed = seed

    @pyqtSlot()
    def run(self):
        # Extract the notes from midi file using midi helper
        midi_extraction = helper.Extract(f"midi/{self.filename}")
        midi_extraction.parse_midi()
        chords = midi_extraction.get_chords()

        # Generate markov chain
        markov_chain = Markov(3)
        markov = markov_chain.transition_matrix(chords)

        # Generate a sequence of notes using the markov chain
        notes = markov_chain.generate_sequence(markov)

        # rules = {"a": "b[a]b(a)a", "b": "bb"}
        rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

        rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}

        tree = l_system.lsystem("abacd", rules, 7)

        durations = l_system.parse_lengths(tree)

        helper.write_to_midi(f"{self.filename[:-4]}_{self.seed}.mid", notes, durations)

        # Play midi file using timidity binary
        os.system(f"timidity -Os out/{self.filename[:-4]}_{self.seed}.mid")


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)
        self.list_widget = QListWidget()
        self.window().resize(500, 500)

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
        for count, file in enumerate(files):
            self.list_widget.insertItem(count, file)

        # self.listwidget.clicked.connect(self.clicked)
        layout.addWidget(self.list_widget)

        self.button_generate = QPushButton()
        self.button_generate.setText("Generate")
        self.button_generate.clicked.connect(self.generate)
        layout.addWidget(self.button_generate)

    def clicked(self, qmodelindex):
        item = self.list_widget.currentItem()
        print(item.text())

    def generate(self):
        if self.threadpool.activeThreadCount() == 0:
            item = self.list_widget.currentItem()
            worker = Worker(item.text())
            self.threadpool.start(worker)
        else:
            print("Worker already running")


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())
