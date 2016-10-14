open-health-inspection-api
==========================

The API for the Open Health Inspection app.

This API provides an interface to a MongoDB containing data from the Virginia Department of Health on inspections of food service facilities. Data is returned via JSON. To get the current list of routes make a call to the root URL.

It can be implemented using Flask with [WSGI on Apache/Nginx](http://flask.pocoo.org/docs/deploying/mod_wsgi/), or very simply on [Heroku with Gunicorn](https://devcenter.heroku.com/articles/getting-started-with-python).

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
<li><b>Name</b><br />ex. <a href="https://ohi-api.code4hr.org/vendors?name=Havana">ohi-api.code4hr.org/vendors?name=Havana</a></li>
<li><b>Address</b><br />ex. <a href="https://ohi-api.code4hr.org/vendors?address=Newtown%20Rd">api.openhealthinspection.com/vendors?address=Newtown Rd</a></li>
<li><b>City</b><br />ex. <a href="https://ohi-api.code4hr.org/vendors?city=Richmond">ohi-api.code4hr.org/vendors?city=Richmond</a></li>
<li><b>Locality</b>: The health district in which the vendor is located<br />ex. <a href="https://ohi-api.code4hr.org/vendors?locality=Arlington">ohi-api.code4hr.org/vendors?locality=Arlington</a></li>
<li><b>Category</b>: A broad categorization<br />ex. <a href="https://ohi-api.code4hr.org/vendors?category=Restaurant">ohi-api.code4hr.org/vendors?category=Restaurant</a></li>
<li><b>type</b>: A more granular breakdown<br />ex. <a href="https://ohi-api.code4hr.org/vendors?type=Mobile%20Food%20Unit">ohi-api.code4hr.org/vendors?type=Mobile Food Unit</a></li>
<li><b>Score Above Number</b><br />ex. <a href="https://ohi-api.code4hr.org/vendors?score_above=70">ohi-api.code4hr.org/vendors?score_above=70</a></li>
<li><b>Score Below Number</b><br />ex. <a href="https://ohi-api.code4hr.org/vendors?score_below=90">ohi-api.code4hr.org/vendors?score_below=90</a></li>
<li><b>Limit</b><br />Sets a limit on the number of results returned. The default is 1,500.</li>
<li><b>Pretty</b><br />Formats the results for easier reading in a browser. values are 'true' and 'false'. Default is false.</li>
<li><b>Geospatial</b>: Vendors near to a certain point can be found by providing a starting latitude &lt;lat&gt;, longitude &lt;lng&gt;, and distance in meters &lt;dist&gt;
<br />ex. <a href="https://ohi-api.code4hr.org/vendors?lat=36.6337272&lng=-81.7837303&dist=2000">ohi-api.code4hr.org/vendors?lat=36.6337272&lng=-81.7837303&dist=2000</a></li>
</ul>
This route returns name, API url, address, city, locality, category, type, score, and coordinates for each vendor. If a geospatial search was performed it will also return the distance from the starting point.</td>
</tr>
<tr>
<td>/vendor/&lt;vendorid&gt;</td>
<td>provides information on a specific vendor identified by &lt;vendorid&gt;</td>
</tr>
<tr>
<td colspan=2>returns name, address, city, category, type, score, coordinates, and most recent inspection information</td>
</tr>
<td>/inspections</td>
<td>list all inspections of a given vendor</td>
</tr>
<tr>
<td colspan=2>
Can be searched by adding any or all of the following parameters:
<ul>
<li><b>vendorid</b><br />ex. <a href="https://ohi-api.code4hr.org/inspections?vendorid=Backyard-Grillers-1078-Lee-Syd-Moore-Drive-Scottsburg-Virginia-24589">ohi-api.code4hr.org/inspections?vendorid=Backyard-Grillers-1078-Lee-Syd-Moore-Drive-Scottsburg-Virginia-24589</a></li>
<li><b>Inspections Performed Before Date</b>: Specified in the form DD-MM-YYYY<br />ex. <a href="https://ohi-api.code4hr.org/inspections?before=15-09-2013">ohi-api.code4hr.org/inspections?before=15-09-2013</a></li>
<li><b>Inspections Performed After Date</b>: Specified in the form DD-MM-YYYY<br />ex. <a href="https://ohi-api.code4hr.org/inspections?after=29-02-2012">ohi-api.code4hr.org/inspections?after=29-02-2012</a></li>
<li><b>Violation Text</b>: The inspector's description of the violation contains this text<br />ex. <a href="https://ohi-api.code4hr.org/inspections?violation_text=candle">ohi-api.code4hr.org/inspections?violation_text=candle</a></li>
<li><b>Violation Code</b>: The municipal code of the violation<br />ex. <a href="https://ohi-api.code4hr.org/inspections?violation_code=303">ohi-api.code4hr.org/inspections?violation_code=303</a></li>
<li><b>Score Above Number</b><br />ex. <a href="https://ohi-api.code4hr.org/inspections?score_above=70">ohi-api.code4hr.org/inspections?score_above=70</a></li>
<li><b>Score Below Number</b><br />ex. <a href="https://ohi-api.code4hr.org/inspections?score_below=90">ohi-api.code4hr.org/inspections?score_below=90</a></li>
</ul>
This route returns name, address, city, locality, category, type, score, last inspection date, and coordinates for each vendor. It will also return any inspections that met the search criteria.
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
<tr>
<td>/bulk/</td>
</tr>
<tr>
<td colspan=2>Provides bulk downloads of all data in the inspection database. Currently the data is only provided in JSON files but other formats will likely be available in the future. The data is currently updated weekly following a run of the <a href="https://github.com/c4hrva/open-health-inspection-scraper">Scraper</a>. The files are produced using the mongoexport command line tool.</td>
</tr>
</table>
