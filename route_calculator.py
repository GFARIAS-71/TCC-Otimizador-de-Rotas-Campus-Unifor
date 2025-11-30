# route_calculator.py - CÁLCULO DE ROTAS

import streamlit as st
import osmnx as ox
import networkx as nx
import math


def heuristica_astar(G, no_atual, no_destino):
    """
    Função heurística para o algoritmo A*.
    
    Calcula a distância euclidiana entre o nó atual e o nó destino.
    Esta é uma heurística admissível (nunca superestima o custo real).
    
    Args:
        G: Grafo NetworkX
        no_atual: ID do nó atual
        no_destino: ID do nó de destino
        
    Returns:
        Estimativa de distância até o destino em metros
    """
    # Obtém coordenadas dos nós (x=lon, y=lat no OSMnx)
    lat_atual = G.nodes[no_atual]["y"]
    lon_atual = G.nodes[no_atual]["x"]
    
    lat_destino = G.nodes[no_destino]["y"]
    lon_destino = G.nodes[no_destino]["x"]
    
    # Diferenças em graus
    delta_lat = lat_destino - lat_atual
    delta_lon = lon_destino - lon_atual
    
    # Conversão aproximada para metros (1 grau ≈ 111km no equador)
    # Ajustamos pela latitude para maior precisão
    metros_por_grau_lat = 111000
    metros_por_grau_lon = 111000 * math.cos(math.radians(lat_atual))
    
    dist_metros = math.sqrt(
        (delta_lat * metros_por_grau_lat)**2 + 
        (delta_lon * metros_por_grau_lon)**2
    )
    
    return dist_metros


def extrair_geometria_rota(G, rota_nodes):
    """
    Extrai a geometria completa de uma rota a partir dos nós.
    
    Args:
        G: Grafo NetworkX
        rota_nodes: Lista de nós da rota
        
    Returns:
        Lista de tuplas (lat, lon) representando a rota
    """
    pontos_rota = []
    
    for u, v in zip(rota_nodes[:-1], rota_nodes[1:]):
        edge_data = G.get_edge_data(u, v)
        
        if not edge_data:
            continue
        
        # Usa apenas a primeira aresta disponível no multigraph
        attrs = list(edge_data.values())[0]
        
        geom = attrs.get("geometry")
        
        if geom:
            # Se tem geometria, usa todos os pontos da curva
            for lng, lat in geom.coords:  # coords vêm como (lon, lat)
                pontos_rota.append((lat, lng))
        else:
            # Se não tem geometria, usa linha reta entre os nós
            pontos_rota.append((G.nodes[u]["y"], G.nodes[u]["x"]))
            pontos_rota.append((G.nodes[v]["y"], G.nodes[v]["x"]))
    
    return pontos_rota


def calcular_rota(G, origem, destino, algoritmo="astar"):
    """
    Calcula a rota mais curta entre dois pontos usando A*, Dijkstra bidirecional ou Dijkstra unidirecional.
    
    Args:
        G: Grafo NetworkX
        origem: Tupla (lat, lon) do ponto de origem
        destino: Tupla (lat, lon) do ponto de destino
        algoritmo: "astar" (padrão), "dijkstra" (bidirecional), ou "dijkstra_uni" (unidirecional)
        
    Returns:
        Tupla (pontos_rota, distancia) ou (None, None) se não houver rota
    """
    try:
        # Encontra os nós mais próximos no grafo
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        
        # Calcula caminho de acordo com o algoritmo escolhido
        if algoritmo.lower() == "astar":
            # Usa A* com heurística de distância euclidiana (unidirecional)
            rota_nodes = nx.astar_path(
                G, 
                no_origem, 
                no_destino, 
                heuristic=lambda u, v: heuristica_astar(G, u, v),
                weight="length"
            )
            distancia = nx.astar_path_length(
                G,
                no_origem,
                no_destino,
                heuristic=lambda u, v: heuristica_astar(G, u, v),
                weight="length"
            )
        elif algoritmo.lower() == "dijkstra_uni":
            # Usa Dijkstra UNIDIRECIONAL (single-source)
            # Calcula caminhos de origem para todos os nós, mas retorna apenas para destino
            paths = nx.single_source_dijkstra_path(G, no_origem, weight="length")
            lengths = nx.single_source_dijkstra_path_length(G, no_origem, weight="length")
            
            rota_nodes = paths[no_destino]
            distancia = lengths[no_destino]
        else:  # dijkstra (bidirecional - comportamento padrão do NetworkX)
            # Usa Dijkstra BIDIRECIONAL (comportamento padrão de nx.shortest_path)
            rota_nodes = nx.shortest_path(G, no_origem, no_destino, weight="length")
            distancia = nx.shortest_path_length(G, no_origem, no_destino, weight="length")
        
        # Extrai geometria completa
        pontos_rota = extrair_geometria_rota(G, rota_nodes)
        
        return pontos_rota, distancia
        
    except nx.NetworkXNoPath:
        return None, None
    except Exception as e:
        st.error(f"⚠️ Erro ao calcular rota: {e}")
        return None, None


def calcular_rota_completa(G, origem, destino, perfil, algoritmo="astar"):
    """
    Calcula a rota e exibe mensagens de feedback ao usuário.
    
    Args:
        G: Grafo NetworkX
        origem: Tupla (lat, lon) do ponto de origem
        destino: Tupla (lat, lon) do ponto de destino
        perfil: Perfil de mobilidade do usuário
        algoritmo: "astar" (padrão), "dijkstra" (bidirecional), ou "dijkstra_uni" (unidirecional)
        
    Returns:
        Tupla (pontos_rota, distancia) ou (None, None) se não houver rota
    """
    # Mensagem do spinner diferenciada por algoritmo
    if algoritmo.lower() == "astar":
        mensagem_spinner = "🔍 Calculando melhor rota (A*)..."
    elif algoritmo.lower() == "dijkstra_uni":
        mensagem_spinner = "🔍 Calculando melhor rota (Dijkstra Unidirecional)..."
    else:
        mensagem_spinner = "🔍 Calculando melhor rota (Dijkstra Bidirecional)..."
    
    with st.spinner(mensagem_spinner):
        pontos_rota, distancia = calcular_rota(G, origem, destino, algoritmo)
        
        if pontos_rota is None:
            st.error("❌ Não existe rota caminhável entre esses pontos.")
            st.info("💡 Tente selecionar pontos mais próximos ou em áreas diferentes do campus.")
            return None, None
        
        # Mostra mensagem informativa do perfil, se houver
        if perfil.mensagem_informativa:
            st.info(perfil.mensagem_informativa)
        
        return pontos_rota, distancia


def gerar_gpx(rota, nome_rota="Rota Campus Unifor"):
    """
    Gera arquivo GPX a partir de uma rota.
    
    Args:
        rota: Lista de tuplas (lat, lon)
        nome_rota: Nome da rota para o arquivo GPX
        
    Returns:
        String com conteúdo XML do GPX
    """
    gpx_header = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Unifor Route Planner"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 
  http://www.topografix.com/GPX/1/1/gpx.xsd">
'''
    
    gpx_track = f'  <trk>\n    <name>{nome_rota}</name>\n    <trkseg>\n'
    
    for lat, lon in rota:
        gpx_track += f'      <trkpt lat="{lat}" lon="{lon}"></trkpt>\n'
    
    gpx_track += '    </trkseg>\n  </trk>\n'
    gpx_footer = '</gpx>'
    
    return gpx_header + gpx_track + gpx_footer