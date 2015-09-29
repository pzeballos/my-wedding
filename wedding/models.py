from django.db import models
from django.contrib.auth.models import User
import random

LANG_CHOICES=(('en', 'English'),
              ('es', 'Spanish'))

class Code(models.Model):
    code = models.CharField(max_length=30, unique=True)
    user = models.OneToOneField(User)
    keep_together = models.BooleanField(default=True)
    sent_rsvp = models.BooleanField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES,
                                null=False, default='es')
    invited_to_party = models.BooleanField()
    pays = models.BooleanField()
    how_much = models.IntegerField(default=185)
    has_extras = models.BooleanField()
    dinner = models.BooleanField(default=True)

    def __unicode__(self):
        guests = self.guest_set.all()
        return "%s <<%s>>" % (self.code, u', '.join(g.nick for g in guests))

    @classmethod
    def newRandomCode(cls):
        from wedding.claves import generate_code
        code = generate_code()
        while len(cls.objects.filter(code__exact=code)) > 0:
            code = generate_code()
        user = User.objects.create_user(username=code, email=code, password=code)
        code = cls(code=code, user=user, invited_to_party=True, keep_together=True)
        user.save()
        code.save()
        return code

    def to(self, lang=None):
        guests = list(self.guest_set.all())
        if len(guests) == 0:
            return "NOBODY"
        #guests.reverse()
        name = ', '.join(x.nick for x in guests[:-1])
        y = {'en': ' and ', 'es': ' y '}
        if lang is None:
            lang = self.language
        if len(name) > 0:
            name += y.get(lang)
        name += guests[-1].nick
        return name

class Guest(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    full_name = models.CharField(max_length=64, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    nick = models.CharField(max_length=64)
    code = models.ForeignKey(Code, blank=True, help_text="Leave blank to create a new random code")
    is_coming = models.BooleanField()
    is_vegetarian = models.BooleanField()
    other_notes = models.TextField(blank=True)
    people = models.IntegerField(help_text="How many paople are coming for this guest", default=1)
    def __unicode__(self):
        return self.full_name

    def has_confirmed(self):
        return self.code.sent_rsvp

    def invited_to_party(self):
        return self.code.invited_to_party
    def partners(self):
        guests = self.code.guest_set.exclude(full_name=self.full_name)
        return ', '.join(g.full_name for g in guests)

class Affinity(models.Model):
    from_guest = models.ForeignKey(Guest, related_name='affinity_from')
    to_guest = models.ForeignKey(Guest, related_name='affinity_to')
    def __unicode__(self):
        return self.from_guest.full_name + ' -> ' + self.to_guest.full_name
    class Meta:
        verbose_name_plural = "Affinities"

class CodeAffinity(models.Model):
    from_code = models.ForeignKey(Code)
    to_guest = models.ForeignKey(Guest)
    def __unicode__(self):
        return self.from_code.to() + ' -> ' + self.to_guest.full_name
    class Meta:
        verbose_name_plural = "Code Affinities"

class Group(models.Model):
    name = models.CharField(max_length=64)
    guests = models.ManyToManyField(Guest)
    affinity = models.IntegerField()
    def __unicode__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=15)
    code = models.CharField(max_length=2)
    def __unicode__(self):
        return self.name

class IPLog(models.Model):
    ip = models.IPAddressField()
    attempts = models.IntegerField(default=0)
    def __unicode__(self):
        return self.ip

class AccessLog(models.Model):
    code = models.ForeignKey(Code)
    stamp = models.DateTimeField(auto_now_add=True)
    page = models.CharField(max_length=256)
    def __unicode__(self):
        return "%s: (%s) %s" % (self.stamp, self.code.to(lang='es'), self.page)

class Message(models.Model):
    msg = models.TextField()
    rte = models.ForeignKey(Code)
    public = models.BooleanField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES,
                                null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return self.snippet()
    def snippet(self):
        result = self.msg[:100]
        if len(self.msg) > 100:
            result += "..."
        return result

class Music(models.Model):
    name = models.CharField(max_length=256, unique=True)
    url = models.CharField(max_length=2048)
    ranking = models.IntegerField(default=0)
    def __unicode__(self):
        return self.name

class Vote(models.Model):
    code = models.ForeignKey(Code)
    music = models.ForeignKey(Music)
    vote = models.IntegerField(default=0)
    def __unicode__(self):
        if self.vote > 0:
            vote = "+1"
        elif self.vote < 0:
            vote = "-1"
        else:
            raise ValueError("Invalid 0 vote (pk %d)" % self.pk)
        return "Vote: %s for '%s' from %s" % (vote, self.music.name, self.code.to('en'))

class Prezzie(models.Model):
    garbid = models.CharField(unique=True, max_length=100)
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    fotitourl = models.CharField(max_length=150)
    def __unicode__(self):
        return self.title

class Novedad(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    language = models.CharField(max_length=2, choices=LANG_CHOICES,
                                null=True, blank=True)
    def __unicode__(self):
        return self.title

    def snippet(self):
        result = self.text[:100]
        if len(self.text) > 100:
            result += "..."
        return result

    class Meta:
        verbose_name_plural = "Novedades"
