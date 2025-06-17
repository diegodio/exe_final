import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import folium
from streamlit_folium import st_folium

@st.cache_data
def carregar_dados():
    df_2021 = pd.read_csv('https://raw.githubusercontent.com/diegodio/exe_final/refs/heads/main/2021a.csv', encoding='utf-8', sep=',')
    df_2022 = pd.read_csv('https://raw.githubusercontent.com/diegodio/exe_final/refs/heads/main/2022.csv', encoding='utf-8', sep=',')
    df_2023 = pd.read_csv('https://raw.githubusercontent.com/diegodio/exe_final/refs/heads/main/2023a.csv', encoding='utf-8', sep=',')
    df_2024 = pd.read_csv('https://raw.githubusercontent.com/diegodio/exe_final/refs/heads/main/2024.csv', encoding='utf-8', sep=',')

    df = pd.concat([df_2021, df_2022, df_2023, df_2024], ignore_index=True)

    for _, row in df[df['classificacao_acidente'].isna()].iterrows(): #iterrows retorna uma tupla com um int e uma serie
    # print(type(_))
    # print(type(row))
        df.loc[df['id'] == row['id'], 'classificacao_acidente'] = df[ #localiza a classificacao do acidente faltante pelo id
            (df['tipo_acidente'] == row['tipo_acidente']) & #entre as linhas com mesmo tipo de acidente
            (df['causa_acidente'] == row['causa_acidente']) #e mesma causa do acidente
        ]['classificacao_acidente'].value_counts().idxmax() #pega a moda e preenche o valor que tava faltando
    
    for _, row in df[df['regional'].isna()].iterrows(): #iterrows retorna uma tupla com um int e uma serie
        # print(type(_))
        # print(type(row))
        df.loc[df['id'] == row['id'], 'regional'] = 'SPRF-' + row['uf'] #SRPF + o estado
        # print('achou')

    for _, row in df[df['delegacia'].isna()].iterrows(): #iterrows retorna uma tupla com um int e uma serie

        df_uf = df[(df['uf'] == row['uf']) & (df['delegacia'].notna())].copy() #pega todos com mesmo UF, exceto os que não tiverem delegacia
        latitude = float(row['latitude'].replace(',', '.'))
        longitude = float(row['longitude'].replace(',', '.'))

        df_uf['latitude'] = df_uf['latitude'].str.replace(',', '.', regex=False).astype(float)
        df_uf['longitude'] = df_uf['longitude'].str.replace(',', '.', regex=False).astype(float)
    
        df_uf['distancia'] = ((df_uf['latitude']-latitude)**2 + (df_uf['longitude']-longitude)**2)**(1/2)
        
        df.loc[df['id'] == row['id'], 'delegacia'] = df_uf.loc[df_uf['distancia'].idxmin(), 'delegacia']
        # print('achou')

    for _, row in df[df['uop'].isna()].iterrows(): #iterrows retorna uma tupla com um int e uma serie

        df_uf = df[(df['uf'] == row['uf']) & (df['uop'].notna())].copy() #pega todos com mesmo UF, exceto os que não tiverem uop
        latitude = float(row['latitude'].replace(',', '.'))
        longitude = float(row['longitude'].replace(',', '.'))

        df_uf['latitude'] = df_uf['latitude'].str.replace(',', '.', regex=False).astype(float)
        df_uf['longitude'] = df_uf['longitude'].str.replace(',', '.', regex=False).astype(float)
    
        df_uf['distancia'] = ((df_uf['latitude']-latitude)**2 + (df_uf['longitude']-longitude)**2)**(1/2)
        
        df.loc[df['id'] == row['id'], 'uop'] = df_uf.loc[df_uf['distancia'].idxmin(), 'uop']
        # print('achou')

    df['data_inversa'] = pd.to_datetime(df['data_inversa'], dayfirst=False, errors='coerce')

    df['horario'] = pd.to_datetime(df['horario'], format='%H:%M:%S', errors='coerce').dt.time

    df['hora'] = pd.to_datetime(df['horario'], format='%H:%M:%S', errors='coerce').dt.hour

    df['total_vitimas']	= df['mortos'] + df['feridos']

    df['ano'] = df['data_inversa'].dt.year
    df['mes'] = df['data_inversa'].dt.month
    df['dia_do_mes'] = df['data_inversa'].dt.day

    if len(df.loc[df['veiculos'] == 0]) == 0:
        df['feridos_por_veiculo'] = df['feridos'] / df['veiculos']


    return df



st.sidebar.title("Acidentes em BRs")

opcao = st.sidebar.selectbox(
    'Escolha uma opção:',
    ['Qual o período do dia com mais acidentes?', 'Qual a hora com mais acidentes?', 'Qual o dia com mais acidentes?', 'Mortes por Condição Meteorológicas', 'Top 5 Causas de Acidente', 'Top 5 Tipos de Acidente', 'Mapa']
    )

df = carregar_dados()

if opcao == 'Qual o período do dia com mais acidentes?':

    col1, col2 = st.columns(2)

    with col1:
        ano_escolhido = st.multiselect(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        default=[2021],
        )

    with col2:
        estado_escolhido = st.multiselect(
        'Escolha um ano:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        default=['PR'],
        key='estado'
        )


    if len(ano_escolhido) > 0 and len(estado_escolhido) > 0:
        contagem = df[(df['ano'].isin(ano_escolhido)) & (df['uf'].isin(estado_escolhido))]['fase_dia'].value_counts(normalize=True).sort_index() * 100

        fig, ax = plt.subplots(figsize=(8,5))
        bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

        valor_max = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
        ax.set_ylim(0, valor_max)

        ticks = np.arange(0, valor_max+1, 10)
        ax.set_yticks(ticks)

        ax.bar_label(bars, fmt='%.1f%%', padding=3)

        ax.set_title(f'Porcentagem de Acidentes por Período do Dia no ano {sorted(ano_escolhido)} em {estado_escolhido}')
        ax.set_xlabel('Período do Dia')
        ax.set_ylabel('Quantidade de Acidentes (%)')

        st.pyplot(fig)

    st.divider()

    


elif opcao == 'Qual a hora com mais acidentes?':

    col1, col2 = st.columns(2)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_escolhido = st.selectbox(
        'Escolha um estado:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado2'
        )


    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin([estado_escolhido]))]['hora'].value_counts(normalize=True).sort_index() * 100

    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

    valor_max_y = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
    ax.set_ylim(0, valor_max_y)

    yticks = np.arange(0, valor_max_y+1, 10)
    ax.set_yticks(yticks)

    valor_max_x = df['hora'].max()
    xticks = np.arange(0, valor_max_x+1, 1)
    ax.set_xticks(xticks)



    labels = ax.bar_label(bars, fmt='%.1f%%', padding=3)
    for label in labels:
        label.set_fontsize(8)


    ax.set_title(f'Porcentagem de Acidentes por Hora do Dia em {ano_escolhido} em {estado_escolhido}')
    ax.set_xlabel('Hora do Dia')
    ax.set_ylabel('Quantidade de Acidentes (%)')

    st.pyplot(fig)



elif opcao == 'Qual o dia com mais acidentes?':
    st.write(opcao)

    col1, col2, col3 = st.columns(3)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_escolhido = st.selectbox(
        'Escolha um estado:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado'
        )

    with col3:
        mes_escolhido = st.selectbox(
        'Escolha um mês:',
        ['Todos', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        key='mes'
        )

    ordem_dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo',]

    mes_escolhido_lista = []
    if mes_escolhido == 'Todos':
        mes_escolhido_lista = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    else:
        mes_escolhido_lista.append(mes_escolhido)

    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin([estado_escolhido])) & (df['mes'].isin(mes_escolhido_lista))]['dia_semana'].value_counts(normalize=True) * 100
    # Filtrar e contar os dadoss
    # contagem = df[df['mes'].isin([1,2,3,4,5,6,7,8,9,10,11,12])]

    # Converter o índice para Categorical com ordem desejada
    contagem.index = pd.Categorical(contagem.index, categories=ordem_dias, ordered=True)

    # Ordenar pela ordem que você definiu
    contagem = contagem.sort_index()

    ##################################################################################################################

    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

    valor_max_y = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
    ax.set_ylim(0, valor_max_y)

    yticks = np.arange(0, valor_max_y+1, 10)
    ax.set_yticks(yticks)

    valor_max_x = len(df['dia_semana'].unique())
    xticks = np.arange(0, valor_max_x+1, 1)
    ax.set_xticks(xticks)



    labels = ax.bar_label(bars, fmt='%.1f%%', padding=3)
    for label in labels:
        label.set_fontsize(8)


    ax.set_title(f'Porcentagem de Acidentes por Dia em {ano_escolhido} em {estado_escolhido}')
    ax.set_xlabel('Dia da Semana')
    ax.set_ylabel('Quantidade de Acidentes (%)')

    st.pyplot(fig)

elif opcao == 'Mortes por Condição Meteorológicas':
    st.write(opcao)

    col1, col2 = st.columns(2)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_escolhido = st.selectbox(
        'Escolha um estado:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado'
        )

    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin([estado_escolhido]))]
    contagem = (contagem.groupby('condicao_metereologica')['mortos'].sum()*100)/contagem['mortos'].sum()
    # contagem.sort_values(ascending=True)


    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

    valor_max = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
    ax.set_ylim(0, valor_max)

    ticks = np.arange(0, valor_max+1, 10)
    ax.set_yticks(ticks)

    ax.bar_label(bars, fmt='%.1f%%', padding=3)

    ax.set_title(f'Porcentagem de Mortes por Condição Metereológica em {ano_escolhido} em {estado_escolhido}')
    ax.set_xlabel('Condição Metereológica')
    ax.set_ylabel('Quantidade de Mortes (%)')

    ax.set_xticklabels(contagem.index, rotation=45)

    st.pyplot(fig)

elif opcao == 'Top 5 Causas de Acidente':
    st.write(opcao)

    col1, col2 = st.columns(2)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_escolhido = st.selectbox(
        'Escolha um estado:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado'
        )


    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin([estado_escolhido]))]
    contagem = contagem['causa_acidente'].value_counts(normalize=True).sort_index() * 100
    contagem = contagem.sort_values(ascending=False)[:5]
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

    valor_max = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
    ax.set_ylim(0, valor_max)

    ticks = np.arange(0, valor_max+1, 10)
    ax.set_yticks(ticks)

    ax.bar_label(bars, fmt='%.1f%%', padding=3)

    ax.set_title('Top 5 Causas de Acidente')
    ax.set_xlabel('Causa')
    ax.set_ylabel('Quantidade de Acidentes (%)')

    ax.set_xticklabels(contagem.index, rotation=90)


    st.pyplot(fig)

elif opcao == 'Top 5 Tipos de Acidente':
    st.write(opcao)

    col1, col2 = st.columns(2)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_escolhido = st.selectbox(
        'Escolha um estado:',
        ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado'
        )

    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin([estado_escolhido]))]
    contagem = contagem['tipo_acidente'].value_counts(normalize=True).sort_index() * 100
    contagem = contagem.sort_values(ascending=False)[:5]
    fig, ax = plt.subplots(figsize=(8,5))
    bars = ax.bar(contagem.index, contagem.values, color='royalblue') #/contagem.sum() para %

    valor_max = np.ceil(contagem.max()*1.1/5)*5 #arrendonda para cima para o próximo múltiplo de 5. O 1.1 é pra dar um respiro no gráfico.
    ax.set_ylim(0, valor_max)

    ticks = np.arange(0, valor_max+1, 10)
    ax.set_yticks(ticks)

    ax.bar_label(bars, fmt='%.1f%%', padding=3)

    ax.set_title('Top 5 Tipos de Acidente')
    ax.set_xlabel('Tipo de Acidente')
    ax.set_ylabel('Quantidade de Acidentes (%)')

    ax.set_xticklabels(contagem.index, rotation=90)


    st.pyplot(fig)

elif opcao == 'Mapa':
    st.write(opcao)

    col1, col2, col3  = st.columns(3)

    with col1:
        ano_escolhido = st.selectbox(
        'Escolha um ano:',
        [2021, 2022, 2023, 2024],
        )

    with col2:
        estado_regiao = st.selectbox(
        'Escolha um estado/região:',
        ['Brasil', 'Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'],
        key='estado'
        )

    with col3:
        num_porcentagem_str = st.selectbox(
        '% de acidentes no mapa:',
        ['10%', '25%', '50%', '75%', '100%'],
        key='num_porcentagem'
        )

    regioes_estados = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC'],
    'Brasil': [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    }

    st.write('LEGENDA:')
    st.write('🟢 - Sem Vítimas')
    st.write('🟡 - Com Vítimas Feridas')
    st.write('🔴 - Com Vítimas Fatais')

    estado_escolhido = []
    if len(estado_regiao) == 2:
        estado_escolhido.append(estado_regiao)
    else:
        estado_escolhido = regioes_estados[estado_regiao].copy()

    num_porcentagem_float = {'10%': 0.1, '25%': 0.25, '50%': 0.5, '75%': 0.75, '100%': 1.0}    
    contagem = df[(df['ano'].isin([ano_escolhido])) & (df['uf'].isin(estado_escolhido))]
    # st.write(len(contagem))
    contagem = contagem.sample(frac=num_porcentagem_float[num_porcentagem_str], random_state=42)
    # st.write(len(contagem))


    locais = {'Brasil': (-14.2350, -51.9253), 'Norte': (-3.4168, -65.8561), 'Nordeste': (-9.6620, -40.8200), 'Centro-Oeste': (-15.6000, -56.1000), 'Sudeste': (-20.3770, -43.4160), 'Sul': (-27.5000, -50.0000), 'AC': (-9.0238, -70.8120), 'AL': (-9.5713, -36.7820), 'AP': (1.4144, -51.7750), 'AM': (-3.4168, -65.8561), 'BA': (-12.5797, -41.7007), 'CE': (-5.4984, -39.3206), 'DF': (-15.7797, -47.9297), 'ES': (-19.1834, -40.3089), 'GO': (-15.8270, -49.8362), 'MA': (-5.4200, -45.0000), 'MT': (-12.6819, -56.9211), 'MS': (-20.7722, -54.7852), 'MG': (-18.5122, -44.5550), 'PA': (-3.4168, -52.3330), 'PB': (-7.2399, -36.7819), 'PR': (-24.8949, -51.5545), 'PE': (-8.8137, -36.9541), 'PI': (-7.7183, -42.7289), 'RJ': (-22.9068, -43.1729), 'RN': (-5.7945, -36.5261), 'RS': (-30.0346, -51.2177), 'RO': (-10.9430, -62.0686), 'RR': (2.7376, -62.0751), 'SC': (-27.2423, -50.2189), 'SP': (-23.5505, -46.6333), 'SE': (-10.5741, -37.3857), 'TO': (-10.1753, -48.2982)}

    
    mapa = folium.Map(location=[locais[estado_regiao][0], locais[estado_regiao][1]], zoom_start=4)

    # estados = ['PR', 'RS', 'SC']

    cores = {'Com Vítimas Feridas': '#FDFD96', 'Sem Vítimas': '#77DD77', 'Com Vítimas Fatais': '#FF6961'}

    for _, row in contagem[contagem['uf'].isin(estado_escolhido)].iterrows():

    

        folium.CircleMarker(
        location=[row['latitude'].replace(',','.'), row['longitude'].replace(',','.')],
        radius=1,            
        color=cores[row['classificacao_acidente']],         
        # fill=True,           
        # fill_color=cores[row['classificacao_acidente']],    
        fill_opacity=0.7,    
        popup=row['classificacao_acidente'],
                            ).add_to(mapa)



    
    st_data = st_folium(mapa, width=700, height=500)