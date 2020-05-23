class Configuration:
    def __init__(self, game: str, ignore_warnings: bool, process_all_sections: bool):
        self.game = game
        self.ignore_warnings = ignore_warnings  # If False, warnings stop program execution
        # If False, other sections than XSPT will be ignored during WAD processing (speeds up extraction)
        self.process_all_sections = process_all_sections
