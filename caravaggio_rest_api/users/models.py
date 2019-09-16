# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import uuid

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.dispatch import receiver

from django.db import models
from django.db.models import PROTECT
from django.db.models.signals import pre_save, post_save, \
    pre_delete, post_delete

from django.contrib.auth.models import AbstractUser, BaseUserManager

from django.utils.translation import gettext_lazy as _


class CaravaggioUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, client, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not client:
            raise ValueError('The given client must be set')
        if not email:
            raise ValueError('The given email must be set')

        del extra_fields["username"]

        if isinstance(client, (str, uuid.UUID)):
            client = CaravaggioClient.objects.get(id=client)

        email = self.normalize_email(email)
        user = self.model(client=client, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, client, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(client, email, password, **extra_fields)

    def create_superuser(self, client, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(client, email, password, **extra_fields)


class CaravaggioClient(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(
        _('email address'), unique=True, null=False, blank=False)

    name = models.CharField(
        _('client name'), max_length=100, null=False, blank=False)

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this client should be treated as active. '
            'Unselect this instead of deleting clients.'
        ),
    )

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    date_deactivated = models.DateTimeField(
        _('date deactivated'), null=True, blank=True)

    REQUIRED_FIELDS = ['name']

    def __str__(self):  # __unicode__ on Python 2
        return "{} ({} - {})".format(self.name, self.id, self.email)

    class Meta:
        db_table = 'caravaggio_client'
        ordering = ['-date_joined']


class CaravaggioUser(AbstractUser):
    """
    A class implementing a fully featured User model with
    admin-compliant permissions.

    client-id, email and password are required. Other fields are optional.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    client = models.ForeignKey(to=CaravaggioClient, on_delete=PROTECT)

    # organization = models.ForeignKey(
    #    CaravaggioClient,
    #    on_delete=PROTECT,
    #    related_name="_users",
    #    blank=True,
    #    null=True)

    email = models.EmailField(_('email address'), blank=False)

    is_client_staff = models.BooleanField(
        _('client staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can operate with client users.'),
    )

    date_deactivated = models.DateTimeField(
        _('date deactivated'), null=True, blank=True)

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = [
        'client', 'email', "first_name", "last_name", "is_client_staff"]

    objects = CaravaggioUserManager()

    class Meta:
        db_table = 'caravaggio_user'
        unique_together = ('client', 'email',)
        ordering = ['-date_joined']
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):  # __unicode__ on Python 2
        return "{}-{}".format(self.client.id, self.email)


class CaravaggioOrganization(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    client = models.ForeignKey(CaravaggioClient, on_delete=PROTECT)

    email = models.EmailField(_('email address'), blank=False)

    name = models.CharField(
        _('client name'), max_length=100, null=False, blank=False)

    owner = models.ForeignKey(
        CaravaggioUser,
        related_name="owner_of",
        on_delete=PROTECT,
        blank=False,
        null=False)

    administrators = models.ManyToManyField(
        CaravaggioUser, related_name="administrator_of", blank=True)
    members = models.ManyToManyField(
        CaravaggioUser, related_name="member_of", blank=True)
    restricted_members = models.ManyToManyField(
        CaravaggioUser, related_name="restricted_member_of", blank=True)

    # maintain a reference to all the members of the organization
    # useful for queries (QuerySet restricting
    # by the users in the organization)
    all_members = models.ManyToManyField(
        CaravaggioUser, related_name="organizations", blank=True)

    number_of_total_members = models.PositiveIntegerField(default=1)
    number_of_administrators = models.PositiveIntegerField(default=0)
    number_of_members = models.PositiveIntegerField(default=0)
    number_of_restricted_members = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this organization should be treated as active. '
            'Unselect this instead of deleting organizations.'
        ),
    )

    created = models.DateTimeField(_('created'), default=timezone.now)
    updated = models.DateTimeField(_('updated'), default=timezone.now)

    date_deactivated = models.DateTimeField(
        _('date deactivated'), null=True, blank=True)

    REQUIRED_FIELDS = ['email', 'name', 'owner']

    class Meta:
        db_table = 'caravaggio_organization'
        unique_together = ('client', 'email',)
        ordering = ['-created']

    def __str__(self):  # __unicode__ on Python 2
        return "{} ({} - {})".format(self.name, self.id, self.email)


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=CaravaggioClient)
def pre_save_client(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    if instance.is_active and instance.date_deactivated:
        instance.date_deactivated = None

    if not instance.is_active and not instance.date_deactivated:
        instance.date_deactivated = timezone.now()


# We need to check if the Organization has still members or the owner is not
# member of other organization
@receiver(pre_delete, sender=CaravaggioOrganization)
def pre_delete_organization(
        sender, instance=None, using=None, **kwargs):

    if instance.all_members.count() > 1:
        raise ValidationError("The organization still has members")
    elif instance.organizations.count() == 1:
        raise ValidationError("The owner of the organization doesn't "
                              "below to other organization, move it first.")


# We need to check if the Organization has still members or the owner is not
# member of other organization
@receiver(pre_delete, sender=CaravaggioUser)
def pre_delete_user(
        sender, instance=None, using=None, **kwargs):

    for organization in instance.organizations.all():
        compute_member_counters(organization)


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=CaravaggioOrganization)
def pre_save_organization(
        sender, instance=None, using=None, update_fields=None, **kwargs):

    created = False
    if not instance.id:
        created = True
        instance.id = uuid.uuid4()
    else:
        instance.updated = timezone.now()

    if instance.is_active and instance.date_deactivated:
        instance.date_deactivated = None

    if not instance.is_active and not instance.date_deactivated:
        instance.date_deactivated = timezone.now()

    if not created:
        compute_member_counters(instance)


# We need to set the new value for the changed_at field
@receiver(post_save, sender=CaravaggioOrganization)
def post_save_organization(
        sender, instance=None, created=None, using=None,
        update_fields=None, **kwargs):
    if created:
        instance.all_members.add(instance.owner)


def compute_member_counters(instance):
    # Total number of members includes the organization owner
    instance.number_of_total_members = instance.all_members.count()
    instance.number_of_members = instance.members.count()
    instance.number_of_administrators = instance.administrators.count()
    instance.number_of_restricted_members = \
        instance.restricted_members.count()


def m2m_org_administrators_changed(signal, sender, **kwargs):
    """
        When we add/remove someone from the member list
    """
    organization = kwargs['instance']
    action = kwargs['action']

    if kwargs['pk_set']:
        users = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        if action == 'post_add':
            # do something when user was added
            for user in users:
                if organization.owner == user:
                    organization.administrators.remove(user)
            organization.members.remove(*users)
            organization.restricted_members.remove(*users)
            organization.all_members.add(*users)
            compute_member_counters(organization)
        elif action in ('post_remove', 'post_clear'):
            organization.all_members.remove(*users)
            compute_member_counters(organization)
        else:
            pass


def m2m_org_members_changed(signal, sender, **kwargs):
    """
        When we add/remove someone from the member list
    """
    organization = kwargs['instance']
    action = kwargs['action']

    if kwargs['pk_set']:
        users = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        if action == 'post_add':
            # do something when user was added
            for user in users:
                if user == organization.owner and \
                        user not in organization.administrators.all():
                    organization.members.remove(user)
            organization.restricted_members.remove(*users)
            organization.all_members.add(*users)
            compute_member_counters(organization)
        elif action in ('post_remove', 'post_clear'):
            organization.all_members.remove(*users)
            compute_member_counters(organization)
        else:
            pass


def m2m_org_restricted_members_changed(signal, sender, **kwargs):
    """
        When we add/remove someone from the member list
    """
    organization = kwargs['instance']
    action = kwargs['action']

    if kwargs['pk_set']:
        users = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        if action == 'post_add':
            # do something when user was added
            for user in users:
                if user == organization.owner and \
                        user not in organization.members.all() and \
                        user not in organization.administrators.all():
                    organization.restricted_members.remove(user)
            organization.all_members.add(*users)
            compute_member_counters(organization)
        elif action in ('post_remove', 'post_clear'):
            organization.all_members.remove(*users)
            compute_member_counters(organization)
        else:
            pass


# We control changes in the relations of the Organization to make sure
# that only keep the highest permission
models.signals.m2m_changed.connect(
    m2m_org_administrators_changed,
    CaravaggioOrganization.administrators.through)
models.signals.m2m_changed.connect(
    m2m_org_members_changed,
    CaravaggioOrganization.members.through)
models.signals.m2m_changed.connect(
    m2m_org_restricted_members_changed,
    CaravaggioOrganization.restricted_members.through)


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=CaravaggioUser)
def pre_save_user(
        sender, instance=None, using=None, update_fields=None, **kwargs):

    instance.username = "{}-{}".format(instance.client.id, instance.email)

    if instance.is_active and instance.date_deactivated:
        instance.date_deactivated = None

    if not instance.is_active and not instance.date_deactivated:
        instance.date_deactivated = timezone.now()
