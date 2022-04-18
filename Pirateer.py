import pygame
import sys, os
from pathlib import Path
import numpy as np

WINDOW_WIDTH = 1920
WINDOW_HEIGHT  =1440

FRAMES_PER_SECOND = 30
BASE_PATH = Path(__file__).resolve().parent

class PirateerGame(object):
    ANCHOR = np.array([921, -451])
    DX = np.array([57.4, 58.5])
    DY = np.array([-57.4, 58.5])

    def __init__(self):
        self._set_contsants()
        self.load_images()
        self.initialize_players()

        self.active_player = 1
        self.alive = [True, True, True, True]
        self.color_key = {0:'r', 1:'p',2:'k',3:'g'}

        pygame.init()
        self.load_sounds()
        self.window = pygame.display.set_mode(((WINDOW_WIDTH, WINDOW_HEIGHT)))
        self.clock = pygame.time.Clock()
        self.mouse_chit = None

        self.release_held()

    def _set_contsants(self):
        self.chit_count = 12
        self.keys = {'ESC': 27, 'R': 1073742049, 'r': 114}
        self.cardinal_directions = [np.array(t) for t in  [(0, -1), (1, 0), (0, 1), (-1, 0)]]
        self.tradewind_directions = [np.array(t) for t in  [(1, -1), (-1, 1)]]
        self.map_1 = np.concatenate((
            np.array((PirateerGame.DX,
                      PirateerGame.DY,
                      PirateerGame.ANCHOR)).T,
            np.array([[0, 0, 1]])), axis=0)
        self.map_2 = np.linalg.inv(self.map_1)
        self.valid = PirateerGame.valid_grid()
        self.tradewinds = PirateerGame.tradewinds_grid()

    def advance_turn(self):
        #advance player
        self.active_player += 1
        #self.active_player = 0
        if self.active_player>= len(self.alive):
            self.active_player = 0

        #roll dice
        color = self.color_key[self.active_player]
        self.current_roll = [f'{color}{n}' for n in [np.random.randint(1, 7),
                                                     np.random.randint(1, 7)]]
        self.current_valid_moves=self.get_all_valid_moves()

    def _get_active_player(self):
        return self.players[self.active_player]

    def get_all_valid_moves(self):
        ship_locs = self.get_all_ship_locations()
        player=self._get_active_player()
        valid_moves = {}
        dice=self.current_roll #purely for pycharm debugger visibility
        for s in player.get_ships():
            k1 = tuple(s.position_xy)
            directions = self.cardinal_directions.copy()  # NESW
            starts_on_tradewind = self.pos_is_tradewind(s.position_xy)
            if starts_on_tradewind:
                directions += self.tradewind_directions.copy()

            for step_d in directions:  # test each direction
                for die in self.current_roll:
                    dist = int(die[1:])
                    can_move = True
                    lands_on = None
                    for i in range(dist):
                        spot = s.position_xy+step_d*(i+1)


                        #test map validity
                        if np.max(spot) >= 20 or np.min(spot) < 0 or not self.valid[spot[0],spot[1]]: #map spot invalid
                            can_move=False
                            break
                        #test tradewind crossing
                        if i < dist-1:# Not destination
                            if self.pos_is_tradewind(spot) and not starts_on_tradewind:
                                can_move = False
                                break

                        #test other ships
                        if tuple(spot) in ship_locs.keys():
                            if i < dist-1: #cannot pass ship
                                can_move = False
                                break
                            else: #lands on ship
                                lands_on=ship_locs[tuple(spot)]
                                if lands_on == self.active_player:
                                    can_move = False
                                    break
                        #test moving backward with the trasure

                    if can_move:
                        #valid moves make it to here
                        #spot was left at destination
                        if not k1 in valid_moves.keys():
                            valid_moves[k1]={}
                        if not die in valid_moves[k1]:
                            valid_moves[k1][die] = []
                        valid_moves[k1][die].append([spot, lands_on])
        x=561
        #deal with using both dice later

        return valid_moves




    def pos_is_tradewind(self, pos):
        return self.tradewinds[pos[0],pos[1]]

    def get_all_ship_locations(self):
        positions = {}
        for p in self.players:
            for s in p.get_ships():
                positions[tuple(s.position_xy)]=p.position
        return positions

    def load_sounds(self):
        sounds = {}
        for i in range(4):
            p = f'{BASE_PATH}/sounds/Die_roll_{i}.wav'
            print(os.path.exists(p))
            sounds[f'Die_roll_{i}'] = pygame.mixer.Sound(p)
        self.sounds = sounds

    def load_images(self):
        board_image = pygame.image.load(f'{BASE_PATH}/images/board2.png')
        chit_a1 = pygame.image.load(f'{BASE_PATH}/images/chit_a.png')
        chit_b1 = pygame.image.load(f'{BASE_PATH}/images/chit_b.png')
        chit_c1 = pygame.image.load(f'{BASE_PATH}/images/chit_c.png')
        chit_d1 = pygame.image.load(f'{BASE_PATH}/images/chit_d.png')
        highlight_image_p = pygame.image.load(f'{BASE_PATH}/images/highlight_pink.png')
        highlight_image_g = pygame.image.load(f'{BASE_PATH}/images/highlight_green.png')

        self.chit_dimensions = np.array(chit_a1.get_size())
        self.images = {
            'board_image':board_image,
            'chit_a1':chit_a1,
            'chit_b1': chit_b1,
            'chit_c1': chit_c1,
            'chit_d1': chit_d1,
            'spot_pink':highlight_image_p,
            'spot_green': highlight_image_g
          }
        d_add ={}

        #add_faded images
        for k in self.images:
            if k.startswith('chit'):
                im_copy = self.images[k].copy()
                im_copy.set_alpha(128)
                d_add[f'{k}_fade'] = im_copy
        self.images = {**self.images, **d_add}


        for k in [f'die_r{i+1}' for i in range(6)]:
            self.images[k] = pygame.image.load(f'{BASE_PATH}/images/{k}.png')
        for k in [f'die_k{i+1}' for i in range(6)]:
            self.images[k] = pygame.image.load(f'{BASE_PATH}/images/{k}.png')
        for k in [f'die_g{i+1}' for i in range(6)]:
            self.images[k] = pygame.image.load(f'{BASE_PATH}/images/{k}.png')
        for k in [f'die_p{i+1}' for i in range(6)]:
            self.images[k] = pygame.image.load(f'{BASE_PATH}/images/{k}.png')

    def Board_to_pix(self,x,y):
        #Maps
        # 0, 9 to 400, 88
        # 9, 0 to 1430, 88
        # 19, 10 to 1430, 1258
        # 10, 19 to 400, 1258
        return (self.map_1 @ np.array([x,y,1]))[:2]

    @staticmethod
    def tradewinds_grid():
        tw = np.zeros((20, 20), dtype=bool)
        #Ship(16, 7), Ship(7, 16)
        for i in range(7,17):
            tw[i, 23 - i]=True
        #Ship(3, 12), Ship(12, 3)
        for i in range(3, 13):
            tw[i, 15 - i] = True

        return tw

    @staticmethod
    def valid_grid():
        valid = 1 - np.zeros((20, 20), dtype=bool)
        valid[:9 , 0]=False
        valid[15:, 0] = False
        valid[:13, 1] = False
        valid[15:, 1] = False
        valid[:12, 2] = False
        valid[15:, 2] = False
        valid[8, 2] = True
        valid[:4, 3] = False
        valid[16:, 3] = False
        valid[17:, 4] = False
        valid[15, 4] = False

        valid[18, 7] = False
        valid[17:19, 8] = False
        valid[9:11, 9] = False
        valid[17:19, 9] = False
        valid[9:11, 10] = False
        valid[17:19, 10] = False
        valid[18:, 11] = False
        valid[17:, 12] = False
        valid[17:, 13] = False
        valid[17:, 14] = False
        valid[17:, 15] = False
        valid[16:, 16] = False
        valid[17:, 17] = False
        valid[18:, 18] = False
        valid[19:, 19] = False

        for i in range(20):
            for j in range(i,20):
                valid[i,j]=valid[j,i]
        return valid

    def initialize_players(self):
        self.players=[Player(0, self.images['chit_a1'], self.images['chit_a1_fade']),
                      Player(1, self.images['chit_b1'], self.images['chit_b1_fade']),
                      Player(2, self.images['chit_c1'], self.images['chit_c1_fade']),
                      Player(3, self.images['chit_d1'], self.images['chit_d1_fade'])]


    def mouse_to_grid(self, pos):
        # offset accounts for center of chit image and teh 3d perspective offset
        offset = -1 * self.chit_dimensions / 2 - PirateerGame.DY * .18
        x, y = pos + offset
        g_pt = (self.map_2 @ np.array([x, y, 1]))[:2]
        g_pt = np.round(g_pt).astype(int)
        if np.min(g_pt) > -.5 and np.max(g_pt) < 19.5:
            return g_pt
        else:
            return None

    def _evt_mouse_move(self, d):
        self.mouse_chit = self.mouse_to_grid(d['pos'])
        self.mouse_piece_pos = d['pos']-np.array([25,25])

    def release_held(self):
        self.held_piece = [None] * 3

    def execute_move(self, die, ship, destination):
        ship.position_xy=destination
        self.current_roll.pop(self.current_roll.index(die))
        self.current_valid_moves = self.get_all_valid_moves()



    def _evt_mouse_click(self, d, evt):
        button = d['button']
        down = evt.type == pygame.MOUSEBUTTONDOWN
        grid_pos = self.mouse_to_grid(d['pos'])
        if grid_pos is None:return

        if not down:
            if self.held_piece[0] is not None:
                #test for valid move
                x = 561
                grid_pos_array = np.array(grid_pos)
                ship = self.held_piece[2]
                pos_key = tuple(ship.position_xy)
                if pos_key in self.current_valid_moves:
                    d = self.current_valid_moves[pos_key]
                    for die_k in d:
                        for dest in d[die_k]:
                            if not np.any(grid_pos_array-dest[0]):
                                #found it!
                                x = 561
                                print("Valid Move detected")
                                self.execute_move(die_k, ship, grid_pos_array)
                self.release_held()
            else:
                #print(f"Mouse up: {grid_pos}")
                ships = self._get_active_player().get_ships()
                selected_ship = None
                for idx, s in enumerate(ships):
                    if not np.any(s.position_xy-grid_pos):
                        selected_ship = s
                        break
                if selected_ship is not None:
                    self.held_piece = [self.active_player, idx, selected_ship]
                print(selected_ship)

        else:
            #self.held_piece = self.release_held()
            #print(f"Mouse up: {grid_pos}")
            #check if we moved something
            pass


    def die_coords(self,player):
        if player ==0:
            return 40, 100, 150, 30
        elif player ==1:
            return 40, 1160, 160, 1220
        elif player ==2:
            return 1770, 1160, 1650, 1220
        elif player ==3:
            return 1770, 100, 1650, 40

    def game_loop(self):
        g_map = self.Board_to_pix
        self.current_roll = []
        self.current_valid_moves = {}
        while True:
            self.window.blit(self.images['board_image'], (0, 0))

            for player in self.players:
                for ship in player.get_ships():
                    if self.held_piece[2] == ship:
                        self.window.blit(ship.image_fade, g_map(*ship.position_xy))
                    else:
                        self.window.blit(ship.image, g_map(*ship.position_xy))
            #draw dice
            x1,y1,x2,y2 = self.die_coords(self.active_player)
            if len(self.current_roll) > 0:
                self.window.blit(self.images[f'die_{self.current_roll[0]}'], (x1, y1))
            if len(self.current_roll) > 1:
                self.window.blit(self.images[f'die_{self.current_roll[1]}'], (x2, y2))

            #self.window.blit(self.images['die_b1'], (100,100))
            #self.window.blit(self.images['die_b2'], (250, 100))
            #self.window.blit(self.images['die_b3'], (400, 100))
            #self.window.blit(self.images['die_b4'], (550, 100))
            #self.window.blit(self.images['die_b5'], (700, 100))
            #self.window.blit(self.images['die_b6'], (850, 100))


            for event in pygame.event.get():
                if event.type== pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYUP:
                    self.manage_keystroke(event)

                elif event.type == pygame.MOUSEMOTION:
                    self._evt_mouse_move(event.dict)
                elif event.type in [pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN]:
                    self._evt_mouse_click(event.dict, event)
                else:
                    #print(event)

                    pass
            if False:
                for i in range(20):
                    for j in range(20):
                        if self.valid[i,j]:
                            self.window.blit(self.images['spot_pink'], self._spot_map(i,j))
            if self.mouse_chit is not None:
                i = int(self.mouse_chit[0] + .5)
                j = int(self.mouse_chit[1] + .5)
                if self.valid[i, j]:
                    self.window.blit(self.images['spot_pink'], self._spot_map(i,j))
            for p_tup in self.current_valid_moves:
                for die in self.current_valid_moves[p_tup]:
                    for move in self.current_valid_moves[p_tup][die]:
                        self.window.blit(self.images['spot_green'], self._spot_map(move[0][0],move[0][1]))

            #draw held piece
            if self.held_piece[0] is not None:
                self.window.blit(self.held_piece[2].image, self.mouse_piece_pos)

            pygame.display.update()
            self.clock.tick(FRAMES_PER_SECOND)

    def _spot_map(self,i,j):
        return self.Board_to_pix(i, j) + PirateerGame.DY * .16 + PirateerGame.DX * .09

    def manage_keystroke(self, event):
        if event.key == self.keys['ESC']:
            print(event)
            pygame.quit()
            sys.exit()
        elif event.key in [self.keys['R'], self.keys['r']]:
            self.advance_turn()
            self.sounds[f'Die_roll_{np.random.randint(0,4)}'].play()

        else:
            print(event.key)

class Player(object):
    def __init__(self, position = 0, image=None, image_fade = None):
        self.position = position
        if position == 0:
            self.ships = [Ship(0,9),Ship(0,10),Ship(0,11)]
        elif position == 1:
            self.ships = [Ship(10,19),Ship(9,19),Ship(8,19)]
        elif position == 2:
            self.ships = [Ship(19, 10), Ship(19, 9), Ship(19, 8)]
            self.ships = [Ship(3, 12), Ship(14, 12), Ship(9, 7)]
        elif position == 3:
            self.ships = [Ship(9, 0), Ship(10, 0), Ship(11, 0)]
        for s in self.ships:
            s.set_images(image, image_fade)

    def get_ships(self):
        return self.ships

class Ship(object):
    def __init__(self, x, y):
        self.position_xy = np.array([x,y])
        self.image = None

    def set_images(self, image, image_fade):
        self.image= image
        self.image_fade = image_fade

x =PirateerGame().game_loop()