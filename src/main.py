import sys

import lex
import tree
import obj
import error

def main():
    path = sys.argv[1]

    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    root = tree.AstProg.load(src)
    print(root)
    #root.run()

    


if __name__ == "__main__":
    main()

