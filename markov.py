import numpy as np
import pandas as pd


class Markov:
    def __init__(self, order):
        self.order = order

    def transition_matrix(self, transitions):
        unique_states, size = np.unique(transitions, return_counts=True)
        n = len(unique_states)

        sequences = {}

        for i in range(len(transitions)):
            if len(transitions[i:i + self.order + 1]) == self.order + 1:
                key = ",".join(transitions[i:i + self.order + 1])
                if key not in sequences:
                    sequences[key] = 1
                else:
                    sequences[key] += 1

        m = np.zeros((len(sequences), n), int)

        rows = []

        for i, (key, value) in enumerate(sequences.items()):
            splits = key.split(",")
            column = splits[self.order]
            j = np.where(unique_states == column)[0][0]
            m[i][j] = value
            rows.append(",".join(splits[:self.order]))

        df = pd.DataFrame(m)  # convert to dataframe

        # Set axis labels
        df = df.set_axis(rows)
        df = df.set_axis(unique_states, axis=1)

        # Combine rows with same keys
        df = df.groupby(df.index).sum()

        # normalise rows by sum
        df = df.div(df.sum(axis=1), axis=0)

        return df

    def generate_sequence(self, transition_mat, length):
        cur = transition_mat.sample()
        sequence = cur.index.values[0].split(",")
        columns = list(transition_mat.columns.values)
        for i in range(length - self.order):
            probs = cur.values.flatten().tolist()
            state_index = np.random.choice(cur.size, p=probs)
            state = columns[state_index]
            if self.order > 1:
                cur = transition_mat.loc[[",".join(sequence[i + 1:i + self.order]) + f",{state}"]]
            else:
                cur = transition_mat.loc[[f"{state}"]]
            sequence.append(state)
        return sequence
