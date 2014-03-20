import mongolab
from bson.objectid import ObjectId
import json
from flask import Flask, Response, url_for
import re

app = Flask(__name__)
app.config['TESTING'] = True
app.debug = True

db = mongolab.connect()


@app.route('/')
def api_root():
    links = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            links.append(rule.rule)
    print json.dumps(links)
    return Response(json.dumps(links), mimetype='application/json')


@app.route('/vendors')
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
def api_vendor_text_search(searchstring):

    regex = re.compile(re.escape(searchstring), re.IGNORECASE)
    data = db.va.find({ 'name': regex}, {'name': 1, 'address': 1})

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


@app.route('/vendors/geosearch/<lat>/<long>/<dist>')
def api_vendor_geo_search(lat, long, dist):
    return Response('{"message": "route not implemented"}', status=501)


@app.route('/vendor/<vendorid>')
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
def api_inspections(vendorid):
    return Response('{"message": "route not implemented"}', status=501)


if __name__ == '__main__':
    app.run()