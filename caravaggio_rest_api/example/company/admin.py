# -*- coding: utf-8 -*-
from datetime import datetime

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

# Register your models here.
from .models import Company

FOUNDATION_YEAR_DATES = range(2000, datetime.utcnow().year)

ROUND_YEAR_DATES = range(2000, datetime.utcnow().year)

SPECIALITIES = (('tourism','Tourism'),
                ('crypto','Cryptocurrency'),
                ('financial','Financial'),
                ('predictive_analytics','Predictive Analytics'),)


class MultipleValueWidget(forms.TextInput):
    def value_from_datadict(self, data, files, name):
        return data.getlist(name)


def clean_int(x):
    try:
        return int(x)
    except ValueError:
        raise ValidationError("Cannot convert to integer: {}".format(repr(x)))


class MultipleIntField(forms.Field):
    def clean(self, value):
        return [clean_int(x) for x in value]


class CompanyForm(forms.ModelForm):
    country_code = forms.CharField(
        label="Country Code",
        required=True,
        min_length="3",
        max_length="3",
        initial="USA")

    foundation_date = forms.DateField(
        label="Foundation Date",
        required=True,
        widget=forms.SelectDateWidget(years=FOUNDATION_YEAR_DATES),
        initial=datetime.today)

    last_round = forms.DateField(
        label="Latest Round Date",
        required=False,
        widget=forms.SelectDateWidget(years=ROUND_YEAR_DATES),
        initial=datetime.today)

    contact_email = forms.EmailField(
        label="Contact email",
        required=False,
        help_text='A valid email address, please.')

    specialties = forms.MultipleChoiceField(
        label="Business specialties",
        required=False,
        choices=SPECIALITIES, widget=forms.CheckboxSelectMultiple())

    #latest_twitter_followers = MultipleIntField(
    #    label="Tweeter Followers"
    #)

    class Meta:
        model = Company
        exclude = ['_id', 'created_at', "updated_at"]

    def get_admin_request(self):
        form_callback = getattr(self.Meta, "formfield_callback", None)
        if form_callback and getattr(form_callback, "keywords") and \
                form_callback.keywords.get("request", None):
            return form_callback.keywords.get("request", None).user
        return None

    def is_valid(self):
        import pydevd
        pydevd.settrace('localhost', port=8787, stdoutToServer=True,
                        stderrToServer=True)

        if self.instance.last_round and \
                self.instance.last_round < self.instance.foundation_date:
            raise ValidationError(
                "The round date cannot be before the foundation date.")

        current_user = self.get_admin_request()
        if self.instance and self.instance.user != None:
            if self.instance.user != current_user:
                raise ValidationError("You are not the owner of this object."
                                      " Only the owner can change details.")

        return super().is_valid()


# Register your models here.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    form = CompanyForm

    list_display = (
        "_id", "created_at", "updated_at", "name",
        "foundation_date", "country_code"
    )
    exclude = ['user', 'websites', 'founders', 'latest_twitter_followers']
    fieldsets = (
        (None, {
            'fields': ('name', 'short_description',
                       'foundation_date', 'country_code', 'contact_email',
                       'extra_data')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('stock_symbol', 'domain', 'last_round', 'round_notes',
                       'latitude', 'longitude', 'specialties',
                       'crawler_config'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.user:
            # Only set added_by during the first save.
            obj.user = str(request.user.id)
        super().save_model(request, obj, form, change)
