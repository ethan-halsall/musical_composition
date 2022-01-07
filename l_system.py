rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}
rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cd"}


def lsystem(axiom, rules, n):
    out = axiom
    for _ in range(n):
        pos = 0
        for char in out:
            if char in rules:
                out = out[:pos] + rules[char] + out[pos + 1:]
                pos += len(rules[char])
            else:
                pos += 1

    return out


def parse_lengths(tree):
    curr = tree[0]
    length = 0.33
    durations = []
    for char in tree:
        if curr == char:
            length += 0.33
        else:
            if length > 0:
                durations.append(length)
            length = 0

    return durations


tree = lsystem("a", rules, 4)

durations = parse_lengths(tree)
