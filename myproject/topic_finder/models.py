from django.db import models

from jsonfield import JSONField
import json
import datetime

PROGNOSTIC = 'PRG'
PROGNOSTIC_TITLE = 'PRT'
DIAGNOSTIC = 'DIG'
DIAGNOSTIC_TITLE = 'DGT'
DIAGNOSTIC_FREE = 'DGF'
CLINICAL_TRIAL = 'CT'
RCT = 'RCT'
ALL = 'ALL'
STUDY_TYPES = (
    (PROGNOSTIC,      'Prognostic'),
    (PROGNOSTIC_TITLE,'Prognostic Title'),
    (DIAGNOSTIC,      'Diagnostic'),
    (DIAGNOSTIC_TITLE,'Diagnostic Title'),
    (DIAGNOSTIC_FREE, 'Diagnostic Excluding Prognostic'),
    (CLINICAL_TRIAL,  'Clinical Trial'),
    (RCT,             'RCT'),
    (ALL,             'All'),
    )
STUDY_TYPE_SEARCH_QUERIES = {
    PROGNOSTIC: '(prognos* OR predict*)',
    PROGNOSTIC_TITLE: '(prognos*[Title] OR predict*[Title])',
    DIAGNOSTIC: 'sensitivity',
    DIAGNOSTIC_TITLE: '(diagnostic[Title] OR diagnosis[Title])',
    DIAGNOSTIC_FREE: 'sensitivity',
    CLINICAL_TRIAL: '"Clinical Trial"[pt]',
    RCT: '"Randomized Controlled Trial"[pt]',
    ALL: ''}

STUDY_TYPE_BASE_QUERIES = {
    PROGNOSTIC: '(prognos* OR predict*)',
    PROGNOSTIC_TITLE: '(prognos* OR predict*)',
    DIAGNOSTIC: 'sensitivity',
    DIAGNOSTIC_TITLE: 'sensitivity',
    DIAGNOSTIC_FREE: 'sensitivity NOT ("follow-up studies" OR prognos*)',
    CLINICAL_TRIAL: '',
    RCT: '',
    ALL: ''}


class TopicFinderInput(models.Model):     
    main_keyword = models.TextField(default='') #disease, marker, test or intervention
    #main_keyword_in_title = models.BooleanField(default=True)
    study_type = models.CharField(max_length=3,
                                  choices = STUDY_TYPES,
                                  default = PROGNOSTIC)
    #study_type_in_title = models.BooleanField(default=False)
    from_year = models.IntegerField(default = 0)
    to_year = models.IntegerField(default = datetime.date.today().year)    
    custom_search_query = models.TextField(default='', blank=True)
    custom_base_query = models.TextField(default='', blank=True)
    search_date = models.DateField(auto_now_add=True)
    
    def __unicode__(self):
        return self.main_keyword + ' (' + self.study_type + ')'
    
    def get_search_query(self):
        if self.custom_search_query:
            return self.custom_search_query
        search_query = self.main_keyword
        ##TODO: strip, rstrip and deal with " " and alternative names
        search_query += ' '+STUDY_TYPE_SEARCH_QUERIES[self.study_type]+' '
        search_query += str(self.from_year)+':'+str(self.to_year)+'[DP]'    
        return search_query
        
    def get_base_query(self):
        if self.custom_base_query:
            return self.custom_base_query
        base_query = self.main_keyword
        base_query += ' '+STUDY_TYPE_BASE_QUERIES[self.study_type]+' '
        return base_query
        
        
    def get_type_query(self):
        if self.study_type == RCT: 
            return STUDY_TYPE_SEARCH_QUERIES[CLINICAL_TRIAL]
        else:
            return STUDY_TYPE_SEARCH_QUERIES[self.study_type]
            
    def get_main_keyword_wo_title(self):
        return self.main_keyword.replace('[Title]','')
            
class TopicFinderResult(models.Model):
    tfinput = models.OneToOneField(TopicFinderInput,
                                   on_delete = models.CASCADE,
                                   primary_key = True,
                                   related_name = 'result')
    visited_ids = JSONField(default=json.dumps([]))
    total_count = models.IntegerField(default=0)
    done_count = models.IntegerField(default=0)
    no_keywords = JSONField(default=json.dumps([])) # json list
    keywords_data = JSONField(default=json.dumps({})) # json dictionary
    current_keyword = models.TextField(default='', blank=True)
    celery_task_id = models.CharField(max_length=100, default='')
    
    def __unicode__(self):
        return self.tfinput.__unicode__()

class TopicFinderInputClinical(models.Model):
    from_disease = models.TextField(default='')
    to_disease = models.TextField(default='')
    study_type = models.CharField(max_length=3,
                                  choices = STUDY_TYPES,
                                  default = PROGNOSTIC)
    from_year = models.IntegerField(default = 0)
    to_year = models.IntegerField(default = datetime.date.today().year)    
    search_date = models.DateField(auto_now_add=True) 

    def __unicode__(self):
        return 'From ' + self.from_disease + ' To ' + self.to_disease + ' (' + self.study_type + ')'
    
    def get_search_query(self):
        search_query = self.from_disease
        ##TODO: strip, rstrip and deal with " " and alternative names
        search_query += ' '+STUDY_TYPE_SEARCH_QUERIES[self.study_type]+' '
        search_query += str(self.from_year)+':'+str(self.to_year)+'[DP]'    
        return search_query
        
    def get_base_query(self):
        base_query = self.to_disease
        base_query += ' '+STUDY_TYPE_BASE_QUERIES[self.study_type]+' '
        return base_query
        
        
    def get_type_query(self):
        if self.study_type == RCT: 
            return STUDY_TYPE_SEARCH_QUERIES[CLINICAL_TRIAL]
        else:
            return STUDY_TYPE_SEARCH_QUERIES[self.study_type]
            
    def get_to_disease_wo_title(self):
        return self.to_disease.replace('[Title]','')


class TopicFinderResultClinical(models.Model):
    ctfinput = models.OneToOneField(TopicFinderInputClinical,
                                   on_delete = models.CASCADE,
                                   primary_key = True,
                                   related_name = 'cresult')
    visited_ids = JSONField(default=json.dumps([]))
    total_count = models.IntegerField(default=0)
    done_count = models.IntegerField(default=0)
    no_keywords = JSONField(default=json.dumps([])) # json list
    keywords_data = JSONField(default=json.dumps({})) # json dictionary
    current_keyword = models.TextField(default='', blank=True)
    celery_task_id = models.CharField(max_length=100, default='')
    
    def __unicode__(self):
        return self.ctfinput.__unicode__()