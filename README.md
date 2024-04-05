# bruce: a compiler for the HULK programming language

## What is HULK ?

> HULK (Havana University Language for Kompilers) is a didactic, type-safe, object-oriented and incremental programming language, designed for the course Introduction to Compilers in the Computer Science major at University of Havana.

The complete language reference can be found [here](https://matcom.in/hulk/).

## Setup

**bruce** uses [poetry v1.7.1](https://python-poetry.org/) as a project management tool and requires [python v3.11.8](https://www.python.org/downloads/release/python-3118/) to be installed.

To install `poetry`, follow these [instructions](https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx) to install `pipx`, then run:

```bash
pipx install poetry==1.7.1
```

Finally, install the project dependencies and scripts by running:

```bash
poetry install
```

## Usage

To use the project only run the project's main Python file with the desired file as an argument:

```shell
python main.py "file.hulk"
```

Make sure you have the directory `bruce/serialize_objects` because the lexer will try to look up in that folder all the regexs generated previously or create them.
