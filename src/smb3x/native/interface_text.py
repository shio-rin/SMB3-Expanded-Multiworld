# SPDX-License-Identifier: MPL-2.0
"""Authored native labels and rows; numbers/permissions are filled from authority."""
MESSAGES = dict(NoView='MOVE ON MAP FOR HAMMER', LegacyTitle='LEGACY HAMMERS', LegacyLine='USE ORDINARY BAG HAMMERS', LegacyBack='B BACK THEN B INVENTORY', Footer='LR PAGE B BACK START CLOSE', TryRock='A TRY ROCK LR PAGE B BACK', Missing='PERMISSION MISSING B BACK', NoRegion='NO REGIONAL HAMMER', Owned='OWNED', MissingWord='MISSING', Hammer='HAMMER', StarTravel='GATE WORLD 8 TRAVEL', StarBowser='GATE BOWSER CASTLE', StarReady='STAR THRESHOLD MET', StarMissing='STAR THRESHOLD NOT MET', PassNeeded='WORLD 8 PASS ALSO NEEDED', BowserOnly='WORLD TRAVEL UNCHANGED', TravelMap='A TRAVEL B MAP', TravelParent='A TRAVEL B PASSES', CurrentMap='A CLOSE B MAP', CurrentParent='A CLOSE B PASSES', PassMissing='WORLD PASS MISSING', StarGate='STAR GATE          0/  0', Busy='WAIT FOR MAP')

def rows(tile):
    title = lambda s: s.ljust(22) + '1/4'
    ribbon = ''.join((' ' + str(i) + ' ' for i in range(1, 9)))
    region = lambda a, b: (a.ljust(7) + '-').ljust(17) + b.ljust(6) + '-'
    pages = ((title('WORLD PASSES'), 'CURRENT WORLD 1 GRASS', ribbon, ' Y ' * 8, 'Y OWNED  - MISSING', 'TOTAL CHECKS       0/  0', 'A WORLD TRAVEL', 'LR PAGE B BACK START CLOSE'), ('W2 DESERT   HAMMER  OWNED', region('DESERT', 'WATER'), region('GIANT', 'ICE'), 'A TRY ROCK LR PAGE B BACK'), (title('STAR HUNT'), 'FRAGMENTS          0/  0', 'GATE WORLD 8 TRAVEL', 'STAR THRESHOLD NOT MET', 'WORLD 8 PASS ALSO NEEDED', 'PERMANENT FRAGMENTS', 'READ ONLY', 'LR PAGE B BACK START CLOSE'), (title('ITEM CHECKS'), 'CURRENT WORLD 1 GRASS', '               DONE TOTAL', 'CURRENT WORLD      0     0', 'ALL WORLDS         0     0', 'PHYSICAL REWARDS ONLY', 'RELEASES DO NOT COUNT', 'LR PAGE B BACK START CLOSE'), ('WORLD TRAVEL   CURRENT 1', ribbon, ' Y ' * 8, 'WORLD 1 GRASS     OWNED', 'A TRAVEL B MAP', 'LR WORLD START CLOSE'))
    result = []
    for lines in pages:
        result.append(bytes([128] + [tile('-')] * 26 + [129]))
        for line in lines:
            if len(line) > 26:
                raise ValueError('UI row overflow: ' + line)
            result.append(bytes([204] + [tile(c) for c in line.ljust(26)] + [204]))
        result.append(bytes([130] + [tile('-')] * 26 + [131]))
    assert len(result) == 44
    text = 'UiRowsLo: .db ' + ','.join(('LOW(UiText%d)' % i for i in range(44))) + '\n'
    text += 'UiRowsHi: .db ' + ','.join(('HIGH(UiText%d)' % i for i in range(44))) + '\n'
    return text + '\n'.join(('UiText%d: .db ' % i + ','.join(('$%02X' % x for x in row)) for i, row in enumerate(result)))

def values_data(tile, base, rom):
    text = 'UiPageBases: .db 0,10,16,26,36\nUiDigits: .db ' + ','.join((str(tile(str(i))) for i in range(10))) + '\n'
    text += 'UiNames: .db ' + ','.join((str(tile(c)) for n in ('GRASS', 'DESERT', 'WATER', 'GIANT', 'SKY', 'ICE', 'PIPE', 'DARK') for c in n.ljust(8))) + '\n'
    text += 'UiTotals: .db 0,0,0,0,0,0,0,0\n'
    for i, name in enumerate(MESSAGES):
        text += f'Msg{name} = {i}\n'
    text += 'UiMessagesLo: .db ' + ','.join(('LOW(UiMsg' + n + ')' for n in MESSAGES)) + '\n'
    text += 'UiMessagesHi: .db ' + ','.join(('HIGH(UiMsg' + n + ')' for n in MESSAGES)) + '\n'
    for name, message in MESSAGES.items():
        if len(message) > 26:
            raise ValueError('Message overflow ' + name)
        text += 'UiMsg' + name + ': .db ' + ','.join((str(tile(c)) for c in message)) + ',0\n'
    return text
