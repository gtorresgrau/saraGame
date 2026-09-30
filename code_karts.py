"""
Code Karts - Juego de programación visual con un ratón
El jugador arrastra bloques de comandos para guiar al ratón hasta el queso,
evitando la trampa de ratones.
"""

import pygame
import sys

# Inicializar pygame
pygame.init()

# Constantes
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
CELL_SIZE = 60
GRID_COLS = 10
GRID_ROWS = 8
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 80

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (240, 240, 240)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
BROWN = (139, 69, 19)
CREAM = (255, 248, 220)
WALL_COLOR = (70, 70, 70)
PATH_COLOR = (245, 245, 220)

# Colores de bloques
BLOCK_COLORS = {
    'adelante': (76, 175, 80),    # Verde
    'atras': (244, 67, 54),       # Rojo
    'izquierda': (33, 150, 243),  # Azul
    'derecha': (255, 152, 0),     # Naranja
}

# Laberinto (1 = pared, 0 = camino)
MAZE = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Posiciones especiales
MOUSE_START = (1, 1)  # (col, fila)
CHEESE_POS = (8, 5)   # (col, fila)
TRAP_POS = (5, 3)     # (col, fila)

# Direcciones
DIRECTIONS = {
    'adelante': (0, -1),
    'atras': (0, 1),
    'izquierda': (-1, 0),
    'derecha': (1, 0),
}

# Tamaños de bloques
BLOCK_WIDTH = 100
BLOCK_HEIGHT = 50
PALETTE_X = 700
PALETTE_Y = 100
PROGRAM_X = 700
PROGRAM_Y = 400
MAX_COMMANDS = 8


class Block:
    """Bloque de comando arrastrable"""
    def __init__(self, command_type, x, y, in_palette=True):
        self.command_type = command_type
        self.x = x
        self.y = y
        self.in_palette = in_palette
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.width = BLOCK_WIDTH
        self.height = BLOCK_HEIGHT

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, font):
        rect = self.get_rect()
        color = BLOCK_COLORS[self.command_type]
        
        # Sombra
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, DARK_GRAY, shadow_rect, border_radius=8)
        
        # Bloque principal
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, rect, width=2, border_radius=8)
        
        # Texto
        text = font.render(self.command_type.upper(), True, WHITE)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def is_clicked(self, pos):
        return self.get_rect().collidepoint(pos)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Code Karts - El Ratón y el Queso")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 16, bold=True)
        self.title_font = pygame.font.SysFont('Arial', 28, bold=True)
        self.big_font = pygame.font.SysFont('Arial', 36, bold=True)
        
        self.reset_game()

    def reset_game(self):
        """Reiniciar el estado del juego"""
        self.mouse_pos = list(MOUSE_START)
        self.program = []  # Lista de comandos en el área de programa
        self.palette_blocks = self.create_palette()
        self.running = False
        self.won = False
        self.lost = False
        self.executing = False
        self.current_command_index = 0
        self.move_timer = 0
        self.message = ""
        self.message_timer = 0

    def create_palette(self):
        """Crear los bloques de la paleta"""
        blocks = []
        commands = ['adelante', 'atras', 'izquierda', 'derecha']
        for i, cmd in enumerate(commands):
            x = PALETTE_X + (i % 2) * (BLOCK_WIDTH + 20)
            y = PALETTE_Y + (i // 2) * (BLOCK_HEIGHT + 15)
            blocks.append(Block(cmd, x, y, in_palette=True))
        return blocks

    def get_program_block_at(self, index):
        """Obtener un bloque del área de programa por índice"""
        if 0 <= index < len(self.program):
            return self.program[index]
        return None

    def add_to_program(self, block):
        """Añadir un bloque al área de programa"""
        if len(self.program) < MAX_COMMANDS:
            # Crear una copia del bloque para el área de programa
            new_block = Block(block.command_type, 0, 0, in_palette=False)
            self.program.append(new_block)
            self.layout_program_blocks()

    def remove_from_program(self, index):
        """Eliminar un bloque del área de programa"""
        if 0 <= index < len(self.program):
            self.program.pop(index)
            self.layout_program_blocks()

    def layout_program_blocks(self):
        """Organizar los bloques del área de programa verticalmente"""
        for i, block in enumerate(self.program):
            block.x = PROGRAM_X
            block.y = PROGRAM_Y + i * (BLOCK_HEIGHT + 10)

    def is_valid_move(self, col, fila):
        """Verificar si una posición es válida (no es pared)"""
        if 0 <= fila < GRID_ROWS and 0 <= col < GRID_COLS:
            return MAZE[fila][col] == 0
        return False

    def execute_next_command(self):
        """Ejecutar el siguiente comando del programa"""
        if self.current_command_index < len(self.program):
            cmd = self.program[self.current_command_index]
            dx, dy = DIRECTIONS[cmd.command_type]
            new_col = self.mouse_pos[0] + dx
            new_fila = self.mouse_pos[1] + dy
            
            if self.is_valid_move(new_col, new_fila):
                self.mouse_pos = [new_col, new_fila]
            else:
                self.message = "¡El ratón chocó con una pared!"
                self.message_timer = 60
            
            self.current_command_index += 1
            self.move_timer = 20  # Pausa entre movimientos
        else:
            # Verificar condiciones de victoria/derrota
            self.check_win_condition()
            self.executing = False

    def check_win_condition(self):
        """Verificar si el jugador ganó o perdió"""
        if tuple(self.mouse_pos) == CHEESE_POS:
            self.won = True
            self.message = "¡GANASTE! El ratón llegó al queso"
        elif tuple(self.mouse_pos) == TRAP_POS:
            self.lost = True
            self.message = "¡PERDISTE! El ratón cayó en la trampa"
        else:
            self.message = "El ratón no llegó a ningún destino"

    def run_program(self):
        """Iniciar la ejecución del programa"""
        if not self.program:
            self.message = "¡Añade comandos al programa primero!"
            self.message_timer = 90
            return
        
        self.mouse_pos = list(MOUSE_START)
        self.won = False
        self.lost = False
        self.executing = True
        self.current_command_index = 0
        self.move_timer = 30
        self.message = ""

    def handle_events(self):
        """Manejar eventos de pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.run_program()
                if event.key == pygame.K_r:
                    self.reset_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Click izquierdo
                    self.handle_mouse_down(event.pos)
            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.handle_mouse_up(event.pos)
            
            if event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
        
        return True

    def handle_mouse_down(self, pos):
        """Manejar clic del ratón"""
        # Verificar botones
        if self.run_button_rect and self.run_button_rect.collidepoint(pos):
            self.run_program()
            return
        if self.reset_button_rect and self.reset_button_rect.collidepoint(pos):
            self.reset_game()
            return
        
        # Verificar bloques de la paleta
        for block in self.palette_blocks:
            if block.is_clicked(pos):
                block.dragging = True
                block.drag_offset_x = pos[0] - block.x
                block.drag_offset_y = pos[1] - block.y
                return
        
        # Verificar bloques del programa (para eliminarlos)
        for i, block in enumerate(self.program):
            if block.is_clicked(pos):
                self.remove_from_program(i)
                return

    def handle_mouse_up(self, pos):
        """Manejar soltar el ratón"""
        for block in self.palette_blocks:
            if block.dragging:
                block.dragging = False
                # Verificar si se soltó en el área de programa
                if pos[0] > PROGRAM_X - 50 and pos[1] > PROGRAM_Y - 50:
                    self.add_to_program(block)

    def handle_mouse_motion(self, pos):
        """Manejar movimiento del ratón"""
        for block in self.palette_blocks:
            if block.dragging:
                block.x = pos[0] - block.drag_offset_x
                block.y = pos[1] - block.drag_offset_y

    def update(self):
        """Actualizar el estado del juego"""
        if self.message_timer > 0:
            self.message_timer -= 1
        
        if self.executing and not self.won and not self.lost:
            if self.move_timer > 0:
                self.move_timer -= 1
            else:
                self.execute_next_command()

    def draw(self):
        """Dibujar todo en la pantalla"""
        self.screen.fill(CREAM)
        
        # Título
        title = self.title_font.render("CODE KARTS - El Ratón y el Queso", True, BLACK)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 15))
        
        # Dibujar laberinto
        self.draw_maze()
        
        # Dibujar paleta de bloques
        self.draw_palette()
        
        # Dibujar área de programa
        self.draw_program_area()
        
        # Dibujar botones
        self.draw_buttons()
        
        # Dibujar mensaje
        if self.message and self.message_timer > 0:
            self.draw_message()
        
        # Dibujar instrucciones
        self.draw_instructions()
        
        pygame.display.flip()

    def draw_maze(self):
        """Dibujar el laberinto"""
        for fila in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + fila * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                
                if MAZE[fila][col] == 1:
                    # Pared
                    pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    pygame.draw.rect(self.screen, DARK_GRAY, rect, width=2)
                else:
                    # Camino
                    pygame.draw.rect(self.screen, PATH_COLOR, rect)
                    pygame.draw.rect(self.screen, GRAY, rect, width=1)
        
        # Dibujar queso
        cheese_x = GRID_OFFSET_X + CHEESE_POS[0] * CELL_SIZE + CELL_SIZE // 2
        cheese_y = GRID_OFFSET_Y + CHEESE_POS[1] * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, YELLOW, (cheese_x, cheese_y), 20)
        pygame.draw.circle(self.screen, ORANGE, (cheese_x, cheese_y), 20, width=2)
        # Agujeros del queso
        pygame.draw.circle(self.screen, ORANGE, (cheese_x - 5, cheese_y - 5), 3)
        pygame.draw.circle(self.screen, ORANGE, (cheese_x + 7, cheese_y + 3), 2)
        pygame.draw.circle(self.screen, ORANGE, (cheese_x - 2, cheese_y + 8), 2)
        
        # Dibujar trampa
        trap_x = GRID_OFFSET_X + TRAP_POS[0] * CELL_SIZE + CELL_SIZE // 2
        trap_y = GRID_OFFSET_Y + TRAP_POS[1] * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, RED, (trap_x, trap_y), 20)
        pygame.draw.circle(self.screen, BLACK, (trap_x, trap_y), 20, width=2)
        # Dibujar X de trampa
        pygame.draw.line(self.screen, BLACK, (trap_x - 10, trap_y - 10), (trap_x + 10, trap_y + 10), 3)
        pygame.draw.line(self.screen, BLACK, (trap_x + 10, trap_y - 10), (trap_x - 10, trap_y + 10), 3)
        
        # Dibujar ratón
        mouse_x = GRID_OFFSET_X + self.mouse_pos[0] * CELL_SIZE + CELL_SIZE // 2
        mouse_y = GRID_OFFSET_Y + self.mouse_pos[1] * CELL_SIZE + CELL_SIZE // 2
        # Cuerpo del ratón
        pygame.draw.circle(self.screen, GRAY, (mouse_x, mouse_y), 18)
        pygame.draw.circle(self.screen, DARK_GRAY, (mouse_x, mouse_y), 18, width=2)
        # Orejas
        pygame.draw.circle(self.screen, GRAY, (mouse_x - 12, mouse_y - 12), 8)
        pygame.draw.circle(self.screen, GRAY, (mouse_x + 12, mouse_y - 12), 8)
        pygame.draw.circle(self.screen, PINK := (255, 182, 193), (mouse_x - 12, mouse_y - 12), 4)
        pygame.draw.circle(self.screen, PINK, (mouse_x + 12, mouse_y - 12), 4)
        # Ojos
        pygame.draw.circle(self.screen, BLACK, (mouse_x - 5, mouse_y - 3), 3)
        pygame.draw.circle(self.screen, BLACK, (mouse_x + 5, mouse_y - 3), 3)
        # Nariz
        pygame.draw.circle(self.screen, PINK, (mouse_x, mouse_y + 5), 3)

    def draw_palette(self):
        """Dibujar la paleta de bloques"""
        # Fondo de la palette
        palette_bg = pygame.Rect(PALETTE_X - 20, PALETTE_Y - 50, 280, 200)
        pygame.draw.rect(self.screen, LIGHT_GRAY, palette_bg, border_radius=10)
        pygame.draw.rect(self.screen, GRAY, palette_bg, width=2, border_radius=10)
        
        label = self.font.render("BLOQUES (arrastra al programa)", True, BLACK)
        self.screen.blit(label, (PALETTE_X - 10, PALETTE_Y - 40))
        
        for block in self.palette_blocks:
            block.draw(self.screen, self.font)

    def draw_program_area(self):
        """Dibujar el área de programa"""
        # Fondo del área de programa
        area_height = MAX_COMMANDS * (BLOCK_HEIGHT + 10) + 60
        program_bg = pygame.Rect(PROGRAM_X - 20, PROGRAM_Y - 50, 200, area_height)
        pygame.draw.rect(self.screen, LIGHT_GRAY, program_bg, border_radius=10)
        pygame.draw.rect(self.screen, GRAY, program_bg, width=2, border_radius=10)
        
        label = self.font.render("PROGRAMA (máx. 8 comandos)", True, BLACK)
        self.screen.blit(label, (PROGRAM_X - 10, PROGRAM_Y - 40))
        
        for block in self.program:
            block.draw(self.screen, self.font)
        
        # Indicar posición actual durante ejecución
        if self.executing and self.current_command_index < len(self.program):
            block = self.program[self.current_command_index]
            rect = block.get_rect()
            pygame.draw.rect(self.screen, YELLOW, rect, width=3, border_radius=8)

    def draw_buttons(self):
        """Dibujar botones de control"""
        # Botón Ejecutar
        self.run_button_rect = pygame.Rect(700, 620, 120, 40)
        pygame.draw.rect(self.screen, GREEN, self.run_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.run_button_rect, width=2, border_radius=8)
        text = self.font.render("EJECUTAR", True, WHITE)
        text_rect = text.get_rect(center=self.run_button_rect.center)
        self.screen.blit(text, text_rect)
        
        # Botón Reiniciar
        self.reset_button_rect = pygame.Rect(840, 620, 120, 40)
        pygame.draw.rect(self.screen, RED, self.reset_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.reset_button_rect, width=2, border_radius=8)
        text = self.font.render("REINICIAR", True, WHITE)
        text_rect = text.get_rect(center=self.reset_button_rect.center)
        self.screen.blit(text, text_rect)

    def draw_message(self):
        """Dibujar mensaje de estado"""
        if self.won:
            color = GREEN
        elif self.lost:
            color = RED
        else:
            color = BLUE
        
        # Fondo del mensaje
        msg_surface = self.big_font.render(self.message, True, color)
        msg_bg = pygame.Rect(SCREEN_WIDTH // 2 - msg_surface.get_width() // 2 - 20, 
                             SCREEN_HEIGHT - 80, 
                             msg_surface.get_width() + 40, 
                             50)
        pygame.draw.rect(self.screen, WHITE, msg_bg, border_radius=10)
        pygame.draw.rect(self.screen, color, msg_bg, width=3, border_radius=10)
        
        self.screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, SCREEN_HEIGHT - 70))

    def draw_instructions(self):
        """Dibujar instrucciones"""
        instructions = [
            "Instrucciones:",
            "1. Arrastra bloques de la paleta al área de programa",
            "2. Presiona ESPACIO o clic en EJECUTAR para correr",
            "3. Lleva al ratón al queso (amarillo) para ganar",
            "4. Evita la trampa (roja) o perderás",
            "5. Presiona R para reiniciar"
        ]
        
        y = SCREEN_HEIGHT - 180
        for line in instructions:
            text = self.font.render(line, True, DARK_GRAY)
            self.screen.blit(text, (50, y))
            y += 22

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
