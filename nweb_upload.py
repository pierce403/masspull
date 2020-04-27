#!/usr/bin/env python
import json
import time
import random
from sys import argv, exit
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

service_index = "masscan_services"
host_index = "nweb_hosts"

if len(argv)!=2:
  exit("usage: nweb_upload.py <filename>")

filename = argv[1] # pull in import source

# ensure that the indexes exist
service_settings = {
  "mappings": {
    "properties": {
      "ip": {
        "type": "ip"
      },
      "port": {
        "type": "integer"
      },
      "timestamp": {
        "type": "date" 
      }
    }
  }
}

host_settings = {
  "mappings": {
    "properties": {
      "ip": {
        "type": "ip"
      },
      "timestamp": {
        "type": "date" 
      }
    }
  }
}

# create indexes, DGAF about errors
es.indices.create(index=service_index, ignore=400, body=service_settings)
es.indices.create(index=host_index, ignore=400, body=host_settings)

f=open(filename)

count = 0
service_actions=[]
host_actions=[]

for line in f:
  try:
    linedata = line.rstrip().split(' ')

    # make sure the line is somewhat what we expect
    # should be masscan --readfile <in.bin> -oL out.txt
    if len(linedata)!=5:
      continue

    service_actions.append({"port":linedata[2],"ip":linedata[3],"timestamp":linedata[4]})
    host_actions.append({"_id":linedata[3],"ip":linedata[3],"timestamp":linedata[4]})
    # check the first five lines for duplicate data
    count = count+1
    if count < 5:
      result = es.search(index=service_index, doc_type="_doc", body={ "query": {"query_string": { 'query':"port:"+linedata[2]+" ip:"+linedata[3]+" timestamp:"+linedata[4], "default_operator":"AND" }}})
      if int(result['hits']['total']['value']) > 0:
        exit("we've already seen this data")

    if len(service_actions)>=10000:
      helpers.bulk(es, service_actions, index=service_index, doc_type='_doc')
      helpers.bulk(es, host_actions, index=host_index, doc_type='_doc')
      service_actions=[]
      host_actions=[]
      print("uploaded "+str(count)+" results from "+filename+" ..")

  except Exception as e:
    print(e)
    print("something went wrong, waiting 5-15 mins ..")
    time.sleep(random.randint(300,1200))
    continue

# don't forget to upload that last part!
helpers.bulk(es, service_actions, index=service_index, doc_type='_doc')
helpers.bulk(es, host_actions, index=host_index, doc_type='_doc')
print("uploaded "+str(count)+" results from "+filename+" ..")
