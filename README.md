open-health-inspection-api
==========================

The API for the Open Health Inspection app.

This API provides an interface to a MongoDB containing data from the Virginia Department of Health on inspections of food service facilities. Data is returned via JSON. To get the current list of routes make a call to the root URL.

It can be implemented very simply using Flask with [WSGI on Apache](http://flask.pocoo.org/docs/deploying/mod_wsgi/), or very simply on [Heroku with Gunicorn](https://devcenter.heroku.com/articles/getting-started-with-python).

#####Routes implemented
<table>
<tr>
<th>Route</th>
<th>Description</th>
</tr>
<td>/vendors</td>
<td>provides a complete list of food service vendors</td>
</tr>
<tr>
<td colspan=2>returns name, API url, address, and coordinates for each vendor</td>
</tr>
<tr>
<td>/vendors/textsearch/&lt;searchstring&gt;</td>
<td>Allows searching of the vendor database by string. Search name, address, and city</td>
</tr>
<tr>
<td colspan=2>returns name, API url, address, and coordinates for each vendor</td>
</tr>
<tr>
<td>/vendors/geosearch/&lt;lng&gt;/&lt;lat&gt;/&lt;dist&gt;</td>
<td>return all vendors within &lt;dist&gt; distance (in meters) of &lt;lng&gt; longitude and &lt;lat&gt; latitude</td>
</tr>
<tr>
<td colspan=2>returns name, API url, address, and coordinates for each vendor</td>
</tr>
<tr>
<td>/vendor/&lt;vendorid&gt;</td>
<td>provides information on a specific vendor identified by <vendorid&gt;</td>
</tr>
<tr>
<td colspan=2>returns name, address, coordinates, and most recent inspection information</td>
</tr>
<td>/inspections/&lt;vendorid&gt;</td>
<td>list all inspections of a given vendor</td>
</tr>
</table>

#####Routes planned
???


