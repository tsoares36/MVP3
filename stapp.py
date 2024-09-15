import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
from config import *
import os


st.set_page_config(
    page_title='MVP3 - Data Science & Analytics', 
    page_icon=f'{imgdir}ideia.png', 
    layout='wide'
    )

st.subheader('Carros elétricos produzidos nos EUA')
st.markdown('---')

########################################################################################
############################ bases de dados ############################################

df0 = pd.read_csv(f'{bases}Electric_Vehicle_Population_Data_0.csv', sep=",")
df1 = pd.read_csv(f'{bases}Electric_Vehicle_Population_Data_1.csv', sep=",")
df2 = pd.read_csv(f'{bases}Electric_Vehicle_Population_Data_2.csv', sep=",")
df3 = pd.read_csv(f'{bases}Electric_Vehicle_Population_Data_3.csv', sep=",")

df1.columns = df0.columns
df2.columns = df0.columns
df3.columns = df0.columns

df_electric_car = pd.concat([df0, df1, df2, df3], axis=0, ignore_index=True)

# df_electric_car = pd.read_csv(f'{bases}Electric_Vehicle_Population_Data.csv', sep=',')
df_stocks = pd.read_csv(f'{bases}tesla_stock_data.csv')

df_electric_car = df_electric_car.drop(
    ['Postal Code', 'Clean Alternative Fuel Vehicle (CAFV) Eligibility', 'Legislative District', 'DOL Vehicle ID', 'Electric Utility', '2020 Census Tract'], axis = 1)

# remover parênteses
df_electric_car['Vehicle Location'] = df_electric_car['Vehicle Location'].str.replace(r'[()]', '', regex=True)

# separar colunas - latitude/longitude
df_electric_car[['point', 'Latitude', 'Longitude']] = df_electric_car["Vehicle Location"].str.split(" ", expand = True)

# remover texto antes do número
df_electric_car.drop(columns=['Vehicle Location', 'point'], inplace=True)

# converter latitude/longitude para número do tipo float
df_electric_car[['Latitude', 'Longitude']] = df_electric_car[['Latitude', 'Longitude']].astype(float)
########################################################################################

st.sidebar.image(f'{imgdir}tesla.png', caption='MVP3 | Thiago Soares do Nascimento')

st.sidebar.header('Filtros disponíveis')
euastates = st.sidebar.multiselect(
    'Selecione um estado americano',
    options=df_electric_car['State'].unique(),
    default=df_electric_car['State'].unique()
)

company = st.sidebar.multiselect(
    'Selecione uma empresa (padrão Tesla)',
    options=df_electric_car['Make'].unique(),
    default='TESLA'
)

df_electric_car_filtered = df_electric_car[df_electric_car['Make'].isin(company)]

carmodel = st.sidebar.multiselect(
    'Selecione um modelo de carro',
    options=df_electric_car_filtered['Model'].unique(),
    default=df_electric_car_filtered['Model'].unique()
)

df_selection=df_electric_car.query(
    "State==@euastates & Make==@company & Model==@carmodel"
)

anos_analisados = [2020, 2021, 2022, 2023]
tesla_cars_by_year = df_selection.groupby('Model Year')['VIN (1-10)'].count()
df_selection_reduzido = tesla_cars_by_year[tesla_cars_by_year.index.isin(anos_analisados)].reset_index()

df_selection_reduzido.columns = ['Year', 'Quantity']

stocks_by_year = df_stocks.groupby('Year')['Adj Close'].mean().reset_index()
stocks_by_year.columns = ['Year', 'Price']

df_stocks_and_cars = pd.merge(df_selection_reduzido, stocks_by_year, how='inner', on='Year')

def Home():
    with st.expander("Dataframe 'Electric Cars'"):
        showData = st.multiselect('Filtre: ', df_selection.columns, default=[])
        st.write(df_selection[showData])
    
    qtdcarros = int(df_selection['Model'].count())
    percarros = round(qtdcarros/float(df_electric_car['Model'].count()), 2) * 100


    mostfrequent = df_selection["Model"].mode().iloc[0]
    
    # print(df_electric_car[df_electric_car['Model'] == mostfrequent])
    percarromais = round(float(df_electric_car['Model'][df_electric_car['Model'] == mostfrequent].count()) / qtdcarros, 2) * 100
    
    val, val1 = st.columns(2, gap='large')

    with val:
        st.info('Métricas carros fabricados')
        st.metric(label='Contagem', value=f'{qtdcarros}')
        st.metric(label='% do total geral', value=f'{percarros}')

    with val1:
        st.info("Métricas carro mais fabricado")
        st.metric(label='mais fabricado', value=f'{mostfrequent}')
        st.metric(label='% do total de carros no filtro', value=f'{percarromais}')

    st.markdown('---')


def exibir_grafico_carros_ano_a_ano(df):
    # Agrupar os dados por ano do modelo e contar a quantidade de carros fabricados por ano
    escopo_ampliado = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    df_ano = df.groupby('Model Year').size().reset_index(name='Quantidade')

    # Ordenar os dados pelo ano para melhor visualização
    df_ano = df_ano.sort_values('Model Year')
    df_ano = df_ano[df_ano['Model Year'].isin(escopo_ampliado)]

    # Criar um gráfico de barras interativo usando Plotly
    fig = px.bar(
        df_ano,
        x='Model Year',
        y='Quantidade',
        title='Quantidade de carros elétricos fabricados entre 2015 e 2024',
        labels={'Model Year': 'Ano do Modelo', 'Quantidade': 'Quantidade de Carros'},
        template='plotly_white'
    )

    # Configurações opcionais para melhorar a aparência do gráfico
    fig.update_layout(
        xaxis_title='Ano do Modelo',
        yaxis_title='Quantidade de Carros',
        xaxis=dict(tickmode='linear')  # Para mostrar todos os anos
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)
    

def exibir_grafico_carros_por_regiao(df):
    # Remover entradas com valores de localização ausentes
            
    df = df.dropna(subset=['Latitude', 'Longitude'])

    df_coordinates = pd.DataFrame(us_states_coordinates)

    # Mesclando os DataFrames com base na coluna 'State'
    df_merged = pd.merge(df, df_coordinates, on='State', suffixes=('', '_new'))


    # Substituindo os valores de Latitude e Longitude
    df_merged['Latitude'] = df_merged['Latitude_new']
    df_merged['Longitude'] = df_merged['Longitude_new']

    # Removendo as colunas extras usadas para substituição
    df_merged = df_merged.drop(columns=['Latitude_new', 'Longitude_new'])

    df_merged['Latitude'] = df_merged['Latitude'].astype(float).round(2)
    df_merged['Longitude'] = df_merged['Longitude']

    df_merged = df_merged[['Latitude', 'Longitude']]
    df_merged = df_merged.rename(columns={"Latitude": "lat", "Longitude":"lon"})

    df_grouped = df_merged.groupby(["lat", "lon"]).size().reset_index(name='quant')    
    #df_grouped.drop(columns='quant', inplace=True)

    st.write("Carros por estado americano")
    st.map(df_grouped, size="quant", color='#0044ff')


def exibir_grafico_acoes_e_carros(df):
    fig = go.Figure()

    # Adicionando a linha para a quantidade de carros (eixo da esquerda)
    fig.add_trace(
        go.Bar(
            x=df['Year'],
            y=df['Quantity'],
            name='Quantidade de Carros Produzidos',
            marker_color='blue',
            yaxis='y1'
        )
    )

    # Adicionando a linha para o preço das ações (eixo da direita)
    fig.add_trace(
        go.Scatter(
            x=df['Year'],
            y=df['Price'],
            name='Preço das Ações',
            mode='lines+markers',
            line=dict(color='red'),
            yaxis='y2'
        )
    )

    # Ajustando o layout para dois eixos y
    fig.update_layout(
        title='Produção de Carros e Preço das Ações da Tesla',
        xaxis=dict(title='Ano'),
        yaxis=dict(
            title='Quantidade de Carros Produzidos',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue'),
            side='left'
        ),
        yaxis2=dict(
            title='Preço das Ações',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.1, y=1.1)
    )

    st.plotly_chart(fig)


# chamando funções
Home()
exibir_grafico_carros_ano_a_ano(df_selection)
st.markdown('---')
exibir_grafico_carros_por_regiao(df_selection)
st.markdown('---')

st.write("Quantidade de carros produzidos x Preço das ações da Tesla entre 2020 e 2023")
if "TESLA" in company and len(company) == 1:
    exibir_grafico_acoes_e_carros(df_stocks_and_cars)

else:
    st.write(
        "Infelizmente só possuímos dados de ações da Tesla. Para exibir esses dados, selecione apenas a emprea 'Tesla' no filtro"
        )