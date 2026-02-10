"""Verb conjugation service for Dutch verbs"""
import logging
import asyncio
from typing import List, Optional, Dict, Any
from app.dutch_verbs_database import DUTCH_VERBS_DATABASE

logger = logging.getLogger(__name__)

class VerbConjugationService:
    """Service for conjugating Dutch verbs.
    
    This service provides:
    1. Fast lookup from in-memory database (~15 common verbs)
    2. LLM-based conjugation for unknown verbs via OpenRouter
    3. Automatic fallback when database lookup fails
    """
    
    # Use the external Dutch verbs database
    VERB_DATABASE = DUTCH_VERBS_DATABASE
    
    # Keep the old VERB_DATABASE structure in memory for backwards compatibility
    LEGACY_VERB_DATABASE = {
        'zijn': {
            'infinitive': 'zijn',
            'englishTranslation': 'to be',
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
                {
                    'dutch': 'Ik ben een student.',
                    'english': 'I am a student.',
                    'tense': 'Present'
                },
                {
                    'dutch': 'Zij was in Amsterdam gisteren.',
                    'english': 'She was in Amsterdam yesterday.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'We zijn naar het strand geweest.',
                    'english': 'We have been to the beach.',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Zij zal morgen hier zijn.',
                    'english': 'She will be here tomorrow.',
                    'tense': 'Future Simple'
                }
            ]
        },
        'hebben': {
            'infinitive': 'hebben',
            'englishTranslation': 'to have',
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
                {
                    'dutch': 'Ik heb een boek.',
                    'english': 'I have a book.',
                    'tense': 'Present'
                },
                {
                    'dutch': 'Hij had veel geld.',
                    'english': 'He had a lot of money.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'Ze hebben het huis gekocht.',
                    'english': 'They have bought the house.',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Ik zal twee katten hebben.',
                    'english': 'I will have two cats.',
                    'tense': 'Future Simple'
                }
            ]
        },
        'gaan': {
            'infinitive': 'gaan',
            'englishTranslation': 'to go',
            'tenses': [
                {
                    'dutchName': 'Tegenwoordige Tijd',
                    'englishName': 'Present',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'ga'},
                        {'person': 'je/jij', 'conjugation': 'gaat'},
                        {'person': 'hij/zij/het', 'conjugation': 'gaat'},
                        {'person': 'wij', 'conjugation': 'gaan'},
                        {'person': 'jullie', 'conjugation': 'gaan'},
                        {'person': 'zij', 'conjugation': 'gaan'},
                    ]
                },
                {
                    'dutchName': 'Onvoltooid Verleden Tijd',
                    'englishName': 'Simple Past',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'ging'},
                        {'person': 'je/jij', 'conjugation': 'ging'},
                        {'person': 'hij/zij/het', 'conjugation': 'ging'},
                        {'person': 'wij', 'conjugation': 'gingen'},
                        {'person': 'jullie', 'conjugation': 'gingen'},
                        {'person': 'zij', 'conjugation': 'gingen'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Tegenwoordige Tijd',
                    'englishName': 'Present Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'ben gegaan'},
                        {'person': 'je/jij', 'conjugation': 'bent gegaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'is gegaan'},
                        {'person': 'wij', 'conjugation': 'zijn gegaan'},
                        {'person': 'jullie', 'conjugation': 'zijn gegaan'},
                        {'person': 'zij', 'conjugation': 'zijn gegaan'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Verleden Tijd',
                    'englishName': 'Past Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'was gegaan'},
                        {'person': 'je/jij', 'conjugation': 'was gegaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'was gegaan'},
                        {'person': 'wij', 'conjugation': 'waren gegaan'},
                        {'person': 'jullie', 'conjugation': 'waren gegaan'},
                        {'person': 'zij', 'conjugation': 'waren gegaan'},
                    ]
                },
                {
                    'dutchName': 'Toekomende Tijd',
                    'englishName': 'Future Simple',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zal gaan'},
                        {'person': 'je/jij', 'conjugation': 'zal gaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'zal gaan'},
                        {'person': 'wij', 'conjugation': 'zullen gaan'},
                        {'person': 'jullie', 'conjugation': 'zullen gaan'},
                        {'person': 'zij', 'conjugation': 'zullen gaan'},
                    ]
                },
                {
                    'dutchName': 'Voorwaardelijke Wijs',
                    'englishName': 'Conditional',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zou gaan'},
                        {'person': 'je/jij', 'conjugation': 'zou gaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'zou gaan'},
                        {'person': 'wij', 'conjugation': 'zouden gaan'},
                        {'person': 'jullie', 'conjugation': 'zouden gaan'},
                        {'person': 'zij', 'conjugation': 'zouden gaan'},
                    ]
                }
            ],
            'examples': [
                {
                    'dutch': 'Ik ga naar school.',
                    'english': 'I go to school.',
                    'tense': 'Present'
                },
                {
                    'dutch': 'We gingen naar het park.',
                    'english': 'We went to the park.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'Hij is naar Parijs gegaan.',
                    'english': 'He has gone to Paris.',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Zij zal naar Amsterdam gaan.',
                    'english': 'She will go to Amsterdam.',
                    'tense': 'Future Simple'
                }
            ]
        },
        'doen': {
            'infinitive': 'doen',
            'englishTranslation': 'to do',
            'tenses': [
                {
                    'dutchName': 'Tegenwoordige Tijd',
                    'englishName': 'Present',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'doe'},
                        {'person': 'je/jij', 'conjugation': 'doet'},
                        {'person': 'hij/zij/het', 'conjugation': 'doet'},
                        {'person': 'wij', 'conjugation': 'doen'},
                        {'person': 'jullie', 'conjugation': 'doen'},
                        {'person': 'zij', 'conjugation': 'doen'},
                    ]
                },
                {
                    'dutchName': 'Onvoltooid Verleden Tijd',
                    'englishName': 'Simple Past',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'deed'},
                        {'person': 'je/jij', 'conjugation': 'deed'},
                        {'person': 'hij/zij/het', 'conjugation': 'deed'},
                        {'person': 'wij', 'conjugation': 'deden'},
                        {'person': 'jullie', 'conjugation': 'deden'},
                        {'person': 'zij', 'conjugation': 'deden'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Tegenwoordige Tijd',
                    'englishName': 'Present Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'heb gedaan'},
                        {'person': 'je/jij', 'conjugation': 'hebt gedaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'heeft gedaan'},
                        {'person': 'wij', 'conjugation': 'hebben gedaan'},
                        {'person': 'jullie', 'conjugation': 'hebben gedaan'},
                        {'person': 'zij', 'conjugation': 'hebben gedaan'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Verleden Tijd',
                    'englishName': 'Past Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'had gedaan'},
                        {'person': 'je/jij', 'conjugation': 'had gedaan'},
                        {'person': 'hij/zij/het', 'conjugation': 'had gedaan'},
                        {'person': 'wij', 'conjugation': 'hadden gedaan'},
                        {'person': 'jullie', 'conjugation': 'hadden gedaan'},
                        {'person': 'zij', 'conjugation': 'hadden gedaan'},
                    ]
                },
                {
                    'dutchName': 'Toekomende Tijd',
                    'englishName': 'Future Simple',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zal doen'},
                        {'person': 'je/jij', 'conjugation': 'zal doen'},
                        {'person': 'hij/zij/het', 'conjugation': 'zal doen'},
                        {'person': 'wij', 'conjugation': 'zullen doen'},
                        {'person': 'jullie', 'conjugation': 'zullen doen'},
                        {'person': 'zij', 'conjugation': 'zullen doen'},
                    ]
                },
                {
                    'dutchName': 'Voorwaardelijke Wijs',
                    'englishName': 'Conditional',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zou doen'},
                        {'person': 'je/jij', 'conjugation': 'zou doen'},
                        {'person': 'hij/zij/het', 'conjugation': 'zou doen'},
                        {'person': 'wij', 'conjugation': 'zouden doen'},
                        {'person': 'jullie', 'conjugation': 'zouden doen'},
                        {'person': 'zij', 'conjugation': 'zouden doen'},
                    ]
                }
            ],
            'examples': [
                {
                    'dutch': 'Ik doe mijn huiswerk.',
                    'english': 'I do my homework.',
                    'tense': 'Present'
                },
                {
                    'dutch': 'Ze deden hun best.',
                    'english': 'They did their best.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'Wat heb je gedaan?',
                    'english': 'What have you done?',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Ik zal het doen.',
                    'english': 'I will do it.',
                    'tense': 'Future Simple'
                }
            ]
        },
        'maken': {
            'infinitive': 'maken',
            'englishTranslation': 'to make',
            'tenses': [
                {
                    'dutchName': 'Tegenwoordige Tijd',
                    'englishName': 'Present',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'maak'},
                        {'person': 'je/jij', 'conjugation': 'maakt'},
                        {'person': 'hij/zij/het', 'conjugation': 'maakt'},
                        {'person': 'wij', 'conjugation': 'maken'},
                        {'person': 'jullie', 'conjugation': 'maken'},
                        {'person': 'zij', 'conjugation': 'maken'},
                    ]
                },
                {
                    'dutchName': 'Onvoltooid Verleden Tijd',
                    'englishName': 'Simple Past',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'maakte'},
                        {'person': 'je/jij', 'conjugation': 'maakte'},
                        {'person': 'hij/zij/het', 'conjugation': 'maakte'},
                        {'person': 'wij', 'conjugation': 'maakten'},
                        {'person': 'jullie', 'conjugation': 'maakten'},
                        {'person': 'zij', 'conjugation': 'maakten'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Tegenwoordige Tijd',
                    'englishName': 'Present Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'heb gemaakt'},
                        {'person': 'je/jij', 'conjugation': 'hebt gemaakt'},
                        {'person': 'hij/zij/het', 'conjugation': 'heeft gemaakt'},
                        {'person': 'wij', 'conjugation': 'hebben gemaakt'},
                        {'person': 'jullie', 'conjugation': 'hebben gemaakt'},
                        {'person': 'zij', 'conjugation': 'hebben gemaakt'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Verleden Tijd',
                    'englishName': 'Past Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'had gemaakt'},
                        {'person': 'je/jij', 'conjugation': 'had gemaakt'},
                        {'person': 'hij/zij/het', 'conjugation': 'had gemaakt'},
                        {'person': 'wij', 'conjugation': 'hadden gemaakt'},
                        {'person': 'jullie', 'conjugation': 'hadden gemaakt'},
                        {'person': 'zij', 'conjugation': 'hadden gemaakt'},
                    ]
                },
                {
                    'dutchName': 'Toekomende Tijd',
                    'englishName': 'Future Simple',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zal maken'},
                        {'person': 'je/jij', 'conjugation': 'zal maken'},
                        {'person': 'hij/zij/het', 'conjugation': 'zal maken'},
                        {'person': 'wij', 'conjugation': 'zullen maken'},
                        {'person': 'jullie', 'conjugation': 'zullen maken'},
                        {'person': 'zij', 'conjugation': 'zullen maken'},
                    ]
                },
                {
                    'dutchName': 'Voorwaardelijke Wijs',
                    'englishName': 'Conditional',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zou maken'},
                        {'person': 'je/jij', 'conjugation': 'zou maken'},
                        {'person': 'hij/zij/het', 'conjugation': 'zou maken'},
                        {'person': 'wij', 'conjugation': 'zouden maken'},
                        {'person': 'jullie', 'conjugation': 'zouden maken'},
                        {'person': 'zij', 'conjugation': 'zouden maken'},
                    ]
                }
            ],
            'examples': [
                {
                    'dutch': 'Ik maak een taart.',
                    'english': 'I make a cake.',
                    'tense': 'Present'
                },
                {
                    'dutch': 'Hij maakte een fout.',
                    'english': 'He made a mistake.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'Ze hebben hun plan gemaakt.',
                    'english': 'They have made their plan.',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Wat zal je morgen maken?',
                    'english': 'What will you make tomorrow?',
                    'tense': 'Future Simple'
                }
            ]
        },
        'zeggen': {
            'infinitive': 'zeggen',
            'englishTranslation': 'to say',
            'tenses': [
                {
                    'dutchName': 'Tegenwoordige Tijd',
                    'englishName': 'Present',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zeg'},
                        {'person': 'je/jij', 'conjugation': 'zegt'},
                        {'person': 'hij/zij/het', 'conjugation': 'zegt'},
                        {'person': 'wij', 'conjugation': 'zeggen'},
                        {'person': 'jullie', 'conjugation': 'zeggen'},
                        {'person': 'zij', 'conjugation': 'zeggen'},
                    ]
                },
                {
                    'dutchName': 'Onvoltooid Verleden Tijd',
                    'englishName': 'Simple Past',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zei'},
                        {'person': 'je/jij', 'conjugation': 'zei'},
                        {'person': 'hij/zij/het', 'conjugation': 'zei'},
                        {'person': 'wij', 'conjugation': 'zeiden'},
                        {'person': 'jullie', 'conjugation': 'zeiden'},
                        {'person': 'zij', 'conjugation': 'zeiden'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Tegenwoordige Tijd',
                    'englishName': 'Present Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'heb gezegd'},
                        {'person': 'je/jij', 'conjugation': 'hebt gezegd'},
                        {'person': 'hij/zij/het', 'conjugation': 'heeft gezegd'},
                        {'person': 'wij', 'conjugation': 'hebben gezegd'},
                        {'person': 'jullie', 'conjugation': 'hebben gezegd'},
                        {'person': 'zij', 'conjugation': 'hebben gezegd'},
                    ]
                },
                {
                    'dutchName': 'Voltooid Verleden Tijd',
                    'englishName': 'Past Perfect',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'had gezegd'},
                        {'person': 'je/jij', 'conjugation': 'had gezegd'},
                        {'person': 'hij/zij/het', 'conjugation': 'had gezegd'},
                        {'person': 'wij', 'conjugation': 'hadden gezegd'},
                        {'person': 'jullie', 'conjugation': 'hadden gezegd'},
                        {'person': 'zij', 'conjugation': 'hadden gezegd'},
                    ]
                },
                {
                    'dutchName': 'Toekomende Tijd',
                    'englishName': 'Future Simple',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zal zeggen'},
                        {'person': 'je/jij', 'conjugation': 'zal zeggen'},
                        {'person': 'hij/zij/het', 'conjugation': 'zal zeggen'},
                        {'person': 'wij', 'conjugation': 'zullen zeggen'},
                        {'person': 'jullie', 'conjugation': 'zullen zeggen'},
                        {'person': 'zij', 'conjugation': 'zullen zeggen'},
                    ]
                },
                {
                    'dutchName': 'Voorwaardelijke Wijs',
                    'englishName': 'Conditional',
                    'forms': [
                        {'person': 'ik', 'conjugation': 'zou zeggen'},
                        {'person': 'je/jij', 'conjugation': 'zou zeggen'},
                        {'person': 'hij/zij/het', 'conjugation': 'zou zeggen'},
                        {'person': 'wij', 'conjugation': 'zouden zeggen'},
                        {'person': 'jullie', 'conjugation': 'zouden zeggen'},
                        {'person': 'zij', 'conjugation': 'zouden zeggen'},
                    ]
                }
            ],
            'examples': [
                {
                    'dutch': 'Wat zeg je?',
                    'english': 'What do you say?',
                    'tense': 'Present'
                },
                {
                    'dutch': 'Hij zei het waarheid.',
                    'english': 'He said the truth.',
                    'tense': 'Simple Past'
                },
                {
                    'dutch': 'Ze hebben alles gezegd.',
                    'english': 'They have said everything.',
                    'tense': 'Present Perfect'
                },
                {
                    'dutch': 'Ik zal je de waarheid zeggen.',
                    'english': 'I will tell you the truth.',
                    'tense': 'Future Simple'
                }
            ]
        }
    }
    
    @staticmethod
    def conjugate_verb(verb: str) -> Dict[str, Any]:
        """
        Conjugate a Dutch verb from the database.
        
        Args:
            verb: The infinitive form of a Dutch verb
            
        Returns:
            Dictionary with conjugation data including tenses and examples
            
        Raises:
            KeyError: If verb is not found in the database (use conjugate_verb_with_llm for LLM fallback)
        """
        verb_lower = verb.lower().strip()
        
        if verb_lower not in VerbConjugationService.VERB_DATABASE:
            available = ', '.join(list(VerbConjugationService.VERB_DATABASE.keys())[:5])
            raise KeyError(f"Verb '{verb}' not found. Try one of: {available}...")
        
        logger.info(f"Conjugating verb from database: {verb_lower}")
        return VerbConjugationService.VERB_DATABASE[verb_lower]
    
    @staticmethod
    async def conjugate_verb_with_llm(verb: str) -> Dict[str, Any]:
        """
        Conjugate a Dutch verb with LLM fallback for unknown verbs.
        
        First tries to get the conjugation from the local database.
        If not found, uses OpenRouter LLM to generate the conjugation.
        
        Args:
            verb: The infinitive form of a Dutch verb
            
        Returns:
            Dictionary with conjugation data including tenses and examples
            
        Raises:
            ProcessingError: If both database lookup and LLM generation fail
        """
        verb_lower = verb.lower().strip()
        
        # Try database first
        if verb_lower in VerbConjugationService.VERB_DATABASE:
            logger.info(f"Found '{verb_lower}' in database")
            return VerbConjugationService.VERB_DATABASE[verb_lower]
        
        # Fallback to LLM
        logger.info(f"Verb '{verb_lower}' not in database, using LLM to conjugate")
        
        # Import here to avoid circular imports
        from app.llm_service import OpenRouterService
        from app.exceptions import ProcessingError
        
        try:
            conjugation = await OpenRouterService.conjugate_dutch_verb(verb_lower)
            logger.info(f"Successfully generated conjugation for '{verb_lower}' via LLM")
            return conjugation
        except Exception as e:
            logger.error(f"Failed to conjugate '{verb_lower}': {str(e)}")
            available = ', '.join(list(VerbConjugationService.VERB_DATABASE.keys())[:5])
            raise ProcessingError(
                f"Could not conjugate verb '{verb}'. Database: {available}..., LLM: {str(e)}"
            )
