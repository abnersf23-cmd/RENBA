import random

class InternalState:
    """
    Estado interno do RENBA — v0.3

    Representa "como o RENBA está" em um nível mais profundo
    do que a personalidade. São drives existenciais que motivam ações.

    Todos os valores: 0.0 → 1.0

    energia      → capacidade de agir (cai com atividade, sobe com descanso)
    curiosidade  → vontade de explorar (alta = busca novidade)
    estabilidade → conforto interno (baixa = inquietação)
    isolamento   → sensação de solidão/auto-absorção (futuro: social)
    """

    def __init__(self):
        self.energia      = random.uniform(0.5, 1.0)
        self.curiosidade  = random.uniform(0.3, 0.9)
        self.estabilidade = random.uniform(0.3, 0.8)
        self.isolamento   = random.uniform(0.1, 0.5)

    def update(self, dt: float, acao_atual: str, time_engine):
        """
        Atualiza os drives internos com base no tempo, ação atual e fase de vida.

        Cada ação tem consequências diferentes nos estados.
        O tempo de vida também influencia os valores base.
        """
        # Taxa de mudança base — mais lenta no final da vida
        taxa = dt * (1.0 - time_engine.progresso * 0.5)

        if acao_atual == "explorar":
            # Explorar gasta energia e satisfaz a curiosidade (saciedade)
            self.energia     -= taxa * 0.022
            self.curiosidade  = max(0.0, self.curiosidade - taxa * 0.012)

        elif acao_atual == "descansar":
            self.energia     = min(1.0, self.energia + taxa * 0.020)
            self.curiosidade = min(1.0, self.curiosidade + taxa * 0.005)

        elif acao_atual == "expandir":
            self.energia     -= taxa * 0.026
            self.curiosidade  = max(0.0, self.curiosidade - taxa * 0.008)
            self.estabilidade = max(0.0, self.estabilidade - taxa * 0.005)

        elif acao_atual == "retrair":
            self.energia      = min(1.0, self.energia + taxa * 0.006)
            self.estabilidade = min(1.0, self.estabilidade + taxa * 0.010)
            self.isolamento   = min(1.0, self.isolamento + taxa * 0.005)

        elif acao_atual == "observar":
            # Observar é neutro — não recupera energia, só contempla
            self.curiosidade = min(1.0, self.curiosidade + taxa * 0.002)

        # Deriva natural: curiosidade nasce devagar quando está baixa
        # Teto em 0.5 — mantém o RENBA com vontade moderada, não saturada
        if self.curiosidade < 0.5:
            self.curiosidade = min(0.5, self.curiosidade + taxa * 0.002)

        # Isolamento oscila levemente por natureza
        self.isolamento += random.uniform(-taxa * 0.02, taxa * 0.02)
        self.isolamento  = max(0.0, min(1.0, self.isolamento))

        # Energia sem piso — se explorar demais, realmente fica sem força
        # O único limite é o máximo (1.0)
        self.energia = max(0.0, min(1.0, self.energia))

    def aplicar_circadiano(self, circadian, dt: float):
        """
        Aplica as influências do ritmo circadiano nos drives internos.
        Suave e gradual — empurra levemente, não sobrescreve.
        v0.5
        """
        fator = dt * 0.15  # escala mínima — o circadiano é sutil

        # Energia: circadiano empurra para cima de dia, para baixo à noite
        self.energia = max(0.0, min(1.0,
            self.energia + circadian.influencia_energia * fator
        ))

        # Curiosidade: manhã a amplifica, madrugada a suprime
        self.curiosidade = max(0.0, min(1.0,
            self.curiosidade + circadian.influencia_curiosidade * fator
        ))

        # Estabilidade: noite traz mais calma, tarde mais agitação
        self.estabilidade = max(0.0, min(1.0,
            self.estabilidade + circadian.influencia_estabilidade * fator
        ))

    def __repr__(self):
        return (
            f"InternalState("
            f"energia={self.energia:.2f}, "
            f"curiosidade={self.curiosidade:.2f}, "
            f"estabilidade={self.estabilidade:.2f}, "
            f"isolamento={self.isolamento:.2f})"
        )
