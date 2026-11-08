"""
RENBA v0.7
----------
Interação, Cor Emocional e Diário de Vida.

Novo em v0.7:
    - correção: aprendizado, reforço e personalidade agora escalam por dt
      (antes eram aplicados por frame e saturavam em segundos)
    - correção: memória registra por ciclo de decisão, não por frame
    - humor (base e imediato) persiste entre sessões
    - banco usa uma única conexão (antes vazava uma por chamada)
    - estado é salvo mesmo se o programa cair ou receber Ctrl+C
    - dt limitado: arrastar a janela não "teleporta" o RENBA
    - tecla H esconde/mostra o HUD
    - linha de comando: --acelerar N  e  --db CAMINHO

Novo em v0.6:
    interaction.py → sistema de interação mouse↔RENBA
                     - presença do cursor na zona de percepção
                     - clique esquerdo: estímulo positivo (carinho)
                     - clique direito:  estímulo negativo (susto)
                     - RENBA desacelera quando cursor se aproxima
                     - RENBA desvia quando cursor está em contato

    body.py (atualizado) → cor reflete humor_total do Mood
                     - roxo/índigo  : abatido
                     - azul frio    : baixo
                     - azul claro   : neutro (cor original)
                     - turquesa     : bem
                     - dourado/âmbar: ótimo
                     - transição suave via lerp

    diary.py → diário de vida em primeira pessoa
                     - escreve ao acordar e ao dormir
                     - registra mudanças bruscas de humor
                     - registra trocas de fase do dia
                     - entrada periódica a cada 5 minutos
                     - salvo na tabela 'log' do banco
                     - últimas 4 entradas visíveis na tela

Teclas:
    ESC          → encerra (salva e escreve entrada de diário)
    H            → esconde/mostra o HUD
    Clique esq.  → carinho (humor sobe)
    Clique dir.  → susto   (humor cai)
"""

import argparse
import sys

from world import World
from entity import RENBA

# Maior passo de tempo aceito por frame. Se a janela travar (arrastada,
# minimizada, breakpoint) o dt real pode ser de vários segundos — sem limite
# o RENBA atravessaria a tela e os drives dariam saltos.
DT_MAXIMO = 0.1


def _argumentos():
    parser = argparse.ArgumentParser(description="RENBA — organismo digital")
    parser.add_argument(
        "--acelerar", type=float, default=1.0, metavar="N",
        help="multiplicador do tempo de vida (ex.: 3600 = 1h real vira 1 dia). Padrão: 1",
    )
    parser.add_argument(
        "--db", default=None, metavar="CAMINHO",
        help="arquivo SQLite alternativo (útil para testar sem afetar o RENBA principal)",
    )
    return parser.parse_args()


def main():
    # No Windows, com a saída redirecionada o console usa cp1252 e os "→" dos
    # prints derrubariam o programa — força UTF-8 e troca o que não couber
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args  = _argumentos()
    mundo = World()

    cx = World.LARGURA  // 2
    cy = World.ALTURA   // 2
    renba = RENBA(cx, cy, aceleracao=args.acelerar, caminho_db=args.db)

    dt = 0.016

    print(f"[RENBA] v0.7 rodando. ESC para encerrar, H para o HUD.")
    print(f"[RENBA] Clique esq = carinho | Clique dir = susto")
    if args.acelerar != 1.0:
        print(f"[RENBA] Tempo de vida acelerado {args.acelerar:g}x")

    try:
        while mundo.rodando:
            mundo.processar_eventos()
            mundo.limpar()

            renba.update(
                dt, World.LARGURA, World.ALTURA,
                mouse_pos  = mundo.mouse_pos,
                clique_esq = mundo.clique_esq,
                clique_dir = mundo.clique_dir,
            )
            renba.draw(mundo.surface)

            if mundo.mostrar_hud:
                fps = mundo.clock.get_fps()
                mundo.exibir_info(renba, fps)
                mundo.exibir_percepcao(renba)
                mundo.exibir_comportamento(renba)
                mundo.exibir_psicologia(renba)
                mundo.exibir_diario(renba, dt)
            mundo.exibir_interacao(renba)

            dt = min(mundo.atualizar(), DT_MAXIMO)
    except KeyboardInterrupt:
        print("\n[RENBA] Interrompido (Ctrl+C).")
    finally:
        # Salva mesmo se algo der errado no loop — o RENBA não perde o dia
        print("[RENBA] Encerrando — salvando estado e diário...")
        renba.salvar()
        print(f"[RENBA] {renba.memoria}")
        mundo.encerrar()
        print("[RENBA] Até a próxima sessão.")


if __name__ == "__main__":
    main()
