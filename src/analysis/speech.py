def analyse_speech(words: list, duration: float) -> dict:
    """
    Calculate simple speech statistics.
    """

    word_count = len(words)

    if word_count == 0 or duration <= 0:
        return {
            "word_count": 0,
            "words_per_minute": 0,
            "speech_rate": "No speech",
        }

    words_per_minute = (
        word_count / duration
    ) * 60

    if words_per_minute < 100:
        label = "Slow"
    elif words_per_minute < 150:
        label = "Conversational"
    elif words_per_minute < 180:
        label = "Fast"
    else:
        label = "Very Fast"

    return {
        "word_count": word_count,
        "words_per_minute": round(
            words_per_minute,
            1
        ),
        "speech_rate": label,
    }