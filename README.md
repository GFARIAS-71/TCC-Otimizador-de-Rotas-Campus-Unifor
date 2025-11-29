# 🏫 Otimizador de Rotas - Campus Unifor

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.51.0-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/NetworkX-3.6-00599C?style=for-the-badge&logo=networkx&logoColor=white" alt="NetworkX">
  <img src="https://img.shields.io/badge/OSMnx-2.0.7-74AA50?style=for-the-badge&logo=openstreetmap&logoColor=white" alt="OSMnx">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/GeoPandas-1.1.1-139C5A?style=for-the-badge" alt="GeoPandas">
  <img src="https://img.shields.io/badge/Folium-0.20.0-77B829?style=for-the-badge&logo=folium&logoColor=white" alt="Folium">
  <img src="https://img.shields.io/badge/Pandas-2.3.3-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/NumPy-2.3.5-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Algoritmo-A*-orange?style=for-the-badge" alt="A*">
  <img src="https://img.shields.io/badge/Teoria_dos_Grafos-blue?style=for-the-badge" alt="Graph Theory">
  <img src="https://img.shields.io/badge/Licença-Acadêmico-green?style=for-the-badge" alt="License">
  <a href="https://otimizador-de-rotas-campus-unifor.streamlit.app/">
    <img src="https://img.shields.io/badge/Demo-Online-ff69b4?style=for-the-badge&logo=streamlit&logoColor=white" alt="Demo">
  </a>
</p>

---

Sistema de otimização de rotas acessíveis para pessoas com mobilidade reduzida no Campus da Universidade de Fortaleza, desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://otimizador-de-rotas-campus-unifor.streamlit.app/)

## 📋 Sobre o Projeto

Este projeto aplica **Teoria dos Grafos** para resolver um problema social importante: a mobilidade de pessoas com restrições de locomoção em ambientes universitários. O sistema modela o campus como um grafo ponderado e utiliza algoritmos de caminho mínimo (A*) para gerar rotas personalizadas e acessíveis.

### Motivação

- **14,7%** da população brasileira é idosa
- **3,8%** possui deficiência física nos membros inferiores
- **22,35%** da população adulta apresenta obesidade
- Nas eleições de 2024, **36%** do eleitorado com dificuldades de locomoção não compareceu às urnas (vs. 20% da população geral)

Estes números evidenciam a **urgência de ambientes mais inclusivos** e tecnologias que promovam a acessibilidade.

## ✨ Funcionalidades

### 🎯 Seleção de Rotas
- **Clique no mapa** para definir origem e destino
- **Seleção por POIs** através da barra lateral
- **Categorização automática** (Blocos, Estacionamentos, Outros Lugares)

### 👥 Perfis de Mobilidade

| Perfil | Características | Penalizações |
|--------|----------------|--------------|
| **Adulto Sem Dificuldades** | Mobilidade plena (80 m/min) | Sem restrições |
| **Cadeirante** | Requer acessibilidade total (50 m/min) | Escadas: ∞, Rampas: incentivadas |
| **Idoso** | Mobilidade reduzida (60 m/min) | Escadas: 8x, Inclinações: 4x |
| **Gestante** | Conforto e segurança (65 m/min) | Escadas: 5x, Esforço reduzido |
| **Criança/Acompanhante** | Carrinhos de bebê (55 m/min) | Escadas: 10x, Rampas necessárias |
| **Mobilidade Temporária** | Lesões/muletas (55 m/min) | Escadas: 12x, Obstáculos: 5x |

### 📊 Informações Detalhadas
- **Distância** do percurso em metros
- **Tempo estimado** baseado no perfil
- **Contagem de passos** (quando aplicável)
- **Exportação GPX** para uso em apps de GPS
- **Visualização no mapa** com cores por perfil

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.12+**
- **NetworkX** - Manipulação de grafos
- **OSMnx** - Extração de dados do OpenStreetMap
- **GeoPandas** - Processamento de dados geoespaciais
- **Shapely** - Geometrias espaciais

### Frontend
- **Streamlit** - Interface web interativa
- **Folium** - Mapas interativos
- **Streamlit-Folium** - Integração Streamlit + Folium

### Algoritmos
- **A\*** com heurística euclidiana (principal)
- Suporte para Dijkstra

## 📐 Modelagem do Grafo

O campus é representado como um **grafo com as seguintes características**:

| Propriedade | Tipo | Justificativa |
|-------------|------|---------------|
| **Direção** | Não-direcionado | Caminhos bidirecionais |
| **Pesos** | Ponderado | Distância + acessibilidade |
| **Ciclos** | Cíclico | Múltiplas rotas interligadas |
| **Arestas** | Simples | Máximo uma conexão entre pontos |
| **Conectividade** | Conexo | Sempre existe um caminho |
| **Dinamicidade** | Dinâmico | Carregamento a partir da API do OpenStreetMap e Adapta-se ao Perfil do Usuário |

### Ponderação das Arestas

O peso de cada aresta considera:
```python
peso_final = distância_física × (
    penalização_escadas ×
    penalização_rampas ×
    penalização_inclinação ×
    penalização_superfície ×
    penalização_largura ×
    penalização_faixa_pedestre
)
```

## 🚀 Como Executar Localmente

### Pré-requisitos
```bash
Python 3.12 ou superior
pip (gerenciador de pacotes Python)
```

### Instalação

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd otimizador-rotas-unifor
```

2. **Crie um ambiente virtual** (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirement.txt
```

4. **Execute a aplicação**
```bash
streamlit run main.py
```

5. **Acesse no navegador**
```
http://localhost:8501
```

## 📁 Estrutura do Projeto
```
.
├── main.py                    # Aplicação principal
├── config.py                  # Configurações e constantes
├── data_loader.py            # Carregamento de dados (grafo + POIs)
├── graph_weighting.py        # Ponderação do grafo por perfil
├── mobility_profiles.py      # Definição dos perfis de mobilidade
├── route_calculator.py       # Algoritmos de caminho mínimo
├── ui_components.py          # Componentes da interface
├── pontos de interesse.txt   # POIs do campus
├── requirement.txt           # Dependências Python
└── README.md                 # Este arquivo
```

## 📖 Fundamentação Teórica

### Teoria dos Grafos
Desenvolvida formalmente no século XX, permite modelar e resolver problemas de redes, rotas e conexões. Este projeto utiliza:

- **Algoritmo A\***: Busca heurística que combina custo real + estimativa até o destino
- **Pesos dinâmicos**: Adaptados ao perfil do usuário em tempo real
- **Grafo geoespacial**: Extração automática via OpenStreetMap

### Marcos Legais (Brasil)

| Ano | Marco Legal |
|-----|------------|
| 1991 | Lei de Inclusão Produtiva |
| 2000 | Lei da Acessibilidade |
| 2003 | Estatuto do Idoso |
| 2004 | Regulamentação da Lei da Acessibilidade |
| 2015 | Estatuto da Pessoa com Deficiência |
| 2021 | Inclusão da mobilidade aos direitos fundamentais (PEC) |

## 🎯 Objetivos do TCC

### Objetivo Geral
Desenvolver uma solução baseada em teoria dos grafos que identifique rotas otimizadas dentro do campus da Unifor para pessoas com mobilidade reduzida.

### Objetivos Específicos
1. ✅ Identificar e mapear barreiras físicas no campus
2. ✅ Modelar o campus como grafo não-direcionado, ponderado e conexo
3. ✅ Avaliar algoritmos de caminho mínimo (Dijkstra vs A*)
4. ✅ Implementar interface com seleção de perfis
5. ⏳ Testar e validar em situações reais

## 📞 Suporte

Para reportar bugs ou sugerir melhorias:
- Abra uma issue no GitHub
- Entre em contato com o desenvolvedor (email: guifarias71@edu.unifor.br)

## 👨‍💻 Autor

**Guilherme de Farias Loureiro**

- Curso: Ciência da Computação
- Instituição: Universidade de Fortaleza (Unifor)
- Orientador: Prof. Belmondo Rodrigues Aragao Junior
- Ano: 2025

## 📄 Nota

Esta aplicação utiliza dados do OpenStreetMap. As rotas são calculadas com base nos caminhos disponíveis no OSM e podem não refletir 100% a realidade atual do campus.

## 🙏 Agradecimentos

> *"Este trabalho é dedicado às crianças adultas que, quando pequenas, sonharam em se tornar cientistas."*

Aos meus pais, pelo amor, incentivo e apoio incondicional.

---

## 📚 Referências Principais

- MELO, G. S. **Introdução à Teoria dos Grafos**. UFPB, 2014.
- NOTO, M.; SATO, H. **A method for the shortest path search by extended Dijkstra algorithm**. IEEE, 2000.
- BRASIL. **Lei Brasileira de Inclusão da Pessoa com Deficiência** (Lei nº 13.146/2015).

---

<p align="center">
  <i>"Sem dados, você é apenas mais alguém com uma opinião."</i><br>
  — W. Edwards Deming
</p>