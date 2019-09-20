from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from django.shortcuts import redirect
from django.core.urlresolvers import reverse


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
	url(r'^topic_finder/', include('topic_finder.urls', namespace='topic_finder')),
)
