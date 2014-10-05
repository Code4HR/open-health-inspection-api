import mongolab
import json
import os
import re
from math import radians, cos, sin, atan2, sqrt
from collections import OrderedDict
from datetime import datetime
from flask import Flask, Response, url_for, request, current_app, render_template
from functools import wraps
from livesdataexporter import LivesDataExporter
from piwik import Tracker
from threading import Thread

app = Flask(__name__)
app.debug = False

try:
    db = mongolab.connect()
except ValueError:
    print "Could not connect to database"

piwik = Tracker()

@app.before_request
def before_request():
    if piwik:
        piwik.track(request)


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args, **kwargs)) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return Response(f(*args, **kwargs), mimetype='application/json')
    return decorated_function


def great_circle(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # great circle formula
    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    # radius of earth in meters
    m = 6378137 * c
    return m

@app.route('/')
@support_jsonp
def api_root():
    links = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            links.append(rule.rule)
    return json.dumps(links)


@app.route('/vendors')
@support_jsonp
def api_vendors():

    limit = 1500
    query = {}
    output = {'name': 1,
              'address': 1,
              'city': 1,
              'locality': 1,
              'category': 1,
              'type': 1,
              'score': 1,
              'slug': 1,
              'geo.coordinates': 1}

    if request.args.get('limit') is not None:
        limit = int(request.args.get('limit'))
    if request.args.get('category') is not None:
        query.update({'category': re.compile(re.escape(request.args.get('category')), re.IGNORECASE)})
    if request.args.get('type') is not None:
        query.update({'type': re.compile(re.escape(request.args.get('type')), re.IGNORECASE)})
    if request.args.get('name') is not None:
        query['name'] = re.compile(re.escape(request.args.get('name')), re.IGNORECASE)
    if request.args.get('address') is not None:
        query['address'] = re.compile(re.escape(request.args.get('address')), re.IGNORECASE)
    if request.args.get('city') is not None:
        query['city'] = re.compile(re.escape(request.args.get('city')), re.IGNORECASE)
    if request.args.get('locality') is not None:
        query['locality'] = re.compile(re.escape(request.args.get('locality')), re.IGNORECASE)
    if request.args.get('score_above') is not None:
        query['score'] = {'$gt': int(request.args.get('score_above'))}
    if request.args.get('score_below') is not None:
        if 'score' in query:
            query['score'].update({'$lt': int(request.args.get('score_below'))})
    if request.args.get('lat') is not None:
        if request.args.get('lng') is None or request.args.get('dist') is None:
            resp = json.dumps({'status': '401',
                               'error': 'For geospatial searches lat, lng, and dist are all required fields'})
            return resp
        else:
            query['geo'] = {'$nearSphere':
                                {'$geometry':
                                     {'type': "Point",
                                      'coordinates': [ float(request.args.get('lng')), float(request.args.get('lat'))]},
                                 '$maxDistance': int(request.args.get('dist'))}}

    data = db.va.find(query, output).limit(limit)
    
    if data.count() == 0:
        resp = json.dumps({'status': '204', 'message': 'no results returned'})
    else:
        vendor_list = OrderedDict()
        for item in data:
            url = url_for('api_vendor', vendorid=item['slug'])
            vendor_list[str(item['slug'])] = OrderedDict({'url': url,
                                                          'name': item['name'],
                                                          'address': item['address'],
                                                          'city': item['city'],
                                                          'locality': item['locality'],
                                                          'type': item['type']})
            if 'category' in item:
                vendor_list[item['slug']]['category'] = item['category']
            if 'score' in item:
                vendor_list[item['slug']]['score'] = item['score']
            if 'geo' in item:
                vendor_list[item['slug']]['coordinates'] = {'latitude': item['geo']['coordinates'][1],
                                                            'longitude': item['geo']['coordinates'][0]}
            if request.args.get('lat') is not None:
                vendor_list[item['slug']]['dist'] = round(great_circle(float(request.args.get('lng')),
                                                                       float(request.args.get('lat')),
                                                                       item['geo']['coordinates'][0],
                                                                       item['geo']['coordinates'][1]), 2)

        if request.args.get('pretty') == 'true':
            resp = json.dumps(vendor_list, indent=4)
        else:
            resp = json.dumps(vendor_list)
    return resp


@app.route('/vendor/<vendorid>')
@support_jsonp
def api_vendor(vendorid):
    data = db.va.find({'slug': vendorid}, {'name': 1,
                                           'address': 1,
                                           'city': 1,
                                           'locality': 1,
                                           'type': 1,
                                           'category': 1,
                                           'slug': 1,
                                           'score': 1,
                                           'inspections.0': {'$slice': 1},
                                           'geo.coordinates': 1}).sort('inspection.date')
    if data.count() == 1:
        item = data[0]

        vendor = OrderedDict({item['slug']: {'name': item['name'],
                                             'address': item['address'],
                                             'city': item['city'],
                                             'locality': item['locality'],
                                             'type': item['type']}})
        if 'category' in item:
            vendor[item['slug']]['category'] = item['category']
        if 'score' in item:
            vendor[item['slug']]['score'] = item['score']
        if 'geo' in item:
            vendor[item['slug']]['coordinates'] = {'latitude': item['geo']['coordinates'][1],
                                                   'longitude': item['geo']['coordinates'][0]}
        if 'inspections' in item:
            inspection = item['inspections'][0]
            vendor[item['slug']].update({'last_inspection_date': inspection['date'].strftime('%d-%b-%Y'),
                                         'violations': inspection['violations']})

        if request.args.get('pretty') == 'true':
            resp = json.dumps(vendor, indent=4)
        else:
            resp = json.dumps(vendor)

    elif data.count() > 1:
        resp = json.dumps({'status': '300'})
    else:
        resp = json.dumps({'status': '204'})
    return resp


@app.route('/inspections')
@support_jsonp
def api_inspections():

    limit = 1500
    query = {}
    output = {'slug': 1,
              'name': 1,
              'address': 1,
              'city': 1,
              'locality': 1,
              'category': 1,
              'type': 1,
              'score': 1,
              'last_inspection_date': 1,
              'inspections': 1,
              'geo.coordinates': 1}

    if request.args.get('limit') is not None:
        limit = int(request.args.get('limit'))
    if request.args.get('vendorid') is not None:
        query['slug'] = request.args.get('vendorid')
    if request.args.get('before') is not None:
        if request.args.get('after') is not None and datetime.strptime(request.args.get('after'), '%d-%m-%Y') > datetime.strptime(request.args.get('before'), '%d-%m-%Y'):
            resp = json.dumps({'status': '401',
                               'error': 'before date must be greater than after date'})
            return resp
        query['inspections.date'] = {'$lte': datetime.strptime(request.args.get('before'),
                                                               '%d-%m-%Y')}
    if request.args.get('after') is not None:
        if 'inspections.date' in query:
            query['inspections.date'].update({'$gte': datetime.strptime(request.args.get('after'),
                                                                        '%d-%m-%Y')})
        else:
            query['inspections.date'] = {'$gte': datetime.strptime(request.args.get('after'),
                                                                   '%d-%m-%Y')}
    if request.args.get('score_above') is not None:
        query['inspections.score'] = {'$gt': int(request.args.get('score_above'))}
    if request.args.get('score_below') is not None:
        if 'inspections.score' in query:
            query['inspections.score'].update({'$lt': int(request.args.get('score_below'))})
        else:
            query['inspections.score'] = {'$lt': int(request.args.get('score_below'))}
    if request.args.get('violation_text') is not None:
        query['inspections.violations.observation'] = re.compile(re.escape(request.args.get('violation_text')),
                                                                 re.IGNORECASE)
    if request.args.get('violation_code') is not None:
        query['inspections.violations.code'] = re.compile(re.escape(request.args.get('violation_code')),
                                                          re.IGNORECASE)

    score_below = 101 if request.args.get('score_below') is None else int(request.args.get('score_below'))
    score_above = 0 if request.args.get('score_above') is None else int(request.args.get('score_above'))

    data = db.va.find(query, output).limit(limit)

    if data.count() == 0:
        resp = json.dumps({'Status': 204, 'Message': 'No results returned'})
    else:
        vendor_list = OrderedDict()
        for item in data:
            if 'inspections' in item:
                inspections = OrderedDict()
                for index, inspection in enumerate(item['inspections']):
                    if request.args.get('before') is not None and inspection['date'] > datetime.strptime(request.args.get('before'), '%d-%m-%Y'):
                        continue
                    if request.args.get('after') is not None and inspection['date'] < datetime.strptime(request.args.get('after'), '%d-%m-%Y'):
                        continue
                    if request.args.get('score_above') is not None or request.args.get('score_below') is not None:
                        if 'score' not in inspection:
                            continue
                        if not(score_below > int(inspection['score']) > score_above):
                            continue

                    inspections[index] = OrderedDict({'date': inspection['date'].strftime('%d-%b-%Y')})
                    if 'score' in inspection:
                        inspections[index]['score'] = inspection['score']

                    inspections[index]['violations'] = []

                    for violation in inspection['violations']:
                        if request.args.get('violation_text') is not None and request.args.get('violation_text') in violation['observation']:
                            inspections[index]['violations'].append(violation)
                        elif request.args.get('violation_code') is not None and request.args.get('violation_code') in violation['code']:
                            inspections[index]['violations'].append(violation)
                        elif request.args.get('violation_text') is None and request.args.get('violation_code') is None:
                            inspections[index]['violations'].append(violation)

            if inspections is None:
                continue

            vendor_list[item['slug']] = OrderedDict({'name': item['name'],
                                                     'address': item['address'],
                                                     'city': item['city'],
                                                     'locality': item['locality']})

            if 'category' in item:
                vendor_list[item['slug']].update({'category': item['category'],
                                                  'type': item['type']})
            if 'score' in item:
                vendor_list[item['slug']]['score'] = item['score']

            vendor_list[item['slug']].update({'last_inspection_date': item['last_inspection_date'].strftime('%d-%b-%Y'),
                                              'inspections': inspections})

            if 'score' in item:
                vendor_list[item['slug']]['score'] = item['score']
            if 'geo' in item:
                vendor_list[item['slug']]['coordinates'] = {'latitude': item['geo']['coordinates'][1],
                                                            'longitude': item['geo']['coordinates'][0]}
        if request.args.get('pretty') == 'true':
            resp = json.dumps(vendor_list, indent=4)
        else:
            resp = json.dumps(vendor_list)
    return resp


@app.route('/lives/<locality>')
@app.route('/lives/')
def api_lives(locality=""):
    """Request a lives file for given locality
    """
    l = LivesDataExporter(db.va, locality)

    if not l.has_results:
        return json.dumps(
            dict(message="Couldn't find requested locality: " + locality,
                 available=l.available_localities)), 404

    if l.is_stale:
        if l.is_writing:
            print "File is already writing!"
        else:
            l.set_write_lock()
            t = Thread(target=l.write_file)
            t.start()

    return json.dumps(l.metadata), 200


@app.route("/lives-file/<locality>.zip")
def api_lives_file(locality):
    """Retrieve lives file
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), "livesData", locality + ".zip"), "r") as lives_file:
            return Response(lives_file.read(), mimetype="application/octet-stream"), 200
    except IOError:
        return json.dumps(dict(message="File " + locality + ".zip is not available. Please see /lives/" + locality)), \
               404

@app.route('/bulk/')
def show_bulk_list():
    return api_bulk_file(None)

@app.route('/bulk/<filename>')
def api_bulk_file(filename):
    path = os.path.join(os.path.dirname(__file__), 'bulk')

    print filename

    if filename is None:
        files = os.listdir(path)
        file_list = []

        for item in files:
            stats = os.stat(os.path.join(path, item))

            file_list.append({'name': item,
                              'size': '{:,}'.format(stats.st_size)+' bytes',
                              'date': datetime.strftime(datetime.fromtimestamp(stats.st_mtime), '%b %d, %Y')})

        return render_template('bulk_list.html', tree=file_list)

    else:
        with open(os.path.join(path, filename), "r") as bulk_file:
            return Response(bulk_file.read(), mimetype="application/octet-stream"), 200

if __name__ == '__main__':
    app.run()
