import os

class Build:
    release = "RELEASE" in os.environ
    release = True

    # Version
    MAJOR = 1
    MINOR = 1
    PATCH = 1
    BUILD = 0
