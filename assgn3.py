import pygame
import sys

# Initialize Pygame

pygame.init()


def display_text(text, x, y, font, color=(0,0,0)):
    """
    Renders and displays text on the screen at the specified position.

    Args:
        text (str): The text to be displayed.
        x (int): The x-coordinate of the text position.
        y (int): The y-coordinate of the text position.
        font (pygame.font.Font): The font object to use.
        color (tuple): The color of the text (default is black).
    """
    
    lines = text.split('\n')
    
    y_offset = 0
    
    for line in lines:
        
        text_surface =  font.render(line, True, color)
        
        screen.blit(text_surface, (x, y + y_offset))
        
        y_offset += text_surface.get_height()

def show_dialogue(dialogue_list, font, color = (0,0,0)):
    """
    Displays a sequence of dialogues on the screen.

    Args:
        dialogue_list (list): A list of dialogue strings.
        font (pygame.font.Font): The font object to use.
        color (tuple): The color of the text (default is black).
    """
    
    index = 0
    
    while index < len(dialogue_list):
        
        screen.fill(WHITE)
        
        display_text(dialogue_list[index], 20, SCREEN_HEIGHT - 100, font, color)
        
        pygame.display.flip()

        
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                
                pygame.quit()
                
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_SPACE:
                    
                    index += 1
                    
                    break


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Assgn 3")

bg = pygame.image.load("./assets/bg/moon.png")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
guy = pygame.image.load("./assets/ppl/guy.png")
guy = pygame.transform.scale(guy, (guy.get_width() // 8, guy.get_height() // 8))

WHITE = (255, 255, 255)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # Close the game
            running = False

    screen.fill(WHITE)
    screen.blit(bg, (0, 0))

    screen.blit(guy, (0, HEIGHT - guy.get_height()))

    # Update the display

    pygame.display.flip()

pygame.quit()