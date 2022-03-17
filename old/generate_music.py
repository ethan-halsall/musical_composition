import string


class Generate:
    def __init__(self, segments, rules):
        self.segments = segments
        self.dict, self.axiom = self.generate_dict()
        self.rules = rules

    def generate_dict(self):
        dict = {}
        alphabet = list(string.ascii_lowercase)
        alphabet_used = []
        for count, segment in enumerate(self.segments):
            alphabet_used.append(alphabet[count])
            dict[alphabet[count]] = segment

        return dict, alphabet_used

    def l_system(self, axiom, n):
        out = ""
        for char in axiom:
            if char in self.rules:
                out += self.rules[char]
            else:
                out += char
        n -= 1
        if n > 0:
            return self.l_system(out, n)
        return out

    def convert_to_sequence(self, melody):
        out = []
        for char in melody:
            out.append(self.dict[char])

        return out

    def generate_rules(self):
        for key, _ in self.dict:
            print(key)


"""rules = {"a": "b", "b": "(a)[b]"}
rules = {"a": "b[a]b(a)a", "b": "bb"}
# rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}
rules = {"a": "c(ba(b))c[ba[b]]", "b": "c(be)c[bf]", "c": "cgg"}"""

rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cd"}
