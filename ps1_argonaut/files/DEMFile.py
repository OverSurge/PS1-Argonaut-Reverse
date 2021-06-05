from ps1_argonaut.files.DATFile import DATFile


class DEMFile(DATFile):
    suffix = 'DEM'

    def __str__(self):
        return 'Demonstration (DEMO) script'
