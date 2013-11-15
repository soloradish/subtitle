__author__ = 'lowID'
import re
import sys
from google.appengine.api import urlfetch
from errors import FetchError

sys.path.insert(0, 'libs')
from bs4 import BeautifulSoup

xml_gen_prefix = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?uri='


def fetch_subtitle(url):
    res = urlfetch.fetch(url)
    if res.status_code == 200:
        return res.content
    else:
        raise FetchError('<Fetching error>, response code is %s.' % res.status_code)


def get_sub_info(xml_url):
    """
    Receive comedy central web site's shadow xml file,
     return the block info with block's title, subtitle file's url and the full episode source link.
    """
    res = urlfetch.fetch(xml_url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content, features='xml')
        items = soup.channel.find_all('item')
        episode_title = soup.title.text
        sub_info = list()
        for item in items:
            item_info = dict()
            try:
                item_info['sub_url'] = item.find('text')['src']
                item_info['block_title'] = item.find('title').text
                item_info['episode_title'] = episode_title
                item_info['source_link'] = item.link.text
                sub_info.append(item_info)
            except TypeError:
                pass
                #Do some logs

        return sub_info
    else:
        raise FetchError('<Fetching error>, response code is %s.' % res.status_code)


def get_epi_xml(epi_url):
    """
    Receive the episode display page's url,
     return shadow xml file's url.
    """
    res = urlfetch.fetch(epi_url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content)
        epi_xml_url = xml_gen_prefix + soup.find_all(id='video_player_box')[0]['data-mgid']
        return epi_xml_url
    else:
        raise FetchError('<Fetching error>, response code is %s.' % res.status_code)


def get_epi_infos(full_epi_url, channel):
    """
    Receive the full episodes page's url,
     return the all episodes display page's url.
    """
    res = urlfetch.fetch(full_epi_url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content)
        epi_infos = list()
        view_list = soup.find_all('li', class_=re.compile('list_item'))
        for item in view_list:
            item_info = dict()
            item_info['epi_url'] = item.find('a')['href']
            item_info['date'] = item.find('span', class_='air_date').text
            item_info['guest'] = item.find('span', class_='guest').text.replace('-', '').replace(u'\xa0', u'')
            item_info['channel'] = channel
            epi_infos.append(item_info)
        return epi_infos
    else:
        raise FetchError('<Fetching error>, response code is %s.' % res.status_code)