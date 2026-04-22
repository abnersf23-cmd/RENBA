from collections import deque

class Memory:
    """
    Sistema de memória do RENBA — v0.3.1

    MELHORIA 4 — Decaimento da memória:
        A frequência de cada ação decai com o tempo.
        Ações antigas perdem peso gradualmente.
        Evita crescimento infinito e dá mais significado ao presente.

    MELHORIA 5 — Dominante inteligente:
        Em vez de só contar quem apareceu mais vezes no total,
        a dominante considera:
            - recência: ações recentes valem mais
            - peso emocional: ações em momentos de alta energia valem mais
        Isso revela o padrão real atual, não o histórico bruto.

    Preparado para:
        - persistência em SQLite
        - análise comportamental por fase de vida
    """

    CAPACIDADE_CURTA = 20   # janela de memória recente
    FATOR_DECAIMENTO = 0.98  # multiplicador por ciclo de decisão (não por frame)

    def __init__(self):
        # Memória curta: registros recentes com timestamp relativo
        self.curta: deque = deque(maxlen=self.CAPACIDADE_CURTA)

        # --- MELHORIA 4: frequência com decaimento --- #
        # Em vez de inteiros puros, usamos floats que decaem
        self.frequencia: dict[str, float] = {}

        # Ciclo interno de decaimento (aplicado a cada N registros)
        self._ciclos_desde_decaimento: int = 0
        self._decaimento_a_cada: int       = 5  # decai a cada 5 ações

        self._ultima_acao: str = ""

    def registrar(self, acao: str, estado_snapshot: dict):
        """
        Registra uma ação com o estado emocional no momento.
        O peso emocional é calculado a partir da energia e estabilidade.
        """
        # Peso emocional: energia alta + instabilidade = momento marcante
        energia     = estado_snapshot.get("energia", 0.5)
        estabilidade = estado_snapshot.get("estabilidade", 0.5)
        peso_emocional = 0.5 + energia * 0.3 + (1.0 - estabilidade) * 0.2

        registro = {
            "acao":           acao,
            "estado":         estado_snapshot,
            "peso_emocional": round(peso_emocional, 3),
            "indice":         len(self.curta),  # posição relativa (recência)
        }
        self.curta.append(registro)

        # Frequência com decaimento: soma o peso emocional, não +1 fixo
        self.frequencia[acao] = self.frequencia.get(acao, 0.0) + peso_emocional

        self._ultima_acao = acao

        # Aplica decaimento periódico
        self._ciclos_desde_decaimento += 1
        if self._ciclos_desde_decaimento >= self._decaimento_a_cada:
            self._aplicar_decaimento()
            self._ciclos_desde_decaimento = 0

    def _aplicar_decaimento(self):
        """
        Multiplica todas as frequências pelo fator de decaimento.
        Ações que não aparecem recentemente enfraquecem aos poucos.
        Remove ações cujo peso ficou insignificante.
        """
        for acao in list(self.frequencia.keys()):
            self.frequencia[acao] *= self.FATOR_DECAIMENTO
            if self.frequencia[acao] < 0.01:
                del self.frequencia[acao]

    def acao_dominante(self) -> str:
        """
        --- MELHORIA 5: dominante inteligente ---

        Calcula um score ponderado para cada ação na memória curta:
            score = peso_emocional × fator_recencia

        Fator de recência: ações mais recentes têm fator maior.
        O índice mais alto na deque = mais recente = maior peso.

        Retorna a ação com maior score ponderado.
        """
        if not self.curta:
            return "observar"

        lista    = list(self.curta)
        n        = len(lista)
        scores: dict[str, float] = {}

        for i, registro in enumerate(lista):
            acao  = registro["acao"]
            # Recência: vai de 0.1 (mais antigo) a 1.0 (mais recente)
            recencia      = 0.1 + 0.9 * (i / max(n - 1, 1))
            peso_emocional = registro.get("peso_emocional", 0.5)

            score = peso_emocional * recencia
            scores[acao] = scores.get(acao, 0.0) + score

        return max(scores, key=lambda k: scores[k])

    def repeticao_recente(self, acao: str, janela: int = 5) -> float:
        """Proporção da ação nas últimas N entradas. 0.0 → 1.0"""
        recentes = list(self.curta)[-janela:]
        if not recentes:
            return 0.0
        ocorrencias = sum(1 for r in recentes if r["acao"] == acao)
        return ocorrencias / len(recentes)

    def snapshot_estado(self, estado) -> dict:
        """Cria snapshot do estado interno para armazenar."""
        return {
            "energia":      round(estado.energia, 3),
            "curiosidade":  round(estado.curiosidade, 3),
            "estabilidade": round(estado.estabilidade, 3),
            "isolamento":   round(estado.isolamento, 3),
        }

    def __repr__(self):
        dom   = self.acao_dominante()
        total = sum(self.frequencia.values())
        freq  = {k: round(v, 1) for k, v in self.frequencia.items()}
        return f"Memory(peso_total={total:.1f}, dominante={dom}, freq={freq})"
