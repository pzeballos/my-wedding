from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'wedding.views.slash'),
    (r'^(?P<lang>..)/index$', 'wedding.views.index'),
    (r'^(?P<lang>..)/logout$', 'wedding.views.logout_view'),
    (r'^(?P<lang>..)/(?P<template>fotos|general|esquematico|pago|agradecimientos)$', 'wedding.views.simple_page'),
    (r'^(?P<lang>..)/rsvp$', 'wedding.views.rsvp'),
    (r'^(?P<lang>..)/menu$', 'wedding.views.menu'),
    (r'^(?P<lang>..)/sitting$', 'wedding.views.sitting'),
    (r'^(?P<lang>..)_mapa$', 'wedding.views.mapa'),
#    (r'^(?P<lang>..)/alojamiento$', 'wedding.views.alojamiento'),
#    (r'^(?P<lang>..)/travel$', 'wedding.views.travel'),
    (r'^(?P<lang>..)/mensajes$', 'wedding.views.mensajes'),
    (r'^(?P<lang>..)/regalos$', 'wedding.views.regalos'),
    (r'^(?P<lang>..)/mensajes/delete/(?P<msg_id>\d+)$', 'wedding.views.delete_message'),
#    (r'^(?P<lang>..)/music$', 'wedding.views.music'),
    (r'^(?P<lang>..)/novedades$', 'wedding.views.novedades'),
#    (r'^submit/(?P<vote>up|down)/(?P<music_id>\d+)$', 'wedding.views.submit'),
#    (r'^(?P<lang>..)/(?P<vote>up|down)/(?P<music_id>\d+)$', 'wedding.views.musicVote'),
    (r'^(?P<lang>..)/guestinput/(?P<oid>\d+)$', 'wedding.views.guestInput'),
    (r'^(?P<lang>..)/codeinput/(?P<oid>\d+)$', 'wedding.views.codeInput'),
    (r'^countdown$', 'wedding.views.countdown'),

    # Restricted views
    (r'^tarjetas$', 'wedding.views_restricted.tarjetas'),
    (r'^tarjetas/(?P<pk>\d*)$', 'wedding.views_restricted.tarjeta'),
    (r'^tarjetas/imprimir$', 'wedding.views_restricted.imprimir'),
    (r'^invitados$', 'wedding.views_restricted.invitados_web'),
    (r'^invitados.csv$', 'wedding.views_restricted.invitados'),
    (r'^add_prezzie$', 'wedding.views_restricted.add_prezzie'),

)
