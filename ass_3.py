import json
import re
from pathlib import Path

import pygame


WIDTH, HEIGHT = 960, 720
FPS = 60
NOTE_LIMIT = 250
BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "assets"
PLAYER_DIR = BASE_DIR / "player_files"

BRAINS = ["Anton", "Charlie", "Claire", "Cosmo", "Sal", "Sandy"]
BRAIN_CENTERS = [85, 237, 390, 550, 710, 865]
CATEGORIES = ["ASD", "Neurotypical"]

ANSWER_KEY = {
	"Anton": "ASD",
	"Charlie": "Neurotypical",
	"Claire": "ASD",
	"Cosmo": "Neurotypical",
	"Sal": "ASD",
	"Sandy": "Neurotypical",
}

DIALOGUE = [
	"Welcome to the interactive portion of the paper.",
	"Patterns in eye movements and area of focus between people with and without ASD have significant differences.",
    "This activity explores the idea of using eye-tracking to aid in diagnosis for individuals with ASD.",
    "I have provided you with 6 simulated individual's brains.",
     "Using their eye-tracking data, we can simulate you looking through their eyes, focusing on what they focus on,",
     "and you can try to give a likely diagnosis for each individual.",
     "Please note - these are not real people, and this is not a real diagnostic tool."
]

READING_EXCERPTS = [
	("A quiet morning", "The bus arrived early. I found a seat by the window and watched the neighborhood wake up: shop lights, wet pavement, and a dog tugging at its leash."),
	("The museum", "In the gallery, one painting held my attention for a long time. I noticed the tiny marks in the clouds before I noticed the title on the wall."),
	("A new recipe", "The recipe had twelve steps. I laid out each ingredient first, then followed the list in order. The kitchen smelled like lemon and warm bread."),
]

COLORS = {
	"ink": (30, 43, 48),
	"paper": (250, 246, 232),
	"teal": (104, 169, 178),
	"teal_dark": (52, 104, 112),
	"coral": (227, 119, 99),
	"gold": (238, 193, 81),
	"white": (255, 255, 255),
	"muted": (100, 112, 111),
	"green": (61, 143, 101),
	"red": (187, 67, 59),
}


def wrap_text(text, font, max_width):
	lines = []
	current = ""
	for word in text.split():
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


def draw_text(surface, text, font, color, position, center=False):
	rendered = font.render(str(text), True, color)
	rect = rendered.get_rect()
	if center:
		rect.center = position
	else:
		rect.topleft = position
	surface.blit(rendered, rect)
	return rect


def draw_wrapped(surface, text, font, color, rect, line_gap=4):
	y = rect.top
	for line in wrap_text(text, font, rect.width):
		draw_text(surface, line, font, color, (rect.left, y))
		y += font.get_linesize() + line_gap
	return y


class BrainGame:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Interactive")
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		pygame.mouse.set_visible(False)
		self.gaze_position = pygame.mouse.get_pos()
		self.clock = pygame.time.Clock()
		self.font = pygame.font.Font(None, 28)
		self.small_font = pygame.font.Font(None, 22)
		self.heading_font = pygame.font.Font(None, 44)
		self.title_font = pygame.font.Font(None, 76)
		self.big_font = pygame.font.Font(None, 54)
		self.images = {}
		self.scene = "title"
		self.dialogue_index = 0
		self.open_brain = None
		self.file_return_scene = "selection"
		self.activity_type = "reading"
		self.activity_index = 0
		self.active_brain = None
		self.show_heatmaps = False
		self.note_focused = False
		self.selection_notice = ""
		self.player_data = {name: self.load_brain_data(name) for name in BRAINS}
		self.file_button_rects = {}
		self.heatmap_cache = {}
		self.gaze_mask = None
		self.notes_button_rect = pygame.Rect(886, 18, 54, 46)
		self.close_notes_rect = pygame.Rect(886, 18, 54, 46)

	def load_image(self, relative_path, size=None, black_transparent=False):
		key = (str(relative_path), size, black_transparent)
		if key in self.images:
			return self.images[key]
		path = ASSET_DIR / relative_path
		try:
			image = pygame.image.load(str(path)).convert_alpha()
			if black_transparent:
				image.set_colorkey((0, 0, 0))
			if size:
				image = pygame.transform.smoothscale(image, size)
		except (pygame.error, FileNotFoundError):
			image = None
		self.images[key] = image
		return image

	def load_brain_data(self, name):
		path = PLAYER_DIR / f"{name}.json"
		try:
			data = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, json.JSONDecodeError):
			data = {}
		choice = data.get("choice")
		if choice not in CATEGORIES:
			choice = None
		notes = data.get("notes", "")
		if not isinstance(notes, str):
			notes = ""
		return {"choice": choice, "notes": notes[:NOTE_LIMIT]}

	def save_brain_data(self, name):
		PLAYER_DIR.mkdir(parents=True, exist_ok=True)
		path = PLAYER_DIR / f"{name}.json"
		path.write_text(
			json.dumps(self.player_data[name], ensure_ascii=False, indent=2),
			encoding="utf-8",
		)

	def reset_brain_files(self):
		for name in BRAINS:
			self.player_data[name] = {"choice": None, "notes": ""}
			self.save_brain_data(name)

	def background(self, relative_path, fallback=(221, 207, 165)):
		image = self.load_image(relative_path, (WIDTH, HEIGHT))
		if image is None:
			self.screen.fill(fallback)
		else:
			self.screen.blit(image, (0, 0))

	def panel(self, rect, color=None, border=None):
		color = color or COLORS["paper"]
		border = border or COLORS["teal_dark"]
		pygame.draw.rect(self.screen, color, rect, border_radius=8)
		pygame.draw.rect(self.screen, border, rect, width=3, border_radius=8)

	def button(self, rect, label, fill=None, text_color=None):
		fill = fill or COLORS["teal"]
		text_color = text_color or COLORS["ink"]
		hovered = rect.collidepoint(pygame.mouse.get_pos())
		if hovered:
			fill = tuple(min(channel + 18, 255) for channel in fill)
		pygame.draw.rect(self.screen, fill, rect, border_radius=7)
		pygame.draw.rect(self.screen, COLORS["ink"], rect, width=2, border_radius=7)
		draw_text(self.screen, label, self.font, text_color, rect.center, center=True)

	def draw_title(self):
		self.background("bg/MainMenuBG.png")
		shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
		shade.fill((27, 49, 53, 65))
		self.screen.blit(shade, (0, 0))
		draw_text(self.screen, "INTERACTIVE", self.title_font, COLORS["ink"], (WIDTH // 2, 300), center=True)
		self.button(pygame.Rect(365, 500, 230, 64), "BEGIN", COLORS["gold"])

	def draw_dialogue(self):
		self.background("bg/TalkToGuyBG.png")
		guy = self.load_image("ppl/guy.png", (500, 360), black_transparent=True)
		if guy:
			self.screen.blit(guy, (5, 300))
		self.panel(pygame.Rect(340, 365, 570, 230), color=(250, 246, 232))
		draw_text(self.screen, "GUY", self.heading_font, COLORS["teal_dark"], (370, 390))
		draw_wrapped(
			self.screen,
			DIALOGUE[self.dialogue_index],
			self.font,
			COLORS["ink"],
			pygame.Rect(370, 450, 510, 86),
		)
		draw_text(self.screen, "Press Enter to continue", self.small_font, COLORS["muted"], (370, 558))

	def draw_selection(self):
		self.background("bg/SelectionScene.png")
		self.file_button_rects = {}
		for index, name in enumerate(BRAINS):
			center_x = BRAIN_CENTERS[index]
			brain = self.load_image(f"ppl/Brains/{name}Brain.png", (138, 104), black_transparent=True)
			if brain:
				self.screen.blit(brain, brain.get_rect(center=(center_x, 160)))
			draw_text(self.screen, name, self.small_font, COLORS["ink"], (center_x, 90), center=True)
			file_rect = pygame.Rect(center_x - 35, 278, 70, 52)
			file_image = self.load_image("etc/File.png", (70, 52), black_transparent=True)
			if file_image:
				self.screen.blit(file_image, file_rect)
			else:
				pygame.draw.rect(self.screen, COLORS["teal"], file_rect, border_radius=5)
			pygame.draw.rect(self.screen, COLORS["ink"], file_rect, width=1, border_radius=5)
			self.file_button_rects[name] = file_rect
			choice = self.player_data[name]["choice"]
			status = choice if choice else "Not classified"
			draw_text(self.screen, status, self.small_font, COLORS["teal_dark"], (center_x, 340), center=True)

		self.button(pygame.Rect(190, 480, 170, 58), "READING")
		self.button(pygame.Rect(395, 480, 170, 58), "IMAGES", COLORS["coral"])
		complete = all(self.player_data[name]["choice"] for name in BRAINS)
		self.button(
			pygame.Rect(600, 480, 220, 58),
			"CHECK ANSWERS",
			COLORS["gold"] if complete else (195, 190, 169),
		)
		draw_text(self.screen, "Click a file to add notes and choose a label.", self.small_font, COLORS["ink"], (WIDTH // 2, 590), center=True)
		if self.selection_notice:
			draw_text(self.screen, self.selection_notice, self.small_font, COLORS["red"], (WIDTH // 2, 635), center=True)

	def draw_file(self):
		self.background("bg/ActivityBG.png")
		self.panel(pygame.Rect(82, 45, 796, 620))
		name = self.open_brain
		draw_text(self.screen, f"{name}'s file", self.heading_font, COLORS["ink"], (120, 75))
		brain = self.load_image(f"ppl/Brains/{name}Brain.png", (330, 245), black_transparent=True)
		image_rect = pygame.Rect(120, 145, 330, 245)
		if brain:
			self.screen.blit(brain, brain.get_rect(center=image_rect.center))
		pygame.draw.rect(self.screen, COLORS["teal_dark"], image_rect, width=2, border_radius=6)
		draw_text(self.screen, "Classification", self.font, COLORS["ink"], (510, 145))

		data = self.player_data[name]
		for index, category in enumerate(CATEGORIES):
			rect = pygame.Rect(510, 190 + index * 58, 24, 24)
			pygame.draw.rect(self.screen, COLORS["white"], rect, border_radius=3)
			pygame.draw.rect(self.screen, COLORS["ink"], rect, width=2, border_radius=3)
			if data["choice"] == category:
				pygame.draw.line(self.screen, COLORS["green"], (rect.left + 5, rect.centery), (rect.left + 10, rect.bottom - 5), 3)
				pygame.draw.line(self.screen, COLORS["green"], (rect.left + 10, rect.bottom - 5), (rect.right - 4, rect.top + 4), 3)
			draw_text(self.screen, category, self.font, COLORS["ink"], (550, rect.top - 2))

		draw_text(self.screen, "Notes", self.font, COLORS["ink"], (120, 415))
		notes_rect = pygame.Rect(120, 448, 720, 140)
		pygame.draw.rect(self.screen, COLORS["white"], notes_rect, border_radius=5)
		border = COLORS["coral"] if self.note_focused else COLORS["teal_dark"]
		pygame.draw.rect(self.screen, border, notes_rect, width=2, border_radius=5)
		draw_wrapped(
			self.screen,
			data["notes"] or ("Click here and type notes..." if not self.note_focused else ""),
			self.small_font,
			COLORS["ink"] if data["notes"] or self.note_focused else COLORS["muted"],
			notes_rect.inflate(-16, -14),
			line_gap=2,
		)
		draw_text(self.screen, f"{len(data['notes'])}/{NOTE_LIMIT}", self.small_font, COLORS["muted"], (790, 596))
		self.button(pygame.Rect(120, 606, 145, 42), "BACK", COLORS["gold"])
		draw_text(self.screen, "Changes save automatically", self.small_font, COLORS["muted"], (480, 620), center=True)

	def activity_heatmap(self, name, stimulus_index):
		folder = ASSET_DIR / "heatmaps" / name / self.activity_type
		try:
			files = list(folder.glob("*.png"))
		except OSError:
			return None

		expected_number = stimulus_index + 1
		for path in files:
			match = re.match(r"Heatmap(\d+)", path.stem, re.IGNORECASE)
			if match and int(match.group(1)) == expected_number:
				return path.relative_to(ASSET_DIR)

		placeholder_name = "Placeholder.png" if stimulus_index == 0 else f"Placeholder{stimulus_index}.png"
		placeholder = folder / placeholder_name
		return placeholder.relative_to(ASSET_DIR) if placeholder.is_file() else None

	def activity_item_count(self):
		if self.activity_type == "reading":
			return len(READING_EXCERPTS)
		return len(list((ASSET_DIR / "etc" / "images_activity").glob("*.png")))

	def current_activity_index(self):
		item_count = self.activity_item_count()
		return self.activity_index % item_count if item_count else 0

	@staticmethod
	def heatmap_color(color):
		if color.a < 80:
			return None
		red, green, blue = color.r, color.g, color.b
		if blue > 110 and blue > red * 1.25 and blue > green * 1.15:
			return "blue"
		if green > 110 and green > red * 1.25 and green > blue * 1.25:
			return "green"
		if red > 100 and green > 100 and blue < 150:
			return "yellow"
		if red > 110 and red > green * 1.2 and red > blue * 1.2:
			return "red"
		return None

	def get_heatmap_data(self, name):
		path = self.activity_heatmap(name, self.current_activity_index())
		if path is None:
			return None
		cache_key = str(path)
		if cache_key in self.heatmap_cache:
			return self.heatmap_cache[cache_key]

		heatmap = self.load_image(path)
		if heatmap is None:
			return None
		regions = {color: [] for color in ("blue", "green", "yellow", "red")}
		for y in range(0, heatmap.get_height(), 6):
			for x in range(0, heatmap.get_width(), 6):
				color = self.heatmap_color(heatmap.get_at((x, y)))
				if color:
					regions[color].append((x, y))
		data = (heatmap, regions)
		self.heatmap_cache[cache_key] = data
		return data

	def move_mouse_toward_heatmap(self):
		if self.scene != "activity" or not self.active_brain:
			return
		data = self.get_heatmap_data(self.active_brain)
		if not data:
			return
		heatmap, regions = data
		mouse_x, mouse_y = self.gaze_position
		mouse_x = max(0, min(heatmap.get_width() - 1, mouse_x))
		mouse_y = max(0, min(heatmap.get_height() - 1, mouse_y))
		zone = self.heatmap_color(heatmap.get_at((mouse_x, mouse_y)))
		targets = regions["red"]
		if not targets:
			return

		target_x, target_y = min(
			targets,
			key=lambda point: (point[0] - mouse_x) ** 2 + (point[1] - mouse_y) ** 2,
		)
		steps = {None: 7.0, "blue": 5.2, "green": 3.8, "yellow": 2.4, "red": 1.0}
		step = steps[zone]
		delta_x, delta_y = target_x - mouse_x, target_y - mouse_y
		distance = (delta_x * delta_x + delta_y * delta_y) ** 0.5
		if distance <= step or distance == 0:
			new_position = (target_x, target_y)
		else:
			new_position = (
				round(mouse_x + delta_x / distance * step),
				round(mouse_y + delta_y / distance * step),
			)
		self.gaze_position = new_position
		pygame.mouse.set_pos(new_position)

	def handle_mouse_motion(self, position):
		self.gaze_position = position

	def get_gaze_mask(self):
		if self.gaze_mask is None:
			gaze = self.load_image("etc/gaze.png")
			if gaze is None:
				return None
			shape = pygame.mask.from_threshold(
				gaze,
				(217, 217, 217, 255),
				(48, 48, 48, 0),
			)
			mask_surface = shape.to_surface(
				setcolor=(255, 255, 255, 255),
				unsetcolor=(0, 0, 0, 0),
			)
			self.gaze_mask = pygame.transform.smoothscale(mask_surface, (320, 240))
		return self.gaze_mask

	def draw_activity(self):
		self.background("bg/ActivityBG.png")
		side_rect = pygame.Rect(0, 0, 228, HEIGHT)
		pygame.draw.rect(self.screen, COLORS["paper"], side_rect)
		pygame.draw.line(self.screen, COLORS["teal_dark"], (228, 0), (228, HEIGHT), 3)
		draw_text(self.screen, "FILES", self.heading_font, COLORS["ink"], (22, 24))
		for index, name in enumerate(BRAINS):
			row = pygame.Rect(12, 88 + index * 92, 204, 76)
			if name == self.active_brain:
				pygame.draw.rect(self.screen, (223, 237, 221), row, border_radius=6)
			brain_rect = pygame.Rect(18, row.y + 6, 112, 62)
			brain = self.load_image(f"ppl/Brains/{name}Brain.png", (92, 60), black_transparent=True)
			if brain:
				self.screen.blit(brain, brain.get_rect(center=brain_rect.center))
			draw_text(self.screen, name, self.small_font, COLORS["ink"], (75, row.y + 62), center=True)
			file_rect = pygame.Rect(158, row.y + 13, 48, 42)
			file_image = self.load_image("etc/File.png", (48, 42), black_transparent=True)
			if file_image:
				self.screen.blit(file_image, file_rect)
			pygame.draw.rect(self.screen, COLORS["ink"], file_rect, width=1, border_radius=4)

		title = f"Looking through {self.active_brain}'s eyes" if self.active_brain else f"{self.activity_type.title()} activity"
		draw_text(self.screen, title, self.heading_font, COLORS["ink"], (260, 22))
		draw_text(self.screen, "Click a brain to view through their eyes. Click its file to edit it.", self.small_font, COLORS["muted"], (260, 69))

		view_rect = pygame.Rect(258, 108, 680, 520)
		content = pygame.Surface(view_rect.size)
		content.fill(COLORS["paper"])
		stimulus = pygame.Surface(view_rect.size, pygame.SRCALPHA)
		pygame.draw.rect(content, COLORS["teal_dark"], content.get_rect(), width=3, border_radius=8)
		if self.activity_type == "reading":
			current_index = self.current_activity_index()
			title_text, excerpt = READING_EXCERPTS[current_index]
			draw_text(content, title_text, self.heading_font, COLORS["teal_dark"], (36, 34))
			draw_wrapped(stimulus, excerpt, self.font, COLORS["ink"], pygame.Rect(36, 112, 600, 290), line_gap=8)
			draw_text(content, f"Excerpt {current_index + 1}", self.small_font, COLORS["muted"], (36, 464))
		else:
			image_paths = sorted((ASSET_DIR / "etc" / "images_activity").glob("*.png"))
			if image_paths:
				path = image_paths[self.current_activity_index()]
				relative = path.relative_to(ASSET_DIR)
				image = self.load_image(relative, (610, 435))
				if image:
					stimulus.blit(image, image.get_rect(center=(340, 260)))
			draw_text(content, f"Image {self.current_activity_index() + 1}", self.small_font, COLORS["muted"], (36, 474))

		self.screen.blit(content, view_rect)
		if self.active_brain:
			try:
				blurred_stimulus = pygame.transform.box_blur(stimulus, 5)
			except AttributeError:
				small = pygame.transform.smoothscale(stimulus, (170, 130))
				blurred_stimulus = pygame.transform.smoothscale(small, view_rect.size)
			self.screen.blit(blurred_stimulus, view_rect)

			gaze = self.get_gaze_mask()
			if gaze:
				mouse_x, mouse_y = self.gaze_position
				local_gaze_rect = gaze.get_rect(
					center=(mouse_x - view_rect.left, mouse_y - view_rect.top)
				)
				aperture = pygame.Surface(view_rect.size, pygame.SRCALPHA)
				aperture.blit(gaze, local_gaze_rect)
				clear_stimulus = stimulus.copy()
				clear_stimulus.blit(aperture, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
				self.screen.blit(clear_stimulus, view_rect)
		else:
			self.screen.blit(stimulus, view_rect)

		if self.active_brain and self.show_heatmaps:
			data = self.get_heatmap_data(self.active_brain)
			if data:
				heatmap_overlay = data[0].copy()
				heatmap_overlay.set_alpha(170)
				self.screen.blit(heatmap_overlay, (0, 0))

		footer = "Enter: next excerpt" if self.activity_type == "reading" else "Enter: next image"
		if self.active_brain:
			footer += "    X: stop looking through this brain"
		else:
			footer += "    X: return to selection"
		draw_text(self.screen, footer, self.small_font, COLORS["ink"], (260, 661))
		open_file = self.load_image("etc/File(Open).png", self.notes_button_rect.size, black_transparent=True)
		if open_file:
			self.screen.blit(open_file, self.notes_button_rect)
		else:
			self.button(self.notes_button_rect, "NOTES", COLORS["gold"])

	def draw_activity_notes(self):
		self.background("bg/ActivityBG.png")
		self.panel(pygame.Rect(70, 55, 820, 610))
		draw_text(self.screen, "Dr. Guy's notes", self.heading_font, COLORS["ink"], (112, 90))
		self.button(self.close_notes_rect, "X", COLORS["coral"])
		draw_text(self.screen, "Observation excerpt", self.font, COLORS["teal_dark"], (112, 170))
		if self.activity_type == "reading":
			notes = (
				"Insert paragraph about reading patterns, lack of focus, and how that relates to ASD. "
			)
		else:
			notes = (
				"Insert paragraph about how people with ASD tend to focus on different areas of a person's face"
                "than neurotypical individuals"
			)
		draw_wrapped(
			self.screen,
			notes,
			self.font,
			COLORS["ink"],
			pygame.Rect(112, 220, 724, 260),
			line_gap=8,
		)
		draw_text(
			self.screen,
			"These activities are for observation only and are not a diagnostic tool.",
			self.small_font,
			COLORS["muted"],
			(112, 570),
		)

	def draw_won(self):
		self.background("bg/MainMenuBG.png")
		self.panel(pygame.Rect(170, 205, 620, 280))
		draw_text(self.screen, "GAME WON!", self.big_font, COLORS["green"], (WIDTH // 2, 280), center=True)
		draw_text(self.screen, "You checked every file correctly.", self.font, COLORS["ink"], (WIDTH // 2, 350), center=True)
		self.button(pygame.Rect(360, 410, 240, 56), "PLAY AGAIN", COLORS["gold"])

	def draw_cursor(self):
		x, y = self.gaze_position
		outer_points = [
			(x, y), (x + 2, y + 25), (x + 8, y + 19),
			(x + 15, y + 31), (x + 21, y + 28),
			(x + 14, y + 16), (x + 23, y + 15),
		]
		inner_points = [(x + 3, y + 5), (x + 5, y + 19), (x + 9, y + 15), (x + 16, y + 27), (x + 17, y + 26), (x + 10, y + 14), (x + 18, y + 14)]
		pygame.draw.polygon(self.screen, COLORS["ink"], outer_points)
		pygame.draw.polygon(self.screen, COLORS["paper"], inner_points)
		pygame.draw.circle(self.screen, COLORS["coral"], (x + 5, y + 7), 2)

	def open_file(self, name, return_scene):
		self.open_brain = name
		self.file_return_scene = return_scene
		self.note_focused = False
		self.scene = "file"
		pygame.key.stop_text_input()

	def return_from_file(self):
		self.scene = self.file_return_scene
		self.note_focused = False
		if self.scene == "file":
			self.scene = "selection"

	def check_answers(self):
		if not all(self.player_data[name]["choice"] for name in BRAINS):
			self.selection_notice = "Choose ASD or Neurotypical in all six files first."
			return
		if all(self.player_data[name]["choice"] == ANSWER_KEY[name] for name in BRAINS):
			self.scene = "won"
		else:
			self.selection_notice = "Not all correct. Review the files and try again."

	def handle_click(self, position):
		if self.scene == "title":
			if pygame.Rect(365, 500, 230, 64).collidepoint(position):
				self.reset_brain_files()
				self.selection_notice = ""
				self.activity_index = 0
				self.active_brain = None
				self.show_heatmaps = False
				self.scene = "dialogue"
				self.dialogue_index = 0
		elif self.scene == "selection":
			for name, rect in self.file_button_rects.items():
				if rect.collidepoint(position):
					self.open_file(name, "selection")
					return
			if pygame.Rect(190, 480, 170, 58).collidepoint(position):
				self.activity_type = "reading"
				self.activity_index = 0
				self.active_brain = None
				self.scene = "activity"
			elif pygame.Rect(395, 480, 170, 58).collidepoint(position):
				self.activity_type = "images"
				self.activity_index = 0
				self.active_brain = None
				self.scene = "activity"
			elif pygame.Rect(600, 480, 220, 58).collidepoint(position):
				self.check_answers()
		elif self.scene == "file":
			if pygame.Rect(120, 606, 145, 42).collidepoint(position):
				self.return_from_file()
				return
			for index, category in enumerate(CATEGORIES):
				rect = pygame.Rect(500, 180 + index * 58, 340, 42)
				if rect.collidepoint(position):
					self.player_data[self.open_brain]["choice"] = category
					self.save_brain_data(self.open_brain)
					return
			self.note_focused = pygame.Rect(120, 448, 720, 140).collidepoint(position)
			if self.note_focused:
				pygame.key.start_text_input()
			else:
				pygame.key.stop_text_input()
		elif self.scene == "activity":
			if self.notes_button_rect.collidepoint(position):
				self.scene = "activity_notes"
				return
			for index, name in enumerate(BRAINS):
				row_y = 88 + index * 92
				if pygame.Rect(18, row_y + 4, 116, 68).collidepoint(position):
					self.active_brain = None if self.active_brain == name else name
					self.gaze_position = position
					return
				if pygame.Rect(158, row_y + 13, 48, 42).collidepoint(position):
					self.open_file(name, "activity")
					return
		elif self.scene == "activity_notes":
			if self.close_notes_rect.collidepoint(position):
				self.scene = "activity"
		elif self.scene == "won" and pygame.Rect(360, 410, 240, 56).collidepoint(position):
			self.scene = "title"
			self.dialogue_index = 0

	def handle_key(self, event):
		if self.scene == "dialogue" and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
			self.dialogue_index += 1
			if self.dialogue_index >= len(DIALOGUE):
				self.scene = "selection"
		elif self.scene == "activity":
			if event.key == pygame.K_y:
				self.show_heatmaps = not self.show_heatmaps
			elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
				item_count = self.activity_item_count()
				if item_count:
					self.activity_index = (self.activity_index + 1) % item_count
			elif event.key == pygame.K_x:
				if self.active_brain:
					self.active_brain = None
				else:
					self.scene = "selection"
		elif self.scene == "activity_notes" and event.key == pygame.K_ESCAPE:
			self.scene = "activity"
		elif self.scene == "file" and self.note_focused and event.key == pygame.K_BACKSPACE:
			notes = self.player_data[self.open_brain]["notes"]
			self.player_data[self.open_brain]["notes"] = notes[:-1]
			self.save_brain_data(self.open_brain)
		elif self.scene == "file" and event.key == pygame.K_ESCAPE:
			self.return_from_file()

	def handle_text(self, text):
		if self.scene != "file" or not self.note_focused:
			return
		data = self.player_data[self.open_brain]
		remaining = NOTE_LIMIT - len(data["notes"])
		if remaining > 0:
			data["notes"] += text[:remaining]
			self.save_brain_data(self.open_brain)

	def draw(self):
		if self.scene == "title":
			self.draw_title()
		elif self.scene == "dialogue":
			self.draw_dialogue()
		elif self.scene == "selection":
			self.draw_selection()
		elif self.scene == "file":
			self.draw_file()
		elif self.scene == "activity":
			self.draw_activity()
		elif self.scene == "activity_notes":
			self.draw_activity_notes()
		elif self.scene == "won":
			self.draw_won()
		self.draw_cursor()
		pygame.display.flip()

	def run(self, max_frames=None):
		running = True
		frames = 0
		while running and (max_frames is None or frames < max_frames):
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.MOUSEMOTION:
					self.handle_mouse_motion(event.pos)
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					self.handle_click(event.pos)
				elif event.type == pygame.TEXTINPUT:
					self.handle_text(event.text)
				elif event.type == pygame.KEYDOWN:
					self.handle_key(event)
			self.move_mouse_toward_heatmap()
			self.draw()
			self.clock.tick(FPS)
			frames += 1
		return running


def main():
	game = BrainGame()
	game.run()
	pygame.mouse.set_visible(True)
	pygame.quit()


if __name__ == "__main__":
	main()
