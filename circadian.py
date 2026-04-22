import time
import math

class CircadianRhythm:
    """
    Ritmo circadiano do RENBA — v0.5

    Baseado no horário REAL do mundo (relógio da máquina).
    O RENBA vive no mesmo ciclo de dia/noite que você.

    Retorna influências entre -1.0 e +1.0 para cada drive:
        positivo → amplifica o drive
        negativo → suprime o drive

    Fases do dia:
        madrugada  (00h–06h) : tudo suprimido, modo repouso
        manhã      (06h–12h) : despertar gradual, curiosidade sobe
        tarde      (12h–18h) : pico de atividade e exploração
        noite      (18h–24h) : desaceleração, retrair/observar dominam

    Personalidade modula o perfil:
        impulso alto  → acorda mais cedo, dorme mais tarde
        variacao alta → ciclo menos previsível, mais irregular
        estabilidade alta → segue o ciclo rigidamente
    """

    def __init__(self):
        self.hora_atual     = 0.0   # 0.0 → 24.0
        self.fase_dia       = "madrugada"
        self.fator_atividade = 0.0  # 0.0 (dormindo) → 1.0 (pico)

        # Influências individuais nos drives (-1.0 → +1.0)
        self.influencia_energia      = 0.0
        self.influencia_curiosidade  = 0.0
        self.influencia_estabilidade = 0.0
        self.influencia_descanso     = 0.0  # sinal para o motor de decisão

    def update(self, personalidade):
        """
        Recalcula as influências com base na hora real atual
        e na personalidade do RENBA.
        """
        t = time.localtime()
        # Hora como float: 14h30 = 14.5
        self.hora_atual = t.tm_hour + t.tm_min / 60.0 + t.tm_sec / 3600.0

        # Personalidade modifica o ciclo
        # impulso alto → RENBA é mais "madrugador" e "noturno"
        # estabilidade alta → segue ciclo mais regularmente
        deslocamento = (personalidade.impulso - 0.5) * 2.0  # -1h a +1h
        hora_efetiva = (self.hora_atual + deslocamento) % 24.0

        # Curva de atividade base: senoide suavizada
        # Pico às 15h, vale às 3h
        self.fator_atividade = self._curva_atividade(hora_efetiva, personalidade)

        # Determina fase do dia
        h = hora_efetiva
        if h < 6.0:
            self.fase_dia = "madrugada"
        elif h < 12.0:
            self.fase_dia = "manha"
        elif h < 18.0:
            self.fase_dia = "tarde"
        else:
            self.fase_dia = "noite"

        # Calcula influências por drive
        self._calcular_influencias(hora_efetiva, personalidade)

    def _curva_atividade(self, hora: float, personalidade) -> float:
        """
        Curva senoidal que representa o nível de atividade ao longo do dia.
        Suavizada para não ser mecânica demais.

        Pico: ~15h (valor 1.0)
        Vale: ~3h  (valor 0.0)
        """
        # Curva completa de 24h: pico às 15h, vale às 3h
        # Normaliza hora para 0→1 dentro do ciclo, com 15h = 0.5 (pico)
        hora_norm = (hora - 3.0) / 24.0  # 3h=0, 15h=0.5, 3h seguinte=1
        angulo    = hora_norm * 2 * math.pi  # 0 → 2π em 24h
        base      = (math.sin(angulo - math.pi / 2) + 1.0) / 2.0  # 0.0 → 1.0

        # variacao alta → adiciona leve irregularidade ao ciclo
        # (sem aleatoriedade pura — usa hora como seed para ser consistente)
        irregularidade = math.sin(hora * 3.7 + personalidade.variacao * 5.0) * 0.08
        irregularidade *= personalidade.variacao

        return max(0.0, min(1.0, base + irregularidade))

    def _calcular_influencias(self, hora: float, personalidade):
        """
        Traduz o fator de atividade em influências específicas por drive.
        Cada drive tem seu próprio perfil ao longo do dia.
        """
        fa = self.fator_atividade

        # Energia: segue atividade diretamente
        # (circadiano não cria energia — modula quanto o RENBA consegue usar)
        self.influencia_energia = (fa - 0.5) * 0.3

        # Curiosidade: pico na manhã (6h–10h) quando tudo é novo
        # Depois da tarde, curiosidade natural cai
        if 6.0 <= hora < 11.0:
            pico_manha = math.sin((hora - 6.0) / 5.0 * math.pi)
            self.influencia_curiosidade = pico_manha * 0.25
        else:
            self.influencia_curiosidade = (fa - 0.6) * 0.15

        # Estabilidade: maior de noite (quieto), menor de tarde (agitado)
        self.influencia_estabilidade = (0.5 - fa) * 0.2

        # Descanso: forte à noite e madrugada
        # Sinal que o motor de decisão vai usar para aumentar peso de descansar
        if hora < 6.0 or hora >= 22.0:
            # Madrugada/noite profunda: forte impulso para descansar
            if hora >= 22.0:
                prog = (hora - 22.0) / 2.0
            else:
                prog = 1.0 - hora / 6.0
            self.influencia_descanso = 0.3 + prog * 0.5
        elif 6.0 <= hora < 8.0:
            # Acordando: descanso diminui gradualmente
            self.influencia_descanso = 0.3 * (1.0 - (hora - 6.0) / 2.0)
        else:
            self.influencia_descanso = 0.0

    @property
    def hora_formatada(self) -> str:
        h = int(self.hora_atual)
        m = int((self.hora_atual - h) * 60)
        return f"{h:02d}:{m:02d}"

    def __repr__(self):
        return (
            f"Circadian("
            f"hora={self.hora_formatada}, "
            f"fase={self.fase_dia}, "
            f"atividade={self.fator_atividade:.2f}, "
            f"descanso={self.influencia_descanso:.2f})"
        )
