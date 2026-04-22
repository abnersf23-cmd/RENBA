import time

class TimeEngine:
    """
    Motor de tempo do RENBA — v0.4

    Tempo REAL: 1 segundo real = 1 segundo de vida do RENBA.
    Vida total: 30 dias reais = 2.592.000 segundos.

    O tempo_vida é acumulado entre sessões via banco de dados.
    A cada boot, carrega o tempo já vivido e continua de onde parou.

    Fases de vida baseadas em dias reais:
        início  (dia  0 →  9) : alta aleatoriedade, exploração intensa
        meio    (dia  9 → 21) : aprendizado ativo, adaptação
        final   (dia 21 → 30) : padrões consolidados, estabilidade maior
    """

    VIDA_TOTAL_SEGUNDOS = 30 * 24 * 3600  # 30 dias reais em segundos

    def __init__(self, aceleracao: float = 1.0):
        """
        Args:
            aceleracao: multiplicador para testes.
                        1.0   = tempo real (padrão — use isso em produção)
                        60    = 1 minuto real = 1 hora de vida
                        3600  = 1 hora real = 1 dia de vida (teste rápido)
        """
        self.aceleracao  = aceleracao
        self.tempo_vida  = 0.0    # segundos acumulados (carregado do banco)
        self.progresso   = 0.0    # 0.0 → 1.0
        self.idade_dias  = 0.0    # dias vividos (legível)
        self.fase        = "inicio"

    def update(self, dt: float):
        """
        Avança o tempo de vida com base no dt real e na aceleração.
        dt vem do clock do pygame (tempo real entre frames).
        """
        self.tempo_vida += dt * self.aceleracao

        self.progresso  = min(1.0, self.tempo_vida / self.VIDA_TOTAL_SEGUNDOS)
        self.idade_dias = self.tempo_vida / 86400.0  # segundos → dias

        # Fases baseadas em dias reais
        if self.idade_dias < 9.0:
            self.fase = "inicio"
        elif self.idade_dias < 21.0:
            self.fase = "meio"
        else:
            self.fase = "final"

    @property
    def idade_formatada(self) -> str:
        """Retorna a idade de forma legível: '2d 4h 13min'"""
        total_seg = int(self.tempo_vida)
        dias  = total_seg // 86400
        horas = (total_seg % 86400) // 3600
        mins  = (total_seg % 3600)  // 60
        if dias > 0:
            return f"{dias}d {horas}h {mins}min"
        elif horas > 0:
            return f"{horas}h {mins}min"
        else:
            segs = total_seg % 60
            return f"{mins}min {segs}seg"

    @property
    def fator_aleatoriedade(self) -> float:
        """
        Aleatoriedade decresce com a idade.
        Início: 0.8 (muito imprevisível), Final: ~0.2 (mais estável).
        """
        if self.fase == "inicio":
            return 0.8 - self.progresso * 0.5
        elif self.fase == "meio":
            p = (self.progresso - 0.3) / 0.4
            return 0.65 - p * 0.3
        else:
            p = (self.progresso - 0.7) / 0.3
            return 0.35 - p * 0.15

    @property
    def fator_aprendizado(self) -> float:
        """
        Capacidade de aprendizado por fase.
        Início: baixa, Meio: máxima, Final: moderada.
        """
        if self.fase == "inicio":
            return 0.2 + self.progresso * 1.0
        elif self.fase == "meio":
            return 0.8
        else:
            p = (self.progresso - 0.7) / 0.3
            return 0.8 - p * 0.4

    def __repr__(self):
        return (
            f"TimeEngine("
            f"fase={self.fase}, "
            f"idade={self.idade_formatada}, "
            f"progresso={self.progresso:.4f})"
        )

