# -*- coding: utf-8 -*-
# Copyright (c) 2020 BuildGroup Data Services Inc.
import importlib
import sys

from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError
from django.db import connections


class CaravaggioBaseCommand(BaseCommand):
    """CaravaggioBaseCommand class. attrs: `sub_commands` (dict)"""

    argv = []
    sub_commands = {}
    loaded_sub_commands = {}

    @staticmethod
    def _get_class_from_name(class_name):
        module_name = ".".join(class_name.split(".")[:-1])
        clazz_name = class_name.split(".")[-1]

        module = importlib.import_module(module_name)
        return getattr(module, clazz_name)

    def _get_current_parent_module(self):
        raise NotImplementedError()

    def _get_command_class_by_name(self, command_file_name):
        current_module = self._get_current_parent_module()

        sub_command = "%s.sub_commands.%s.Command" % (current_module, command_file_name)
        sub_command_class = self._get_class_from_name(sub_command)

        return sub_command_class

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="sub_command", title="sub_commands", description="")
        subparsers.required = True

        for command_name, command_file_name in self.sub_commands.items():
            command_class = self._get_command_class_by_name(command_file_name)
            command = command_class()

            self.loaded_sub_commands[command_name] = command_class

            subparser = subparsers.add_parser(command_name, help=command_class.help)
            command.add_arguments(subparser)

    def run_from_argv(self, argv):
        self.argv = argv
        return super().run_from_argv(argv)

    def handle(self, *args, **options):
        command_name = self.argv[2]

        if command_name not in self.loaded_sub_commands:
            raise ValueError("Unknown sub_command: %" % command_name)

        command_class = self.loaded_sub_commands[command_name]

        if len(self.argv):
            args = [self.argv[0]] + self.argv[2:]
            return command_class().run_from_argv(args)
        return command_class().execute(*args, **options)


class CaravaggioSubCommand(BaseCommand):
    """CaravaggioSubCommand class."""

    def run_from_argv(self, argv):
        parser = self.create_parser(argv[0], argv[1])
        options, known_args = parser.parse_known_args(argv[2:])

        cmd_options = vars(options)
        args = cmd_options.pop("args", ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            if options.traceback or not isinstance(e, CommandError):
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write("%s: %s" % (e.__class__.__name__, e))
            sys.exit(1)
        finally:
            try:
                connections.close_all()
            except ImproperlyConfigured:
                # Ignore if connections aren't setup at this point (e.g. no
                # configured settings).
                pass

    def handle(self, *args, **options):
        raise NotImplementedError
