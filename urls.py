from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('wedding.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    # Serve static files from ./static
    # Comment this line out in production!!
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.BASE_DIR + '/wedding/static'}),
)


