from django.conf.urls import patterns,url
from topic_finder import views

urlpatterns = patterns('',
	url(r'group_authors$', views.group_authors, name='group_authors'),
	url(r'resume/(?P<id>\d+)$', views.resume, name='resume'),
	url(r'stop/(?P<id>\d+)$', views.stop, name='stop'),
	url(r'get_progress$', views.get_progress, name='get_progress'),
	url(r'result/(?P<id>\d+)$', views.show_result, name='result'),
	url(r'result_clinical/(?P<id>\d+)$', views.show_result_clinical, name='result_clinical'),
	url(r'clinical$', views.start_clinical, name='start_clinical'),	
	url(r'sysrev$',views.start, name='start'),
)