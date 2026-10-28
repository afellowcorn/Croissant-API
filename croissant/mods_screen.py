import i18n
import pygame
import pygame_gui

from scripts.game_structure import game, image_cache
from scripts.game_structure.game.settings import (
	game_settings_save,
	game_setting_toggle,
	game_setting_get,
	game_setting_set,
)
from scripts.game_structure.screen_settings import MANAGER

from scripts.ui.elements.modified_scrolling_container import UIModifiedScrollingContainer
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from scripts.ui.theme import get_text_box_theme

from scripts.screens.Screens import Screens
from croissant.croissant import Croissant as CR

class ModsScreen(Screens):
	settings_changed = False

	def __init__(self, name="mods_screen"):
		super().__init__(name)
		self.toggled_theme = "dark" if game_setting_get("dark mode") else "light"

		if not CR.mod_list:
			CR.load_mods()

		self.back_button = None
		self.save_button = None

		self.enabled_mods = None
		self.list_frame = None
		self.mod_list_container = None
		self.mod_buttons = {}

		self.disabled_mods = None
		self.disabled_list_frame = None
		self.disabled_mod_list_container = None
		self.disabled_mod_buttons = {}

		self.up_order_buttons = {}
		self.down_order_buttons = {}

		self.selected_info = {
			"enabled": "",
			"mod_id": "",
			"name": "",
			"version": "",
			"description": "",
			"dependency_name": "",
		}

		self.enable_button = None

		self.info_frame = None
		self.info_container = None
		self.info_text = {}

		self.set_self_values()

	def handle_event(self, event):
		if event.type == pygame_gui.UI_BUTTON_START_PRESS:
			self.mute_button_pressed(event)

			# RETURN
			if event.ui_element == self.back_button:
				self.change_screen(game.last_screen_forupdate)
				return
			elif event.ui_element == self.save_button:
				self.save_changes()
				return

			# SELECT MOD
			elif event.ui_element in self.mod_buttons.values():
				for index, button in self.mod_buttons.items():
					if button == event.ui_element:
						self.kill_info_display()
						self.set_mod_info(self.enabled_mods[index])
						self.create_info_display()
						break
			elif event.ui_element in self.disabled_mod_buttons.values():
				for index, button in self.disabled_mod_buttons.items():
					if button == event.ui_element:
						self.kill_info_display()
						self.set_mod_info(self.disabled_mods[index])
						self.create_info_display()
						break

			# ORDER UP
			elif event.ui_element in self.up_order_buttons.values():
				for index, button in self.up_order_buttons.items():
					if button == event.ui_element:
						self.kill_mod_buttons()
						mod = self.enabled_mods.pop(index)
						self.enabled_mods.insert(index-1, mod)
						self.create_mod_display()

			# ORDER DOWN
			elif event.ui_element in self.down_order_buttons.values():
				for index, button in self.down_order_buttons.items():
					if button == event.ui_element:
						self.kill_mod_buttons()
						mod = self.enabled_mods.pop(index)
						self.enabled_mods.insert(index+1, mod)
						self.create_mod_display()

			# ENABLE/DISABLE
			elif event.ui_element == self.enable_button:
				self.kill_info_display()
				self.kill_mod_buttons()
				self.change_enabled_state()
				self.create_mod_display()
				self.create_info_display()
				return

	def screen_switches(self):
		super().screen_switches()
		self.settings_changed = False

		self.back_button = UISurfaceImageButton(
			ui_scale(pygame.Rect((25, 25), (105, 30))),
			"buttons.back",
			get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
			manager=MANAGER,
			object_id="@buttonstyles_squoval",
			starting_height=1,
		)

		self.save_button = UISurfaceImageButton(
			ui_scale(pygame.Rect((30, 25), (150, 30))),
			"buttons.save_settings",
			get_button_dict(ButtonStyles.SQUOVAL, (150, 30)),
			object_id="@buttonstyles_squoval",
			manager=MANAGER,
			anchors={"left_target": self.back_button},
		)

		self.list_frame = pygame_gui.elements.UIImage(
			ui_scale(pygame.Rect((60, 80), (250, 350))),
			get_box(BoxStyles.ROUNDED_BOX, (250, 350)),
			starting_height=3,
			manager=MANAGER,
		)

		self.disabled_list_frame = pygame_gui.elements.UIImage(
			ui_scale(pygame.Rect((60, 0), (250, 220))),
			get_box(BoxStyles.ROUNDED_BOX, (250, 220)),
			starting_height=3,
			manager=MANAGER,
			anchors={"top_target": self.list_frame}
		)

		self.create_mod_display()

	def exit_screen(self):
		self.back_button.kill()
		self.save_button.kill()
		self.list_frame.kill()
		self.disabled_list_frame.kill()
		
		self.kill_mod_buttons()

		self.enable_button.kill()
		if self.info_frame:
			self.info_frame.kill()
			if self.info_text:
				for ele in self.info_text.values():
					ele.kill()
				self.info_text.clear()

		self.clear_mod_info()

		self.toggled_theme = "dark" if game_setting_get("dark mode") else "light"

	def on_use(self):
		self.show_bg(theme=self.toggled_theme)

	def set_self_values(self):
		self.enabled_mods = CR.enabled_mods
		self.disabled_mods = [x.mod_id for x in CR.mod_list.values() if not x.enabled]

	def create_mod_display(self):
		self.kill_mod_buttons()

		if not self.mod_list_container:
			self.mod_list_container = UIModifiedScrollingContainer(
				ui_scale(pygame.Rect((68, 90), (236, 330))),
				starting_height=3,
				manager=MANAGER,
				allow_scroll_y=True,
			)

		for index, mod in enumerate(self.enabled_mods):
			self.mod_buttons[index] = UISurfaceImageButton(
				ui_scale(pygame.Rect((0, -2 if index > 0 else 0), (234, 36))),
				CR.mod_list[mod].name,
				get_button_dict(ButtonStyles.DROPDOWN, (234, 36)),
				manager=MANAGER,
				object_id="@buttonstyles_dropdown",
				starting_height=1,
				anchors={"top_target": self.mod_buttons[index - 1]}
				if self.mod_buttons.get(index - 1)
				else None,
				container=self.mod_list_container,
			)
			self.up_order_buttons[index] = UIImageButton(
				ui_scale(pygame.Rect((10, 2 if index == 0 else 0), (16, 16))),
				text="",
				manager=MANAGER,
				object_id="#vertical_slider_up_arrow_button",
				anchors={"top_target": self.mod_buttons[index -1]}
				if self.mod_buttons.get(index - 1)
				else None,
				container=self.mod_list_container,
			)
			self.down_order_buttons[index] = UIImageButton(
				ui_scale(pygame.Rect((10, -1), (16, 16))),
				text="",
				manager=MANAGER,
				object_id="#vertical_slider_down_arrow_button",
				anchors={"top_target": self.up_order_buttons[index]},
				container=self.mod_list_container,
			)

		if not self.disabled_mod_list_container:
			self.disabled_mod_list_container = UIModifiedScrollingContainer(
				ui_scale(pygame.Rect((68, 20), (236, 200))),
				starting_height=3,
				manager=MANAGER,
				allow_scroll_y=True,
				anchors={"top_target": self.mod_list_container}
			)

		for index, mod in enumerate(self.disabled_mods):
			self.disabled_mod_buttons[index] = UISurfaceImageButton(
				ui_scale(pygame.Rect((0, -2 if index > 0 else 0), (234, 36))),
				CR.mod_list[mod].name,
				get_button_dict(ButtonStyles.DROPDOWN, (234, 36)),
				manager=MANAGER,
				object_id="@buttonstyles_dropdown",
				starting_height=1,
				anchors={"top_target": self.disabled_mod_buttons[index - 1]}
				if self.disabled_mod_buttons.get(index - 1)
				else None,
				container=self.disabled_mod_list_container,
			)

	def kill_mod_buttons(self):
		for mod in self.mod_buttons:
			self.mod_buttons[mod].kill()
		if self.mod_list_container:
			self.mod_list_container.kill()

		for mod in self.disabled_mod_buttons:
			self.disabled_mod_buttons[mod].kill()
		if self.disabled_mod_list_container:
			self.disabled_mod_list_container.kill()

		for ele in self.up_order_buttons:
			self.up_order_buttons[ele].kill()
		for ele in self.down_order_buttons:
			self.down_order_buttons[ele].kill()

	def create_info_display(self):
		self.info_frame = pygame_gui.elements.UIImage(
			ui_scale(pygame.Rect((300, 100), (470, 490))),
			get_box(BoxStyles.FRAME, (470, 490)),
			starting_height=2,
			manager=MANAGER,
		)
		self.info_container = UIModifiedScrollingContainer(
			ui_scale(pygame.Rect((314, 110), (490, 430))),
			starting_height=4,
			manager=MANAGER,
			allow_scroll_y=True,
		)
		self.info_container.scrollable_container.resize_top = False

		self.info_text["name"] = pygame_gui.elements.UITextBox(
			f"<b>{self.selected_info["name"]}</b>",
			ui_scale(pygame.Rect((0, 0), (310, -1))),
			object_id=get_text_box_theme("#text_box_30_horizcenter"),
			manager=MANAGER,
			container=self.info_container,
		)
		self.info_text["id"] = pygame_gui.elements.UITextBox(
			f"ID: <i>{self.selected_info["mod_id"]}</i>",
			ui_scale(pygame.Rect((30, 0), (400, -1))),
			object_id=get_text_box_theme("#text_box_30_horizleft"),
			manager=MANAGER,
			container=self.info_container,
			anchors={
				"top_target": self.info_text["name"],
			},
		)
		self.info_text["version"] = pygame_gui.elements.UITextBox(
			f"Version: {self.selected_info["version"]}",
			ui_scale(pygame.Rect((0, 0), (130, -1))),
			object_id=get_text_box_theme("#text_box_30_horizleft"),
			manager=MANAGER,
			container=self.info_container,
			anchors={
				"left_target": self.info_text["name"],
			},
		)
		self.info_text["name_divider"] = pygame_gui.elements.UIImage(
			ui_scale(pygame.Rect((0, -12), (600, 24))),
			pygame.transform.scale(
				image_cache.load_image("resources/images/spacer.png").convert_alpha(),
				ui_scale_dimensions((600, 24)),
			),
			container=self.info_container,
			manager=MANAGER,
			anchors={"top_target": self.info_text["id"]},
		)
		self.info_text["description"] = pygame_gui.elements.UITextBox(
			self.selected_info["description"],
			ui_scale(pygame.Rect((0, 0), (440, -1))),
			object_id=get_text_box_theme("#text_box_30_horizleft"),
			manager=MANAGER,
			container=self.info_container,
			anchors={
				"top_target": self.info_text["name_divider"],
			},
		)

		if self.selected_info.get("dependency_name"):
			if self.selected_info.get("description"):
				self.info_text["desc_divider"] = pygame_gui.elements.UIImage(
					ui_scale(pygame.Rect((0, -12), (600, 24))),
					pygame.transform.scale(
						image_cache.load_image("resources/images/spacer.png").convert_alpha(),
						ui_scale_dimensions((600, 24)),
					),
					container=self.info_container,
					manager=MANAGER,
					anchors={"top_target": self.info_text["description"]},
				)
			self.info_text["dependency"] = pygame_gui.elements.UITextBox(
				f"Dependencies: {self.selected_info["dependency_name"]}",
				ui_scale(pygame.Rect((0, 0), (460, -1))),
				object_id=get_text_box_theme("#text_box_30_horizleft"),
				manager=MANAGER,
				container=self.info_container,
				anchors={
					"top_target": self.info_text["desc_divider"],
				},
			)

		if self.selected_info.get("enabled"):
			enable_text = "disable"
		else:
			enable_text = "enable"
		self.enable_button = UISurfaceImageButton(
			ui_scale(pygame.Rect((20, 15), (150, 30))),
			enable_text,
			get_button_dict(ButtonStyles.SQUOVAL, (150, 30)),
			object_id="@buttonstyles_squoval",
			manager=MANAGER,
			anchors={
				"top_target": self.info_frame,
				"left_target": self.disabled_mod_list_container,
			},
		)

	def kill_info_display(self):
		if self.info_container:
			self.info_frame.kill()
			self.info_container.kill()
		if self.enable_button:
			self.enable_button.kill()

	def set_mod_info(self, mod):
		self.clear_mod_info()
		for key in self.selected_info.keys():
			val = getattr(CR.mod_list[mod], key)
			if val:
				if key == "dependency_name":
					for name in val:
						self.selected_info[key].join(f", {name}")
					continue
				self.selected_info[key] = val

	def clear_mod_info(self):
		for key in self.selected_info.keys():
			self.selected_info[key] = ""

	def change_enabled_state(self):
		mod = self.selected_info["mod_id"]
		if self.selected_info["enabled"]:
			enable = False
		else:
			enable = True
		CR._update_mod_list(mod, enable)
		self.set_self_values()
		self.selected_info.update({"enabled": enable})

	def save_changes(self):
		CR._save_mod_list()