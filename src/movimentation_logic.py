from knowledge_base import KnowledgeBase
from environment import WumpusWorld
from utilities import possible_actions

# Medida de desempenho
got_gold = 1000
got_killed = -1000
action_exe = -1
arrow_use = -10

# Limite de iterações sem obter novos conhecimentos sobre o ambiente
max_iter = 8


class Exploration:

    def __init__(self, world: WumpusWorld, base: KnowledgeBase):

        self.world = world
        self.base = base
        self.position = world.agent
        self.pointing = 'Direita'
        self.time = 0
        self.points = 0
        self.gold = False
        self.arrow = True
        self.alive = True

        self.previous_position = world.agent
        self.previous_pointing = 'Direita'
        self.wumpus_killed = 0
        self.pits_fallen = 0
        self.arrows_used = 0
        self.total_actions = 0

    def move_agent(self):

        # Primeira iteração: Apenas exibe a percepção recebida pelo agente no início, e realiza algumas deduções
        self.previous_position = self.position
        perception = self.world.get_perception(self.position)
        _, count = self.base.tell_perception(self.position, self.previous_position, perception)

        # Se o agente estagna em busca pelo ouro, a exploração se encerra
        while count < max_iter:

            # Obtém todas as posições adjacentes e pergunta à base de conhecimento qual o melhor movimento
            actions = possible_actions(self.position)
            next_action = self.base.ask_knowledge_base(self.previous_position, actions)

            # Atualiza as posições anterior e atual do agente
            self.previous_position = self.position
            self.position = next_action

            # Se o agente foi para uma posição que contém um poço ou o Wumpus vivo, o jogo encerra
            self.check_alive(self.position)
            if not self.alive:
                self.points += got_killed
                print('\nO agente foi MORTO!')
                break

            # Atualiza a pontuação, direção anterior e atual do agente
            self.previous_pointing = self.pointing
            actual, self.pointing = self.calculate_action(self.previous_position, self.previous_pointing, self.position)
            self.total_actions += actual

            # Obtém a percepção da posição atual do agente
            perception = self.world.get_perception(self.position)

            # Informa à base de conhecimento a percepção atual para inferir possíveis objetos ao redor do agente
            status, count = self.base.tell_perception(self.position, self.previous_position, perception)

            # Caso em que o agente encontra uma parede
            if status == 'Volte':
                self.pointing = self.rotate_180(self.previous_pointing)
                self.position = self.previous_position
                self.total_actions += 3     # Gira 180° e move para frente
                print('\nO agente encontrou uma PAREDE e ficou na posição ' + str(self.position))

            # Caso em que o agente encontra o ouro
            elif status == 'Ouro':
                self.total_actions += 1     # Agarrar o ouro
                self.points += got_gold
                self.gold = True
                break

            # Se o agente não consegue progredir, este tenta atirar a flecha no Wumpus
            if count == max_iter - 1 and self.arrow:
                shoot = self.base.shoot_arrow()

                # Checa se existe uma posição válida para atirar
                if shoot:
                    self.arrow = False
                    self.points += arrow_use
                    check = self.world.kill_wumpus(shoot)
                    self.base.update_knowledge_base(shoot, check)

        # Calcula a pontuação final conforme o número de ações executadas
        self.points += self.total_actions * action_exe

    def check_alive(self, position):

        x, y = position[0], position[1]
        perception = self.world.get_perception(position)

        # Diz se o agente foi morto conforme a posição dada
        if self.world.field[x][y] == 'P':
            self.alive = False
        elif self.world.field[x][y] == 'W' and perception[4] != 'Grito':
            self.alive = False
        elif self.world.field[x][y] == 'O&W' and perception[4] != 'Grito':
            self.alive = False

    @staticmethod
    def rotate_180(previous_pointing):

        if previous_pointing == 'Direita':
            return 'Esquerda'
        elif previous_pointing == 'Esquerda':
            return 'Direita'
        elif previous_pointing == 'Cima':
            return 'Baixo'
        else:
            return 'Cima'

    @staticmethod
    def calculate_action(previous_position, previous_pointing, position):

        pointing = str()
        actions = 1
        x1, y1 = previous_position[0], previous_position[1]
        x2, y2 = position[0], position[1]

        # x da posição atual maior que a anterior --> o agente moveu-se para baixo
        if x2 > x1 and y2 == y1:
            pointing = 'Baixo'

            # Se o agente estava apontando para cima, ele deve rotacionar 2 vezes para apontar para baixo
            if previous_pointing == 'Cima':
                actions += 2
            elif previous_pointing == 'Direita' or previous_position == 'Esquerda':
                actions += 1

        elif x2 < x1 and y2 == y1:
            pointing = 'Cima'

            if previous_pointing == 'Baixo':
                actions += 2
            elif previous_pointing == 'Direita' or previous_position == 'Esquerda':
                actions += 1

        elif x2 == x1 and y2 > y1:
            pointing = 'Direita'

            if previous_pointing == 'Esquerda':
                actions += 2
            elif previous_pointing == 'Cima' or previous_position == 'Baixo':
                actions += 1

        elif x2 == x1 and y2 < y1:
            pointing = 'Esquerda'

            if previous_pointing == 'Direita':
                actions += 2
            elif previous_pointing == 'Cima' or previous_position == 'Baixo':
                actions += 1

        return actions, pointing
