# visualizar_benchmark.py
# -------------------------------------------------------------
# Visualizações para benchmark de TRÊS algoritmos
# 
# Gráficos gerados:
# 1. Speedup comparativo entre os três algoritmos
# 2. Economia de nós por algoritmo
# 3. Distribuição de tempos
# 4. Heatmap de performance
# 5. Análise por categoria de distância
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
plt.rcParams['figure.figsize'] = (16, 9)
plt.rcParams['font.size'] = 11


class VisualizadorTresAlgoritmos:
    def __init__(self, arquivo_json: str):
        """
        Args:
            arquivo_json: Caminho para o arquivo JSON do benchmark
        """
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            self.dados = json.load(f)
        
        self.df = self._processar_dados()
        self.output_dir = Path("benchmark_results/tres_algoritmos/graficos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Paleta de cores
        self.cores_algoritmos = {
            'Dijkstra Unidirecional': '#E74C3C',  # Vermelho
            'Dijkstra Bidirecional': '#3498DB',   # Azul
            'A*': '#2ECC71'                        # Verde
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
                
                # Dijkstra Unidirecional
                'dijkstra_uni_tempo_ms': r['dijkstra_unidirecional']['tempo_medio_ms'],
                'dijkstra_uni_nos': r['dijkstra_unidirecional']['nos_explorados'],
                'dijkstra_uni_distancia': r['dijkstra_unidirecional']['distancia'],
                
                # Dijkstra Bidirecional
                'dijkstra_bi_tempo_ms': r['dijkstra_bidirecional']['tempo_medio_ms'],
                'dijkstra_bi_nos': r['dijkstra_bidirecional']['nos_explorados'],
                'dijkstra_bi_distancia': r['dijkstra_bidirecional']['distancia'],
                
                # A*
                'astar_tempo_ms': r['astar']['tempo_medio_ms'],
                'astar_nos': r['astar']['nos_explorados'],
                'astar_distancia': r['astar']['distancia'],
                
                # Speedups
                'speedup_astar_vs_uni': r['speedups']['astar_vs_dijkstra_uni'],
                'speedup_astar_vs_bi': r['speedups']['astar_vs_dijkstra_bi'],
                'speedup_bi_vs_uni': r['speedups']['dijkstra_bi_vs_uni'],
                
                # Economias
                'economia_astar_vs_uni': r['economia_nos_pct']['astar_vs_dijkstra_uni'],
                'economia_astar_vs_bi': r['economia_nos_pct']['astar_vs_dijkstra_bi'],
                'economia_bi_vs_uni': r['economia_nos_pct']['dijkstra_bi_vs_uni']
            })
        
        return pd.DataFrame(registros)
    
    def plot_speedup_comparativo(self):
        """Gráfico de speedup mostrando todas as comparações"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
        
        # Speedups médios por perfil
        speedups = self.df.groupby('perfil')[['speedup_astar_vs_uni', 'speedup_astar_vs_bi', 'speedup_bi_vs_uni']].mean()
        speedups = speedups.sort_values('speedup_astar_vs_uni', ascending=True)
        
        # Gráfico 1: A* vs Dijkstras
        y_pos = np.arange(len(speedups))
        width = 0.35
        
        ax1.barh(y_pos - width/2, speedups['speedup_astar_vs_uni'], width, 
                label='A* vs Dijkstra Uni', color='#2ECC71', alpha=0.8)
        ax1.barh(y_pos + width/2, speedups['speedup_astar_vs_bi'], width, 
                label='A* vs Dijkstra Bi', color='#27AE60', alpha=0.8)
        
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(speedups.index)
        ax1.set_xlabel('Speedup (x)', fontweight='bold')
        ax1.set_title('Speedup do A* sobre Dijkstra', fontsize=14, fontweight='bold')
        ax1.axvline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax1.legend()
        ax1.grid(axis='x', alpha=0.3)
        
        # Adiciona valores
        for i, (v1, v2) in enumerate(zip(speedups['speedup_astar_vs_uni'], speedups['speedup_astar_vs_bi'])):
            ax1.text(v1 + 0.05, i - width/2, f'{v1:.2f}x', va='center', fontsize=9)
            ax1.text(v2 + 0.05, i + width/2, f'{v2:.2f}x', va='center', fontsize=9)
        
        # Gráfico 2: Dijkstra Bi vs Uni
        speedups_bi = speedups['speedup_bi_vs_uni'].sort_values(ascending=True)
        y_pos2 = np.arange(len(speedups_bi))
        
        ax2.barh(y_pos2, speedups_bi, color='#3498DB', alpha=0.8)
        ax2.set_yticks(y_pos2)
        ax2.set_yticklabels(speedups_bi.index)
        ax2.set_xlabel('Speedup (x)', fontweight='bold')
        ax2.set_title('Speedup: Dijkstra Bidirecional vs Unidirecional', fontsize=14, fontweight='bold')
        ax2.axvline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax2.grid(axis='x', alpha=0.3)
        
        # Adiciona valores
        for i, v in enumerate(speedups_bi):
            ax2.text(v + 0.02, i, f'{v:.2f}x', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'speedup_comparativo_tres.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: speedup_comparativo_tres.png")
        plt.close()
    
    def plot_tempos_absolutos(self):
        """Gráfico de barras agrupadas com tempos absolutos"""
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # Tempos médios por perfil
        tempos = self.df.groupby('perfil')[['dijkstra_uni_tempo_ms', 'dijkstra_bi_tempo_ms', 'astar_tempo_ms']].mean()
        tempos = tempos.sort_values('dijkstra_uni_tempo_ms', ascending=False)
        
        x = np.arange(len(tempos))
        width = 0.25
        
        ax.bar(x - width, tempos['dijkstra_uni_tempo_ms'], width, 
              label='Dijkstra Unidirecional', color='#E74C3C', alpha=0.8)
        ax.bar(x, tempos['dijkstra_bi_tempo_ms'], width, 
              label='Dijkstra Bidirecional', color='#3498DB', alpha=0.8)
        ax.bar(x + width, tempos['astar_tempo_ms'], width, 
              label='A*', color='#2ECC71', alpha=0.8)
        
        ax.set_xlabel('Perfil de Mobilidade', fontweight='bold')
        ax.set_ylabel('Tempo Médio (ms)', fontweight='bold')
        ax.set_title('Comparação de Tempo de Execução por Perfil', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tempos.index, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'tempos_absolutos.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: tempos_absolutos.png")
        plt.close()
    
    def plot_nos_explorados(self):
        """Comparação de nós explorados"""
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # Nós médios por perfil
        nos = self.df.groupby('perfil')[['dijkstra_uni_nos', 'dijkstra_bi_nos', 'astar_nos']].mean()
        nos = nos.sort_values('dijkstra_uni_nos', ascending=False)
        
        x = np.arange(len(nos))
        width = 0.25
        
        ax.bar(x - width, nos['dijkstra_uni_nos'], width, 
              label='Dijkstra Unidirecional', color='#E74C3C', alpha=0.8)
        ax.bar(x, nos['dijkstra_bi_nos'], width, 
              label='Dijkstra Bidirecional', color='#3498DB', alpha=0.8)
        ax.bar(x + width, nos['astar_nos'], width, 
              label='A*', color='#2ECC71', alpha=0.8)
        
        ax.set_xlabel('Perfil de Mobilidade', fontweight='bold')
        ax.set_ylabel('Média de Nós Explorados', fontweight='bold')
        ax.set_title('Comparação de Nós Explorados por Perfil', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(nos.index, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'nos_explorados.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: nos_explorados.png")
        plt.close()
    
    def plot_boxplot_tempos(self):
        """Boxplots de distribuição de tempos"""
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        
        # Prepara dados para boxplot
        perfis = sorted(self.df['perfil'].unique())
        
        for idx, (col, titulo, ax) in enumerate(zip(
            ['dijkstra_uni_tempo_ms', 'dijkstra_bi_tempo_ms', 'astar_tempo_ms'],
            ['Dijkstra Unidirecional', 'Dijkstra Bidirecional', 'A*'],
            axes
        )):
            data_por_perfil = [self.df[self.df['perfil'] == p][col].values for p in perfis]
            
            bp = ax.boxplot(data_por_perfil, labels=perfis, patch_artist=True)
            
            # Cores
            cores = ['#E74C3C', '#3498DB', '#2ECC71']
            for patch in bp['boxes']:
                patch.set_facecolor(cores[idx])
                patch.set_alpha(0.7)
            
            ax.set_ylabel('Tempo (ms)', fontweight='bold')
            ax.set_title(titulo, fontsize=12, fontweight='bold')
            ax.set_xticklabels(perfis, rotation=45, ha='right')
            ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'boxplot_tempos.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: boxplot_tempos.png")
        plt.close()
    
    def plot_speedup_por_categoria(self):
        """Speedup separado por categoria de distância"""
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        
        categorias = ['curta', 'média', 'longa']
        
        for i, cat in enumerate(categorias):
            df_cat = self.df[self.df['categoria'] == cat]
            
            speedups = df_cat.groupby('perfil')[['speedup_astar_vs_uni', 'speedup_astar_vs_bi', 'speedup_bi_vs_uni']].mean()
            speedups = speedups.sort_values('speedup_astar_vs_uni', ascending=True)
            
            y_pos = np.arange(len(speedups))
            width = 0.25
            
            axes[i].barh(y_pos - width, speedups['speedup_astar_vs_uni'], width,
                        label='A* vs Dij-Uni', color='#2ECC71', alpha=0.8)
            axes[i].barh(y_pos, speedups['speedup_astar_vs_bi'], width,
                        label='A* vs Dij-Bi', color='#27AE60', alpha=0.8)
            axes[i].barh(y_pos + width, speedups['speedup_bi_vs_uni'], width,
                        label='Dij-Bi vs Dij-Uni', color='#3498DB', alpha=0.8)
            
            axes[i].set_yticks(y_pos)
            axes[i].set_yticklabels(speedups.index)
            axes[i].set_xlabel('Speedup (x)')
            axes[i].set_title(f'Categoria: {cat.capitalize()}', fontweight='bold')
            axes[i].axvline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[i].legend(fontsize=9)
            axes[i].grid(axis='x', alpha=0.3)
        
        plt.suptitle('Speedup por Categoria de Distância', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'speedup_por_categoria.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: speedup_por_categoria.png")
        plt.close()
    
    def plot_economia_nos(self):
        """Gráfico de economia de nós"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        economia = self.df.groupby('perfil')[['economia_astar_vs_uni', 'economia_astar_vs_bi', 'economia_bi_vs_uni']].mean()
        economia = economia.sort_values('economia_astar_vs_uni', ascending=True)
        
        y_pos = np.arange(len(economia))
        width = 0.25
        
        ax.barh(y_pos - width, economia['economia_astar_vs_uni'], width,
               label='A* vs Dijkstra Uni', color='#2ECC71', alpha=0.8)
        ax.barh(y_pos, economia['economia_astar_vs_bi'], width,
               label='A* vs Dijkstra Bi', color='#27AE60', alpha=0.8)
        ax.barh(y_pos + width, economia['economia_bi_vs_uni'], width,
               label='Dijkstra Bi vs Uni', color='#3498DB', alpha=0.8)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(economia.index)
        ax.set_xlabel('Economia de Nós (%)', fontweight='bold')
        ax.set_title('Economia de Nós Explorados - Comparação', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='x', alpha=0.3)
        
        # Adiciona valores
        for i, (v1, v2, v3) in enumerate(zip(economia['economia_astar_vs_uni'], 
                                              economia['economia_astar_vs_bi'],
                                              economia['economia_bi_vs_uni'])):
            ax.text(v1 + 1, i - width, f'{v1:.1f}%', va='center', fontsize=8)
            ax.text(v2 + 1, i, f'{v2:.1f}%', va='center', fontsize=8)
            ax.text(v3 + 1, i + width, f'{v3:.1f}%', va='center', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'economia_nos.png', dpi=300, bbox_inches='tight')
        print(f"✅ Gráfico salvo: economia_nos.png")
        plt.close()
    
    def gerar_tabela_resumo(self):
        """Gera tabela resumo em markdown"""
        caminho = self.output_dir / 'resumo_tres_algoritmos.md'
        
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("# Resumo do Benchmark: Dijkstra Uni vs Dijkstra Bi vs A*\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total de testes: {len(self.df)}\n")
            f.write(f"Perfis testados: {self.df['perfil'].nunique()}\n\n")
            
            # Tabela por perfil
            f.write("## Estatísticas por Perfil\n\n")
            
            resumo = self.df.groupby('perfil').agg({
                'dijkstra_uni_tempo_ms': ['mean', 'std'],
                'dijkstra_bi_tempo_ms': ['mean', 'std'],
                'astar_tempo_ms': ['mean', 'std'],
                'speedup_astar_vs_uni': ['mean', 'median', 'min', 'max'],
                'speedup_astar_vs_bi': ['mean', 'median', 'min', 'max'],
                'speedup_bi_vs_uni': ['mean', 'median', 'min', 'max']
            }).round(2)
            
            f.write(resumo.to_markdown())
            f.write("\n\n")
            
            # Insights
            f.write("## Insights Principais\n\n")
            
            # Melhor speedup A* vs Uni
            melhor_astar_uni = self.df.groupby('perfil')['speedup_astar_vs_uni'].mean().idxmax()
            valor_astar_uni = self.df.groupby('perfil')['speedup_astar_vs_uni'].mean().max()
            f.write(f"- **Melhor speedup A* vs Dijkstra Uni**: {melhor_astar_uni} ({valor_astar_uni:.2f}x)\n")
            
            # Melhor speedup A* vs Bi
            melhor_astar_bi = self.df.groupby('perfil')['speedup_astar_vs_bi'].mean().idxmax()
            valor_astar_bi = self.df.groupby('perfil')['speedup_astar_vs_bi'].mean().max()
            f.write(f"- **Melhor speedup A* vs Dijkstra Bi**: {melhor_astar_bi} ({valor_astar_bi:.2f}x)\n")
            
            # Speedup Bi vs Uni
            speedup_bi_uni_medio = self.df['speedup_bi_vs_uni'].mean()
            f.write(f"- **Speedup médio Dijkstra Bi vs Uni**: {speedup_bi_uni_medio:.2f}x\n")
            
            # Economia de nós
            economia_astar_uni = self.df['economia_astar_vs_uni'].mean()
            economia_astar_bi = self.df['economia_astar_vs_bi'].mean()
            economia_bi_uni = self.df['economia_bi_vs_uni'].mean()
            
            f.write(f"\n## Economia Média de Nós\n\n")
            f.write(f"- **A* vs Dijkstra Uni**: {economia_astar_uni:.2f}%\n")
            f.write(f"- **A* vs Dijkstra Bi**: {economia_astar_bi:.2f}%\n")
            f.write(f"- **Dijkstra Bi vs Uni**: {economia_bi_uni:.2f}%\n")
            
            f.write("\n## Análise por Categoria\n\n")
            for cat in ['curta', 'média', 'longa']:
                df_cat = self.df[self.df['categoria'] == cat]
                speedup_astar_uni = df_cat['speedup_astar_vs_uni'].mean()
                speedup_astar_bi = df_cat['speedup_astar_vs_bi'].mean()
                speedup_bi_uni = df_cat['speedup_bi_vs_uni'].mean()
                
                f.write(f"### {cat.capitalize()}\n")
                f.write(f"- A* vs Dijkstra Uni: {speedup_astar_uni:.2f}x\n")
                f.write(f"- A* vs Dijkstra Bi: {speedup_astar_bi:.2f}x\n")
                f.write(f"- Dijkstra Bi vs Uni: {speedup_bi_uni:.2f}x\n\n")
        
        print(f"✅ Resumo salvo: resumo_tres_algoritmos.md")
    
    def gerar_todos_graficos(self):
        """Gera todos os gráficos de uma vez"""
        print("\n📊 Gerando visualizações para três algoritmos...")
        print("-" * 60)
        
        self.plot_speedup_comparativo()
        self.plot_tempos_absolutos()
        self.plot_nos_explorados()
        self.plot_boxplot_tempos()
        self.plot_speedup_por_categoria()
        self.plot_economia_nos()
        self.gerar_tabela_resumo()
        
        print("-" * 60)
        print(f"✅ Todos os gráficos foram salvos em: {self.output_dir}")


# -------------------------------------------------------------
# Execução
# -------------------------------------------------------------

def main():
    import sys
    from glob import glob
    
    # Procura o arquivo JSON mais recente
    arquivos = sorted(glob("benchmark_results/tres_algoritmos/benchmark_tres_algoritmos_*.json"))
    
    if not arquivos:
        print("❌ Nenhum arquivo de benchmark encontrado!")
        print("Execute primeiro: python benchmark_tres_algoritmos.py")
        return
    
    arquivo = arquivos[-1] if len(sys.argv) < 2 else sys.argv[1]
    
    print(f"📂 Carregando: {arquivo}")
    
    viz = VisualizadorTresAlgoritmos(arquivo)
    viz.gerar_todos_graficos()


if __name__ == "__main__":
    main()