import pygame
import math

class Body:
    """
    Representa a forma visual do RENBA.
    v0.6: cor base agora reflete o humor_total do Mood.
        humor alto   → tons quentes (dourado/âmbar)
        humor neutro → azul original
        humor baixo  → tons frios/roxos (abatido)
        Transição suave via lerp na cor atual.
    """

    def __init__(self):
        self.raio_base   = 24
        self.raio_atual  = 24.0
        self.pulso       = 0.0
        self.deformacao  = 0.0

        # Cor atual interpolada suavemente
        self.cor_atual = [140.0, 200.0, 240.0]

    def _cor_alvo(self, humor: float) -> tuple:
        """
        Retorna a cor alvo RGB baseada no humor_total (0.0 → 1.0).

        0.00 → 0.30 : roxo/índigo  (abatido)
        0.30 → 0.50 : azul frio    (baixo)
        0.50 → 0.65 : azul claro   (neutro — cor original)
        0.65 → 0.80 : turquesa     (bem)
        0.80 → 1.00 : dourado      (ótimo)
        """
        if humor < 0.30:
            t = humor / 0.30
            return (100 + t * 20, 80 + t * 60, 200 + t * 30)
        elif humor < 0.50:
            t = (humor - 0.30) / 0.20
            return (120 + t * 20, 140 + t * 60, 230 + t * 10)
        elif humor < 0.65:
            t = (humor - 0.50) / 0.15
            return (140 + t * 20, 200 + t * 20, 240 - t * 20)
        elif humor < 0.80:
            t = (humor - 0.65) / 0.15
            return (160 - t * 40, 220 + t * 20, 220 - t * 80)
        else:
            t = (humor - 0.80) / 0.20
            return (120 + t * 130, 240 - t * 60, 140 - t * 80)

    def update(self, personalidade, dt, humor=None):
        """Atualiza aparência. humor = objeto Mood (opcional)."""
        self.pulso += dt * (0.5 + personalidade.ritmo * 3.0)

        amplitude_pulso = personalidade.impulso * 6.0
        self.raio_atual = self.raio_base + math.sin(self.pulso) * amplitude_pulso
        self.deformacao = personalidade.variacao

        # Interpola cor suavemente em direção ao alvo
        alvo = self._cor_alvo(humor.humor_total) if humor is not None else (140.0, 200.0, 240.0)
        taxa = dt * 0.8
        for i in range(3):
            self.cor_atual[i] += (alvo[i] - self.cor_atual[i]) * taxa

    def draw(self, surface, x, y, personalidade):
        """Desenha o RENBA com cor que reflete o humor."""
        num_pontos = 32
        pontos = []

        for i in range(num_pontos):
            angulo = (2 * math.pi * i) / num_pontos
            amplitude_def = self.deformacao * (1.0 - personalidade.estabilidade * 0.7) * 8.0
            frequencia    = 3 + int(personalidade.variacao * 4)
            desvio        = math.sin(angulo * frequencia + self.pulso * 0.7) * amplitude_def
            r  = self.raio_atual + desvio
            px = x + math.cos(angulo) * r
            py = y + math.sin(angulo) * r
            pontos.append((px, py))

        brilho = int(personalidade.impulso * 40)
        cor = (
            min(255, int(self.cor_atual[0]) + brilho),
            min(255, int(self.cor_atual[1]) + brilho // 2),
            min(255, int(self.cor_atual[2])),
        )

        # Halo externo
        halo_r = int(self.raio_atual + 10)
        halo_surf = pygame.Surface((halo_r * 2 + 4, halo_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (*cor, 35), (halo_r + 2, halo_r + 2), halo_r)
        surface.blit(halo_surf, (x - halo_r - 2, y - halo_r - 2))

        # Corpo principal
        if len(pontos) >= 3:
            pygame.draw.polygon(surface, cor, pontos)

        # Núcleo interno
        nucleo_r = max(3, int(self.raio_atual * 0.3))
        cor_nucleo = (
            min(255, cor[0] + 60),
            min(255, cor[1] + 60),
            min(255, cor[2] + 40),
        )
        pygame.draw.circle(surface, cor_nucleo, (int(x), int(y)), nucleo_r)
