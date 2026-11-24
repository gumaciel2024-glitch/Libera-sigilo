# SAJ — Remoção de sigilo de decisões

Aplicação local para Windows. Após abrir os autos e fechar **Pendências**, o robô localiza os rótulos na árvore de documentos e clica em **Peças sigilosas**, **Decisão**, no cadeado e em **Remover sigilo**. A busca aceita uma única correspondência visível para **Decisão** na faixa recuada abaixo da seção. Se um alvo estiver ausente ou houver mais de uma correspondência, o robô para e registra a etapa. Petições ficam fora do fluxo.

## Instalação e atualização

Extraia o projeto, execute `instalar.bat` com Python 3.11 ou superior instalado e abra `iniciar.bat`. Ao atualizar uma instalação existente, preserve `calibracao.json`, `imagens/` e `dados/`. Mantenha apenas um robô do SAJ em execução.

Preencha `modelo_planilha.xlsx` com o número completo em formato Texto e o status **REMOVER SIGILO**. Escolha a planilha e clique em **Conferir planilha**.

## Calibração de imagens

Use o SAJ maximizado na resolução, escala e largura de painéis que usará na execução. As calibrações anteriores de navegação, pendências, cadeado e menu podem ser reaproveitadas. Cadastre os três itens novos em **Calibrar imagens**.

1. **Área da árvore de documentos.** Arraste do canto superior esquerdo até o canto inferior direito da lista superior de documentos. A seleção deve incluir as linhas que aparecem após rolar a lista e terminar acima de **Peças aguardando liberação**.
2. **Peças sigilosas.** Recorte apenas o texto do rótulo, sem ícone nem botão +/−. Clique no centro do texto recortado para marcar o ponto de ação.
3. **Decisão.** Com **Peças sigilosas** aberta, recorte apenas o texto **Decisão** da linha recuada dentro dela. Deixe outra linha selecionada durante a captura para o texto aparecer sem o realce azul. Clique no centro do texto recortado.

O robô busca os rótulos verticalmente dentro da área marcada e usa a posição horizontal da calibração para distinguir a decisão recuada das decisões no nível principal. Se a seção estiver recolhida, usa a seta à direita após clicar no rótulo. Para liberar em lote, são necessárias também as imagens **Limpar** e **Processo vazio**.

## Execução

1. Deixe **Remover sigilo** desmarcado, escolha uma linha e clique em **Executar selecionado** para ensaiar. Volte ao SAJ em cinco segundos. O ensaio para com o menu do cadeado aberto.
2. Para a execução real, marque **Remover sigilo**. O robô envia o clique final e segue para a próxima linha sem uma tela de confirmação ou checagem do resultado após o clique.
3. O resultado **Clique em Remover sigilo enviado** registra o clique, cuja efetivação depende do SAJ. Se um alvo não puder ser localizado, a tabela e o registro do aplicativo mostram onde o lote parou.

O histórico registra a tentativa antes da navegação e a solicitação antes do clique final. Uma falha da versão anterior ao ler a árvore pelo Windows pode ser tentada de novo automaticamente quando o histórico não registra uma solicitação de remoção. Para repetir após um ensaio ou outra interrupção, confira primeiro o SAJ, feche o app, faça uma cópia de `dados/historico.jsonl` e remova do histórico de trabalho somente as entradas do processo revisado. Para interromper a automação, mova o ponteiro ao canto superior esquerdo.
