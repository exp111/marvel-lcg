"""Command-line entry point for the v1.8 timing fixture generator."""

from engine import Engine  # noqa: F401 - establish the project's import order
from game.test.v18_timing_harness import validate_all, write_all


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate", action="store_true")
    arguments = parser.parse_args()

    if arguments.write:
        write_all()
    if arguments.validate or not arguments.write:
        validate_all()
