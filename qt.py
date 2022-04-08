import os
import sys

from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool, Qt
from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

import midi_helper as helper
import workers

from dataclasses import dataclass, fields

from configparser import ConfigParser


@dataclass()
class Settings:
    order: int = 3
    prune: bool = True
    max_length: int = 4
    quantize: bool = True
    # multiple_channels: bool = False


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, figure):
        fig = figure
        super(MplCanvas, self).__init__(fig)


class SettingsPopup(QWidget):
    def __init__(self, settings):
        QWidget.__init__(self)
        self.settings = settings
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.setWindowTitle("Options")

        self.signals = workers.WorkerSignals()

        # Markov order
        self.order_label = QLabel()
        self.order_label.setText("Markov chain order")
        self.order_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.order_label, 0, 0)

        self.order_text_field = QLineEdit()
        self.order_text_field.setMaxLength(1)
        self.order_text_field.setText(str(self.settings.order))
        self.layout.addWidget(self.order_text_field, 0, 1)

        """# Multiple channels
        self.multiple_channels_label = QLabel()
        self.multiple_channels_label.setText("Multiple instruments")
        self.multiple_channels_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.multiple_channels_label, 1, 0)
        self.multiple_channels_checkbox = QCheckBox()
        self.multiple_channels_checkbox.setChecked(
            self.settings.multiple_channels)
        self.layout.addWidget(self.multiple_channels_checkbox, 1, 1)"""

        # Max length of segment
        self.max_length_label = QLabel()
        self.max_length_label.setText("Maximum length of segment")
        self.max_length_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.max_length_label, 2, 0)

        self.max_length_text_field = QLineEdit()
        self.max_length_text_field.setMaxLength(2)
        self.max_length_text_field.setText(str(self.settings.max_length))
        self.layout.addWidget(self.max_length_text_field, 2, 1)

        # Quantization
        self.quantization_label = QLabel()
        self.quantization_label.setText("Quantize durations")
        self.quantization_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.quantization_label, 3, 0)
        self.quantization_checkbox = QCheckBox()
        self.quantization_checkbox.setChecked(self.settings.quantize)
        self.layout.addWidget(self.quantization_checkbox, 3, 1)

        # Prune
        self.prune_label = QLabel()
        self.prune_label.setText("Prune segments")
        self.prune_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.prune_label, 4, 0)
        self.prune_checkbox = QCheckBox()
        self.prune_checkbox.setChecked(self.settings.prune)
        self.layout.addWidget(self.prune_checkbox, 4, 1)

        # Save button
        self.button_save = QPushButton()
        self.button_save.setText("Save")
        self.button_save.clicked.connect(self.on_save)
        self.layout.addWidget(self.button_save, 5, 0)

        # Cancel button
        self.cancel_save = QPushButton()
        self.cancel_save.setText("Cancel")
        self.cancel_save.clicked.connect(self.quit)
        self.layout.addWidget(self.cancel_save, 5, 1)

    def quit(self):
        self.destroy()

    def on_save(self):
        settings = Settings(int(self.order_text_field.text()),
                            self.prune_checkbox.isChecked(),
                            int(self.max_length_text_field.text()),
                            self.quantization_checkbox.isChecked())
        self.signals.result.emit(settings)
        self.destroy()


class GeneratorPopup(QWidget):
    def __init__(self, segment, threadpool):
        QWidget.__init__(self)
        self.window().resize(1280, 720)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.threadpool = threadpool

        self.segment = segment
        self.figure = None
        self.now_playing = False

        self.button_play = QPushButton()
        self.button_play.setText("Play")
        self.button_play.clicked.connect(self.play)
        self.layout.addWidget(self.button_play, 1, 7)

        self.button_export = QPushButton()
        self.button_export.setText("Export")
        self.button_export.clicked.connect(self.export)
        self.layout.addWidget(self.button_export, 1, 6)

        self.draw_graph()

    def draw_graph(self):
        part = self.segment.part
        plot = part.plot(doneAction=None)
        self.figure = MplCanvas(plot.figure)
        self.layout.addWidget(self.figure, 0, 0, 1, 8)

    def play(self):
        if not self.now_playing:
            worker = workers.PlayMidiWorker(self.segment)
            self.threadpool.start(worker)
            worker.signals.finished.connect(self.playing_complete)
            self.now_playing = True
        else:
            print("Music already playing")

    def export(self):
        filename = QFileDialog.getSaveFileName(
            self, 'Save File', directory="./out", filter="Midi files (*.mid)")
        if filename[0] != '':
            self.segment.write_to_midi(export=True, filename=filename[0])

    def playing_complete(self):
        self.now_playing = False


class InstrumentSelector(QWidget):
    def __init__(self, filename, threadpool, settings):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.window().resize(500, 500)
        self.filename = filename
        self.layout.addWidget(self.list_widget)
        self.threadpool = threadpool
        self.setWindowTitle("Instruments")
        self.settings = settings

        self.midi_extraction = None

        self.signals = workers.WorkerSignals()

        self.button_sequence = QPushButton()
        self.button_sequence.setText("Select instrument")
        self.button_sequence.clicked.connect(self.select_instrument)
        self.layout.addWidget(self.button_sequence, 2, 0)

        worker = ProcessMidiWorker(self.filename)
        self.threadpool.start(worker)
        worker.signals.result.connect(self.display_midi_data)

    def display_midi_data(self, midi_extraction):
        self.midi_extraction = midi_extraction
        for count, inst in enumerate(midi_extraction.get_instruments()):
            self.list_widget.insertItem(count, str(inst))

    def sequence_complete(self, filename):
        self.signals.finished.emit(filename)
        self.destroy()

    def select_instrument(self):
        if self.midi_extraction is None:
            return

        item = self.list_widget.currentItem().text()

        worker = workers.SequenceWorker(
            self.midi_extraction, self.filename, item, self.settings.order, self.settings.max_length)
        self.threadpool.start(worker)
        worker.signals.finished.connect(self.sequence_complete)


class ProcessMidiWorker(QRunnable):
    def __init__(self, item):
        super().__init__()
        self.signals = workers.WorkerSignals()
        self.filename = item
        self.midi_extraction = None

    @pyqtSlot()
    def run(self):
        try:
            # Extract the notes from midi file using midi helper
            self.midi_extraction = helper.Extract(f"midi/{self.filename}")
        finally:
            if self.midi_extraction is not None:
                self.signals.result.emit(self.midi_extraction)


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.settings = Settings()
        self.selector = None
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.window().resize(1280, 720)
        self.setWindowTitle("Composer")

        self.current_segments = None
        self.current_segment = None
        self.current_row = ""
        self.sequence_generating = False
        self.now_playing = False
        self.sequences = []
        self.figure = None

        self.popup = None

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" %
              self.threadpool.maxThreadCount())

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
        self.graph_positions = {}
        for count, file in enumerate(files):
            self.list_widget.insertItem(count, file)
            self.graph_positions[file] = 0
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.clicked.connect(self.clicked)
        self.list_widget.setCurrentRow(0)
        self.layout.addWidget(self.list_widget, 0, 0, 2, 2)

        self.button_sequence = QPushButton()
        self.button_sequence.setText("Generate sequences")
        self.button_sequence.clicked.connect(self.on_button_sequence)
        self.layout.addWidget(self.button_sequence, 2, 0)

        self.button_generate = QPushButton()
        self.button_generate.setText("Generate music")
        self.button_generate.clicked.connect(self.on_button_generate)
        self.layout.addWidget(self.button_generate, 2, 1)

        # Create button for going to previous graph
        self.button_previous = QPushButton()
        self.button_previous.setText("Prev")
        self.button_previous.clicked.connect(self.prev_graph)
        self.layout.addWidget(self.button_previous, 1, 8)

        # Create button for going to next graph
        self.button_forward = QPushButton()
        self.button_forward.setText("Next")
        self.button_forward.clicked.connect(self.next_graph)
        self.layout.addWidget(self.button_forward, 1, 9)

        # Indicator label
        self.indicator = QLabel()
        self.indicator.setText("0/0")
        self.indicator.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.indicator, 2, 9)

        # Create button for going to next graph
        self.button_play = QPushButton()
        self.button_play.setText("Play")
        self.button_play.clicked.connect(self.play)
        self.layout.addWidget(self.button_play, 1, 7)

        # Create button for options
        self.button_options = QPushButton()
        self.button_options.setText("Options")
        self.button_options.clicked.connect(self.open_options)
        self.layout.addWidget(self.button_options, 1, 2)

        # Create Checkbox
        self.check_box = QCheckBox("Include")
        self.check_box.clicked.connect(self.click_box_listener)
        self.layout.addWidget(self.check_box, 2, 8)

        # Key label
        self.key_label = QLabel()
        self.key_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.key_label, 2, 7)

        # self.draw_graph(files[0], pos=0) this needs to be run after constructor

    def open_options(self):
        self.popup = SettingsPopup(self.settings)
        self.popup.signals.result.connect(self.update_settings)
        self.popup.show()

    def update_settings(self, settings):
        old = self.settings
        self.settings = settings

        if settings.order != old.order:
            # self.on_button_sequence() #either message of warning saying it will not update current setup or update all...?
            pass
        elif settings.prune != old.prune:
            # Redraw current graph
            if self.current_segments is not None:
                print(self.current_row)
                self.on_listbox_click(self.current_row, update=True)

    def click_box_listener(self):
        segment = self.current_segment
        if self.check_box.isChecked():
            self.sequences.append(segment)
        else:
            self.sequences.remove(segment)

        print(self.sequences)

    def next_graph(self):
        item = self.list_widget.currentItem().text()
        new_pos = self.graph_positions[item] + 1
        if new_pos < len(self.current_segments):
            self.graph_positions[item] += 1
            self.on_listbox_click(item)

    def prev_graph(self):
        item = self.list_widget.currentItem().text()
        new_pos = self.graph_positions[item] - 1
        if new_pos >= 0:
            self.graph_positions[item] -= 1
            self.on_listbox_click(item)

    def clicked(self):
        item = self.list_widget.currentItem()
        self.on_listbox_click(item.text())

    def draw_graph(self, result: list[helper.Segment] = None):
        if result is not None:
            self.current_segments = result

        # Assign current row only if we have data to draw
        self.current_row = self.current_segments[0].filename

        pos = self.graph_positions[self.current_segments[0].filename]
        filename = self.current_segments[0].filename

        if self.current_segments[pos] in self.sequences:
            self.check_box.setChecked(True)
        else:
            self.check_box.setChecked(False)

        segment = self.current_segments[pos]

        if self.figure is not None:
            self.figure.close()

        # bug here does not show after regen
        self.key_label.setText(segment.get_key())
        part = segment.part
        plot = part.plot(doneAction=None)
        self.figure = MplCanvas(plot.figure)
        self.layout.addWidget(self.figure, 0, 2, 1, 8)
        self.indicator.setText(
            f"{self.graph_positions[filename] + 1}/{len(self.current_segments)}")
        self.current_segment = segment

    def on_listbox_click(self, filename, update=False):
        if self.current_segments is None or filename != self.current_row or update:
            fetch = workers.FetchDataWorker(filename, self.settings.prune, self.settings.quantize)
            fetch.signals.result.connect(self.draw_graph)
            fetch.signals.error.connect(self.fetch_failed)
            self.threadpool.start(fetch)
        else:
            self.draw_graph()

    def fetch_failed(self, error):
        if self.figure is not None:
            self.figure.close()
        fig = plt.figure()
        self.figure = MplCanvas(fig)
        self.layout.addWidget(self.figure, 0, 2, 1, 8)
        self.check_box.setChecked(False)
        self.indicator.setText("0/0")
        self.key_label.setText("")

    def play(self):
        if self.current_segment is not None and not self.now_playing:
            worker = workers.PlayMidiWorker(self.current_segment)
            self.threadpool.start(worker)
            worker.signals.finished.connect(self.playing_complete)
            self.now_playing = True
        else:
            print("Music already playing")

    def playing_complete(self):
        self.now_playing = False

    def sequence_complete(self, filename):
        self.sequence_generating = False
        self.on_listbox_click(filename, update=True)

    def on_button_sequence(self):
        if not self.sequence_generating:
            item = self.list_widget.currentItem().text()
            self.selector = InstrumentSelector(
                item, self.threadpool, self.settings)
            self.selector.show()
            self.selector.signals.finished.connect(self.sequence_complete)
            self.sequence_generating = True
        else:
            print("Worker already running")

    def on_button_generate(self):
        rules = {"a": "b", "b": "ba", "c": "bc"}
        if self.sequences:
            gen = helper.Generate(self.sequences, rules)
            gen.generate_rules()
            melody = gen.l_system(gen.axiom, 4)
            print(melody)
            notes, durations = gen.convert_to_segments(melody)

            """  durations = []
            notes = []
            durations = []
            for sequence in sequences:
                notes += sequence.get_segment()
                durations += sequence.durations"""

            segment = helper.Segment(
                notes, "test.mid", 0, durations, "", self.settings.prune, self.settings.quantize)

            self.popup = GeneratorPopup(segment, self.threadpool)
            self.popup.show()


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())
