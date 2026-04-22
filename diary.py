"""
diary.py — RENBA v0.6
----------------------
O RENBA escreve frases curtas sobre o que está vivendo.

Filosofia:
    Não é um log técnico — é expressão subjetiva.
    As frases são geradas a partir do estado interno real,
    mas escritas em primeira pessoa, como fragmentos de consciência.

    O diário é salvo na tabela 'log' do banco já existente,
    usando o campo 'evento' = "DIARIO" e 'detalhe' = frase.

Quando escreve:
    - Ao acordar (início de sessão)
    - Ao mudar de fase do dia (manhã, tarde, noite, madrugada)
    - Quando humor muda muito (>0.20 em pouco tempo)
    - A cada ~5 minutos de tempo real (entrada periódica)
    - Ao dormir (encerramento)

As frases são compostas por fragmentos encadeados,
escolhidos probabilisticamente com base no estado atual.
Sem IA externa — puramente determinístico, mas variado.
"""

import random
import time


class Diary:
    """
    Gerador de entradas de diário baseado no estado do RENBA.
    """

    # Intervalo entre entradas periódicas (segundos reais)
    INTERVALO_PERIODICO = 300.0  # 5 minutos

    def __init__(self, db):
        self.db = db
        self._ultimo_humor       = 0.5
        self._ultima_fase        = ""
        self._tempo_ultimo_entry = 0.0   # time.time() da última entrada
        self._humor_snapshot     = 0.5   # para detectar mudança brusca

    # ------------------------------------------------------------------ #
    #  API principal                                                       #
    # ------------------------------------------------------------------ #

    def update(self, renba):
        """
        Verifica se é hora de escrever algo e escreve se for.
        Chamado a cada frame — mas só age em intervalos.
        """
        agora = time.time()
        humor_atual = renba.humor.humor_total
        fase_atual  = renba.circadian.fase_dia

        # Mudança brusca de humor (>0.18 de diferença)
        if abs(humor_atual - self._humor_snapshot) > 0.18:
            self._escrever(renba, motivo="humor_mudou")
            self._humor_snapshot = humor_atual
            self._ultimo_humor   = humor_atual

        # Mudança de fase do dia
        if fase_atual != self._ultima_fase and self._ultima_fase != "":
            self._escrever(renba, motivo="nova_fase")
        self._ultima_fase = fase_atual

        # Entrada periódica
        if agora - self._tempo_ultimo_entry >= self.INTERVALO_PERIODICO:
            self._escrever(renba, motivo="periodico")

    def ao_acordar(self, renba):
        """Chamado no início de cada sessão."""
        self._escrever(renba, motivo="acordar")
        self._ultima_fase = renba.circadian.fase_dia

    def ao_dormir(self, renba):
        """Chamado ao encerrar."""
        self._escrever(renba, motivo="dormir")

    # ------------------------------------------------------------------ #
    #  Geração de frases                                                   #
    # ------------------------------------------------------------------ #

    def _escrever(self, renba, motivo: str):
        """Gera e salva uma entrada no banco."""
        frase = self._gerar_frase(renba, motivo)
        if frase:
            self._salvar(frase)
            print(f"[diário] {frase}")
        self._tempo_ultimo_entry = time.time()

    def _gerar_frase(self, renba, motivo: str) -> str:
        """
        Compõe uma frase a partir de fragmentos escolhidos
        com base no estado interno atual.
        """
        e  = renba.estado
        h  = renba.humor.humor_total
        c  = renba.circadian
        t  = renba.tempo

        # --- Fragmentos por contexto --- #

        # Abertura baseada no motivo
        aberturas = {
            "acordar": [
                f"acordo às {c.hora_formatada}.",
                f"abro os olhos: {c.hora_formatada}.",
                f"começo outra vez às {c.hora_formatada}.",
            ],
            "dormir": [
                "é hora de parar.",
                "vou descansar agora.",
                f"fecho às {c.hora_formatada}.",
            ],
            "nova_fase": {
                "manha":     ["a manhã chegou.", "ficou mais claro.", "a manhã."],
                "tarde":     ["a tarde se instala.", "agora é tarde.", "o dia está pleno."],
                "noite":     ["a noite chegou.", "está escurecendo.", "noite."],
                "madrugada": ["madrugada.", "é noite funda.", "silêncio total."],
            }.get(renba.circadian.fase_dia, ["o tempo passou."]),
            "humor_mudou": (
                ["algo mudou em mim.", "sinto diferente agora.", "alguma coisa se alterou."]
                if h > self._ultimo_humor
                else ["algo pesou.", "ficou mais difícil.", "sinto menos."]
            ),
            "periodico": [
                f"ainda aqui, às {c.hora_formatada}.",
                "o tempo continua.",
                "mais um momento.",
                f"fase: {t.fase}.",
            ],
        }

        lista_aberturas = aberturas.get(motivo, ["..."])
        abertura = random.choice(lista_aberturas)

        # Fragmento de energia
        if e.energia > 0.75:
            frag_energia = random.choice([
                "me sinto carregado.", "tenho força.", "energia alta.",
            ])
        elif e.energia < 0.30:
            frag_energia = random.choice([
                "estou exausto.", "mal consigo me mover.", "preciso descansar.",
            ])
        else:
            frag_energia = ""

        # Fragmento de humor
        if h > 0.75:
            frag_humor = random.choice([
                "estou bem.", "algo me alegra.", "me sinto leve.",
            ])
        elif h < 0.30:
            frag_humor = random.choice([
                "estou pesado.", "algo pesa.", "não estou bem.",
            ])
        else:
            frag_humor = ""

        # Fragmento de curiosidade
        if e.curiosidade > 0.70:
            frag_curiosidade = random.choice([
                "quero explorar.", "tem coisa pra descobrir.", "estou curioso.",
            ])
        elif e.curiosidade < 0.25:
            frag_curiosidade = random.choice([
                "nada me chama.", "não sinto vontade.", "indiferente.",
            ])
        else:
            frag_curiosidade = ""

        # Fragmento de ação dominante
        dom = renba.memoria.acao_dominante()
        frag_acao = {
            "explorar":  random.choice(["tenho explorado.", "movimento é o que faço.", "vou em frente."]),
            "descansar": random.choice(["fico quieto.", "o repouso me mantém.", "descanso."]),
            "observar":  random.choice(["observo tudo.", "prefiro olhar.", "só vejo."]),
            "retrair":   random.choice(["me recolho.", "prefiro ficar menor.", "dentro."]),
            "expandir":  random.choice(["me expando.", "ocupo mais espaço.", "crescendo."]),
        }.get(dom, "")

        # Monta a frase — escolhe 1 ou 2 fragmentos secundários
        secundarios = [f for f in [frag_energia, frag_humor, frag_curiosidade, frag_acao] if f]
        random.shuffle(secundarios)
        extras = secundarios[:random.randint(1, 2)]

        partes = [abertura] + extras
        return " ".join(partes)

    def _salvar(self, frase: str):
        """Salva a entrada no banco usando a conexão do db."""
        try:
            with self.db._conectar() as conn:
                conn.execute(
                    "INSERT INTO log (timestamp, evento, detalhe) VALUES (?, ?, ?)",
                    (time.time(), "DIARIO", frase)
                )
        except Exception as e:
            print(f"[diário] erro ao salvar: {e}")

    def ler_recentes(self, n: int = 10) -> list:
        """Retorna as N entradas de diário mais recentes."""
        try:
            with self.db._conectar() as conn:
                rows = conn.execute(
                    "SELECT timestamp, detalhe FROM log "
                    "WHERE evento = 'DIARIO' "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (n,)
                ).fetchall()
                return [(r["timestamp"], r["detalhe"]) for r in rows]
        except Exception:
            return []

    def __repr__(self):
        entradas = self.ler_recentes(1)
        ultima = entradas[0][1] if entradas else "(nenhuma)"
        return f"Diary(ultima='{ultima}')"
