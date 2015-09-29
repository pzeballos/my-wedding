# -*- coding: utf-8 -*-
from wedding.models import Code

def get_language(request):
    parts = request.path.strip('/').split('/')
    if len(parts) > 0 and parts[0] in ['es', 'en']:
        return parts[0]
    elif 'yesido' in request.get_host():
        return 'en'
    else:
        return 'es'

def nTag(request):
    """ Returns a printable string containing the nicknames of all those related
        to the authenticated code """
    if not request.user.is_authenticated():
        return ''
    if len(Code.objects.filter(user=request.user)) == 0:
        return 'God'
    guests = request.user.code.guest_set.all()
    nicks = [g.nick for g in guests]
#    nicks.reverse()
    if len(nicks) == 0:
        tag = ''
    elif len(nicks) == 1:
        tag = nicks[0]
    else:
        y = {'es': ' y ', 'en': ' and '}[get_language(request)]
        tag = ', '.join(nicks[:-1]) + y + nicks[-1]
    return tag

months = {'en': ["", "January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"],
          'es': ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                 "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"],
         }

patterns = {'en': "%(month)s %(day)s", 'es': "%(day)s de %(month)s"}

def pronounce_date(date, lang):
    return patterns[lang] % {'month': months[lang][date.month],
                             'day': date.day}
    
    