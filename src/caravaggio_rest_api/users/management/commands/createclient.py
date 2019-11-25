"""
Management utility to create superusers.
"""
import getpass
import sys

from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.utils.text import capfirst

from caravaggio_rest_api.users.models import CaravaggioClient


class NotRunningInTTYException(Exception):
    pass


PASSWORD_FIELD = 'password'


class Command(BaseCommand):
    help = 'Used to create a new client.'
    requires_migrations_checks = True
    stealth_options = ('stdin',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_field = CaravaggioClient._meta.get_field("email")

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            help='Specifies the email for the new client.',
        )
        parser.add_argument(
            '--name',
            help='Specifies the name for the new client.',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false', dest='interactive',
            help=(
                'Tells Django to NOT prompt the user for input of any kind. '
                'You must use --email with --noinput, along with an option for'
                ' any other required field.'
            ),
        )
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )

    def execute(self, *args, **options):
        self.stdin = options.get('stdin', sys.stdin)  # Used for testing
        return super().execute(*args, **options)

    def handle(self, *args, **options):
        email = options["email"]
        database = options['database']
        client_data = {}

        try:
            if options['interactive']:
                # Same as user_data but with foreign keys as fake model
                # instances instead of raw IDs.
                fake_user_data = {}
                if hasattr(self.stdin, 'isatty') and not self.stdin.isatty():
                    raise NotRunningInTTYException
                if email:
                    error_msg = self._validate_email(email, database)
                    if error_msg:
                        self.stderr.write(error_msg)
                        email = None
                elif email == '':
                    raise CommandError('Email cannot be blank.')
                # Prompt for email.
                while email is None:
                    message = self._get_input_message(self.email_field, "")
                    email = self.get_input_data(self.email_field, message, "")
                    if email:
                        error_msg = self._validate_email(email, database)
                        if error_msg:
                            self.stderr.write(error_msg)
                            email = None
                            continue
                client_data["email"] = email

                # Prompt for required fields.
                for field_name in CaravaggioClient.REQUIRED_FIELDS:
                    field = CaravaggioClient._meta.get_field(field_name)
                    client_data[field_name] = options[field_name]
                    while client_data[field_name] is None:
                        message = self._get_input_message(field)
                        input_value = self.get_input_data(field, message)
                        client_data[field_name] = input_value
            else:
                # Non-interactive mode.
                if email is None:
                    raise CommandError('You must use --email with --noinput.')
                else:
                    error_msg = self._validate_email(email, database)
                    if error_msg:
                        raise CommandError(error_msg)

                client_data["email"] = email
                for field_name in CaravaggioClient.REQUIRED_FIELDS:
                    if options[field_name]:
                        field = CaravaggioClient._meta.get_field(field_name)
                        client_data[field_name] = field.clean(
                            options[field_name], None)
                    else:
                        raise CommandError(
                            'You must use --%s with --noinput.' % field_name)

            object = CaravaggioClient.objects.create(**client_data)
            if options['verbosity'] >= 1:
                self.stdout.write("Client [{}] created successfully.".
                                  format(object.id))
        except KeyboardInterrupt:
            self.stderr.write('\nOperation cancelled.')
            sys.exit(1)
        except exceptions.ValidationError as e:
            raise CommandError('; '.join(e.messages))
        except NotRunningInTTYException:
            self.stdout.write(
                'Client creation skipped due to not running in a TTY. '
                'You can run `manage.py createclient` in your project '
                'to create one manually.'
            )

    def get_input_data(self, field, message, default=None):
        """
        Override this method if you want to customize data inputs or
        validation exceptions.
        """
        raw_value = input(message)
        if default and raw_value == '':
            raw_value = default
        try:
            val = field.clean(raw_value, None)
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % '; '.join(e.messages))
            val = None

        return val

    def _get_input_message(self, field, default=None):
        return '%s%s%s: ' % (
            capfirst(field.verbose_name),
            " (leave blank to use '%s')" % default if default else '',
            ' (%s.%s)' % (
                field.remote_field.model._meta.object_name,
                field.remote_field.field_name,
            ) if field.remote_field else '',
        )

    def _validate_email(self, email, database):
        """Validate email. If invalid, return a string error message."""
        try:
            CaravaggioClient.objects.db_manager(database).\
                get(email=email)
        except CaravaggioClient.DoesNotExist:
            pass
        else:
            return 'Error: That email is already taken.'

        if not email:
            return 'Email cannot be blank.'
        try:
            self.email_field.clean(email, None)
        except exceptions.ValidationError as e:
            return '; '.join(e.messages)
