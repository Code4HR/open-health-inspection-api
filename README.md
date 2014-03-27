open-health-inspection-api
==========================

The API for the Open Health Inspection app.

This API provides an interface to a MongoDB containing data from the Virginia Department of Health on inspections of food service facilities. Data is returned via JSON. To get the current list of routes make a call to the root URL.

It can be implemented very simply using Flask with [WSGI on Apache](http://flask.pocoo.org/docs/deploying/mod_wsgi/), or very simply on [Heroku with Gunicorn](https://devcenter.heroku.com/articles/getting-started-with-python).

Routes implemented:

* /vendors - provides a complete list of food service vendors
    * returns name, API url, and address for each vendor
* /vendors/textsearch/&lt;searchstring&gt; - Allows searching of the vendor database by string, currently only searches name
    * returns name, API url, and address for each vendor
* /vendor/&lt;vendorid&gt; - provides information on a specific vendor identified by <vendorid&gt;
    * returns name, address, and most recent inspection information
* /inspections/&lt;vendorid&gt; - list all inspections of a given vendor

Routes planned:

* /vendors/geosearch/&lt;lat&gt;/&lt;long&gt;/&lt;dist&gt; - return all vendors with &lt;dist&gt; distance of &lt;lat&gt; latitude and &lt;long&gt; longitude
