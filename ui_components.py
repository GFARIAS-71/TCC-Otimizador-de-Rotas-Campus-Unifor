# ui_components.py - COMPONENTES DE INTERFACE

import streamlit as st
import folium
from streamlit_folium import st_folium
from config import CENTRO_MAPA, ZOOM_INICIAL, TILES_URL, TILES_ATTR, VELOCIDADE_CAMINHADA, TAMANHO_PASSO
from mobility_profiles import listar_perfis, obter_descricoes_perfis, obter_perfil
from route_calculator import gerar_gpx

# Mapeamento de cores por categoria
CORES_CATEGORIAS = {
    "Blocos": "blue",
    "Outros Lugares": "green",
    "Estacionamentos": "orange",
    "Outros": "gray"
}

# Ícones por categoria
ICONES_CATEGORIAS = {
    "Blocos": "home",
    "Outros Lugares": "info-sign",
    "Estacionamentos": "car",
    "Outros": "map-marker"
}

def renderizar_cabecalho():
    """Renderiza o cabeçalho da aplicação"""
    st.title("🏫 Rotas a Pé dentro do Campus da Unifor")
    
    st.markdown("""
    ### 🖱️ Como usar:
    
    **Opção 1:** Clique em **dois pontos no mapa**  
    **Opção 2:** Clique em **dois marcadores coloridos** (Pontos de Interesse)  
    **Opção 3:** Use a **barra lateral** para selecionar Pontos de Interesse por categoria
    
    A rota ideal aparecerá automaticamente! 🚶‍♀️
    """)
    
    # Legenda de cores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔵 **Blocos Acadêmicos**")
    with col2:
        st.markdown("🟢 **Outros Lugares**")
    with col3:
        st.markdown("🟠 **Estacionamentos**")
    
    st.divider()


def renderizar_sidebar(G, pontos, categorias):
    """
    Renderiza a barra lateral com controles e informações.
    
    Args:
        G: Grafo NetworkX
        pontos: Dicionário de POIs {nome: (lat, lon)}
        categorias: Dicionário {nome: categoria}
        
    Returns:
        Lista com [origem, destino] se POIs foram selecionados, None caso contrário
    """
    with st.sidebar:
        st.header("⚙️ Painel de Controle")
        
        # --- SELETOR DE PERFIL DE MOBILIDADE ---
        st.subheader("👤 Perfil de Mobilidade")
        
        perfis_disponiveis = listar_perfis()
        descricoes = obter_descricoes_perfis()
        
        # Cria lista formatada para o selectbox
        opcoes_perfis = list(perfis_disponiveis.values())
        chaves_perfis = list(perfis_disponiveis.keys())
        
        # Encontra índice do perfil atual
        perfil_atual = st.session_state.get("perfil_mobilidade", "padrao")
        try:
            indice_atual = chaves_perfis.index(perfil_atual)
        except ValueError:
            indice_atual = 0
        
        # Selectbox de perfil
        perfil_selecionado = st.selectbox(
            "Selecione seu perfil:",
            opcoes_perfis,
            index=indice_atual,
            help="O perfil afeta a velocidade e os caminhos priorizados"
        )
        
        # Converte de volta para chave
        indice_selecionado = opcoes_perfis.index(perfil_selecionado)
        chave_selecionada = chaves_perfis[indice_selecionado]
        
        # Atualiza estado se mudou
        if chave_selecionada != st.session_state.get("perfil_mobilidade"):
            st.session_state["perfil_mobilidade"] = chave_selecionada
            # Limpa rota anterior ao mudar perfil
            st.session_state["rota"] = []
            st.session_state["distancia"] = None
            st.rerun()
        
        # Mostra descrição do perfil
        st.caption(f"ℹ️ {descricoes[chave_selecionada]}")
        
        st.divider()
        
        # --- Seleção de POIs por Categoria ---
        if pontos:
            st.subheader("📍 Selecionar Pontos de Interesse")
            
            # Organizar POIs por categoria
            pois_por_categoria = {}
            for nome, categoria in categorias.items():
                if categoria not in pois_por_categoria:
                    pois_por_categoria[categoria] = []
                pois_por_categoria[categoria].append(nome)
            
            # Ordenar categorias e POIs dentro de cada categoria
            for cat in pois_por_categoria:
                pois_por_categoria[cat].sort()
            
            # Criar lista de opções com separadores
            opcoes_origem = ["Selecione..."]
            opcoes_destino = ["Selecione..."]
            
            for categoria in sorted(pois_por_categoria.keys()):
                # Adiciona separador visual
                separador = f"--- {categoria} ---"
                opcoes_origem.append(separador)
                opcoes_destino.append(separador)
                
                # Adiciona POIs da categoria
                for poi in pois_por_categoria[categoria]:
                    opcoes_origem.append(f"  {poi}")
                    opcoes_destino.append(f"  {poi}")
            
            # Selectboxes
            poi_origem = st.selectbox(
                "🔵 Ponto de Origem",
                opcoes_origem,
                key="poi_origem"
            )
            
            poi_destino = st.selectbox(
                "🔴 Ponto de Destino",
                opcoes_destino,
                key="poi_destino"
            )
            
            # Botão para traçar rota
            if st.button("🎯 Traçar Rota entre Pontos Selecionados", use_container_width=True):
                # Remove espaços extras dos nomes
                origem_limpo = poi_origem.strip()
                destino_limpo = poi_destino.strip()
                
                if not origem_limpo.startswith("---") and origem_limpo != "Selecione..." and \
                   not destino_limpo.startswith("---") and destino_limpo != "Selecione...":
                    
                    if origem_limpo == destino_limpo:
                        st.error("❌ Selecione dois pontos diferentes!")
                    else:
                        return [pontos[origem_limpo], pontos[destino_limpo]]
                else:
                    st.warning("⚠️ Selecione origem e destino válidos")
            
            st.divider()
            
            # Filtro por categoria
            st.subheader("🔍 Filtrar no Mapa")
            categorias_unicas = sorted(set(categorias.values()))
            
            if "filtros_categorias" not in st.session_state:
                st.session_state["filtros_categorias"] = categorias_unicas
            
            filtros_selecionados = st.multiselect(
                "Mostrar categorias:",
                categorias_unicas,
                default=st.session_state["filtros_categorias"],
                key="filtro_cat"
            )
            
            st.session_state["filtros_categorias"] = filtros_selecionados
            
            st.divider()
        
        # --- Estatísticas do Grafo ---
        st.subheader("📊 Informações do Mapa")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nós", len(G.nodes))
            st.metric("POIs", len(pontos))
        with col2:
            st.metric("Arestas", len(G.edges))
            st.metric("Categorias", len(set(categorias.values())))
        
        # Densidade do grafo
        densidade = len(G.edges) / len(G.nodes) if len(G.nodes) > 0 else 0
        st.metric("Densidade", f"{densidade:.2f}")
        
        st.divider()
        
        # --- Modo Debug ---
        st.subheader("🐛 Desenvolvimento")
        
        debug = st.checkbox("Modo Debug", value=st.session_state.get("debug_mode", False))
        st.session_state["debug_mode"] = debug
        
        if debug:
            st.json({
                "clicks": st.session_state.get("clicks", []),
                "num_pontos_rota": len(st.session_state.get("rota", [])),
                "distancia": st.session_state.get("distancia"),
                "perfil": st.session_state.get("perfil_mobilidade", "padrao"),
                "filtros_ativos": st.session_state.get("filtros_categorias", [])
            })
        
        # --- Informações ---
        st.divider()
        st.caption("💡 **Dica:** Escolha seu perfil de mobilidade para rotas otimizadas!")
    
    return None


def criar_mapa_base():
    """Cria o mapa base do Folium"""
    m = folium.Map(
        location=CENTRO_MAPA,
        zoom_start=ZOOM_INICIAL,
        tiles=TILES_URL,
        attr=TILES_ATTR
    )
    
    folium.LayerControl().add_to(m)
    
    return m


def adicionar_pois_ao_mapa(m, pontos, categorias):
    """Adiciona marcadores de POIs ao mapa com cores por categoria"""
    filtros_ativos = st.session_state.get("filtros_categorias", list(set(categorias.values())))
    
    for nome, (lat, lon) in pontos.items():
        categoria = categorias.get(nome, "Outros")
        
        # Aplica filtro
        if categoria not in filtros_ativos:
            continue
        
        # Define cor e ícone baseado na categoria
        cor = CORES_CATEGORIAS.get(categoria, "gray")
        icone = ICONES_CATEGORIAS.get(categoria, "map-marker")
        
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>{nome}</b><br><i>{categoria}</i>", max_width=250),
            tooltip=f"{nome} ({categoria})",
            icon=folium.Icon(color=cor, icon=icone, prefix="glyphicon")
        ).add_to(m)


def adicionar_marcadores_rota(m):
    """Adiciona marcadores de origem e destino ao mapa"""
    clicks = st.session_state.get("clicks", [])
    
    for i, (lat, lon) in enumerate(clicks):
        if i == 0:
            cor = "darkblue"
            label = "🔵 Origem"
            icon = "play"
        else:
            cor = "darkred"
            label = "🔴 Destino"
            icon = "stop"
        
        folium.Marker(
            [lat, lon],
            popup=label,
            tooltip=label,
            icon=folium.Icon(color=cor, icon=icon, prefix="glyphicon")
        ).add_to(m)


def adicionar_linha_rota(m, perfil):
    """Adiciona a linha da rota ao mapa com cor baseada no perfil"""
    rota = st.session_state.get("rota", [])
    
    if rota:
        folium.PolyLine(
            rota,
            color=perfil.cor_rota,
            weight=6,
            opacity=0.85,
            popup="Rota calculada"
        ).add_to(m)


def renderizar_mapa(pontos, categorias, perfil):
    """
    Renderiza o mapa completo com POIs, marcadores e rota.
    
    Args:
        pontos: Dicionário de POIs
        categorias: Dicionário de categorias
        perfil: Perfil de mobilidade atual
        
    Returns:
        Dados do mapa (cliques e interações)
    """
    # Cria mapa base
    m = criar_mapa_base()
    
    # Adiciona elementos
    adicionar_pois_ao_mapa(m, pontos, categorias)
    adicionar_marcadores_rota(m)
    adicionar_linha_rota(m, perfil)
    
    # Renderiza
    map_data = st_folium(
        m,
        height=600,
        width=None,
        returned_objects=["last_clicked", "last_object_clicked"],
        key="mapa_unifor"
    )
    
    return map_data


def renderizar_informacoes_rota(perfil):
    """Renderiza as informações da rota calculada"""
    distancia = st.session_state.get("distancia")
    rota = st.session_state.get("rota", [])
    
    if not distancia or not rota:
        return
    
    # Cálculos baseados no perfil
    tempo_min = distancia / perfil.velocidade_caminhada
    
    # Passos só faz sentido para quem caminha
    if perfil.tamanho_passo > 0:
        passos = int(distancia / perfil.tamanho_passo)
        mostrar_passos = True
    else:
        passos = 0
        mostrar_passos = False
    
    st.divider()
    
    # Informações principais
    st.markdown(f"### {perfil.icone} Informações da Rota")
    
    if mostrar_passos:
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="📏 Distância",
            value=f"{distancia:.1f} m",
            help="Distância total do percurso"
        )
    
    with col2:
        st.metric(
            label="⏱️ Tempo Estimado",
            value=f"{tempo_min:.1f} min",
            help=f"Baseado em velocidade de {perfil.velocidade_caminhada}m/min para {perfil.nome}"
        )
    
    if mostrar_passos:
        with col3:
            st.metric(
                label="👣 Passos",
                value=f"{passos:,}",
                help=f"Aproximadamente {perfil.tamanho_passo}m por passo"
            )
    
    # Informações específicas do perfil
    if perfil.requer_acessibilidade:
        st.info("♿ Esta rota foi otimizada considerando requisitos de acessibilidade.")
    
    # Botão de exportar
    st.markdown("---")
    
    gpx_data = gerar_gpx(rota, f"Rota Unifor - {perfil.nome}")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.download_button(
            label="📥 Exportar Rota (GPX)",
            data=gpx_data,
            file_name=f"rota_unifor_{perfil.nome.lower().replace(' ', '_')}.gpx",
            mime="application/gpx+xml",
            use_container_width=True,
            help="Baixe a rota em formato GPX para usar em apps de GPS"
        )