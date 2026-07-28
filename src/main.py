import sys

import lex
import tree
import error


def main():
    path = sys.argv[1]

    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    root = tree.AstProg.load(src)
    asm = root.compile()

    with open("build.asm", "w") as f:
        f.write(asm)


    


if __name__ == "__main__":
    main()

