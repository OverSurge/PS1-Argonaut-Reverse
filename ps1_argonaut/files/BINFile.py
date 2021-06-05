from ps1_argonaut.files.DATFile import DATFile


class BINFile(DATFile):
    suffix = 'BIN'

    def __str__(self):
        return 'Translated text'
