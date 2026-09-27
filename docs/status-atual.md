# Visão do jogo e estado atual

## Proposta

Em plena Guerra Fria, os Estados Unidos chegam primeiro à Lua. Inconformado,
o coronel Dmitri Petrovitch ordena uma missão soviética ainda mais ambiciosa:
alcançar Marte. Ele escolhe Valentina Tereshkova para uma missão que espera que
seja suicida. Valentina sobrevive à viagem, chega ao planeta vermelho e
transforma a sentença de morte em uma conquista impossível.

O jogo é um shooter arcade inspirado em *Space Invaders*, com padrões de
inimigos e um confronto de chefe antes da chegada a Marte. Nas fases de
travessia, a nave de Valentina se move nos dois eixos enquanto o cenário rola
verticalmente, transmitindo a subida e o afastamento da Terra.

## Jornada da campanha

| Fase | Papel na proposta | Estado no código |
| --- | --- | --- |
| Estação de Lançamento — Estação Krasny Mir | Apresentação e lançamento | Implementada com botão de lançamento e animação de fumaça, sem nave jogável na cena. |
| Estratosfera | Gaivotas e asteroides | Implementada com fundo rolável, ondas de gaivotas, chuva de asteroides e cutscene de saída. |
| Espaço Próximo | Satélite quebrado, Buran e drones | Implementada com drones, satélite direcionado ao jogador, rasantes do Buran, Terra e fundo rolável. |
| Espaço Profundo | Drones e minas espaciais | Implementada com drones, drones do mal com raio giratório e minas gravitacionais. |
| Órbita de Marte | Nave-mãe, gaivotas-robô, escoltas, lasers e mísseis | Boss fight implementada com sete ondas temporais e repetição das ondas 2–7. |
| Chegada a Marte | Desfecho da missão | Diálogo de aproximação, pouso de cerca de 12 s, falas após o pouso e créditos; movimento bloqueado. |

As fases são declaradas em `src/initializations/phases.py`. A lista
`planned_enemies` registra o conteúdo previsto, mas não o instancia.

## O que está jogável

- Menu inicial com botão Play, atalho Enter e Ctrl+Shift+C para abrir os créditos.
- Música ambiente na campanha, trilha própria durante a boss fight, efeitos de
  motor e efeitos de inimigos existentes.
- Transição preta de 1 s entre fases, com a cena pausada durante a troca; a saída da Estratosfera e o pouso em Marte exibem seus spritesheets antes da progressão. O pouso termina com novas falas e os créditos.
- Campanha linear com seis fases; Krasny Mir mostra o primeiro quadro da
  animação de lançamento parado e o botão no canto inferior direito até o
  clique, então reproduz a animação e avança. As demais fases avançam por
  duração, ondas ou chefe.
- Diálogos narrativos nas seis fases, carregados de
  `assets/dialogues/campaign.json`, com nome, retrato disponível, efeito de
  digitação e paginação automática. A ação fica pausada enquanto o painel está
  aberto; Espaço ou clique esquerdo completa/avança a fala. Ctrl+Shift+P pula todas
  as falas da cena atual, inclusive as que aparecem após uma cutscene, mantendo
  a animação e os eventos de conclusão.
- Movimento da nave com `W`, `A`, `S` e `D`, aceleração, desaceleração,
  inclinação visual e limites da tela.
- Fundos fixos/roláveis; a Estratosfera, o Espaço Próximo e os placeholders das
  duas fases posteriores passam uma sensação de deslocamento vertical.
- Vida global de 10 HP, preservada entre fases, com 1,5 s de invulnerabilidade,
  pisca, knockback, barra por cores e no máximo um dano por frame.
- Tela de derrota com reinício da campanha por Enter e retorno ao menu por Esc.
- Colisão poligonal entre jogador, inimigos, projéteis, raios e a Nave-Mãe.
- Gaivotas, gaivotas-robô, drones, naves laser, drones do mal, asteroides,
  satélite quebrado, minas espaciais, alienígenas e Nave-Mãe.
- Formações, investidas, perseguição, passagens rápidas, órbitas, zigue-zague,
  chuva de asteroides e minas que atraem a nave.
- Avisos de perigo usam o sprite animado de alerta a 12 fps; rasantes de alien e
  Buran sinalizam na borda e na altura exata da entrada antes de cruzarem a tela.
- O Buran também faz rasantes pela borda inferior, alternando os lados; ficar
  parado embaixo não evita o contato com a nave.
- Os drones da pinça orbital perseguem a posição atual do jogador dentro de
  margens visíveis, sem atravessar os limites da tela.
- Mísseis do chefe perseguem pelo menor ângulo, com giro limitado a 240°/s;
  quando armados, causam dano ao colidir com qualquer ponto do casco, inclusive
  nas bordas. A Nave-Mãe pisca ao receber o impacto.
- Ao concluir Marte, entram créditos comemorativos com as seis etapas, citações
  verificadas, distinção entre a missão fictícia e as conquistas reais, equipe
  e fontes. A rolagem desce com delta time; Espaço ou Shift acelera e Esc retorna
  ao menu. Marte ocupa toda a largura da tela e entra pela mesma rolagem dos
  cartões, com um intervalo amplo depois que o último texto sai da tela.
  Durante a rolagem, um limite acompanha Marte e impede a nave de alcançá-lo.
  Quando a rolagem para, a nave pode tocar Marte no alto para encerrar os
  créditos. A nave pode ser pilotada com WASD ou setas, sem colisões de combate
  ou dano, e aparece à frente dos cartões. O fundo é preto; os cenários dos
  cartões são estáticos.
- Retorno ao menu com Esc, limpando a cena e recriando a campanha para uma
  nova partida.

## Limitações atuais

- Não há disparo, pontuação ou itens coletáveis; Valentina derrota a Nave-Mãe
  somente atraindo mísseis armados para o alvo vulnerável.
- A cutscene e o encerramento de chegada a Marte estão implementados; não há exploração após o pouso.
- Espaço Profundo e Órbita de Marte reutilizam o cenário de Espaço Próximo.
- Petrovitch e o Comando usam retratos no painel de diálogo.
- As velocidades e janelas do boss, incluindo o giro ajustado do míssil, ainda
  precisam de playtest humano para ajuste fino de corredores e duração média.

## Prioridades sugeridas

1. Fazer playtest humano das sete ondas do boss e ajustar apenas as dataclasses
   de balanceamento.
2. Criar os cenários próprios de Espaço Profundo, Órbita e chegada a Marte.
3. Criar os retratos de Petrovitch e do Comando para completar os diálogos.
4. Fazer playtest dos rasantes do Buran e da trajetória do satélite contra a posição do jogador.

## Referência de controles

| Ação | Tecla |
| --- | --- |
| Iniciar no menu | Enter ou botão Play |
| Lançar em Krasny Mir | Botão de lançamento |
| Mover a nave | W, A, S, D ou setas direcionais |
| Voltar ao menu durante a campanha | Esc |
| Abrir créditos no menu | Ctrl+Shift+C |
| Acelerar os créditos | Segurar Espaço ou Shift |
| Mover a nave nos créditos | W, A, S, D ou setas direcionais |
| Voltar ao menu nos créditos | Esc; tocar Marte depois da rolagem também encerra os créditos |
| Avançar diálogo, quando usado | Espaço ou clique esquerdo |
| Pular todos os diálogos da cena atual | Ctrl+Shift+P |
| Ativar/desativar God Mode | Ctrl+Shift+O |

O God Mode é uma ferramenta de teste: permanece ativo durante as trocas de
fase, desativa as colisões do jogador e impede sua destruição. Pressione a
combinação novamente para voltar ao comportamento normal.
