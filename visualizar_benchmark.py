# visualizar_benchmark_multiperfil.py
# -------------------------------------------------------------
# Visualizações para análise comparativa entre perfis de mobilidade
# 
# Gráficos gerados:
# 1. Speedup por perfil (comparação lado a lado)
# 2. Economia de nós por perfil
# 3. Distribuição de tempos por perfil
# 4. Impacto das penalizações nas rotas
# 5. Heatmap de performance
# 6. Análise por categoria de distância e perfil
# -------------------------------------------------------------

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuração de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class VisualizadorBenchmarkMultiPerfil:
    def __init__(self, arquivo_json: str):
        """
        Args:
            arquivo_json: Caminho para o arquivo JSON do benchmark multiperfil
        """
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.df = self._processar_dados()
        self.output_dir = Path("benchmark_results/multiperfil/graficos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Paleta de cores por perfil
        self.cores_perfis = {
            'Adulto Sem Dificuldades': '#DC143C',
            'Cadeirante': '#0066CC',
            'Idoso': '#FF8C00',
            'Gestante': '#FF69B4',
            'Criança/Acompanhante': '#9370DB',
            'Mobilidade Temporariamente Reduzida': '#FFD700'
        }
    
    def _processar_dados(self) -> pd.DataFrame:
        """Converte JSON para DataFrame do pandas"""
        registros = []
        
        for r in self.dados['resultados']:
            registros.append({
                'perfil': r['perfil'],
                'origem': r['origem'],
                'destino': r['destino'],
                'distancia_euclidiana': r['distancia_euclidiana'],
                'categoria': r['categoria'],
                'dijkstra_tempo_ms': r['dijkstra']['tempo_medio_ms'],
                'astar_tempo_ms': r['astar']['tempo_medio_ms'],
                'dijkstra_nos': r['dijkstra']['nos_explorados'],
                'astar_nos': r['astar']['nos_explorados'],
                'dijkstra_distancia': r['comprimento_rota_dijkstra'],
                'astar_distancia': r['comprimento_rota_astar'],
                'speedup': r['speedup_medio'],
                'economia_nos_pct': r['economia_nos_pct'],
                'diferenca_rotas_pct': r['diferenca_rotas_pct']
            })
        
        return pd.DataFrame(registros)
    
    def plot_speedup_comparativo(self):
        """Gráfico comparativo de speedup entre perfis"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calcula médias por perfil
        speedup_por_perfil = self.df.groupby('perfil')['speedup'].agg(['mean', 'std']).reset_index()
        speedup_por_perfil = speedup_por_perfil.sort_values('mean', ascending=True)
        
        # Gráfico de barras horizontais com erro
        cores = [self.cores_perfis.get(p, '#777777') for p in speedup_por_perfil['perfil']]
        
        y_pos = np.arange(len(speedup_por_perfil))
        ax.barh(y_pos, speedup_por_perfil['mean'], xerr=speedup_por_perfil['std'],
                color=cores, alpha=0.8, capsize=5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(speedup_por_perfil['perfil'])
        ax.set_xlabel('Speedup Médio (A* / Dijkstra)')
        ax.set_title('Comparação de Speedup entre Perfis de Mobilidade', fontsize=14, fontweight='bold')
        ax.axvline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Paridade')
        ax.grid(axis='x', alpha=0.3)
        ax.legend()
        
        # Adiciona valores nas barras
        for i, v in enumerate(speedup_por_perfil['mean']):
            ax.text(v + 0.05, i, f'{v:.2f}x', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'speedup_comparativo.png', dpi=300)
        print(f"✅ Gráfico salvo: speedup_comparativo.png")
        plt.close()
    
    def plot_economia_nos_comparativo(self):
        """Gráfico de economia de nós por perfil"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        economia_por_perfil = self.df.groupby('perfil')['economia_nos_pct'].agg(['mean', 'std']).reset_index()
        economia_por_perfil = economia_por_perfil.sort_values('mean', ascending=True)
        
        cores = [self.cores_perfis.get(p, '#777777') for p in economia_por_perfil['perfil']]
        
        y_pos = np.arange(len(economia_por_perfil))
        ax.barh(y_pos, economia_por_perfil['mean'], xerr=economia_por_perfil['std'],
                color=cores, alpha=0.8, capsize=5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(economia_por_perfil['perfil'])
        ax.set_xlabel('Economia Média de Nós (%)')
        ax.set_title('Economia de Nós Explorados (A* vs Dijkstra) por Perfil', fontsize=14, fontweight='bold')
        ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        
        # Adiciona valores nas barras
        for i, v in enumerate(economia_por_perfil['mean']):
            ax.text(v + 1, i, f'{v:.1f}%', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'economia_nos_comparativo.png', dpi=300)
        print(f"✅ Gráfico salvo: economia_nos_comparativo.png")
        plt.close()
    
    def plot_distribuicao_tempos_perfil(self):
        """Boxplots de distribuição de tempos por perfil"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Dijkstra
        self.df.boxplot(column='dijkstra_tempo_ms', by='perfil', ax=ax1, patch_artist=True)
        ax1.set_xlabel('Perfil de Mobilidade')
        ax1.set_ylabel('Tempo (ms)')
        ax1.set_title('Distribuição de Tempo - Dijkstra', fontsize=12, fontweight='bold')
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
        ax1.get_figure().suptitle('')
        
        # A*
        self.df.boxplot(column='astar_tempo_ms', by='perfil', ax=ax2, patch_artist=True)
        ax2.set_xlabel('Perfil de Mobilidade')
        ax2.set_ylabel('Tempo (ms)')
        ax2.set_title('Distribuição de Tempo - A*', fontsize=12, fontweight='bold')
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
        ax2.get_figure().suptitle('')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'distribuicao_tempos_perfil.png', dpi=300)
        print(f"✅ Gráfico salvo: distribuicao_tempos_perfil.png")
        plt.close()
    
    def plot_impacto_penalizacoes(self):
        """Análise do impacto das penalizações nas rotas"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        impacto = self.df.groupby('perfil')['diferenca_rotas_pct'].agg(['mean', 'std']).reset_index()
        impacto = impacto.sort_values('mean', ascending=False)
        
        cores = [self.cores_perfis.get(p, '#777777') for p in impacto['perfil']]
        
        x_pos = np.arange(len(impacto))
        ax.bar(x_pos, impacto['mean'], yerr=impacto['std'],
               color=cores, alpha=0.8, capsize=5)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(impacto['perfil'], rotation=45, ha='right')
        ax.set_ylabel('Diferença Média entre Rotas (%)')
        ax.set_title('Impacto das Penalizações: Diferença entre Rotas Dijkstra vs A*', 
                    fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Adiciona valores nas barras
        for i, v in enumerate(impacto['mean']):
            ax.text(i, v + impacto['std'].iloc[i] + 0.2, f'{v:.2f}%', ha='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'impacto_penalizacoes.png', dpi=300)
        print(f"✅ Gráfico salvo: impacto_penalizacoes.png")
        plt.close()
    
    def plot_heatmap_performance(self):
        """Heatmap de performance (speedup) por perfil e categoria"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Pivot table: perfil x categoria
        pivot = self.df.pivot_table(
            values='speedup',
            index='perfil',
            columns='categoria',
            aggfunc='mean'
        )
        
        # Ordena categorias
        ordem_categorias = ['curta', 'média', 'longa']
        pivot = pivot[ordem_categorias]
        
        # Heatmap
        sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn', 
                   cbar_kws={'label': 'Speedup (x)'},
                   linewidths=1, linecolor='gray', ax=ax)
        
        ax.set_title('Heatmap de Speedup: Perfil × Categoria de Distância', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Categoria de Distância', fontweight='bold')
        ax.set_ylabel('Perfil de Mobilidade', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'heatmap_performance.png', dpi=300)
        print(f"✅ Gráfico salvo: heatmap_performance.png")
        plt.close()
    
    def plot_nos_explorados_comparativo(self):
        """Comparação de nós explorados por perfil"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Agrupa por perfil
        nos_por_perfil = self.df.groupby('perfil').agg({
            'dijkstra_nos': 'mean',
            'astar_nos': 'mean'
        }).reset_index()
        
        x = np.arange(len(nos_por_perfil))
        width = 0.35
        
        cores_dijkstra = [self.cores_perfis.get(p, '#777777') for p in nos_por_perfil['perfil']]
        cores_astar = [c + '80' for c in cores_dijkstra]  # Adiciona transparência
        
        ax.bar(x - width/2, nos_por_perfil['dijkstra_nos'], width, 
               label='Dijkstra', color=cores_dijkstra, alpha=0.7)
        ax.bar(x + width/2, nos_por_perfil['astar_nos'], width, 
               label='A*', color=cores_dijkstra, alpha=0.4)
        
        ax.set_xlabel('Perfil de Mobilidade', fontweight='bold')
        ax.set_ylabel('Média de Nós Explorados', fontweight='bold')
        ax.set_title('Comparação de Nós Explorados: Dijkstra vs A* por Perfil', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(nos_por_perfil['perfil'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'nos_explorados_comparativo.png', dpi=300)
        print(f"✅ Gráfico salvo: nos_explorados_comparativo.png")
        plt.close()
    
    def plot_speedup_por_categoria(self):
        """Speedup separado por categoria de distância"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        categorias = ['curta', 'média', 'longa']
        
        for i, cat in enumerate(categorias):
            df_cat = self.df[self.df['categoria'] == cat]
            speedup_cat = df_cat.groupby('perfil')['speedup'].mean().sort_values()
            
            cores = [self.cores_perfis.get(p, '#777777') for p in speedup_cat.index]
            
            speedup_cat.plot(kind='barh', ax=axes[i], color=cores, alpha=0.8)
            axes[i].set_xlabel('Speedup (x)')
            axes[i].set_title(f'Categoria: {cat.capitalize()}', fontweight='bold')
            axes[i].axvline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[i].grid(axis='x', alpha=0.3)
            
            # Adiciona valores
            for j, v in enumerate(speedup_cat):
                axes[i].text(v + 0.05, j, f'{v:.2f}x', va='center')
        
        plt.suptitle('Speedup por Categoria de Distância', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'speedup_por_categoria.png', dpi=300)
        print(f"✅ Gráfico salvo: speedup_por_categoria.png")
        plt.close()
    
    def plot_comprimento_rotas(self):
        """Análise de comprimento de rotas por perfil"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Média de comprimento de rota por perfil
        comprimento = self.df.groupby('perfil').agg({
            'dijkstra_distancia': 'mean',
            'astar_distancia': 'mean'
        }).reset_index()
        
        x = np.arange(len(comprimento))
        width = 0.35
        
        ax.bar(x - width/2, comprimento['dijkstra_distancia'], width, 
               label='Dijkstra', color='#FF6B6B', alpha=0.8)
        ax.bar(x + width/2, comprimento['astar_distancia'], width, 
               label='A*', color='#4ECDC4', alpha=0.8)
        
        ax.set_xlabel('Perfil de Mobilidade', fontweight='bold')
        ax.set_ylabel('Comprimento Médio da Rota (m)', fontweight='bold')
        ax.set_title('Comprimento Médio das Rotas por Perfil', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(comprimento['perfil'], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comprimento_rotas.png', dpi=300)
        print(f"✅ Gráfico salvo: comprimento_rotas.png")
        plt.close()
    
    def gerar_tabela_resumo(self):
        """Gera tabela resumo em markdown"""
        resumo_perfil = self.df.groupby('perfil').agg({
            'dijkstra_tempo_ms': ['mean', 'std'],
            'astar_tempo_ms': ['mean', 'std'],
            'speedup': ['mean', 'median', 'min', 'max'],
            'economia_nos_pct': 'mean',
            'diferenca_rotas_pct': 'mean'
        }).round(2)
        
        caminho = self.output_dir / 'resumo_multiperfil.md'
        
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("# Resumo do Benchmark Multi-Perfil: Dijkstra vs A*\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total de testes: {len(self.df)}\n")
            f.write(f"Perfis testados: {self.df['perfil'].nunique()}\n\n")
            
            f.write("## Estatísticas por Perfil\n\n")
            f.write(resumo_perfil.to_markdown())
            f.write("\n\n")
            
            f.write("## Insights Principais\n\n")
            
            # Perfil com melhor speedup
            melhor_speedup = self.df.groupby('perfil')['speedup'].mean().idxmax()
            valor_speedup = self.df.groupby('perfil')['speedup'].mean().max()
            f.write(f"- **Perfil com melhor speedup**: {melhor_speedup} ({valor_speedup:.2f}x)\n")
            
            # Perfil com maior economia de nós
            melhor_economia = self.df.groupby('perfil')['economia_nos_pct'].mean().idxmax()
            valor_economia = self.df.groupby('perfil')['economia_nos_pct'].mean().max()
            f.write(f"- **Perfil com maior economia de nós**: {melhor_economia} ({valor_economia:.2f}%)\n")
            
            # Perfil com maior impacto nas rotas
            maior_impacto = self.df.groupby('perfil')['diferenca_rotas_pct'].mean().idxmax()
            valor_impacto = self.df.groupby('perfil')['diferenca_rotas_pct'].mean().max()
            f.write(f"- **Perfil com maior impacto nas rotas**: {maior_impacto} ({valor_impacto:.2f}%)\n")
            
            f.write("\n## Análise por Categoria\n\n")
            
            # Speedup por categoria
            for cat in ['curta', 'média', 'longa']:
                df_cat = self.df[self.df['categoria'] == cat]
                speedup_medio = df_cat['speedup'].mean()
                f.write(f"- **{cat.capitalize()}**: Speedup médio = {speedup_medio:.2f}x\n")
        
        print(f"✅ Resumo salvo: resumo_multiperfil.md")
    
    def gerar_todos_graficos(self):
        """Gera todos os gráficos de uma vez"""
        print("\n📊 Gerando visualizações multi-perfil...")
        print("-" * 50)
        
        self.plot_speedup_comparativo()
        self.plot_economia_nos_comparativo()
        self.plot_distribuicao_tempos_perfil()
        self.plot_impacto_penalizacoes()
        self.plot_heatmap_performance()
        self.plot_nos_explorados_comparativo()
        self.plot_speedup_por_categoria()
        self.plot_comprimento_rotas()
        self.gerar_tabela_resumo()
        
        print("-" * 50)
        print(f"✅ Todos os gráficos foram salvos em: {self.output_dir}")


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    import sys
    from glob import glob
    
    # Procura o arquivo JSON mais recente
    arquivos = sorted(glob("benchmark_results/multiperfil/benchmark_multiperfil_*.json"))
    
    if not arquivos:
        print("❌ Nenhum arquivo de benchmark multiperfil encontrado!")
        print("Execute primeiro: python benchmark_multiperfil.py")
        return
    
    arquivo = arquivos[-1] if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"📂 Carregando: {arquivo}")
    
    viz = VisualizadorBenchmarkMultiPerfil(arquivo)
    viz.gerar_todos_graficos()


if __name__ == "__main__":
    main()