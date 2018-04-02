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
_console_bg = 'terminal_bg.png'
_ipe = '.pat'  # image pattern extension

_font_list = (
	{'file': 'iosevka-term-medium.ttf', 'size': '26', 'name': 'IosevkaM26'},
	{'file': 'Trump_Town_Pro.otf', 'size': '42', 'name': 'Trump42'}
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
			logger.debug("Creating image from pattern '{0}'".format(file_))
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
	logger.debug("Creating theme file from pattern '{0}'".format(theme_pattern))
	config_pattern = os.path.join(_pattern_path, theme_pattern)
	config_file = os.path.join(_theme_path, 'theme.txt')

	with open(config_pattern, 'r') as source_, open(config_file, 'w') as output_:
		txt = source_.read()
		for k, v in replacements.items():
			txt = txt.replace(k, v)
		output_.write(txt)


def build_background(image):
	if image is not None and os.path.isfile(image):
		background = image
	else:
		logger.warning("No background image specified, using console background color as fallback")
		background = os.path.join(_theme_path, _console_bg)

	_run(['cp', background, os.path.join(_theme_path, 'background.png')])


def build_fonts(font_list):
	for font in font_list:
		logger.debug("Converting font '{0}'".format(font['file']))
		input_file = os.path.join(_pattern_path, font['file'])
		output_file = os.path.join(_theme_path, font['name'] + '.pf2',)

		convert_cmd = ['grub-mkfont', input_file, '-s', font['size'], '-n', font['name'], '-o', output_file]
		_run(convert_cmd)


def build_theme(options):
	replacements = {
		'$main-color': options.main_color,
		'$second-color': options.second_color,
		'$bg-color': options.bg_color
	}
	logger.debug(
		"Colors: main #{0}; second #{1}; bg #{2}".format(options.main_color, options.second_color, options.bg_color)
	)
	logger.debug("Background file: {0}".format(options.background))

	create_dir(_theme_path)
	build_images(replacements)
	build_config(replacements, _theme_pattern)
	build_background(options.background)
	build_fonts(_font_list)


def parse_command_line():
	parser = ArgumentParser()
	parser.add_argument('--background', '-i', metavar='FILE', help='Background image')
	parser.add_argument('--main-color', '-m', metavar='RRGGBB', default='CB252D', help='Main theme color')
	parser.add_argument('--second-color', '-s', metavar='RRGGBB', default='CCCCCC', help='Second theme color')
	parser.add_argument('--bg-color', '-b', metavar='RRGGBB', default='1A1A1A', help='Background theme color')
	parser.add_argument('--log-level', '-l', metavar='LEVEL', default='INFO', help='Log level')

	options = parser.parse_args()

	if isinstance(options.background, str) and options.background[0] != '/':
		options.background = os.path.join(_base_path, options.background)

	return options


if __name__ == "__main__":
	args = parse_command_line()
	logger.setLevel(logging.getLevelName(args.log_level))

	build_theme(args)
