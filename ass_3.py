import os
import sys

import pygame


pygame.init()

WIDTH, HEIGHT = 960, 720
FPS = 60
ASSET_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Guy's Brain Quest")
clock = pygame.time.Clock()

FONT = pygame.font.Font(None, 30)
SMALL_FONT = pygame.font.Font(None, 24)
TITLE_FONT = pygame.font.Font(None, 76)
HEADING_FONT = pygame.font.Font(None, 46)

INK = (25, 38, 48)
PAPER = (248, 244, 230)
MINT = (116, 218, 194)
CORAL = (241, 130, 111)
GOLD = (246, 202, 91)
MUTED = (119, 133, 138)
WHITE = (255, 255, 255)
GREEN = (89, 176, 127)
RED = (213, 91, 83)


def load_image(relative_path):
	path = os.path.join(ASSET_ROOT, relative_path)
	try:
		return pygame.image.load(path).convert_alpha()
	except (pygame.error, FileNotFoundError):
		return None


def fit_image(image, size):
	if image is None:
		return None
	return pygame.transform.smoothscale(image, size)


backgrounds = {
	"one": load_image(os.path.join("bg", "background1.jpg")),
	"two": load_image(os.path.join("bg", "background2.png")),
}
guy_image = load_image(os.path.join("ppl", "guy.png"))
brain_files = [
	"brain.png",
	"brain(1).png",
	"brain(2).png",
	"brain(3).png",
	"brain(4).png",
	"AntonBrain.png",
]
brains = [
	(filename.rsplit(".", 1)[0].replace("brain", "Brain ").strip(),
	 load_image(os.path.join("ppl", "Brains", filename)))
	for filename in brain_files
]

PATHS = {
	"memory": {
		"title": "Memory Garden",
		"subtitle": "Recall, patterns, and the little details",
		"questions": [
			{
				"prompt": "Which kind of memory holds a phone number just long enough to dial it?",
				"options": ["Working memory", "Procedural memory", "Long-term memory", "Sensory memory"],
				"answer": 0,
			},
			{
				"prompt": "Which strategy is most useful for remembering a list of unrelated items?",
				"options": ["Multitasking", "Chunking", "Skipping breaks", "Reading it once"],
				"answer": 1,
			},
			{
				"prompt": "When is spaced practice generally more effective than cramming?",
				"options": ["Only during a test", "Never", "When learning over several days", "Only for easy topics"],
				"answer": 2,
			},
		],
	},
	"focus": {
		"title": "Focus Tower",
		"subtitle": "Attention, choices, and staying on task",
		"questions": [
			{
				"prompt": "What is selective attention?",
				"options": ["Remembering every sound", "Focusing on relevant information", "Doing two tasks equally", "Avoiding all decisions"],
				"answer": 1,
			},
			{
				"prompt": "What is a helpful first step when a task feels overwhelming?",
				"options": ["Add more distractions", "Wait until it disappears", "Break it into smaller steps", "Start every part at once"],
				"answer": 2,
			},
			{
				"prompt": "A short planned break can help you...",
				"options": ["Forget the whole task", "Avoid learning", "Work without stopping forever", "Return with renewed attention"],
				"answer": 3,
			},
		],
	},
}

INTRO_LINES = [
	"Hey! I'm Guy. Welcome to my brain quest.",
	"We'll explore two parts of the mind: memory and focus.",
	"Pick a path, choose a brain, and see what you know. Ready?",
]
ENDING_LINES = [
	"You made it through both paths! Nice work.",
	"Every brain learns in its own way. Keep asking questions,",
	"and I'll see you on the next adventure!",
]

scene = "title"
dialogue_index = 0
active_path = None
selected_brain = None
question_index = 0
selected_answer = None
answer_feedback = None
completed_paths = set()


def draw_background(key):
	image = backgrounds.get(key)
	if image is None:
		image = backgrounds.get("two")
	if image is None:
		screen.fill((37, 61, 71))
		return
	screen.blit(fit_image(image, (WIDTH, HEIGHT)), (0, 0))


def draw_text(text, font, color, position, center=False):
	surface = font.render(text, True, color)
	rect = surface.get_rect()
	if center:
		rect.center = position
	else:
		rect.topleft = position
	screen.blit(surface, rect)
	return rect


def wrap_text(text, font, max_width):
	words = text.split()
	lines = []
	current = ""
	for word in words:
		candidate = f"{current} {word}".strip()
		if font.size(candidate)[0] <= max_width:
			current = candidate
		else:
			if current:
				lines.append(current)
			current = word
	if current:
		lines.append(current)
	return lines


def draw_wrapped(text, font, color, rect, line_gap=5):
	y = rect.top
	for line in wrap_text(text, font, rect.width):
		draw_text(line, font, color, (rect.left, y))
		y += font.get_linesize() + line_gap


def draw_panel(rect, color=PAPER, alpha=244, border=MINT):
	panel = pygame.Surface(rect.size, pygame.SRCALPHA)
	panel.fill((*color, alpha))
	pygame.draw.rect(panel, (*border, 255), panel.get_rect(), width=3, border_radius=14)
	screen.blit(panel, rect.topleft)


def draw_button(rect, label, enabled=True, accent=MINT):
	mouse_pos = pygame.mouse.get_pos()
	hovered = rect.collidepoint(mouse_pos) and enabled
	fill = accent if enabled else (157, 165, 163)
	if hovered:
		fill = tuple(min(255, channel + 16) for channel in fill)
	pygame.draw.rect(screen, fill, rect, border_radius=12)
	pygame.draw.rect(screen, INK, rect, width=2, border_radius=12)
	draw_text(label, FONT, INK, rect.center, center=True)
	return rect


def draw_guy(position=(95, 250), max_size=(300, 390)):
	if guy_image is None:
		pygame.draw.circle(screen, CORAL, (position[0] + 125, position[1] + 120), 90)
		draw_text("GUY", HEADING_FONT, PAPER, (position[0] + 125, position[1] + 120), center=True)
		return
	image = fit_image(guy_image, max_size)
	screen.blit(image, position)


def begin_path(path_key):
	global active_path, selected_brain, question_index, selected_answer, answer_feedback, scene
	active_path = path_key
	selected_brain = None
	question_index = 0
	selected_answer = None
	answer_feedback = None
	scene = "brains"


def begin_quiz(brain_index):
	global selected_brain, question_index, selected_answer, answer_feedback, scene
	selected_brain = brain_index
	question_index = 0
	selected_answer = None
	answer_feedback = None
	scene = "quiz"


def advance_dialogue(lines):
	global dialogue_index, scene
	dialogue_index += 1
	if dialogue_index >= len(lines):
		dialogue_index = 0
		scene = "choices" if lines is INTRO_LINES else "ending"


def draw_title():
	draw_background("two")
	shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
	shade.fill((17, 31, 40, 138))
	screen.blit(shade, (0, 0))
	draw_text("GUY'S", TITLE_FONT, PAPER, (WIDTH // 2, 185), center=True)
	draw_text("BRAIN QUEST", TITLE_FONT, MINT, (WIDTH // 2, 260), center=True)
	draw_text("Two paths. Six brains. Your next big idea.", FONT, PAPER, (WIDTH // 2, 335), center=True)
	draw_button(pygame.Rect(350, 430, 260, 68), "Start adventure", accent=GOLD)
	draw_text("Click to begin", SMALL_FONT, PAPER, (WIDTH // 2, 530), center=True)


def draw_dialogue(lines, ending=False):
	draw_background("one" if not ending else "two")
	draw_guy((70, 190), (310, 420))
	panel = pygame.Rect(345, 390, 550, 210)
	draw_panel(panel, color=(249, 246, 233), border=CORAL if ending else MINT)
	draw_text("GUY", HEADING_FONT, INK, (panel.x + 28, panel.y + 22))
	draw_wrapped(lines[dialogue_index], FONT, INK, pygame.Rect(panel.x + 28, panel.y + 82, 485, 70))
	draw_button(pygame.Rect(panel.right - 190, panel.bottom - 62, 160, 42), "Continue", accent=GOLD)
	draw_text(f"{dialogue_index + 1} / {len(lines)}", SMALL_FONT, MUTED, (panel.x + 30, panel.bottom - 53))


def draw_choices():
	draw_background("two")
	draw_text("Choose your next path", HEADING_FONT, PAPER, (WIDTH // 2, 95), center=True)
	draw_text("Complete both paths to meet Guy again.", FONT, PAPER, (WIDTH // 2, 148), center=True)
	card_y, card_w, card_h = 250, 380, 260
	for index, key in enumerate(PATHS):
		path = PATHS[key]
		x = 70 + index * 440
		rect = pygame.Rect(x, card_y, card_w, card_h)
		complete = key in completed_paths
		draw_panel(rect, color=(248, 244, 230), alpha=245, border=GOLD if complete else MINT)
		draw_text(path["title"], HEADING_FONT, INK, (rect.centerx, rect.y + 65), center=True)
		draw_wrapped(path["subtitle"], SMALL_FONT, MUTED, pygame.Rect(x + 32, card_y + 105, card_w - 64, 54))
		button_label = "Path complete" if complete else "Choose this path"
		draw_button(pygame.Rect(x + 65, card_y + 175, 250, 54), button_label, not complete,
					accent=GOLD if complete else MINT)
	draw_text(f"Paths complete: {len(completed_paths)} / 2", SMALL_FONT, PAPER, (WIDTH // 2, 580), center=True)


def draw_brain_selection():
	draw_background("one")
	path = PATHS[active_path]
	draw_text(path["title"], HEADING_FONT, INK, (WIDTH // 2, 70), center=True)
	draw_text("Pick a brain to begin your quiz", FONT, INK, (WIDTH // 2, 125), center=True)
	item_w, item_h, gap = 128, 190, 18
	total_width = len(brains) * item_w + (len(brains) - 1) * gap
	start_x = (WIDTH - total_width) // 2
	for index, (name, image) in enumerate(brains):
		x = start_x + index * (item_w + gap)
		rect = pygame.Rect(x, 245, item_w, item_h)
		draw_panel(rect, color=(250, 247, 235), alpha=236, border=CORAL)
		if image is not None:
			scaled = fit_image(image, (104, 110))
			screen.blit(scaled, scaled.get_rect(center=(rect.centerx, rect.y + 75)))
		else:
			pygame.draw.ellipse(screen, CORAL, pygame.Rect(x + 23, rect.y + 34, 82, 70))
		draw_text(name, SMALL_FONT, INK, (rect.centerx, rect.y + 150), center=True)
		draw_button(pygame.Rect(x + 17, rect.bottom + 16, item_w - 34, 42), "Choose", accent=MINT)
	draw_button(pygame.Rect(390, 590, 180, 48), "Back", accent=GOLD)


def draw_quiz():
	draw_background("two")
	path = PATHS[active_path]
	questions = path["questions"]
	question = questions[question_index]
	draw_text(path["title"], HEADING_FONT, PAPER, (55, 50))
	draw_text(f"Question {question_index + 1} of {len(questions)}", FONT, PAPER, (60, 110))
	draw_text(f"Selected: {brains[selected_brain][0]}", SMALL_FONT, PAPER, (590, 65))
	panel = pygame.Rect(55, 165, 850, 390)
	draw_panel(panel, color=(248, 244, 230), alpha=246, border=MINT)
	draw_wrapped(question["prompt"], HEADING_FONT, INK, pygame.Rect(90, 200, 775, 95), line_gap=4)
	for index, option in enumerate(question["options"]):
		option_rect = pygame.Rect(95, 320 + index * 54, 770, 44)
		if selected_answer == index:
			fill = GREEN if index == question["answer"] else RED
		else:
			fill = PAPER
		pygame.draw.rect(screen, fill, option_rect, border_radius=8)
		pygame.draw.rect(screen, INK, option_rect, width=2, border_radius=8)
		draw_text(option, SMALL_FONT, INK, (option_rect.x + 16, option_rect.y + 11))
	if answer_feedback:
		draw_text(answer_feedback, SMALL_FONT, GREEN if selected_answer == question["answer"] else RED,
				  (WIDTH // 2, 575), center=True)
	next_label = "Finish quiz" if question_index == len(questions) - 1 else "Next question"
	draw_button(pygame.Rect(690, 615, 215, 58), next_label,
				enabled=selected_answer is not None, accent=GOLD)


def handle_click(position):
	global scene, dialogue_index, question_index, selected_answer, answer_feedback
	if scene == "title":
		if pygame.Rect(350, 430, 260, 68).collidepoint(position):
			scene = "intro"
			dialogue_index = 0
	elif scene == "intro":
		if pygame.Rect(705, 538, 160, 42).collidepoint(position):
			advance_dialogue(INTRO_LINES)
	elif scene == "choices":
		for index, key in enumerate(PATHS):
			rect = pygame.Rect(70 + index * 440 + 65, 425, 250, 54)
			if rect.collidepoint(position) and key not in completed_paths:
				begin_path(key)
				break
	elif scene == "brains":
		item_w, item_h, gap = 128, 190, 18
		total_width = len(brains) * item_w + (len(brains) - 1) * gap
		start_x = (WIDTH - total_width) // 2
		for index in range(len(brains)):
			x = start_x + index * (item_w + gap)
			card = pygame.Rect(x, 245, item_w, item_h)
			choose = pygame.Rect(x + 17, card.bottom + 16, item_w - 34, 42)
			if card.collidepoint(position) or choose.collidepoint(position):
				begin_quiz(index)
				return
		if pygame.Rect(390, 590, 180, 48).collidepoint(position):
			scene = "choices"
	elif scene == "quiz":
		question = PATHS[active_path]["questions"][question_index]
		if selected_answer is None:
			for index in range(len(question["options"])):
				option_rect = pygame.Rect(95, 320 + index * 54, 770, 44)
				if option_rect.collidepoint(position):
					selected_answer = index
					answer_feedback = "Correct!" if index == question["answer"] else "Not quite. The highlighted answer is correct."
					break
		if pygame.Rect(690, 615, 215, 58).collidepoint(position) and selected_answer is not None:
			if question_index + 1 < len(PATHS[active_path]["questions"]):
				question_index += 1
				selected_answer = None
				answer_feedback = None
			else:
				completed_paths.add(active_path)
				if len(completed_paths) == len(PATHS):
					scene = "ending"
					dialogue_index = 0
				else:
					scene = "choices"
	elif scene == "ending":
		if pygame.Rect(705, 538, 160, 42).collidepoint(position):
			if dialogue_index + 1 < len(ENDING_LINES):
				dialogue_index += 1
			else:
				scene = "title"
				dialogue_index = 0
				completed_paths.clear()


def main():
	global scene
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				if scene in ("brains", "choices"):
					scene = "choices"
				elif scene == "quiz":
					scene = "choices"
				else:
					running = False
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				handle_click(event.pos)

		if scene == "title":
			draw_title()
		elif scene == "intro":
			draw_dialogue(INTRO_LINES)
		elif scene == "choices":
			draw_choices()
		elif scene == "brains":
			draw_brain_selection()
		elif scene == "quiz":
			draw_quiz()
		elif scene == "ending":
			draw_dialogue(ENDING_LINES, ending=True)

		pygame.display.flip()
		clock.tick(FPS)

	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	main()
