import tokeniser
import sys
import util
import examples


def main():
    html_string = examples.ex1
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "-f":
        filename = args[1]
        with open(filename, 'r') as f:
            html_string = f.read()
    t = tokeniser.Tokeniser(util.Reader(html_string))
    print(t.tokenise())
    for html in examples.all:
        t = tokeniser.Tokeniser(util.Reader(html))
        print(t.tokenise())


if __name__ == "__main__":
    main()