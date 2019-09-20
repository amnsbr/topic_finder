# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TopicFinderInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('main_keyword', models.TextField(default=b'')),
                ('study_type', models.CharField(default=b'PRG', max_length=3, choices=[(b'PRG', b'Prognostic'), (b'PRT', b'Prognostic Title'), (b'DIG', b'Diagnostic'), (b'DGT', b'Diagnostic Title'), (b'DGF', b'Diagnostic Excluding Prognostic'), (b'CT', b'Clinical Trial'), (b'RCT', b'RCT'), (b'ALL', b'All')])),
                ('from_year', models.IntegerField(default=0)),
                ('to_year', models.IntegerField(default=2019)),
                ('custom_search_query', models.TextField(default=b'', blank=True)),
                ('custom_base_query', models.TextField(default=b'', blank=True)),
                ('search_date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TopicFinderInputClinical',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_disease', models.TextField(default=b'')),
                ('to_disease', models.TextField(default=b'')),
                ('study_type', models.CharField(default=b'PRG', max_length=3, choices=[(b'PRG', b'Prognostic'), (b'PRT', b'Prognostic Title'), (b'DIG', b'Diagnostic'), (b'DGT', b'Diagnostic Title'), (b'DGF', b'Diagnostic Excluding Prognostic'), (b'CT', b'Clinical Trial'), (b'RCT', b'RCT'), (b'ALL', b'All')])),
                ('from_year', models.IntegerField(default=0)),
                ('to_year', models.IntegerField(default=2019)),
                ('search_date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TopicFinderResult',
            fields=[
                ('tfinput', models.OneToOneField(related_name='result', primary_key=True, serialize=False, to='topic_finder.TopicFinderInput')),
                ('visited_ids', jsonfield.fields.JSONField(default=b'[]')),
                ('total_count', models.IntegerField(default=0)),
                ('done_count', models.IntegerField(default=0)),
                ('no_keywords', jsonfield.fields.JSONField(default=b'[]')),
                ('keywords_data', jsonfield.fields.JSONField(default=b'{}')),
                ('current_keyword', models.TextField(default=b'', blank=True)),
                ('celery_task_id', models.CharField(default=b'', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TopicFinderResultClinical',
            fields=[
                ('ctfinput', models.OneToOneField(related_name='cresult', primary_key=True, serialize=False, to='topic_finder.TopicFinderInputClinical')),
                ('visited_ids', jsonfield.fields.JSONField(default=b'[]')),
                ('total_count', models.IntegerField(default=0)),
                ('done_count', models.IntegerField(default=0)),
                ('no_keywords', jsonfield.fields.JSONField(default=b'[]')),
                ('keywords_data', jsonfield.fields.JSONField(default=b'{}')),
                ('current_keyword', models.TextField(default=b'', blank=True)),
                ('celery_task_id', models.CharField(default=b'', max_length=100)),
            ],
        ),
    ]
