import random

# Espaço de ações disponíveis para o RENBA
ACOES = ["explorar", "descansar", "expandir", "retrair", "observar"]


class DecisionEngine:
    """
    Motor de decisão do RENBA — v0.3.1

    MELHORIA 1 — Probabilidades reais:
        Cada ação recebe um peso calculado a partir do estado interno.
        Os pesos são convertidos em probabilidades (somam 1.0).
        A escolha é uma roleta honesta — não há if fixo.

    MELHORIA 2 — Conflito interno:
        Cada drive do estado interno "puxa" para uma ação diferente.
        Eles competem entre si a cada decisão:
            curiosidade  → explorar
            emoção       → retrair
            estabilidade → observar
            cansaço      → descansar
        Um RENBA curioso E instável fica em conflito real.

    MELHORIA 5 — Tendências com decaimento:
        Os pesos aprendidos também decaem levemente com o tempo,
        evitando que uma preferência antiga domine para sempre.
    """

    PESO_MIN    = 0.05
    PESO_MAX    = 3.0
    DECAIMENTO  = 0.9995  # fator aplicado a cada decisão (muito suave)

    def __init__(self):
        # Pesos iniciais diferentes por design —
        # já nasce com leve preferência por explorar e observar
        self.tendencias: dict[str, float] = {
            "explorar":  1.2,
            "descansar": 0.8,
            "expandir":  1.0,
            "retrair":   0.9,
            "observar":  1.1,
        }

        self.acao_atual:       str   = "observar"
        self.probabilidades:   dict  = {a: 0.2 for a in ACOES}  # visível no debug
        self.tempo_na_acao:    float = 0.0
        self.duracao_acao:     float = 2.0

    def update(self, dt: float, estado, time_engine,
               circadian=None, humor=None) -> str:
        """Avança o motor. Reavalia a ação quando o tempo se esgota."""
        self.tempo_na_acao += dt

        frequencia = 1.5 + time_engine.fator_aleatoriedade * 3.0
        if self.tempo_na_acao >= (self.duracao_acao / frequencia):
            self.acao_atual    = self._escolher(estado, time_engine,
                                                circadian, humor)
            self.tempo_na_acao = 0.0
            self.duracao_acao  = random.uniform(5.0, 18.0)
            self._decair_tendencias()

        return self.acao_atual

    def _calcular_pesos(self, estado, time_engine,
                        circadian=None, humor=None) -> dict[str, float]:
        """
        Calcula o peso de cada ação baseado no conflito interno.
        v0.5: circadian e humor adicionam novos drives à competição.
        """
        cansaco = 1.0 - estado.energia
        emocao  = 1.0 - estado.estabilidade

        pesos = dict(self.tendencias)

        # Drives existentes
        fator_energia_para_explorar = max(0.0, (estado.energia - 0.2) / 0.8)
        pesos["explorar"]  *= (1.0 + estado.curiosidade * 2.0) * fator_energia_para_explorar
        pesos["descansar"] *= 1.0 + cansaco * 3.0
        pesos["retrair"]   *= 1.0 + emocao * 1.8
        pesos["observar"]  *= 1.0 + estado.estabilidade * 1.5
        pesos["expandir"]  *= 1.0 + estado.energia * 0.8 + estado.curiosidade * 0.4

        # --- v0.5: Ritmo circadiano influencia pesos --- #
        if circadian is not None:
            # Noite/madrugada: empurra descansar fortemente
            if circadian.influencia_descanso > 0:
                pesos["descansar"] *= 1.0 + circadian.influencia_descanso * 3.0
                pesos["explorar"]  *= max(0.1, 1.0 - circadian.influencia_descanso * 2.0)
                pesos["expandir"]  *= max(0.1, 1.0 - circadian.influencia_descanso * 1.5)

            # Manhã: curiosidade amplificada
            if circadian.fase_dia == "manha":
                pesos["explorar"] *= 1.0 + circadian.fator_atividade * 0.5

            # Tarde: atividade em geral amplificada
            elif circadian.fase_dia == "tarde":
                pesos["explorar"] *= 1.0 + circadian.fator_atividade * 0.4
                pesos["expandir"] *= 1.0 + circadian.fator_atividade * 0.3

            # Noite: introspeccão
            elif circadian.fase_dia == "noite":
                pesos["observar"] *= 1.3
                pesos["retrair"]  *= 1.2

        # --- v0.5: Humor influencia pesos --- #
        if humor is not None:
            h = humor.humor_total
            if h < 0.35:
                # Mal-humorado: retrair e descansar sobem
                pesos["retrair"]   *= 1.0 + (0.35 - h) * 2.0
                pesos["descansar"] *= 1.0 + (0.35 - h) * 1.5
                pesos["explorar"]  *= max(0.1, h / 0.35)
            elif h > 0.65:
                # Bem-humorado: explorar e expandir sobem
                pesos["explorar"]  *= 1.0 + (h - 0.65) * 1.5
                pesos["expandir"]  *= 1.0 + (h - 0.65) * 1.0

        # Ruído proporcional à fase de vida
        ruido = time_engine.fator_aleatoriedade
        for acao in pesos:
            fator_ruido = random.uniform(1.0 - ruido * 0.35, 1.0 + ruido * 0.35)
            pesos[acao] = max(0.001, pesos[acao] * fator_ruido)

        return pesos

    def _escolher(self, estado, time_engine,
                  circadian=None, humor=None) -> str:
        """Converte pesos em probabilidades e sorteia."""
        pesos = self._calcular_pesos(estado, time_engine, circadian, humor)
        total = sum(pesos.values())

        self.probabilidades = {a: pesos[a] / total for a in pesos}

        sorteio   = random.uniform(0, total)
        acumulado = 0.0
        for acao, peso in pesos.items():
            acumulado += peso
            if sorteio <= acumulado:
                return acao

        return ACOES[-1]

    def _decair_tendencias(self):
        """
        Aplica decaimento suave nas tendências a cada decisão.
        Impede que preferências antigas dominem para sempre.
        Puxa todos os pesos lentamente em direção ao valor neutro (1.0).
        """
        for acao in self.tendencias:
            atual   = self.tendencias[acao]
            neutro  = 1.0
            # Move o valor 0.05% em direção ao neutro
            self.tendencias[acao] = atual + (neutro - atual) * (1.0 - self.DECAIMENTO)

    def reforcar(self, acao: str, resultado: float):
        """
        Ajusta o peso de uma ação com base no resultado observado.
        resultado: +1.0 (funcionou bem) → -1.0 (não funcionou)
        """
        if acao not in self.tendencias:
            return
        ajuste = resultado * 0.05
        self.tendencias[acao] = max(
            self.PESO_MIN,
            min(self.PESO_MAX, self.tendencias[acao] + ajuste)
        )

    def __repr__(self):
        probs = ", ".join(f"{k}={v:.1%}" for k, v in self.probabilidades.items())
        return f"DecisionEngine(acao={self.acao_atual}, probs=[{probs}])"
