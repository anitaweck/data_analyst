# -*- coding: utf-8 -*-
# get original file size from exported file "Meddersheim_Bad-Muenster_Bad-Kreuznach_original"
# get number of data tags from exported file "Meddersheim_Bad-Muenster_Bad-Kreuznach_original"
# get number of unique users for this dataset
'''
Created on Dec 6, 2015

@author: anita
'''

import xml.etree.ElementTree as ET
import json
import pprint
import re
import os
from stat import *

street_map_file = "Meddersheim_Bad-Muenster_Bad-Kreuznach_original"
add_address = {}
CREATED = ["version", "changeset", "timestamp", "user", "uid"]
i = []

def read_file(street_map_file):
    json_data_array = []
    dic_tag = {}
    users = set()
    users = []
    file_orig = os.stat(street_map_file) #get statistical information from dataset
    file_orig_size = float(file_orig.st_size) #get file size
    for event, element in ET.iterparse(street_map_file):
        # get user IDs
        uid = element.get('uid')
        if uid !=None:
            users.append(uid)
        el = shape_element(element)
        # count xml-tags
        if dic_tag.has_key(element.tag):
            dic_tag[element.tag] = dic_tag[element.tag] + 1
        else:
            dic_tag[element.tag] = 1
        if el != {}:
            #set german characters is readable
            json_data = json.dumps(el, indent = 2) +"\n"
            #print json_data
            json_data_array.append(json_data)
    users = set(users)
    f = open("P3_Meddersheim_Germany",'w')
    f.writelines(json_data_array)
    f.close()
    file_json = os.stat(f.name) #get statistical information from dataset
    file_size = float(file_json.st_size) #get file size
    pprint.pprint("0.1 Size of original file from OSM [MB]:")
    pprint.pprint(file_orig_size/1000000) #get size of the original file in [MB]
    pprint.pprint("0.2 Size of json file from OSM [MB]:")
    pprint.pprint(file_size/1000000) #get size of the original file in [MB]
    pprint.pprint("1. Number of nodes, ways and other data:")
    pprint.pprint(dic_tag)
    pprint.pprint("2. Number if unique users:")
    pprint.pprint(len(users))
    return f, dic_tag, users

#separate definition in case 'addr:' is available in different data types
def address_element(child_name, child):
    child_content_new = None
    child_name = child_name.replace("addr:","")
    child_name = child_name.split(":")
    if len(child_name)<2:
        add_address[child_name[0]] = child.get('v')
    elif len(child_name)>1:
        add_address[child_name[1]] = child.get('v')   
    #pattern definitions for wrangling address contents
    p_wrangle = re.compile("(?=hein$)", re.IGNORECASE)
    p_bad = re.compile("bad")
    p_line = re.compile("\w-\w")
    p_street = re.compile("strasse")
    # conistent street naming, use always german characters
    if child_name[0] == "street":
        if re.search(p_street,child.get('v')) != None:
            child_content = child.get('v')
            child_content_new = child_content.replace("strasse", "straße")
            add_address["street"] = child_content_new
    # correct city names spelling mistakes, sensitive style and consistent hyphen whitespacing
    if child_name[0] == "city":
        if re.search(p_wrangle,child.get('v')) != None:
            child_content = child.get('v')
            child_content_new = child_content.replace("hein", "heim")
        elif re.search(p_bad,child.get('v')) != None:
            child_content = child.get('v')
            child_content_new = child_content.replace("bad", "Bad")
        elif re.search(p_line, child.get('v')) != None:
            child_content = child.get('v')
            child_content_new = child_content.replace("-"," - ") 
        if child_content_new != None:
            add_address["city"] = child_content_new
    return add_address

def shape_element(element):
    node = {}
    openGeoDB = {}
    auto_update = []
    is_in = []
    position = []
    node_refs = []
    relation_member_attrib = []
    relation_member = []
    add_created = {}
    tag_sep = []
    tag_sep_dict = {}
    relation_tag_attrib = {}
    child_name = None
    #set type of parsed data based on tag
    if element.tag =="bounds" or element.tag == "note" or element.tag == "meta" or element.tag == "osm" or\
    element.tag == "node" or element.tag == "way" or element.tag == "relation":
        node["type"] = element.tag
    # get information from tags which only appear once
    if element.tag =="bounds" or element.tag == "note" or element.tag == "meta" or element.tag == "osm":
        if element.tag == "note":
            node[element.tag] = element.text
        else:
            node[element.tag] = element.attrib
            #print node
    #shape data
    for child in element:
        child_name = child.get('k')
        p = re.compile('openGeoDB:', re.IGNORECASE)
        
        #put data in an array, because it is a list of descriptive location
        if child_name == "is_in":
            is_in = child.get('v').split(',')
            node[child_name]=is_in
        # get all data which contain 'openGeoDB' also in small letters
        elif child_name != None and re.search(p,child_name) != None:
            child_name = p.sub("", child_name)
            if child_name == 'auto_update':
                auto_update = child.get('v').split(',')
                openGeoDB[child_name]=auto_update
            elif child_name == "is_in":
                is_in = child.get('v').split(',')
                openGeoDB[child_name]=is_in
            elif child_name == 'lat':
                position.append(float(child.get('v')))
            elif child_name == 'lon':
                position.append(float(child.get('v')))
            else:
                openGeoDB[child_name] = child.get('v')
            # put latitude and longitude data in an array which are inside 'openGeoDB' data
            openGeoDB['position'] = position
            node['openGeoDB'] = openGeoDB
            #print node
        #check all data which contain a 'ref'-tag
        elif child.get('ref') != None:
                node_refs.append(child.get('ref'))
                node['node_refs'] = node_refs
        #shape all data in 'tag'-tag because some names are the same like in nodes => type, so cluster 'tag' is kept
        elif child.tag == "tag":
            child_name = child.get('k')
            #shape address data in dictionary address
            if child_name != None and child.get('k').startswith("addr:"):
                add_address = address_element(child_name, child)
                node["address"]=add_address
            #shape all other data which use ':' as a separator depending on amount of this separator
            elif re.search(':', child_name) != None:
                tag_sep = child_name.split(':')
                i.append(len(tag_sep))
                if len(tag_sep) == 2:
                    tag_sep_dict[tag_sep[1]] = child.get('v') 
                    node[tag_sep[0]] = tag_sep_dict
                elif len(tag_sep) == 3:
                    tag_sep_dict[tag_sep[2]] = child.get('v') 
                    node[tag_sep[0]] = tag_sep_dict
                elif len(tag_sep) == 4:
                    tag_sep_dict[tag_sep[3]] = child.get('v') 
                    node[tag_sep[0]] = tag_sep_dict   
            else:
                relation_tag_attrib[child.get('k')] = child.get('v')
                node['tag'] = relation_tag_attrib   
        #shape 'member'-tag data in dicitionary 'member' inside dictionary node
        elif child.tag == "member":
                #print child.get('type')
                relation_member_attrib = child.get('type'), child.get('ref'), child.get('role')
                relation_member.append(relation_member_attrib)
                node['member'] = relation_member
        else:
            if child_name != None:
                node[child_name]=child.get('v')
    #shape tag header-data in 'CREATED' dictionary, see lesson 6 - Cast Study - OpenStreetMap data
    for elem in element.attrib:
        for entry in CREATED:
            if elem == entry and elem != None:
                if element.get(entry) != None:
                    add_created[elem] = element.get(entry)
            elif elem == "id" and elem != None:
                if element.get(elem) != None:
                    node[elem] = element.get(elem)
    #shape position data in positin array for each data-element
    if element.get != None and element.get('lat') or element.get('lon'):
        position = []
        position.append(float(element.get('lat')))   
        position.append(float(element.get('lon')))
        node["pos"]= position
    if len(add_created) > 1:
        node["created"] = add_created
    return node

def get_db():
    #import MongoClient from pymongo
    from pymongo import MongoClient
    client = MongoClient('localhost',27017)
    #print client
    db = client['DW_P3_OSM_after']
    coll = db.P3_Meddersheim_Germany
    return db
 
#getting wineries    
def range_query():
    query = {"tag.shop":"winery"}
    return query

#getting types of nodes   
def make_pipeline():
    pipeline = []
    pipeline = [{"$match":{"type":"node","type":{"$ne":None},"tag.amenity":{"$ne":None}}},
                {"$group":{"_id":"$tag.amenity","count":{"$sum":1}}},
                {"$sort":{"count":-1}}]
    #pipeline = [{"$match":{"openGeoDB.type":{"$ne":None}}},
    #            {"$group":{"_id":"$openGeoDB.type","count":{"$sum":1}}},
    #            {"$sort":{"count":-1}}]
    #print pipeline
    return pipeline

def osm_sources(db, pipeline):
    return [doc for doc in db.P3_Meddersheim_Germany.aggregate(pipeline)]

if __name__ == '__main__':
    read_file(street_map_file)
    db = get_db()
    pipeline = make_pipeline()
    query = range_query()
    result_id = db.P3_Meddersheim_Germany.find(query)
    for r in result_id:
        pprint.pprint(r)
    result = osm_sources(db, pipeline)
    pprint.pprint(result_id)
    pprint.pprint(result)
    #pass