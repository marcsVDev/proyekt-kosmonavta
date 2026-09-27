# Arquitetura atual

## Visão geral

`src/game.py` cria duas cenas de jogo, `menu` e `game`, e controla a cena
independente `credits`. O loop roda a 60 FPS, coleta
eventos do Pygame, delega atualização/desenho à cena ativa e apresenta o frame.
O delta de tempo é convertido para segundos e entregue aos sistemas e entidades.

```text
Game
 ├─ Scene(menu): fundo, título e Play
 ├─ Credits: cartões pré-renderizados, sprites animados, nave visual controlável e rolagem por delta
 ├─ RunState: HP e derrota da campanha
 └─ Scene(game)
     ├─ Progression: escolhe e avança fases
     ├─ WaveSystem: agenda e conclui ondas
     ├─ BossFightSystem: dirige exclusivamente a Órbita de Marte
     ├─ entidades: Player, Enemy, Background, scrollers, projéteis
     └─ UI: título da fase e estado de onda
```

## Ciclo de fases

Ao iniciar, `Game.play()` emite `GAME_STARTED`, carrega a primeira `Phase` e
troca para a cena de jogo. `Progression` mantém o índice da campanha. Cada
fase fornece entidades padrão, ondas opcionais, duração e `free_movement`.

`Game.load_phase()` limpa a cena anterior, adiciona as entidades da nova fase,
aplica a permissão de movimento ao jogador e entrega a fase ao `WaveSystem` ou
ao `BossFightSystem`. Todas as instâncias de `Player` recebem o mesmo
`RunState`, portanto a troca de fase não cura Valentina. Na Órbita, somente o
diretor do boss emite `PHASE_COMPLETED`, após a animação de derrota da
Nave-Mãe. Depois da sexta fase, `Progression` emite `GAME_COMPLETED`.
Nesse evento, `Game` abre `Credits`; Ctrl+Shift+C na tela inicial usa o mesmo componente.
`Credits` carrega os recursos uma vez, mantém as atribuições da equipe em
`src/ui/credits.py` e volta ao menu com Esc ou ao tocar Marte no encerramento. A nave
dos créditos usa os comandos de movimento do jogo, sem participar da cena de
combate ou receber dano. Marte ocupa a largura da tela e rola junto com os
cartões, após um intervalo amplo desde o último cartão. Enquanto a rolagem
continua, um limite móvel mantém a nave afastada de Marte. Ao parar, o limite
é liberado e um contato da nave com Marte encerra a cena.

Entre duas fases, `Game` pausa a atualização da cena por 1 s e mantém o frame
preto. A música ambiente é substituída por `musicfinal.mp3` ao entrar na
Órbita de Marte e restaurada ao sair da luta ou voltar ao menu.

Para cenas sem ondas, `duration` é a contagem até a conclusão. Em fases de
combate, o sistema inicia a primeira onda após 2 s e troca de onda após o
`rest` configurado em cada `Wave`.

## Atualização de cena

Em cada frame, `Scene.run()` executa, nesta ordem:

1. sistemas;
2. entidades;
3. remoção das entidades marcadas para destruição;
4. colisões, apenas na cena de jogo;
5. atualização da UI;
6. desenho de entidades e UI.

`Scene` mantém listas de entidades, inimigos e itens de UI, uma referência ao
jogador e uma blackboard por nome. O método `clear_scene()` destrói entidades
antes de limpar as coleções, importante para desconectar eventos e parar sons.

## Entidades e colisão

`Entity` define o contrato mínimo de atualização, desenho e destruição.
`Character` acrescenta sprite animado, escala, rotação e colisor. `Player` lê
WASD ou setas direcionais, limita sua posição à tela e aceita acelerações externas via
`apply_force`. `Enemy` executa uma sequência de padrões e pode receber um
ataque independente.

Antes do teste SAT, a cena faz uma triagem por alcance. Em seguida,
`Collidable` usa os vértices poligonais já rotacionados. Inimigos, projéteis,
raios e a Nave-Mãe que tocam o jogador geram uma única ocorrência de
`PLAYER_COLLIDE` por frame. `Player` consulta o `RunState`, aplica um ponto de
dano e abre a janela de invulnerabilidade. O míssil teleguiado usa resolução
especial e contínua, priorizando casco da Nave-Mãe, nave laser, jogador e
inimigo menor. Uma entidade sem vértices não participa da colisão comum.

## Ondas, padrões e ataques

`Wave` contém `EnemySpawn`s e intervalo de descanso. Cada spawn descreve uma
chave de inimigo e factories de movimento e ataque. `EnemyRegistry` resolve a
chave para uma classe concreta e constrói uma instância isolada: padrões e
ataques não podem compartilhar estado entre spawns.

`WaveSystem` mantém spawns pendentes e inimigos ativos. Ele passa um provider
da posição do jogador aos padrões para que investidas e mira não dependam da
cena. A onda termina quando não há pendências, inimigos ativos nem projéteis
vivos; ao fim da última onda, a fase é concluída.

Os builders de `src/enemys/behaviors.py` produzem as formações usadas pela
campanha. Os padrões ficam em `src/enemys/patterns/` e os ataques em
`src/enemys/attacks.py`. Consulte [enemy-waves.md](enemy-waves.md) para o
catálogo e instruções de extensão.

## Eventos

O `EventBus` é um canal simples de assinaturas em memória. Além dos eventos de
campanha e onda, publica `RUN_RESET`, `PLAYER_DAMAGED`, `PLAYER_DIED`,
`BOSS_STARTED`, `BOSS_DAMAGED` e `BOSS_DEFEATED`. Eventos terminais possuem
guardas para serem emitidos uma única vez.

## Sistema da Nave-Mãe

`MotherShipEnemy` mantém a integridade e os cinco alvos lógicos, sem conhecer a
cena ou o agendamento. `GuidedMissile` contém direção, aceleração, limite de
giro, armamento, teste do segmento percorrido e resultado único de explosão.
`BossFightSystem` abre alvos, cria inimigos pelo `EnemyRegistry`, limita ameaças,
executa as sete ondas e volta da sétima para a segunda. As configurações de
vida, chefe, míssil, gaivota-robô e laser são dataclasses imutáveis.

## Recursos e testes

Os caminhos de recursos são centralizados em `src/game_consts.py`; `assets/`
contém sprites, cenários, UI, fontes e SFX. Os testes em `tests/` usam SDL
dummy e cobrem navegação, progressão, ondas, padrões e novas mecânicas de
inimigos. Execute-os com:

```powershell
python -B -m unittest discover -s tests -v
```
