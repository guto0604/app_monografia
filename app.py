import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium, folium_static
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns

# Leitura dos Dados
df_orig = (pl.scan_parquet('data/colisoes.parquet')
    .filter(
    pl.col('id_colisao').is_not_null()
    )
    .select(['id_colisao','dt_colisao','intensidade','velocidade','local_colisao','cidade_colisao','estado_colisao','desc_modelo_y','cd_segmento_final','latitude','longitude'])
    ).collect().to_pandas()

# Ajuste Nomes de Colunas
df_orig = df_orig.rename(columns= {
    'dt_colisao': 'Data_Colisao',
    'intensidade': 'Intensidade',
    'velocidade':'Velocidade_KM/H',
    'local_colisao': 'Local_Colisao_Veiculo',
    'cidade_colisao':'Cidade_Colisao',
    'estado_colisao':'Estado_Colisao',
    'desc_modelo_y':'Modelo',
    'cd_segmento_final' : 'Segmento'
    })


# Ajuste em Colunas

df_orig['Segmento'] = df_orig['Segmento'].map(
    {'RS':'Motorista Aplicativo',
     'PFAD':'Aluguel Tradicional',
     'PFAM': 'Aluguel Tradicional',
     'COAM':'Carro Corporativo',
     'COAD':'Carro Corporativo',
     'TRAM' : 'Carro Corporativo',
     'TRAD': 'Carro Corporativo',
     'GF':'Carro Corporativo',
     'OTA':'Outros',
     'RE': 'Outros'}
)

df_orig['lat_lon'] = df_orig[['latitude', 'longitude']].values.tolist()
df_orig['Data_Colisao'] = df_orig['Data_Colisao'].dt.date
df_orig['Modelo_Resumido'] = [i[0] for i in df_orig['Modelo'].str.split(' \d.\d') ]


# Função Exibição do Mapa
def Show_Map(df, estilo, lat_col='latitude', lon_col='longitude'):
    lats_longs = df[[lat_col, lon_col]].values.tolist()
    m = folium.Map(location=[-22, -45], zoom_start=6, tiles="Cartodb dark_matter")
    
    if estilo == 'Mapa de Calor':
        HeatMap(lats_longs).add_to(m)
    else:
        marker_cluster = MarkerCluster().add_to(m)
        for point in lats_longs:
            folium.Marker(location=point).add_to(marker_cluster)
    
    return m

# Função do Download dos Dados
@st.cache_data
def convert_df(df):
   return df.to_csv().encode('utf-8')


st.title("Colisões Carros Alugados 2023")

# Filtros
st.sidebar.header("Filtros")
# Filtro de Estilo do mapa
estilo = st.sidebar.radio(
    'Selecione o Estilo do Mapa',
    ['Mapa de Calor', 'Pontos']
)
# Filtro de Data
min_date = df_orig['Data_Colisao'].min()
max_date = df_orig['Data_Colisao'].max()
date_range = st.sidebar.slider(
    'Selecione o Intervalo de Datas',
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)
# Filtro de Segmento
opcoes_segmento = ['Todos']
opcoes_segmento.extend( df_orig['Segmento'].value_counts().index.to_list()[:20] )
Segmento_filter = st.sidebar.multiselect(
    'Selecione o segmento do motorista',
    options=opcoes_segmento,
    default= 'Todos'
)
# Filtro de Estado
opcoes_Estado_Colisao = ['Todos']
opcoes_Estado_Colisao.extend( df_orig['Estado_Colisao'].value_counts().index.to_list()[:20] )
Estado_Colisao_filter = st.sidebar.multiselect(
    'Selecione o Estado da Colisão',
    options=opcoes_Estado_Colisao,
    default= 'Todos'
)
# Filtro de Cidade
opcoes_Cidade_Colisao = ['Todos']
opcoes_Cidade_Colisao.extend( df_orig['Cidade_Colisao'].value_counts().index.to_list()[:20] )
Cidade_Colisao_filter = st.sidebar.multiselect(
    'Selecione a Cidade da Colisão',
    options=opcoes_Cidade_Colisao,
    default= 'Todos'
)
# Filtro de Intensidade
opcoes_intensidade = ['Todos']
opcoes_intensidade.extend( df_orig['Intensidade'].value_counts().index.to_list() )
intensidade_filter = st.sidebar.multiselect(
    'Selecione a Intensidade',
    options=opcoes_intensidade,
    default= 'Todos'
)
# Filtro de tipo
opcoes_local = ['Todos']
opcoes_local.extend( df_orig['Local_Colisao_Veiculo'].value_counts().index.to_list() )
local_filter = st.sidebar.multiselect(
    'Selecione o Local da colisão',
    options= opcoes_local,
    default= 'Todos'
)

# Filtrar o DataFrame
df_exibicao = df_orig.copy()

df_exibicao = df_exibicao[ (df_exibicao['Data_Colisao'] > date_range[0]) & (df_exibicao['Data_Colisao'] < date_range[1]) ]

if 'Todos' not in Segmento_filter:
    df_exibicao = df_exibicao[ df_exibicao['Segmento'].isin(Segmento_filter) ] 

if 'Todos' not in Estado_Colisao_filter:
    df_exibicao = df_exibicao[ df_exibicao['Estado_Colisao'].isin(Estado_Colisao_filter) ] 

if 'Todos' not in Cidade_Colisao_filter:
    df_exibicao = df_exibicao[ df_exibicao['Cidade_Colisao'].isin(Cidade_Colisao_filter) ] 

if 'Todos' not in intensidade_filter:
    df_exibicao = df_exibicao[ df_exibicao['Intensidade'].isin(intensidade_filter) ]

if 'Todos' not in local_filter:
    df_exibicao = df_exibicao[ df_exibicao['Local_Colisao_Veiculo'].isin(local_filter) ]


## Mostrar o mapa
m = Show_Map(df_exibicao, estilo)
folium_static(m, width=700)


## Exibe e Baixa os Dados Filtrados
df_out = df_exibicao[['Data_Colisao','Velocidade_KM/H','Intensidade','Local_Colisao_Veiculo','Estado_Colisao','Cidade_Colisao','Modelo','Segmento','latitude','longitude']].reset_index(drop = True)

csv = convert_df(df_out)
st.download_button(
   "Baixar Dados",
   csv,
   "Colisoes.csv",
   "text/csv",
   key='download-csv'
)

st.dataframe(df_out)

if df_out.shape[0] > 0:
    fig, ax = plt.subplots()
    
    fig.patch.set_facecolor('#2E2E2E')
    ax.set_facecolor('#2E2E2E')
    
    sns.histplot(data = df_out, x = 'Velocidade_KM/H', binwidth= 5, color='snow')
    ax.set_title('Histograma da Velocidade das Colisões', color='white')
    ax.set_ylabel('Frequência Absoluta', color='white')
    ax.set_xlabel('Velocidade KM/H', color='white')
    ls_ticks = range(0,  int( df_out['Velocidade_KM/H'].max() ) + 10  ,10)
    ax.set_xticks( ticks = ls_ticks )
    ax.set_xticklabels(ls_ticks, fontsize=9, rotation = 45, color='white')
    ax.tick_params(axis='y', colors='white')
    
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    
    
    st.pyplot(fig)
