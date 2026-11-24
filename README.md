# SAJ — Remoção de sigilo de decisões

Aplicação local para Windows. O robô verifica automaticamente o número completo do processo e a posição da decisão na árvore de documentos. Trata uma única decisão por processo. Quando encontra mais de uma, interrompe o lote e registra o motivo na interface e no histórico. Petições ficam fora deste fluxo.

## Instalação e atualização

Extraia o projeto, execute `instalar.bat` com Python 3.11 ou superior instalado e abra `iniciar.bat`. Se já usava o robô, execute `instalar.bat` novamente para instalar a biblioteca de acessibilidade do Windows. Preserve seu histórico e sua calibração ao atualizar a pasta existente. Mantenha apenas um robô do SAJ em execução.

## Planilha e calibração

Preencha `modelo_planilha.xlsx` com o número completo em formato Texto e o status **REMOVER SIGILO**. Escolha a planilha e clique em **Conferir planilha**. Em **Calibrar imagens**, capture os controles de navegação, o cadeado habilitado e a opção inteira **Remover sigilo**, sem realce. Indique o centro da opção como ponto de clique. As referências **Limpar** e **Processo vazio** são necessárias para lotes com mais de um processo. Mantenha a resolução, a escala e os painéis usados na calibração.

## Execução

1. Deixe **Remover sigilo** desmarcado e clique em **Executar selecionado** para ensaiar. Volte ao SAJ em cinco segundos. O robô abre os autos, verifica o número completo, expande **Peças sigilosas** quando existir e seleciona a única **Decisão** diretamente dentro dessa seção. O ensaio para com o menu do cadeado aberto.
2. Para a execução real, marque **Remover sigilo**. Se houver uma única decisão sigilosa, o robô seleciona a peça, abre o cadeado e clica em **Remover sigilo**. Antes de avançar, verifica se a decisão saiu da seção e se apareceu uma decisão a mais no nível principal da árvore. O robô pula processos em que consegue ler a árvore e não encontra decisão sigilosa. O resultado aparece na tabela e no registro do aplicativo.
3. O robô tenta ler a árvore de documentos pelo controle nativo do Windows (Win32) e, quando necessário, pela interface de acessibilidade (UI Automation). A etapa de seleção usa um clique na linha da decisão. Se a árvore, a identidade do processo, a seleção ou o resultado ficarem inconclusivos, o lote para e registra a etapa. Valide com um ensaio na sua estação antes de executar a remoção real.

O histórico em `dados/historico.jsonl` registra a tentativa antes da navegação e a solicitação antes do clique final. Processos já tentados ficam bloqueados. Para repetir após um ensaio ou interrupção, confira primeiro o SAJ, feche o app, faça uma cópia do histórico e remova do histórico de trabalho somente as entradas do processo revisado. Para interromper a automação, mova o ponteiro ao canto superior esquerdo.
