from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_app

import urllib, urllib2 #obsolete
import requests
import json
from BeautifulSoup import BeautifulSoup as BS
import time

from topic_finder.models import *

import sys
import gc
EUTILS_BASE = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
CHUNK_SIZE = 10


def pubmed_search(term, retmax=0, retstart=0, retry=5):
    """
    Searches term in PubMed and returns retrieved pids.
    """
    if retmax:
        RetMax = str(retmax)
    else:
        RetMax = '100000'
    term_ascii_only = ''.join([i if ord(i) < 128 else ' ' for i in term])
    url = EUTILS_BASE + 'esearch.fcgi?db=pubmed&term=' + urllib.quote(term_ascii_only) + '&RetMax=' + RetMax + '&RetStart=' + str(retstart)

    session = requests.Session()
    session.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    adapter = requests.adapters.HTTPAdapter()
    session.mount('http://', adapter)

    #xmlRes = urllib2.urlopen(url).read()
    for retries in range(30):
        try:
            xmlRes = session.get(url).text
        ##except requests.ConnectionError:
        except:
            sys.stdout.write("Connection Error occured. Retry: "+str(retries+1))
            time.sleep(10+(retries*3))
        else:
            break

    soup = BS(xmlRes)
    if soup.idlist:
        id_objs = soup.idlist.findAll('id')
    else:
        if retry > 0:
            return pubmed_search(term, retmax=retmax, retstart=retstart, retry=retry-1)
        else:
            print "Failed search: ",term
            return []
    ids = []
    for id_obj in id_objs:
        ids.append(id_obj.text.encode('utf-8'))
    return ids

def pubmed_search_count(term, retmax=0, retstart=0, retry=5):
    """
    Counts the number of search results for term.
    """
    if retmax:
        RetMax = str(retmax)
    else:
        RetMax = '100000'
    term_ascii_only = ''.join([i if ord(i) < 128 else ' ' for i in term])
    url = EUTILS_BASE + 'esearch.fcgi?db=pubmed&term=' + urllib.quote(term_ascii_only) + '&RetMax=' + RetMax + '&RetStart=' + str(retstart) + '&RetType=count'

    session = requests.Session()
    session.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    adapter = requests.adapters.HTTPAdapter()
    session.mount('http://', adapter)

    #xmlRes = urllib2.urlopen(url).read()
    for retries in range(30):
        try:
            xmlRes = session.get(url).text
        ##except requests.ConnectionError:
        except:
            sys.stdout.write("Connection Error occured. Retry: "+str(retries+1))
            time.sleep(10+(retries*3))
        else:
            break

    soup = BS(xmlRes)
    try:
        return int(soup.count.text.encode('utf-8'))
    except:
        if retry > 0:
            return pubmed_search_count(term, retmax=retmax, retstart=retstart, retry=retry-1)
        else:
            print "Failed search_count: ", term
            return -1

def get_authors_list(pid):
    url = EUTILS_BASE + 'efetch.fcgi?db=pubmed&rettype=abstract&id=' + pid
    session = requests.Session()
    session.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    adapter = requests.adapters.HTTPAdapter()
    session.mount('http://', adapter)
    xmlRes = session.get(url).text
    soup = BS(xmlRes)
    authors_list = []
    authors_objs = soup.findAll('author')
    for author_obj in authors_objs:
        author_full_name = ''
        if author_obj.initials:
            author_full_name += author_obj.initials.text + ' '
        if author_obj.lastname:
            author_full_name += author_obj.lastname.text
        if author_full_name:
            authors_list.append(author_full_name)
    return authors_list

def group_by_authors(term):
    pids = pubmed_search(term)
    authors_sets = {}
    for pid in pids:
        authors_sets[pid] = set(get_authors_list(pid))
    groups = []
    for pid, authors_set in authors_sets.items():
        for pid2, authors_set2 in authors_sets.items():
            if (pid != pid2) and authors_set.intersection(authors_set2):
                new_group = True
                for group in groups:
                    if set([pid,pid2]).intersection(group):
                        group.update(set([pid,pid2]))
                        new_group = False
                if new_group:
                    groups.append(set([pid,pid2]))
    for pid in pids:
        has_no_group = True
        for group in groups:
            if pid in group:
                has_no_group = False
        if has_no_group:
            groups.append(set([pid]))
    return groups


@shared_task
def get_keywords_data(tfresult_pk, chunk_first_idx=0):
    tfresult = TopicFinderResult.objects.get(pk=tfresult_pk)
    search_query = tfresult.tfinput.get_search_query()
    base_query = tfresult.tfinput.get_base_query()
    ids = pubmed_search(search_query)
    tfresult.total_count = len(ids)
    #if chunk does not exist, finish the process
    if chunk_first_idx > tfresult.total_count - 1:
        return
    tfresult.done_count = 0+chunk_first_idx
    tfresult.save(update_fields=['total_count','done_count'])
    chunk = ids[chunk_first_idx:chunk_first_idx+CHUNK_SIZE]
    #using requests.session for supposedly better performance and avoiding crashes
    session = requests.Session()
    session.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    adapter = requests.adapters.HTTPAdapter()
    session.mount('http://', adapter)
    #headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    for idx in range(len(chunk)):
        #sys.stdout.write("\r%d/%d"%(idx+1,len(ids)))
        #sys.stdout.flush()
        id = chunk[idx]
        if id in tfresult.visited_ids:
            tfresult.done_count += 1
            tfresult.save(update_fields=['done_count'])
            continue
        url = EUTILS_BASE + 'efetch.fcgi?db=pubmed&rettype=abstract&id=' + id
        
        for retries in range(30):
            try:
                xmlRes = session.get(url).text
            ##except requests.ConnectionError:
            except:
                sys.stdout.write("Connection Error occured. Retry: "+str(retries+1))
                time.sleep(10+(retries*3))
            else:
                break
        
        soup = BS(xmlRes)

        if soup.chemicallist:
            chemical_objs = soup.chemicallist.findAll('nameofsubstance')
        else:
            chemical_objs = []

        if soup.meshheadinglist:
            descriptor_objs = soup.meshheadinglist.findAll('descriptorname')
        else:
            descriptor_objs = []

        if soup.keywordlist:
            keyword_objs = soup.keywordlist.findAll('keyword')
        else:
            keyword_objs = []
        if keyword_objs or descriptor_objs or chemical_objs:
            for obj in keyword_objs + descriptor_objs + chemical_objs:
                keyword = obj.text.lower() #.lower() to avoid getting stat for both "Heart Failure" and "heart failure"
                if not tfresult.keywords_data.get(keyword) and not keyword in base_query: #TODO: remove Person, Statistics and other nonspecific mesh terms
                    tfresult.current_keyword = keyword
                    tfresult.save(update_fields=['current_keyword'])
                    wide_sysrev_count = pubmed_search_count(tfresult.tfinput.get_main_keyword_wo_title()
                                                  + ' AND ("systematic review" OR "systematic reviews" OR "meta-analysis") AND "%s"'%(keyword))
                    meta_result = pubmed_search(base_query 
                                                + ' AND "meta-analysis" AND "%s"'%(keyword))
                    meta_count = len(meta_result)
                    sysrev_result = pubmed_search(base_query 
                                                  + ' AND ("systematic review" OR "systematic reviews" OR "meta-analysis") AND "%s"'%(keyword))
                    sysrev_count = len(sysrev_result)
                    topic_count = pubmed_search_count(base_query 
                                                      + ' AND "%s"'%(keyword))
                    title_count = pubmed_search_count(base_query 
                                                      + ' AND "%s"[Title]'%(keyword))
                    type_count = pubmed_search_count(tfresult.tfinput.main_keyword
                                                     + ' AND %s AND "%s"[Title]'%(tfresult.tfinput.get_type_query(),
                                                                                  keyword))

                    tfresult.keywords_data[keyword] = {'meta_count':meta_count, 
                                                       'meta_result': meta_result,
                                                       'sysrev_count':sysrev_count,
                                                       'sysrev_result':sysrev_result,
                                                       'title_count':title_count, 
                                                       'topic_count':topic_count, 
                                                       'type_count':type_count,
                                                       'wide_sysrev_count':wide_sysrev_count}
                    tfresult.save(update_fields=['keywords_data'])
                    time.sleep(0.5) #to avoid ratelimitation TODO: figure out optimized sleep time
        else:
            tfresult.no_keywords.append(id)
        tfresult.visited_ids.append(id)
        tfresult.done_count += 1
        tfresult.save(update_fields=['visited_ids','done_count'])

    sys.stdout.write("Chunk Done: from %d to %d"%(chunk_first_idx+1, chunk_first_idx+CHUNK_SIZE+1))
    return get_keywords_data.delay(tfresult.pk,chunk_first_idx=chunk_first_idx+CHUNK_SIZE)

@shared_task
def get_keywords_data_clinical(ctfresult_pk, chunk_first_idx=0):
    ctfresult = TopicFinderResultClinical.objects.get(pk=ctfresult_pk)
    search_query = ctfresult.ctfinput.get_search_query()
    base_query = ctfresult.ctfinput.get_base_query()
    ids = pubmed_search(search_query)
    ctfresult.total_count = len(ids)
    #if chunk does not exist, finish the process
    if chunk_first_idx > ctfresult.total_count - 1:
        return
    ctfresult.done_count = 0+chunk_first_idx
    ctfresult.save(update_fields=['total_count','done_count'])
    chunk = ids[chunk_first_idx:chunk_first_idx+CHUNK_SIZE]
    #using requests.session for supposedly better performance and avoiding crashes
    session = requests.Session()
    session.headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    adapter = requests.adapters.HTTPAdapter()
    session.mount('http://', adapter)
    #headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0' }
    for idx in range(len(chunk)):
        #sys.stdout.write("\r%d/%d"%(idx+1,len(ids)))
        #sys.stdout.flush()
        id = chunk[idx]
        if id in ctfresult.visited_ids:
            ctfresult.done_count += 1
            ctfresult.save(update_fields=['done_count'])
            continue
        url = EUTILS_BASE + 'efetch.fcgi?db=pubmed&rettype=abstract&id=' + id
        
        for retries in range(30):
            try:
                xmlRes = session.get(url).text
            ##except requests.ConnectionError:
            except:
                sys.stdout.write("Connection Error occured. Retry: "+str(retries+1))
                time.sleep(10+(retries*3))
            else:
                break
       
        soup = BS(xmlRes)

        if soup.chemicallist:
            chemical_objs = soup.chemicallist.findAll('nameofsubstance')
        else:
            chemical_objs = []

        if soup.meshheadinglist:
            descriptor_objs = soup.meshheadinglist.findAll('descriptorname')
        else:
            descriptor_objs = []

        if soup.keywordlist:
            keyword_objs = soup.keywordlist.findAll('keyword')
        else:
            keyword_objs = []
        if keyword_objs or descriptor_objs or chemical_objs:
            for obj in keyword_objs + descriptor_objs + chemical_objs:
                keyword = obj.text.lower() #.lower() to avoid getting stat for both "Heart Failure" and "heart failure"
                if not ctfresult.keywords_data.get(keyword) and not keyword in base_query: #TODO: remove Person, Statistics and other nonspecific mesh terms
                    ctfresult.current_keyword = keyword
                    ctfresult.save(update_fields=['current_keyword'])
                    from_disease_count = pubmed_search_count(search_query 
                                                                + ' AND "%s"[Title]'%(keyword))
                    title_studytype_count = pubmed_search_count(base_query 
                                                                + ' AND "%s"[Title]'%(keyword))
                    title_count = pubmed_search_count(ctfresult.ctfinput.to_disease
                                                        + ' AND "%s"[Title]'%(keyword))
                    topic_count = pubmed_search_count(ctfresult.ctfinput.to_disease
                                                        + ' AND "%s"'%(keyword))
                    wide_count = pubmed_search_count(ctfresult.ctfinput.get_to_disease_wo_title()
                                                     + ' AND "%s"'%(keyword))

                    ctfresult.keywords_data[keyword] = {'from_disease_count': from_disease_count,
                                                        'title_studytype_count': title_studytype_count,
                                                        'title_count': title_count,
                                                        'topic_count': topic_count,
                                                        'wide_count': wide_count}
                    ctfresult.save(update_fields=['keywords_data'])
                    time.sleep(0.5) #to avoid ratelimitation TODO: figure out optimized sleep time
        else:
            ctfresult.no_keywords.append(id)
        ctfresult.visited_ids.append(id)
        ctfresult.done_count += 1
        ctfresult.save(update_fields=['visited_ids','done_count'])

    sys.stdout.write("Chunk Done: from %d to %d"%(chunk_first_idx+1, chunk_first_idx+CHUNK_SIZE+1))
    return get_keywords_data_clinical.delay(ctfresult.pk,chunk_first_idx=chunk_first_idx+CHUNK_SIZE)