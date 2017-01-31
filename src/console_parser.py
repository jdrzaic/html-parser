import tree_builder
import html_tag
import sys
import examples


def main():
    html_string = examples.ex1
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "-f":
        filename = args[1]
        with open(filename, 'r') as f:
            html_string = f.read()
    html_tag.initialize_tags()
    builder = tree_builder.TreeBuilder(html_string)
    builder.parse()



if __name__ == "__main__":
    main()