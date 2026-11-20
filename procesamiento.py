from collections import Counter
import re

def cargar_lexico_nrc(file_nrc):
    word_to_emotions = {}
    word_to_sentiments = {}

    emisiones_emociones = {
        'anger', 'anticipation', 'disgust', 'fear',
        'joy', 'sadness', 'surprise', 'trust'
    }
    emisiones_sentimientos = {'positive', 'negative'}

    categories_order = [
        'anger', 'anticipation', 'disgust', 'fear', 'joy',
        'negative', 'positive', 'sadness', 'surprise', 'trust'
    ]

    with open(file_nrc, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f):
            parts = line.strip().split()
            if not parts or (line_num == 0 and 'english' in parts[0].lower()):
                continue

            if len(parts) >= 12:
                spanish_word = parts[-1].lower()
                emos = []
                sents = []

                for idx, cat in enumerate(categories_order):
                    try:
                        if parts[idx + 1] == '1':
                            if cat in emisiones_emociones:
                                emos.append(cat)
                            elif cat in emisiones_sentimientos:
                                sents.append(cat)
                    except IndexError:
                        continue

                if emos:
                    word_to_emotions[spanish_word] = emos
                if sents:
                    word_to_sentiments[spanish_word] = sents

    return word_to_emotions, word_to_sentiments

STOP_WORDS_ES = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero',
    'de', 'del', 'a', 'en', 'por', 'para', 'con', 'sin', 'su', 'sus', 'es', 'son',
    'que', 'se', 'lo', 'como', 'más', 'fue', 'ha', 'este', 'esta', 'estos', 'estas'
}

def sanitizar_texto(texto):
    texto_limpio = '' if texto is None else str(texto)
    texto_limpio = texto_limpio.replace('\r\n', '\n').replace('\r', '\n')
    texto_limpio = texto_limpio.replace(';', ',')
    texto_limpio = re.sub(r'\n{2,}', '\n', texto_limpio)

    return texto_limpio.strip()

def procesar_texto(texto, nlp, word_to_emotions, word_to_sentiments):
    texto_limpio = sanitizar_texto(texto)

    conteo_emociones = Counter()
    conteo_sentimientos = Counter()

    if texto_limpio:
        doc = nlp(texto_limpio)
        for token in doc:
            if token.is_alpha and not token.is_stop:
                lema = token.lemma_.lower()
                if lema not in STOP_WORDS_ES:
                    if lema in word_to_emotions:
                        conteo_emociones.update(word_to_emotions[lema])
                    if lema in word_to_sentiments:
                        conteo_sentimientos.update(word_to_sentiments[lema])

    emotion_map = dict(conteo_emociones)
    sentiment_pol = dict(conteo_sentimientos)
    emotion_main = conteo_emociones.most_common(1)[0][0] if conteo_emociones else None
    sentiment_main = conteo_sentimientos.most_common(1)[0][0] if conteo_sentimientos else None

    return {
        'texto': texto_limpio,
        'emotion_map': emotion_map,
        'sentiment_pol': sentiment_pol,
        'emotion_main': emotion_main,
        'sentiment_main': sentiment_main
    }