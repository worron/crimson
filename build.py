#!/usr/bin/python3

import os
import sys
import subprocess
import logging

from argparse import ArgumentParser
from tempfile import NamedTemporaryFile


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


# Script environment setup
_base_path = os.path.dirname(os.path.abspath(__file__))
_pattern_path = os.path.join(_base_path, 'patterns')
_theme_path = os.path.join(_base_path, 'crimson')

_font_list = (
	{'file': 'iosevka-term-medium.ttf', 'size': '26', 'name': 'IosevkaM26'},
	{'file': 'Trump_Town_Pro.otf', 'size': '42', 'name': 'Trump42'}
)


# Script functions
def _run(cmd):
	try:
		subprocess.call(cmd)
		logger.debug("Successfully executed:\n{0}".format(' '.join(cmd)))
	except Exception as e:
		logger.error("Fail to run command\n{0}\n\n{1}".format(' '.join(cmd), e))
		sys.exit(1)


def _create_dir(dir_):
	if not os.path.exists(dir_):
		os.makedirs(dir_)
		logger.info("New folder created:\n{0}".format(dir_))


def build_images(options):
	tmp_file = NamedTemporaryFile(delete=False)
	replacements = {
		'$main-color': options.main_color,
		'$second-color': options.second_color,
		'$bg-color': options.bg_color
	}

	for root, dirs, files in os.walk(_pattern_path):
		for file_ in filter(lambda f: f.endswith('.pat'), files):
			logger.debug("Creating image from pattern '{0}'".format(file_))
			with open(os.path.join(root, file_), 'r') as source_, open(tmp_file.name, 'r+') as output_:
				txt = source_.read()
				for k, v in replacements.items():
					txt = txt.replace(k, v)

				output_.seek(0)
				output_.truncate()
				output_.write(txt)

			png_file = os.path.join(_theme_path, file_.replace('.pat', '.png'))
			_run(['rsvg-convert', tmp_file.name, '-o', png_file])

	# tmp_file.close()
	os.unlink(tmp_file.name)


def build_config(options):
	replacements = {
		'$main-color': options.main_color,
		'$second-color': options.second_color,
	}

	logger.debug("Creating theme file from pattern")
	config_pattern = os.path.join(_pattern_path, 'theme.tpt')
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
		background = os.path.join(_theme_path, 'terminal_bg.png')

	_run(['cp', background, os.path.join(_theme_path, 'background.png')])


def build_fonts(font_list):
	for font in font_list:
		logger.debug("Converting font '{0}'".format(font['file']))
		input_file = os.path.join(_pattern_path, font['file'])
		output_file = os.path.join(_theme_path, font['name'] + '.pf2',)

		convert_cmd = ['grub-mkfont', input_file, '-s', font['size'], '-n', font['name'], '-o', output_file]
		_run(convert_cmd)


def build_theme(options):
	_create_dir(_theme_path)

	build_images(options)
	build_config(options)
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
