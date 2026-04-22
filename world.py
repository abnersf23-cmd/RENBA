import pygame

class World:
    """
    Gerencia a janela, o fundo e a interface de exibição.
    v0.6: captura mouse, exibe diário e indicador de interação.
    """

    LARGURA   = 1280
    ALTURA    = 720
    FPS       = 60
    COR_FUNDO = (8, 10, 20)

    def __init__(self):
        pygame.init()
        self.surface = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("RENBA v0.6")
        self.clock   = pygame.time.Clock()
        self.rodando = True

        self.fonte      = pygame.font.SysFont("monospace", 13)
        self.fonte_diario = pygame.font.SysFont("monospace", 12)

        # Estado do mouse — atualizado a cada frame
        self.mouse_pos   = (0, 0)
        self.clique_esq  = False
        self.clique_dir  = False

        # Últimas entradas do diário para exibir na tela
        self._cache_diario    = []
        self._timer_diario    = 0.0
        self.REFRESH_DIARIO   = 15.0  # segundos entre refresh do cache

    def processar_eventos(self):
        """Verifica eventos do sistema. Retorna estado de cliques."""
        self.clique_esq = False
        self.clique_dir = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.rodando = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.rodando = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.clique_esq = True
                elif event.button == 3:
                    self.clique_dir = True

        self.mouse_pos = pygame.mouse.get_pos()

    def limpar(self):
        self.surface.fill(self.COR_FUNDO)

    # ------------------------------------------------------------------ #
    #  HUD                                                                 #
    # ------------------------------------------------------------------ #

    def exibir_info(self, renba, fps):
        p = renba.personalidade
        linhas = [
            f"FPS: {fps:.0f}",
            f"impulso:      {p.impulso:.2f}",
            f"estabilidade: {p.estabilidade:.2f}",
            f"variacao:     {p.variacao:.2f}",
            f"ritmo:        {p.ritmo:.2f}",
        ]
        cor_texto = (100, 140, 180)
        for i, linha in enumerate(linhas):
            texto = self.fonte.render(linha, True, cor_texto)
            self.surface.blit(texto, (12, 12 + i * 18))

    def exibir_percepcao(self, renba):
        pc = renba.percepcao
        dados = [
            ("esq",  pc.borda_esquerda),
            ("dir",  pc.borda_direita),
            ("topo", pc.borda_topo),
            ("base", pc.borda_base),
            ("geral",pc.proximidade_geral),
        ]
        cor_label    = (80, 110, 150)
        cor_barra_vazia = (25, 35, 55)
        largura_barra = 80
        altura_barra  = 6
        x0 = 12
        y0 = self.ALTURA - (len(dados) * 22) - 12

        titulo = self.fonte.render("[ percepção ]", True, (60, 90, 130))
        self.surface.blit(titulo, (x0, y0 - 18))

        for i, (nome, valor) in enumerate(dados):
            y = y0 + i * 22
            label = self.fonte.render(f"{nome:<5}", True, cor_label)
            self.surface.blit(label, (x0, y))
            bx = x0 + 42
            pygame.draw.rect(self.surface, cor_barra_vazia,
                             (bx, y + 3, largura_barra, altura_barra), border_radius=2)
            fill = int(valor * largura_barra)
            if fill > 0:
                intensidade = valor
                cor_fill = (
                    int(60  + intensidade * 180),
                    int(140 - intensidade * 100),
                    int(200 - intensidade * 150),
                )
                pygame.draw.rect(self.surface, cor_fill,
                                 (bx, y + 3, fill, altura_barra), border_radius=2)
            num = self.fonte.render(f"{valor:.2f}", True, cor_label)
            self.surface.blit(num, (bx + largura_barra + 6, y))

    def exibir_comportamento(self, renba):
        e   = renba.estado
        t   = renba.tempo
        d   = renba.decisao
        mem = renba.memoria

        x0 = self.LARGURA - 210

        titulo = self.fonte.render("[ comportamento ]", True, (60, 100, 80))
        self.surface.blit(titulo, (x0, 12))

        barra_vida = 120
        prog_fill  = int(t.progresso * barra_vida)
        pygame.draw.rect(self.surface, (20, 35, 25), (x0, 32, barra_vida, 6), border_radius=2)
        if prog_fill > 0:
            pygame.draw.rect(self.surface, (60, 180, 100), (x0, 32, prog_fill, 6), border_radius=2)
        fase_txt = self.fonte.render(f"fase: {t.fase}  {t.idade_formatada}", True, (70, 130, 90))
        self.surface.blit(fase_txt, (x0, 42))

        acao_cor = {
            "explorar":  (100, 180, 255),
            "descansar": (100, 200, 140),
            "expandir":  (220, 160, 80),
            "retrair":   (180, 100, 200),
            "observar":  (140, 140, 160),
        }
        cor_acao  = acao_cor.get(d.acao_atual, (150, 150, 150))
        acao_label = self.fonte.render(f"ação: {d.acao_atual}", True, cor_acao)
        self.surface.blit(acao_label, (x0, 60))

        dom = mem.acao_dominante()
        dom_label = self.fonte.render(f"padrão: {dom}", True, (80, 110, 90))
        self.surface.blit(dom_label, (x0, 76))

        cor_label = (70, 110, 80)
        cor_vazia = (20, 32, 22)
        drives = [
            ("energia", e.energia,      (80, 200, 120)),
            ("curiosid", e.curiosidade, (80, 160, 220)),
            ("estabil",  e.estabilidade,(160, 120, 220)),
            ("isolam",   e.isolamento,  (180, 140, 80)),
        ]
        bw = 80
        bh = 5
        y0 = 96
        for i, (nome, valor, cor_fill) in enumerate(drives):
            y = y0 + i * 19
            lbl = self.fonte.render(f"{nome:<8}", True, cor_label)
            self.surface.blit(lbl, (x0, y))
            bx = x0 + 70
            pygame.draw.rect(self.surface, cor_vazia, (bx, y + 2, bw, bh), border_radius=2)
            fill = int(valor * bw)
            if fill > 0:
                pygame.draw.rect(self.surface, cor_fill, (bx, y + 2, fill, bh), border_radius=2)
            num = self.fonte.render(f"{valor:.2f}", True, cor_label)
            self.surface.blit(num, (bx + bw + 5, y))

        y_tend = y0 + len(drives) * 19 + 6
        tend_titulo = self.fonte.render("probabilidades:", True, (60, 90, 70))
        self.surface.blit(tend_titulo, (x0, y_tend))
        probs = d.probabilidades
        for j, acao in enumerate(["explorar", "descansar", "expandir", "retrair", "observar"]):
            prob  = probs.get(acao, 0.0)
            y     = y_tend + 16 + j * 16
            bx    = x0 + 70
            bw2   = 60
            fill2 = int(prob * bw2)
            pygame.draw.rect(self.surface, cor_vazia, (bx, y + 2, bw2, 4), border_radius=1)
            if fill2 > 0:
                cor_t = acao_cor.get(acao, (120, 120, 120))
                pygame.draw.rect(self.surface, cor_t, (bx, y + 2, fill2, 4), border_radius=1)
            lbl2 = self.fonte.render(f"{acao[:7]:<7}", True, (60, 90, 70))
            self.surface.blit(lbl2, (x0, y))
            num2 = self.fonte.render(f"{prob:.0%}", True, (70, 110, 80))
            self.surface.blit(num2, (bx + bw2 + 4, y))

    def exibir_psicologia(self, renba):
        c   = renba.circadian
        m   = renba.humor
        x0  = self.LARGURA - 210
        y0  = self.ALTURA  - 185

        cor_titulo = (80, 60, 120)
        cor_label  = (100, 80, 150)
        cor_vazia  = (22, 18, 35)

        titulo = self.fonte.render("[ psicologia ]", True, cor_titulo)
        self.surface.blit(titulo, (x0, y0))

        fase_cor = {
            "madrugada": (80, 80, 140),
            "manha":     (200, 180, 80),
            "tarde":     (220, 140, 60),
            "noite":     (100, 80, 160),
        }
        cor_fase = fase_cor.get(c.fase_dia, (140, 140, 160))
        linha = self.fonte.render(
            f"{c.hora_formatada}  {c.fase_dia}  ativ:{c.fator_atividade:.2f}",
            True, cor_fase
        )
        self.surface.blit(linha, (x0, y0 + 16))

        humor_cor = {
            "abatido":  (200, 80, 80),
            "baixo":    (200, 130, 80),
            "neutro":   (140, 140, 160),
            "estável":  (100, 160, 200),
            "bem":      (80, 200, 140),
            "ótimo":    (120, 220, 100),
        }
        cor_humor = humor_cor.get(m.descricao, (140, 140, 160))
        humor_lbl = self.fonte.render(
            f"humor: {m.descricao}  ({m.humor_total:.2f})",
            True, cor_humor
        )
        self.surface.blit(humor_lbl, (x0, y0 + 32))

        bw = 80
        bh = 5
        camadas = [
            ("base",  m.humor_base,    (120, 100, 200)),
            ("imed",  m.humor_imediato,(160, 130, 230)),
            ("total", m.humor_total,   cor_humor),
        ]
        for i, (nome, valor, cor_b) in enumerate(camadas):
            y = y0 + 50 + i * 18
            lbl = self.fonte.render(f"{nome:<6}", True, cor_label)
            self.surface.blit(lbl, (x0, y))
            bx = x0 + 50
            pygame.draw.rect(self.surface, cor_vazia, (bx, y + 2, bw, bh), border_radius=2)
            fill = int(valor * bw)
            if fill > 0:
                pygame.draw.rect(self.surface, cor_b, (bx, y + 2, fill, bh), border_radius=2)
            num = self.fonte.render(f"{valor:.2f}", True, cor_label)
            self.surface.blit(num, (bx + bw + 5, y))

        y_inf = y0 + 110
        inf_titulo = self.fonte.render("circadiano:", True, cor_titulo)
        self.surface.blit(inf_titulo, (x0, y_inf))
        influencias = [
            ("energia", c.influencia_energia),
            ("curiosid", c.influencia_curiosidade),
            ("estabil",  c.influencia_estabilidade),
            ("descanso", c.influencia_descanso),
        ]
        for i, (nome, val) in enumerate(influencias):
            y   = y_inf + 16 + i * 15
            lbl = self.fonte.render(f"{nome:<8}", True, cor_label)
            self.surface.blit(lbl, (x0, y))
            bx  = x0 + 68
            bw2 = 60
            centro = bx + bw2 // 2
            pygame.draw.rect(self.surface, cor_vazia, (bx, y + 2, bw2, 4), border_radius=1)
            pygame.draw.line(self.surface, cor_label, (centro, y), (centro, y + 8))
            if abs(val) > 0.001:
                fill_w  = int(abs(val) * bw2 // 2)
                cor_dir = (80, 180, 120) if val > 0 else (200, 100, 80)
                if val > 0:
                    pygame.draw.rect(self.surface, cor_dir, (centro, y + 2, fill_w, 4))
                else:
                    pygame.draw.rect(self.surface, cor_dir, (centro - fill_w, y + 2, fill_w, 4))
            num = self.fonte.render(f"{val:+.2f}", True, cor_label)
            self.surface.blit(num, (bx + bw2 + 4, y))

    # ------------------------------------------------------------------ #
    #  v0.6 — Interação e Diário                                          #
    # ------------------------------------------------------------------ #

    def exibir_interacao(self, renba):
        """
        Exibe indicador de presença do cursor e dica de interação.
        Aparece só quando o cursor está na zona de percepção.
        """
        inter = renba.interacao
        if inter.presenca < 0.05:
            return

        # Círculo de presença ao redor do RENBA (raio visual)
        raio_vis = int(inter.RAIO_PERCEPCAO * inter.presenca * 0.5 + 30)
        alpha    = int(inter.presenca * 60)
        surf = pygame.Surface((raio_vis * 2, raio_vis * 2), pygame.SRCALPHA)

        # Cor do círculo baseada no último toque
        if inter.ultimo_toque == "positivo" and inter.tempo_ultimo_toque < 2.0:
            cor_halo = (100, 220, 150, alpha)
        elif inter.ultimo_toque == "negativo" and inter.tempo_ultimo_toque < 2.0:
            cor_halo = (220, 100, 100, alpha)
        else:
            cor_halo = (180, 160, 255, alpha)

        pygame.draw.circle(surf, cor_halo, (raio_vis, raio_vis), raio_vis, 2)
        rx = int(renba.x) - raio_vis
        ry = int(renba.y) - raio_vis
        self.surface.blit(surf, (rx, ry))

        # Dica de interação (só se nunca tocou ainda)
        cor_dica = (120, 100, 180)
        desc = inter.descricao_presenca
        lbl  = self.fonte.render(
            f"[clique] carinho  [dir] susto  — {desc}",
            True, cor_dica
        )
        self.surface.blit(lbl, (self.LARGURA // 2 - lbl.get_width() // 2,
                                self.ALTURA - 30))

    def exibir_diario(self, renba, dt):
        """
        Exibe as últimas 4 entradas do diário no centro inferior da tela.
        Atualiza o cache a cada REFRESH_DIARIO segundos.
        """
        self._timer_diario += dt
        if self._timer_diario >= self.REFRESH_DIARIO or not self._cache_diario:
            self._cache_diario = renba.diario.ler_recentes(4)
            self._timer_diario = 0.0

        if not self._cache_diario:
            return

        x0 = 160
        y0 = self.ALTURA - 120
        cor_titulo = (60, 50, 100)
        cor_texto  = (90, 75, 140)

        titulo = self.fonte_diario.render("[ diário ]", True, cor_titulo)
        self.surface.blit(titulo, (x0, y0))

        for i, (ts, frase) in enumerate(reversed(self._cache_diario)):
            # Opacidade decrescente para entradas mais antigas
            alpha_idx = len(self._cache_diario) - 1 - i
            brilho    = 140 - alpha_idx * 25
            cor       = (brilho - 20, brilho - 30, brilho + 20)
            txt = self.fonte_diario.render(f"  {frase}", True, cor)
            self.surface.blit(txt, (x0, y0 + 16 + i * 16))

    # ------------------------------------------------------------------ #

    def atualizar(self):
        pygame.display.flip()
        return self.clock.tick(self.FPS) / 1000.0

    def encerrar(self):
        pygame.quit()
