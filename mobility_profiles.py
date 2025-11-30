# mobility_profiles.py - PERFIS DE MOBILIDADE

from dataclasses import dataclass
from typing import Dict

@dataclass
class MobilityProfile:
    """Perfil de mobilidade do usuário"""
    nome: str
    descricao: str
    icone: str
    velocidade_caminhada: float  # metros por minuto
    tamanho_passo: float  # metros por passo
    
    # Fatores de penalização (multiplicadores de peso)
    penalizacao_sem_rampa: float  # Penaliza arestas sem rampa
    penalizacao_sem_faixa: float  # Penaliza cruzamentos sem faixa
    penalizacao_escadas: float  # Penaliza escadas
    penalizacao_inclinacao: float  # Penaliza inclinações acentuadas
    
    # Preferências
    requer_acessibilidade: bool  # Se True, evita rotas inacessíveis
    prefere_faixas: bool  # Se True, prioriza cruzamentos com faixa
    
    # Informações adicionais
    cor_rota: str  # Cor da rota no mapa
    mensagem_informativa: str  # Mensagem sobre cuidados específicos


# Definição dos perfis disponíveis
PERFIS_MOBILIDADE: Dict[str, MobilityProfile] = {
    "padrao": MobilityProfile(
        nome="Adulto Sem Dificuldades",
        descricao="Pessoa adulta com mobilidade plena",
        icone="🚶",
        velocidade_caminhada=80.0,  # ~4.8 km/h
        tamanho_passo=0.75,
        penalizacao_sem_rampa=1.0,  # Sem penalização
        penalizacao_sem_faixa=1.0,
        penalizacao_escadas=1.0,
        penalizacao_inclinacao=1.0,
        requer_acessibilidade=False,
        prefere_faixas=False,
        cor_rota="#DC143C",  # Crimson red
        mensagem_informativa=""
    ),
    
    "cadeirante": MobilityProfile(
        nome="Cadeirante",
        descricao="Pessoa em cadeira de rodas - requer acessibilidade total",
        icone="♿",
        velocidade_caminhada=50.0,  # ~3 km/h - mais lento
        tamanho_passo=0.0,  # Não aplicável
        penalizacao_sem_rampa=100.0,  # FORTE penalização
        penalizacao_sem_faixa=5.0,  # Prefere faixas
        penalizacao_escadas=1000.0,  # EVITA completamente
        penalizacao_inclinacao=3.0,  # Dificuldade em subidas
        requer_acessibilidade=True,
        prefere_faixas=True,
        cor_rota="#0066CC",  # Azul acessibilidade
        mensagem_informativa="⚠️ Rota otimizada para acessibilidade. Evita escadas e prioriza rampas."
    ),
    
    "idoso": MobilityProfile(
        nome="Idoso",
        descricao="Pessoa idosa com mobilidade reduzida",
        icone="👴",
        velocidade_caminhada=60.0,  # ~3.6 km/h
        tamanho_passo=0.60,  # Passos menores
        penalizacao_sem_rampa=3.0,  # Dificuldade com degraus
        penalizacao_sem_faixa=3.0,  # Segurança em cruzamentos
        penalizacao_escadas=8.0,  # Evita bastante
        penalizacao_inclinacao=4.0,  # Dificuldade em subidas
        requer_acessibilidade=True,
        prefere_faixas=True,
        cor_rota="#FF8C00",  # Laranja
        mensagem_informativa="⚠️ Rota otimizada para segurança. Evita escadas e inclinações acentuadas."
    ),
    
    "gravida": MobilityProfile(
        nome="Gestante",
        descricao="Mulher grávida - conforto e segurança",
        icone="🤰",
        velocidade_caminhada=65.0,  # ~3.9 km/h
        tamanho_passo=0.65,
        penalizacao_sem_rampa=2.5,
        penalizacao_sem_faixa=2.5,  # Segurança importante
        penalizacao_escadas=5.0,  # Evita bastante
        penalizacao_inclinacao=3.0,  # Evita esforço
        requer_acessibilidade=False,
        prefere_faixas=True,
        cor_rota="#FF69B4",  # Rosa
        mensagem_informativa="⚠️ Rota mais confortável. Evita escadas e esforço excessivo."
    ),
    
    "crianca": MobilityProfile(
        nome="Criança/Acompanhante",
        descricao="Criança pequena ou pessoa com carrinho de bebê",
        icone="👶",
        velocidade_caminhada=55.0,  # ~3.3 km/h
        tamanho_passo=0.50,
        penalizacao_sem_rampa=6.0,  # Carrinhos precisam de rampas
        penalizacao_sem_faixa=4.0,  # Segurança crucial
        penalizacao_escadas=10.0,  # Muito difícil com carrinho
        penalizacao_inclinacao=2.5,
        requer_acessibilidade=False,
        prefere_faixas=True,
        cor_rota="#9370DB",  # Roxo
        mensagem_informativa="⚠️ Rota adequada para carrinhos. Evita escadas e prioriza segurança."
    ),
    
    "mobilidade_temporaria": MobilityProfile(
        nome="Mobilidade Temporariamente Reduzida",
        descricao="Pessoa com lesão temporária (muletas, bota ortopédica, etc.)",
        icone="🩼",
        velocidade_caminhada=55.0,  # ~3.3 km/h
        tamanho_passo=0.55,
        penalizacao_sem_rampa=4.0,
        penalizacao_sem_faixa=2.5,
        penalizacao_escadas=12.0,  # Muito difícil
        penalizacao_inclinacao=5.0,  # Esforço adicional
        requer_acessibilidade=True,
        prefere_faixas=True,
        cor_rota="#FFD700",  # Dourado
        mensagem_informativa="⚠️ Rota adaptada para recuperação. Minimiza obstáculos e esforço."
    ),
    
    "obeso": MobilityProfile(
        nome="Pessoa com Obesidade",
        descricao="Pessoa adulta com obesidade - redução de resistência física",
        icone="🚶‍♂️",
        velocidade_caminhada=58.0,  # ~3.5 km/h - velocidade reduzida
        tamanho_passo=0.68,  # Passos ligeiramente menores
        penalizacao_sem_rampa=3.5,  # Dificuldade moderada com degraus
        penalizacao_sem_faixa=2.0,  # Preferência por segurança
        penalizacao_escadas=9.0,  # Evita bastante - alto gasto energético
        penalizacao_inclinacao=6.0,  # Forte dificuldade em subidas - fadiga rápida
        requer_acessibilidade=True,  # Beneficia-se de rotas acessíveis
        prefere_faixas=True,
        cor_rota="#FF6347",  # Tomato red
        mensagem_informativa="⚠️ Rota otimizada para conforto. Evita escadas e inclinações íngremes para reduzir fadiga."
    )
}


def obter_perfil(chave: str) -> MobilityProfile:
    """
    Obtém um perfil de mobilidade pela chave.
    
    Args:
        chave: Chave do perfil (ex: "cadeirante")
        
    Returns:
        MobilityProfile correspondente ou perfil padrão se não encontrado
    """
    return PERFIS_MOBILIDADE.get(chave, PERFIS_MOBILIDADE["padrao"])


def listar_perfis() -> Dict[str, str]:
    """
    Lista todos os perfis disponíveis.
    
    Returns:
        Dict com {chave: "ícone nome"}
    """
    return {
        chave: f"{perfil.icone} {perfil.nome}"
        for chave, perfil in PERFIS_MOBILIDADE.items()
    }


def obter_descricoes_perfis() -> Dict[str, str]:
    """
    Obtém as descrições de todos os perfis.
    
    Returns:
        Dict com {chave: descricao}
    """
    return {
        chave: perfil.descricao
        for chave, perfil in PERFIS_MOBILIDADE.items()
    }