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

    # Criar um gráfico de barras interativo usando Plotly-
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
    
    st.markdown('**Carros por estado americano**')
    st.map(df_grouped, size="quant", color='#0044ff')


def exibir_grafico_vendas_projetadas(df):
    # obter valores exclusivos para preço de venda sugerido
    df_sugg_price = df_electric_car[['Model', 'Base MSRP']].drop_duplicates()

    # preencher com a mediana dos valores
    # Substituir valores 0 por NaN para calcular a mediana corretamente
    df_sugg_price['Base MSRP'].replace(0.0, np.nan, inplace=True)

    # Calcular a mediana dos valores não nulos
    median_price = df_sugg_price['Base MSRP'].median()

    # Preencher os valores NaN com a mediana
    df_sugg_price['Base MSRP'] = df_sugg_price['Base MSRP'].fillna(median_price)

    df_ = pd.merge(df, df_sugg_price, on='Model', how='left', suffixes=('', '_y'))
    df_ = df_.dropna()
    df_ = df_.loc[:,~df_.columns.duplicated()]
    df_ = df_.drop(columns=['Base MSRP'])
    df_ = df_.rename(columns={'Base MSRP_y': 'Base MSRP'})

    # Agrupar e calcular as vendas por ano
    tesla_car_sells_by_year = df_.groupby('Model Year')['Base MSRP'].sum()
    
    tesla_car_sells_by_year_millions = tesla_car_sells_by_year / 1e6

    escopo_ampliado = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
   
    # Filtrar os anos no DataFrame com base no escopo ampliado
    tesla_car_sells_by_year_millions = tesla_car_sells_by_year_millions.reindex(escopo_ampliado, fill_value=0)

    # Gerar o gráfico usando Plotly Express
    fig = px.bar(
        tesla_car_sells_by_year_millions,
        x=tesla_car_sells_by_year_millions.index,
        y=tesla_car_sells_by_year_millions.values,
        labels={'x': 'Ano', 'y': 'Vendas (em milhões)'},
        title='Vendas Projetadas por Ano (em milhões de dólares)',
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)

    return df_


def vendas_projetadas_por_modelo(df_):
    tesla_car_sells_by_year = df_.groupby('Model')['Base MSRP'].sum()
    print(df_.columns)
    tesla_car_sells_by_year_millions = tesla_car_sells_by_year / 1e6

    carros = df_['Model'].drop_duplicates().to_list()
   
    # Filtrar os anos no DataFrame com base no escopo ampliado
    tesla_car_sells_by_year_millions = tesla_car_sells_by_year_millions.reindex(carros, fill_value=0)

    # Gerar o gráfico usando Plotly Express
    fig = px.bar(
        tesla_car_sells_by_year_millions,
        x=tesla_car_sells_by_year_millions.index,
        y=tesla_car_sells_by_year_millions.values,
        labels={'x': 'Ano', 'y': 'Vendas (em milhões)'},
        title='Vendas Projetadas por Ano, por modelo de carro (em milhões de dólares)',
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)


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
        xaxis=dict(
            title='Ano',
            tickmode='linear',
            dtick=1
            ),
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


# chamando as funções
Home()
exibir_grafico_carros_ano_a_ano(df_selection)
st.markdown('---')
exibir_grafico_carros_por_regiao(df_selection)
st.markdown('---')
df = exibir_grafico_vendas_projetadas(df_selection)
st.markdown('---')
vendas_projetadas_por_modelo(df)

if "TESLA" in company and len(company) == 1:    
    exibir_grafico_acoes_e_carros(df_stocks_and_cars)

else:
    st.write(
        "Infelizmente só possuímos dados de ações da Tesla. Para exibir esses dados, selecione apenas a emprea 'Tesla' no filtro"
        )