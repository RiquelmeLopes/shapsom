from io import StringIO
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import plotly.express as px
import numpy as np
import branca.colormap as cm
from branca.colormap import linear
from PIL import Image
import re
import folium
import json
import PIL
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
from pypdf import PdfMerger
import math
from streamlit_folium import st_folium
import matplotlib.colors as mcolors
from streamlit_javascript import st_javascript
import weasyprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from sklearn import tree
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn import tree
import matplotlib.pyplot as plt
import globals

import unicodedata
from datetime import datetime
import pytz
from sortedcontainers import SortedSet

import geopandas as gpd
import os

import plotly.graph_objects as go

from pagess.Análise_Estatística_Exploratória import pagina_analise_estatistica_exploratoria
from pagess.Anomalias import pagina_anomalias
from pagess.Relatório_das_Regiões import relatorio_regioes
from pagess.Relatório_dos_Municípios import relatorio_municipios


# Set page configuration
#st.set_page_config(layout='wide')
def quebra_pagina():
    st.markdown("""
        <style type="text/css" media="print">
        hr{
            page-break-after: always;
            page-break-inside: avoid;
        }
        <style>
    """, unsafe_allow_html= True)

def pagina_analise_por_grupos():
    st.title("**Sistema de Apoio a Auditorias do Tribunal de Contas do Estado 📊**")
    has_databases = True
    try:
        has_databases = has_databases and globals.current_database is not None
        has_databases = has_databases and globals.crunched_df is not None
        has_databases = has_databases and globals.som_data is not None
    except:
        has_databases = False

    if has_databases:
        df =  globals.current_database
        for i in range(globals.som_data['Grupo'].max() + 1):
            filepath = f'mapa{i}.html'
            if os.path.exists(filepath):
                os.remove(filepath)

        def secao1():
            st_theme = st_javascript("""window.getComputedStyle(window.parent.document.getElementsByClassName("stApp")[0]).getPropertyValue("color-scheme")""")

            def verificarColunaDesc(database):
                nStrings = 0
                for i in range(database.shape[1]):
                    try:
                        float(np.array(database.iloc[0])[i])
                    except ValueError:
                        nStrings+=1
                if(nStrings==database.shape[1]):
                    return True
                else:
                    return False

            def convert_numeric(x):
                try:
                    if float(x).is_integer():
                        return int(float(x))
                    else:
                        return float(x)
                except (ValueError,AttributeError):
                    return x

            # Cálculo de data
            current_time_utc = datetime.utcnow()
            your_timezone = pytz.timezone('America/Recife')
            current_time_local = current_time_utc.replace(tzinfo=pytz.utc).astimezone(your_timezone)
            formatted_date = current_time_local.strftime("%d/%m/%Y")

            if(globals.current_database is not None):
                # Gerar base de dados sem descrição completa
                if(verificarColunaDesc(globals.original_database)):
                    analyzed_database = globals.original_database.drop(globals.original_database.index[0]).applymap(convert_numeric)
                    analyzed_database.index = analyzed_database.index-1
                else:
                    analyzed_database = globals.original_database

                # Gerar primeira seção
                num_rows, num_columns = analyzed_database.shape
                texto1 = 'Este relatório foi elaborado com base nos dados presentes no arquivo “'+unicodedata.normalize('NFKC', globals.current_database_name)+'” no dia '+formatted_date+'. A tabela fornecida possui '+str(num_rows)+' linhas e '+str(num_columns)+' colunas.'
                valoresFaltantes = analyzed_database.isnull().sum().sum()
                if(valoresFaltantes==0):
                    textoFaltantes = 'A tabela não possui valores faltantes.'
                elif(valoresFaltantes==1):
                    textoFaltantes = 'A tabela possui 1 valor faltante na linha '+str(1+np.where(analyzed_database.isnull())[0][0]) +' e na coluna "'+analyzed_database.columns[np.where(analyzed_database.isnull())[1][0]]+'".'
                else:
                    textoFaltantes = 'A tabela possui '+str(valoresFaltantes)+' valores faltantes'
                    if(valoresFaltantes < 6):
                        textoFaltantes += ' nas seguintes localizações: '
                        for i in range(valoresFaltantes):
                            textoFaltantes += 'linha '+str(1+np.where(analyzed_database.isnull())[0][i]) +' e coluna "'+analyzed_database.columns[np.where(analyzed_database.isnull())[1][i]]+'", '
                        textoFaltantes = textoFaltantes[:-2]+'.'
                    else:
                        textoFaltantes += '.'

                texto1 = texto1 + ' ' + textoFaltantes
                texto1 += ' A seguir, na tabela 1, apresentamos o dicionário de dados. É importante notar que colunas com texto ou aquelas que foram ocultadas durante a criação do mapa não foram incluídas na análise.'

                # Dicionário de dados

                def checarTipo(X,tipo):
                    if(tipo=='01'):
                        for i in X:
                            if(i not in [0,1]):
                                return False
                        return True
                    elif(tipo=='0'):
                        for i in X:
                            if(i != 0):
                                return False
                        return True
                    elif(tipo=='1'):
                        for i in X:
                            if(i != 1):
                                return False
                        return True
                    else:
                        for i in X:
                            if(not isinstance(i,tipo)):
                                return False
                        return True

                def gerarArray(X):
                    array1 = []
                    for i in X:
                        array1+= [i]
                    return array1

                def detectarTipo(X):

                    tipo = ''
                    faltantes = ''

                    if(X.isnull().sum()!=0):
                        faltantes = ' com valores faltantes'
                        X = X.dropna()

                    arrX = gerarArray(X)

                    if(checarTipo(arrX,'0')):
                        tipo ='Numérico (0)'
                    elif(checarTipo(arrX,'1')):
                        tipo ='Numérico (1)'
                    elif(checarTipo(arrX,'01')):
                        tipo ='Binário (0 ou 1)'
                    elif(checarTipo(arrX,(int,float))):
                        tipo = 'Numérico'
                        unicos = [int(num) if num == int(num) else format(num,'.1f') for num in SortedSet(X)]
                        if(len(unicos)<4):
                            tipo+= ' ('
                            for i in unicos:
                                tipo+=str(i)+', '
                            tipo = tipo[:-2]
                            tipo+= ')'
                        elif(max(arrX)<=1 and min(arrX)>=0):
                            tipo += ' (entre 0 e 1)'
                    elif(checarTipo(arrX,str)):
                        tipo = 'Textual'
                    else:
                        tipo = 'Outro'

                    return tipo+faltantes

                tiposDados = []
                for i in range(analyzed_database.columns.size):
                    tiposDados+=[detectarTipo(analyzed_database.iloc[:,i])]
                nomesDados = analyzed_database.columns.tolist()

                # Descrição de dados

                descDados = []

                if(globals.original_database.shape!=analyzed_database.shape):
                    descDados = np.array(globals.original_database.iloc[0])

                # Número das variáveis

                numDados = []
                varNum = 1
                for i in range(len(tiposDados)):
                    if(nomesDados[i] in globals.current_label_columns):
                        numDados += ['Nome']
                    elif(nomesDados[i] in globals.current_output_columns):
                        numDados += ['Saída']
                    elif(nomesDados[i] in analyzed_database[globals.current_input_columns].select_dtypes(include='number').columns):
                        numDados += [varNum]
                        varNum += 1
                    else:
                        numDados+=['']

                def insert_newlines(text, every=40):
                    lines = []
                    while len(text) > every:
                        split_index = text.rfind(' ', 0, every)
                        if split_index == -1:
                            split_index = every
                        lines.append(text[:split_index].strip())
                        text = text[split_index:].strip()
                    lines.append(text)
                    return '\n'.join(lines)

                def dividirlinhas(data, every):
                    if(len(data)>every):
                        data = insert_newlines(data, every=every)
                    return data


                # Geração do dicionário de dados
                if(len(descDados)==0):
                    dicionarioDados = np.array([numDados,nomesDados,tiposDados]).tolist()
                    for i in range(len(dicionarioDados[1])):
                        dicionarioDados[1][i]=dividirlinhas(dicionarioDados[1][i],80)
                    for i in range(len(dicionarioDados[2])):
                        dicionarioDados[2][i]=dividirlinhas(dicionarioDados[2][i],25)
                else:
                    dicionarioDados = np.array([numDados,nomesDados,descDados,tiposDados]).tolist()
                    for i in range(len(dicionarioDados[1])):
                        dicionarioDados[1][i]=dividirlinhas(dicionarioDados[1][i],40)
                    for i in range(len(dicionarioDados[2])):
                        dicionarioDados[2][i]=dividirlinhas(dicionarioDados[2][i],40)
                    for i in range(len(dicionarioDados[3])):
                        dicionarioDados[3][i]=dividirlinhas(dicionarioDados[3][i],25)
                dicionarioDados = np.array(dicionarioDados).T.tolist()


                dicionarioDados = pd.DataFrame(dicionarioDados)
                if(len(descDados)==0):
                    dicionarioDados.columns = ['Fator','Nome da coluna','Tipo de dado']
                else:
                    dicionarioDados.columns = ['Fator','Nome da coluna','Descrição do dado','Tipo de dado']

            def gerarEspaco():
                st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)


            st.subheader('Seção 1 - Descrição do arquivo de entrada')
            if( globals.current_database is None):
                st.write('Escolha a base de dados.')
            else:
                st.markdown('Esta seção trará informações gerais sobre o arquivo de entrada escolhido pelo usuário e os parâmetros utilizados para a criação do mapa SOM.')
                botaos1 = st.button('Gerar Descrição do arquivo de entrada')
                gerarEspaco()
                if botaos1:
                    st.write('#### 1.1 Dicionário de Dados')
                    gerarEspaco()
                    textoDicionario = 'Um dicionário de dados é uma tabela que contém informações sobre os dados disponibilizados. As informações reveladas abaixo revelam o número atribuído a cada fator, sua descrição quando disponibilizada e seu tipo de dado.'
                    st.write(texto1)
                    st.write(textoDicionario)

                    custom_css = """

                    <style>
                    thead th {
                        background-color: #717171;
                        color: white;
                    }
                    </style>
                    """
                    st.markdown(custom_css, unsafe_allow_html=True)


                    if( globals.current_database is not None):
                        st.markdown(dicionarioDados.style.hide(axis="index").to_html(), unsafe_allow_html=True)

                    gerarEspaco()

                    globals.table_list.append('table3')
                    st.info(f'Tabela {len(globals.table_list)} - Dicionário de Dados')

                    st.write('#### 1.2 Parâmetros de Treinamento')
                    gerarEspaco()

                    st.write('Nesta seção, apresentamos os hiperparâmetros utilizados para configurar o algoritmo. Os dados mencionados no parágrafo anterior foram aplicados a um algoritmo de Mapas Auto-Organizáveis (Mapas SOM), utilizando os seguintes parâmetros:')
                    param_treino = [
                        "Topologia: "+str(globals.topology),
                        f"Distância de cluster: "+str(globals.cluster_distance),
                        f"Épocas: "+str(globals.epochs),
                        f"Tamanho do mapa: "+str(globals.size),
                        f"Sigma: "+str(globals.sigma),
                        f"Taxa de aprendizado: "+str(globals.lr)
                    ]
                    for item in param_treino:
                        st.write(f"- {item}")

                    #if(globals.current_output_columns != []):
                    #    gerarEspaco()
                    #    st.write('#### 1.3 Parâmetros de Triagem')
                    #    gerarEspaco()
                    #    textoTriagem = 'A etapa de triagem realizará uma análise filtrada em relação à saída "'+globals.current_output_columns[0]+'". Os limites mínimo e máximo determinam o intervalo percentual do filtro realizado.'
                    #    gerarRetangulo(textoTriagem)
                    #    gerarEspaco()
                    #    st.write('Os limites utilizados para a realização da triagem foram:')
                    #    param_triagem = [
                    #        f"Limite mínimo: {min_filter*100:.0f}%",
                    #        f"Limite máximo: {max_filter*100:.0f}%"
                    #    ]
                    #    for item in param_triagem:
                    #        st.write(f"- {item}")
                    #    gerarEspaco()

        def gerar_df_shap():
            tabela_df = globals.shapsom_data.copy()
            tabela_df.drop(['Municípios', 'Nota', 'SHAP Normalizado', 'x', 'y', 'Cor', 'SHAP Original'], axis=1, inplace=True)


            tabela_unica = tabela_df.drop_duplicates(subset=['Cor Central', 'Grupo'])

            nome_variavel_coluna = 'Nome Variável'
            grupos_colunas = sorted(tabela_unica['Grupo'].unique())
            colunas_novo_df = [nome_variavel_coluna] + [f'Grupo {grupo}' for grupo in grupos_colunas]


            novo_df = pd.DataFrame(columns=colunas_novo_df)

            for idx, nome_variavel in enumerate(globals.shap_columns):
                novo_df.at[idx, 'Nome Variável'] = nome_variavel
                for grupo in grupos_colunas:
                    valores_grupo = tabela_unica.loc[tabela_unica['Grupo'] == grupo, 'SHAP Media Cluster'].values
                    if len(valores_grupo) > 0 and len(valores_grupo[0]) > idx:
                        novo_df.at[idx, f'Grupo {grupo}'] = valores_grupo[0][idx]
                    else:
                        novo_df.at[idx, f'Grupo {grupo}'] = None

            return novo_df

        def html_to_png(html_file, output_png):
            # Configuração do WebDriver (neste caso, estou usando o Chrome)
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(options=chrome_options)

            driver.set_window_size(600, 350)

            # Carrega o arquivo HTML no navegador
            caminho_atual = os.getcwd()
            caminho_html = os.path.join(caminho_atual, html_file)
            driver.get("file:///" + caminho_html)

            # Espera um pouco para garantir que o HTML seja totalmente carregado
            time.sleep(2)

            # Captura a tela e salva como um arquivo PNG
            driver.save_screenshot(output_png)

            # Fecha o navegador
            driver.quit()

        ##############################################################################
        # FUNÇÕES AUXILIARES PARA AS SEÇÕES 2 E 5
        def formatDf(df):
            formated_df = df.drop(columns=['Município'])
            nums_columns = list(range(1, len(formated_df.columns) + 1))
            formated_df.columns = nums_columns

            return formated_df

        def generate_heatmap(data, cmap):
                largura, altura = data.shape
                sns.set_theme()
                plt.figure(figsize=(altura/9.15 ,largura/7))
                heatmap =sns.heatmap(data,
                    annot=False,
                    cmap=cmap,
                    square=True,
                    vmin=0,
                    vmax = 1,
                    cbar_kws={'orientation': 'vertical'}

                    )

                return heatmap

        def gerar_pdf_secao2e5(filename : str, titulo: str, text_data, filtro_min=0.0, filtro_max=500):
            image_filenames = []
            numeric_cols = list(globals.crunched_df.select_dtypes(include=['float64', 'int64']).columns)
            max_rows = math.ceil(len(globals.crunched_df)/ 3)
            candidate_rows = np.array(list(globals.crunched_df[list(globals.crunched_df.columns)[-1]].values))
            indexes = np.where((candidate_rows >= filtro_min/100) & (candidate_rows <= filtro_max/100))[0].tolist()

            partitions = [indexes[i:i+max_rows] for i in range(0, len(indexes), max_rows)]

            # gerando heatmaps das Médias
            avg_imagens = []
            for partition in partitions:
                _titulo = f'Médias {partition[0]+1}-{partition[-1]+1}'
                df_media_filtrado = globals.crunched_df.iloc[partition]
                df_media_filtrado_formatado = formatDf(df_media_filtrado)
                heatmap_media = generate_heatmap(df_media_filtrado_formatado, 'YlOrRd')
                heatmap_media.figure.savefig(f'{_titulo}.png', bbox_inches='tight', pad_inches=0.05)
                avg_imagens.append(PIL.Image.open(f'{_titulo}.png'))
                image_filenames.append(f'{_titulo}.png')


            # gerando heatmaps dos Desvios Padrão
            std_imagens = []
            for partition in partitions:
                _titulo = f'Desvios Padrão {partition[0]+1}-{partition[-1]+1}'
                df_dp_filtrado = globals.crunched_std.iloc[partition]
                df_dp_filtrado_formatado = formatDf(df_dp_filtrado)
                heatmap_dp = generate_heatmap(df_dp_filtrado_formatado, 'gray')
                heatmap_dp.figure.savefig(f'{_titulo}.png', bbox_inches='tight', pad_inches=0.05)
                std_imagens.append(PIL.Image.open(f'{_titulo}.png'))
                image_filenames.append(f'{_titulo}.png')

            h_percentages = [len(p) / max_rows for p in partitions]
            page_data = [[a,b,hp] for a,b,hp in list(zip(avg_imagens, std_imagens, h_percentages))]
            page_data = [page_data[:1]] + [page_data[1:][i:i+2] for i in range(0, len(page_data[1:]), 2)]
            tempfiles = [f"temp_page_{i}.pdf" for i in range(len(page_data))]

            # Iterando pelas páginas
            for i,pg in enumerate(page_data):
                init_offset = 65
                c = canvas.Canvas(tempfiles[i])
                page_w, page_h = letter

                # Cabeçalho
                c.drawImage('cabecalho.jpeg', inch-8, page_h-50,page_w-inch-52,50)

                if i == 0:
                    init_offset = (inch*1.2)

                    # Título
                    message = Paragraph(titulo, ParagraphStyle(titulo, fontName="helvetica-Bold", fontSize=16))
                    w, h = message.wrap(page_w, page_h)
                    message.drawOn(c, inch, page_h-65)

                    for _text, _style in text_data:
                        if _text:
                            t = Paragraph(_text, ParagraphStyle(_text, fontName=f"helvetica{_style}", fontSize=12))
                            w, h = t.wrap(page_w, page_h)
                            t.drawOn(c, inch, page_h-init_offset)
                        init_offset += 12

                # Adicionando as imagens
                acc_offset = 0
                for a,b,hp in pg:
                    w,h = a.size
                    desired_h = 4.75 * inch * hp
                    desired_w = 4.5 * inch * min(len(numeric_cols), 32) / 45
                    spacing_x = 0.25 * inch
                    x_offset = (page_w - 2 * desired_w) / 2
                    y_offset = page_h - desired_h - init_offset - acc_offset
                    acc_offset += desired_h * 1.0625
                    c.drawImage(ImageReader(a), x_offset-(spacing_x/2), y_offset, width=desired_w, height=desired_h)
                    c.drawImage(ImageReader(b), x_offset+desired_w+(spacing_x/2), y_offset, width=desired_w, height=desired_h)
                c.save()

            # Juntando páginas
            merger = PdfMerger()
            for t in tempfiles:
                merger.append(t)
            merger.write(filename)
            merger.close()

            # Limpando arquivos gerados
            for f in image_filenames + tempfiles:
                os.remove(f)
        ###################################################################################

        def secao2():
            st.subheader('**Seção 2 - Visão dos Dados e Gráficos de Mapas de Calor**')
            st.markdown('''
                        Esta seção traz uma análise visual da base de dados, fornecendo mapas de calor para a média
                        (*Gráfico 1*) e desvio padrão (*Gráfico 2*) dos fatores disponibilizados para cada um dos municípios.
                        Mapa de Calor, também conhecido como Heatmap, é uma visualização gráfica que usa cores para representar a intensidade dos valores
                        em uma matriz de dados. Cada célula da matriz é colorida de acordo com seu valor, facilitando a identificação de
                        padrões, tendências e anomalias nos dados.
                        **Média**: É a soma de todos os valores de um conjunto dividida pelo número de valores.
                        Representa o valor médio
                        **Desvio padrão**: Mede a dispersão dos valores em relação à média. Mostra o quanto os valores variam da média.
                        ''')
            st.markdown('''Importante:
                        Nos gráficos referentes aos Mapas de Calor:
                        As linhas representam os municípios, que estão em ordem alfabética;
                        As colunas representam os fatores selecionados pelo usuário na base de dados''')

            text_secao2 = [
                ("Esta seção traz uma análise visual da base de dados, fornecendo mapas de calor para", ""),
                ("a média (Gráfico 1) e desvio padrão (Gráfico 2) dos fatores disponibilizados para cada ",""),
                ("um dos municípios.",""),
                ("Mapa de Calor, também conhecido como Heatmap, é uma visualização gráfica que usa",""),
                ("cores para representar a intensidade dos valores em uma matriz de dados. Cada célula",""),
                ("da matriz é colorida de acordo com seu valor, facilitando a identificação de padrões,",""),
                ("tendências e anomalias nos dados.",""),
                (" ",""),
                ("Média: ","-Bold"),
                ("- É a soma de todos os valores de um conjunto dividida pelo número de valores.",""),
                ("Representa o valor médio.",""),
                ("Desvio padrão: ","-Bold"),
                ("- Mede a dispersão dos valores em relação à média. Mostra o quanto os valores",""),
                ("variam da média.",""),
                ("",""),
                ("Importante:", "-Bold"),
                ("Nos gráficos referentes aos Mapas de Calor:", ""),
                ("As linhas representam os municípios, que estão em ordem alfabética;", ""),
                ("As colunas representam os fatores selecionados pelo usuário na base de dados;", "")]
            botaos2 = st.button('Gerar Visão Geral de Dados e Mapas de Calor')
            if botaos2:
                col1, col2 = st.columns(2)
                with col1:
                    crunched_df = formatDf(globals.crunched_df)
                    st.dataframe(globals.crunched_df)
                    globals.table_list.append('table4')
                    st.info(f"**Tabela {len(globals.table_list)} - Média**")
                    heatmap1 = generate_heatmap(crunched_df, 'YlOrRd')
                    st.pyplot(heatmap1.figure)
                    globals.graphic_list.append('graph1')
                    st.info(f'Gráfico {len(globals.graphic_list)} - Mapa de Calor (Heatmap) da Média dos Dados dos Municípios')

                with col2:
                    crunched_std = formatDf(globals.crunched_std)
                    st.dataframe(globals.crunched_std)
                    globals.table_list.append('table5')
                    st.info(f"**Tabela {len(globals.table_list)} - Desvio Padrão**")
                    heatmap2 = generate_heatmap(crunched_std, 'gray')
                    st.pyplot(heatmap2.figure)
                    globals.graphic_list.append('graph2')
                    st.info(f'Gráfico {len(globals.graphic_list)} - Mapa de Calor (Heatmap) do Desvião Padrão dos Dados dos Municípios')

                gerar_pdf_secao2e5("secao2.pdf","Seção 2 - Visão dos Dados e Gráficos de Mapas de Calor", text_secao2)


        def arvore_decisao():
            st.subheader('Seção 3.2 - Análise de agrupamentos com Árvore de Decisão')

            st.markdown(''' Esta seção divide-se em duas partes: Primeiro, uma tabela que lista as variáveis utilizadas no modelo de árvore de decisão juntamente com sua importância relativa. Em seguida, a própria imagem da árvore de decisões.
                    ''')

            st.markdown(''' A importância de uma variável indica quanto ela contribui para a decisão final do modelo. Valores mais altos de importância sugerem que a variável tem um impacto maior na previsão do modelo. Dessa forma, quanto maior o valor
                    de sua importância na tabela, maior a importância dessa variável em geral (desconsiderando agrupamentos). Da mesma forma, quanto mais alto ela estiver posicionada na Árvore de Decisão, maior sua importância.
                    Lembrando que essa Árvore de Decisão mostra a importância das variáveis num contexto mais amplo e desconsidera a análise posterior utilizando agrupamentos.
            ''')
            botao_arvore = st.button('Gerar análise de agrupamento com árvore de decisão')

            if botao_arvore:
                df =  globals.current_database
                # Define the features and the target
                #X = df[df.columns[3:-1]]
                #y = df[df.columns[-1]]
                X = df[globals.current_input_columns]
                y = df[globals.current_output_columns]

                # Split the data into training and test sets
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Create a decision tree regressor and fit it to the training data
                reg = DecisionTreeRegressor(max_depth=3, random_state=42)
                reg.fit(X_train, y_train)

                # Create a pandas DataFrame with feature importances
                # feature_importances = pd.DataFrame(reg.feature_importances_,
                #                                 index = X.columns,
                #                                 columns=['importance']).sort_values('importance', ascending=False)
               
                feature_importances = pd.DataFrame({
                    "Variáveis": X.columns,
                    "Importância": reg.feature_importances_
                }).sort_values("Importância", ascending=False)
                

                # st.dataframe(feature_importances, column_config={
                #     '': 'Variáveis',
                #     'importance': 'Importância'
                # })
                st.dataframe(feature_importances)

                
                globals.table_list.append('table2') 
                texto_tabela = f'Importância das Variáveis no Modelo de Árvore de Decisão'
                st.info(f"Tabela {globals.table_list.index('table2')+1} - {texto_tabela}")
                #st.info(f'Tabela 2 -  Importância das Variáveis no Modelo de Árvore de Decisão')

                # Create a larger figure
                fig, ax = plt.subplots(figsize=(20, 20))

                # Plot the decision tree with larger fonts
                tree.plot_tree(reg, ax=ax, feature_names=X.columns, filled=True, fontsize=10)

                # Show the plot in Streamlit
                st.pyplot(fig)

                globals.img_list.append('img2') 
                texto_imagem = f'Árvore de Decisão'
                st.info(f"Figura {globals.img_list.index('img2')+1} - {texto_imagem}")
                #st.info(f"Figura 2 - Árvore de Decisão")
                
                gerar_pdf_3_2({'dados': feature_importances, "tabela_nome": "table2", "tabela_texto":texto_tabela }, {"dados": fig, "imagem_nome":'img2', "imagem_texto": texto_imagem})

        def secao3():
            st.subheader('**Seção 3.1 - Análise de agrupamentos com SHAP**')

            st.markdown('''Nesta seção, apresentamos os grupos identificados e as variáveis que mais influenciaram na formação desses grupos.
            Um "agrupamento" reúne dados que são mais semelhantes em termos de suas características globais. Esses grupos são utilizados na aplicação de IA através de bases de dados (tabelas) fornecidas pela área usuária para o processamento com Redes Neurais Artificiais.
            "Agrupamento" é o processo de reunir, por exemplo, municípios, com base em suas semelhanças, visando realizar triagens para guiar auditorias.''')

            botaos3 = st.button('Gerar Análise de agrupamentos com SHAP')
            if botaos3:
                novo_df = gerar_df_shap()

                def change_color(val):
                    if isinstance(val, (int, float)):
                        if(val < 0):
                            color = 'red'
                        elif(val > 0):
                            color = 'blue'
                       # color = 'red' if val < 0 else 'blue'

                        return f'color: {color}'

                styled_df = novo_df.style.applymap(change_color)

                st.dataframe(styled_df)
                #st.dataframe(novo_df, hide_index=True)


                globals.table_list.append('table6')
                texto_tabela = f'Influências Positivas(azul) e Negativas(vermelho) das Variáveis nos Grupos'
                st.info(f'Tabela {len(globals.table_list)} - {texto_tabela}')
                gerar_pdf_3_1(styled_df, 'table6', texto_tabela)
            
            arvore_decisao()
            
        def gerar_pdf_3_1(styled_df: pd.DataFrame, nome_tabela, texto_tabela):
            # Criando o esqueleto do HTML que irá formar o PDF
            html = f"""<!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            @media print {{
            @page {{
                margin-top: 1.5in;
                size: A4;
            }}
            }}

            body {{
                font-family: "Helvetica";
                font-weight: bold;
            }}

            header {{
                text-align: left
                margin-top: 0px; /* Espaço superior */
            }}

            .table-text {{
                text-align: justify; /* Alinha o texto com justificação */
                margin-bottom: 10px; /* Margem para alinhamento com as extremidades da página */
                font-size: 12px;
            }}
            
            .legenda-tabela {{
                font-size: 10px;
                font-style: italic;
                color:blue;
            }}

            /* Define o tamanho da tabela */
            table {{
                width: 50vw; /* 50% da largura da viewport */
                height: calc(297mm / 2); /* Metade da altura de uma folha A4 */
                border: 1px solid black; /* Borda da tabela */
                border-collapse: collapse; /* Colapso das bordas da tabela */
            }}
            /* Estilo das células */
            td, th {{
                border: 1px solid black; /* Borda das células */
                padding: 4px; /* Espaçamento interno das células */
                text-align: center; /* Alinhamento do texto */
                font-size: 12px; /* Tamanho da fonte */
            }}

            .mensagem {{
                text-align: center; /* Centraliza o texto */
            }}

            .texto-clusters {{
                font-size: 12px; /* Tamanho do texto */
            }}

            .evitar-quebra-pagina {{
                page-break-inside: avoid; /* Evita quebra de página dentro do bloco */
            }}

            .container {{
                text-align: center;
                position: relative;
                width: 500px;
            height: 500px;
            }}

            .imagem-sobreposta {{
                position: absolute;
                bottom: 420px;
                right: -180px;
                width: 50px;
                height: 50px;
            }}

            </style>
            </head>

            <body>
            <header>
                <h2>3. Análise dos agrupamentos</h2>
            </header>
            <h3> Análise dos agrupamentos com SHAP</h3>
            <p class="table-text">Nesta seção, apresentamos os grupos identificados e as variáveis que mais influenciaram na formação desses grupos.
            Um "agrupamento" reúne dados que são mais semelhantes em termos de suas características globais. Esses grupos são utilizados na aplicação de IA através de bases de dados (tabelas) fornecidas pela área usuária para o processamento com Redes Neurais Artificiais.
            "Agrupamento" é o processo de reunir, por exemplo, municípios, com base em suas semelhanças, visando realizar triagens para guiar auditorias..</p>
            
            <div class="evitar-quebra-pagina">
            *-*-*-*-*
            
            <p class="legenda-tabela">tabela_secao_3</p>
            </div>

            <div class="evitar-quebra-pagina">
            <p class="mensagem">Mapa SOM completo</p>
            ***
            </div>
            
            </body>
            </html>
            """
            
            
            tabela_df = globals.shapsom_data.copy()
            tabela_unica = tabela_df.drop_duplicates(subset=['Cor Central', 'Grupo'])
            
            html = html.replace('*-*-*-*-*', styled_df.to_html())
            cores = tabela_unica["Cor Central"].tolist()
           
            for i in range(len(cores)):
                html = html.replace(f'level0 col{i+1}"', f'level0 col{i+1}" style="background-color: {cores[i]}" ')
        
        
            html = html.replace('tabela_secao_3', f"Tabela {globals.table_list.index(nome_tabela)+1} - {texto_tabela}")
            path = os.path.join(f"secao3_3_1.pdf")
            weasyprint.HTML(string=html).write_pdf(path)

        def gerar_pdf_3_2(tabela_arvore_decisao, imagem_arvore_decisao):
            # Criando o esqueleto do HTML que irá formar o PDF
            html = f"""<!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            @media print {{
            @page {{
                margin-top: 1.5in;
                size: A4;
            }}
            }}

            body {{
                font-family: "Helvetica";
                font-weight: bold;
            }}

            header {{
                text-align: left
                margin-top: 0px; /* Espaço superior */
            }}

            .table-text {{
                text-align: justify; /* Alinha o texto com justificação */
                margin-bottom: 10px; /* Margem para alinhamento com as extremidades da página */
                font-size: 12px;
            }}
            
            .legenda-tabela {{
                font-size: 10px;
                font-style: italic;
                color:blue;
            }}

            /* Define o tamanho da tabela */
            table {{
                width: 50vw; /* 50% da largura da viewport */
                height: calc(297mm / 2); /* Metade da altura de uma folha A4 */
                border: 1px solid black; /* Borda da tabela */
                border-collapse: collapse; /* Colapso das bordas da tabela */
            }}
            /* Estilo das células */
            td, th {{
                border: 1px solid black; /* Borda das células */
                padding: 4px; /* Espaçamento interno das células */
                text-align: center; /* Alinhamento do texto */
                font-size: 12px; /* Tamanho da fonte */
            }}

            .mensagem {{
                text-align: center; /* Centraliza o texto */
            }}

            .texto-clusters {{
                font-size: 12px; /* Tamanho do texto */
            }}

            .evitar-quebra-pagina {{
                page-break-inside: avoid; /* Evita quebra de página dentro do bloco */
            }}
            
            .a4-size {{
                width: 210mm; /* Largura de uma folha A4 em milímetros */
                height: auto; /* Altura proporcional */
                max-width: 100%; /* Garante que a imagem não ultrapasse a largura da janela */
            }}


            </style>
            </head>

            <body>
            <!--- *())*()* aqui vai ser caso n tenha o anterior--->
            <h3> Análise de agrupamentos com Árvore de Decisão </h3>
            <p class="table-text"> Esta seção divide-se em duas partes: Primeiro, uma tabela que lista as variáveis utilizadas no modelo de árvore de decisão juntamente com sua importância relativa. Em seguida, a própria imagem da árvore de decisões.<br>
            
            
            
            A importância de uma variável indica quanto ela contribui para a decisão final do modelo. Valores mais altos de importância sugerem que a variável tem um impacto maior na previsão do modelo. Dessa forma, quanto maior o valor
            de sua importância na tabela, maior a importância dessa variável em geral (desconsiderando agrupamentos). Da mesma forma, quanto mais alto ela estiver posicionada na Árvore de Decisão, maior sua importância.
            Lembrando que essa Árvore de Decisão mostra a importância das variáveis num contexto mais amplo e desconsidera a análise posterior utilizando agrupamentos.
            
            </p>
            
            <div class="evitar-quebra-pagina">
            *-*-*-*-*
            <p class="legenda-tabela">tabela_secao_3_2</p>
            </div>

            <div class="evitar-quebra-pagina">
            ******
            <p class="legenda-tabela">imagem_secao_3_2</p>
            </div>

            </body>
            </html>
            """
            
            # caso nao tiver a secao anterior de SHAP, colocar isso no inicio
            # header_inicio = '''<header>
            #    <h2>3. Análise dos agrupamentos</h2>
            #    </header>'''
            #tabela_arvore_decisao['dados'] = 
            
            try:
                html = html.replace('*-*-*-*-*', tabela_arvore_decisao['dados'].to_html())
                html = html.replace('tabela_secao_3_2', f"Tabela {globals.table_list.index(tabela_arvore_decisao['tabela_nome'])+1} - {tabela_arvore_decisao['tabela_texto']}")
                
                caminho_salvo = "arvore_decisao.png"
                caminho_atual = os.getcwd()
                caminho_final = os.path.join(caminho_atual,f"{caminho_salvo}")
                imagem_arvore_decisao['dados'].savefig("arvore_decisao.png")
                
                html = html.replace('******', f'<img src="file:///{caminho_final}" alt="Árvore de decisão" class="a4-size">')
                html = html.replace('imagem_secao_3_2', f"Imagem {globals.img_list.index(imagem_arvore_decisao['imagem_nome'])+1} - {imagem_arvore_decisao['imagem_texto']}")
            except Exception as error:
                print(error)
            
            path = os.path.join(f"secao3_3_2.pdf")
            weasyprint.HTML(string=html).write_pdf(path)
            
            
        def secao4():
            #Criando as variáveis

            tabela_df = globals.shapsom_data.copy()
            tabela_df.drop(['Municípios', 'Nota', 'SHAP Normalizado', 'x', 'y', 'Cor', 'SHAP Original'], axis=1, inplace=True)
            tabela_unica = tabela_df.drop_duplicates(subset=['Cor Central', 'Grupo'])
            nome_variavel_coluna = 'Nome Variável'
            grupos_colunas = sorted(tabela_unica['Grupo'].unique())
            colunas_novo_df = [nome_variavel_coluna] + [f'Grupo {grupo}' for grupo in grupos_colunas]
            novo_df = pd.DataFrame(columns=colunas_novo_df)

            original_df = globals.crunched_df
            df = globals.shapsom_data
            max_grupo = df['Grupo'].max()
            df_expandido = df.assign(municipios=df['Municípios'].str.split(',')).explode('municipios').reset_index(drop=True)
            df_expandido = df_expandido.drop(columns=['Municípios', 'x', 'y'])

            output_column = original_df.columns[-1]
            output_values = original_df.iloc[:, -1]
            df_expandido[output_column] = output_values.values
            novo_df = gerar_df_shap()

            grupos = df_expandido.groupby('Grupo')

            html = f"""<!DOCTYPE html>
            <html lang="en">
                <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                @media print {{
                @page {{
                    margin-top: 1.5in;
                    size: A4;
                }}
                }}

                body {{
                    font-family: "Helvetica";
                    font-weight: bold;
                    font-size: 12px;
                }}

                header {{
                    text-align: left;
                    margin-top: 0px; /* Espaço superior */
                }}

                .table-text {{
                    text-align: justify; /* Alinha o texto com justificação */
                    margin-bottom: 10px; /* Margem para alinhamento com as extremidades da página */
                    font-size: 12px;
                }}

                /* Define o tamanho da tabela */
                table {{
                    width: 50vw; /* 50% da largura da viewport */
                    height: calc(297mm / 2); /* Metade da altura de uma folha A4 */
                    border: 1px solid black; /* Borda da tabela */
                    border-collapse: collapse; /* Colapso das bordas da tabela */
                }}
                /* Estilo das células */
                td, th {{
                    border: 1px solid black; /* Borda das células */
                    padding: 4px; /* Espaçamento interno das células */
                    text-align: center; /* Alinhamento do texto */
                    font-size: 12px; /* Tamanho da fonte */
                }}


                .mensagem {{
                    text-align: center; /* Centraliza o texto */
                }}

                .texto-clusters {{
                    font-size: 12px; /* Tamanho do texto */
                }}

                .evitar-quebra-pagina {{
                    page-break-inside: avoid; /* Evita quebra de página dentro do bloco */
                }}

                .legenda-tabela {{
                    font-size: 10px;
                    font-style: italic;
                    color: blue;
                }}

                .legenda-mapa {{
                    font-size: 10px;
                    font-style: italic;
                    color: blue;
                    page-break-after: always;
                }}

                </style>
                </head>

                <body>
                <header>
                    <h2>4. Diferenças entre agrupamentos</h2>
                </header>
                <p class="table-text">A análise comparativa entre os agrupamentos é conduzida combinando todas as informações
                        da "Análise de Agrupamentos" (Seção 3), organizando-as em uma disposição paralela. Isso tem o
                        objetivo de destacar de forma mais clara as disparidades nas estruturas dos agrupamentos.</p>

                <div class="evitar-quebra-pagina">
                </div>


                ---===---


                </body>

                </html>
                """

            html_clusters = ''
            st.subheader('Seção 4 - Diferenças entre grupos')
            st.markdown('''A análise comparativa entre os agrupamentos é conduzida combinando todas as informações
                        da "Análise de Agrupamento" (Seção 3), organizando-as em uma disposição paralela. Isso tem o
                        objetivo de destacar de forma mais clara as disparidades nas estruturas dos agrupamentos.''')
            botaos4 = st.button('Gerar Diferenças entre grupos')
            if botaos4:
                for i in range(max_grupo+1):
                    if i in grupos.groups:
                        #Tabelas
                        grupo_df = grupos.get_group(i)
                        media_valor = grupo_df[output_column].mean()
                        media_valor = media_valor.round(2)
                        cor_grupo = grupo_df['Cor'].iloc[0]
                        lista_cores = grupo_df['Cor'].tolist()

                        st.subheader(f'Grupo {i}')
                        st.text(f'Média de {output_column} do grupo {i}: {media_valor}')

                        def apply_color(val):
                            return f"background-color: {cor_grupo}; "

                        st.dataframe(grupo_df.style.applymap(apply_color).format({output_column:'{:.2f}'}), column_order=['municipios', 'Nota', 'Grupo', 'Cor', output_column] ,column_config={
                            'municipios': 'Municípios',
                            'Nota': None,
                            'Grupo': 'Grupo',
                            'Cor': None
                            }
                        )
                        html_clusters += f'<h3 style="background-color: {cor_grupo}"> Grupo {i} </h3>'
                        html_clusters += f'<p class="texto-clusters">{output_column} do Grupo {i}: {media_valor}</p>'
                        html_clusters += f'<p class="texto-clusters">Cidades do cluster: {", ".join(sorted(set(grupo_df["municipios"])))}</p>'

                        globals.table_list.append(f'table{i+4}')
                        st.info(f"**Tabela {len(globals.table_list)} - Municípios do Grupo {i}**")

                        df_shap_grupo = novo_df.iloc[:, [0, i]]
                        grupo_colunas = [col for col in df_shap_grupo.columns if col.startswith('Grupo')]
                        # Lista para armazenar os resultados
                        filtered_rows = []

                        for coluna in grupo_colunas:
                            max_val = df_shap_grupo[coluna].max()
                            min_val = df_shap_grupo[coluna].min()

                            max_row = df_shap_grupo[df_shap_grupo[coluna] == max_val]
                            min_row = df_shap_grupo[df_shap_grupo[coluna] == min_val]

                            filtered_rows.append(max_row)
                            filtered_rows.append(min_row)

                        # Concatenando todas as linhas filtradas
                        filtered_df = pd.concat(filtered_rows).drop_duplicates().reset_index(drop=True)
                        st.dataframe(filtered_df)
                        globals.table_list.append(f'table2_{i+4}')
                        st.info(f"**Tabela {len(globals.table_list)} - Valores Que Mais Influenciam Positivamente e Negativamente no Grupo {i}**")

                        html_df = filtered_df.to_html(index=False)
                        html_df += f'<p class="legenda-tabela"> Tabela {len(globals.table_list) - i} - Valores Que Mais Influenciam Positivamente e Negativamente no Grupo {i}</p>'
                        html_clusters += html_df

                        #Mapas

                        def generate_map():
                            # Convert the DataFrame to a GeoDataFrame
                            gdf = gpd.read_file('PE_Municipios_2022.zip')
                            gdf = gdf.merge(grupo_df[[grupo_df.columns[2],grupo_df.columns[-2]]], left_on='NM_MUN', right_on=grupo_df.columns[-2])

                            fig, ax = plt.subplots(1, 1)

                            custom_cmap = mcolors.ListedColormap([cor_grupo])

                            values_range = np.linspace(0, 1, 10)

                            # Plot the map and apply the custom colormap
                            m = gdf.explore(column=grupo_df.columns[2], cmap=custom_cmap, vmin=0, vmax=1, fitbounds="locations", map_kwrds={'scrollWheelZoom': 4})

                            components.html(m._repr_html_(), height=400)

                            outfp = f"mapa{i}.html"

                            m.save(outfp)

                        with st.spinner('Gerando mapa...'):
                            if os.path.exists(f'mapa{i}.html'):
                                m_repr_html_ = open(f'mapa{i}.html').read()
                                components.html(m_repr_html_, height=400)
                            else:
                                generate_map()

                        globals.img_list.append(f'img{i+3}')
                        st.info(f"**Figura {len(globals.img_list)} - Mapa de Municípios do Grupo {i}**")

                        html_to_png(f'mapa{i}.html', f'mapa{i}.png')
                        caminho_atual = os.getcwd()
                        caminho_final = os.path.join(caminho_atual,f"mapa{i}.png")
                        html_clusters += f'<img src="file:///{caminho_final}" alt="Screenshot">'
                        html_clusters += f'<p class="legenda-mapa"> Figura {len(globals.img_list)} - Mapa de Municípios do Grupo {i}</p>'

                html = html.replace('---===---', html_clusters)
                path = os.path.join(f"secao3_4.pdf")
                weasyprint.HTML(string=html).write_pdf(path)

        def secao5():
            st.subheader('**Seção 5 - Filtro de Triagem**')
            st.markdown('''Esta seção, assim como na seção 2, traz uma análise visual da base de dados, porém agora em uma fatia dos dados
                        escolida pelo usuário.
                        Essa visualização é útil para analizar de forma mais detalhada elementos de interesse da base de dados.''')
            st.markdown('''Como essa seção funciona:
                        Ela usa os valores fornecidos pelo usuário nos campos abaixo para filtrar
                        a última coluna da base (saída), exibindo as tabelas e mapas de calor para
                        o conjuto de dados cujo o valor da coluna de saída esteja dentro do intervalo
                        de valores fornecido pelo usuário.''')

            last_column_name = globals.crunched_df.columns[-1]

            col1, col2 = st.columns(2)
            with col1:
                val_min = st.number_input("Valor mínimo", value= 0, placeholder="Digite um número", min_value = 0, max_value=100)
            with col2:
                val_max = st.number_input("Valor máximo", value= 70, placeholder="Digite um número", min_value = 0, max_value=100)

            def filtrar_df(df, minimo, maximo):
                    df_filtrado = df[(df.iloc[:, -1] >= (minimo/100)) & (df.iloc[:, -1] <= (maximo/100))]
                    return df_filtrado

            text_secao5 = [
                ("Esta seção, assim como na seção 2, traz uma análise visual da base de dados, porém ", ""),
                ("agora em uma fatia dos dados escolida pelo usuário. Essa visualização é útil para",""),
                ("analizar de forma mais detalhada elementos elementos de interesse da base de dados.",""),
                ("",""),
                ("Importante:", "-Bold"),
                (f'- As imagens abaixo mostram os dados cujo o valor da coluna "{last_column_name}" está', ""),
                (f"  compreendido entre {val_min}% e {val_max}%", "")]

            if val_min > val_max:
                st.write("**O valor mínimo deve ser menor que o valor máximo**")
            elif (not (0<= val_min<= 100)) or (not (0 <= val_max <= 100)):
                st.write("**Os valores devem estar entre 0 e 100**")
            else:
                botao = st.button("Gerar Filtro", type='primary')

                if botao:
                    media_df_filtrado = filtrar_df(globals.crunched_df, val_min, val_max)
                    std_filtrado = globals.crunched_std.iloc[media_df_filtrado.index]
                    crunched_df = formatDf(media_df_filtrado)
                    crunched_std = formatDf(std_filtrado)
                    if media_df_filtrado.empty:
                        st.write("**Não há dados nesse intevalo de valores**")
                    else:
                        with col1:
                            st.dataframe(media_df_filtrado)
                            globals.table_list.append('table5x1')
                            st.info(f"**Tabela {len(globals.table_list)} - Média**")
                            heatmap1 = generate_heatmap(crunched_df, 'YlOrRd')
                            st.pyplot(heatmap1.figure)
                            globals.graphic_list.append('graph5x1')
                            st.info(f"**Gráfico {len(globals.graphic_list)} - Média**")

                        with col2:
                            st.dataframe(std_filtrado)
                            globals.table_list.append('table5x2')
                            st.info(f"**Tabela {len(globals.table_list)} - MapaDesvio Padrão**")
                            heatmap2 = generate_heatmap(crunched_std, 'gray')
                            st.pyplot(heatmap2.figure)
                            globals.graphic_list.append('graph5x2')
                            st.info(f"**Gráfico {len(globals.graphic_list)} - Desvio Padrão**")

                        gerar_pdf_secao2e5("secao5.pdf","Seção 5 - Filtro de Triagem", text_secao5, val_min, val_max)


        st.title('Análise Por Grupos com SHAP/SOM')
        for i,secao in enumerate([secao1, secao2, secao3, secao4, secao5]):
            try:
                secao()
                st.divider()
                quebra_pagina()
            except:
                st.subheader(f'Seção {i+1} - Erro')


    pagina_anomalias()



