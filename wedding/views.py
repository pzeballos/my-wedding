# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404, Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from util import get_language, nTag, pronounce_date
from django.template import loader, RequestContext
from wedding.models import (Code, Guest, Affinity, CodeAffinity, IPLog,
                            AccessLog, Message, Music, Vote, Prezzie, Novedad)
import datetime

def slash(request):
    url = request.get_full_path()
    return HttpResponseRedirect(url.strip('/') + '/' + get_language(request) + '/index')

def index(request, lang):
    blocked = False
    required = False
    mismatch = False
    dinner = False
    unauthorized = 'next' in request.GET
    next = request.GET.get('next', '')
    template = 'login.html'
    sent_rsvp = True
    invited_to_party = False
    pays = False
    how_much = 0
    has_extras = False
    atts = {}
    if request.user.is_authenticated() and not request.user.is_superuser:
        template = 'welcome.html'
        sent_rsvp = request.user.code.sent_rsvp
        code = request.user.code
        invited_to_party = code.invited_to_party
        pays = code.pays
        how_much = code.how_much
        has_extras = code.has_extras
        dinner = code.dinner
        log = AccessLog(code=code, page=request.path)
        log.save()
    elif request.method == 'POST':
        iplogs = IPLog.objects.filter(ip=request.META['REMOTE_ADDR'])
        if 'code' in request.POST and len(request.POST['code']):
            codes = Code.objects.filter(code__iexact=request.POST['code'])
            if len(codes) > 0:
                user = codes[0].user
                user = authenticate(username=user.username, password=codes[0].code)
                if user is None:
                    mismatch = True
                else:
                    login(request, user)
                    template = 'welcome.html'
                    code = request.user.code
                    log = AccessLog(code=code, page=request.path)
                    log.save()
                    sent_rsvp = code.sent_rsvp
                    pays = code.pays
                    how_much = code.how_much
                    has_extras = code.has_extras
                    invited_to_party = code.invited_to_party
                    dinner = code.dinner
                    if len(iplogs) > 0:
                        iplogs[0].delete()
                    if 'goto' in request.POST:
                        return HttpResponseRedirect(request.POST['goto'])
            else:
                if len(iplogs) > 0:
                    iplog = iplogs[0]
                else:
                    iplog = IPLog(ip=request.META['REMOTE_ADDR'])
                iplog.attempts = iplog.attempts + 1
                iplog.save()
                mismatch = True
        else:
            required = True
    atts.update({
        'lang': lang,
        'spanish': lang=='es',
        'mismatch': mismatch,
        'required': required,
        'unauthorized': unauthorized,
        'blocked': blocked,
        'next': next,
        'nametag': nTag(request),
        'sent_rsvp': sent_rsvp,
        'invited_to_party': invited_to_party,
        'pays': pays,
        'how_much': how_much,
        'has_extras': has_extras,
        'dinner': dinner
    })
    context = RequestContext(request,atts)
    return render_to_response(template, context)

def logout_view (request, lang):
    logout(request)
    context = RequestContext(request, {'lang': lang,
            'spanish': lang=='es',
            'nametag': nTag(request),
            'sent_rsvp': True,
    })
    return render_to_response('logout.html', context)

def simple_page (request, template, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    atts = {'lang': lang, 'spanish': lang=='es',
             'nametag': nTag(request),
             'sent_rsvp': code.sent_rsvp, 'pays': code.pays, 'how_much': code.how_much, 'has_extras': code.has_extras, 'dinner': code.dinner,
             'invited_to_party': code.invited_to_party,
             'bgimg': template + '_bgimg',
             }
    context = RequestContext(request, atts)
    return render_to_response(template+'.html', context)

def rsvp(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    guests = code.guest_set.all()
    saved = False # True when the rsvp is sent for the first time
    edited = False # True when the rsvp is re-sent
    if request.method == 'POST':
        if 'confirm' in request.POST:
            if request.POST['confirm'] == 'yes':
                for g in guests:
                    g.is_coming = True
            elif request.POST['confirm'] == 'complicated':
                for g in guests:
                    g.is_coming = 'confirm_' + str(g.id) in request.POST
            elif request.POST['confirm'] == 'no':
                for g in guests:
                    g.is_coming = False
            for g in guests:
                g.save()
            if code.sent_rsvp:
                edited = True
            else:
                saved = True
            code.sent_rsvp = True
            code.save()
    all_confirmed = code.sent_rsvp and all(g.is_coming for g in guests)
    none_confirmed = code.sent_rsvp and all(not g.is_coming for g in guests)
    some_confirmed = code.sent_rsvp and not (all_confirmed or none_confirmed)
    atts = {
        'lang': lang, 'spanish': lang=='es',
        'guests': guests, 'multiple': sum([x.people for x in guests]) > 1,
        'amount': sum([x.people for x in guests]), 'all': all_confirmed, 'none': none_confirmed,
        'some': some_confirmed, 'saved': saved, 'edited': edited,
        'nametag': nTag(request), 'pays': code.pays, 'dinner': code.dinner,
        'sent_rsvp': request.user.code.sent_rsvp,
        'invited_to_party': request.user.code.invited_to_party,
    }
    context = RequestContext(request, atts)

    return render_to_response('rsvp.html', context)

def menu(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    guests = code.guest_set.filter(is_coming=True)
    saved = False
    if request.method == 'POST':
        for g in guests:
            g.is_vegetarian = request.POST.get('is_vegetarian_'+str(g.id), False)
            g.other_notes = request.POST.get('other_notes_'+str(g.id), '')
            g.save()
            saved = True

    missing =  code.sent_rsvp and len(code.guest_set.filter(is_coming=False)) > 0
    atts = {
        'lang': lang, 'spanish': lang=='es',
        'guests': guests, 'multiple': len(guests) > 1, 'pays': code.pays,
        'sent_rsvp': code.sent_rsvp, 'saved': saved,
        'invited_to_party': code.invited_to_party, 'dinner': code.dinner,
        'some_missing': missing, 'nametag': nTag(request),
        'bgimg': 'menu_bgimg',
    }
    context = RequestContext(request, atts)

    return render_to_response('menu.html', context)

def sitting(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    guests = code.guest_set.filter(is_coming=True)
    saved = False
    if request.method == 'POST':
        code.keep_together = request.POST.get('keep_together') == 'yes'
        code.save()
        Affinity.objects.filter(from_guest__in=guests).delete()
        CodeAffinity.objects.filter(from_code=code).delete()
        if code.keep_together:
            raw = request.POST.get('code_affinity').split(',')
            newIds = [int(a) for a in raw if a.isdigit()]
            for id in newIds:
                try:
                    guest = Guest.objects.get(pk=id)
                    affinity = CodeAffinity(from_code=code, to_guest=guest)
                    affinity.save()
                except:
                    pass # Bad id
        else: # Covers individual invitations *and* groups that don't want to sit together
            for g in guests:
                raw = request.POST.get('affinity' + str(g.id)).split(',')
                newIds = [int(a) for a in raw if a.isdigit()]
                for id in newIds:
                    try:
                        guest = Guest.objects.get(pk=id)
                        affinity = Affinity(from_guest=g, to_guest=guest)
                        affinity.save()
                    except:
                        pass # Bad id
        saved = True
    missing =  code.sent_rsvp and len(code.guest_set.filter(is_coming=False)) > 0

    code_selected = '[]'
    if code.keep_together:
        selected = CodeAffinity.objects.filter(from_code=code)
        code_selected = ['{"id": "%s", "name": "%s"}' %
                        (s.to_guest.id, s.to_guest.full_name) for s in selected]
        code_selected = '[%s]' % ','.join(code_selected)
    for g in guests:
        selected = Affinity.objects.filter(from_guest=g)
        items = ['{"id": "%s", "name": "%s"}' %
                (s.to_guest.id, s.to_guest.full_name) for s in selected]
        g.selected = '[%s]' % ','.join(items)

    atts = {'lang': lang, 'spanish': lang=='es',
        'guests': guests, 'multiple': len(guests) > 1,
        'sent_rsvp': code.sent_rsvp, 'saved': saved,
        'invited_to_party': code.invited_to_party,
        'some_missing': missing, 'code_selected': code_selected,
        'keep_together': code.keep_together, 'nametag': nTag(request),
        'code_id': code.id, 'pays': code.pays, 'dinner': code.dinner,
        }
    context = RequestContext(request, atts)

    return render_to_response('sitting.html', context)

def guestInput(request, lang, oid):
    if not request.user.is_authenticated():
        raise Http404()
    query = request.GET.get('q', '')
    guest = get_object_or_404(Guest, pk=oid)
    return tokenInput(omit=[guest], query=query, lang=lang)

def codeInput(request, lang, oid):
    if not request.user.is_authenticated():
        raise Http404()
    query = request.GET.get('q', '')
    guests = Guest.objects.filter(code__id__exact=oid)
    return tokenInput(omit=guests, query=query, lang=lang)

def tokenInput(omit, query, lang):
    party = Guest.objects.filter(code__invited_to_party=True)
    party = party.exclude(code__sent_rsvp=True, is_coming=False)

    rows = []
    for g in party:
        if query in g.full_name.lower() and not g in omit:
            rows.append(g)
            if len(rows) > 15:
                break
    def rcomp(a, b):
        return cmp(a.full_name, b.full_name)
    rows.sort(rcomp)
    opts = ['{"id": "%s", "name": "%s"}' % (r.id, r.full_name) for r in rows]
    return HttpResponse('[%s]' % (',\n'.join(opts)))



# http://valeyachuni.com.ar:8000/es/ ABQIAAAAu0eX6JSNjMxM97aApIVuzBQXCcfvyCwCNY-JCJ_9UX0BE22U5xTxbe5ilq9iH0-Ka_8t1JLE2Z-2jA
# http://valeyachuni.com.ar:8000/    ABQIAAAAu0eX6JSNjMxM97aApIVuzBSunVKGhDEDRz8GYtNGIU5kObjqChTm6Y7K46I5VceuxO8gHjXs6o17cw
# http://yesido.com.ar/              ABQIAAAAu0eX6JSNjMxM97aApIVuzBRYYJGMO8kP34zJ4tRc3N3uDI2uxBQ1XCWcwC-WhG0PF6u45uqXD7hvuA
# http://valeyachuni.com.ar/         ABQIAAAAu0eX6JSNjMxM97aApIVuzBTLytsNl1nbkc13cw-gDRvVGbzopRRP1CAOVbBaIosqVEmIbZAaCBWzOg
# http://achuni.com.ar/              ABQIAAAAu0eX6JSNjMxM97aApIVuzBS7VRcjPEkhSAkpZ1oGTCC1TpdkihSoskMexgOIjuCfhszsU-QpDc_UCQ

def mapa(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    if 'valeyachuni' in request.get_host():
        apikey = 'ABQIAAAAu0eX6JSNjMxM97aApIVuzBTLytsNl1nbkc13cw-gDRvVGbzopRRP1CAOVbBaIosqVEmIbZAaCBWzOg'
    elif 'yesido' in request.get_host():
        apikey = 'ABQIAAAAu0eX6JSNjMxM97aApIVuzBRYYJGMO8kP34zJ4tRc3N3uDI2uxBQ1XCWcwC-WhG0PF6u45uqXD7hvuA'
    elif 'achuni' in request.get_host():
        apikey = 'ABQIAAAAu0eX6JSNjMxM97aApIVuzBS7VRcjPEkhSAkpZ1oGTCC1TpdkihSoskMexgOIjuCfhszsU-QpDc_UCQ'
    else:
        apikey = 'UnknownHost-' + request.get_host()
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    context = RequestContext(request, {'lang': lang, 'spanish': lang=='es',
                             'nametag': nTag(request), 'apikey':apikey,
                             'sent_rsvp': code.sent_rsvp, 'pays': code.pays,
                             'invited_to_party': code.invited_to_party,
                             'dinner': code.dinner,
                            # 'bgimg': 'mapa_bgimg',
                             })
    return render_to_response('mapa.html', context)


def mensajes(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    submitted = False
    if request.method == 'POST':
        if request.POST.get('body'):
            msg = Message(msg=request.POST.get('body'),
                          public=request.POST.get('public', False),
                          rte=code, language=lang)
            msg.save()
            submitted = True

    otherlang = (lang == 'es') and 'en' or 'es'
    msgs = Message.objects.filter(public=True).exclude(language__exact=otherlang).order_by('-timestamp')
    startdate = datetime.datetime(2010, 7, 25)
    for msg in msgs:
        msg.localTo = msg.rte.to(lang)
        msg.own = msg.rte == code
        if msg.timestamp > startdate:
            msg.timestampstr = pronounce_date(msg.timestamp, lang)

    atts = {'lang': lang, 'spanish': lang=='es',
            'nametag': nTag(request),
            'sent_rsvp': request.user.code.sent_rsvp,
            'invited_to_party': request.user.code.invited_to_party,
            'code': code.code, 'pays': code.pays, 'dinner': code.dinner,
            'submitted': submitted,
            'msgs': msgs,
           }
    context = RequestContext(request, atts)
    return render_to_response('mensajes.html', context)

def delete_message(request, lang, msg_id):
    if not request.user.is_authenticated() or request.user.is_superuser:
        raise Http404()
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    msg = get_object_or_404(Message, pk=msg_id)
    if msg.rte != code:
        raise Http404()
    msg.delete()
    return HttpResponseRedirect('/%s/mensajes' % lang)

def music(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()

    submitted = False
    error = ''
    if request.method == 'POST':
        if request.POST.get('name'):
            try:
                music = Music(name=request.POST['name'],
                              url=request.POST['url'],
                              ranking=1)
                music.save()
                vote = Vote(code=code, music=music, vote=1)
                vote.save()
            except:
                errs = {'es': 'Ya hay un tema llamado "%s"',
                        'en': 'Somebody has already suggested "%s"'}
                error =  errs[lang] % music.name
            submitted = True
        elif request.POST.get('url'):
            errs = {'es': "El campo 'Tema' es obligatorio",
                    'en': "The 'Song' field is required."}
            error =  errs[lang]


    music = Music.objects.order_by('ranking').reverse()
    myvotes = Vote.objects.filter(code__exact=code)
    ms = {}
    for m in music:
        m.upped = False
        m.downed = False
        ms[m.pk] = m
    for v in myvotes:
        if v.vote > 0:
            ms[v.music.pk].upped = True
        elif v.vote < 0:
            ms[v.music.pk].downed = True
        else:
            raise ValueError("Found null vote (pk %d)" % v.pk)
    atts = {'lang': lang, 'spanish': lang=='es',
            'nametag': nTag(request),
            'sent_rsvp': request.user.code.sent_rsvp,
            'invited_to_party': request.user.code.invited_to_party,
            'error': error,
            'code': code.code, 'pays': code.pays,
            'music': music,
           }
    context = RequestContext(request, atts)

    return render_to_response('music.html', context)

def _vote(code, music_id, vote):
    music = get_object_or_404(Music, pk=music_id)
    votes = Vote.objects.filter(code__exact=code, music__exact=music)
    if len(votes) == 0:
        votes = {'up': 1, 'down': -1}
        result = votes[vote]
        vote = Vote(code=code, music=music, vote=result)
        vote.save()
        music.ranking += vote.vote
        music.save()
    else:
        for v in votes:
            music.ranking -= v.vote
            v.delete()
        result = 0
        music.save()
    return result, music.ranking

def musicVote(request, lang, vote, music_id):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
#    log = AccessLog(code=code, page=request.path)
#    log.save()
    _vote(code, music_id, vote)
    return HttpResponseRedirect('/' + lang + '/music')

def submit(request, vote, music_id):
    if not request.user.is_authenticated() or request.user.is_superuser:
        raise Http404()
    code = request.user.code
#    log = AccessLog(code=code, page=request.path)
#    log.save()
    result = _vote(code, music_id, vote)
    return HttpResponse ('{"s": %s, "ranking": %s}' % result)

def regalos(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    prezzies = Prezzie.objects.order_by('price').all()
    atts = {'lang': lang, 'spanish': lang=='es',
            'nametag': nTag(request),
            'sent_rsvp': request.user.code.sent_rsvp,
            'invited_to_party': request.user.code.invited_to_party,
            'code': code.code, 'pays': code.pays,
            'prezzies': prezzies,
           }
    context = RequestContext(request, atts)

    return render_to_response('regalos.html', context)

def novedades(request, lang):
    if not request.user.is_authenticated() or request.user.is_superuser:
        return HttpResponseRedirect('/%s/index?next=%s' % (lang,request.path))
    code = request.user.code
    log = AccessLog(code=code, page=request.path)
    log.save()
    news = Novedad.objects.order_by('-date').filter(language=lang)
    for n in news:
        n.datestr = pronounce_date(n.date, lang)
    atts = {'lang': lang, 'spanish': lang=='es',
            'nametag': nTag(request),
            'sent_rsvp': request.user.code.sent_rsvp,
            'invited_to_party': request.user.code.invited_to_party,
            'code': code.code, 'pays': code.pays, 'dinner': code.dinner,
            'news': news,
           }
    context = RequestContext(request, atts)
    return render_to_response('news.html', context)

def countdown(request):
    theDate = datetime.datetime(2010, 9, 25, 22)
    delta = theDate - theDate.now()
    atts = {'days': delta.days,
            'hours': '%02d' % (delta.seconds / 60 / 60,),
            'mins': '%02d' % ((delta.seconds / 60) % 60,),
            'secs': '%02d' % (delta.seconds % 60,),
            'original': '2010, 8, 25, 22',
           }
    return render_to_response('countdown.html', atts)
