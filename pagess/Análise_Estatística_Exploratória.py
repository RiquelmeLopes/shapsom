from io import StringIO
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import plotly.express as px
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import branca.colormap as cm
from branca.colormap import linear
from PIL import Image
import folium
import json
from streamlit_folium import st_folium
import weasyprint
import kaleido
import matplotlib.pyplot as plt
import globals
import plotly.graph_objects as go
from my_utils import add_cabecalho
import base64
from pypdf import PdfMerger
from capa import criar_capa
import locale
from datetime import datetime
import geopandas as gpd

import os

def juntar_pdfs(pdfs):
  merger = PdfMerger()
  for pdf in pdfs:
      merger.append(pdf)

  nome = 'Análise Estatística Exploratória.pdf'
  merger.write(nome)
  merger.close()

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

def pagina_analise_estatistica_exploratoria():
    st.title("Sistema de Apoio a Auditorias do Tribunal de Contas do Estado 📊")
    st.subheader("Análise Estatística Exploratória")

    has_databases = True
    try:
        has_databases = has_databases and globals.current_database is not None
    except:
        has_databases = False

    if has_databases:

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
                    <h1>Análise Estatística Exploratória</h1>
                </header>
                
                <div class="evitar-quebra-pagina">
                </div>


                ---===---


                </body>

                </html>
                """

        html_clusters = ''

        df =  globals.current_database
        st.subheader('Mapa de Análise da Variável Alvo')

        st.markdown('''O mapa de análise da variável alvo apresenta uma análise geoespacial dos municípios do estado de Pernambuco. As diferentes tonalidades de cores no 
                    mapa representam as variações nos níveis da variável de escolha. As áreas em tons mais escuros indicam um desempenho superior, 
                    enquanto as áreas em tons mais claros refletem um desempenho inferior. Esta visualização detalhada é crucial para identificar regiões que necessitam de 
                    intervenções mais intensivas, ajudando a direcionar políticas públicas e recursos de forma mais eficiente.''')
 
        with st.expander('Visualizar mapa de Análise da Variável Alvo', expanded=True):
            def generate_map():
                # Convert the DataFrame to a GeoDataFrame
                gdf = gpd.read_file('PE_Municipios_2022.zip')
                gdf = gdf.merge(df[[df.columns[0],df.columns[-1]]], left_on='NM_MUN', right_on=df.columns[0])

                fig, ax = plt.subplots(1, 1)

                df[df.columns[-1]] = df[df.columns[-1]].round(2)

                bounds = gdf.total_bounds  # Get the bounds of the data
                center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
                m = gdf.explore(df.columns[-1], cmap='RdBu', fit_bounds=True, map_kwds={'location': center, 'zoom_start':4})

                components.html(m._repr_html_(), height=400)

                outfp = r"mapa.html"

                m.save(outfp)

            with st.spinner('Gerando mapa...'):
                if os.path.exists('mapa.html'):
                    m_repr_html_ = open('mapa.html').read()
                    components.html(m_repr_html_, height=600)
                else:
                    generate_map()

            st.info(f'Figura 1 - Mapa Colorido Baseado na Variação de Valores da Variável Alvo.')

        check_mapa = st.checkbox('Gostaria de adicionar o Mapa de Análise da Variável Alvo ao relatório?')
        if check_mapa:
            html_to_png(f'mapa.html', f'mapa.png')
            caminho_atual = os.getcwd()
            caminho_mapa = os.path.join(caminho_atual,f"mapa.png")
            html_clusters += '<h2> Mapa de Análise de Variável </h2>'
            html_clusters += '''<p> O mapa de análise da variável alvo apresenta uma análise geoespacial dos municípios do estado de Pernambuco. As diferentes tonalidades de cores no 
                                    mapa representam as variações nos níveis da variável de escolha. As áreas em tons mais escuros indicam um desempenho superior, 
                                    enquanto as áreas em tons mais claros refletem um desempenho inferior. Esta visualização detalhada é crucial para identificar regiões que necessitam de 
                                    intervenções mais intensivas, ajudando a direcionar políticas públicas e recursos de forma mais eficiente. </p>'''
            html_clusters += f'<img src="file:///{caminho_mapa}" alt="Screenshot">'
            html_clusters += f'<p class="legenda-mapa"> Figura 1 - Mapa Colorido Baseado na Variação de Valores da Variável Alvo </p>' 
        
        st.divider()

        st.subheader('Análise Estatística')

        dfmc = df.groupby(df.columns[0])[df.columns[-1]].apply(lambda x: x.mode().iloc[0]).reset_index()
        dfm = df.groupby(df.columns[0])[df.columns[3:]].apply(lambda x: x.mode().iloc[0]).reset_index()
        dfmc[dfmc.columns[-1]] = dfmc[dfmc.columns[-1]].round(2)

        st.markdown('''A tabela de estatísticas fornece um resumo estatístico descritivo da variável alvo para os municípios analisados. Os valores apresentados 
                    incluem a contagem de observações, média, desvio padrão, valores mínimos e máximos, bem como os percentis 25%, 50% 
                    (mediana) e 75%. Estas estatísticas são úteis para entender a distribuição e a variabilidade entre os municípios.''')
        
        
        with st.expander('Visualizar Estatísticas'):
            dfmc_copy = dfmc[dfmc.columns[-1]].describe().to_frame().T
            st.dataframe(dfmc_copy, column_config={
                'count': 'Contagem',
                'mean': 'Média',
                'std': 'Desvio Padrão',
                'min': 'Mínimo',
                '25%': '1° Quartil',
                '50%': 'Mediana',
                '75%': '3° Quartil',
                'max': 'Máximo'
            })            
            st.info(f'Tabela 1 - Estatísticas Descritivas da Variável Alvo')

        check_analise = st.checkbox('Gostaria de adicionar a Análise Estatística ao relatório?')
        if check_analise:
            html_clusters += '<h2> Análise Estatística </h2>'
            html_clusters += '''<p> A tabela de estatísticas fornece um resumo estatístico descritivo da variável alvo para os municípios analisados. Os valores apresentados 
                        incluem a contagem de observações, média, desvio padrão, valores mínimos e máximos, bem como os percentis 25%, 50% 
                        (mediana) e 75%. Estas estatísticas são úteis para entender a distribuição e a variabilidade entre os municípios. </p>'''
            html_df = dfmc_copy.to_html(index=False)
            html_df += f'<p class="legenda-tabela"> Tabela 1 - Estatísticas Descritivas da Variável Alvo </p>'
            html_clusters += html_df
            
        st.divider()

        st.subheader('Gráfico de Dispersão')
        st.markdown('''O gráfico de dispersão faz parte de uma análise estatística mais ampla apresentada no relatório, que visa 
                        explorar a variabilidade e o desempenho geral dos municípios. Ele permite identificar quais municípios
                        apresentam desempenhos extremos, tanto positivos quanto negativos, e como os valores da nossa variável alvo estão dispersos
                        em relação à media. Esta visualização facilita uma identificação mais superficial das áreas que necessitam de maior atenção e recursos.''')
        
        
        with st.expander('Visualizar Gráfico de Dispersão'):
            opcoes = df.columns[3:].tolist()
            variavel = st.selectbox('Selecione a variável', opcoes, index= len(opcoes)-1)
            nome_variavel_padrao = df.columns[-1]
            nome_df = globals.current_label_columns
            st.markdown(f'Caso queira trocar a variável padrão, que é "{nome_variavel_padrao}", sua variável de saída padrão, selecione uma nova variável e gere o gráfico de dispersão novamente.')
            # Create a scatterplot of the penultimate column
            fig = px.scatter(
                dfm.reset_index(),
                y=variavel,
                x=dfmc.columns[0],
                # size=dfmc.columns[-1],                
                color=variavel,
                color_continuous_scale='icefire_r',
            )

            # Show the scatterplot in Streamlit
            st.plotly_chart(fig, use_container_width=True)
            st.info(f'Gráfico 1 - Gráfico de Dispersão da Distribuição da Variável Selecionada por Município')
            fig.write_image("scatter_plot.png")
            caminho_atual = os.getcwd()
            caminho_grafico = os.path.join(caminho_atual,f"scatter_plot.png")

        check_grafico = st.checkbox('Gostaria de adicionar o gráfico de dispersão ao relatório?')
        if check_grafico:
            html_clusters += '<h2> Gráfico de Dispersão </h2>'
            html_clusters += '''<p> O gráfico de dispersão faz parte de uma análise estatística mais ampla apresentada no relatório, que visa 
                            explorar a variabilidade e o desempenho geral dos municípios. Ele permite identificar quais municípios
                            apresentam desempenhos extremos, tanto positivos quanto negativos, e como os valores da nossa variável alvo estão dispersos
                            em relação à media. Esta visualização facilita uma identificação mais superficial das áreas que necessitam de maior atenção e recursos. </p>'''
            html_clusters += f'<img src="file:///{caminho_grafico}" alt="Screenshot">'
            html_clusters += f'<p class="legenda-tabela"> Gráfico 1 - Gráfico de Dispersão da Distribuição da Variável Selecionada por Município </p>'

        html = html.replace('---===---', html_clusters)
        path = os.path.join(f"Análise Estatística Exploratória.pdf")
        weasyprint.HTML(string=html).write_pdf(path)

        st.divider()
        st.subheader('Geração de Relatório de Análise Estatística Exploratória')
        titulo_estatistica = st.text_input("**Informe o nome do relatório de Análise Estatística a ser gerado**", help='Esse nome será utilizado no título do arquivo de PDF que será gerado ao fim da aplicação.')
        gerar_relatorio_estatistica = st.button('Clique aqui para gerar seu relatório de Análise Estátistica')
        if gerar_relatorio_estatistica:
            criar_capa('Análise Estatística')
            arquivos = ['capa.pdf', 'Análise Estatística Exploratória.pdf']
            juntar_pdfs(arquivos)
            add_cabecalho('Análise Estatística Exploratória.pdf')
            with open('Análise Estatística Exploratória.pdf', "rb") as f:
                    pdf_contents = f.read()

                # Baixar o PDF quando o botão é clicado
            b64 = base64.b64encode(pdf_contents).decode()
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            data_atual = datetime.now()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatório_Estatística_{titulo_estatistica}_{data_atual}.pdf"><button style="background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">Baixar Relatório de Análise Estatística</button></a>', unsafe_allow_html=True)

        
        st.divider()
        st.markdown('Você chegou ao fim da página de Análises Estatística Exploratória! Para prosseguir com a aplicação, volte para o topo da página e clique em "Análise Por Grupos" para prosseguir até a próxima página.')