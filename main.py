from bruce import pipeline

import sys


def main(path):
    with open(path, "r") as file:
        program = file.read()
    pipeline(program)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print("Usage: python main.py <file.hulk>")
            sys.exit(1)
        elif sys.argv[1][-5:] != ".hulk":
            print(f"{sys.argv[1]} is not a valid file")
            sys.exit(1)
        main(sys.argv[1])
    except FileNotFoundError:
        print("File not found")
        sys.exit(1)
