from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^gettask/assignment/(?P<assignment_id>.+)$', 'retainer.gettask.get_task'),
    url(r'^ping/worker/(?P<worker_id>.+)/assignment/(?P<assignment_id>.+)/hit/(?P<hit_id>.+)/event/(?P<ping_type>.+)$', 'retainer.ping.ping'),
    url(r'^puttask$', 'retainer.puttask.put_task'),
    url(r'^putwork$', 'retainer.putwork.put_work'),
    url(r'^putwork/done$', 'retainer.putwork.finish_work'),
    # Examples:
    # url(r'^$', 'retainer.views.home', name='home'),
    # url(r'^retainer/', include('retainer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
