# config.py - CONFIGURAÇÕES E CONSTANTES

import streamlit as st
from shapely.geometry import Polygon

# --- Configurações da página ---
def configurar_pagina():
    """Configura as propriedades da página Streamlit"""
    st.set_page_config(
        page_title="Rotas para Pedestres - Campus Unifor",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# --- Coordenadas do campus ---
COORDENADAS_CAMPUS = [
    (-38.481661, -3.771271),
    (-38.482034, -3.768190),
    (-38.480789, -3.768051),
    (-38.480912, -3.766418),
    (-38.477034, -3.766084),
    (-38.476956, -3.766911),
    (-38.476444, -3.766839),
    (-38.475435, -3.766550),
    (-38.473797, -3.766980),
    (-38.473748, -3.768062),
    (-38.473145, -3.768340),
    (-38.474609, -3.770682),
    (-38.481661, -3.771271)
]

# Polígono do campus com buffer
POLYGON_CAMPUS = Polygon(COORDENADAS_CAMPUS).buffer(0.0003)

# --- Centro do mapa ---
CENTRO_MAPA = [-3.7695, -38.4785]
ZOOM_INICIAL = 17

# --- Filtro OSM para caminhos pedestres ---
FILTRO_OSM = (
    '["highway"~"footway|path|pedestrian|living_street|residential|service|track|steps|corridor"]'
)

# --- Constantes de cálculo ---
VELOCIDADE_CAMINHADA = 80  # metros por minuto
TAMANHO_PASSO = 0.75  # metros por passo

# --- Tiles do mapa ---
TILES_URL = "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
TILES_ATTR = "OpenStreetMap France"

# --- Inicializa estado da sessão ---
def inicializar_estado():
    """Inicializa variáveis de estado do Streamlit"""
    if "initialized" not in st.session_state:
        st.session_state.update({
            "clicks": [],
            "rota": [],
            "distancia": None,
            "perfil_mobilidade": "padrao",  # Perfil padrão
            "initialized": True,
            "debug_mode": False
        })