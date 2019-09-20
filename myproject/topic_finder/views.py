from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404, FileResponse
from django.views.decorators.cache import never_cache
import json
from topic_finder.models import TopicFinderInput, TopicFinderResult, TopicFinderInputClinical, TopicFinderResultClinical
from topic_finder.forms import TopicFinderForm, TopicFinderFormClinical
from topic_finder import tasks
from myproject.celery import app as celery_app
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def start(request):
    if request.method == 'POST':
        bound_form = TopicFinderForm(request.POST)
        if bound_form.is_valid():
            try:
                tfinput = TopicFinderInput.objects.get(main_keyword = bound_form.cleaned_data['main_keyword'],
                                                  study_type = bound_form.cleaned_data['study_type'])
                bound_existing_form = TopicFinderForm(request.POST, instance = tfinput)
                tfinput = bound_existing_form.save()
                tfresult = tfinput.result
            except:
                tfinput = bound_form.save()
                tfresult = TopicFinderResult(tfinput = tfinput)
                tfresult.save()
            res = tasks.get_keywords_data.delay(tfresult.pk)
            tfresult.celery_task_id = res.task_id
            tfresult.save()
            
            return redirect(reverse('topic_finder:result', kwargs={'id':tfresult.pk}))
    form = TopicFinderForm()
    return render(request,'topic_finder/start.html',{'form':form})

def start_clinical(request):
    if request.method == 'POST':
        bound_form = TopicFinderFormClinical(request.POST)
        if bound_form.is_valid():
            try:
                ctfinput = TopicFinderInputClinical.objects.get(from_disease = bound_form.cleaned_data['from_disease'],
                                                                to_disease = bound_form.cleaned_data['to_disease'],
                                                                study_type = bound_form.cleaned_data['study_type'])
                bound_existing_form = TopicFinderFormClinical(request.POST, instance = ctfinput)
                ctfinput = bound_existing_form.save()
                ctfresult = ctfinput.cresult
            except:
                ctfinput = bound_form.save()
                ctfresult = TopicFinderResultClinical(ctfinput = ctfinput)
                ctfresult.save()
            res = tasks.get_keywords_data_clinical.delay(ctfresult.pk)
            ctfresult.celery_task_id = res.task_id
            ctfresult.save()
            
            return redirect(reverse('result_clinical', kwargs={'id':ctfresult.pk}))
    form = TopicFinderFormClinical()
    return render(request,'topic_finder/start.html',{'form':form})
    
def show_result(request, id):
    if request.GET.get('full'):
        full_results = True
    else:
        full_results = False
    tfresult = get_object_or_404(TopicFinderResult, pk=int(id))
    sorted_keywords_data = sorted(tfresult.keywords_data.items(), 
                                  key = lambda item: (item[1]['meta_count'], 
                                                      -item[1]['type_count'], 
                                                      -item[1]['title_count'], 
                                                      -item[1]['topic_count']))
    total_keywords_count = len(sorted_keywords_data)
    useful_keywords_data = []
    if not full_results:
        for keyword_data in sorted_keywords_data:
            if (keyword_data[1]['meta_count'] < 2) \
                and (keyword_data[1]['title_count'] > 0)\
                and (keyword_data[1]['topic_count'] > 1):
                useful_keywords_data.append(keyword_data)
        sorted_keywords_data = useful_keywords_data
    return render(request,
                  template_name='topic_finder/result.html',
                  context= {'tfresult':tfresult, 
                            'keywords_data':sorted_keywords_data, 
                            'no_keywords':tfresult.no_keywords, 
                            'visited_count': len(tfresult.visited_ids), 
                            'visited_ids':tfresult.visited_ids,
                            'task_id':tfresult.celery_task_id,
                            'total_keywords_count':total_keywords_count,
                            'full_results':full_results})

def show_result_clinical(request, id):
    if request.GET.get('full'):
        full_results = True
    else:
        full_results = False
    ctfresult = get_object_or_404(TopicFinderResultClinical, pk=int(id))
    sorted_keywords_data = sorted(ctfresult.keywords_data.items(), 
                                  key = lambda item: (item[1]['wide_count'], 
                                                      -item[1]['from_disease_count'],
                                                      item[1]['title_studytype_count'], 
                                                      item[1]['title_count'], 
                                                      item[1]['topic_count']))
    total_keywords_count = len(sorted_keywords_data)
    useful_keywords_data = []
    if not full_results:
        for keyword_data in sorted_keywords_data:
            if (keyword_data[1]['wide_count'] < 2) \
                and (keyword_data[1]['from_disease_count'] > 0):
                useful_keywords_data.append(keyword_data)
        sorted_keywords_data = useful_keywords_data
    paginator = Paginator(sorted_keywords_data, 100) # Show 25 contacts per page
    page = request.GET.get('page')
    try:
        sorted_keywords_data = paginator.page(page) 
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        sorted_keywords_data = paginator.page(1)
        page = 1
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        sorted_keywords_data = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    start_number = (int(page) - 1) * 100
    return render(request,
                  template_name='topic_finder/result_clinical.html',
                  context= {'ctfresult':ctfresult, 
                            'keywords_data':sorted_keywords_data, 
                            'no_keywords':ctfresult.no_keywords, 
                            'visited_count': len(ctfresult.visited_ids), 
                            'visited_ids':ctfresult.visited_ids,
                            'task_id':ctfresult.celery_task_id,
                            'total_keywords_count':total_keywords_count,
                            'full_results':full_results,
                            'start_number':start_number})

@never_cache
def get_progress(request):
    clinical = request.GET.get('clinical')
    id = request.GET.get('id')
    if id:
            if clinical:
                tfresult = get_object_or_404(TopicFinderResultClinical, pk=int(id))
            else:
                tfresult = get_object_or_404(TopicFinderResult, pk=int(id))
    else:
        raise Http404
    tfresult.refresh_from_db()
    total = tfresult.total_count
    done = tfresult.done_count
    current_keyword = tfresult.current_keyword
    data = {'total':total, 'done':done, 'current_keyword':current_keyword}
    return HttpResponse(json.dumps(data))
    
def stop(request,id):
    #TODO: ajax
    tfresult = get_object_or_404(TopicFinderResult, pk=int(id))
    celery_app.control.revoke(tfresult.celery_task_id, terminate=True)
    return redirect(reverse('topic_finder:result', kwargs={'id':tfresult.pk}))

def resume(request,id):
    clinical = request.GET.get('clinical')
    if clinical:
        ctfresult = get_object_or_404(TopicFinderResultClinical, pk = int(id))
        res = tasks.get_keywords_data_clinical.delay(ctfresult.pk)
        ctfresult.celery_task_id = res.task_id
        ctfresult.save()
        return redirect(reverse('result_clinical', kwargs={'id':ctfresult.pk}))
    else:
        tfresult = get_object_or_404(TopicFinderResult, pk=int(id))
        res = tasks.get_keywords_data.delay(tfresult.pk)
        tfresult.celery_task_id = res.task_id
        tfresult.save()
        return redirect(reverse('topic_finder:result', kwargs={'id':tfresult.pk}))

def group_authors(request):
    term = request.GET.get('term')
    if term:    
        groups = tasks.group_by_authors(term)
        return render(request,'topic_finder/group_authors.html',{'term':term,
                                                           'groups':groups})
    else:
        raise Http404