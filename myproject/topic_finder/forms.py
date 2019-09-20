from django import forms
from topic_finder import models
from django.core.exceptions import ValidationError
from topic_finder import tasks

class TopicFinderForm(forms.ModelForm):
    custom_search_query = forms.CharField(required = False,
                                          max_length = 10000,
                                          widget = forms.widgets.Textarea)
    custom_base_query = forms.CharField(required = False,
                                        max_length = 10000,
                                        widget = forms.widgets.Textarea)
    class Meta:
        model = models.TopicFinderInput
        fields = '__all__'
        widgets = {
            'main_keyword': forms.widgets.TextInput
        }
        help_texts = {
            'main_keyword': 'A disease, prognostic marker, \
                             diagnostic test or an intervention',
            'from_year': 'Put 0 to search from the beginning',
        }

class TopicFinderFormClinical(forms.ModelForm):
    class Meta:
        model = models.TopicFinderInputClinical
        fields = ['from_disease', 'to_disease', 'study_type', 'from_year', 'to_year']
        widgets = {
            'from_disease': forms.widgets.TextInput,
            'to_disease': forms.widgets.TextInput
        }
        help_texts = {
            'from_year': 'Put 0 to search from the beginning',
        }
