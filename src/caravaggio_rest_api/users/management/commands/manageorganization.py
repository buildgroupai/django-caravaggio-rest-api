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


class Command(BaseCommand):
    help = 'Used to manage an existent organization (members, etc.).'
    requires_migrations_checks = True
    stealth_options = ('stdin',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            required=True,
            help='Specifies the ID of the Organization to manage.',
        )
        parser.add_argument(
            '--relation',
            required=True,
            type=str,
            choices=["administrators", "members", "restricted_members"],
            help='Specifies the collection we want to manage.',
        )
        parser.add_argument(
            '--action',
            default="add",
            type=str,
            choices=["add", "remove"],
            help='If we want to add or remove users to the collection.',
        )
        parser.add_argument(
            '--users',
            required=True,
            type=str,
            nargs="+",
            help='Specifies the list of emails for users that we want to add'
                 'or remove from the collection.'
                 'Ex. bruno@buildgroupai.com joao@buildgroupai.com',
        )

    def execute(self, *args, **options):
        self.stdin = options.get('stdin', sys.stdin)  # Used for testing
        return super().execute(*args, **options)

    def handle(self, *args, **options):
        id = options["id"]
        relation = options["relation"]
        action = options['action']
        users_email = options['users']
        organization = None

        try:

            organization = CaravaggioOrganization.objects.get(id=id)

            users = []
            for user_email in users_email:
                users.append(CaravaggioUser.objects.get(
                    client=organization.client, email=user_email))

            getattr(getattr(organization, relation), action)(*users)
        except CaravaggioOrganization.DoesNotExist:
            self.stderr.write(
                '\nOrganization with ID [{}] do not exists .'.format(id))
            sys.exit(1)
        except CaravaggioUser.DoesNotExist:
            self.stderr.write(
                '\nUser do no exists in client [{}].'.format(
                    organization.client.id))
            sys.exit(1)
