import ast
import os
from flask import Flask, abort, redirect, render_template, request, url_for
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import spacy
from procesamiento import cargar_lexico_nrc, procesar_texto

app = Flask(__name__)

CSV_PATH = os.path.join('data', 'textos_Bo_procesado.csv')
RUTA_NRC = os.path.join('data', 'nrc_lexicon', 'NRC-Emotion-Lexicon-Wordlevel-v0.92_Spanish.txt')
RUTA_IMGS = os.path.join('static', 'images')

DEPARTAMENTO_A_SIGLA = {
    'Pando': 'BO-N',
    'La Paz': 'BO-L',
    'Beni': 'BO-B',
    'Oruro': 'BO-O',
    'Cochabamba': 'BO-C',
    'Santa Cruz': 'BO-S',
    'Potosi': 'BO-P',
    'Chuquisaca': 'BO-H',
    'Tarija': 'BO-T',
}

nlp = spacy.load('es_core_news_sm')
word_to_emotions, word_to_sentiments = cargar_lexico_nrc(RUTA_NRC)
sns.set_theme(style='whitegrid')


def cargar_datos():
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame(columns=[
        'titulo', 'texto', 'autor', 'departamento', 'sigla', 'id',
        'emotion_map', 'sentiment_pol', 'emotion_main', 'sentiment_main'
    ])

def generar_grafico_registro(record_id, emotions, sentiment):
    os.makedirs(RUTA_IMGS, exist_ok=True)
    emotions = ast.literal_eval(emotions) if isinstance(emotions, str) else (emotions or {})
    sentiment = ast.literal_eval(sentiment) if isinstance(sentiment, str) else (sentiment or {})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [3, 1]})

    emo_keys = list(emotions.keys())
    emo_values = list(emotions.values())
    if emo_keys:
        sns.barplot(x=emo_values, y=emo_keys, ax=ax1, hue=emo_keys, palette='viridis', legend=False, orient='h')
    ax1.set_title(f'Distribución Emocional - {record_id}', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Intensidad / Conteo')
    ax1.set_ylabel('')

    sent_keys = list(sentiment.keys())
    sent_values = list(sentiment.values())
    colores_polaridad = ['#2ecc71' if k == 'positive' else '#e74c3c' for k in sent_keys]
    ax2.bar(sent_keys, sent_values, color=colores_polaridad, edgecolor='black', alpha=0.8)
    ax2.set_title('Polaridad', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Conteo')

    plt.tight_layout()
    safe_id = str(record_id).replace('/', '_')
    nombre_archivo = os.path.join(RUTA_IMGS, f'p2_{safe_id}.png')
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()

def generar_siguiente_id(df, sigla, excluir_idx=None):
    prefijo = f"{sigla}_"
    ids_validos = df.drop(index=excluir_idx)['id'] if excluir_idx in df.index else df['id']
    numeros = [
        int(str(val).split('_')[-1])
        for val in ids_validos.dropna()
        if str(val).startswith(prefijo) and str(val).split('_')[-1].isdigit()
    ]
    siguiente = (max(numeros) + 1) if numeros else 1
    return f"{sigla}_{str(siguiente).zfill(4)}"

@app.route('/')
def index():
    df = cargar_datos()
    registros = df.to_dict(orient='records') if not df.empty else []
    return render_template('index.html', registros=registros)


@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        texto = request.form.get('texto', '').strip()
        autor = request.form.get('autor', '').strip()
        departamento = request.form.get('departamento', '').strip()

        if departamento not in DEPARTAMENTO_A_SIGLA:
            abort(400)

        sigla = DEPARTAMENTO_A_SIGLA[departamento]
        res_nlp = procesar_texto(texto, nlp, word_to_emotions, word_to_sentiments)

        data_df = cargar_datos()
        nuevo_registro = {
            'titulo': titulo,
            'texto': texto,
            'autor': autor,
            'departamento': departamento,
            'sigla': sigla,
            'id': '',
            'emotion_map': str(res_nlp['emotion_map']),
            'sentiment_pol': str(res_nlp['sentiment_pol']),
            'emotion_main': res_nlp['emotion_main'],
            'sentiment_main': res_nlp['sentiment_main'],
        }

        data_df = pd.concat([data_df, pd.DataFrame([nuevo_registro])], ignore_index=True)

        data_df['sigla'] = data_df['departamento'].map(DEPARTAMENTO_A_SIGLA)
        secuencia = data_df.groupby('sigla').cumcount() + 1
        data_df['id'] = data_df['sigla'] + '_' + secuencia.astype(str).str.zfill(4)

        nuevo_id = data_df.iloc[-1]['id']
        generar_grafico_registro(nuevo_id, res_nlp['emotion_map'], res_nlp['sentiment_pol'])

        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        data_df.to_csv(CSV_PATH, index=False)

        return redirect(url_for('detalle_relato', id_relato=nuevo_id))

    return render_template('adicionar.html')


@app.route('/relato/<id_relato>')
def detalle_relato(id_relato):
    df = cargar_datos()
    if df.empty:
        abort(404)

    registro = df[df['id'] == id_relato]
    if registro.empty:
        abort(404)

    relato = registro.iloc[0].to_dict()
    nombre_imagen = f'p2_{id_relato}.png'
    return render_template('detalle.html', relato=relato, imagen=nombre_imagen)

@app.route('/relato/<id_relato>/reiniciar-analisis', methods=['POST'])
def reiniciar_analisis(id_relato):
    df = cargar_datos()
    if df.empty:
        abort(404)

    matches = df.index[df['id'] == id_relato].tolist()
    if not matches:
        abort(404)

    idx = matches[0]
    texto_actual = df.loc[idx, 'texto']

    res_nlp = procesar_texto(texto_actual, nlp, word_to_emotions, word_to_sentiments)
    df.loc[idx, 'emotion_map'] = str(res_nlp['emotion_map'])
    df.loc[idx, 'sentiment_pol'] = str(res_nlp['sentiment_pol'])
    df.loc[idx, 'emotion_main'] = res_nlp['emotion_main']
    df.loc[idx, 'sentiment_main'] = res_nlp['sentiment_main']

    generar_grafico_registro(id_relato, res_nlp['emotion_map'], res_nlp['sentiment_pol'])
    df.to_csv(CSV_PATH, index=False)

    return redirect(url_for('detalle_relato', id_relato=id_relato))


@app.route('/relato/<id_relato>/editar', methods=['GET', 'POST'])
def editar_relato(id_relato):
    df = cargar_datos()
    if df.empty:
        abort(404)

    matches = df.index[df['id'] == id_relato].tolist()
    if not matches:
        abort(404)

    idx = matches[0]

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        autor = request.form.get('autor', '').strip()
        departamento = request.form.get('departamento', '').strip()
        texto = request.form.get('texto', '').strip()

        if departamento not in DEPARTAMENTO_A_SIGLA:
            abort(400)

        nueva_sigla = DEPARTAMENTO_A_SIGLA[departamento]
        id_final = id_relato if nueva_sigla == df.loc[idx, 'sigla'] else generar_siguiente_id(df, nueva_sigla, excluir_idx=idx)

        res_nlp = procesar_texto(texto, nlp, word_to_emotions, word_to_sentiments)

        df.loc[idx, 'titulo'] = titulo
        df.loc[idx, 'autor'] = autor
        df.loc[idx, 'departamento'] = departamento
        df.loc[idx, 'sigla'] = nueva_sigla
        df.loc[idx, 'id'] = id_final
        df.loc[idx, 'texto'] = texto
        df.loc[idx, 'emotion_map'] = str(res_nlp['emotion_map'])
        df.loc[idx, 'sentiment_pol'] = str(res_nlp['sentiment_pol'])
        df.loc[idx, 'emotion_main'] = res_nlp['emotion_main']
        df.loc[idx, 'sentiment_main'] = res_nlp['sentiment_main']

        generar_grafico_registro(id_final, res_nlp['emotion_map'], res_nlp['sentiment_pol'])
        df.to_csv(CSV_PATH, index=False)

        return redirect(url_for('detalle_relato', id_relato=id_final))

    relato = df.loc[idx].to_dict()
    return render_template(
        'editar.html',
        relato=relato,
        departamentos=list(DEPARTAMENTO_A_SIGLA.keys())
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3600))
    app.run(debug=False, host='0.0.0.0', port=port)