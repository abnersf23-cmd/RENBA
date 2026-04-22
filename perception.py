class Perception:
    """
    Sistema de percepção do RENBA — v0.2

    Detecta a proximidade da entidade em relação às bordas da tela
    e normaliza os valores entre 0.0 e 1.0.

    NÃO interfere diretamente no movimento nem no corpo visual.
    Apenas expõe dados para que a personalidade decida como reagir.

    Escala de proximidade:
        0.0 → longe da borda (dentro da zona de conforto)
        1.0 → muito próximo / encostado na borda

    Preparado para futuras expansões:
        - percepção de outras entidades
        - percepção de estímulos externos (luz, calor, etc.)
        - memória perceptual ao longo do tempo
    """

    # Distância (em pixels) a partir da qual a borda começa a ser "sentida"
    ZONA_PERCEPCAO = 180.0

    def __init__(self):
        # Proximidade individual de cada borda (0.0 = longe, 1.0 = encostado)
        self.borda_esquerda = 0.0
        self.borda_direita  = 0.0
        self.borda_topo     = 0.0
        self.borda_base     = 0.0

        # Valor agregado: média das quatro bordas
        self.proximidade_geral = 0.0

    def update(self, x, y, largura, altura):
        """
        Recalcula a percepção com base na posição atual da entidade.

        Args:
            x, y         : posição atual do RENBA
            largura, altura : dimensões da tela
        """
        zona = self.ZONA_PERCEPCAO

        # Distância bruta até cada borda
        dist_esq    = x
        dist_dir    = largura - x
        dist_topo   = y
        dist_base   = altura - y

        # Normalização: converte distância em nível de percepção
        # Quanto mais perto da borda, maior o valor (mais próximo de 1.0)
        self.borda_esquerda = self._normalizar(dist_esq,  zona)
        self.borda_direita  = self._normalizar(dist_dir,  zona)
        self.borda_topo     = self._normalizar(dist_topo, zona)
        self.borda_base     = self._normalizar(dist_base, zona)

        # Valor geral: média das quatro percepções
        self.proximidade_geral = (
            self.borda_esquerda +
            self.borda_direita  +
            self.borda_topo     +
            self.borda_base
        ) / 4.0

    def _normalizar(self, distancia, zona):
        """
        Converte distância em intensidade de percepção.
        Retorna 0.0 se fora da zona, 1.0 se na borda exata.
        """
        if distancia >= zona:
            return 0.0
        return 1.0 - (distancia / zona)

    def __repr__(self):
        return (
            f"Perception("
            f"esq={self.borda_esquerda:.2f}, "
            f"dir={self.borda_direita:.2f}, "
            f"topo={self.borda_topo:.2f}, "
            f"base={self.borda_base:.2f}, "
            f"geral={self.proximidade_geral:.2f})"
        )
