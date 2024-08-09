from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from my_utils import add_cabecalho
from reportlab.lib import colors
from datetime import datetime
from pypdf import PdfMerger
from capa import criar_capa
import streamlit as st
from tqdm import tqdm
import pandas as pd
import warnings
import globals
import zipfile
import base64
import locale
import os

warnings.filterwarnings("ignore")

global current_list_labels
global shape_results
global shap_columns
global cluster_dict

def verifica_gerados(diretorio):
    # Lista de possíveis PDFs
    criar_capa('Análise por Agrupamentos')
    secoes = ['capa.pdf','secao1.pdf', 'secao2.pdf', 'secao3_3_1.pdf','secao3_3_2.pdf','secao4.pdf', 'secao5.pdf', 'secao6.pdf', 'secao7.pdf']
    # Lista para armazenar os PDFs gerados
    gerados = []
    # Verificar a existência de cada PDF
    for secao in secoes:
        caminho = os.path.join(diretorio, secao)
        if os.path.isfile(caminho):
            gerados.append(secao)
    return gerados

def juntar_pdfs(nome_arquivo):
    caminho = os.getcwd()
    pdfs = verifica_gerados(caminho)
    merger = PdfMerger()
    
    for pdf in pdfs:
        merger.append(pdf)

    nome = nome_arquivo + '.pdf'
    merger.write(nome)
    merger.close()

def relatorio_municipios():
    # Gerar Relatório de Agrupamento
    st.divider()
    st.subheader('Geração do Relatório de Auditoria')
    title = st.text_input("**Informe o nome do relatório a ser gerado**", help='Esse nome será utilizado no título do arquivo de PDF que será gerado ao fim da aplicação.')
    nome_arquivo = title + '.pdf'
    gerar_relatorio = st.button('Clique aqui para gerar seu relatório de Análise de Agrupamentos')
    if gerar_relatorio:
        juntar_pdfs(title)
        add_cabecalho(nome_arquivo)
        with open(nome_arquivo, "rb") as f:
                pdf_contents = f.read()

        # Baixar o PDF quando o botão é clicado
        b64 = base64.b64encode(pdf_contents).decode()
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        data_atual = datetime.now()
        st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatório_Agrupamentos_{title}_{data_atual}.pdf"><button style="background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">Baixar Relatório de Análise de Agrupamentos</button></a>', unsafe_allow_html=True)
    # ------------------------------

    st.divider()
    st.subheader('Relatório Individual dos Municípios')

    list_all_labels = [m for m in globals.shape_results.keys()]

    with st.form("form"):
        st.subheader("Selecione os Municípios")
        list_selected_labels = st.multiselect("Municípios", list_all_labels, help='Selecione os municípios para gerar os relatórios individuais de cada um deles', key="my_multiselect")
        use_mark_all = st.checkbox("Selecionar Todos", help="Selecione para gerar o relatório de todos os municípios")
        button = st.form_submit_button('Executar')

    if button:
        globals.current_list_labels = list_all_labels if use_mark_all else list_selected_labels
        gerar_anexos()

# PDF
def gerarSecao(c,tipo,paragrafo,h):
    page_w, page_h = letter
    if(tipo=='p'):
        style_paragrafo = ParagraphStyle("paragrafo", fontName="Helvetica-Bold", fontSize=12, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='t'):
        style_paragrafo = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='t1'):
        style_paragrafo = ParagraphStyle("titulo1", fontName="Times-Bold", fontSize=35, alignment=TA_CENTER, leading=18, encoding="utf-8")
    elif(tipo=='s'):
        style_paragrafo = ParagraphStyle("subtitulo", fontName="Helvetica-Bold", fontSize=14, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='c'):
        style_paragrafo = ParagraphStyle("caption-up", fontName="Times-Bold" , leftIndent=5, rightIndent=1, textColor='#8B4513', fontSize=21, alignment=TA_CENTER, leading=25, borderColor='gray', borderWidth=2, borderPadding=5, encoding="utf-8")
    elif(tipo=='c1'):
        style_paragrafo = ParagraphStyle("caption-down", fontName="Times-Bold" , leftIndent=5, rightIndent=1, textColor='black', fontSize=12, alignment=TA_CENTER, leading=25, borderColor='gray', borderWidth=2, borderPadding=5, encoding="utf-8")

    message_paragrafo = Paragraph(paragrafo, style_paragrafo)
    w_paragrafo, h_paragrafo = message_paragrafo.wrap(page_w -2*inch, page_h)
    message_paragrafo.drawOn(c, inch, page_h - h- h_paragrafo)
    return (c, h+h_paragrafo+30) if tipo != 'c' and tipo != 'c1' else (c, h+h_paragrafo+8)

def gerarLegenda(c,paragrafo,h):
    page_w, page_h = letter
    style_paragrafo = ParagraphStyle("paragrafo", fontName="Helvetica-Oblique", fontSize=13, alignment=4, leading=18, encoding="utf-8", textColor = 'blue')
    message_paragrafo = Paragraph(paragrafo, style_paragrafo)
    w_paragrafo, h_paragrafo = message_paragrafo.wrap(page_w -2*inch, page_h)
    message_paragrafo.drawOn(c, inch, page_h - h- h_paragrafo)
    return c, h+h_paragrafo+20

def gerarTabela(data, columns, j):
    data = [columns]+data

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'WORD'),
    ])

    if  (j==1): col_widths = [52,297,50,75]
    elif(j==2): col_widths = [189,48,189,48]
    elif(j==3 or j==4): col_widths = [237,237]

    table = Table(data, colWidths=col_widths)
    table.setStyle(style)
    return table

def gerarTabelaPdf(c,data,h,start,columns,j):
    page_w, page_h = letter
    if(len(data)>start):
        data2 = []
        end = 0
        for i in range(len(data)-start+1):
            table = gerarTabela(data2,columns,j)
            w_paragrafo, h_paragrafo = table.wrapOn(c, 0, 0)
            if(page_h - h- h_paragrafo< inch):
                end = i
                break

            if(i<len(data)-start):
                data2+= [data[i+start]]
        table.drawOn(c, inch, page_h - h- h_paragrafo)
        return c, h_paragrafo+h, start+end
    else:
        return c, h, start

def quebraPagina(c, posicao, h, tamanho):
    page_w, page_h = letter
    if(posicao % 200 > tamanho):
        c.drawImage('cabecalho.jpeg', inch-8, page_h-50,page_w-inch-52,50)
        c.saveState()
        c.showPage()
        h=65
    return c, h

def gerarSecaoTabela(c,h,dados,columns,j):
    start = 0
    start2 = 0
    while(True):
        c, h, start = gerarTabelaPdf(c,dados,h,start,columns,j)
        if(start==start2):
            break
        else:
            c, h = quebraPagina(c, h, h, 0)
            start2=start
    return c, h

def insert_newlines(text, every=40):
    lines = []
    while len(text) > every:
        split_index = text.rfind(' ', 0, every)
        if split_index == -1:
            split_index = every
        lines.append(text[:split_index].strip())
        text = text[split_index:].strip()
    lines.append(text)
    return '\n\n'.join(lines)

def dividirlinhas(data, every):
    if(len(data)>every):
        data = insert_newlines(data, every=every)
    return data

def ajustarDataFrames(df, colunas, numCar):
     for coluna in colunas:
         df[coluna] = [dividirlinhas(str(linha), numCar) for linha in df[coluna]]
     return df

def gerarDataFrames(municipio, indices_maiores_valores, indices_menores_valores, dados, score_municipio, cell_labels):
    df1 = pd.DataFrame(data={'Índice'       : range(1, len(globals.shap_columns) + 1),
                             'Fatores'      : globals.shap_columns,
                             'Valor'        : [f"{x:.2f}" for x in globals.shape_results[municipio]['data']],
                             'Influência'   : [f"{x:.3f}" for x in globals.shape_results[municipio]['values']]})
    
    df2 = pd.DataFrame(data={'Positivamente': list(reversed([globals.shap_columns[chave] for chave, valor in indices_maiores_valores.items()])) + ['---'] * (3 - len(indices_maiores_valores)),
                             '+'            : list(reversed([f"{valor:.3f}" for chave, valor in indices_maiores_valores.items()])) + ['---'] * (3 - len(indices_maiores_valores)),
                             'Negativamente': list(reversed([globals.shap_columns[chave] for chave, valor in indices_menores_valores.items()])) + ['---'] * (3 - len(indices_menores_valores)),
                             '-'            : list(reversed([f"{valor:.3f}" for chave, valor in indices_menores_valores.items()])) + ['---'] * (3 - len(indices_menores_valores))})
    
    df3 = pd.DataFrame(data={f"Grupo {dados['cluster'] + 1}": [f"{dados['cluster_score']*100:.2f} %"],
                              'Município'                   : [f"{score_municipio*100:.2f} %"]})

    df4 = pd.DataFrame(data={'Nome'                              : [label for label in cell_labels] if len(cell_labels) > 0 else ['---'],
                             dividirlinhas(f"{dados['feature']}",30): [f"{dados['scores'][dados['labels'].index(label)]*100:.2f} %" for label in cell_labels] if len(cell_labels) > 0 else ['---']})
    
    return df1, df2, df3, df4

def gerar_anexos():
    pdf_filenames = []
    st.divider()
    st.write("#### Relatórios Individuais")
    progress_bar = st.progress(0)
    total_iterations = len(globals.current_list_labels) 
    # Caminho da pasta para salvar os PDFs
    save_path = "Relatório dos Municípios"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for i, municipio in tqdm(enumerate(globals.current_list_labels), desc="Gerando Anexos", total=total_iterations, unit="it/s"):
        progress_bar.progress(int((i + 1) / total_iterations * 100))
        with st.expander(municipio, expanded=False):
            dados = {}
            for cluster in globals.cluster_dict.keys():
                for coord in globals.cluster_dict[cluster].keys():
                    if municipio in globals.cluster_dict[cluster][coord]['labels']:
                        dados['cluster'] = globals.cluster_dict[cluster][coord]['cluster']
                        dados['feature'] = list(globals.cluster_dict[cluster][coord]['cluster_scores'].keys())[-1]
                        dados['cluster_score'] = globals.cluster_dict[cluster][coord]['cluster_scores'][dados['feature']]
                        dados['labels'] = globals.cluster_dict[cluster][coord]['labels']
                        dados['scores'] = globals.cluster_dict[cluster][coord]['score'][dados['feature']]

            table1 =  f"<h1 style='font-family: \"Helvetica\"; text-align: center; font-weight: bold;'>{municipio}</h1>"
            table1 +=  '<table style="margin-left: auto; margin-right: auto; margin-top: 40px; width: 627px; border: 2px solid grey;">'
            table1 += f"<caption style='color: #8B4513; caption-side: top; border: 2px solid grey; text-align: center; font-weight: bold; font-size: 23px; padding: 10px 0; '> Resultado da Influência dos Fatores no(a) {dados['feature']} </caption>"
            table1 +=  '<thead>'
            table1 +=  "<tr style='font-size: 18px; padding: 9px; text-align: center;'>"
            table1 +=  '<th style="border: 1px solid grey;"> Índice </th>'
            table1 +=  '<th style="border: 1px solid grey;"> Fatores </th>'
            table1 +=  '<th style="border: 1px solid grey;"> Valor </th>'
            table1 +=  '<th style="border: 1px solid grey;"> Influência </th>'
            table1 +=  '</tr>'
            table1 +=  '</thead>'

            for linha in range(len(globals.shap_columns)):
                data  = globals.shape_results[municipio]['data'][linha]
                value = globals.shape_results[municipio]['values'][linha]
                table1 +=  '<tr style="text-align: center;">'
                table1 += f'<td style="border: 1px solid grey;"> {linha + 1} </td>'
                table1 += f'<td style="border: 1px solid grey;"> {globals.shap_columns[linha]} </td>'
                table1 += f'<td style="border: 1px solid grey;"> {data:0.2f} </td>' if data != 0 else '<td style="border: 1px solid grey;"> 0 </td>'
                table1 += f'<td style="color: blue; border: 1px solid grey;">' if value > 0 else (f'<td style="color: red; border: 1px solid grey;">' if value < 0 else f'<td style="border: 1px solid grey;">')
                table1 += f'{value:0.3f}' if value != 0 else '0'
                table1 += '</td>'
                table1 += '</tr>'
            table1 +=  '<tr>'
            table1 +=  '<td colspan="4" style="font-size:15px; text-align:left;">'
            table1 += f"<span style=\"color:blue;\">&#x25A0;</span> : INFLUÊNCIA <span style=\"color:blue;\">POSITIVA</span> (AUMENTA A {dados['feature'].upper()}).<br>"
            table1 += f"<span style=\"color:red;\">&#x25A0;</span> : INFLUÊNCIA <span style=\"color:red;\">NEGATIVA</span> (DIMINUI A {dados['feature'].upper()})."
            table1 +=  '</td>'
            table1 +=  '</tr>'
            table1 +=  '</table>'
            table1 += f"<p class='legenda-tabela'> Tabela 1 - Impacto dos Fatores na Taxa de {dados['feature']} </p>"

            table2 = '<table style="margin-left: auto; margin-right: auto; margin-top: 60px; width: 627px; border: 2px solid grey;">'
            table2 += '<caption style="color: #8B4513; caption-side: top; border: 2px solid grey; text-align: center; font-weight: bold; font-size: 23px; padding: 10px 0;"> Fatores que Mais Influenciaram </caption>'
            table2 += '<thead>'
            table2 += "<tr style='font-size: 18px; padding: 9px; text-align: center;'>"
            table2 += '<th style="width:50%; border: 1px solid grey;" colspan="2"> Positivamente </th>'
            table2 += '<th style="width:50%; border: 1px solid grey;" colspan="2"> Negativamente </th>'
            table2 += '</tr>'
            table2 += '</thead>'

            numero_atributos = 3
            values = globals.shape_results[f'{municipio}']['values']
            maiores_valores = [v for v in sorted(values, reverse=True)[:numero_atributos] if v > 0]
            menores_valores = [v for v in sorted(values)[:numero_atributos] if v < 0]
            indices_maiores_valores = {}
            indices_menores_valores = {}
            for id, v in enumerate(values):
                if v in maiores_valores and id not in indices_maiores_valores:
                    indices_maiores_valores[id] = v
                elif v in menores_valores and id not in indices_menores_valores:
                    indices_menores_valores[id] = v
            indices_maiores_valores = dict(sorted(indices_maiores_valores.items(), key=lambda item: item[1]))
            indices_menores_valores = dict(sorted(indices_menores_valores.items(), key=lambda item: item[1], reverse=True))
            maiores_valores_copy, menores_valores_copy = indices_maiores_valores.copy(), indices_menores_valores.copy()
            for linha in range(numero_atributos):
                chave_maior, valor_maior = indices_maiores_valores.popitem() if indices_maiores_valores else (None, None)
                chave_menor, valor_menor = indices_menores_valores.popitem() if indices_menores_valores else (None, None)
                table2 += '<tr style="font-size: 17px; text-align: center;">'
                table2 += f'<td style="width:40%; border: 1px solid grey;"> {globals.shap_columns[chave_maior] if chave_maior is not None else "---"} </td>'
                table2 += f'<td style="color: blue; width:10%; border: 1px solid grey;">' + (f'{valor_maior:.3f}' if valor_maior is not None else "---") + '</td>'
                table2 += f'<td style="width:40%; border: 1px solid grey;"> {globals.shap_columns[chave_menor] if chave_menor is not None else "---"} </td>'
                table2 += f'<td style="color: red; width:10%; border: 1px solid grey;">' + (f'{valor_menor:.3f}' if valor_menor is not None else "---") + '</td>'
                table2 += '</tr>'
            table2 += '</table>'
            table2 += f'<p class="legenda-tabela"> Tabela 2 - Principais Fatores de Influência </p>'

            score_municipio = dados['scores'][dados['labels'].index(municipio)]
            table3 =   '<table style="margin-left: auto; margin-right: auto; margin-top: 60px; width: 627px; border: 2px solid grey;">'
            table3 += f"<caption style='color: #8B4513; caption-side: top; border: 2px solid grey; text-align: center; font-weight: bold; font-size: 23px; padding: 10px 0; '> {dados['feature']} </caption>"
            table3 += '<thead>'
            table3 +=  "<tr style='font-size: 18px; padding: 9px; text-align: center;'>"
            table3 += f"<th style='width:50%; border: 1px solid grey;'> Grupo {dados['cluster'] + 1}</th>"
            table3 +=  '<th style="width:50%; border: 1px solid grey;"> Município </th>'
            table3 +=  '</tr>'
            table3 += '</thead>'
            table3 +=  '<tr style="text-align: center; font-size: 17px;">'
            table3 += f"<td style='border: 1px solid grey;'> {dados['cluster_score']*100:0.2f} % </td>" if dados['cluster_score'] != 0 else '<td style="font-size: 17px; border: 1px solid grey;"> 0 % </td>'
            table3 += f'<td style="color: blue; border: 1px solid grey;">' if score_municipio > dados['cluster_score'] else (f'<td style="color: red; font-size: 17px; border: 1px solid grey;">' if score_municipio < dados['cluster_score'] else f'<td style="font-size: 17px; border: 1px solid grey;">')
            table3 += f'{score_municipio*100:0.2f} %' if score_municipio != 0 else '0 %'
            table3 += '</td>'
            table3 += '</tr>'
            table3 +=  '<tr>'
            table3 +=  '<td colspan="2" style="font-size:15px; text-align:left;">'
            table3 += f"<span style=\"color:blue;\">&#x25A0;</span> : VALOR <span style=\"color:blue;\">ACIMA</span> DA MÉDIA DO GRUPO.<br>"
            table3 += f"<span style=\"color:red;\">&#x25A0;</span> : VALOR <span style=\"color:red;\">ABAIXO</span> DA MÉDIA DO GRUPO."
            table3 +=  '</td>'
            table3 +=  '</tr>'
            table3 += '</table>'
            table3 += f"<p class='legenda-tabela'> Tabela 3 - Comparação do(a) {dados['feature']} entre o Município e o seu Grupo </p>"

            cell_labels = [label for label in dados['labels'] if label != municipio]
            cell_labels.sort()
            table4 =   '<table style="margin-left: auto; margin-right: auto; margin-top: 60px; width: 627px; border: 2px solid grey;">'
            table4 +=  '<caption style="color: #8B4513; caption-side: top; border: 2px solid grey; text-align: center; font-weight: bold; font-size: 23px; padding: 10px 0; "> Vizinhos Mais Próximos </caption>'
            table4 +=  '<thead>'
            table4 +=  "<tr style='font-size: 18px; padding: 9px; text-align: center;'>"
            table4 +=  '<th style="width:50%; border: 1px solid grey;"> Nome </th>'
            table4 += f"<th style='width:50%; border: 1px solid grey;'> {dados['feature']} </th>"
            table4 +=  '</tr>'
            table4 +=  '</thead>'

            if len(cell_labels) > 0:
                for linha in range(len(cell_labels)):
                    score_label = dados['scores'][dados['labels'].index(cell_labels[linha])]
                    table4 +=  '<tr style="text-align: center; font-size: 17px;">'
                    table4 += f'<td style="border: 1px solid grey;"> {cell_labels[linha]} </td>'
                    table4 +=  '<td style="border: 1px solid grey;">'
                    table4 += f'{score_label*100:0.2f} %' if score_label != 0 else '0 %'
                    table4 +=  '</td>'
                    table4 +=  '</tr>'
            else:
                table4 +=  '<tr style="text-align: center; font-size: 17px;">'
                table4 += f'<td style="border: 1px solid grey;"> --- </td>'
                table4 +=  '<td style="border: 1px solid grey;"> --- </td>'
                table4 +=  '</tr>'

            table4 +=   '<tr>'
            table4 +=   ' <td colspan="2" style="font-size:15px; text-align: center;"> OBS: A <i>PROXIMIDADE</i> ENVOLVE O <span style="color:#00FFFF;">CONJUNTO TOTAL</span> DOS FATORES E SUAS SEMELHANÇAS, AO INVÉS DE QUESTÕES GEOGRÁFICAS. </td>'
            table4 +=   '</tr>'
            table4 +=   '</table>'
            table4 += f'<p class="legenda-tabela"> Tabela 4 - Municípios Mais Semelhantes a {municipio} </p>'

            html = f"""{table1}
                       {table2}
                       {table3}
                       {table4}"""

            pdf_filename = os.path.join(save_path, f'{municipio}.pdf')
            df1, df2, df3, df4 = gerarDataFrames(municipio, maiores_valores_copy, menores_valores_copy, dados, score_municipio, cell_labels)

            # Ajusta algumas colunas do DF (arg2), definindo um número máximo de caracteres (arg3) em uma linha 
            df1 = ajustarDataFrames(df1, ['Fatores'], 38)
            df1 = ajustarDataFrames(df1, ['Valor'], 6)
            df2 = ajustarDataFrames(df2, ['Positivamente', 'Negativamente'], 24)

            # Constroi e gera o PDF
            page_w, page_h = letter
            c = canvas.Canvas(pdf_filename)
            c, h = gerarSecao(c,'t1',municipio,65)
            c, h = gerarSecao(c,'c',f"Resultado da Influência dos Fatores no(a) {dados['feature']}",h+30)
            c, h = gerarSecaoTabela(c,h,df1.to_numpy(), df1.columns.tolist(),1)
            c, h = gerarLegenda(c,f"Tabela 1 - Impacto dos Fatores na Taxa de {dados['feature']}", h+5)
            posicao, h_last = 61 + df1.shape[0] * 14, h # Calcula +/- a posição da tabela no pdf
            c, h = quebraPagina(c, posicao, h, 98) # Tenta evitar que a tabela 2 seja quebrada ao meio
            pagina_quebrada = True if h < h_last else False
            c, h = gerarSecao(c,'c',"Fatores que Mais Influenciaram",h+30)
            c, h = gerarSecaoTabela(c,h,df2.to_numpy(), df2.columns.tolist(),2)
            c, h = gerarLegenda(c,"Tabela 2 - Principais Fatores de Influência", h+5)
            posicao, h_last = (posicao + 14 + df2.shape[0] * 14, h) if not pagina_quebrada else (34 + df2.shape[0] * 14, h)
            c, h = quebraPagina(c, posicao, h, 165) # Tenta evitar que a tabela 3 seja quebrada ao meio
            pagina_quebrada = True if h < h_last else False
            c, h = gerarSecao(c,'c',f"{dados['feature']}",h+30)
            c, h = gerarSecaoTabela(c,h,df3.to_numpy(), df3.columns.tolist(),3)
            c, h = gerarLegenda(c,f"Tabela 3 - Comparação do(a) {dados['feature']} entre o Município e o seu Grupo", h+5)
            posicao, h_last = (posicao + 14 + df3.shape[0] * 14, h) if not pagina_quebrada else (34 + df3.shape[0] * 14, h)
            c, h = quebraPagina(c, posicao, h, 103) # Tenta evitar que a tabela 4 seja quebrada ao meio
            c, h = gerarSecao(c,'c',"Vizinhos Mais Próximos",h+30)
            c, h = gerarSecaoTabela(c,h,df4.to_numpy(), df4.columns.tolist(),4)
            c, h = gerarSecao(c,'c1',"OBS: A PROXIMIDADE ENVOLVE O CONJUNTO TOTAL DOS FATORES E SUAS SEMELHANÇAS, AO INVÉS DE QUESTÕES GEOGRÁFICAS.",h+8)
            c, h = gerarLegenda(c,f"Tabela 4 - Municípios Mais Semelhantes a {municipio}", h+5)
            h = h+30
            c.drawImage('cabecalho.jpeg', inch-8, page_h-50,page_w-inch-52,50)
            c.saveState()
            c.showPage()
            c.save()

            # Salvar o nome do pdf para depois adicionar no zip
            pdf_filenames.append(pdf_filename)

            # Ler o PDF
            with open(pdf_filename, "rb") as f:
                pdf_contents = f.read()

            # Baixar o PDF quando o botão é clicado
            b64 = base64.b64encode(pdf_contents).decode()
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            data_atual = datetime.now()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Relatório_Agrupamentos_{data_atual}_{municipio}.pdf"><button style="background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">Baixar Relatório</button></a>', unsafe_allow_html=True)

            # Exibir as tabelas na tela
            st.markdown(html, unsafe_allow_html=True)

    # Criar um arquivo zip
    zip_filename = os.path.join(save_path, 'Anexos.zip')
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        # Adicionar cada arquivo PDF ao arquivo zip
        for pdf_file in pdf_filenames:
            zipf.write(pdf_file)

    # Baixar o arquivo zip quando o botão é clicado
    with open(zip_filename, "rb") as f:
        zip_contents = f.read()
    b64 = base64.b64encode(zip_contents).decode()
    st.sidebar.divider()
    st.sidebar.title('Anexos', help="Clique no botão abaixo para baixar os relatórios de todos os municípios selecionados")
    st.sidebar.markdown(f'<a href="data:application/zip;base64,{b64}" download="Anexos.zip"><button style="background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">Baixar Relatórios Individuais</button></a>', unsafe_allow_html=True)

    # Remove os PDFs e o arquivo zip
    for pdf_file in pdf_filenames:
        os.remove(pdf_file)
    os.remove(zip_filename)

    # Remover a pasta
    os.rmdir(save_path)
