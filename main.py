import pygame
import sys
import config
import random
import qiskit as qk
from pygame.locals import *
from utils import *

qc = generate_board(8, 18, 1)
shots = 1024

def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode(config.SCREEN_SIZE)
    pygame.display.set_caption("Battleship Game")
    return screen

def classic(pos):
    x, y = pos
    circ = qc[x]
    circ.measure(y, y)
    simulator = qk.Aer.get_backend('qasm_simulator')
    result = qk.execute(circ, simulator, shots=1).result()
    counts = result.get_counts(circ)
    for key in counts:
        return int(key[y])
 
def get_prob(row):
    circuit = qc[row]
    circuit.measure_all()
    simulator = qk.Aer.get_backend('qasm_simulator')
    result = qk.execute(circuit, simulator, shots=1024).result()
    counts = result.get_counts(circuit)
    prob = [0 for _ in range(8)]
    for key in counts:
        for k in range(8):
            if int(key[k]) == 1:
                prob[k] += counts[key]
    for k in range(8):
        prob[k] = str(round(100 * prob[k]/shots))
    return prob

def main_menu(screen):
    _, _, background_image, scroll_image, _, _, _ = load_images()
    click_sound, _, _ = load_sounds()
    
    title_font = pygame.font.Font("assets/fonts/OpenSans-VariableFont_wdth,wght.ttf", 70)
    title_font.set_bold(True)
    button_font = pygame.font.Font("assets/fonts/OpenSans-VariableFont_wdth,wght.ttf", 20)
    title_surface = title_font.render('Quantum Battleships', True, config.SPECIAL_RED)
    scroll_rect = scroll_image.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 3.5))
    title_rect = title_surface.get_rect(center=(scroll_rect.centerx, scroll_rect.centery - 25))
    button_y = scroll_rect.bottom + 50  
    button_size = (200, 60)
    buttons = {
        'start': {
            'color': config.DARK_GREY,
            'rect': pygame.Rect((config.SCREEN_WIDTH // 2 - button_size[0] // 2, button_y), button_size),
            'text': 'Start Game',
            'action': lambda: main(screen),
        }
    }

    clock = pygame.time.Clock()
    is_running = True

    while is_running:
        time_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                click_sound.play()
                mouse_pos = event.pos
                for button_key, button_props in buttons.items():
                    if button_props['rect'].collidepoint(mouse_pos):
                        button_props['action']() 
                        is_running = False 

        screen.blit(background_image, (0, 0))
        screen.blit(scroll_image, scroll_rect)
        screen.blit(title_surface, title_rect)
        for button_key, button_props in buttons.items():
            draw_button(screen, button_props['color'], button_props['rect'].topleft, button_props['rect'].size)
            text_surf = button_font.render(button_props['text'], True, config.LIGHT_GREY)
            text_rect = text_surf.get_rect(center=button_props['rect'].center)
            screen.blit(text_surf, text_rect)
        pygame.display.update()

    pygame.quit()
    sys.exit()

def main(screen):
    target_image, sea_image, background_image, _, quote_image, fire_image, wreck_image = load_images()
    click_sound, explosion_sound, splash_sound = load_sounds()
    target_image_rect = target_image.get_rect()
    font = pygame.font.Font("assets/fonts/OpenSans-VariableFont_wdth,wght.ttf", 16)
    font.set_bold(True)
    show_popup = False
    event_string_background = create_overlay((config.GRID_WIDTH + 80, 40), 150, config.LIGHT_GREY)
    heat_map_toggle_background = create_overlay((config.GRID_WIDTH + 80, 40), 150, config.LIGHT_GREY)
    counts_background = create_overlay((config.GRID_WIDTH + 80, 40), 150, config.LIGHT_GREY)
    settings_background = create_overlay((config.GRID_WIDTH + 80, 40), 150, config.LIGHT_GREY)
    grid_background = create_overlay((config.GRID_WIDTH + 80, config.GRID_HEIGHT + 80), 150, config.LIGHT_GREY)
    heat_map_background = create_overlay((config.GRID_WIDTH + 80, config.GRID_HEIGHT + 80), 150, config.LIGHT_GREY)
    button_overlay = create_overlay(config.BUTTON_SIZE, 175, config.BLACK)
    grid_buttons = create_grid_buttons(config.GRID_OFFSET_X, config.GRID_OFFSET_Y)
    probabilities = [get_prob(y) for y in range(8)]
    entangled = set()
    while len(entangled) < 16:
        x = random.randint(0, 7)
        y = random.randint(0, 7)
        entangled.add((x, y))
    
    entangled = list(entangled)
    a = entangled[:8]
    b = entangled[8:]
    lookup1 = dict(zip(a, b))
    lookup2 = dict(zip(b, a))
    for key in lookup1:
        val = lookup1[key]
        k1, k2 = key
        v1, v2 = val
        p = int(0.5 * (int(probabilities[k1][k2]) + int(probabilities[v1][v2])))
        probabilities[k1][k2] = p
        probabilities[v1][v2] = p

    running = True
    display_heat_map = True
    current_pos = [0, 0]
    event_time = pygame.time.get_ticks() - 3000
    discovered = set() 
    cannon = 0  
    prob_display = [[False for x in range(8)] for y in range(8)]
    shots_fired, ships_sunk = 0, 0
    ship_state = [[[-1, 0] for _ in range(8)] for _ in range(8)]
    current_event_message = None
    current_event_start_time = None
    quantum_fired = False

    while running:
        screen.blit(background_image, (0, 0))
        screen.blit(event_string_background, (config.GRID_OFFSET_X - 40, config.GRID_OFFSET_Y - 120))
        screen.blit(heat_map_toggle_background, (config.HEAT_MAP_OFFSET_X - 40, config.HEAT_MAP_OFFSET_Y - 120))
        screen.blit(counts_background, (config.GRID_OFFSET_X - 40, config.GRID_OFFSET_Y - 160))
        screen.blit(settings_background, (config.HEAT_MAP_OFFSET_X - 40, config.HEAT_MAP_OFFSET_Y - 160))
        screen.blit(grid_background, (config.GRID_OFFSET_X - 40, config.GRID_OFFSET_Y - 40))
        screen.blit(heat_map_background, (config.HEAT_MAP_OFFSET_X - 40, config.HEAT_MAP_OFFSET_Y - 40))
        screen.blit(sea_image, (config.GRID_OFFSET_X, config.GRID_OFFSET_Y))
        scale_factor = 2.05
        button_spacing = 10
        home_toggle_text = font.render('HOME', True, config.LIGHT_GREY)
        home_toggle_rect_original = home_toggle_text.get_rect(center=(config.HEAT_MAP_OFFSET_X + 80, config.HEAT_MAP_OFFSET_Y - 142))
        home_toggle_rect_padded = home_toggle_rect_original.inflate(20, 8)
        original_width, original_height = home_toggle_rect_padded.size
        new_width = original_width * scale_factor
        home_toggle_rect = pygame.Rect(home_toggle_rect_original.left, home_toggle_rect_original.top, new_width, original_height)
        reset_toggle_rect = pygame.Rect(home_toggle_rect.right + button_spacing, home_toggle_rect.top, new_width, original_height)
        reset_toggle_text = font.render('RESET', True, config.LIGHT_GREY)
        reset_toggle_rect.center = reset_toggle_rect.center 
        pygame.draw.rect(screen, config.DARK_GREY, home_toggle_rect, border_radius=8)
        home_text_x = home_toggle_rect.x + (home_toggle_rect.width - home_toggle_text.get_width()) // 2
        home_text_y = home_toggle_rect.y + (home_toggle_rect.height - home_toggle_text.get_height()) // 2
        screen.blit(home_toggle_text, (home_text_x, home_text_y - 1))
        pygame.draw.rect(screen, config.DARK_GREY, reset_toggle_rect, border_radius=8)
        reset_text_x = reset_toggle_rect.x + (reset_toggle_rect.width - reset_toggle_text.get_width()) // 2
        reset_text_y = reset_toggle_rect.y + (reset_toggle_rect.height - reset_toggle_text.get_height()) // 2
        screen.blit(reset_toggle_text, (reset_text_x, reset_text_y - 1))

        heat_map_text = font.render('Heat Map', True, config.SPECIAL_RED)
        shots_fired_text = font.render('Shots Fired: ' + str(shots_fired), True, config.BLACK)
        screen.blit(shots_fired_text, (config.GRID_OFFSET_X, config.GRID_OFFSET_Y - 149))
        ships_sunk_text = font.render('Ships Sunk: ' + str(ships_sunk), True, config.BLACK)
        screen.blit(ships_sunk_text, (config.GRID_OFFSET_X + config.GRID_WIDTH - 105, config.GRID_OFFSET_Y - 149))

        current_time = pygame.time.get_ticks()

        if not current_event_message or current_time - current_event_start_time > 3000:
            text, special_event = determine_event_string(cannon, current_pos, ship_state, event_time, lookup1, lookup2, quantum_fired)
            
            if special_event:
                current_event_message = text
                current_event_start_time = current_time

                if quantum_fired:
                    quantum_fired = False
        else:
            text = current_event_message

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_pos[1] = max(current_pos[1] - 1, 0)
                elif event.key == pygame.K_RIGHT:
                    current_pos[1] = min(current_pos[1] + 1, config.GRID_COLS - 1 - cannon)
                elif event.key == pygame.K_UP:
                    current_pos[0] = max(current_pos[0] - 1, 0)
                elif event.key == pygame.K_DOWN:
                    current_pos[0] = min(current_pos[0] + 1, config.GRID_ROWS - 1 - cannon)
                elif event.key == pygame.K_RETURN:
                    if pygame.time.get_ticks() - event_time > 3000:
                        event_time = pygame.time.get_ticks()
                    if cannon == 1:
                        quantum_fired = True
                        shots_fired += 1
                        x, y = current_pos
                        squares = [(x, y), (x+1, y), (x, y+1), (x+1, y+1)]
                        for s in squares:
                            x1, y1 = s
                            if grid_buttons[s]['state'] == config.BUTTON_NORMAL:
                                prob_display[x1][y1] = True
                    else:
                        pos_key = tuple(current_pos)
                        x, y = pos_key
                        if pos_key not in discovered:
                            shots_fired += 1
                            discovered.add(pos_key)
                            grid_buttons[pos_key]['state'] = config.BUTTON_CLICKED
                            prob_display[x][y] = False
                            state = classic(pos_key)
                            twin = None
                            if (x, y) in lookup1.keys():
                                twin = lookup1[(x, y)]
                            elif (x, y) in lookup2.keys():
                                twin = lookup2[(x, y)]
                            if state == 1: #hit
                                explosion_sound.play()
                                if twin:
                                    tx, ty = twin
                                    ships_sunk += 1
                                    probabilities[tx][ty] = 100 
                                    ship_state[tx][ty] = (1, pygame.time.get_ticks())
                                    discovered.add(twin)
                                    grid_buttons[twin]['state'] = config.BUTTON_CLICKED
                                    prob_display[tx][ty] = False

                                ships_sunk += 1
                                probabilities[x][y] = 100 
                                ship_state[x][y] = (1, pygame.time.get_ticks())
                            else: #miss
                                splash_sound.play()
                                if twin:
                                    tx, ty = twin
                                    probabilities[tx][ty] = 0
                                    ship_state[tx][ty][0] = 0
                                    discovered.add(twin)
                                    grid_buttons[twin]['state'] = config.BUTTON_CLICKED
                                    prob_display[tx][ty] = False
                                probabilities[x][y] = 0
                                ship_state[x][y][0] = 0
                elif event.key == pygame.K_SPACE:
                    if cannon == 0:
                        if current_pos[0] == config.GRID_ROWS - 1:
                            current_pos[0] -= 1
                        if current_pos[1] == config.GRID_COLS - 1:
                            current_pos[1] -= 1
                        new_width = target_image.get_width() * 2
                        new_height = target_image.get_height() * 2
                        target_image = pygame.transform.scale(target_image, (new_width, new_height))
                        cannon = 1
                    else:
                        new_width = target_image.get_width() / 2
                        new_height = target_image.get_height() / 2
                        target_image = pygame.transform.scale(target_image, (new_width, new_height))
                        cannon = 0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_sound.play()
                if heat_map_toggle_rect.collidepoint(event.pos):
                    display_heat_map = not display_heat_map 
                elif home_toggle_rect.collidepoint(event.pos):
                    main_menu(screen)
                elif reset_toggle_rect.collidepoint(event.pos):
                    main(screen)

        if display_heat_map:
            draw_heat_map(screen, probabilities, font)
            draw_indices(screen, config.HEAT_MAP_OFFSET_X, config.HEAT_MAP_OFFSET_Y, font)
        else:
            screen.blit(quote_image, (config.HEAT_MAP_OFFSET_X, config.HEAT_MAP_OFFSET_Y))

        for i in range(8):
            for j in range(8):
                if ship_state[j][i][0] == 1: 
                    time_since_hit = pygame.time.get_ticks() - ship_state[j][i][1]
                    pos = (config.GRID_OFFSET_X + 51*i, config.GRID_OFFSET_Y + 51*j)  

                    if time_since_hit < 2000:
                        fire_image.set_alpha(255)
                        screen.blit(fire_image, pos)
                    else:
                        fade_duration = 2500  
                        if time_since_hit - 2000 < fade_duration:
                            fire_alpha = max(0, min(255, int(255 - ((time_since_hit - 2000) / fade_duration) * 255)))
                            fire_image.set_alpha(fire_alpha)
                            screen.blit(fire_image, pos)

                            wreck_alpha = max(0, min(255, int(((time_since_hit - 2000) / fade_duration) * 255)))
                            wreck_image.set_alpha(wreck_alpha)
                            screen.blit(wreck_image, pos)
                        else:
                            wreck_image.set_alpha(255)
                            screen.blit(wreck_image, pos)

        draw_indices(screen, config.GRID_OFFSET_X, config.GRID_OFFSET_Y, font)

        for pos_key, button_data in grid_buttons.items():
            button_rect = button_data['rect']
            if pos_key not in discovered:
                screen.blit(button_overlay, button_rect.topleft)

        for x in range(8):
            for y in range(8):
                pos = (config.GRID_OFFSET_X + y * (config.BUTTON_WIDTH + config.GRID_PADDING),
                        config.GRID_OFFSET_Y + x * (config.BUTTON_HEIGHT + config.GRID_PADDING))

                probability = probabilities[x][y]
                if prob_display[x][y]:
                    text = font.render(str(probability) + "%", True, config.LIGHT_GREY)
                    text_rect = text.get_rect()
                    center_x = pos[0] + config.BUTTON_WIDTH // 2
                    center_y = pos[1] + config.BUTTON_HEIGHT // 2
                    text_rect.center = (center_x, center_y)
                    screen.blit(text, text_rect.topleft)

        target_image_rect.topleft = grid_buttons[tuple(current_pos)]['rect'].topleft
        screen.blit(target_image, target_image_rect.topleft)

        if ships_sunk == 10 or ships_sunk == 11:
            draw_popup(screen, shots_fired)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

def draw_blurred_background(screen):
    background = screen.copy()
    overlay = pygame.Surface((background.get_width(), background.get_height()), flags=pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 180))  
    background.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return background

def draw_popup(screen, shots_taken):
    blurred_bg = draw_blurred_background(screen)
    screen.blit(blurred_bg, (0, 0))
    popup_rect = pygame.Rect(0, 0, 300, 200)
    popup_rect.center = screen.get_rect().center
    pygame.draw.rect(screen, (50, 50, 50), popup_rect, border_radius=12)
    font = pygame.font.Font(None, 36)
    win_text = font.render('You Win!', True, config.LIGHT_GREY)
    win_text_rect = win_text.get_rect(center=(popup_rect.centerx, popup_rect.centery - 20))
    screen.blit(win_text, win_text_rect)
    shots_text = font.render(f'Shots taken: {shots_taken}', True, config.LIGHT_GREY)
    shots_text_rect = shots_text.get_rect(center=(popup_rect.centerx, popup_rect.centery + 20))
    screen.blit(shots_text, shots_text_rect)

if __name__ == "__main__":
    screen = init_pygame()
    theme_song = pygame.mixer.init()
    pygame.mixer.music.load('assets/sounds/theme_song.mp3')
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
    main_menu(screen)