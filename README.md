# 🧬 RENBA - Organismo Digital com Inteligência Artificial

> 🧠 Um organismo digital que percebe, decide e evolui ao longo do tempo.
 RENBA é um projeto experimental desenvolvido em Python que simula um organismo digital com comportamento adaptativo. O sistema é baseado em conceitos de Inteligência Artificial, incluindo percepção, memória, estados internos e tomada de decisão.

⚠️ **Projeto em desenvolvimento**
Esta é a primeira versão do RENBA, criada com foco em experimentação e aprendizado prático em Inteligência Artificial. Novas funcionalidades e melhorias estão sendo desenvolvidas continuamente.



## 🚀 Demonstração

![RENBA em execução](demo.gif)



## 🎮 Interação e Comportamento

O RENBA simula um organismo digital com comportamento dinâmico, reagindo ao ambiente em tempo real.

Nesta versão inicial, o sistema já apresenta:

* 🧠 Tomada de decisão baseada em estado interno
* 💭 Sistema de memória com decaimento
* 😊 Estados emocionais (humor)
* 👁️ Percepção do ambiente
* ⚡ Sistema de energia
* 🔄 Comportamento emergente básico

## 🔥 Diferencial

Este projeto vai além de scripts tradicionais, simulando um organismo digital com comportamento emergente, inspirado em conceitos de IA e sistemas adaptativos.

## 🏗️ Arquitetura do Sistema

O projeto é modularizado para simular componentes cognitivos:

* `main.py` → ponto de entrada
* `entity.py` → entidade principal
* `decision.py` → tomada de decisão
* `memory.py` → memória
* `mood.py` → estado emocional
* `perception.py` → percepção
* `world.py` → ambiente
* `time_engine.py` → tempo
* `circadian.py` → ciclo biológico
* `personality.py` → personalidade
* `internal_state.py` → drives internos (energia, curiosidade...)
* `interaction.py` → interação com o mouse
* `body.py` → forma e cor (reflete o humor)
* `diary.py` → diário em primeira pessoa
* `database.py` → persistência SQLite e efeitos do tempo offline



## ▶️ Como executar

Requer Python 3.10+.

```bash
pip install -r requirements.txt
python main.py
```

Opções:

| Opção | Efeito |
|---|---|
| `--acelerar N` | multiplica o tempo de vida (`3600` → 1 hora real = 1 dia de vida) |
| `--db CAMINHO` | usa outro arquivo de banco (teste sem afetar o RENBA principal) |

Teste rápido sem mexer no RENBA principal:

```bash
python main.py --acelerar 3600 --db teste.db
```

O estado fica em `renba.db` (tabelas `state`, `memory` e `log`). Apagar esse
arquivo faz um RENBA novo nascer.

## 🕹️ Controles

| Entrada | Efeito |
|---|---|
| Clique esquerdo perto dele | carinho: humor e curiosidade sobem |
| Clique direito perto dele | susto: humor cai |
| Cursor por perto | ele percebe, desacelera e foge se você encostar |
| `H` | esconde/mostra o HUD |
| `ESC` | encerra, escreve no diário e salva |



## 💡 Objetivo

Explorar na prática conceitos de Inteligência Artificial e sistemas adaptativos, evoluindo o projeto ao longo do tempo.



## 🚀 Próximas evoluções

* Ciclo de vida completo (o que acontece após os 30 dias)
* Aprendizado adaptativo
* Interface mais avançada
* Expansão da interação
* Visualização de dados



## 🛠️ Tecnologias

* Python 🐍
* SQLite 🗄️
* Lógica de programação
* Conceitos de IA



## 👨‍💻 Autor

Abner Ferreira
📧 [abnersf23@gmail.com](mailto:abnersf23@gmail.com)
🔗 https://github.com/abnersf23-cmd



## ⭐ Observação

Este projeto faz parte da minha evolução prática na área de Inteligência Artificial e continuará sendo aprimorado com o tempo.
