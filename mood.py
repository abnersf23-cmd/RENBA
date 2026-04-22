import random
import math

class Mood:
    """
    Sistema de humor em camadas do RENBA — v0.5

    Duas camadas que interagem:

    humor_base (lento):
        Muda em horas. Representa "como o RENBA está se sentindo hoje".
        Influenciado por: histórico de energia, ciclo circadiano, fase de vida.
        É o chão emocional — o estado de fundo que persiste.

    humor_imediato (rápido):
        Muda em segundos/minutos. Reação ao que está acontecendo agora.
        Influenciado por: ação atual, energia, mudanças bruscas de estado.
        Oscila em torno do humor_base.

    humor_total:
        Combinação dos dois. É o que realmente afeta o comportamento.
        humor_total = humor_base * 0.6 + humor_imediato * 0.4

    Escala: 0.0 (muito mal) → 0.5 (neutro) → 1.0 (muito bem)

    O humor_total influencia:
        - pesos de decisão (humor baixo → retrair/descansar)
        - personalidade visual (humor afeta ritmo e variação)
        - não cria regras — é mais um drive que compete
    """

    def __init__(self):
        # Ambos começam próximos do neutro com leve variação
        self.humor_base      = random.uniform(0.35, 0.65)
        self.humor_imediato  = self.humor_base + random.uniform(-0.1, 0.1)
        self.humor_imediato  = max(0.0, min(1.0, self.humor_imediato))

        # Histórico de energia recente (para influenciar humor_base)
        self._historico_energia: list[float] = []
        self._acumulador_base: float = 0.0   # timer para atualizar humor_base

        # Velocidade de mudança do humor_base (segundos para mudar significativamente)
        self.PERIODO_BASE = 1800.0  # 30 minutos reais

    def update(self, dt: float, estado, circadian, time_engine):
        """
        Atualiza ambas as camadas de humor.
        """
        self._atualizar_imediato(dt, estado, circadian)
        self._atualizar_base(dt, estado, circadian, time_engine)

    def _atualizar_imediato(self, dt: float, estado, circadian):
        """
        Humor imediato: reage rápido ao que está acontecendo agora.

        Sobe quando:
            - energia está alta
            - circadiano está no pico de atividade
            - estabilidade interna é alta

        Cai quando:
            - energia está muito baixa
            - é tarde da noite (circadiano suprime)
            - instabilidade interna alta
        """
        alvo_imediato = (
            estado.energia      * 0.40 +
            circadian.fator_atividade * 0.30 +
            estado.estabilidade * 0.30
        )

        # Adiciona leve oscilação natural (o humor não é plano)
        oscilacao = math.sin(dt * 0.1 + self.humor_imediato * 3.0) * 0.01
        alvo_imediato = max(0.0, min(1.0, alvo_imediato + oscilacao))

        # Lerp rápido em direção ao alvo (reage em segundos)
        taxa_imediata = 0.8 * dt
        self.humor_imediato += (alvo_imediato - self.humor_imediato) * taxa_imediata
        self.humor_imediato  = max(0.0, min(1.0, self.humor_imediato))

    def _atualizar_base(self, dt: float, estado, circadian, time_engine):
        """
        Humor base: acumula lentamente ao longo do tempo.

        É influenciado pela média do estado interno nas últimas horas,
        pelo ciclo circadiano acumulado e pela fase de vida.
        """
        # Acumula energia recente para calcular média
        self._historico_energia.append(estado.energia)
        if len(self._historico_energia) > 500:
            self._historico_energia.pop(0)

        self._acumulador_base += dt

        # Só reavalia o humor_base a cada ~60 segundos
        if self._acumulador_base < 60.0:
            return
        self._acumulador_base = 0.0

        # Média de energia recente
        media_energia = (
            sum(self._historico_energia) / len(self._historico_energia)
            if self._historico_energia else 0.5
        )

        # Alvo do humor_base
        alvo_base = (
            media_energia           * 0.50 +
            circadian.fator_atividade * 0.25 +
            estado.estabilidade     * 0.25
        )

        # Fase de vida influencia: início é mais volátil, final mais estável
        # No início, humor_base oscila mais
        volatilidade = 0.3 * (1.0 - time_engine.progresso * 0.5)
        ruido = random.uniform(-volatilidade, volatilidade) * 0.05
        alvo_base = max(0.0, min(1.0, alvo_base + ruido))

        # Lerp muito lento (muda em horas, não em segundos)
        taxa_base = 60.0 / self.PERIODO_BASE  # fração do período por ciclo
        self.humor_base += (alvo_base - self.humor_base) * taxa_base
        self.humor_base  = max(0.0, min(1.0, self.humor_base))

    @property
    def humor_total(self) -> float:
        """
        Combinação ponderada das duas camadas.
        humor_base define o chão, humor_imediato oscila ao redor.
        """
        return self.humor_base * 0.6 + self.humor_imediato * 0.4

    @property
    def descricao(self) -> str:
        """Descrição textual do humor atual para debug."""
        h = self.humor_total
        if h < 0.20: return "abatido"
        if h < 0.35: return "baixo"
        if h < 0.50: return "neutro"
        if h < 0.65: return "estável"
        if h < 0.80: return "bem"
        return "ótimo"

    def __repr__(self):
        return (
            f"Mood("
            f"base={self.humor_base:.2f}, "
            f"imediato={self.humor_imediato:.2f}, "
            f"total={self.humor_total:.2f}, "
            f"estado={self.descricao})"
        )
