from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gettask/worker/(?P<worker_id>.+)/assignment/(?P<assignment_id>.+)$', 'retainer.gettask.get_task'),
    # Examples:
    # url(r'^$', 'retainer.views.home', name='home'),
    # url(r'^retainer/', include('retainer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
