open-health-inspection-api
==========================

The API for the Open Health Inspection app.

This API provides an interface to a MongoDB containing data from the Virginia Department of Health on inspections of food service facilities. Data is returned via JSON. To get the current list of routes make a call to the root URL.

It can be implemented using Flask with [WSGI on Apache](http://flask.pocoo.org/docs/deploying/mod_wsgi/), or very simply on [Heroku with Gunicorn](https://devcenter.heroku.com/articles/getting-started-with-python).

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
<td colspan=2>
Can be searched by adding any or all of the following parameters:
<ul>
<li>name<br />ex. <a href="http://api.openhealthinspection.com/vendors?name=Havana">api.openhealthinspection.com/vendors?name=Havana</a></li>
<li>address<br />ex. <a href="http://api.openhealthinspection.com/vendors?address=Newtown%20Rd">api.openhealthinspection.com/vendors?address=Newtown%20Rd</a></li>
<li>city<br />ex. <a href="http://api.openhealthinspection.com/vendors?city=Richmond">api.openhealthinspection.com/vendors?city=Richmond</a></li>
<li>locality: A broader geographic boundary than city. Often this relates to county<br />ex. <a href="http://api.openhealthinspection.com/vendors?locality=Arlington">api.openhealthinspection.com/vendors?locality=Arlington</a></li>
<li>category: A broad categorization<br />ex. <a href="http://api.openhealthinspection.com/vendors?category=Restaurant">api.openhealthinspection.com/vendors?category=Restaurant</a></li>
<li>type: A more granular breakdown<br />ex. <a href="http://api.openhealthinspection.com/vendors?type=Mobile%20Food%20Unit">api.openhealthinspection.com/vendors?type=Mobile Food Unit</a></li>
<li>limit<br />Sets a limit on the number of results returned. The default is 1,500.</li>
<li>pretty<br />Formats the results for easier reading in a browser. values are 'true' and 'false'. Default is false.</li>
<li>Geospatial: Vendors near to a certain point can be found by providing a starting latitude &lt;lat&gt;, longitude &lt;lng&gt;, and distance in meters &lt;dist&gt;
<br />ex. <a href="http://api.openhealthinspection.com/vendors?lat=36&lng=-76&dist=200">api.openhealthinspection.com/vendors?lat=36&lng=-76&dist=200</a></li>
</ul>
This route returns name, API url, address, city, category, type, and coordinates for each vendor. If a geospatial search was performed it will also return the distance from the starting point.</td>
</tr>
<tr>
<td>/vendor/&lt;vendorid&gt;</td>
<td>provides information on a specific vendor identified by &lt;vendorid&gt;</td>
</tr>
<tr>
<td colspan=2>returns name, address, city, category, type, coordinates, and most recent inspection information</td>
</tr>
<td>/inspections</td>
<td>list all inspections of a given vendor</td>
</tr>
<tr>
<td colspan=2>
Can be searched by adding any or all of the following parameters:
<ul>
<li>vendorid<br />ex. <a href="http://api.openhealthinspection.com/inspections?vendorid=53532d309047231f00c6434f">api.openhealthinspection.com/inspections?vendorid=53532d309047231f00c6434f</a></li>
<li>Inspections Performed Before Date: Specified in the form DD-MM-YYYY<br />ex. <a href="http://api.openhealthinspection.com/inspections?before=15-09-2013">api.openhealthinspection.com/inspections?before=15-09-2013</a></li>
<li>Inspections Performed After Date: Specified in the form DD-MM-YYYY<br />ex. <a href="http://api.openhealthinspection.com/inspections?after=29-02-2012">api.openhealthinspection.com/inspections?after=29-02-2012</a></li>
<li>Violation Text: The inspector's description of the violation contains this text<br />ex. <a href="http://api.openhealthinspection.com/inspections?violation_text=candle">api.openhealthinspection.com/inspections?violation_text=candle</a></li>
<li>Violation Code: The municipal code of the violation<br />ex. <a href="http://api.openhealthinspection.com/inspections?violation_code=303">api.openhealthinspection.com/inspections?violation_code=303</a></li>
</ul>
</td>
</tr>
<tr>
<td>/lives/&lt;locality&gt;</td>
</tr>
<tr>
<td colspan=2>request a file in LIVES format for a given locality. See <a href="http://www.yelp.com/healthscores">yelp.com/healthscores</a> for format.</td>
</tr>
<tr>
<td>/lives-file/&lt;locality&gt;.zip</td>
</tr>
<tr>
<td colspan=2>After a file is requested through /lives/, it will be available at this URL.</td>
</tr>
</table>
