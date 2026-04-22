"""
RENBA v0.6
----------
Interação, Cor Emocional e Diário de Vida.

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
    Clique esq.  → carinho (humor sobe)
    Clique dir.  → susto   (humor cai)
"""

from world import World
from entity import RENBA


def main():
    mundo = World()

    cx = World.LARGURA  // 2
    cy = World.ALTURA   // 2
    renba = RENBA(cx, cy)

    dt = 0.016

    print(f"[RENBA] v0.6 rodando. ESC para encerrar.")
    print(f"[RENBA] Clique esq = carinho | Clique dir = susto")

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

        fps = 1.0 / dt if dt > 0 else 60.0
        mundo.exibir_info(renba, fps)
        mundo.exibir_percepcao(renba)
        mundo.exibir_comportamento(renba)
        mundo.exibir_psicologia(renba)
        mundo.exibir_interacao(renba)         # v0.6
        mundo.exibir_diario(renba, dt)        # v0.6

        dt = mundo.atualizar()

    print("[RENBA] Encerrando — salvando estado e diário...")
    renba.salvar()
    print(f"[RENBA] {renba.memoria}")
    mundo.encerrar()
    print("[RENBA] Até a próxima sessão.")


if __name__ == "__main__":
    main()
