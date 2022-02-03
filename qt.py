import os

from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtWidgets import *
import sys

import midi_helper as helper
from database import DatabaseWorker
from l_system import lsystem, parse_lengths
from markov import Markov
from random import randint, choice
import itertools


class Worker(QRunnable):
    def __init__(self, items, database):
        super().__init__()
        self.database = database
        self.items = items
        self.seed = 0

    @pyqtSlot()
    def run(self):
        blocks = []
        for item in self.items:
            filename = item.text()
            # Extract the notes from midi file using midi helper
            midi_extraction = helper.Extract(f"midi/{filename}")
            midi_extraction.parse_midi()
            chords = midi_extraction.get_chords()

            # Generate markov chain
            markov_chain = Markov(3)
            markov = markov_chain.transition_matrix(chords)

            # Generate 15 sequence of notes using the markov chain
            for _ in range(15):
                success = False
                while not success:
                    try:
                        # Generate a segment of length some power 2^n
                        length = 2 ** randint(2, 3)
                        notes = markov_chain.generate_sequence(markov, length=length)
                        blocks.append(notes)
                        success = True
                    except Exception as e:
                        print(e)

            self.database.insert(filename, self.database.to_json(blocks))

        notes = [choice(blocks) for x in range(50)]

        # rules = {"a": "b", "b": "(a)[b]"}
        # rules = {"a": "b[a]b(a)a", "b": "bb"}
        # rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}
        rules = {"a": "c(ba(b))c[ba[b]]", "b": "c(be)c[bf]", "c": "cgg"}
        # rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cd"}

        tree = lsystem("a", rules, 8)
        durations = parse_lengths(tree)
        # print(durations)
        self.filename = "mozasasaassaas"
        helper.write_to_midi(f"{self.filename[:-4]}_{self.seed}.mid", list(itertools.chain.from_iterable(notes)),
                             durations)

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
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.list_widget)

        self.button_generate = QPushButton()
        self.button_generate.setText("Generate")
        self.button_generate.clicked.connect(self.generate)
        layout.addWidget(self.button_generate)

        # Create a database object on a background thread
        self.database = DatabaseWorker()
        self.threadpool.start(self.database)

    def generate(self):
        if self.threadpool.activeThreadCount() == 0:
            items = self.list_widget.selectedItems()
            print(items)
            worker = Worker(items, self.database)
            self.threadpool.start(worker)
        else:
            print("Worker already running")


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())
