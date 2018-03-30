#!/usr/bin/python3

import os
import sys
import subprocess

from argparse import ArgumentParser
from tempfile import NamedTemporaryFile


_base_path = os.path.dirname(os.path.abspath(__file__))
_pattern_path = os.path.join(_base_path, 'patterns')
_theme_path = os.path.join(_base_path, 'crimson')


def _run(cmd):
	try:
		subprocess.call(cmd)
	except Exception as e:
		print("Fail to run command\n{0}\n\n{1}".format(' '.join(cmd), e))
		sys.exit()


def _create_dir(dir_):
	if not os.path.exists(dir_):
		os.makedirs(dir_)


def build_images(options):
	tmp_file = NamedTemporaryFile(delete=False)
	replacements = {
		'$main-color': options.main_color,
		'$second-color': options.second_color,
		'$bg-color': options.bg_color
	}

	for root, dirs, files in os.walk(_pattern_path):
		for file_ in filter(lambda f: f.endswith('.pat'), files):
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
		print("Using default background")
		background = os.path.join(_theme_path, 'terminal_bg.png')

	_run(['cp', background, os.path.join(_theme_path, 'background.png')])


def build_theme(options):
	print(options)
	_create_dir(_theme_path)

	build_images(options)
	build_config(options)
	build_background(options.background)


def parse_command_line():
	parser = ArgumentParser()
	parser.add_argument('--background', '-i', metavar='FILE', help='Background image')
	parser.add_argument('--main-color', '-m', metavar='RRGGBB', default='CB252D', help='Main theme color')
	parser.add_argument('--second-color', '-s', metavar='RRGGBB', default='CCCCCC', help='Second theme color')
	parser.add_argument('--bg-color', '-b', metavar='RRGGBB', default='1A1A1A', help='Background theme color')

	options = parser.parse_args()

	if isinstance(options.background, str) and options.background[0] != '/':
		options.background = os.path.join(_base_path, options.background)

	return options


if __name__ == "__main__":
	args = parse_command_line()
	build_theme(args)
