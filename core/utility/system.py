class System:

    @staticmethod
    def SetTitle(title: str) -> None:
        import ctypes
        import os

        if os.name == "nt":
            ctypes.windll.kernel32.SetConsoleTitleW(str(title))

    @staticmethod
    def Pause() -> None:
        input("Press Enter to continue . . .")

    @staticmethod
    def Sleep(secs: float):
        from time import sleep
        return sleep(secs)
