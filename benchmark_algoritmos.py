# benchmark_multiperfil.py
# -------------------------------------------------------------
# Benchmark MULTI-PERFIL: Dijkstra vs A* com diferentes perfis de mobilidade
# 
# Analisa como as diferentes penalizações de cada perfil afetam:
# 1. Tempo de execução dos algoritmos
# 2. Número de nós explorados
# 3. Comprimento das rotas geradas
# 4. Speedup do A* sobre Dijkstra
# 
# Perfis testados:
# - Adulto Sem Dificuldades (baseline)
# - Cadeirante (penalizações muito altas)
# - Idoso (penalizações médias-altas)
# - Gestante (penalizações médias)
# - Criança/Acompanhante (penalizações variadas)
# - Mobilidade Temporariamente Reduzida (penalizações altas)
# -------------------------------------------------------------

import time
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

from route_calculator import calcular_rota, heuristica_astar
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
class ResultadoComparacaoPerfil:
    """Resultado da comparação entre algoritmos para um perfil específico"""
    perfil: str
    origem: str
    destino: str
    distancia_euclidiana: float
    categoria_distancia: str
    
    # Resultados Dijkstra
    dijkstra: MedicaoAlgoritmo
    
    # Resultados A*
    astar: MedicaoAlgoritmo
    
    # Métricas comparativas
    speedup_medio: float
    speedup_mediano: float
    economia_nos_pct: float
    
    # Análise do impacto do perfil
    comprimento_rota_dijkstra: float
    comprimento_rota_astar: float
    diferenca_rotas_pct: float  # % de diferença entre as rotas


# -------------------------------------------------------------
# Funções auxiliares
# -------------------------------------------------------------

def calcular_distancia_euclidiana(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula distância euclidiana aproximada em metros"""
    import math
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

def contar_nos_dijkstra(G, origem_id, destino_id) -> int:
    """Conta nós explorados pelo Dijkstra"""
    try:
        import heapq
        
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


def contar_nos_astar(G, origem_id, destino_id) -> int:
    """Conta nós explorados pelo A*"""
    try:
        import heapq
        
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
# Medição de algoritmos
# -------------------------------------------------------------

def medir_algoritmo_completo(G, origem, destino, algoritmo: str, repeticoes: int = 20) -> MedicaoAlgoritmo:
    """
    Mede tempo e nós explorados de um algoritmo com múltiplas repetições.
    
    Args:
        G: Grafo NetworkX
        origem: (lat, lon)
        destino: (lat, lon)
        algoritmo: "dijkstra" ou "astar"
        repeticoes: Número de repetições para média
        
    Returns:
        MedicaoAlgoritmo com estatísticas completas
    """
    tempos = []
    pontos_rota = None
    distancia = None
    nos_explorados = 0
    
    try:
        # Warm-up (3 iterações descartadas)
        for _ in range(3):
            calcular_rota(G, origem, destino, algoritmo)
        
        # Medições oficiais
        for _ in range(repeticoes):
            inicio = time.perf_counter()
            resultado_rota, resultado_dist = calcular_rota(G, origem, destino, algoritmo)
            tempo_ms = (time.perf_counter() - inicio) * 1000
            
            if resultado_rota is None:
                return MedicaoAlgoritmo(
                    algoritmo=algoritmo,
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
        
        if algoritmo.lower() == "dijkstra":
            nos_explorados = contar_nos_dijkstra(G, no_origem, no_destino)
        else:
            nos_explorados = contar_nos_astar(G, no_origem, no_destino)
        
        return MedicaoAlgoritmo(
            algoritmo=algoritmo,
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
            algoritmo=algoritmo,
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

class BenchmarkMultiPerfil:
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
        self.output_dir = Path("benchmark_results/multiperfil")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def executar(self, num_testes: int = 30, repeticoes_por_teste: int = 20, 
                 perfis_a_testar: Optional[List[str]] = None):
        """
        Executa benchmark comparativo para múltiplos perfis de mobilidade.
        
        Args:
            num_testes: Número de pares origem-destino a testar
            repeticoes_por_teste: Repetições por medição (para média)
            perfis_a_testar: Lista de chaves de perfis (None = todos)
        """
        
        # Define quais perfis testar
        if perfis_a_testar is None:
            perfis_a_testar = list(PERFIS_MOBILIDADE.keys())
        
        nomes = list(self.pois.keys())
        
        print("\n" + "="*70)
        print("🔬 BENCHMARK MULTI-PERFIL: Dijkstra vs A*")
        print("="*70)
        print(f"🎲 Seed: {self.seed}")
        print(f"📍 POIs disponíveis: {len(nomes)}")
        print(f"🧪 Pares origem-destino: {num_testes}")
        print(f"👥 Perfis a testar: {len(perfis_a_testar)}")
        print(f"🔁 Repetições por teste: {repeticoes_por_teste}")
        print(f"📁 Saída: {self.output_dir}")
        print("="*70)
        print("\n🧑‍🦽 Perfis que serão testados:")
        for chave in perfis_a_testar:
            perfil = obter_perfil(chave)
            print(f"  {perfil.icone} {perfil.nome}")
        print("="*70 + "\n")
        
        # Gera pares válidos uma única vez (reutiliza para todos os perfis)
        print("📋 Gerando pares origem-destino válidos...")
        pares_validos = []
        tentativas = 0
        max_tentativas = num_testes * 10  # Limite de segurança
        
        while len(pares_validos) < num_testes and tentativas < max_tentativas:
            origem_nome, destino_nome = random.sample(nomes, 2)
            origem = self.pois[origem_nome]
            destino = self.pois[destino_nome]
            
            # Valida conectividade no grafo base
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
        
        with tqdm(total=total_testes, desc="Progresso Total", ncols=80) as pbar:
            for chave_perfil in perfis_a_testar:
                perfil = obter_perfil(chave_perfil)
                
                # Pondera o grafo para este perfil
                G_ponderado = ponderar_grafo(self.G_base.copy(), perfil)
                
                pbar.set_description(f"Testando {perfil.icone} {perfil.nome[:20]}")
                
                # Testa cada par
                for par in pares_validos:
                    # Mede algoritmos
                    dijkstra = medir_algoritmo_completo(
                        G_ponderado, par['origem'], par['destino'], 
                        "dijkstra", repeticoes_por_teste
                    )
                    
                    astar = medir_algoritmo_completo(
                        G_ponderado, par['origem'], par['destino'], 
                        "astar", repeticoes_por_teste
                    )
                    
                    # Valida sucesso
                    if not (dijkstra.sucesso and astar.sucesso):
                        pbar.update(1)
                        continue
                    
                    # Calcula métricas
                    speedup_medio = dijkstra.tempo_medio_ms / astar.tempo_medio_ms if astar.tempo_medio_ms > 0 else 0
                    speedup_mediano = dijkstra.tempo_mediano_ms / astar.tempo_mediano_ms if astar.tempo_mediano_ms > 0 else 0
                    
                    economia_nos = 0
                    if dijkstra.nos_explorados > 0:
                        economia_nos = 100 * (1 - astar.nos_explorados / dijkstra.nos_explorados)
                    
                    # Diferença entre comprimentos de rota
                    diferenca_rotas = 0
                    if dijkstra.distancia > 0:
                        diferenca_rotas = 100 * abs(dijkstra.distancia - astar.distancia) / dijkstra.distancia
                    
                    # Registra resultado
                    resultado = ResultadoComparacaoPerfil(
                        perfil=perfil.nome,
                        origem=par['origem_nome'],
                        destino=par['destino_nome'],
                        distancia_euclidiana=par['distancia_euclidiana'],
                        categoria_distancia=par['categoria'],
                        dijkstra=dijkstra,
                        astar=astar,
                        speedup_medio=speedup_medio,
                        speedup_mediano=speedup_mediano,
                        economia_nos_pct=economia_nos,
                        comprimento_rota_dijkstra=dijkstra.distancia,
                        comprimento_rota_astar=astar.distancia,
                        diferenca_rotas_pct=diferenca_rotas
                    )
                    
                    self.resultados.append(resultado)
                    pbar.update(1)
        
        print(f"\n✅ Benchmark concluído! Total de resultados: {len(self.resultados)}")
        
        return self.resultados
    
    def exportar_csv(self):
        """Exporta resultados para CSV"""
        caminho = self.output_dir / f"benchmark_multiperfil_{self.timestamp}.csv"
        
        with open(caminho, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Cabeçalho
            writer.writerow([
                "perfil", "origem", "destino", "distancia_euclidiana_m", "categoria",
                "dijkstra_tempo_medio_ms", "dijkstra_desvio_padrao_ms", "dijkstra_nos_explorados",
                "dijkstra_distancia_rota_m", "astar_tempo_medio_ms", "astar_desvio_padrao_ms",
                "astar_nos_explorados", "astar_distancia_rota_m", "speedup_medio",
                "economia_nos_pct", "diferenca_rotas_pct"
            ])
            
            # Dados
            for r in self.resultados:
                writer.writerow([
                    r.perfil, r.origem, r.destino, f"{r.distancia_euclidiana:.2f}", r.categoria_distancia,
                    f"{r.dijkstra.tempo_medio_ms:.4f}", f"{r.dijkstra.desvio_padrao_ms:.4f}",
                    r.dijkstra.nos_explorados, f"{r.comprimento_rota_dijkstra:.2f}",
                    f"{r.astar.tempo_medio_ms:.4f}", f"{r.astar.desvio_padrao_ms:.4f}",
                    r.astar.nos_explorados, f"{r.comprimento_rota_astar:.2f}",
                    f"{r.speedup_medio:.2f}", f"{r.economia_nos_pct:.2f}",
                    f"{r.diferenca_rotas_pct:.2f}"
                ])
        
        print(f"💾 CSV exportado: {caminho}")
    
    def exportar_json(self):
        """Exporta resultados para JSON"""
        caminho = self.output_dir / f"benchmark_multiperfil_{self.timestamp}.json"
        
        dados = {
            "metadata": {
                "timestamp": self.timestamp,
                "seed": self.seed,
                "num_testes": len(self.resultados),
                "perfis_testados": list(set([r.perfil for r in self.resultados]))
            },
            "resultados": [
                {
                    "perfil": r.perfil,
                    "origem": r.origem,
                    "destino": r.destino,
                    "distancia_euclidiana": r.distancia_euclidiana,
                    "categoria": r.categoria_distancia,
                    "dijkstra": asdict(r.dijkstra),
                    "astar": asdict(r.astar),
                    "speedup_medio": r.speedup_medio,
                    "economia_nos_pct": r.economia_nos_pct,
                    "comprimento_rota_dijkstra": r.comprimento_rota_dijkstra,
                    "comprimento_rota_astar": r.comprimento_rota_astar,
                    "diferenca_rotas_pct": r.diferenca_rotas_pct
                }
                for r in self.resultados
            ]
        }
        
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON exportado: {caminho}")
    
    def gerar_relatorio_comparativo(self):
        """Gera relatório comparativo entre perfis"""
        if not self.resultados:
            print("⚠️  Sem resultados para gerar relatório")
            return
        
        print("\n" + "="*70)
        print("📊 RELATÓRIO COMPARATIVO ENTRE PERFIS")
        print("="*70)
        
        # Agrupa por perfil
        resultados_por_perfil = defaultdict(list)
        for r in self.resultados:
            resultados_por_perfil[r.perfil].append(r)
        
        print(f"\n📈 RESUMO GERAL")
        print("-" * 70)
        print(f"{'Perfil':30} {'Testes':>8} {'Speedup Médio':>15} {'Economia Nós':>15}")
        print("-" * 70)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            speedup_medio = statistics.mean([r.speedup_medio for r in resultados])
            economia_media = statistics.mean([r.economia_nos_pct for r in resultados])
            
            print(f"{perfil:30} {len(resultados):>8} {speedup_medio:>14.2f}x {economia_media:>14.1f}%")
        
        print("\n" + "="*70)
        print("⏱️  ANÁLISE DE TEMPO DE EXECUÇÃO POR PERFIL")
        print("="*70)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            
            tempos_dijkstra = [r.dijkstra.tempo_medio_ms for r in resultados]
            tempos_astar = [r.astar.tempo_medio_ms for r in resultados]
            
            print(f"\n{perfil}:")
            print(f"  Dijkstra - Média: {statistics.mean(tempos_dijkstra):.4f} ms")
            print(f"  A*       - Média: {statistics.mean(tempos_astar):.4f} ms")
            print(f"  Speedup  - Média: {statistics.mean([r.speedup_medio for r in resultados]):.2f}x")
        
        print("\n" + "="*70)
        print("🛣️  IMPACTO DAS PENALIZAÇÕES NAS ROTAS")
        print("="*70)
        
        for perfil in sorted(resultados_por_perfil.keys()):
            resultados = resultados_por_perfil[perfil]
            
            # Rotas que mudaram significativamente (>5% diferença)
            rotas_alteradas = [r for r in resultados if r.diferenca_rotas_pct > 5.0]
            
            print(f"\n{perfil}:")
            print(f"  Diferença média entre rotas: {statistics.mean([r.diferenca_rotas_pct for r in resultados]):.2f}%")
            print(f"  Rotas significativamente diferentes (>5%): {len(rotas_alteradas)}/{len(resultados)}")
            
            if rotas_alteradas:
                maior_diferenca = max(rotas_alteradas, key=lambda x: x.diferenca_rotas_pct)
                print(f"  Maior diferença: {maior_diferenca.diferenca_rotas_pct:.2f}% ({maior_diferenca.origem} → {maior_diferenca.destino})")
        
        print("\n" + "="*70)
    
    def executar_completo(self, num_testes: int = 30, repeticoes: int = 20, 
                         perfis_a_testar: Optional[List[str]] = None):
        """Executa benchmark + exportações + relatório"""
        self.executar(num_testes, repeticoes, perfis_a_testar)
        self.exportar_csv()
        self.exportar_json()
        self.gerar_relatorio_comparativo()


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    print("📥 Carregando dados...")
    
    G = carregar_grafo()
    pois, _ = carregar_pois("pontos de interesse.txt")

    print(f"✅ Grafo carregado: {len(G.nodes)} nós, {len(G.edges)} arestas")
    
    # Cria benchmark
    bench = BenchmarkMultiPerfil(G, pois, seed=42)
    
    # Executa com todos os perfis
    # Para testes rápidos, use: num_testes=10, repeticoes=10
    # Para produção: num_testes=50, repeticoes=20
    bench.executar_completo(
        num_testes=30,
        repeticoes=15,
        perfis_a_testar=None  # None = todos os perfis
    )


if __name__ == "__main__":
    main()