"""
database.py — RENBA v0.4
-------------------------
Responsável por toda a persistência do RENBA entre sessões.

Filosofia:
    O banco é a "memória de longo prazo" do organismo.
    Tudo que o RENBA aprende e sente deve poder sobreviver
    ao fechamento do programa.

Estrutura do banco (renba.db):
    Tabela 'state'  → estado único do RENBA (sempre 1 linha, id=1)
    Tabela 'memory' → frequência das ações com seus pesos acumulados
    Tabela 'log'    → registro de eventos importantes (auditoria / diário)

Responsabilidades desta classe:
    - Criar banco se não existir
    - Salvar estado completo
    - Carregar estado completo
    - Calcular e aplicar efeitos do tempo offline
    - Salvar automaticamente a cada N ciclos
    - Proteger contra perda de dados em fechamento inesperado
"""

import sqlite3
import time
import math
import os

# Nome do arquivo do banco — na mesma pasta do projeto
CAMINHO_DB = "renba.db"

# Salva automaticamente a cada N ciclos de decisão
SALVAR_A_CADA_CICLOS = 30


class DatabaseManager:
    """
    Gerencia toda a persistência do RENBA via SQLite.

    Uso:
        db = DatabaseManager()
        dados = db.carregar()          # ao iniciar
        db.salvar(renba)               # periodicamente e ao fechar
        db.tick_ciclo(renba)           # a cada decisão (auto-save)
    """

    def __init__(self, caminho: str = CAMINHO_DB):
        self.caminho          = caminho
        self._ciclos          = 0          # contador para auto-save
        self._conexao         = None       # conexão reutilizável

        # Abre/cria o banco e garante que as tabelas existem
        self._inicializar_banco()

    # ------------------------------------------------------------------ #
    #  Inicialização                                                       #
    # ------------------------------------------------------------------ #

    def _inicializar_banco(self):
        """Cria as tabelas se não existirem. Idempotente."""
        with self._conectar() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS state (
                    id              INTEGER PRIMARY KEY DEFAULT 1,

                    -- Estado interno (InternalState)
                    energia         REAL DEFAULT 0.8,
                    curiosidade     REAL DEFAULT 0.5,
                    estabilidade    REAL DEFAULT 0.5,
                    isolamento      REAL DEFAULT 0.3,

                    -- Personalidade (Personality)
                    impulso         REAL DEFAULT 0.5,
                    variacao        REAL DEFAULT 0.4,
                    ritmo           REAL DEFAULT 0.5,
                    p_estabilidade  REAL DEFAULT 0.5,

                    -- Tempo de vida (TimeEngine)
                    tempo_vida      REAL DEFAULT 0.0,

                    -- Tendências de decisão (DecisionEngine) — JSON simples
                    tendencias      TEXT DEFAULT '{}',

                    -- Controle de sessão
                    last_update     REAL DEFAULT 0.0,
                    total_sessoes   INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS memory (
                    acao    TEXT PRIMARY KEY,
                    valor   REAL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   REAL,
                    evento      TEXT,
                    detalhe     TEXT
                );
            """)

    def _conectar(self) -> sqlite3.Connection:
        """Retorna uma conexão com o banco. Cria o arquivo se necessário."""
        conn = sqlite3.connect(self.caminho)
        conn.row_factory = sqlite3.Row  # acesso por nome de coluna
        return conn

    # ------------------------------------------------------------------ #
    #  Verificação de existência                                           #
    # ------------------------------------------------------------------ #

    def existe_estado_salvo(self) -> bool:
        """Retorna True se já há dados salvos para este RENBA."""
        with self._conectar() as conn:
            row = conn.execute("SELECT id FROM state WHERE id = 1").fetchone()
            return row is not None

    # ------------------------------------------------------------------ #
    #  Salvar                                                              #
    # ------------------------------------------------------------------ #

    def salvar(self, renba):
        """
        Salva o estado completo do RENBA no banco.
        Chamado periodicamente e sempre ao encerrar.
        Usa INSERT OR REPLACE para garantir apenas 1 linha (id=1).
        """
        import json

        e  = renba.estado
        p  = renba.personalidade
        t  = renba.tempo
        d  = renba.decisao
        mem = renba.memoria

        tendencias_json = json.dumps(d.tendencias)

        with self._conectar() as conn:
            # Salva estado principal
            conn.execute("""
                INSERT OR REPLACE INTO state (
                    id, energia, curiosidade, estabilidade, isolamento,
                    impulso, variacao, ritmo, p_estabilidade,
                    tempo_vida, tendencias, last_update, total_sessoes
                ) VALUES (
                    1, ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, COALESCE(
                        (SELECT total_sessoes FROM state WHERE id=1), 0
                    )
                )
            """, (
                e.energia, e.curiosidade, e.estabilidade, e.isolamento,
                p.impulso, p.variacao, p.ritmo, p.estabilidade,
                t.tempo_vida, tendencias_json, time.time()
            ))

            # Salva memória de frequências
            conn.execute("DELETE FROM memory")
            for acao, valor in mem.frequencia.items():
                conn.execute(
                    "INSERT INTO memory (acao, valor) VALUES (?, ?)",
                    (acao, valor)
                )

        # Não printa a cada auto-save — só quando chamado explicitamente
        # (o log de auto-save fica no tick_ciclo)

    def registrar_sessao(self, nova: bool):
        """
        Registra início de sessão no log e incrementa contador.
        nova=True → primeiro boot, nova=False → retorno de sessão.
        """
        evento = "NASCIMENTO" if nova else "RETORNO"
        with self._conectar() as conn:
            conn.execute("""
                UPDATE state SET total_sessoes = total_sessoes + 1
                WHERE id = 1
            """)
            conn.execute("""
                INSERT INTO log (timestamp, evento, detalhe)
                VALUES (?, ?, ?)
            """, (time.time(), evento, f"sessao iniciada"))

    def registrar_encerramento(self):
        """Registra encerramento no log."""
        with self._conectar() as conn:
            conn.execute("""
                INSERT INTO log (timestamp, evento, detalhe)
                VALUES (?, ?, ?)
            """, (time.time(), "ENCERRAMENTO", "programa fechado"))

    # ------------------------------------------------------------------ #
    #  Carregar                                                            #
    # ------------------------------------------------------------------ #

    def carregar(self) -> dict:
        """
        Carrega o estado salvo do banco.
        Retorna um dicionário com todos os dados ou None se não houver.
        """
        import json

        with self._conectar() as conn:
            row = conn.execute("SELECT * FROM state WHERE id = 1").fetchone()
            if not row:
                return None

            mem_rows = conn.execute("SELECT acao, valor FROM memory").fetchall()
            frequencia = {r["acao"]: r["valor"] for r in mem_rows}

            tendencias = json.loads(row["tendencias"] or "{}")

            return {
                # Estado interno
                "energia":        row["energia"],
                "curiosidade":    row["curiosidade"],
                "estabilidade":   row["estabilidade"],
                "isolamento":     row["isolamento"],
                # Personalidade
                "impulso":        row["impulso"],
                "variacao":       row["variacao"],
                "ritmo":          row["ritmo"],
                "p_estabilidade": row["p_estabilidade"],
                # Tempo
                "tempo_vida":     row["tempo_vida"],
                # Decisão
                "tendencias":     tendencias,
                # Memória
                "frequencia":     frequencia,
                # Sessão
                "last_update":    row["last_update"],
                "total_sessoes":  row["total_sessoes"],
            }

    # ------------------------------------------------------------------ #
    #  Tempo offline                                                       #
    # ------------------------------------------------------------------ #

    def calcular_tempo_offline(self, last_update: float) -> float:
        """
        Calcula quantos segundos reais passaram desde o último save.
        Retorna 0 se last_update for inválido.
        """
        if last_update <= 0:
            return 0.0
        agora = time.time()
        return max(0.0, agora - last_update)

    def aplicar_efeitos_offline(self, renba, segundos_offline: float):
        """
        Aplica os efeitos do tempo que passou enquanto o RENBA estava offline.

        Lógica:
            - Descanso natural: energia se recupera (até 95% do máximo)
            - Estabilidade sobe levemente (RENBA "acalma" sem estímulos)
            - Memória de frequência decai (o tempo apaga padrões antigos)
            - Curiosidade sobe levemente (ficou sem estímulos = quer explorar)

        Escala:
            Os efeitos são proporcionais ao tempo, mas com teto razoável.
            Após 24h offline, o RENBA está bem descansado mas um pouco
            mais curioso e com memória parcialmente esquecida.

        Não mexe em: tendências, personalidade base, tempo de vida acumulado.
        """
        if segundos_offline <= 0:
            return

        # Converte para horas para cálculo mais intuitivo
        horas = segundos_offline / 3600.0

        # Teto: efeitos de até 24h (além disso, retornos decrescentes)
        horas_efetivas = min(horas, 24.0)
        fator = horas_efetivas / 24.0  # 0.0 → 1.0

        e = renba.estado

        # Energia: recupera até 0.95 proporcionalmente ao tempo offline
        energia_alvo  = 0.95
        energia_ganho = (energia_alvo - e.energia) * fator * 0.85
        e.energia = min(0.95, e.energia + energia_ganho)

        # Estabilidade: sobe levemente (sem estresse = mais calmo)
        e.estabilidade = min(1.0, e.estabilidade + fator * 0.10)

        # Curiosidade: sobe um pouco (ausência de estímulos gera vontade)
        e.curiosidade  = min(1.0, e.curiosidade  + fator * 0.12)

        # Memória: decai proporcionalmente ao tempo
        fator_decaimento = math.pow(0.85, horas_efetivas / 6.0)  # decai 15% a cada 6h
        for acao in list(renba.memoria.frequencia.keys()):
            renba.memoria.frequencia[acao] *= fator_decaimento
            if renba.memoria.frequencia[acao] < 0.01:
                del renba.memoria.frequencia[acao]

        # Clamp final de segurança
        e.energia      = max(0.05, min(1.0, e.energia))
        e.estabilidade = max(0.0,  min(1.0, e.estabilidade))
        e.curiosidade  = max(0.0,  min(1.0, e.curiosidade))

    # ------------------------------------------------------------------ #
    #  Auto-save por ciclos                                                #
    # ------------------------------------------------------------------ #

    def tick_ciclo(self, renba):
        """
        Chamado a cada mudança de ação (ciclo de decisão).
        Acumula contador e salva quando atingir o limite.
        Silencioso — não imprime nada na tela.
        """
        self._ciclos += 1
        if self._ciclos >= SALVAR_A_CADA_CICLOS:
            self.salvar(renba)
            self._ciclos = 0

    # ------------------------------------------------------------------ #
    #  Utilitários                                                         #
    # ------------------------------------------------------------------ #

    def total_sessoes(self) -> int:
        """Retorna quantas vezes o RENBA foi iniciado."""
        with self._conectar() as conn:
            row = conn.execute(
                "SELECT total_sessoes FROM state WHERE id = 1"
            ).fetchone()
            return row["total_sessoes"] if row else 0

    def __repr__(self):
        existe = os.path.exists(self.caminho)
        tamanho = os.path.getsize(self.caminho) if existe else 0
        return f"DatabaseManager(db={self.caminho}, size={tamanho}b)"
