CROC_1_PS1 = "Croc 1 PS1"
CROC_2_PS1 = "Croc 2 PS1"
CROC_2_DEMO_PS1 = "Croc 2 Demo PS1"
CROC_2_DEMO_PS1_DUMMY = "Croc 2 Demo PS1 (Dummy)"
HARRY_POTTER_1_PS1 = "Harry Potter 1 PS1"
HARRY_POTTER_2_PS1 = "Harry Potter 2 PS1"

# Croc 1 parsing is not supported, but it can be extracted
PARSABLE_GAMES = (CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1)
EXTRACTABLE_GAMES = (
    CROC_1_PS1, CROC_2_PS1, CROC_2_DEMO_PS1, CROC_2_DEMO_PS1_DUMMY, HARRY_POTTER_1_PS1, HARRY_POTTER_2_PS1)

dir_dat = {CROC_1_PS1: (24, 'CROCFILE.DIR', 'CROCFILE.1'), CROC_2_PS1: (20, 'CROCII.DIR', 'CROCII.DAT'),
           CROC_2_DEMO_PS1: (20, 'CROCII.DIR', 'CROCII.DAT'), CROC_2_DEMO_PS1_DUMMY: (None, None, 'DUMMY.DAT'),
           HARRY_POTTER_1_PS1: (20, 'POTTER.DIR', 'POTTER.DAT'), HARRY_POTTER_2_PS1: (20, 'POTTER.DIR', 'POTTER.DAT')}
