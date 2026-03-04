"""Dutch words with articles (de/het) and metadata for the article game."""

DUTCH_ARTICLE_WORDS = [
    # Common nouns with 'de' article
    {"word": "appel", "article": "de", "translation": "apple", "difficulty": "easy", "category": "food"},
    {"word": "boom", "article": "de", "translation": "tree", "difficulty": "easy", "category": "nature"},
    {"word": "boek", "article": "de", "translation": "book", "difficulty": "easy", "category": "object"},
    {"word": "auto", "article": "de", "translation": "car", "difficulty": "easy", "category": "transport"},
    {"word": "brief", "article": "de", "translation": "letter", "difficulty": "easy", "category": "object"},
    {"word": "buurt", "article": "de", "translation": "neighborhood", "difficulty": "medium", "category": "place"},
    {"word": "deur", "article": "de", "translation": "door", "difficulty": "easy", "category": "object"},
    {"word": "dag", "article": "de", "translation": "day", "difficulty": "easy", "category": "time"},
    {"word": "deken", "article": "de", "translation": "blanket", "difficulty": "medium", "category": "object"},
    {"word": "diamant", "article": "de", "translation": "diamond", "difficulty": "medium", "category": "object"},
    {"word": "dokter", "article": "de", "translation": "doctor", "difficulty": "easy", "category": "person"},
    {"word": "domein", "article": "de", "translation": "domain", "difficulty": "medium", "category": "place"},
    {"word": "droom", "article": "de", "translation": "dream", "difficulty": "medium", "category": "abstract"},
    {"word": "duif", "article": "de", "translation": "dove", "difficulty": "medium", "category": "animal"},
    {"word": "economie", "article": "de", "translation": "economy", "difficulty": "hard", "category": "abstract"},
    {"word": "emmer", "article": "de", "translation": "bucket", "difficulty": "medium", "category": "object"},
    {"word": "engel", "article": "de", "translation": "angel", "difficulty": "medium", "category": "abstract"},
    {"word": "epidemie", "article": "de", "translation": "epidemic", "difficulty": "hard", "category": "abstract"},
    {"word": "familie", "article": "de", "translation": "family", "difficulty": "easy", "category": "person"},
    {"word": "farm", "article": "de", "translation": "farm", "difficulty": "medium", "category": "place"},
    {"word": "fase", "article": "de", "translation": "phase", "difficulty": "medium", "category": "abstract"},
    {"word": "fles", "article": "de", "translation": "bottle", "difficulty": "easy", "category": "object"},
    {"word": "film", "article": "de", "translation": "film", "difficulty": "easy", "category": "object"},
    {"word": "gaaf", "article": "de", "translation": "cool", "difficulty": "hard", "category": "abstract"},
    {"word": "gale", "article": "de", "translation": "gallery", "difficulty": "medium", "category": "object"},
    {"word": "gang", "article": "de", "translation": "hallway", "difficulty": "easy", "category": "place"},
    {"word": "garantie", "article": "de", "translation": "guarantee", "difficulty": "medium", "category": "abstract"},
    
    # Common nouns with 'het' article
    {"word": "aambeeldhouwwerk", "article": "het", "translation": "sculpture", "difficulty": "hard", "category": "object"},
    {"word": "aanbod", "article": "het", "translation": "offer", "difficulty": "medium", "category": "abstract"},
    {"word": "aanzicht", "article": "het", "translation": "view", "difficulty": "hard", "category": "abstract"},
    {"word": "bed", "article": "het", "translation": "bed", "difficulty": "easy", "category": "object"},
    {"word": "been", "article": "het", "translation": "leg", "difficulty": "easy", "category": "body"},
    {"word": "beeld", "article": "het", "translation": "image", "difficulty": "medium", "category": "object"},
    {"word": "beroep", "article": "het", "translation": "profession", "difficulty": "medium", "category": "abstract"},
    {"word": "bewijs", "article": "het", "translation": "proof", "difficulty": "medium", "category": "abstract"},
    {"word": "bier", "article": "het", "translation": "beer", "difficulty": "easy", "category": "food"},
    {"word": "blad", "article": "het", "translation": "leaf", "difficulty": "easy", "category": "nature"},
    {"word": "bloed", "article": "het", "translation": "blood", "difficulty": "easy", "category": "body"},
    {"word": "bos", "article": "het", "translation": "forest", "difficulty": "easy", "category": "nature"},
    {"word": "brood", "article": "het", "translation": "bread", "difficulty": "easy", "category": "food"},
    {"word": "bruidsmeisje", "article": "het", "translation": "bridesmaid", "difficulty": "hard", "category": "person"},
    {"word": "budget", "article": "het", "translation": "budget", "difficulty": "medium", "category": "abstract"},
    {"word": "bureau", "article": "het", "translation": "desk", "difficulty": "easy", "category": "object"},
    {"word": "cafe", "article": "het", "translation": "cafe", "difficulty": "easy", "category": "place"},
    {"word": "centrum", "article": "het", "translation": "center", "difficulty": "medium", "category": "place"},
    {"word": "compliment", "article": "het", "translation": "compliment", "difficulty": "medium", "category": "abstract"},
    {"word": "concern", "article": "het", "translation": "concern", "difficulty": "medium", "category": "abstract"},
    {"word": "congres", "article": "het", "translation": "congress", "difficulty": "hard", "category": "abstract"},
    {"word": "continent", "article": "het", "translation": "continent", "difficulty": "medium", "category": "place"},
    {"word": "contract", "article": "het", "translation": "contract", "difficulty": "medium", "category": "abstract"},
    {"word": "controle", "article": "het", "translation": "control", "difficulty": "medium", "category": "abstract"},
    {"word": "copyright", "article": "het", "translation": "copyright", "difficulty": "hard", "category": "abstract"},
    {"word": "ei", "article": "het", "translation": "egg", "difficulty": "easy", "category": "food"},
    {"word": "eind", "article": "het", "translation": "end", "difficulty": "easy", "category": "abstract"},
    {"word": "elf", "article": "het", "translation": "elf", "difficulty": "hard", "category": "abstract"},
    {"word": "embrion", "article": "het", "translation": "embryo", "difficulty": "hard", "category": "object"},
    {"word": "exemplaar", "article": "het", "translation": "copy", "difficulty": "hard", "category": "object"},
    {"word": "experiment", "article": "het", "translation": "experiment", "difficulty": "hard", "category": "abstract"},
    {"word": "freitag", "article": "het", "translation": "Friday", "difficulty": "medium", "category": "time"},
    {"word": "gebouw", "article": "het", "translation": "building", "difficulty": "medium", "category": "place"},
    {"word": "gedeelte", "article": "het", "translation": "part", "difficulty": "medium", "category": "abstract"},
    {"word": "gedrag", "article": "het", "translation": "behavior", "difficulty": "medium", "category": "abstract"},
    {"word": "gefoel", "article": "het", "translation": "feeling", "difficulty": "hard", "category": "abstract"},
    {"word": "geheime", "article": "het", "translation": "secret", "difficulty": "medium", "category": "abstract"},
    {"word": "gehoor", "article": "het", "translation": "hearing", "difficulty": "hard", "category": "body"},
    {"word": "gelegenheid", "article": "het", "translation": "opportunity", "difficulty": "medium", "category": "abstract"},
    {"word": "geloof", "article": "het", "translation": "belief", "difficulty": "medium", "category": "abstract"},
    {"word": "gemak", "article": "het", "translation": "convenience", "difficulty": "hard", "category": "abstract"},
    {"word": "gemeenschap", "article": "het", "translation": "community", "difficulty": "medium", "category": "abstract"},
    {"word": "gemiddelde", "article": "het", "translation": "average", "difficulty": "hard", "category": "abstract"},
    {"word": "gepeins", "article": "het", "translation": "thought", "difficulty": "hard", "category": "abstract"},
    {"word": "gered", "article": "het", "translation": "saved", "difficulty": "hard", "category": "abstract"},
    {"word": "geschenk", "article": "het", "translation": "gift", "difficulty": "easy", "category": "object"},
    {"word": "geschiedenis", "article": "het", "translation": "history", "difficulty": "medium", "category": "abstract"},
    {"word": "gesprek", "article": "het", "translation": "conversation", "difficulty": "easy", "category": "abstract"},
]

def get_random_words(count: int = 20):
    """
    Get a random selection of Dutch words.
    
    Args:
        count: Number of words to return (max 50, default 20)
        
    Returns:
        List of word dictionaries with word, article, difficulty, category
    """
    import random
    
    if count > len(DUTCH_ARTICLE_WORDS):
        count = len(DUTCH_ARTICLE_WORDS)
    if count < 1:
        count = 1
    
    return random.sample(DUTCH_ARTICLE_WORDS, count)

def get_word_info(word: str):
    """Get info about a specific word."""
    for w in DUTCH_ARTICLE_WORDS:
        if w["word"].lower() == word.lower():
            return w
    return None
