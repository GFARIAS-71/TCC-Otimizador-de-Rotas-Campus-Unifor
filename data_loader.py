# data_loader.py - CARREGAMENTO DE DADOS

import streamlit as st
import osmnx as ox
from config import POLYGON_CAMPUS, FILTRO_OSM

@st.cache_data(show_spinner=True)
def carregar_grafo():
    """
    Carrega o grafo de ruas do campus da Unifor usando OSMnx.
    Retorna apenas a maior componente conectada.
    """
    with st.spinner("🔄 Carregando rede de caminhos da Unifor..."):
        try:
            ox.settings.useful_tags_way = ['wheelchair', 'surface', 'width', 'incline', 
                      'ramp', 'crossing', 'highway']
            G = ox.graph_from_polygon(
                POLYGON_CAMPUS,
                custom_filter=FILTRO_OSM,
                simplify=True,
            )
            
            # Mantém somente a maior componente (evita erro de NoPath)
            G = ox.truncate.largest_component(G, strongly=True)
            
            st.success(f"✅ Grafo carregado: {len(G.nodes)} nós e {len(G.edges)} arestas")
            return G
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar grafo: {e}")
            return None


@st.cache_data
def carregar_pois(caminho):
    """
    Carrega pontos de interesse de um arquivo de texto estruturado por categorias.
    
    Formato esperado:
    ---Categoria---
    Nome do Local: latitude, longitude
    
    Args:
        caminho: Path do arquivo de texto
        
    Returns:
        Tuple: (pontos_dict, categorias_dict)
        - pontos_dict: {nome: (lat, lon)}
        - categorias_dict: {nome: categoria}
    """
    pontos = {}
    categorias = {}
    categoria_atual = "Outros"
    
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            for num_linha, linha in enumerate(f, 1):
                linha = linha.strip()
                
                # Ignora linhas vazias
                if not linha:
                    continue
                
                # Detecta cabeçalhos de categoria
                if linha.startswith("---") and linha.endswith("---"):
                    categoria_atual = linha.strip("-").strip()
                    continue
                
                # Ignora comentários
                if linha.startswith("#"):
                    continue
                
                # Valida formato
                if ":" not in linha:
                    continue
                
                # Extrai dados
                partes = linha.split(":", 1)
                if len(partes) != 2:
                    continue
                    
                nome = partes[0].strip()
                coords = partes[1].strip()
                
                try:
                    lat, lon = map(float, coords.split(","))
                    pontos[nome] = (lat, lon)
                    categorias[nome] = categoria_atual
                except ValueError:
                    st.warning(f"⚠️ Linha {num_linha}: coordenadas inválidas para '{nome}'")
                    continue
        
        if pontos:
            # Conta POIs por categoria
            contagem = {}
            for cat in categorias.values():
                contagem[cat] = contagem.get(cat, 0) + 1
            
            st.success(f"✅ {len(pontos)} POIs carregados: {dict(contagem)}")
        else:
            st.info("ℹ️ Nenhum ponto de interesse encontrado no arquivo")
            
    except FileNotFoundError:
        st.error(f"❌ Arquivo '{caminho}' não encontrado.")
        st.info("""
        💡 **Como criar o arquivo:**
        
        Crie um arquivo `pontos de interesse.txt` com o formato:
        ```
        ---Blocos---
        Bloco A: -3.7710, -38.4812
        Bloco B: -3.7707, -38.4813
        
        ---Estacionamentos---
        Estacionamento Central: -3.7703, -38.4777
        ```
        """)
    
    return pontos, categorias


def validar_coordenada(lat, lon):
    """
    Verifica se uma coordenada está dentro do polígono do campus.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        bool: True se está dentro do campus
    """
    from shapely.geometry import Point
    
    ponto = Point(lon, lat)
    return POLYGON_CAMPUS.contains(ponto)