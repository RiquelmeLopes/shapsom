from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import streamlit as st
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

df = None

def relatorio_regioes():
    st.title("**Sistema de Apoio a Auditorias do Tribunal de Contas do Estado 📊**")

    secao7()
    st.subheader('Seção 7 - Identificação de Mesorregiões e Microrregiões')
    st.markdown('Essa seção traz uma tabela com todos os municípios de Pernambuco, identificando suas mesorregiões e microrregiões e dando um índice para elas, que é o índice utilizado nos Mapas de Calor.')
    with st.expander("Relatório", expanded=False):
        st.dataframe(df, use_container_width=True)
        
    st.info(f"**Tabela 7 - Municípios e Suas Mesorregiões e Microrregiões**")

# PDF
def gerarSecao(c,tipo,paragrafo,h):
    page_w, page_h = letter
    if(tipo=='p'):
        style_paragrafo = ParagraphStyle("paragrafo", fontName="Helvetica", fontSize=12, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='t'):
        style_paragrafo = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='s'):
        style_paragrafo = ParagraphStyle("subtitulo", fontName="Helvetica-Bold", fontSize=14, alignment=4, leading=18, encoding="utf-8")
    elif(tipo=='c'):
        style_paragrafo = ParagraphStyle("caption", fontName="Helvetica-Bold",backColor='#d3d3d3' , textColor='black', fontSize=18, alignment=TA_CENTER, leading=25, borderColor='gray', borderWidth=2, borderPadding=5, encoding="utf-8")
    message_paragrafo = Paragraph(paragrafo, style_paragrafo)
    w_paragrafo, h_paragrafo = message_paragrafo.wrap(page_w -2*inch, page_h)
    message_paragrafo.drawOn(c, inch, page_h - h- h_paragrafo)
    return (c, h+h_paragrafo+30) if tipo != 'c' else (c, h+h_paragrafo+12)

def gerarLegenda(c,paragrafo,h):
    page_w, page_h = letter
    style_paragrafo = ParagraphStyle("paragrafo", fontName="Helvetica-Oblique", fontSize=10, alignment=4, leading=18, encoding="utf-8", textColor = 'blue')
    message_paragrafo = Paragraph(paragrafo, style_paragrafo)
    w_paragrafo, h_paragrafo = message_paragrafo.wrap(page_w -2*inch, page_h)
    message_paragrafo.drawOn(c, inch, page_h - h- h_paragrafo)
    return c, h+h_paragrafo+20

def gerarTabela(data):
    data = [['Índice','Nome Município','Mesorregião', 'Microrregião']]+data

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'WORD'),
    ])

    col_widths = [40,140,140,150]

    table = Table(data, colWidths=col_widths)
    table.setStyle(style)
    return table

def gerarTabelaPdf(c,data,h,start):
    page_w, page_h = letter
    if(len(data)>start):
        data2 = []
        end = 0
        for i in range(len(data)-start+1):
            table = gerarTabela(data2)
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

def quebraPagina(c, h, tamanho):
    page_w, page_h = letter
    if(h>tamanho):
        c.drawImage('cabecalho.jpeg', inch-8, page_h-50,page_w-inch-52,50)
        c.saveState()
        c.showPage()
        h=65
    return c, h

def gerarSecaoTabela(c,h,dados):
    start = 0
    start2 = 0
    while(True):
        c, h, start = gerarTabelaPdf(c,dados,h,start)
        if(start==start2):
            break
        else:
            c, h = quebraPagina(c, h, 0)
            start2=start
    return c, h

def secao7():
    # Constroi o DataFrame
    global df
    df = pd.read_csv('Regiões-PE.csv')
    df = df.drop(['IBGE', 'Segmento Fiscalizador', 'GRE', 'geom'], axis=1)
    df.index = range(1, len(df) + 1)
    df.insert(0, 'Índice', df.index)

    # Constroi e gera o PDF
    page_w, page_h = letter
    texto1 = 'Essa seção traz uma tabela com todos os municípios de Pernambuco, identificando suas mesorregiões e microrregiões e dando um índice para elas, que é o índice utilizado nos Mapas de Calor.'
    c = canvas.Canvas('secao7.pdf')
    c, h = gerarSecao(c,'t','Seção 7 - Identificação de Meso e Microrregiões',65)
    c, h = gerarSecao(c,'p',texto1,h)
    c, h = gerarSecaoTabela(c,h,df.to_numpy())
    c, h = gerarLegenda(c,'Tabela 7 - Municípios e Suas Mesorregiões e Microrregiões', h+5)
    h = h+30
    c.drawImage('cabecalho.jpeg', inch-8, page_h-50,page_w-inch-52,50)
    c.saveState()
    c.showPage()
    c.save()

    # Remove coluna de índice do DataFrame
    df = df.drop(['Índice'], axis=1)