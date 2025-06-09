import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Consulta AvalieCE 2024",
    layout="wide",
    page_icon="📊"
)

# Autenticação simples
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def authenticate(username, password):
    return username == "Formace" and password == "Formace"

def login_form():
    with st.form("login"):
        st.title("🔐 Login")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        if submit:
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.experimental_rerun()
                return
            else:
                st.error("Usuário ou senha incorretos.")

def grafico_barra(df, taxa_acerto, descricao_habilidade, codigo_habilidade):    
    df[taxa_acerto] = pd.to_numeric(df[taxa_acerto], errors='coerce')
    df = df[df[taxa_acerto] > 0]

    df_agrupado = df.groupby([codigo_habilidade, descricao_habilidade], as_index=False)[taxa_acerto].mean()
    df_agrupado = df_agrupado.sort_values(by=codigo_habilidade)

    fig = px.bar(
        df_agrupado, 
        x=codigo_habilidade, 
        y=taxa_acerto,
        color=taxa_acerto,
        color_continuous_scale=[
            [0.0, "#e94f0e"],
            [0.25, "#f59c00"],
            [0.5, "#fccf05"],
            [0.75, "#2db39e"],
            [1.0, "#26a737"]
        ],
        range_color=[0, 100],
        text=df_agrupado[taxa_acerto].round(1),
        hover_data={
            descricao_habilidade: True,
            taxa_acerto: ':.2f'
        },
        labels={
            codigo_habilidade: 'Habilidade',
            taxa_acerto: 'Taxa de Acerto (%)',
            descricao_habilidade: 'Descrição da Habilidade'
        },
        height=500
    )

    fig.update_traces(
        texttemplate='%{text}%',
        textposition='inside',
        textfont_size=18,
        hoverlabel=dict(font_size=18)
    )

    fig.update_layout(
        yaxis=dict(range=[0, 100]),
        plot_bgcolor='white',
        showlegend=False,
        coloraxis_colorbar=dict(title='Acerto (%)'),
        title={'text': "Taxa Média de Acerto por Habilidade"},
        xaxis_title_font=dict(size=20),
        yaxis_title_font=dict(size=20),
        xaxis_tickfont=dict(size=16),
        yaxis_tickfont=dict(size=16),
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def carregar_dados():
    return pd.read_csv("dados.csv")

def main_app():
    st.title("📋 Sistema de Consulta - AvalieCE 2024")

    try:
        df = carregar_dados()

        st.sidebar.header("🎯 Filtros")

        regionais = ['Todas'] + sorted(df['NM_ENTIDADE'].dropna().unique().tolist())
        regional = st.sidebar.selectbox("Crede:", regionais)
        df_filtrado = df.copy()
        if regional != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['NM_ENTIDADE'] == regional]

        redes = ['Todas'] + sorted(df_filtrado['VL_FILTRO_REDE'].dropna().unique().tolist())
        rede = st.sidebar.selectbox("Rede:", redes)
        if rede != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['VL_FILTRO_REDE'] == rede]

        etapas = ['Todas'] + sorted(df_filtrado['VL_FILTRO_ETAPA'].dropna().unique().tolist())
        etapa = st.sidebar.selectbox("Etapa:", etapas)
        if etapa != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['VL_FILTRO_ETAPA'] == etapa]

        disciplinas = ['Todas'] + sorted(df_filtrado['VL_FILTRO_DISCIPLINA'].dropna().unique().tolist())
        disciplina = st.sidebar.selectbox("Disciplina:", disciplinas)
        if disciplina != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['VL_FILTRO_DISCIPLINA'] == disciplina]

        search_term = st.text_input("🔍 Buscar por palavra-chave (habilidade, código etc):")
        if search_term and 'DC_HABILIDADE' in df_filtrado.columns and 'CD_HABILIDADE' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[['DC_HABILIDADE', 'CD_HABILIDADE']].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)]

        if df_filtrado.empty:
            st.warning("Nenhum registro encontrado.")
        else:
            colunas_exibir = ['CD_HABILIDADE', 'DC_HABILIDADE', 'TX_ACERTO', 'DC_FILTRO_AVALIACAO']
            colunas_validas = [col for col in colunas_exibir if col in df_filtrado.columns]
            st.dataframe(df_filtrado[colunas_validas], use_container_width=True)
            st.success(f"✅ Total de registros: {len(df_filtrado)}")

            st.subheader("📊 Gráficos de Acerto por Habilidade (por Avaliação)")
            avaliacoes = df_filtrado['DC_FILTRO_AVALIACAO'].dropna().unique().tolist()

            for avaliacao in avaliacoes:
                df_avaliacao = df_filtrado[df_filtrado['DC_FILTRO_AVALIACAO'] == avaliacao]
                with st.expander(f"📝 {avaliacao}", expanded=False):
                    grafico_barra(
                        df_avaliacao,
                        taxa_acerto='TX_ACERTO',
                        descricao_habilidade='DC_HABILIDADE',
                        codigo_habilidade='CD_HABILIDADE'
                    )

        st.markdown("---")
        st.subheader("💬 Sua opinião é importante!")
        st.info(
            "Este sistema está em constante melhoria. Se você encontrou algum problema ou tem sugestões, "
            "**por favor, compartilhe com a equipe responsável.**"
        )

    except FileNotFoundError:
        st.error("❌ Arquivo 'dados.csv' não encontrado.")
    except Exception as e:
        st.error(f"❌ Erro: {e}")

    if st.sidebar.button("Sair"):
        st.session_state.authenticated = False
        st.experimental_rerun()

# Execução principal
if st.session_state.authenticated:
    main_app()
else:
    login_form()
    st.stop()  # Para a execução após o login
