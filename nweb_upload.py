#!/usr/bin/env python
import json
from sys import argv
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

filename = argv[1]
#scantime = argv[2]

if len(argv)!=1:
  print("usage: nweb_upload.py <filename> <scantime>")

f=open(argv[1])

count = 0

for line in f:
  try:
    #print("inserting "+json.loads(line[:-2])['ip'])
    count = count+1
    if count%1000 == 0:
      print("uploaded "+str(count)+" results from "+argv[1]+" ..")

    # ip is unique for "hosts", and "services" indexes all ports
    es.index(index='masscan_hosts', doc_type="_doc", id=json.loads(line[:-2])['ip'], body=line[:-2])
    es.index(index='masscan_services', doc_type="_doc", body=line[:-2])
  except:
    print("whoops ("+argv[1]+")")
    continue

