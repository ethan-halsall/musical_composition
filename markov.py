import numpy as np
import pandas as pd


class Markov:
    def __init__(self, order):
        self.order = order

    def transition_matrix(self, transitions):
        values, size = np.unique(transitions, return_counts=True)
        n = len(values)

        sequences = {}

        for x in range(len(transitions)):
            if len(transitions[x:x + self.order + 1]) == self.order + 1:
                key = ",".join(transitions[x:x + self.order + 1])
                if key not in sequences:
                    sequences[key] = 1
                else:
                    sequences[key] += 1

        m = np.zeros((len(sequences), n), int)

        states = []

        for i, (key, value) in enumerate(sequences.items()):
            splits = key.split(",")
            column = splits[self.order]
            j = np.where(values == column)[0][0]
            m[i][j] = value
            states.append(",".join(splits[:self.order]))

        df = pd.DataFrame(m)  # convert to dataframe

        # Set axis labels
        df = df.set_axis(states)
        df = df.set_axis(values, axis=1)

        # Combine rows with same keys
        df = df.groupby(df.index).sum()

        # normalise rows by sum
        df = df.div(df.sum(axis=1), axis=0)

        return df

    def generate_sequence(self, df, length=400):
        cur = df.sample()
        notes = cur.index.values[0].split(",")
        columns = list(df.columns.values)
        for i in range(length - 1):
            probs = cur.values.flatten().tolist()
            note_index = np.random.choice(cur.size, p=probs)
            note = columns[note_index]
            cur = df.loc[[",".join(notes[i + 1:i + self.order]) + f",{note}"]]
            notes.append(note)
        return notes
