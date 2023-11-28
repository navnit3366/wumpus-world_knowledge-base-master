from environment import WumpusWorld
from environment import size
from environment import player_position
from utilities import possible_actions
from utilities import exclude_walls
from utilities import random


class KnowledgeBase:

    def __init__(self, world: WumpusWorld):

        self.visited = [world.agent]
        self.safe = [world.agent]
        self.limits = list()
        self.danger = list()
        self.unknown = list()

        self.possible_pit = list()
        self.possible_wumpus = list()
        self.no_pits = list()
        self.no_wumpus = list()
        self.max_iterations = 0

        self.get_unknown_positions()

    def get_unknown_positions(self):

        positions = list()

        # Obtém todas as posições do mundo, exceto a que o agente começa
        for x in range(size):
            for y in range(size):
                if [x, y] != player_position:
                    positions.append([x, y])

        self.unknown = positions.copy()

    def tell_perception(self, position, previous_position, perception):

        # Se a posição atual é visitada pela primeira vez, adiciona-se a lista de visitados e zera o contador para continuar a exploração
        if position not in self.visited:
            self.max_iterations = 0
            self.visited.append(position)
        else:
            self.max_iterations += 1

        # Se a posição atual era desconhecida, obviamente ela é conhecida agora
        if position in self.unknown:
            self.unknown.remove(position)

        print('\n')
        print('Posição atual:          ' + str(position))
        print('Percepção atual:        ' + str(perception))
        print('Posições desconhecidas: ' + str(self.unknown))

        # Se o agente caminha para uma parede, este recebe uma percepção de impacto e deve voltar para sua posição anterior
        if perception[3] == 'Impacto':
            self.limits.append(position)
            return 'Volte', self.max_iterations

        if perception[2] == 'Resplendor':
            return 'Ouro', self.max_iterations

        if position not in self.safe:
            self.safe.append(position)

        # Obtém todos os adjacentes da posição atual, excetuando a anterior
        adjacent = possible_actions(position)
        if position != previous_position:
            adjacent.remove(previous_position)

        # Se a percepção atual indica perigo, as posições adjacentes são marcadas indicando os locais onde o agente não poderia se arriscar
        for adj in adjacent:

            # Analisa somente posições interiores ao mundo (Exclui as paredes)
            if exclude_walls(adj, size):

                # Se não há brisa ou fedor, as posições adjacentes são seguras
                if perception[0] == 'Nada' and perception[1] == 'Nada' and adj not in self.safe:
                    self.safe.append(adj)

                if perception[0] == 'Fedor' and adj not in self.safe and\
                        adj not in self.possible_wumpus and adj not in self.no_wumpus:
                    self.possible_wumpus.append(adj)
                if perception[1] == 'Brisa' and adj not in self.safe and\
                        adj not in self.possible_pit and adj not in self.no_pits:
                    self.possible_pit.append(adj)

                # O agente pode descartar possíveis Wumpus e poços em determinadas posições de acordo com percepções anteriores
                if perception[0] == 'Nada' and adj in self.possible_wumpus:
                    self.no_wumpus.append(adj)
                if perception[1] == 'Nada' and adj in self.possible_pit:
                    self.no_pits.append(adj)

        for x in self.no_wumpus:
            if x in self.possible_wumpus:
                self.possible_wumpus.remove(x)

        for x in self.no_pits:
            if x in self.possible_pit:
                self.possible_pit.remove(x)

        print('Possível Poço em:       ' + str(self.possible_pit))
        print('Possível Wumpus em:     ' + str(self.possible_wumpus))
        print('Posições seguras:       ' + str(self.safe))

        return 'Continue', self.max_iterations

    def ask_knowledge_base(self, previous_position, actions):

        prior_1, prior_2, prior_3 = list(), list(), list()

        # Este laço possibilita o agente caminhar para uma parede, recebendo um impacto na percepção
        # Retorna uma ação que garante a segurança do agente, priorizando por posições desconhecidas no mundo
        for action in actions:
            if action in self.unknown and action not in self.possible_wumpus and action not in self.possible_pit:
                prior_3.append(action)

        if prior_3:
            if previous_position in prior_3 and len(prior_3) > 1:
                prior_3.remove(previous_position)
            return random.choice(prior_3)

        # Procura por posições seguras, mas não visitadas
        for action in actions:
            if action in self.safe and action not in self.visited:
                prior_2.append(action)

        if prior_2:
            if previous_position in prior_2 and len(prior_2) > 1:
                prior_2.remove(previous_position)
            return random.choice(prior_2)

        # Por fim, retorna uma posição segura e já visitada, em caso negativo nas 2 condições anteriores
        for action in actions:
            if action in self.safe:
                prior_1.append(action)

        if prior_1:
            if previous_position in prior_1 and len(prior_1) > 1:
                prior_1.remove(previous_position)
            return random.choice(prior_1)

    def shoot_arrow(self):

        # Se existe posições válidas em que o Wumpus pode estar
        if self.possible_wumpus:

            # Se existe mais de uma, o agente escolhe de forma aleatória para onde atirar
            if len(self.possible_wumpus) > 1:
                return random.choice(self.possible_wumpus)

            # Tiro certeiro
            else:
                return self.possible_wumpus[0]
        else:
            return False

    def update_knowledge_base(self, shoot, check):

        # Se o Wumpus foi morto ou não, atualiza-se a base de conhecimento
        if check:
            print('\nO agente atirou a flecha em ' + str(shoot) + ' e MATOU o Wumpus!')

            self.safe.append(shoot)
            self.possible_wumpus.remove(shoot)

            if self.possible_wumpus:
                for position in self.possible_wumpus:
                    if position not in self.possible_pit:
                        self.possible_wumpus.pop(0)
                        self.safe.append(position)
        else:
            if shoot not in self.possible_pit:
                self.possible_wumpus.remove(shoot)
                self.safe.append(shoot)

            print('\nO agente atirou a flecha em ' + str(shoot) + ' e NÃO MATOU o Wumpus!')

        # Continua a exploração
        self.max_iterations = 0
