# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from models import Code, Guest, Prezzie
import re
import tempfile
import os
import codecs
from StringIO import StringIO
import csv
from urllib import urlopen

@staff_member_required
def tarjetas(request):
    invites = Code.objects.all()
    return render_to_response('invites.html', {'invites': invites})

@staff_member_required
def invitados_web(request):
    guests = Guest.objects.all()
    nparticipados = sum(g.people for g in Guest.objects.filter(code__invited_to_party=False))
    nnovienen = sum(g.people for g in Guest.objects.filter(code__sent_rsvp=True, is_coming=False))
    nvienen = Guest.objects.filter(code__sent_rsvp=True, is_coming=True).count()
    nnoconfirmados = sum(g.people for g in Guest.objects.filter(code__invited_to_party=True, code__sent_rsvp=False))
    total = nparticipados + nnovienen + nvienen + nnoconfirmados
    participados = nparticipados * 100 / total
    noconfirmados = nnoconfirmados * 100 / total
    novienen = nnovienen * 100 / total
    vienen = nvienen * 100 / total
    atts = {'guests': guests,
            'participados': participados,
            'novienen': novienen,
            'vienen': vienen,
            'noconfirmados': noconfirmados,
            'nparticipados': nparticipados,
            'nnovienen': nnovienen,
            'nvienen': nvienen,
            'nnoconfirmados': nnoconfirmados,
           }
    return render_to_response('invitados.html', atts)

def _generate_invite (invite, out_filename):
    source, origin = loader.find_template_source('tarjeta_%s.svg' % invite.language)
    source = re.sub(r"%([^(])", r"%%\1", source)
    if not invite.invited_to_party:
        if invite.language == 'es':
            source = source.replace ("%(pueden)s avisarnos si %(vienen)s, y", "%(pueden)s conocer varios otros")
            source = source.replace (u"ayudarnos con varios aspectos de la", u"aspectos de nuestro casamiento")
            source = source.replace (u"organización.", u" ")
        else:
            source = source.replace ("You can let us know if you're coming,", "you can find out other details")
            source = source.replace ("and help us with several bits of", "about our wedding")
            source = source.replace ("the organization.", " ")
    in_filename = tempfile.mktemp() + '.svg'
    f = codecs.open(in_filename, 'w', encoding='utf-8')
    f.write(card)
    f.close()
    os.system ('inkscape --export-dpi=600 --export-pdf=%s %s' % (out_filename, in_filename))
    os.unlink(in_filename)

@staff_member_required
def imprimir(request):
    """ Print multiple invitations at once """
    if request.method == 'POST':
        pks = [int(x) for x in request.POST.getlist('code')]
        intermediate = tempfile.mktemp()
        for pk in pks:
            invite = Code.objects.get(pk=pk)
            _generate_invite(invite, intermediate + str(pk))
        filenames = " ".join(intermediate + str(pk) for pk in pks)
        out_filename = tempfile.mktemp()
        cmd = 'pdftk %s cat output %s' % (filenames, out_filename)
        os.system(cmd)
        for pk in pks:
            os.unlink(intermediate + str(pk))
        g = open(out_filename)
        img = g.read()
        response = HttpResponse(img, mimetype="application-pdf")
        g.close()
        os.unlink(out_filename)
        return response
    else:
        return HttpResponseRedirect('/tarjetas')

@staff_member_required
def tarjeta(request, pk):
    """ Print an invitation """
    invite = Code.objects.get(pk=pk)
    out_filename = tempfile.mktemp()
    _generate_invite(invite, out_filename)
    g = open(out_filename)
    img = g.read()
    response = HttpResponse(img, mimetype="application-pdf")
    g.close()
    os.unlink(out_filename)
    return response

@staff_member_required
def invitados(request):
    def is_coming(g):
        if g.code.invited_to_party:
            if g.code.sent_rsvp:
                if g.is_coming:
                    return "Si"
                else:
                    return "No"
            else:
                return "No se"
        else:
            return "---"
    codes = Code.objects.all()
    m = StringIO()
    csv_writer = csv.writer(m)
    csv_writer.writerow(["Codigo", "Tarjeta", "Invitado", "Paga", "Cuánto", "Nombre completo", "Viene", "Cantidad"])
    for code in codes:
        guests = list(code.guest_set.all())
        if len(guests) == 0:
            continue
        g0 = guests[0]
        fullname = g0.full_name.encode('utf-8')
        nametag = code.to().encode('utf-8')
        csv_writer.writerow([code.code, nametag, code.invited_to_party, code.pays, code.how_much, fullname, is_coming(g0), g0.people])
        for guest in guests[1:]:
            fullname = guest.full_name.encode('utf-8')
            csv_writer.writerow([code.code, "", "", "", "", fullname, is_coming(guest), guest.people])
    return HttpResponse(m.getvalue(), mimetype="text-csv")

@staff_member_required
def add_prezzie(request):
    prezzie_id = request.GET.get('prezzie_id')
    if prezzie_id is None:
        return render_to_response('add_prezzie.html', {})
    url = 'http://www.garbarino.com/productos/producto.php?codigo=%s'
    f = urlopen(url % prezzie_id)
    doc = f.read()
    starttag = '<h1 class="TituloProducto">'
    endtag = '</h1>'
    start = doc.find(starttag)
    end = doc.find(endtag, start)
    if start == -1:
        msg = u"No hay ningún producto con ID %s" % prezzie_id
        return render_to_response('add_prezzie.html', {'msg': msg})
    title = doc[start + len(starttag):end]
    title = title.decode('utf-8').title()
    start = doc.find('>', doc.find('class="PrecioMasInfo"')) + 1
    end = doc.find('</td>', start)
    price = int(doc[start:end])
    if len(Prezzie.objects.filter(garbid=prezzie_id)) > 0:
        msg = "Ya agregaste %s" % title
        return render_to_response('add_prezzie.html', {'msg': msg})
    pats = ['http://www.garbarino.com/img_prod/chicas/%(id)s.gif',
            'http://www.garbarino.com/img_prod/nuevas/%(id)s/%(id)s.jpg',
           ]
    fotitourl = ''
    for pat in pats:
        url = pat % {'id':prezzie_id}
        g = urlopen(url)
        if g.getcode() != 404:
            fotitourl = url
            break
    if 'confirm' in request.GET:
        prezzie = Prezzie(title=title, garbid=prezzie_id, price=price, fotitourl=fotitourl)
        prezzie.save()
        msg = u"Se agregó %s" % title
        return render_to_response('add_prezzie.html', {'msg': msg})
    atts = {'confirm': True,
            'garbid': prezzie_id,
            'title': title,
            'price': price,
            'fotitourl': fotitourl,
            }
    return render_to_response('add_prezzie.html', atts)
