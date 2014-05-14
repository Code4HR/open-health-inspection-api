import mongolab
import json
import re
#import csv
#import zipfile
from math import radians, cos, sin, atan2, sqrt
from bson.objectid import ObjectId
from flask import Flask, Response, url_for, request, current_app
from functools import wraps
from collections import OrderedDict


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
        print vendor_list

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
        inspection = item['inspections'][0]
        vendor = {str(item['_id']): {'name': item['name'],
                                     'address': item['address'],
                                     'type': item['type'],
                                     'last_inspection_date': inspection['date'],
                                     'violations': inspection["violations"],
                                     'coordinates': {
                                                 'latitude': item['geo']['coordinates'][0],
                                                 'longitude': item['geo']['coordinates'][1]}}}
        resp = json.dumps(vendor)
    elif data.count() > 1:
        resp = json.dumps({'status': '300'})
    else:
        resp = json.dumps({'status': '204'})
    return resp


@app.route('/inspections/<vendorid>')
@support_jsonp
def api_inspections(vendorid):
    data = db.va.find({'_id': ObjectId(vendorid)}, {'name': 1,
                                                    'address': 1,
                                                    'type': 1,
                                                    'last_inspection_date': 1,
                                                    'inspections': 1,
                                                    'geo.coordinates': 1})
    if data.count() == 1:
        vendor = {str(data[0]["_id"]): {'name': data[0]['name'],
                                        'address': data[0]['address'],
                                        'type': data[0]['type'],
                                        'last_inspection_date': data[0]['last_inspection_date'],
                                        'inspections': data[0]['inspections'],
                                        'coordinates': {
                                                 'latitude': data[0]['geo']['coordinates'][0],
                                                 'longitude': data[0]['geo']['coordinates'][1]}}}
        resp = json.dumps(vendor)
    elif data.count() > 1:
        resp = json.dumps({'status': '300'})
    else:
        resp = json.dumps({'status': '204'})
    return resp



@app.route('/lives')
def api_lives():
    data = db.va.find({}, {'name': 1,
                           'address': 1,
                           'city': 1,
                           'geo': 1,
                           'inspections': 1})

    businesses_csv = open('businesses.csv', 'wb')
    inspections_csv = open('inspections.csv', 'wb')
    violations_csv = open('violations.csv', 'wb')
    with zipfile.ZipFile('lives.zip', 'w') as lives_zip:
        vendors = []
        inspections = []
        violations = []
        for vendor in data:
            vendors.append([str(vendor["_id"]),
                      vendor['_id'],
                      vendor['_id'],
                      vendor['_id'],
                     'VA',
                     '',
                     vendor['geo']['coordinates'][0],
                     vendor['geo']['coordinates'][0],
                     ''])
            for inspection in vendor['inspections']:
                inspections.append([str(vendor['_id']),
                                    '',
                                    inspection['date'],
                                    '',
                                    inspections['type']])
                for violation in inspection['violations']:
                    violations.append([str(vendor['_id']),
                                       inspection['date'],
                                       violation['code'][0],
                                       violation['observation']])
    businesses_csv.writerows(vendors)
    inspections_csv.writerows(inspections)
    violations_csv.writerows(violations)


if __name__ == '__main__':
    app.run()