"""
Management utility to create superusers.
"""
import getpass
import sys

from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.utils.text import capfirst

from caravaggio_rest_api.users.models import \
    CaravaggioClient, CaravaggioUser, CaravaggioOrganization


class NotRunningInTTYException(Exception):
    pass


PASSWORD_FIELD = 'password'


class Command(BaseCommand):
    help = 'Used to create a new organization.'
    requires_migrations_checks = True
    stealth_options = ('stdin',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_field = CaravaggioOrganization._meta.get_field("email")
        self.name = CaravaggioOrganization._meta.get_field("name")
        self.owner = CaravaggioOrganization._meta.get_field("owner")

    def add_arguments(self, parser):
        parser.add_argument(
            '--client',
            required=True,
            help='Specifies the ID of our Client (external system).',
        )
        parser.add_argument(
            '--email',
            help='Specifies the email for the new client.',
        )
        parser.add_argument(
            '--name',
            help='Specifies the name of the new Organization.',
        )
        parser.add_argument(
            '--owner',
            required=True,
            help='Specifies the ID of the user that will become the'
                 ' owner of the organization.',
        )
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help=(
                'Tells Django to NOT prompt the user for input of any kind. '
                'You must use --email with --noinput, along with an option for '
                'any other required field.'
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
        client_id = options["client"]
        email = options["email"]
        database = options['database']

        org_data = {
            "client": client_id
        }

        try:
            if options['interactive']:
                # Same as org_data but with foreign keys as fake model
                # instances instead of raw IDs.
                fake_org_data = {}
                if hasattr(self.stdin, 'isatty') and not self.stdin.isatty():
                    raise NotRunningInTTYException

                if client_id is None:
                    raise CommandError('Client cannot be blank.')

                if email:
                    error_msg = self._validate_email(
                        client_id, email, database)
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
                        error_msg = self._validate_email(
                            client_id, email, database)
                        if error_msg:
                            self.stderr.write(error_msg)
                            email = None
                            continue
                org_data["email"] = email

                # Prompt for required fields.
                for field_name in CaravaggioOrganization.REQUIRED_FIELDS:
                    field = CaravaggioOrganization._meta.get_field(field_name)
                    org_data[field_name] = options[field_name]
                    while org_data[field_name] is None:
                        message = self._get_input_message(field)
                        input_value = self.get_input_data(field, message)
                        org_data[field_name] = input_value
            else:
                # Non-interactive mode.
                if client_id is None:
                    raise CommandError('Client cannot be blank.')

                if email is None:
                    raise CommandError('You must use --email with --noinput.')
                else:
                    error_msg = self._validate_email(
                        client_id, email, database)
                    if error_msg:
                        raise CommandError(error_msg)

                org_data["email"] = email
                for field_name in CaravaggioOrganization.REQUIRED_FIELDS:
                    if options[field_name]:
                        field = CaravaggioOrganization._meta.get_field(field_name)
                        org_data[field_name] = field.clean(
                            options[field_name], None)
                    else:
                        raise CommandError(
                            'You must use --%s with --noinput.' % field_name)

            org_data["client"] = \
                CaravaggioClient.objects.get(pk=org_data["client"])

            org_data["owner"] = \
                CaravaggioUser.objects.get(pk=org_data["owner"])

            object = CaravaggioOrganization.objects.create(**org_data)

            if options['verbosity'] >= 1:
                self.stdout.write("Organization [{}] - [{}] "
                                  "created successfully.".
                                  format(object.id, object.name))
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

    def _validate_email(self, client_id, email, database):
        """Validate email. If invalid, return a string error message."""
        try:
            CaravaggioOrganization.objects.db_manager(database).\
                get(client=client_id, email=email)
        except CaravaggioOrganization.DoesNotExist:
            pass
        else:
            return 'Error: That email is already taken.'

        if not email:
            return 'Email cannot be blank.'
        try:
            self.email_field.clean(email, None)
        except exceptions.ValidationError as e:
            return '; '.join(e.messages)
