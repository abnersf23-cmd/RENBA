import math

class Interaction:
    """
    Sistema de interação mouse→RENBA — v0.6

    O usuário pode interagir com o RENBA de duas formas:

    1. PROXIMIDADE (hover):
        Quando o cursor se aproxima, o RENBA "sente" a presença.
        Gera um estímulo de percepção social que afeta:
            - curiosidade sobe (quer investigar)
            - estabilidade cai levemente (surpresa/tensão)
        Efeito começa a 200px e cresce até 60px de distância.

    2. TOQUE (clique):
        Clique esquerdo → estímulo positivo (carinho)
            humor_imediato sobe, curiosidade sobe
        Clique direito  → estímulo negativo (susto)
            humor_imediato cai, estabilidade cai

    O estímulo de toque decai naturalmente em poucos segundos.
    """

    RAIO_PERCEPCAO  = 200.0   # distância máxima para sentir o cursor
    RAIO_CONTATO    = 60.0    # distância de "toque"
    DECAIMENTO_TOQUE = 0.6    # por segundo — efeito some em ~3s

    def __init__(self):
        self.distancia_cursor  = 9999.0   # distância atual do cursor
        self.presenca          = 0.0      # 0.0 (longe) → 1.0 (muito perto)
        self.estimulo_humor    = 0.0      # impulso transitório no humor
        self.estimulo_curiosidade = 0.0   # impulso transitório na curiosidade
        self.ultimo_toque      = ""       # "positivo", "negativo" ou ""
        self.tempo_ultimo_toque = 0.0     # segundos desde o último toque

    def update(self, dt, mouse_x, mouse_y, renba_x, renba_y,
               clique_esq=False, clique_dir=False):
        """
        Chamado a cada frame com a posição do cursor e eventos de clique.
        Atualiza estímulos e decai efeitos antigos.
        """
        dx = mouse_x - renba_x
        dy = mouse_y - renba_y
        self.distancia_cursor = math.sqrt(dx * dx + dy * dy)

        # Presença: 0 se longe, 1 se muito perto
        if self.distancia_cursor >= self.RAIO_PERCEPCAO:
            self.presenca = 0.0
        else:
            self.presenca = 1.0 - (self.distancia_cursor / self.RAIO_PERCEPCAO)

        # Processa cliques
        if clique_esq and self.distancia_cursor < self.RAIO_PERCEPCAO:
            self._aplicar_toque_positivo()
        elif clique_dir and self.distancia_cursor < self.RAIO_PERCEPCAO:
            self._aplicar_toque_negativo()

        # Decai os estímulos de toque ao longo do tempo
        self.estimulo_humor       *= (1.0 - self.DECAIMENTO_TOQUE * dt)
        self.estimulo_curiosidade *= (1.0 - self.DECAIMENTO_TOQUE * dt)
        self.tempo_ultimo_toque   += dt

        # Zera estímulo residual muito pequeno
        if abs(self.estimulo_humor) < 0.001:
            self.estimulo_humor = 0.0
        if abs(self.estimulo_curiosidade) < 0.001:
            self.estimulo_curiosidade = 0.0

    def _aplicar_toque_positivo(self):
        """Clique esquerdo — carinho. Humor e curiosidade sobem."""
        self.estimulo_humor       = min(1.0, self.estimulo_humor + 0.25)
        self.estimulo_curiosidade = min(1.0, self.estimulo_curiosidade + 0.15)
        self.ultimo_toque         = "positivo"
        self.tempo_ultimo_toque   = 0.0
        print("[interação] toque positivo — carinho")

    def _aplicar_toque_negativo(self):
        """Clique direito — susto. Humor cai, instabilidade sobe."""
        self.estimulo_humor       = max(-1.0, self.estimulo_humor - 0.30)
        self.estimulo_curiosidade = max(-1.0, self.estimulo_curiosidade - 0.10)
        self.ultimo_toque         = "negativo"
        self.tempo_ultimo_toque   = 0.0
        print("[interação] toque negativo — susto")

    def aplicar_em_estado(self, estado, mood):
        """
        Aplica os efeitos da interação no estado interno e no humor.
        Chamado a cada frame pela entity.

        Presença do cursor: empurra curiosidade suavemente.
        Estímulos de toque: modificam humor_imediato diretamente.
        """
        # Presença: curiosidade sobe levemente quando o cursor está perto
        if self.presenca > 0.1:
            estado.curiosidade = min(1.0,
                estado.curiosidade + self.presenca * 0.003
            )
            # Leve queda de estabilidade (surpresa/atenção)
            estado.estabilidade = max(0.0,
                estado.estabilidade - self.presenca * 0.001
            )

        # Estímulo de toque: afeta humor_imediato diretamente
        if abs(self.estimulo_humor) > 0.005:
            delta = self.estimulo_humor * 0.05
            mood.humor_imediato = max(0.0, min(1.0,
                mood.humor_imediato + delta
            ))

        # Estímulo de curiosidade
        if abs(self.estimulo_curiosidade) > 0.005:
            delta = self.estimulo_curiosidade * 0.04
            estado.curiosidade = max(0.0, min(1.0,
                estado.curiosidade + delta
            ))

    @property
    def em_contato(self) -> bool:
        """True se o cursor está dentro do raio de contato."""
        return self.distancia_cursor < self.RAIO_CONTATO

    @property
    def descricao_presenca(self) -> str:
        if self.presenca < 0.05:   return "ausente"
        if self.presenca < 0.30:   return "longe"
        if self.presenca < 0.60:   return "próximo"
        if self.em_contato:        return "contato"
        return "perto"

    def __repr__(self):
        return (
            f"Interaction("
            f"presenca={self.presenca:.2f}, "
            f"dist={self.distancia_cursor:.0f}px, "
            f"humor_stim={self.estimulo_humor:+.2f})"
        )
