import subprocess


def EditCode(file_path: str) -> None:
    """Open a source file in VS Code from a development checkout."""
    subprocess.Popen(["code", file_path])
