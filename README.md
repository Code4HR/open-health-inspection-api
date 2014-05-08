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
<li>name<br />ex. <a href="http://api.ttavenner.com/vendors?name=Havana">api.ttavenner.com/vendors?name=Havana</a></li>
<li>address<br />ex. <a href="http://api.ttavenner.com/vendors?address=Newtown%20Rd">api.ttavenner.com/vendors?address=Newtown%20Rd</a></li>
<li>city<br />ex. <a href="http://api.ttavenner.com/vendors?city=Richmond">api.ttavenner.com/vendors?city=Richmond</a></li>
<li>Geospatial: Vendors near to a certain point can be found by providing a starting latitude &lt;lat&gt;, longitude &lt;lng&gt;, and distance in meters &lt;dist&gt;
<br />ex. <a href="http://api.ttavenner.com/vendors?lat=36&lng=-76&dist=200">api.ttavenner.com/vendors?lat=36&lng=-76&dist=200</a></li>
</ul>
This route returns name, API url, address, city, and coordinates for each vendor. If a geospatial search was performed it will also return the distance from the starting point.</td>
</tr>
<tr>
<td>/vendor/&lt;vendorid&gt;</td>
<td>provides information on a specific vendor identified by &lt;vendorid&gt;</td>
</tr>
<tr>
<td colspan=2>returns name, address, coordinates, and most recent inspection information</td>
</tr>
<td>/inspections/&lt;vendorid&gt;</td>
<td>list all inspections of a given vendor</td>
</tr>
</table>