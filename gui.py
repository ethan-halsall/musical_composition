import tkinter as tk
from tkinter import messagebox
import os

# The main tkinter window
import numpy as np
import random
from markov import Markov
import midi_helper as helper
from l_system import lsystem, parse_lengths
from markov import Markov
import threading

seed = random.randint(0, 2 ** 32 - 1)
# Set numpy seed for random
np.random.seed(seed)


class Window:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Music')
        self.window.geometry("500x500")
        self.thread = threading.Thread()
        self.lb = tk.Listbox(self.window)
        self.lb.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
        for count, file in enumerate(files):
            self.lb.insert(count,file)

        tk.Button(self.window, text='Generate music', command=self.generate_music).pack(pady=20)
        self.show = tk.Label(self.window)
        self.show.pack()

    def gen(self, filename):
        # Extract the notes from midi file using midi helper
        midi_extraction = helper.Extract(f"midi/{filename}")
        midi_extraction.parse_midi()
        chords = midi_extraction.get_chords()

        # Generate markov chain
        markov_chain = Markov(3)
        markov = markov_chain.transition_matrix(chords)

        # Generate a sequence of notes using the markov chain
        notes = markov_chain.generate_sequence(markov)

        # rules = {"a": "b[a]b(a)a", "b": "bb"}
        # rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

        rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}

        tree = lsystem("abacd", rules, 7)

        durations = parse_lengths(tree)

        helper.write_to_midi(f"{filename[:-4]}_{seed}.mid", notes, durations)

        # Play midi file using timidity binary
        os.system(f"timidity -Os out/{filename[:-4]}_{seed}.mid")

    def generate_music(self):
        if not self.thread.is_alive():
            filename = self.lb.get(tk.ANCHOR)
            self.show.config(text=f"Generating music based on {filename}")
            thread = threading.Thread(target=self.gen, args=[filename])
            thread.start()
        else:
            messagebox.showerror('Error', 'Cannot do multiple generations at the same time')

    def start(self):
        self.window.mainloop()


gui = Window()
gui.start()
