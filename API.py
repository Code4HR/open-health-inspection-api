import mongolab
import json
import re
from math import radians, cos, sin, atan2, sqrt
from bson.objectid import ObjectId
from flask import Flask, Response, url_for, request, current_app
from functools import wraps
from collections import OrderedDict
from datetime import datetime
from threading import Thread
import os

from livesdataexporter import LivesDataExporter


app = Flask(__name__)
app.debug = True

try:
    db = mongolab.connect()
except ValueError:
    print "Could not connect to database"


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

    if request.args.get('limit') is not None:
        limit = int(request.args.get('limit'))
    if request.args.get('name') is not None:
        query.update({'name': re.compile(re.escape(request.args.get('name')), re.IGNORECASE)})
    if request.args.get('address') is not None:
        query.update({'address': re.compile(re.escape(request.args.get('address')), re.IGNORECASE)})
    if request.args.get('city') is not None:
        query.update({'city': re.compile(re.escape(request.args.get('city')), re.IGNORECASE)})
    if request.args.get('locality') is not None:
        query.update({'locality': re.compile(re.escape(request.args.get('locality')), re.IGNORECASE)})
    if request.args.get('lat') is not None:
        query.update({'geo':
                           {'$nearSphere':
                                {'$geometry':
                                     {'type': "Point",
                                      'coordinates': [ float(request.args.get('lng')), float(request.args.get('lat'))]},
                                 '$maxDistance': int(request.args.get('dist'))}}})
    data = db.va.find(query,
                      {'name': 1,
                       'address': 1,
                       'type': 1,
                       'geo.coordinates': 1}).limit(limit)
    if data.count() == 0:
        resp = json.dumps({'status': '204', 'message': 'no results returned'})
    else:
        vendor_list = OrderedDict()
        for item in data:
            url = url_for('api_vendor', vendorid=str(item['_id']))
            vendor_list[str(item['_id'])] = OrderedDict({'url': url,
                                             'name': item['name'],
                                             'address': item['address'],
                                             'type': item['type']})
            if 'geo' in item:
                vendor_list[str(item['_id'])]['coordinates'] = {'latitude': item['geo']['coordinates'][1],
                                                                'longitude': item['geo']['coordinates'][0]}
            if request.args.get('lat') is not None:
                vendor_list[str(item['_id'])]['dist'] = round(great_circle(float(request.args.get('lng')),
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
    data = db.va.find({'_id': ObjectId(vendorid)}, {'name': 1,
                                                    'address': 1,
                                                    'type': 1,
                                                    'inspections.0': {'$slice': 1},
                                                    'geo.coordinates': 1}).sort('inspection.date')
    if data.count() == 1:
        item = data[0]

        vendor = OrderedDict({str(item['_id']): {'name': item['name'],
                                                 'address': item['address'],
                                                 'type': item['type'],
                                                 'coordinates': {
                                                     'latitude': item['geo']['coordinates'][1],
                                                     'longitude': item['geo']['coordinates'][0]}}})

        if item['inspections']:
            inspection = item['inspections'][0]
            vendor[str(item['_id'])].update({'last_inspection_date': inspection['date'].strftime('%d-%b-%Y'),
                                             'violations': inspection['violations']})

        resp = json.dumps(vendor)
    elif data.count() > 1:
        resp = json.dumps({'status': '300'})
    else:
        resp = json.dumps({'status': '204'})
    return resp


@app.route('/inspections')
@support_jsonp
def api_inspections():

    limit = 500
    query = {}

    if request.args.get('vendorid') is not None:
        query.update({'_id': ObjectId(request.args.get('vendorid'))})
    if request.args.get('before') is not None:
        query.update({'inspections.date': {'$lte': datetime.strptime(request.args.get('before'), '%d-%m-%Y')}})
    if request.args.get('after') is not None:
        query.update({'inspections.date': {'$gte': datetime.strptime(request.args.get('after'), '%d-%m-%Y')}})
    print query
    data = db.va.find(query, {'name': 1,
                              'address': 1,
                              'type': 1,
                              'last_inspection_date': 1,
                              'inspections': 1,
                              'geo.coordinates': 1}).limit(limit)
    if data.count() > 0:
        vendor_list = OrderedDict()
        for item in data:
            if 'inspections' in item:
                inspections = OrderedDict()
                for inspection in item['inspections']:
                    inspections[len(inspections)] = OrderedDict({'date': inspection['date'].strftime('%d-%b-%Y'),
                                                                 'violations': inspection['violations']})

            vendor_list[str(item["_id"])] = OrderedDict({'name': item['name'],
                                                         'address': item['address'],
                                                         'type': item['type']})
            if item['last_inspection_date'] is not None:
                vendor_list[str(item['_id'])].update({'last_inspection_date': item['last_inspection_date'].strftime('%d-%b-%Y')})
            if inspections:
                vendor_list[str(item['_id'])].update({'inspections': inspections})
            if 'geo' in item:
                vendor_list[str(item['_id'])].update({'coordinates': { 'latitude': item['geo']['coordinates'][1],
                                                                       'longitude': item['geo']['coordinates'][0]}})
        if request.args.get('pretty') == 'true':
            resp = json.dumps(vendor_list, indent=4)
        else:
            resp = json.dumps(vendor_list)


@app.route('/lives/<locality>')
def api_lives(locality):
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


if __name__ == '__main__':
    app.run()
