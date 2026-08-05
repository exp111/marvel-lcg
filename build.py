import os

class Build:
    release = "RELEASE" in os.environ
    release = True

    # Version
    MAJOR = 1
    MINOR = 0
    PATCH = 0
    BUILD = 1
