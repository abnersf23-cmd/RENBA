import math
import random
from personality import Personality
from body import Body
from perception import Perception
from time_engine import TimeEngine
from internal_state import InternalState
from decision import DecisionEngine
from memory import Memory
from database import DatabaseManager
from circadian import CircadianRhythm
from mood import Mood
from interaction import Interaction   # v0.6
from diary import Diary               # v0.6

class RENBA:
    """
    Entidade principal do organismo digital.
    v0.6: interação com mouse, cor reflete humor, diário de vida.
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.angulo     = random.uniform(0, 2 * math.pi)
        self.velocidade = 0.0

        self.corpo     = Body()
        self.percepcao = Perception()
        self.db        = DatabaseManager()

        dados = self.db.carregar() if self.db.existe_estado_salvo() else None

        # v0.6 — interação e diário (sempre inicializados)
        self.interacao = Interaction()

        if dados:
            self._carregar_de_dados(dados)
        else:
            self._inicializar_novo()

        # Diário precisa do db já configurado
        self.diario = Diary(self.db)
        self.diario.ao_acordar(self)

    def _inicializar_novo(self):
        self.personalidade = Personality()
        self.estado        = InternalState()
        self.decisao       = DecisionEngine()
        self.memoria       = Memory()
        self.tempo         = TimeEngine(aceleracao=1.0)
        self.circadian     = CircadianRhythm()
        self.humor         = Mood()

        print("=" * 55)
        print("[RENBA] Primeiro nascimento detectado.")
        print(f"[RENBA] {self.personalidade}")
        print(f"[RENBA] {self.estado}")
        print("=" * 55)

        self.db.salvar(self)
        self.db.registrar_sessao(nova=True)

    def _carregar_de_dados(self, dados: dict):
        self.personalidade              = Personality()
        self.personalidade.impulso      = dados["impulso"]
        self.personalidade.variacao     = dados["variacao"]
        self.personalidade.ritmo        = dados["ritmo"]
        self.personalidade.estabilidade = dados["p_estabilidade"]

        self.estado              = InternalState()
        self.estado.energia      = dados["energia"]
        self.estado.curiosidade  = dados["curiosidade"]
        self.estado.estabilidade = dados["estabilidade"]
        self.estado.isolamento   = dados["isolamento"]

        self.tempo            = TimeEngine(aceleracao=1.0)
        self.tempo.tempo_vida = dados["tempo_vida"]

        segundos_offline = self.db.calcular_tempo_offline(dados["last_update"])
        if segundos_offline > 0:
            self.tempo.tempo_vida += segundos_offline
        self.tempo.update(0)

        self.decisao = DecisionEngine()
        if dados["tendencias"]:
            self.decisao.tendencias = dados["tendencias"]

        self.memoria            = Memory()
        self.memoria.frequencia = dados["frequencia"]
        self.circadian          = CircadianRhythm()
        self.humor              = Mood()

        horas_offline = segundos_offline / 3600.0

        print("=" * 55)
        print(f"[RENBA] Retornando... sessão #{dados['total_sessoes'] + 1}")
        print(f"[RENBA] Tempo offline: {self._formatar_tempo(segundos_offline)}")

        if segundos_offline > 60:
            self.db.aplicar_efeitos_offline(self, segundos_offline)
            print(f"[RENBA] Efeitos aplicados:")
            print(f"         energia      → {self.estado.energia:.2f}")
            print(f"         estabilidade → {self.estado.estabilidade:.2f}")
            print(f"         curiosidade  → {self.estado.curiosidade:.2f}")
            if horas_offline > 1:
                print(f"         memória decaída proporcionalmente")
        else:
            print("[RENBA] Retorno rápido — nenhum efeito offline aplicado.")

        print(f"[RENBA] Fase de vida: {self.tempo.fase} | {self.tempo.idade_formatada}")
        print("=" * 55)

        self.db.registrar_sessao(nova=False)

    @staticmethod
    def _formatar_tempo(segundos: float) -> str:
        if segundos < 60:
            return f"{int(segundos)}seg"
        elif segundos < 3600:
            return f"{int(segundos // 60)}min {int(segundos % 60)}seg"
        else:
            h = int(segundos // 3600)
            m = int((segundos % 3600) // 60)
            return f"{h}h {m}min"

    def update(self, dt, largura, altura, mouse_pos=None,
               clique_esq=False, clique_dir=False):
        """
        Atualiza estado interno, interação, movimento e corpo a cada frame.
        v0.6: aceita posição do mouse e eventos de clique.
        """
        # 1. Tempo de vida
        self.tempo.update(dt)

        # 2. Circadiano e humor
        self.circadian.update(self.personalidade)
        self.humor.update(dt, self.estado, self.circadian, self.tempo)

        # 3. v0.6 — Interação com mouse
        if mouse_pos is not None:
            self.interacao.update(
                dt, mouse_pos[0], mouse_pos[1],
                self.x, self.y,
                clique_esq, clique_dir
            )
            self.interacao.aplicar_em_estado(self.estado, self.humor)

        # 4. Circadiano influencia estado interno
        self.estado.aplicar_circadiano(self.circadian, dt)

        # 5. Personalidade
        self.personalidade.update(dt)

        # 6. Percepção
        self.percepcao.update(self.x, self.y, largura, altura)
        self.personalidade.aplicar_percepcao(self.percepcao)

        # 7. Decisão
        acao_anterior = self.decisao.acao_atual
        acao = self.decisao.update(dt, self.estado, self.tempo,
                                   self.circadian, self.humor)

        if acao != acao_anterior:
            probs = self.decisao.probabilidades
            probs_fmt = "  ".join(f"{a[:3]}={p:.0%}" for a, p in probs.items())
            dom = self.memoria.acao_dominante()
            print(
                f"[decisão] {acao_anterior:>8} → {acao:<8} | "
                f"E:{self.estado.energia:.2f} "
                f"C:{self.estado.curiosidade:.2f} "
                f"S:{self.estado.estabilidade:.2f} | "
                f"probs: {probs_fmt} | dominante: {dom}"
            )
            self.db.tick_ciclo(self)

        # 8. Estado interno
        self.estado.update(dt, acao, self.tempo)

        # 9. Reforço
        resultado = self._avaliar_resultado(acao)
        self.decisao.reforcar(acao, resultado)

        # 10. Memória
        snapshot = self.memoria.snapshot_estado(self.estado)
        self.memoria.registrar(acao, snapshot)

        # 11. Ação influencia personalidade
        self._aplicar_acao_na_personalidade(acao)

        # 12. v0.6 — Diário
        self.diario.update(self)

        # 13. Velocidade alvo
        acao_atual = self.decisao.acao_atual

        # v0.6: proximidade do cursor desacelera levemente (atenção)
        fator_interacao = 1.0 - self.interacao.presenca * 0.4

        if acao_atual == "descansar":
            velocidade_alvo = 0.0
        elif acao_atual == "retrair":
            velocidade_alvo = (15.0 + self.personalidade.impulso * 20.0) * fator_interacao
        elif acao_atual == "observar":
            velocidade_alvo = (8.0 + self.personalidade.impulso * 12.0) * fator_interacao
        elif acao_atual == "explorar":
            velocidade_alvo = (50.0 + self.personalidade.impulso * 100.0) * fator_interacao
        elif acao_atual == "expandir":
            velocidade_alvo = (70.0 + self.personalidade.impulso * 120.0) * fator_interacao
        else:
            velocidade_alvo = 40.0 + self.personalidade.impulso * 80.0

        if acao_atual == "descansar":
            taxa_suavizacao = 0.4
        elif acao_atual in ("observar", "retrair"):
            taxa_suavizacao = 0.8
        else:
            taxa_suavizacao = 1.2
        self.velocidade += (velocidade_alvo - self.velocidade) * taxa_suavizacao * dt

        # 14. Direção
        if acao_atual == "descansar":
            amplitude_angular = 0.01 * dt
        elif acao_atual == "observar":
            amplitude_angular = 0.3 * dt
        elif acao_atual == "retrair":
            amplitude_angular = 0.8 * dt
        else:
            amplitude_angular = (
                self.personalidade.variacao *
                (1.0 - self.personalidade.estabilidade * 0.6) *
                2.5 * dt
            )

        # v0.6: cursor muito próximo faz o RENBA girar em direção oposta
        if self.interacao.em_contato:
            import math as _math
            dx = self.x - (mouse_pos[0] if mouse_pos else self.x)
            dy = self.y - (mouse_pos[1] if mouse_pos else self.y)
            angulo_fuga = _math.atan2(dy, dx)
            diff = angulo_fuga - self.angulo
            while diff >  _math.pi: diff -= 2 * _math.pi
            while diff < -_math.pi: diff += 2 * _math.pi
            self.angulo += diff * 0.05
        else:
            self.angulo += random.uniform(-amplitude_angular, amplitude_angular)

        # 15. Movimento
        self.x += math.cos(self.angulo) * self.velocidade * dt
        self.y += math.sin(self.angulo) * self.velocidade * dt

        # 16. Reflexão nas bordas
        margem = self.corpo.raio_base + 5

        if self.x < margem:
            self.x = margem
            self.angulo = math.pi - self.angulo
        elif self.x > largura - margem:
            self.x = largura - margem
            self.angulo = math.pi - self.angulo

        if self.y < margem:
            self.y = margem
            self.angulo = -self.angulo
        elif self.y > altura - margem:
            self.y = altura - margem
            self.angulo = -self.angulo

        # 17. Corpo visual — v0.6: passa humor para cor dinâmica
        self.corpo.update(self.personalidade, dt, self.humor)

    def draw(self, surface):
        self.corpo.draw(surface, int(self.x), int(self.y), self.personalidade)

    def salvar(self):
        self.diario.ao_dormir(self)
        self.db.salvar(self)
        self.db.registrar_encerramento()

    # ------------------------------------------------------------------ #
    #  Auxiliares                                                          #
    # ------------------------------------------------------------------ #

    def _avaliar_resultado(self, acao: str) -> float:
        e = self.estado
        if acao == "explorar":
            return (e.curiosidade * 0.6 + e.energia * 0.4) - 0.5
        elif acao == "descansar":
            return ((1.0 - e.energia) * 0.8) - 0.3
        elif acao == "expandir":
            return (e.energia * 0.7 + e.estabilidade * 0.3) - 0.5
        elif acao == "retrair":
            return ((1.0 - e.estabilidade) * 0.7) - 0.3
        elif acao == "observar":
            return 0.1
        return 0.0

    def _aplicar_acao_na_personalidade(self, acao: str):
        p   = self.personalidade
        ftr = self.tempo.fator_aprendizado * 0.008

        if acao == "explorar":
            p.impulso  = min(1.0, p.impulso  + ftr)
            p.variacao = min(1.0, p.variacao  + ftr * 0.5)
        elif acao == "descansar":
            p.impulso      = max(0.0, p.impulso    - ftr * 0.5)
            p.estabilidade = min(1.0, p.estabilidade + ftr)
        elif acao == "expandir":
            p.variacao = min(1.0, p.variacao + ftr * 0.8)
            p.ritmo    = min(1.0, p.ritmo    + ftr * 0.3)
        elif acao == "retrair":
            p.variacao     = max(0.0, p.variacao   - ftr * 0.5)
            p.estabilidade = min(1.0, p.estabilidade + ftr * 0.5)
        elif acao == "observar":
            pass
