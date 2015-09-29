from wedding.models import (Language, Code, Guest, Group, IPLog,
                                   AccessLog, Message, Music, Vote,
                                   CodeAffinity, Affinity, Prezzie, Novedad)
from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import F

try:
    from tinymce.widgets import TinyMCE
except ImportError:
    TinyMCE = None

class NovedadAdminForm(forms.ModelForm):
    if TinyMCE is not None:
        text = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 20},
                   mce_attrs={'theme': "advanced", 'relative_urls': False}))
    class Meta:
        model = Novedad

class NovedadAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'snippet')
    form = NovedadAdminForm

class GuestAdminForm(forms.ModelForm):
    class Meta:
        model = Guest

    def clean_code(self):
        code = self.cleaned_data['code']
        if code is None:
            code = Code.newRandomCode()
        return code

class CodeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,   {'fields': ['code', 'language', 'invited_to_party', 'dinner',  'pays', 'how_much', 'has_extras']}),
        ('User', {'fields': ['user'], 'classes': ['collapse']}),
        ('Feedback', {'fields': ['sent_rsvp', 'keep_together'], 'classes': ['collapse']}),
    ]
    search_fields = ['code', 'guest__full_name', 'guest__nick']
    list_display = ('code', 'to', 'invited_to_party', 'dinner', 'sent_rsvp', 'keep_together', 'language', 'pays', 'how_much', 'has_extras')
    list_filter = ['invited_to_party', 'sent_rsvp', 'language', 'pays', 'has_extras', 'dinner', 'how_much']

    def toggle_invite(self, request, queryset):
        # hack due to the following not working (not F() doesn't work)
        # queryset.update(invited_to_party = not F('invited_to_party'))
        for code in queryset:
            code.invited_to_party = not code.invited_to_party
            code.save()

    def toggle_dinner(self, request, queryset):
        # hack due to the following not working (not F() doesn't work)
        # queryset.update(dinner = not F('dinner'))
        for code in queryset:
            code.dinner = not code.dinner
            code.save()

    def toggle_pays(self, request, queryset):
        # hack due to the following not working (not F() doesn't work)
        # queryset.update(pays = not(F('pays')))
        for code in queryset:
            code.pays = not code.pays
            code.save()

    def how_much_setter(amount = 185):
        def ret(self, request, queryset):
            queryset.update(how_much = amount)
        ret.short_description = ' '.join(('Set paying amount to', str(amount)))
        return ret

    how_much_100 = how_much_setter(100)
    how_much_120 = how_much_setter(120)
    how_much_220 = how_much_setter(220)

    actions = ['toggle_dinner', 'toggle_pays', 'toggle_invite', 'how_much_100', 'how_much_120', 'how_much_220']

class GuestAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,   {'fields': ['full_name', 'nick', 'gender', 'code', 'people']}),
        ('RSVP', {'fields': ['is_coming'], 'classes': ['collapse']}),
        ('Menu', {'fields': ['is_vegetarian', 'other_notes'], 'classes': ['collapse']}),
    ]
    list_display = ('full_name', 'is_coming', 'has_confirmed', 'invited_to_party', 'code')
    form = GuestAdminForm
    list_filter = ['is_coming', 'is_vegetarian', 'gender']
    search_fields = ['full_name', 'nick']

    def toggle_is_coming(self, request, queryset):
        # hack due to the following not working (not F() doesn't work)
        # queryset.update(dinner = not F('dinner'))
        for guest in queryset:
            guest.is_coming = not guest.is_coming
            guest.code.sent_rsvp = True
            guest.code.save()
            guest.save()

    actions = ['toggle_is_coming']

class MessageAdmin(admin.ModelAdmin):
    list_display = ('rte', 'public', 'timestamp', 'snippet')
    list_filter = ['public', 'timestamp']

class IPLogAdmin(admin.ModelAdmin):
    list_display = ('ip', 'attempts')

class GroupAdminForm(forms.ModelForm):
    guests = forms.ModelMultipleChoiceField(
                widget = FilteredSelectMultiple('Guests',False),
                queryset = Guest.objects.filter(is_coming=True))
    class Meta:
        model = Group


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm

admin.site.register(Language)
admin.site.register(Code, CodeAdmin)
admin.site.register(Guest, GuestAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(IPLog, IPLogAdmin)
admin.site.register(AccessLog)
admin.site.register(Message, MessageAdmin)
admin.site.register(Music)
admin.site.register(Vote)
admin.site.register(CodeAffinity)
admin.site.register(Affinity)
admin.site.register(Prezzie)
admin.site.register(Novedad, NovedadAdmin)
