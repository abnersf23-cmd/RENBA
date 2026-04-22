import random

class Personality:
    """
    Representa o estado interno do RENBA.
    Quatro variáveis entre 0.0 e 1.0 que influenciam
    comportamento e forma visual ao longo do tempo.
    """

    def __init__(self):
        # Valores iniciais aleatórios
        self.impulso     = random.uniform(0.3, 0.9)  # controla velocidade e movimento
        self.estabilidade = random.uniform(0.3, 0.9)  # suaviza mudanças bruscas
        self.variacao    = random.uniform(0.1, 0.7)  # introduz aleatoriedade
        self.ritmo       = random.uniform(0.2, 0.8)  # controla pulsação visual

    def update(self, dt):
        """
        Aplica pequenas variações contínuas às variáveis internas.
        A estabilidade controla o quanto cada variável pode mudar.
        A variacao amplifica a aleatoriedade das mudanças.
        """
        # Fator de mudança: quanto menor a estabilidade, maior a oscilação possível
        fator = (1.0 - self.estabilidade) * self.variacao * dt

        self.impulso      = self._variar(self.impulso,      fator * 0.8)
        self.estabilidade = self._variar(self.estabilidade, fator * 0.3)  # muda devagar
        self.variacao     = self._variar(self.variacao,     fator * 0.6)
        self.ritmo        = self._variar(self.ritmo,        fator * 0.5)

    def aplicar_percepcao(self, perception):
        """
        Recebe os dados de percepção e aplica influência suave
        nas variáveis internas. — v0.2

        A percepção NÃO controla comportamento diretamente.
        Ela apenas "empurra" levemente o estado interno,
        e o comportamento continua emergindo desse estado.

        Regras de influência:
            proximidade alta → variacao sobe levemente
            proximidade alta → estabilidade cai levemente
            (o RENBA "sente" tensão ao se aproximar das bordas)
        """
        p = perception.proximidade_geral

        # Intensidade do efeito: pequena e gradual
        efeito = p * 0.004 * (1.0 - self.estabilidade) # mais efeito se estiver menos estável

        # Proximidade aumenta a variação (comportamento mais errático)
        self.variacao     = min(1.0, self.variacao     + efeito)

        # Proximidade reduz estabilidade (o RENBA fica "inquieto")
        self.estabilidade = max(0.0, self.estabilidade - efeito * 0.5)

    def _variar(self, valor, amplitude):
        """Aplica uma variação aleatória dentro da amplitude e mantém no intervalo [0, 1]."""
        delta = random.uniform(-amplitude, amplitude)
        return max(0.0, min(1.0, valor + delta))

    def __repr__(self):
        return (
            f"Personality("
            f"impulso={self.impulso:.2f}, "
            f"estabilidade={self.estabilidade:.2f}, "
            f"variacao={self.variacao:.2f}, "
            f"ritmo={self.ritmo:.2f})"
        )
