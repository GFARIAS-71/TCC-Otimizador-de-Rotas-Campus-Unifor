# benchmark_algoritmos.py
# -------------------------------------------------------------
# Benchmark COMPLETO: Dijkstra Unidirecional vs Dijkstra Bidirecional vs A*
# 
# Analisa TRÊS algoritmos:
# 1. Dijkstra Unidirecional (single_source_dijkstra)
# 2. Dijkstra Bidirecional (bidirectional_dijkstra) - padrão do nx.shortest_path
# 3. A* Unidirecional (astar_path)
# 
# Métricas analisadas:
# - Tempo de execução
# - Número de nós explorados
# - Comprimento das rotas geradas
# - Speedup comparativo
# -------------------------------------------------------------

import time
import math
import heapq
import random
import statistics
import json
import csv
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import networkx as nx
import osmnx as ox
from tqdm import tqdm

from route_calculator import heuristica_astar, extrair_geometria_rota
from data_loader import carregar_grafo, carregar_pois
from graph_weighting import ponderar_grafo
from mobility_profiles import obter_perfil, PERFIS_MOBILIDADE


# -------------------------------------------------------------
# Classes de dados
# -------------------------------------------------------------

@dataclass
class MedicaoAlgoritmo:
    """Resultado de uma medição de algoritmo"""
    algoritmo: str
    sucesso: bool
    tempos_ms: List[float]
    tempo_medio_ms: float
    tempo_mediano_ms: float
    desvio_padrao_ms: float
    distancia: float
    num_pontos: int
    nos_explorados: int
    erro: Optional[str] = None


@dataclass
class ResultadoComparacao:
    """Resultado da comparação entre os TRÊS algoritmos"""
    perfil: str
    origem: str
    destino: str
    distancia_euclidiana: float
    categoria_distancia: str
    
    # Resultados dos três algoritmos
    dijkstra_unidirecional: MedicaoAlgoritmo
    dijkstra_bidirecional: MedicaoAlgoritmo
    astar: MedicaoAlgoritmo
    
    # Métricas comparativas
    speedup_astar_vs_dijkstra_uni: float
    speedup_astar_vs_dijkstra_bi: float
    speedup_dijkstra_bi_vs_uni: float
    
    economia_nos_astar_vs_dijkstra_uni_pct: float
    economia_nos_astar_vs_dijkstra_bi_pct: float
    economia_nos_dijkstra_bi_vs_uni_pct: float
    
    # Diferenças nas rotas
    diferenca_rotas_dijkstra_bi_vs_uni_pct: float
    diferenca_rotas_astar_vs_dijkstra_uni_pct: float
    diferenca_rotas_astar_vs_dijkstra_bi_pct: float


# -------------------------------------------------------------
# Funções auxiliares
# -------------------------------------------------------------

def calcular_distancia_euclidiana(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula distância euclidiana aproximada em metros"""
    lat1, lon1 = p1
    lat2, lon2 = p2
    
    metros_por_grau_lat = 111000
    metros_por_grau_lon = 111000 * math.cos(math.radians(lat1))
    
    delta_lat = (lat2 - lat1) * metros_por_grau_lat
    delta_lon = (lon2 - lon1) * metros_por_grau_lon
    
    return math.sqrt(delta_lat**2 + delta_lon**2)


def categorizar_distancia(dist_metros: float) -> str:
    """Categoriza distância em curta/média/longa"""
    if dist_metros < 200:
        return "curta"
    elif dist_metros < 500:
        return "média"
    else:
        return "longa"


def verificar_conectividade(G, origem, destino) -> bool:
    """Verifica se há caminho entre origem e destino"""
    try:
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        return nx.has_path(G, no_origem, no_destino)
    except:
        return False


# -------------------------------------------------------------
# Contagem de nós explorados
# -------------------------------------------------------------

def contar_nos_dijkstra_unidirecional(G, origem_id, destino_id) -> int:
    """Conta nós explorados pelo Dijkstra UNIDIRECIONAL"""
    try:
        explorados = set()
        dist = {origem_id: 0}
        visitados = set()
        heap = [(0, origem_id)]
        
        while heap:
            d, u = heapq.heappop(heap)
            
            if u in visitados:
                continue
            
            visitados.add(u)
            explorados.add(u)
            
            if u == destino_id:
                break
            
            for v in G.neighbors(u):
                if v not in visitados:
                    peso_minimo = float('inf')
                    for key in G[u][v]:
                        peso = G[u][v][key].get('length', 1.0)
                        if peso < peso_minimo:
                            peso_minimo = peso
                    
                    nova_dist = d + peso_minimo
                    
                    if v not in dist or nova_dist < dist[v]:
                        dist[v] = nova_dist
                        heapq.heappush(heap, (nova_dist, v))
        
        return len(explorados)
    except Exception as e:
        return 0


def contar_nos_dijkstra_bidirecional(G, origem_id, destino_id) -> int:
    """
    Estima nós explorados pelo Dijkstra BIDIRECIONAL.
    
    Nota: Esta é uma aproximação baseada na execução do algoritmo.
    O NetworkX não expõe diretamente a contagem de nós.
    """
    try:
        # Busca forward
        explorados_forward = set()
        dist_forward = {origem_id: 0}
        visitados_forward = set()
        heap_forward = [(0, origem_id)]
        
        # Busca backward
        explorados_backward = set()
        dist_backward = {destino_id: 0}
        visitados_backward = set()
        heap_backward = [(0, destino_id)]
        
        encontrado = False
        
        while (heap_forward or heap_backward) and not encontrado:
            # Expande forward
            if heap_forward:
                d_f, u_f = heapq.heappop(heap_forward)
                
                if u_f not in visitados_forward:
                    visitados_forward.add(u_f)
                    explorados_forward.add(u_f)
                    
                    if u_f in visitados_backward:
                        encontrado = True
                        break
                    
                    for v in G.neighbors(u_f):
                        if v not in visitados_forward:
                            peso_minimo = float('inf')
                            for key in G[u_f][v]:
                                peso = G[u_f][v][key].get('length', 1.0)
                                if peso < peso_minimo:
                                    peso_minimo = peso
                            
                            nova_dist = d_f + peso_minimo
                            
                            if v not in dist_forward or nova_dist < dist_forward[v]:
                                dist_forward[v] = nova_dist
                                heapq.heappush(heap_forward, (nova_dist, v))
            
            # Expande backward
            if heap_backward and not encontrado:
                d_b, u_b = heapq.heappop(heap_backward)
                
                if u_b not in visitados_backward:
                    visitados_backward.add(u_b)
                    explorados_backward.add(u_b)
                    
                    if u_b in visitados_forward:
                        encontrado = True
                        break
                    
                    for v in G.neighbors(u_b):
                        if v not in visitados_backward:
                            peso_minimo = float('inf')
                            for key in G[u_b][v]:
                                peso = G[u_b][v][key].get('length', 1.0)
                                if peso < peso_minimo:
                                    peso_minimo = peso
                            
                            nova_dist = d_b + peso_minimo
                            
                            if v not in dist_backward or nova_dist < dist_backward[v]:
                                dist_backward[v] = nova_dist
                                heapq.heappush(heap_backward, (nova_dist, v))
        
        # Total = união dos nós explorados
        total = len(explorados_forward.union(explorados_backward))
        return total
        
    except Exception as e:
        return 0


def contar_nos_astar(G, origem_id, destino_id) -> int:
    """Conta nós explorados pelo A*"""
    try:
        explorados = set()
        visitados = set()
        dist = {origem_id: 0}
        heap = [(0, origem_id)]
        
        while heap:
            f_score, u = heapq.heappop(heap)
            
            if u in visitados:
                continue
            
            visitados.add(u)
            explorados.add(u)
            
            if u == destino_id:
                break
            
            for v in G.neighbors(u):
                if v not in visitados:
                    peso_minimo = float('inf')
                    for key in G[u][v]:
                        peso = G[u][v][key].get('length', 1.0)
                        if peso < peso_minimo:
                            peso_minimo = peso
                    
                    nova_dist = dist[u] + peso_minimo
                    
                    if v not in dist or nova_dist < dist[v]:
                        dist[v] = nova_dist
                        h = heuristica_astar(G, v, destino_id)
                        f = nova_dist + h
                        heapq.heappush(heap, (f, v))
        
        return len(explorados)
    except Exception as e:
        return 0


# -------------------------------------------------------------
# Funções de cálculo de rota
# -------------------------------------------------------------

def calcular_rota_dijkstra_unidirecional(G, origem, destino):
    """Calcula rota usando Dijkstra UNIDIRECIONAL"""
    try:
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        
        # Usa single_source_dijkstra para garantir unidirecional
        distancia, rota_nodes = nx.single_source_dijkstra(G, no_origem, no_destino, weight="length")
        
        # Extrai geometria
        pontos_rota = extrair_geometria_rota(G, rota_nodes)
        
        return pontos_rota, distancia
        
    except nx.NetworkXNoPath:
        return None, None
    except Exception as e:
        print(f"Erro Dijkstra Uni: {e}")
        return None, None


def calcular_rota_dijkstra_bidirecional(G, origem, destino):
    """Calcula rota usando Dijkstra BIDIRECIONAL (padrão do NetworkX)"""
    try:
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        
        # Usa bidirectional_dijkstra explicitamente
        distancia, rota_nodes = nx.bidirectional_dijkstra(G, no_origem, no_destino, weight="length")
        
        # Extrai geometria
        pontos_rota = extrair_geometria_rota(G, rota_nodes)
        
        return pontos_rota, distancia
        
    except nx.NetworkXNoPath:
        return None, None
    except Exception as e:
        print(f"Erro Dijkstra Bi: {e}")
        return None, None


def calcular_rota_astar(G, origem, destino):
    """Calcula rota usando A* - VERSÃO CORRIGIDA (executa apenas 1x)"""
    try:
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        
        # Calcula caminho UMA VEZ (não usar astar_path_length - executa 2x!)
        rota_nodes = nx.astar_path(
            G, 
            no_origem, 
            no_destino, 
            heuristic=lambda u, v: heuristica_astar(G, u, v),
            weight="length"
        )
        
        # Calcula distância MANUALMENTE a partir do caminho já calculado
        distancia = 0
        for u, v in zip(rota_nodes[:-1], rota_nodes[1:]):
            # Pega o peso mínimo entre arestas paralelas (multigraph)
            edge_data = G.get_edge_data(u, v)
            if edge_data:
                peso_minimo = min(
                    attrs.get("length", float('inf')) 
                    for attrs in edge_data.values()
                )
                distancia += peso_minimo
        
        # Extrai geometria
        pontos_rota = extrair_geometria_rota(G, rota_nodes)
        
        return pontos_rota, distancia
        
    except nx.NetworkXNoPath:
        return None, None
    except Exception as e:
        print(f"Erro A*: {e}")
        return None, None


# -------------------------------------------------------------
# Medição de algoritmos
# -------------------------------------------------------------

def medir_algoritmo(G, origem, destino, algoritmo: str, repeticoes: int = 20) -> MedicaoAlgoritmo:
    """
    Mede tempo e nós explorados de um algoritmo.
    
    Args:
        G: Grafo NetworkX
        origem: (lat, lon)
        destino: (lat, lon)
        algoritmo: "dijkstra_uni", "dijkstra_bi" ou "astar"
        repeticoes: Número de repetições para média
        
    Returns:
        MedicaoAlgoritmo com estatísticas completas
    """
    tempos = []
    pontos_rota = None
    distancia = None
    nos_explorados = 0
    
    # Escolhe função de cálculo
    if algoritmo == "dijkstra_uni":
        funcao_calculo = calcular_rota_dijkstra_unidirecional
        funcao_contagem = contar_nos_dijkstra_unidirecional
        nome_display = "Dijkstra Unidirecional"
    elif algoritmo == "dijkstra_bi":
        funcao_calculo = calcular_rota_dijkstra_bidirecional
        funcao_contagem = contar_nos_dijkstra_bidirecional
        nome_display = "Dijkstra Bidirecional"
    else:  # astar
        funcao_calculo = calcular_rota_astar
        funcao_contagem = contar_nos_astar
        nome_display = "A*"
    
    try:
        # Warm-up (3 iterações descartadas)
        for _ in range(3):
            funcao_calculo(G, origem, destino)
        
        # Medições oficiais
        for _ in range(repeticoes):
            inicio = time.perf_counter()
            resultado_rota, resultado_dist = funcao_calculo(G, origem, destino)
            tempo_ms = (time.perf_counter() - inicio) * 1000
            
            if resultado_rota is None:
                return MedicaoAlgoritmo(
                    algoritmo=nome_display,
                    sucesso=False,
                    tempos_ms=[],
                    tempo_medio_ms=0,
                    tempo_mediano_ms=0,
                    desvio_padrao_ms=0,
                    distancia=0,
                    num_pontos=0,
                    nos_explorados=0,
                    erro="Caminho não encontrado"
                )
            
            tempos.append(tempo_ms)
            
            if pontos_rota is None:
                pontos_rota = resultado_rota
                distancia = resultado_dist
        
        # Conta nós explorados (1 vez apenas)
        no_origem = ox.distance.nearest_nodes(G, origem[1], origem[0])
        no_destino = ox.distance.nearest_nodes(G, destino[1], destino[0])
        nos_explorados = funcao_contagem(G, no_origem, no_destino)
        
        return MedicaoAlgoritmo(
            algoritmo=nome_display,
            sucesso=True,
            tempos_ms=tempos,
            tempo_medio_ms=statistics.mean(tempos),
            tempo_mediano_ms=statistics.median(tempos),
            desvio_padrao_ms=statistics.stdev(tempos) if len(tempos) > 1 else 0,
            distancia=distancia,
            num_pontos=len(pontos_rota),
            nos_explorados=nos_explorados
        )
        
    except Exception as e:
        return MedicaoAlgoritmo(
            algoritmo=nome_display,
            sucesso=False,
            tempos_ms=[],
            tempo_medio_ms=0,
            tempo_mediano_ms=0,
            desvio_padrao_ms=0,
            distancia=0,
            num_pontos=0,
            nos_explorados=0,
            erro=str(e)
        )


# -------------------------------------------------------------
# Classe principal de benchmark
# -------------------------------------------------------------

class BenchmarkTresAlgoritmos:
    def __init__(self, G_base, pois: Dict[str, Tuple[float, float]], seed: int = 42):
        """
        Args:
            G_base: Grafo base (sem ponderação)
            pois: Dicionário {nome: (lat, lon)}
            seed: Seed para reprodutibilidade
        """
        self.G_base = G_base
        self.pois = pois
        self.seed = seed
        self.resultados = []
        
        random.seed(seed)
        
        # Diretório de saída
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("benchmark_results/tres_algoritmos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def executar(self, num_testes: int = 30, repeticoes_por_teste: int = 20, 
                 perfis_a_testar: Optional[List[str]] = None):
        """
        Executa benchmark comparativo dos TRÊS algoritmos.
        
        Args:
            num_testes: Número de pares origem-destino a testar
            repeticoes_por_teste: Repetições por medição (para média)
            perfis_a_testar: Lista de chaves de perfis (None = todos)
        """
        
        # Define quais perfis testar
        if perfis_a_testar is None:
            perfis_a_testar = list(PERFIS_MOBILIDADE.keys())
        
        nomes = list(self.pois.keys())
        
        print("\n" + "="*80)
        print("🔬 BENCHMARK COMPLETO: Dijkstra Uni vs Dijkstra Bi vs A*")
        print("="*80)
        print(f"🎲 Seed: {self.seed}")
        print(f"📍 POIs disponíveis: {len(nomes)}")
        print(f"🧪 Pares origem-destino: {num_testes}")
        print(f"👥 Perfis a testar: {len(perfis_a_testar)}")
        print(f"🔁 Repetições por teste: {repeticoes_por_teste}")
        print(f"📂 Saída: {self.output_dir}")
        print("="*80)
        print("\n🧑‍🦽 Perfis que serão testados:")
        for chave in perfis_a_testar:
            perfil = obter_perfil(chave)
            print(f"  {perfil.icone} {perfil.nome}")
        print("="*80 + "\n")
        
        # Gera pares válidos
        print("📋 Gerando pares origem-destino válidos...")
        pares_validos = []
        tentativas = 0
        max_tentativas = num_testes * 10
        
        while len(pares_validos) < num_testes and tentativas < max_tentativas:
            origem_nome, destino_nome = random.sample(nomes, 2)
            origem = self.pois[origem_nome]
            destino = self.pois[destino_nome]
            
            if verificar_conectividade(self.G_base, origem, destino):
                dist_euclidiana = calcular_distancia_euclidiana(origem, destino)
                categoria = categorizar_distancia(dist_euclidiana)
                
                pares_validos.append({
                    'origem_nome': origem_nome,
                    'destino_nome': destino_nome,
                    'origem': origem,
                    'destino': destino,
                    'distancia_euclidiana': dist_euclidiana,
                    'categoria': categoria
                })
            
            tentativas += 1
        
        print(f"✅ {len(pares_validos)} pares válidos gerados\n")
        
        # Testa cada perfil
        total_testes = len(perfis_a_testar) * len(pares_validos)
        
        with tqdm(total=total_testes, desc="Progresso Total", ncols=100) as pbar:
            for chave_perfil in perfis_a_testar:
                perfil = obter_perfil(chave_perfil)
                
                # Pondera o grafo para este perfil
                G_ponderado = ponderar_grafo(self.G_base.copy(), perfil)
                
                pbar.set_description(f"Testando {perfil.icone} {perfil.nome[:25]}")
                
                # Testa cada par
                for par in pares_validos:
                    # Mede os TRÊS algoritmos
                    dijkstra_uni = medir_algoritmo(
                        G_ponderado, par['origem'], par['destino'], 
                        "dijkstra_uni", repeticoes_por_teste
                    )
                    
                    dijkstra_bi = medir_algoritmo(
                        G_ponderado, par['origem'], par['destino'], 
                        "dijkstra_bi", repeticoes_por_teste
                    )
                    
                    astar = medir_algoritmo(
                        G_ponderado, par['origem'], par['destino'], 
                        "astar", repeticoes_por_teste
                    )
                    
                    # Valida sucesso
                    if not (dijkstra_uni.sucesso and dijkstra_bi.sucesso and astar.sucesso):
                        pbar.update(1)
                        continue
                    
                    # Calcula speedups
                    speedup_astar_vs_uni = dijkstra_uni.tempo_medio_ms / astar.tempo_medio_ms if astar.tempo_medio_ms > 0 else 0
                    speedup_astar_vs_bi = dijkstra_bi.tempo_medio_ms / astar.tempo_medio_ms if astar.tempo_medio_ms > 0 else 0
                    speedup_bi_vs_uni = dijkstra_uni.tempo_medio_ms / dijkstra_bi.tempo_medio_ms if dijkstra_bi.tempo_medio_ms > 0 else 0
                    
                    # Calcula economias de nós
                    economia_astar_vs_uni = 0
                    if dijkstra_uni.nos_explorados > 0:
                        economia_astar_vs_uni = 100 * (1 - astar.nos_explorados / dijkstra_uni.nos_explorados)
                    
                    economia_astar_vs_bi = 0
                    if dijkstra_bi.nos_explorados > 0:
                        economia_astar_vs_bi = 100 * (1 - astar.nos_explorados / dijkstra_bi.nos_explorados)
                    
                    economia_bi_vs_uni = 0
                    if dijkstra_uni.nos_explorados > 0:
                        economia_bi_vs_uni = 100 * (1 - dijkstra_bi.nos_explorados / dijkstra_uni.nos_explorados)
                    
                    # Diferenças entre rotas
                    diff_bi_vs_uni = 0
                    if dijkstra_uni.distancia > 0:
                        diff_bi_vs_uni = 100 * abs(dijkstra_bi.distancia - dijkstra_uni.distancia) / dijkstra_uni.distancia
                    
                    diff_astar_vs_uni = 0
                    if dijkstra_uni.distancia > 0:
                        diff_astar_vs_uni = 100 * abs(astar.distancia - dijkstra_uni.distancia) / dijkstra_uni.distancia
                    
                    diff_astar_vs_bi = 0
                    if dijkstra_bi.distancia > 0:
                        diff_astar_vs_bi = 100 * abs(astar.distancia - dijkstra_bi.distancia) / dijkstra_bi.distancia
                    
                    # Registra resultado
                    resultado = ResultadoComparacao(
                        perfil=perfil.nome,
                        origem=par['origem_nome'],
                        destino=par['destino_nome'],
                        distancia_euclidiana=par['distancia_euclidiana'],
                        categoria_distancia=par['categoria'],
                        dijkstra_unidirecional=dijkstra_uni,
                        dijkstra_bidirecional=dijkstra_bi,
                        astar=astar,
                        speedup_astar_vs_dijkstra_uni=speedup_astar_vs_uni,
                        speedup_astar_vs_dijkstra_bi=speedup_astar_vs_bi,
                        speedup_dijkstra_bi_vs_uni=speedup_bi_vs_uni,
                        economia_nos_astar_vs_dijkstra_uni_pct=economia_astar_vs_uni,
                        economia_nos_astar_vs_dijkstra_bi_pct=economia_astar_vs_bi,
                        economia_nos_dijkstra_bi_vs_uni_pct=economia_bi_vs_uni,
                        diferenca_rotas_dijkstra_bi_vs_uni_pct=diff_bi_vs_uni,
                        diferenca_rotas_astar_vs_dijkstra_uni_pct=diff_astar_vs_uni,
                        diferenca_rotas_astar_vs_dijkstra_bi_pct=diff_astar_vs_bi
                    )
                    
                    self.resultados.append(resultado)
                    pbar.update(1)
        
        print(f"\n✅ Benchmark concluído! Total de resultados: {len(self.resultados)}")
        
        return self.resultados
    
    def exportar_csv(self):
        """Exporta resultados para CSV"""
        caminho = self.output_dir / f"benchmark_tres_algoritmos_{self.timestamp}.csv"
        
        with open(caminho, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Cabeçalho
            writer.writerow([
                "perfil", "origem", "destino", "distancia_euclidiana_m", "categoria",
                "dijkstra_uni_tempo_ms", "dijkstra_uni_desvpad_ms", "dijkstra_uni_nos",
                "dijkstra_bi_tempo_ms", "dijkstra_bi_desvpad_ms", "dijkstra_bi_nos",
                "astar_tempo_ms", "astar_desvpad_ms", "astar_nos",
                "speedup_astar_vs_dijkstra_uni", "speedup_astar_vs_dijkstra_bi", 
                "speedup_dijkstra_bi_vs_uni",
                "economia_nos_astar_vs_uni_pct", "economia_nos_astar_vs_bi_pct",
                "economia_nos_bi_vs_uni_pct"
            ])
            
            # Dados
            for r in self.resultados:
                writer.writerow([
                    r.perfil, r.origem, r.destino, f"{r.distancia_euclidiana:.2f}", r.categoria_distancia,
                    f"{r.dijkstra_unidirecional.tempo_medio_ms:.4f}", 
                    f"{r.dijkstra_unidirecional.desvio_padrao_ms:.4f}",
                    r.dijkstra_unidirecional.nos_explorados,
                    f"{r.dijkstra_bidirecional.tempo_medio_ms:.4f}",
                    f"{r.dijkstra_bidirecional.desvio_padrao_ms:.4f}",
                    r.dijkstra_bidirecional.nos_explorados,
                    f"{r.astar.tempo_medio_ms:.4f}",
                    f"{r.astar.desvio_padrao_ms:.4f}",
                    r.astar.nos_explorados,
                    f"{r.speedup_astar_vs_dijkstra_uni:.2f}",
                    f"{r.speedup_astar_vs_dijkstra_bi:.2f}",
                    f"{r.speedup_dijkstra_bi_vs_uni:.2f}",
                    f"{r.economia_nos_astar_vs_dijkstra_uni_pct:.2f}",
                    f"{r.economia_nos_astar_vs_dijkstra_bi_pct:.2f}",
                    f"{r.economia_nos_dijkstra_bi_vs_uni_pct:.2f}"
                ])
        
        print(f"💾 CSV exportado: {caminho}")
    
    def exportar_json(self):
        """Exporta resultados para JSON"""
        caminho = self.output_dir / f"benchmark_tres_algoritmos_{self.timestamp}.json"
        
        dados = {
            "metadata": {
                "timestamp": self.timestamp,
                "seed": self.seed,
                "num_testes": len(self.resultados),
                "perfis_testados": list(set([r.perfil for r in self.resultados])),
                "algoritmos": ["Dijkstra Unidirecional", "Dijkstra Bidirecional", "A*"]
            },
            "resultados": [
                {
                    "perfil": r.perfil,
                    "origem": r.origem,
                    "destino": r.destino,
                    "distancia_euclidiana": r.distancia_euclidiana,
                    "categoria": r.categoria_distancia,
                    "dijkstra_unidirecional": asdict(r.dijkstra_unidirecional),
                    "dijkstra_bidirecional": asdict(r.dijkstra_bidirecional),
                    "astar": asdict(r.astar),
                    "speedups": {
                        "astar_vs_dijkstra_uni": r.speedup_astar_vs_dijkstra_uni,
                        "astar_vs_dijkstra_bi": r.speedup_astar_vs_dijkstra_bi,
                        "dijkstra_bi_vs_uni": r.speedup_dijkstra_bi_vs_uni
                    },
                    "economia_nos_pct": {
                        "astar_vs_dijkstra_uni": r.economia_nos_astar_vs_dijkstra_uni_pct,
                        "astar_vs_dijkstra_bi": r.economia_nos_astar_vs_dijkstra_bi_pct,
                        "dijkstra_bi_vs_uni": r.economia_nos_dijkstra_bi_vs_uni_pct
                    }
                }
                for r in self.resultados
            ]
        }
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON exportado: {caminho}")
    
    def gerar_relatorio(self):
        """Gera relatório comparativo"""
        if not self.resultados:
            print("⚠️  Sem resultados para gerar relatório")
            return
        
        print("\n" + "="*80)
        print("📊 RELATÓRIO COMPARATIVO - TRÊS ALGORITMOS")
        print("="*80)
        
        # Agrupa por perfil
        resultados_por_perfil = defaultdict(list)
        for r in self.resultados:
            resultados_por_perfil[r.perfil].append(r)
        
        print(f"\n📈 RESUMO GERAL")
        print("-" * 80)
        print(f"{'Perfil':35} {'Testes':>8} {'A*/Dij-Uni':>12} {'A*/Dij-Bi':>12} {'Dij-Bi/Uni':>12}")
        print("-" * 80)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            speedup_astar_uni = statistics.mean([r.speedup_astar_vs_dijkstra_uni for r in resultados])
            speedup_astar_bi = statistics.mean([r.speedup_astar_vs_dijkstra_bi for r in resultados])
            speedup_bi_uni = statistics.mean([r.speedup_dijkstra_bi_vs_uni for r in resultados])
            
            print(f"{perfil:35} {len(resultados):>8} {speedup_astar_uni:>11.2f}x {speedup_astar_bi:>11.2f}x {speedup_bi_uni:>11.2f}x")
        
        print("\n" + "="*80)
        print("⏱️  ANÁLISE DE TEMPO MÉDIO (ms)")
        print("="*80)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            
            tempo_uni = statistics.mean([r.dijkstra_unidirecional.tempo_medio_ms for r in resultados])
            tempo_bi = statistics.mean([r.dijkstra_bidirecional.tempo_medio_ms for r in resultados])
            tempo_astar = statistics.mean([r.astar.tempo_medio_ms for r in resultados])
            
            print(f"\n{perfil}:")
            print(f"  Dijkstra Unidirecional: {tempo_uni:>8.4f} ms")
            print(f"  Dijkstra Bidirecional:  {tempo_bi:>8.4f} ms")
            print(f"  A*:                     {tempo_astar:>8.4f} ms")
        
        print("\n" + "="*80)
        print("🔍 ECONOMIA DE NÓS EXPLORADOS (%)")
        print("="*80)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            
            economia_astar_uni = statistics.mean([r.economia_nos_astar_vs_dijkstra_uni_pct for r in resultados])
            economia_astar_bi = statistics.mean([r.economia_nos_astar_vs_dijkstra_bi_pct for r in resultados])
            economia_bi_uni = statistics.mean([r.economia_nos_dijkstra_bi_vs_uni_pct for r in resultados])
            
            print(f"\n{perfil}:")
            print(f"  A* vs Dijkstra Uni:      {economia_astar_uni:>6.2f}%")
            print(f"  A* vs Dijkstra Bi:       {economia_astar_bi:>6.2f}%")
            print(f"  Dijkstra Bi vs Uni:      {economia_bi_uni:>6.2f}%")
        
        print("\n" + "="*80)
    
    def executar_completo(self, num_testes: int = 30, repeticoes: int = 20, 
                         perfis_a_testar: Optional[List[str]] = None):
        """Executa benchmark + exportações + relatório"""
        self.executar(num_testes, repeticoes, perfis_a_testar)
        self.exportar_csv()
        self.exportar_json()
        self.gerar_relatorio()


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    print("🔥 Carregando dados...")
    
    G = carregar_grafo()
    pois, _ = carregar_pois("pontos de interesse.txt")

    print(f"✅ Grafo carregado: {len(G.nodes)} nós, {len(G.edges)} arestas")
    
    # Cria benchmark
    bench = BenchmarkTresAlgoritmos(G, pois, seed=42)
    
    # Executa com todos os perfis
    bench.executar_completo(
        num_testes=30,
        repeticoes=15,
        perfis_a_testar=None  # None = todos os perfis
    )


if __name__ == "__main__":
    main()