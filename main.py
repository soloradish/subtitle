#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import sys
sys.path.insert(0, 'libs')
import webapp2
import datetime
import json
from google.appengine.ext import db
from subtitle import *
from errors import FetchError


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Implement DATA API yourself...')


class CronHandler(webapp2.RequestHandler):
    def get(self):
        tds_full_epi = 'http://www.thedailyshow.com/full-episodes'
        cbr_full_epi = 'http://www.colbertnation.com/full-episodes'
        epi_infos = list()
        try:
            epi_infos.extend(get_epi_infos(tds_full_epi, 'tds'))
            epi_infos.extend(get_epi_infos(cbr_full_epi, 'cbr'))
            epi_saved = list()
            epi_xml_urls = list()
            sub_infos = list()

            for epi_info in epi_infos:
                episode = Episode.get_by_key_name(epi_info['epi_url'])
                if episode:
                    #Check if fetched the episode before.
                    self.response.write(u'Get nothing new.\n')
                else:
                    episode = Episode.get_or_insert(key_name=epi_info['epi_url'])
                    episode.epi_url = epi_info['epi_url']
                    episode.epi_date = epi_info['date']
                    episode.epi_channel = epi_info['channel']
                    episode.epi_guest = epi_info['guest']
                    episode.epi_create_date = datetime.datetime.now()
                    episode.put()
                    epi_saved.append(epi_info['epi_url'])

            #Gather the full episodes xml urls.
            for epi in epi_saved:
                epi_xml_urls.append(get_epi_xml(epi))

            #Gather the block sub urls.
            for epi_xml_url in epi_xml_urls:
                sub_infos.extend(get_sub_info(epi_xml_url))

            #Fetch and store the subtitles.
            for sub_info in sub_infos:
                sub_parent = Episode.get_by_key_name(sub_info['source_link'])
                block = Block.get_by_key_name(sub_info['sub_url'])
                if block:
                    #Do some logs.
                    pass
                else:
                    block = Block.get_or_insert(key_name=sub_info['sub_url'], parent=sub_parent)
                    block.blk_title = sub_info['block_title']
                    block.blk_sub_url = sub_info['sub_url']
                    block.blk_create_date = datetime.datetime.now()
                    block.put()

            self.response.write('Done')

        except FetchError:
            self.response.write('FetchError')
            #log something.


class InitHandler(webapp2.RequestHandler):
    #Because the handler executing deadline. You may get a 500 error when you run the CronHandler first time.
    #So you need to run this Handler an give a integer as the parameter. Iterate the episodes info manually.
    def get(self, _offset):
        _offset = int(_offset)
        limit = 5
        episodes = Episode.all()
        epi_xmls = list()
        sub_infos = list()
        for episode in episodes.run(offset=_offset, limit=limit):
            epi_xmls.append(get_epi_xml(episode.epi_url))
        for epi_xml in epi_xmls:
            sub_infos.extend(get_sub_info(epi_xml))
        for sub_info in sub_infos:
            sub_parent = Episode.get_by_key_name(sub_info['source_link'])
            block = Block.get_by_key_name(sub_info['sub_url'])
            if block:
                #Do some logs.
                pass
            else:
                block = Block.get_or_insert(key_name=sub_info['sub_url'], parent=sub_parent)
                block.blk_title = sub_info['block_title']
                block.blk_sub_url = sub_info['sub_url']
                block.blk_create_date = datetime.datetime.now()
                block.put()
        self.response.write('Done page %s' % _offset)


class Episode(db.Model):
    epi_url = db.StringProperty()
    epi_date = db.StringProperty()
    epi_guest = db.StringProperty()
    epi_channel = db.StringProperty()
    epi_create_date = db.DateTimeProperty()


class Block(db.Model):
    blk_title = db.StringProperty()
    blk_sub_url = db.StringProperty()
    blk_create_date = db.DateTimeProperty()

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/task/fetchsubtitle', CronHandler),
    (r'/init/(\d+)', InitHandler)
], debug=True)
