import string
import turtle

rules = {"a": "b", "b": "(a)[b]"}
rules = {"a": "b[a]b(a)a", "b": "bb"}
#rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}
rules = {"a": "c(ba(b))c[ba[b]]", "b": "c(be)c[bf]", "c": "cgg"}
#rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cd"}


def lsystem(axiom, rules, n):
    out = ""
    for char in axiom:
        if char in rules:
            out += rules[char]
        else:
            out += char
    n -= 1
    if n > 0:
        return lsystem(out, rules, n)
    return out


def parse_lengths(tree, length=0.14):
    durations = [length]
    for op in tree:
        if op.isalpha():
            durations[len(durations) - 1] += length
        elif op == "(":
            durations.append(length)
        elif op == "[":
            durations.append(length)

    return durations


tree = lsystem("a", rules, 2)
print(tree)

"""tree = lsystem("a", rules, 7)


gen = turtle.Turtle()
gen.speed(0)
gen.left(90)
size = 10
positions = []
turtle.tracer(0, 0)

durations = [0.33]
length = 0.33

for op in tree:
    if op.isalpha():
        gen.forward(size)
        durations[len(durations) - 1] += length
    elif op == "(":
        durations.append(length)
        positions.append(gen.position())
        gen.left(size)
    elif op == ")":
        gen.setposition(positions.pop())
        gen.right(size)
    elif op == "[":
        durations.append(length)
        positions.append(gen.position())
        gen.right(size)
    elif op == "]":
        gen.setposition(positions.pop())
        gen.left(size)


print(durations)

turtle.mainloop()
turtle.exitonclick()"""
