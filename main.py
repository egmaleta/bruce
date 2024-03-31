from bruce import pipeline

import sys


def main(path):
    with open(path, "r") as file:
        program = file.read()
    pipeline(program)


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except IndexError:
        print("Usage: python main.py <path>")
        sys.exit(1)
    except FileNotFoundError:
        print("File not found")
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)
