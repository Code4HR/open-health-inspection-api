import mongolab
from bson.objectid import ObjectId
import json
from flask import Flask, Response, url_for, request, current_app
from functools import wraps
import re
import logging

app = Flask(__name__)
app.config['TESTING'] = True
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


@app.route('/')
@support_jsonp
def api_root():
    links = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            links.append(rule.rule)
    print json.dumps(links)
    return Response(json.dumps(links), mimetype='application/json')


@app.route('/vendors')
@support_jsonp
def api_vendors():
    data = db.va.find({}, {'name': 1, 'address': 1})
    if data.count() > 0:
        vendor_list = {}
        for item in data:
            url = url_for("api_vendor", vendorid=str(item["_id"]))
            vendor_list[str(item["_id"])] = {'url': url, 'name': item["name"], 'address': item["address"]}

        resp = Response(json.dumps(vendor_list), mimetype='application/json')
    else:
        resp = Response(status=204)

    return resp


@app.route('/vendors/textsearch/<searchstring>')
@support_jsonp
def api_vendor_text_search(searchstring):

    regex = re.compile(re.escape(searchstring), re.IGNORECASE)
    data = db.va.find({ '$or': [{ 'name': regex}, {'address': regex}, {'city': regex}]}, {'name': 1, 'address': 1})

    if data.count() == 0:
        resp = Response(status=204)
    else:
        vendor_list = {}
        for item in data:
            print item["_id"]
            url = url_for('api_vendor', vendorid=item["_id"])
            print url
            vendor_list[str(item["_id"])] = dict({'url': url, 'name': item["name"], 'address': item["address"]})

        resp = Response(json.dumps(vendor_list), mimetype='application/json')

    return resp


@app.route('/vendors/geosearch/<lat>/<lng>/<dist>')
@support_jsonp
def api_vendor_geo_search(lat, lng, dist):
    data = db.va.find({'geo': { '$nearSphere': { '$geometry': { 'type': 'Point', 'coordinates': [ lng, lat]}, '$maxDistance': dist}}},  {'name': 1, 'address': 1})
    return Response('{"message": "route not implemented"}', status=501)


@app.route('/vendor/<vendorid>')
@support_jsonp
def api_vendor(vendorid):

    data = db.va.find({'_id': ObjectId(vendorid)}, {'name': 1, 'address': 1, 'inspections.0': { '$slice': 1}}).sort('inspection.date')

    if data.count() == 1:
        for item in data:
            inspection = item["inspections"][0]
            violations = {}
            for i in range(0,len(inspection["violations"])):
                violations[i] = {'code': inspection["violations"][i]["code"], 'observations': inspection["violations"][i]["observations"]}
            vendor = {str(item["_id"]): {'name': item["name"], 'address': item["address"], 'last_inspection_date': inspection["date"], 'violations': violations}}
        resp = Response(json.dumps(vendor), mimetype='application/json')
    elif data.count() > 1:
        resp = Response(status=300)
    else:
        resp = Response(status=204)

    return resp


@app.route('/inspections/<vendorid>')
@support_jsonp
def api_inspections(vendorid):
    return Response('{"message": "route not implemented"}', status=501)


if __name__ == '__main__':
    app.run()