# SAJ — Remoção de sigilo de decisões

Aplicação local para Windows. O lote é acompanhado e trata uma decisão sigilosa por processo. Se houver várias decisões ou se a conferência for inconclusiva, use **Cancelar** para interromper. Petições ficam fora deste fluxo.

## Instalação

Extraia o ZIP em uma pasta própria, execute `instalar.bat` com Python 3.11 ou superior instalado e abra `iniciar.bat`. Mantenha apenas um robô do SAJ em execução.

## Planilha e calibração

Preencha `modelo_planilha.xlsx` com o número completo em formato Texto e o status **REMOVER SIGILO**. Escolha a planilha e clique em **Conferir planilha**.

Em **Calibrar imagens**, capture as referências na sua estação. Use o SAJ maximizado e mantenha a mesma escala, resolução e largura dos painéis. Na árvore, capture apenas o texto de **Peças sigilosas** e o texto **Decisão**, com a decisão selecionada em destaque. Para o cadeado, use o ícone habilitado. Para **Remover sigilo**, abra o menu e tire o ponteiro de cima da opção antes da captura. Defina como ponto de clique o centro da opção. As referências **Limpar** e **Processo vazio** são necessárias para dois ou mais processos.

## Ensaio e remoção

1. Com **Remover sigilo** desmarcado, selecione uma linha pronta e clique em **Executar selecionado**. Volte à tela inicial do SAJ em cinco segundos.
2. Na conferência, alterne para o SAJ, verifique os 20 dígitos e selecione a decisão dentro de **Peças sigilosas**. Volte à confirmação. Escolha **Sim** se houver uma única decisão sigilosa e ela estiver selecionada, **Não** se o processo conferido não tiver decisão sigilosa, ou **Cancelar** em caso de dúvida ou várias decisões.
3. Após responder, volte aos autos em cinco segundos. O ensaio abre o menu do cadeado. A janela do aplicativo pode cobrir parte do SAJ ao encerrar.
4. Para a execução real, marque **Remover sigilo**. O clique nessa opção no SAJ é imediato. Vá ao SAJ, confirme visualmente que a decisão saiu da seção e responda **Sim** na conferência. Se houver outro processo, volte aos autos em cinco segundos para continuar o lote.

O histórico em `dados/historico.jsonl` registra a tentativa antes da navegação e a solicitação antes do clique. Processos já tentados ficam bloqueados. Para repetir após um ensaio ou interrupção, confira primeiro o SAJ, feche o app, faça uma cópia do histórico e remova do histórico de trabalho somente as entradas do processo revisado.

Use **Cancelar** durante as conferências. Durante o movimento automático do mouse, leve o ponteiro ao canto superior esquerdo para interromper. A aplicação precisa de validação acompanhada no Windows e no SAJ antes de uso real.
