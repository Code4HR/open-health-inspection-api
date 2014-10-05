from urlparse import urlparse
import config
import random
import requests


class Tracker:

    def __init__(self):
        c = config.load()

        self.params = {}
        try:
            self.endpoint = 'http://' + c['piwik_endpoint'] + '/piwik.php'
        except AttributeError:
            print 'Piwik endpoint not defined!'

        try:
            self.params['idsite'] = c['piwik_siteid'] # ID of the site being tracked
        except AttributeError:
            print 'Piwik site ID not defined!'

        try:
            self.params['token_auth'] = c['piwik_tokenauth']  # API token auth from Piwik
        except AttributeError:
            print 'Piwik token auth not defined!'

        self.params['rec'] = 1  # Required field. (always eq. 1)
        self.params['apiv'] = 1 # API version (always eq. 1)

    def track(self, data):
        if 'User-Agent' in data.headers:
            self.params['ua'] = data.headers['User-Agent']
        if data.referrer:
            self.params['urlref'] = data.referrer

        self.params['url'] = data.url  # full URL of the current action
        self.params['action_name'] = urlparse(data.url).path.replace('/','')
        self.params['_id'] = ''  # unique visitor id
        self.params['rand'] = random.randint(0, 999999)  # random ID for current request
        self.params['cip'] = data.remote_addr

        r = requests.get(self.endpoint, params=self.params)


