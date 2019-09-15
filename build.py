#!/usr/bin/python3

import os
import sys
import subprocess
import logging

from argparse import ArgumentParser
from tempfile import NamedTemporaryFile


# Script environment setup
_base_path = os.path.dirname(os.path.abspath(__file__))
_pattern_path = os.path.join(_base_path, 'patterns')
_theme_path = os.path.join(_base_path, 'crimson')
_theme_pattern = 'theme.tpt'
_console_bg = 'terminal_c.png'
_ipe = '.pat'  # image pattern extension
_base_font_size = 26
_menu_font_size = 42

_font_list = {
	'base': {'file': 'iosevka-term-medium.ttf', 'name': 'IosevkaM'},
	'menu': {'file': 'Trump_Town_Pro.otf', 'name': 'Trump'}
}

_warning_message = (
	"The theme creation is complete. Beware that script doesn't verify input data and result. "
	"You can check the theme with 'grub2-theme-preview' utility or some virtual machine to be safe."
)

# Logger setup
CI = dict(zip(("BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"), range(8)))
COLORS = {'WARNING': CI["YELLOW"], 'INFO': CI["GREEN"], 'DEBUG': CI["BLUE"], 'CRITICAL': CI["RED"], 'ERROR': CI["RED"]}

RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[0;%dm"
BOLD_SEQ = "\033[1m"

COLOR_PACK = list(('$' + color, COLOR_SEQ % (30 + CI[color])) for color in CI.keys())
MESSAGE_PATTERN = "$COLOR$BOLD%(levelname)s $RESET$COLOR(L%(lineno)d): $RESET%(message)s"


class ColoredFormatter(logging.Formatter):
	def format(self, record):
		level_color = COLOR_SEQ % (30 + COLORS[record.levelname])
		message = super().format(record)
		for rep in [('$RESET', RESET_SEQ), ('$BOLD', BOLD_SEQ), ('$COLOR', level_color)] + COLOR_PACK:
			message = message.replace(*rep)
		return message + RESET_SEQ


logger = logging.getLogger(__name__)
color_formatter = ColoredFormatter(MESSAGE_PATTERN)
stream_handler = logging.StreamHandler(stream=sys.stdout)

stream_handler.setFormatter(color_formatter)
logger.addHandler(stream_handler)


# Script functions
def _run(cmd):
	try:
		subprocess.call(cmd)
		logger.debug("Successfully executed: {0}".format(' '.join(cmd)))
	except Exception as e:
		logger.error("Fail to run command: {0}\n{1}".format(' '.join(cmd), e))
		sys.exit(1)


def create_dir(dir_):
	if not os.path.exists(dir_):
		os.makedirs(dir_)
		logger.info("New folder created:\n{0}".format(dir_))


def build_images(replacements):
	tmp_file = NamedTemporaryFile(delete=False)

	for root, dirs, files in os.walk(_pattern_path):
		for file_ in filter(lambda f: f.endswith(_ipe), files):
			logger.debug("Creating image from the pattern '{0}'".format(file_))
			with open(os.path.join(root, file_), 'r') as source_, open(tmp_file.name, 'r+') as output_:
				txt = source_.read()
				for k, v in replacements.items():
					txt = txt.replace(k, v)

				output_.seek(0)
				output_.truncate()
				output_.write(txt)

			png_file = os.path.join(_theme_path, file_.replace(_ipe, '.png'))
			_run(['rsvg-convert', tmp_file.name, '-o', png_file])

	# tmp_file.close()
	os.unlink(tmp_file.name)


def build_config(replacements, theme_pattern):
	logger.debug("Creating theme file from the pattern '{0}'".format(theme_pattern))
	config_pattern = os.path.join(_pattern_path, theme_pattern)
	config_file = os.path.join(_theme_path, 'theme.txt')

	with open(config_pattern, 'r') as source_, open(config_file, 'w') as output_:
		txt = source_.read()
		for k, v in replacements.items():
			txt = txt.replace(k, v)
		output_.write(txt)


def build_background(source_, bg_destination, name):
	if isinstance(source_, str) and source_[0] != '/':
		source_ = os.path.join(_base_path, source_)

	if source_ is not None and os.path.isfile(source_):
		background = source_
	else:
		logger.info("No {0} background image specified, using console {1} as fallback".format(*name))
		background = os.path.join(_theme_path, _console_bg)

	new_background = os.path.join(_theme_path, bg_destination)
	if background != new_background:
		_run(['cp', background, new_background])


def build_fonts(font_list):
	for font in font_list.values():
		logger.debug("Converting font '{0}'".format(font['file']))
		input_file = os.path.join(_pattern_path, font['file'])
		output_file = os.path.join(_theme_path, font['name'] + '.pf2',)

		convert_cmd = ['grub-mkfont', input_file, '-s', font['size'], '-n', font['name'], '-o', output_file]
		_run(convert_cmd)


def build_theme(options):
	replacements = {
		'$main-color': options.main_color,
		'$second-color': options.second_color,
		'$bg-color': options.bg_color,

		'$console-margin': str(options.console_margin) + '%',
		'$console-size': str(100 - 2*options.console_margin) + '%',

		'$base_font_size': str(options.base_font_size),
		'$menu_font_size': str(options.menu_font_size),
	}

	_font_list['base']['size'] = str(options.base_font_size)
	_font_list['menu']['size'] = str(options.menu_font_size)

	logger.debug(
		"Colors: main #{0}; second #{1}; bg #{2}".format(options.main_color, options.second_color, options.bg_color)
	)
	logger.debug("Main background file: {0}".format(options.background))
	logger.debug("Console background file: {0}".format(options.console_background))
	logger.debug("Console margin: {0}%".format(options.console_margin))
	logger.debug("Base font size: {0}; menu font size: {1}".format(options.base_font_size, options.menu_font_size))

	create_dir(_theme_path)
	build_images(replacements)
	build_config(replacements, _theme_pattern)
	build_background(options.console_background, _console_bg, ("console", "color"))
	build_background(options.background, 'background.png', ("main", "background"))
	build_fonts(_font_list)


def parse_command_line():
	parser = ArgumentParser()
	parser.add_argument(
		'--background', '-i', metavar='FILE',
		help="Main background image."
	)
	parser.add_argument(
		'--console-background', '-c', metavar='FILE',
		help="Console background image."
	)
	parser.add_argument(
		'--main-color', '-m', metavar='RRGGBB', default='CB252D',
		help="Main color. Active menu items and some other elements."
	)
	parser.add_argument(
		'--second-color', '-s', metavar='RRGGBB', default='CCCCCC',
		help="Second color. Inactive menu items and some other elements."
	)
	parser.add_argument(
		'--bg-color', '-b', metavar='RRGGBB', default='1A1A1A',
		help="Console background color. Used as main background color if image not specified."
	)
	parser.add_argument(
		'--console-margin', type=int, default=2,
		help="Console margin in percents."
	)
	parser.add_argument(
		'--log-level', '-l', metavar='LEVEL', default='INFO',
		help='Log level [DEBUG, INFO, WARNING, ERROR, CRITICAL].'
	)
	parser.add_argument(
		'--base-font-size', type=int, default=_base_font_size,
		help="Console margin in percents."
	)
	parser.add_argument(
		'--menu-font-size', type=int, default=_menu_font_size,
		help="Console margin in percents."
	)

	options = parser.parse_args()
	return options


if __name__ == "__main__":
	args = parse_command_line()
	logger.setLevel(logging.getLevelName(args.log_level))

	build_theme(args)
	logger.info(_warning_message)
