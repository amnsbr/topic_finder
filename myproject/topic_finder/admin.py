from django.contrib import admin
from topic_finder.models import *

class TopicFinderAdmin(admin.ModelAdmin):
	search_fields = ('main_keyword', 'study_type')

class ClinicalTopicFinderAdmin(admin.ModelAdmin):
	search_fields = ('from_disease', 'to_disease', 'study_type')

# Register your models here.
admin.site.register(TopicFinderInput, TopicFinderAdmin)
admin.site.register(TopicFinderResult)
admin.site.register(TopicFinderInputClinical, ClinicalTopicFinderAdmin)
admin.site.register(TopicFinderResultClinical)

