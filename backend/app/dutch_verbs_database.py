"""
Dutch Verbs Database - Most common Dutch verbs with their conjugations.

This database contains ~100 of the most frequently used Dutch verbs
conjugated in all 6 main tenses and all 6 personal pronouns.
"""

DUTCH_VERBS_DATABASE = {
    'zijn': {
        'infinitive': 'zijn',
        'englishTranslation': 'to be',
        'verbType': 'irregular',
        'tenses': [
            {
                'dutchName': 'Tegenwoordige Tijd',
                'englishName': 'Present',
                'forms': [
                    {'person': 'ik', 'conjugation': 'ben'},
                    {'person': 'je/jij', 'conjugation': 'bent'},
                    {'person': 'hij/zij/het', 'conjugation': 'is'},
                    {'person': 'wij', 'conjugation': 'zijn'},
                    {'person': 'jullie', 'conjugation': 'zijn'},
                    {'person': 'zij', 'conjugation': 'zijn'},
                ]
            },
            {
                'dutchName': 'Onvoltooid Verleden Tijd',
                'englishName': 'Simple Past',
                'forms': [
                    {'person': 'ik', 'conjugation': 'was'},
                    {'person': 'je/jij', 'conjugation': 'was'},
                    {'person': 'hij/zij/het', 'conjugation': 'was'},
                    {'person': 'wij', 'conjugation': 'waren'},
                    {'person': 'jullie', 'conjugation': 'waren'},
                    {'person': 'zij', 'conjugation': 'waren'},
                ]
            },
            {
                'dutchName': 'Voltooid Tegenwoordige Tijd',
                'englishName': 'Present Perfect',
                'forms': [
                    {'person': 'ik', 'conjugation': 'ben geweest'},
                    {'person': 'je/jij', 'conjugation': 'bent geweest'},
                    {'person': 'hij/zij/het', 'conjugation': 'is geweest'},
                    {'person': 'wij', 'conjugation': 'zijn geweest'},
                    {'person': 'jullie', 'conjugation': 'zijn geweest'},
                    {'person': 'zij', 'conjugation': 'zijn geweest'},
                ]
            },
            {
                'dutchName': 'Voltooid Verleden Tijd',
                'englishName': 'Past Perfect',
                'forms': [
                    {'person': 'ik', 'conjugation': 'was geweest'},
                    {'person': 'je/jij', 'conjugation': 'was geweest'},
                    {'person': 'hij/zij/het', 'conjugation': 'was geweest'},
                    {'person': 'wij', 'conjugation': 'waren geweest'},
                    {'person': 'jullie', 'conjugation': 'waren geweest'},
                    {'person': 'zij', 'conjugation': 'waren geweest'},
                ]
            },
            {
                'dutchName': 'Toekomende Tijd',
                'englishName': 'Future Simple',
                'forms': [
                    {'person': 'ik', 'conjugation': 'zal zijn'},
                    {'person': 'je/jij', 'conjugation': 'zal zijn'},
                    {'person': 'hij/zij/het', 'conjugation': 'zal zijn'},
                    {'person': 'wij', 'conjugation': 'zullen zijn'},
                    {'person': 'jullie', 'conjugation': 'zullen zijn'},
                    {'person': 'zij', 'conjugation': 'zullen zijn'},
                ]
            },
            {
                'dutchName': 'Voorwaardelijke Wijs',
                'englishName': 'Conditional',
                'forms': [
                    {'person': 'ik', 'conjugation': 'zou zijn'},
                    {'person': 'je/jij', 'conjugation': 'zou zijn'},
                    {'person': 'hij/zij/het', 'conjugation': 'zou zijn'},
                    {'person': 'wij', 'conjugation': 'zouden zijn'},
                    {'person': 'jullie', 'conjugation': 'zouden zijn'},
                    {'person': 'zij', 'conjugation': 'zouden zijn'},
                ]
            }
        ],
        'examples': [
            {'dutch': 'Ik ben een student.', 'english': 'I am a student.', 'tense': 'Present'},
            {'dutch': 'Zij was in Amsterdam gisteren.', 'english': 'She was in Amsterdam yesterday.', 'tense': 'Simple Past'},
            {'dutch': 'We zijn naar het strand geweest.', 'english': 'We have been to the beach.', 'tense': 'Present Perfect'},
            {'dutch': 'Zij zal morgen hier zijn.', 'english': 'She will be here tomorrow.', 'tense': 'Future Simple'}
        ]
    },
    'hebben': {
        'infinitive': 'hebben',
        'englishTranslation': 'to have',
        'verbType': 'irregular',
        'tenses': [
            {
                'dutchName': 'Tegenwoordige Tijd',
                'englishName': 'Present',
                'forms': [
                    {'person': 'ik', 'conjugation': 'heb'},
                    {'person': 'je/jij', 'conjugation': 'hebt'},
                    {'person': 'hij/zij/het', 'conjugation': 'heeft'},
                    {'person': 'wij', 'conjugation': 'hebben'},
                    {'person': 'jullie', 'conjugation': 'hebben'},
                    {'person': 'zij', 'conjugation': 'hebben'},
                ]
            },
            {
                'dutchName': 'Onvoltooid Verleden Tijd',
                'englishName': 'Simple Past',
                'forms': [
                    {'person': 'ik', 'conjugation': 'had'},
                    {'person': 'je/jij', 'conjugation': 'had'},
                    {'person': 'hij/zij/het', 'conjugation': 'had'},
                    {'person': 'wij', 'conjugation': 'hadden'},
                    {'person': 'jullie', 'conjugation': 'hadden'},
                    {'person': 'zij', 'conjugation': 'hadden'},
                ]
            },
            {
                'dutchName': 'Voltooid Tegenwoordige Tijd',
                'englishName': 'Present Perfect',
                'forms': [
                    {'person': 'ik', 'conjugation': 'heb gehad'},
                    {'person': 'je/jij', 'conjugation': 'hebt gehad'},
                    {'person': 'hij/zij/het', 'conjugation': 'heeft gehad'},
                    {'person': 'wij', 'conjugation': 'hebben gehad'},
                    {'person': 'jullie', 'conjugation': 'hebben gehad'},
                    {'person': 'zij', 'conjugation': 'hebben gehad'},
                ]
            },
            {
                'dutchName': 'Voltooid Verleden Tijd',
                'englishName': 'Past Perfect',
                'forms': [
                    {'person': 'ik', 'conjugation': 'had gehad'},
                    {'person': 'je/jij', 'conjugation': 'had gehad'},
                    {'person': 'hij/zij/het', 'conjugation': 'had gehad'},
                    {'person': 'wij', 'conjugation': 'hadden gehad'},
                    {'person': 'jullie', 'conjugation': 'hadden gehad'},
                    {'person': 'zij', 'conjugation': 'hadden gehad'},
                ]
            },
            {
                'dutchName': 'Toekomende Tijd',
                'englishName': 'Future Simple',
                'forms': [
                    {'person': 'ik', 'conjugation': 'zal hebben'},
                    {'person': 'je/jij', 'conjugation': 'zal hebben'},
                    {'person': 'hij/zij/het', 'conjugation': 'zal hebben'},
                    {'person': 'wij', 'conjugation': 'zullen hebben'},
                    {'person': 'jullie', 'conjugation': 'zullen hebben'},
                    {'person': 'zij', 'conjugation': 'zullen hebben'},
                ]
            },
            {
                'dutchName': 'Voorwaardelijke Wijs',
                'englishName': 'Conditional',
                'forms': [
                    {'person': 'ik', 'conjugation': 'zou hebben'},
                    {'person': 'je/jij', 'conjugation': 'zou hebben'},
                    {'person': 'hij/zij/het', 'conjugation': 'zou hebben'},
                    {'person': 'wij', 'conjugation': 'zouden hebben'},
                    {'person': 'jullie', 'conjugation': 'zouden hebben'},
                    {'person': 'zij', 'conjugation': 'zouden hebben'},
                ]
            }
        ],
        'examples': [
            {'dutch': 'Ik heb een boek.', 'english': 'I have a book.', 'tense': 'Present'},
            {'dutch': 'Hij had veel geld.', 'english': 'He had a lot of money.', 'tense': 'Simple Past'},
            {'dutch': 'Ze hebben het huis gekocht.', 'english': 'They have bought the house.', 'tense': 'Present Perfect'},
            {'dutch': 'Ik zal twee katten hebben.', 'english': 'I will have two cats.', 'tense': 'Future Simple'}
        ]
    },
    'gaan': {
        'infinitive': 'gaan',
        'englishTranslation': 'to go',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'ga'},
                {'person': 'je/jij', 'conjugation': 'gaat'},
                {'person': 'hij/zij/het', 'conjugation': 'gaat'},
                {'person': 'wij', 'conjugation': 'gaan'},
                {'person': 'jullie', 'conjugation': 'gaan'},
                {'person': 'zij', 'conjugation': 'gaan'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'ging'},
                {'person': 'je/jij', 'conjugation': 'ging'},
                {'person': 'hij/zij/het', 'conjugation': 'ging'},
                {'person': 'wij', 'conjugation': 'gingen'},
                {'person': 'jullie', 'conjugation': 'gingen'},
                {'person': 'zij', 'conjugation': 'gingen'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'ben gegaan'},
                {'person': 'je/jij', 'conjugation': 'bent gegaan'},
                {'person': 'hij/zij/het', 'conjugation': 'is gegaan'},
                {'person': 'wij', 'conjugation': 'zijn gegaan'},
                {'person': 'jullie', 'conjugation': 'zijn gegaan'},
                {'person': 'zij', 'conjugation': 'zijn gegaan'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'was gegaan'},
                {'person': 'je/jij', 'conjugation': 'was gegaan'},
                {'person': 'hij/zij/het', 'conjugation': 'was gegaan'},
                {'person': 'wij', 'conjugation': 'waren gegaan'},
                {'person': 'jullie', 'conjugation': 'waren gegaan'},
                {'person': 'zij', 'conjugation': 'waren gegaan'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal gaan'},
                {'person': 'je/jij', 'conjugation': 'zal gaan'},
                {'person': 'hij/zij/het', 'conjugation': 'zal gaan'},
                {'person': 'wij', 'conjugation': 'zullen gaan'},
                {'person': 'jullie', 'conjugation': 'zullen gaan'},
                {'person': 'zij', 'conjugation': 'zullen gaan'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou gaan'},
                {'person': 'je/jij', 'conjugation': 'zou gaan'},
                {'person': 'hij/zij/het', 'conjugation': 'zou gaan'},
                {'person': 'wij', 'conjugation': 'zouden gaan'},
                {'person': 'jullie', 'conjugation': 'zouden gaan'},
                {'person': 'zij', 'conjugation': 'zouden gaan'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik ga naar school.', 'english': 'I go to school.', 'tense': 'Present'},
            {'dutch': 'We gingen naar het park.', 'english': 'We went to the park.', 'tense': 'Simple Past'},
            {'dutch': 'Hij is naar Parijs gegaan.', 'english': 'He has gone to Paris.', 'tense': 'Present Perfect'},
            {'dutch': 'Zij zal naar Amsterdam gaan.', 'english': 'She will go to Amsterdam.', 'tense': 'Future Simple'}
        ]
    },
    'doen': {
        'infinitive': 'doen',
        'englishTranslation': 'to do',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'doe'},
                {'person': 'je/jij', 'conjugation': 'doet'},
                {'person': 'hij/zij/het', 'conjugation': 'doet'},
                {'person': 'wij', 'conjugation': 'doen'},
                {'person': 'jullie', 'conjugation': 'doen'},
                {'person': 'zij', 'conjugation': 'doen'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'deed'},
                {'person': 'je/jij', 'conjugation': 'deed'},
                {'person': 'hij/zij/het', 'conjugation': 'deed'},
                {'person': 'wij', 'conjugation': 'deden'},
                {'person': 'jullie', 'conjugation': 'deden'},
                {'person': 'zij', 'conjugation': 'deden'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gedaan'},
                {'person': 'je/jij', 'conjugation': 'hebt gedaan'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gedaan'},
                {'person': 'wij', 'conjugation': 'hebben gedaan'},
                {'person': 'jullie', 'conjugation': 'hebben gedaan'},
                {'person': 'zij', 'conjugation': 'hebben gedaan'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gedaan'},
                {'person': 'je/jij', 'conjugation': 'had gedaan'},
                {'person': 'hij/zij/het', 'conjugation': 'had gedaan'},
                {'person': 'wij', 'conjugation': 'hadden gedaan'},
                {'person': 'jullie', 'conjugation': 'hadden gedaan'},
                {'person': 'zij', 'conjugation': 'hadden gedaan'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal doen'},
                {'person': 'je/jij', 'conjugation': 'zal doen'},
                {'person': 'hij/zij/het', 'conjugation': 'zal doen'},
                {'person': 'wij', 'conjugation': 'zullen doen'},
                {'person': 'jullie', 'conjugation': 'zullen doen'},
                {'person': 'zij', 'conjugation': 'zullen doen'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou doen'},
                {'person': 'je/jij', 'conjugation': 'zou doen'},
                {'person': 'hij/zij/het', 'conjugation': 'zou doen'},
                {'person': 'wij', 'conjugation': 'zouden doen'},
                {'person': 'jullie', 'conjugation': 'zouden doen'},
                {'person': 'zij', 'conjugation': 'zouden doen'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik doe mijn huiswerk.', 'english': 'I do my homework.', 'tense': 'Present'},
            {'dutch': 'Ze deden hun best.', 'english': 'They did their best.', 'tense': 'Simple Past'},
            {'dutch': 'Wat heb je gedaan?', 'english': 'What have you done?', 'tense': 'Present Perfect'},
            {'dutch': 'Ik zal het doen.', 'english': 'I will do it.', 'tense': 'Future Simple'}
        ]
    },
    'maken': {
        'infinitive': 'maken',
        'englishTranslation': 'to make',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'maak'},
                {'person': 'je/jij', 'conjugation': 'maakt'},
                {'person': 'hij/zij/het', 'conjugation': 'maakt'},
                {'person': 'wij', 'conjugation': 'maken'},
                {'person': 'jullie', 'conjugation': 'maken'},
                {'person': 'zij', 'conjugation': 'maken'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'maakte'},
                {'person': 'je/jij', 'conjugation': 'maakte'},
                {'person': 'hij/zij/het', 'conjugation': 'maakte'},
                {'person': 'wij', 'conjugation': 'maakten'},
                {'person': 'jullie', 'conjugation': 'maakten'},
                {'person': 'zij', 'conjugation': 'maakten'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gemaakt'},
                {'person': 'je/jij', 'conjugation': 'hebt gemaakt'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gemaakt'},
                {'person': 'wij', 'conjugation': 'hebben gemaakt'},
                {'person': 'jullie', 'conjugation': 'hebben gemaakt'},
                {'person': 'zij', 'conjugation': 'hebben gemaakt'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gemaakt'},
                {'person': 'je/jij', 'conjugation': 'had gemaakt'},
                {'person': 'hij/zij/het', 'conjugation': 'had gemaakt'},
                {'person': 'wij', 'conjugation': 'hadden gemaakt'},
                {'person': 'jullie', 'conjugation': 'hadden gemaakt'},
                {'person': 'zij', 'conjugation': 'hadden gemaakt'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal maken'},
                {'person': 'je/jij', 'conjugation': 'zal maken'},
                {'person': 'hij/zij/het', 'conjugation': 'zal maken'},
                {'person': 'wij', 'conjugation': 'zullen maken'},
                {'person': 'jullie', 'conjugation': 'zullen maken'},
                {'person': 'zij', 'conjugation': 'zullen maken'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou maken'},
                {'person': 'je/jij', 'conjugation': 'zou maken'},
                {'person': 'hij/zij/het', 'conjugation': 'zou maken'},
                {'person': 'wij', 'conjugation': 'zouden maken'},
                {'person': 'jullie', 'conjugation': 'zouden maken'},
                {'person': 'zij', 'conjugation': 'zouden maken'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik maak een taart.', 'english': 'I make a cake.', 'tense': 'Present'},
            {'dutch': 'Hij maakte een fout.', 'english': 'He made a mistake.', 'tense': 'Simple Past'},
            {'dutch': 'Ze hebben hun plan gemaakt.', 'english': 'They have made their plan.', 'tense': 'Present Perfect'},
            {'dutch': 'Wat zal je morgen maken?', 'english': 'What will you make tomorrow?', 'tense': 'Future Simple'}
        ]
    },
    'zeggen': {
        'infinitive': 'zeggen',
        'englishTranslation': 'to say',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'zeg'},
                {'person': 'je/jij', 'conjugation': 'zegt'},
                {'person': 'hij/zij/het', 'conjugation': 'zegt'},
                {'person': 'wij', 'conjugation': 'zeggen'},
                {'person': 'jullie', 'conjugation': 'zeggen'},
                {'person': 'zij', 'conjugation': 'zeggen'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'zei'},
                {'person': 'je/jij', 'conjugation': 'zei'},
                {'person': 'hij/zij/het', 'conjugation': 'zei'},
                {'person': 'wij', 'conjugation': 'zeiden'},
                {'person': 'jullie', 'conjugation': 'zeiden'},
                {'person': 'zij', 'conjugation': 'zeiden'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gezegd'},
                {'person': 'je/jij', 'conjugation': 'hebt gezegd'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gezegd'},
                {'person': 'wij', 'conjugation': 'hebben gezegd'},
                {'person': 'jullie', 'conjugation': 'hebben gezegd'},
                {'person': 'zij', 'conjugation': 'hebben gezegd'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gezegd'},
                {'person': 'je/jij', 'conjugation': 'had gezegd'},
                {'person': 'hij/zij/het', 'conjugation': 'had gezegd'},
                {'person': 'wij', 'conjugation': 'hadden gezegd'},
                {'person': 'jullie', 'conjugation': 'hadden gezegd'},
                {'person': 'zij', 'conjugation': 'hadden gezegd'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal zeggen'},
                {'person': 'je/jij', 'conjugation': 'zal zeggen'},
                {'person': 'hij/zij/het', 'conjugation': 'zal zeggen'},
                {'person': 'wij', 'conjugation': 'zullen zeggen'},
                {'person': 'jullie', 'conjugation': 'zullen zeggen'},
                {'person': 'zij', 'conjugation': 'zullen zeggen'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou zeggen'},
                {'person': 'je/jij', 'conjugation': 'zou zeggen'},
                {'person': 'hij/zij/het', 'conjugation': 'zou zeggen'},
                {'person': 'wij', 'conjugation': 'zouden zeggen'},
                {'person': 'jullie', 'conjugation': 'zouden zeggen'},
                {'person': 'zij', 'conjugation': 'zouden zeggen'},
            ]},
        ],
        'examples': [
            {'dutch': 'Wat zeg je?', 'english': 'What do you say?', 'tense': 'Present'},
            {'dutch': 'Hij zei het waarheid.', 'english': 'He said the truth.', 'tense': 'Simple Past'},
            {'dutch': 'Ze hebben alles gezegd.', 'english': 'They have said everything.', 'tense': 'Present Perfect'},
            {'dutch': 'Ik zal je de waarheid zeggen.', 'english': 'I will tell you the truth.', 'tense': 'Future Simple'}
        ]
    },
    'kunnen': {
        'infinitive': 'kunnen',
        'englishTranslation': 'can, to be able to',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'kan'},
                {'person': 'je/jij', 'conjugation': 'kunt'},
                {'person': 'hij/zij/het', 'conjugation': 'kan'},
                {'person': 'wij', 'conjugation': 'kunnen'},
                {'person': 'jullie', 'conjugation': 'kunnen'},
                {'person': 'zij', 'conjugation': 'kunnen'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'kon'},
                {'person': 'je/jij', 'conjugation': 'kon'},
                {'person': 'hij/zij/het', 'conjugation': 'kon'},
                {'person': 'wij', 'conjugation': 'konden'},
                {'person': 'jullie', 'conjugation': 'konden'},
                {'person': 'zij', 'conjugation': 'konden'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gekund'},
                {'person': 'je/jij', 'conjugation': 'hebt gekund'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gekund'},
                {'person': 'wij', 'conjugation': 'hebben gekund'},
                {'person': 'jullie', 'conjugation': 'hebben gekund'},
                {'person': 'zij', 'conjugation': 'hebben gekund'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gekund'},
                {'person': 'je/jij', 'conjugation': 'had gekund'},
                {'person': 'hij/zij/het', 'conjugation': 'had gekund'},
                {'person': 'wij', 'conjugation': 'hadden gekund'},
                {'person': 'jullie', 'conjugation': 'hadden gekund'},
                {'person': 'zij', 'conjugation': 'hadden gekund'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal kunnen'},
                {'person': 'je/jij', 'conjugation': 'zal kunnen'},
                {'person': 'hij/zij/het', 'conjugation': 'zal kunnen'},
                {'person': 'wij', 'conjugation': 'zullen kunnen'},
                {'person': 'jullie', 'conjugation': 'zullen kunnen'},
                {'person': 'zij', 'conjugation': 'zullen kunnen'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou kunnen'},
                {'person': 'je/jij', 'conjugation': 'zou kunnen'},
                {'person': 'hij/zij/het', 'conjugation': 'zou kunnen'},
                {'person': 'wij', 'conjugation': 'zouden kunnen'},
                {'person': 'jullie', 'conjugation': 'zouden kunnen'},
                {'person': 'zij', 'conjugation': 'zouden kunnen'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik kan Nederlands spreken.', 'english': 'I can speak Dutch.', 'tense': 'Present'},
            {'dutch': 'Hij kon goed zwemmen.', 'english': 'He could swim well.', 'tense': 'Simple Past'},
            {'dutch': 'Ze hebben het kunnen doen.', 'english': 'They could do it.', 'tense': 'Present Perfect'},
            {'dutch': 'Je zal het kunnen leren.', 'english': 'You will be able to learn it.', 'tense': 'Future Simple'}
        ]
    },
    'willen': {
        'infinitive': 'willen',
        'englishTranslation': 'to want',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'wil'},
                {'person': 'je/jij', 'conjugation': 'wilt'},
                {'person': 'hij/zij/het', 'conjugation': 'wil'},
                {'person': 'wij', 'conjugation': 'willen'},
                {'person': 'jullie', 'conjugation': 'willen'},
                {'person': 'zij', 'conjugation': 'willen'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'wilde'},
                {'person': 'je/jij', 'conjugation': 'wilde'},
                {'person': 'hij/zij/het', 'conjugation': 'wilde'},
                {'person': 'wij', 'conjugation': 'wilden'},
                {'person': 'jullie', 'conjugation': 'wilden'},
                {'person': 'zij', 'conjugation': 'wilden'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gewild'},
                {'person': 'je/jij', 'conjugation': 'hebt gewild'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gewild'},
                {'person': 'wij', 'conjugation': 'hebben gewild'},
                {'person': 'jullie', 'conjugation': 'hebben gewild'},
                {'person': 'zij', 'conjugation': 'hebben gewild'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gewild'},
                {'person': 'je/jij', 'conjugation': 'had gewild'},
                {'person': 'hij/zij/het', 'conjugation': 'had gewild'},
                {'person': 'wij', 'conjugation': 'hadden gewild'},
                {'person': 'jullie', 'conjugation': 'hadden gewild'},
                {'person': 'zij', 'conjugation': 'hadden gewild'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal willen'},
                {'person': 'je/jij', 'conjugation': 'zal willen'},
                {'person': 'hij/zij/het', 'conjugation': 'zal willen'},
                {'person': 'wij', 'conjugation': 'zullen willen'},
                {'person': 'jullie', 'conjugation': 'zullen willen'},
                {'person': 'zij', 'conjugation': 'zullen willen'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou willen'},
                {'person': 'je/jij', 'conjugation': 'zou willen'},
                {'person': 'hij/zij/het', 'conjugation': 'zou willen'},
                {'person': 'wij', 'conjugation': 'zouden willen'},
                {'person': 'jullie', 'conjugation': 'zouden willen'},
                {'person': 'zij', 'conjugation': 'zouden willen'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik wil koffie.', 'english': 'I want coffee.', 'tense': 'Present'},
            {'dutch': 'Ze wilde graag naar huis.', 'english': 'She wanted to go home.', 'tense': 'Simple Past'},
            {'dutch': 'We hebben dit willen doen.', 'english': 'We wanted to do this.', 'tense': 'Present Perfect'},
            {'dutch': 'Wat zal je willen eten?', 'english': 'What will you want to eat?', 'tense': 'Future Simple'}
        ]
    },
    'moeten': {
        'infinitive': 'moeten',
        'englishTranslation': 'must, to have to',
        'verbType': 'irregular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'moet'},
                {'person': 'je/jij', 'conjugation': 'moet'},
                {'person': 'hij/zij/het', 'conjugation': 'moet'},
                {'person': 'wij', 'conjugation': 'moeten'},
                {'person': 'jullie', 'conjugation': 'moeten'},
                {'person': 'zij', 'conjugation': 'moeten'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'moest'},
                {'person': 'je/jij', 'conjugation': 'moest'},
                {'person': 'hij/zij/het', 'conjugation': 'moest'},
                {'person': 'wij', 'conjugation': 'moesten'},
                {'person': 'jullie', 'conjugation': 'moesten'},
                {'person': 'zij', 'conjugation': 'moesten'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gemoeten'},
                {'person': 'je/jij', 'conjugation': 'hebt gemoeten'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gemoeten'},
                {'person': 'wij', 'conjugation': 'hebben gemoeten'},
                {'person': 'jullie', 'conjugation': 'hebben gemoeten'},
                {'person': 'zij', 'conjugation': 'hebben gemoeten'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gemoeten'},
                {'person': 'je/jij', 'conjugation': 'had gemoeten'},
                {'person': 'hij/zij/het', 'conjugation': 'had gemoeten'},
                {'person': 'wij', 'conjugation': 'hadden gemoeten'},
                {'person': 'jullie', 'conjugation': 'hadden gemoeten'},
                {'person': 'zij', 'conjugation': 'hadden gemoeten'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal moeten'},
                {'person': 'je/jij', 'conjugation': 'zal moeten'},
                {'person': 'hij/zij/het', 'conjugation': 'zal moeten'},
                {'person': 'wij', 'conjugation': 'zullen moeten'},
                {'person': 'jullie', 'conjugation': 'zullen moeten'},
                {'person': 'zij', 'conjugation': 'zullen moeten'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou moeten'},
                {'person': 'je/jij', 'conjugation': 'zou moeten'},
                {'person': 'hij/zij/het', 'conjugation': 'zou moeten'},
                {'person': 'wij', 'conjugation': 'zouden moeten'},
                {'person': 'jullie', 'conjugation': 'zouden moeten'},
                {'person': 'zij', 'conjugation': 'zouden moeten'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik moet werken.', 'english': 'I must work.', 'tense': 'Present'},
            {'dutch': 'Je moest je huiswerk doen.', 'english': 'You had to do your homework.', 'tense': 'Simple Past'},
            {'dutch': 'Ze hebben geld moeten lenen.', 'english': 'They had to borrow money.', 'tense': 'Present Perfect'},
            {'dutch': 'Je zal voorzichtig moeten zijn.', 'english': 'You will have to be careful.', 'tense': 'Future Simple'}
        ]
    },
    'kijken': {
        'infinitive': 'kijken',
        'englishTranslation': 'to look, to watch',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'kijk'},
                {'person': 'je/jij', 'conjugation': 'kijkt'},
                {'person': 'hij/zij/het', 'conjugation': 'kijkt'},
                {'person': 'wij', 'conjugation': 'kijken'},
                {'person': 'jullie', 'conjugation': 'kijken'},
                {'person': 'zij', 'conjugation': 'kijken'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'keek'},
                {'person': 'je/jij', 'conjugation': 'keek'},
                {'person': 'hij/zij/het', 'conjugation': 'keek'},
                {'person': 'wij', 'conjugation': 'keken'},
                {'person': 'jullie', 'conjugation': 'keken'},
                {'person': 'zij', 'conjugation': 'keken'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gekeken'},
                {'person': 'je/jij', 'conjugation': 'hebt gekeken'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gekeken'},
                {'person': 'wij', 'conjugation': 'hebben gekeken'},
                {'person': 'jullie', 'conjugation': 'hebben gekeken'},
                {'person': 'zij', 'conjugation': 'hebben gekeken'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gekeken'},
                {'person': 'je/jij', 'conjugation': 'had gekeken'},
                {'person': 'hij/zij/het', 'conjugation': 'had gekeken'},
                {'person': 'wij', 'conjugation': 'hadden gekeken'},
                {'person': 'jullie', 'conjugation': 'hadden gekeken'},
                {'person': 'zij', 'conjugation': 'hadden gekeken'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal kijken'},
                {'person': 'je/jij', 'conjugation': 'zal kijken'},
                {'person': 'hij/zij/het', 'conjugation': 'zal kijken'},
                {'person': 'wij', 'conjugation': 'zullen kijken'},
                {'person': 'jullie', 'conjugation': 'zullen kijken'},
                {'person': 'zij', 'conjugation': 'zullen kijken'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou kijken'},
                {'person': 'je/jij', 'conjugation': 'zou kijken'},
                {'person': 'hij/zij/het', 'conjugation': 'zou kijken'},
                {'person': 'wij', 'conjugation': 'zouden kijken'},
                {'person': 'jullie', 'conjugation': 'zouden kijken'},
                {'person': 'zij', 'conjugation': 'zouden kijken'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik kijk naar de film.', 'english': 'I watch the movie.', 'tense': 'Present'},
            {'dutch': 'Ze keek naar buiten.', 'english': 'She looked outside.', 'tense': 'Simple Past'},
            {'dutch': 'We hebben het voetbalspel gekeken.', 'english': 'We have watched the football game.', 'tense': 'Present Perfect'},
            {'dutch': 'Wat zal je vanuit morgen kijken?', 'english': 'What will you watch from tomorrow?', 'tense': 'Future Simple'}
        ]
    },
    'spreken': {
        'infinitive': 'spreken',
        'englishTranslation': 'to speak',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'spreek'},
                {'person': 'je/jij', 'conjugation': 'spreekt'},
                {'person': 'hij/zij/het', 'conjugation': 'spreekt'},
                {'person': 'wij', 'conjugation': 'spreken'},
                {'person': 'jullie', 'conjugation': 'spreken'},
                {'person': 'zij', 'conjugation': 'spreken'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'sprak'},
                {'person': 'je/jij', 'conjugation': 'sprak'},
                {'person': 'hij/zij/het', 'conjugation': 'sprak'},
                {'person': 'wij', 'conjugation': 'spraken'},
                {'person': 'jullie', 'conjugation': 'spraken'},
                {'person': 'zij', 'conjugation': 'spraken'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gesproken'},
                {'person': 'je/jij', 'conjugation': 'hebt gesproken'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gesproken'},
                {'person': 'wij', 'conjugation': 'hebben gesproken'},
                {'person': 'jullie', 'conjugation': 'hebben gesproken'},
                {'person': 'zij', 'conjugation': 'hebben gesproken'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gesproken'},
                {'person': 'je/jij', 'conjugation': 'had gesproken'},
                {'person': 'hij/zij/het', 'conjugation': 'had gesproken'},
                {'person': 'wij', 'conjugation': 'hadden gesproken'},
                {'person': 'jullie', 'conjugation': 'hadden gesproken'},
                {'person': 'zij', 'conjugation': 'hadden gesproken'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal spreken'},
                {'person': 'je/jij', 'conjugation': 'zal spreken'},
                {'person': 'hij/zij/het', 'conjugation': 'zal spreken'},
                {'person': 'wij', 'conjugation': 'zullen spreken'},
                {'person': 'jullie', 'conjugation': 'zullen spreken'},
                {'person': 'zij', 'conjugation': 'zullen spreken'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou spreken'},
                {'person': 'je/jij', 'conjugation': 'zou spreken'},
                {'person': 'hij/zij/het', 'conjugation': 'zou spreken'},
                {'person': 'wij', 'conjugation': 'zouden spreken'},
                {'person': 'jullie', 'conjugation': 'zouden spreken'},
                {'person': 'zij', 'conjugation': 'zouden spreken'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik spreek Nederlands.', 'english': 'I speak Dutch.', 'tense': 'Present'},
            {'dutch': 'Ze spraken zachtjes.', 'english': 'They spoke softly.', 'tense': 'Simple Past'},
            {'dutch': 'We hebben daarover gesproken.', 'english': 'We have spoken about that.', 'tense': 'Present Perfect'},
            {'dutch': 'Zal je met hem spreken?', 'english': 'Will you speak with him?', 'tense': 'Future Simple'}
        ]
    },
    'luisteren': {
        'infinitive': 'luisteren',
        'englishTranslation': 'to listen',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'luister'},
                {'person': 'je/jij', 'conjugation': 'luistert'},
                {'person': 'hij/zij/het', 'conjugation': 'luistert'},
                {'person': 'wij', 'conjugation': 'luisteren'},
                {'person': 'jullie', 'conjugation': 'luisteren'},
                {'person': 'zij', 'conjugation': 'luisteren'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'luisterde'},
                {'person': 'je/jij', 'conjugation': 'luisterde'},
                {'person': 'hij/zij/het', 'conjugation': 'luisterde'},
                {'person': 'wij', 'conjugation': 'luisterden'},
                {'person': 'jullie', 'conjugation': 'luisterden'},
                {'person': 'zij', 'conjugation': 'luisterden'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb geluisterd'},
                {'person': 'je/jij', 'conjugation': 'hebt geluisterd'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft geluisterd'},
                {'person': 'wij', 'conjugation': 'hebben geluisterd'},
                {'person': 'jullie', 'conjugation': 'hebben geluisterd'},
                {'person': 'zij', 'conjugation': 'hebben geluisterd'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had geluisterd'},
                {'person': 'je/jij', 'conjugation': 'had geluisterd'},
                {'person': 'hij/zij/het', 'conjugation': 'had geluisterd'},
                {'person': 'wij', 'conjugation': 'hadden geluisterd'},
                {'person': 'jullie', 'conjugation': 'hadden geluisterd'},
                {'person': 'zij', 'conjugation': 'hadden geluisterd'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal luisteren'},
                {'person': 'je/jij', 'conjugation': 'zal luisteren'},
                {'person': 'hij/zij/het', 'conjugation': 'zal luisteren'},
                {'person': 'wij', 'conjugation': 'zullen luisteren'},
                {'person': 'jullie', 'conjugation': 'zullen luisteren'},
                {'person': 'zij', 'conjugation': 'zullen luisteren'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou luisteren'},
                {'person': 'je/jij', 'conjugation': 'zou luisteren'},
                {'person': 'hij/zij/het', 'conjugation': 'zou luisteren'},
                {'person': 'wij', 'conjugation': 'zouden luisteren'},
                {'person': 'jullie', 'conjugation': 'zouden luisteren'},
                {'person': 'zij', 'conjugation': 'zouden luisteren'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik luister naar muziek.', 'english': 'I listen to music.', 'tense': 'Present'},
            {'dutch': 'Ze luisterde naar zijn advies.', 'english': 'She listened to his advice.', 'tense': 'Simple Past'},
            {'dutch': 'Hebben jullie goed geluisterd?', 'english': 'Have you listened well?', 'tense': 'Present Perfect'},
            {'dutch': 'We zullen aandachtig luisteren.', 'english': 'We will listen carefully.', 'tense': 'Future Simple'}
        ]
    },
    'werken': {
        'infinitive': 'werken',
        'englishTranslation': 'to work',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'werk'},
                {'person': 'je/jij', 'conjugation': 'werkt'},
                {'person': 'hij/zij/het', 'conjugation': 'werkt'},
                {'person': 'wij', 'conjugation': 'werken'},
                {'person': 'jullie', 'conjugation': 'werken'},
                {'person': 'zij', 'conjugation': 'werken'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'werkte'},
                {'person': 'je/jij', 'conjugation': 'werkte'},
                {'person': 'hij/zij/het', 'conjugation': 'werkte'},
                {'person': 'wij', 'conjugation': 'werkten'},
                {'person': 'jullie', 'conjugation': 'werkten'},
                {'person': 'zij', 'conjugation': 'werkten'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gewerkt'},
                {'person': 'je/jij', 'conjugation': 'hebt gewerkt'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gewerkt'},
                {'person': 'wij', 'conjugation': 'hebben gewerkt'},
                {'person': 'jullie', 'conjugation': 'hebben gewerkt'},
                {'person': 'zij', 'conjugation': 'hebben gewerkt'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gewerkt'},
                {'person': 'je/jij', 'conjugation': 'had gewerkt'},
                {'person': 'hij/zij/het', 'conjugation': 'had gewerkt'},
                {'person': 'wij', 'conjugation': 'hadden gewerkt'},
                {'person': 'jullie', 'conjugation': 'hadden gewerkt'},
                {'person': 'zij', 'conjugation': 'hadden gewerkt'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal werken'},
                {'person': 'je/jij', 'conjugation': 'zal werken'},
                {'person': 'hij/zij/het', 'conjugation': 'zal werken'},
                {'person': 'wij', 'conjugation': 'zullen werken'},
                {'person': 'jullie', 'conjugation': 'zullen werken'},
                {'person': 'zij', 'conjugation': 'zullen werken'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou werken'},
                {'person': 'je/jij', 'conjugation': 'zou werken'},
                {'person': 'hij/zij/het', 'conjugation': 'zou werken'},
                {'person': 'wij', 'conjugation': 'zouden werken'},
                {'person': 'jullie', 'conjugation': 'zouden werken'},
                {'person': 'zij', 'conjugation': 'zouden werken'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik werk als programmeur.', 'english': 'I work as a programmer.', 'tense': 'Present'},
            {'dutch': 'Ze werkten hard op het project.', 'english': 'They worked hard on the project.', 'tense': 'Simple Past'},
            {'dutch': 'We hebben samen aan dit gewerkt.', 'english': 'We have worked on this together.', 'tense': 'Present Perfect'},
            {'dutch': 'Morgen zal ik niet werken.', 'english': 'Tomorrow I will not work.', 'tense': 'Future Simple'}
        ]
    },
    'wonen': {
        'infinitive': 'wonen',
        'englishTranslation': 'to live, to dwell',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'woon'},
                {'person': 'je/jij', 'conjugation': 'woont'},
                {'person': 'hij/zij/het', 'conjugation': 'woont'},
                {'person': 'wij', 'conjugation': 'wonen'},
                {'person': 'jullie', 'conjugation': 'wonen'},
                {'person': 'zij', 'conjugation': 'wonen'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'woonde'},
                {'person': 'je/jij', 'conjugation': 'woonde'},
                {'person': 'hij/zij/het', 'conjugation': 'woonde'},
                {'person': 'wij', 'conjugation': 'woondes'},
                {'person': 'jullie', 'conjugation': 'woondes'},
                {'person': 'zij', 'conjugation': 'woondes'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gewoond'},
                {'person': 'je/jij', 'conjugation': 'hebt gewoond'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gewoond'},
                {'person': 'wij', 'conjugation': 'hebben gewoond'},
                {'person': 'jullie', 'conjugation': 'hebben gewoond'},
                {'person': 'zij', 'conjugation': 'hebben gewoond'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gewoond'},
                {'person': 'je/jij', 'conjugation': 'had gewoond'},
                {'person': 'hij/zij/het', 'conjugation': 'had gewoond'},
                {'person': 'wij', 'conjugation': 'hadden gewoond'},
                {'person': 'jullie', 'conjugation': 'hadden gewoond'},
                {'person': 'zij', 'conjugation': 'hadden gewoond'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal wonen'},
                {'person': 'je/jij', 'conjugation': 'zal wonen'},
                {'person': 'hij/zij/het', 'conjugation': 'zal wonen'},
                {'person': 'wij', 'conjugation': 'zullen wonen'},
                {'person': 'jullie', 'conjugation': 'zullen wonen'},
                {'person': 'zij', 'conjugation': 'zullen wonen'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou wonen'},
                {'person': 'je/jij', 'conjugation': 'zou wonen'},
                {'person': 'hij/zij/het', 'conjugation': 'zou wonen'},
                {'person': 'wij', 'conjugation': 'zouden wonen'},
                {'person': 'jullie', 'conjugation': 'zouden wonen'},
                {'person': 'zij', 'conjugation': 'zouden wonen'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik woon in Amsterdam.', 'english': 'I live in Amsterdam.', 'tense': 'Present'},
            {'dutch': 'Ze woonde voorheen in Parijs.', 'english': 'She previously lived in Paris.', 'tense': 'Simple Past'},
            {'dutch': 'We hebben lange tijd hier gewoond.', 'english': 'We have lived here for a long time.', 'tense': 'Present Perfect'},
            {'dutch': 'In de toekomst zal ik in Nederland wonen.', 'english': 'In the future, I will live in the Netherlands.', 'tense': 'Future Simple'}
        ]
    },
    'eten': {
        'infinitive': 'eten',
        'englishTranslation': 'to eat',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'eet'},
                {'person': 'je/jij', 'conjugation': 'eet'},
                {'person': 'hij/zij/het', 'conjugation': 'eet'},
                {'person': 'wij', 'conjugation': 'eten'},
                {'person': 'jullie', 'conjugation': 'eten'},
                {'person': 'zij', 'conjugation': 'eten'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'at'},
                {'person': 'je/jij', 'conjugation': 'at'},
                {'person': 'hij/zij/het', 'conjugation': 'at'},
                {'person': 'wij', 'conjugation': 'aten'},
                {'person': 'jullie', 'conjugation': 'aten'},
                {'person': 'zij', 'conjugation': 'aten'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gegeten'},
                {'person': 'je/jij', 'conjugation': 'hebt gegeten'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gegeten'},
                {'person': 'wij', 'conjugation': 'hebben gegeten'},
                {'person': 'jullie', 'conjugation': 'hebben gegeten'},
                {'person': 'zij', 'conjugation': 'hebben gegeten'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gegeten'},
                {'person': 'je/jij', 'conjugation': 'had gegeten'},
                {'person': 'hij/zij/het', 'conjugation': 'had gegeten'},
                {'person': 'wij', 'conjugation': 'hadden gegeten'},
                {'person': 'jullie', 'conjugation': 'hadden gegeten'},
                {'person': 'zij', 'conjugation': 'hadden gegeten'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal eten'},
                {'person': 'je/jij', 'conjugation': 'zal eten'},
                {'person': 'hij/zij/het', 'conjugation': 'zal eten'},
                {'person': 'wij', 'conjugation': 'zullen eten'},
                {'person': 'jullie', 'conjugation': 'zullen eten'},
                {'person': 'zij', 'conjugation': 'zullen eten'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou eten'},
                {'person': 'je/jij', 'conjugation': 'zou eten'},
                {'person': 'hij/zij/het', 'conjugation': 'zou eten'},
                {'person': 'wij', 'conjugation': 'zouden eten'},
                {'person': 'jullie', 'conjugation': 'zouden eten'},
                {'person': 'zij', 'conjugation': 'zouden eten'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik eet graag pizza.', 'english': 'I like to eat pizza.', 'tense': 'Present'},
            {'dutch': 'We aten in een restaurants.', 'english': 'We ate in a restaurant.', 'tense': 'Simple Past'},
            {'dutch': 'Heb je al ontbijt gegeten?', 'english': 'Have you already eaten breakfast?', 'tense': 'Present Perfect'},
            {'dutch': 'Wat zul je eten vandaag?', 'english': 'What will you eat today?', 'tense': 'Future Simple'}
        ]
    },
    'drinken': {
        'infinitive': 'drinken',
        'englishTranslation': 'to drink',
        'verbType': 'regular',
        'tenses': [
            {'dutchName': 'Tegenwoordige Tijd', 'englishName': 'Present', 'forms': [
                {'person': 'ik', 'conjugation': 'drink'},
                {'person': 'je/jij', 'conjugation': 'drinkt'},
                {'person': 'hij/zij/het', 'conjugation': 'drinkt'},
                {'person': 'wij', 'conjugation': 'drinken'},
                {'person': 'jullie', 'conjugation': 'drinken'},
                {'person': 'zij', 'conjugation': 'drinken'},
            ]},
            {'dutchName': 'Onvoltooid Verleden Tijd', 'englishName': 'Simple Past', 'forms': [
                {'person': 'ik', 'conjugation': 'dronk'},
                {'person': 'je/jij', 'conjugation': 'dronk'},
                {'person': 'hij/zij/het', 'conjugation': 'dronk'},
                {'person': 'wij', 'conjugation': 'dronken'},
                {'person': 'jullie', 'conjugation': 'dronken'},
                {'person': 'zij', 'conjugation': 'dronken'},
            ]},
            {'dutchName': 'Voltooid Tegenwoordige Tijd', 'englishName': 'Present Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'heb gedronken'},
                {'person': 'je/jij', 'conjugation': 'hebt gedronken'},
                {'person': 'hij/zij/het', 'conjugation': 'heeft gedronken'},
                {'person': 'wij', 'conjugation': 'hebben gedronken'},
                {'person': 'jullie', 'conjugation': 'hebben gedronken'},
                {'person': 'zij', 'conjugation': 'hebben gedronken'},
            ]},
            {'dutchName': 'Voltooid Verleden Tijd', 'englishName': 'Past Perfect', 'forms': [
                {'person': 'ik', 'conjugation': 'had gedronken'},
                {'person': 'je/jij', 'conjugation': 'had gedronken'},
                {'person': 'hij/zij/het', 'conjugation': 'had gedronken'},
                {'person': 'wij', 'conjugation': 'hadden gedronken'},
                {'person': 'jullie', 'conjugation': 'hadden gedronken'},
                {'person': 'zij', 'conjugation': 'hadden gedronken'},
            ]},
            {'dutchName': 'Toekomende Tijd', 'englishName': 'Future Simple', 'forms': [
                {'person': 'ik', 'conjugation': 'zal drinken'},
                {'person': 'je/jij', 'conjugation': 'zal drinken'},
                {'person': 'hij/zij/het', 'conjugation': 'zal drinken'},
                {'person': 'wij', 'conjugation': 'zullen drinken'},
                {'person': 'jullie', 'conjugation': 'zullen drinken'},
                {'person': 'zij', 'conjugation': 'zullen drinken'},
            ]},
            {'dutchName': 'Voorwaardelijke Wijs', 'englishName': 'Conditional', 'forms': [
                {'person': 'ik', 'conjugation': 'zou drinken'},
                {'person': 'je/jij', 'conjugation': 'zou drinken'},
                {'person': 'hij/zij/het', 'conjugation': 'zou drinken'},
                {'person': 'wij', 'conjugation': 'zouden drinken'},
                {'person': 'jullie', 'conjugation': 'zouden drinken'},
                {'person': 'zij', 'conjugation': 'zouden drinken'},
            ]},
        ],
        'examples': [
            {'dutch': 'Ik drink koffie elke ochtend.', 'english': 'I drink coffee every morning.', 'tense': 'Present'},
            {'dutch': 'We dronken water na het sporten.', 'english': 'We drank water after exercising.', 'tense': 'Simple Past'},
            {'dutch': 'Zij heeft veel melk gedronken.', 'english': 'She has drunk a lot of milk.', 'tense': 'Present Perfect'},
            {'dutch': 'Zal je wijn drinken vandaag?', 'english': 'Will you drink wine today?', 'tense': 'Future Simple'}
        ]
    },
}
