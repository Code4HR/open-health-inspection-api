import mongolab
import json
import os
import time
import datetime
from dateutil import parser
import sys
import csv

class Lives:

    dataDir = "livesData"

    def __init__(self, db, locality):
        self.db = db
        self.locality = locality
        self.tmpDir = self.dataDir + "/tmp"
        self.metadataFile = "livesData/" + self.locality + ".json"
        self.data = self.db.va.find({"locality": locality})

        if not os.path.exists(self.dataDir):
            os.makedirs(self.dataDir)
            os.makedirs(self.tmpDir)

    def has_results(self):
        return self.data.count() > 0

    def get_status(self):
        try:
            with open(self.metadataFile, "r") as file:
                metadata = json.load(file)
        except IOError:
            metadata = {
                    "path" : "lives-file/" + self.locality,
                    "available" : False
            }
            self.write_metadata(metadata)

        return metadata

    def write_metadata(self, metadata):
        with open(self.metadataFile, "w") as file:
            json.dump(metadata, file)

    def is_stale(self, metadata):
        try:
            last_written = parser.parse(metadata['last_written'])
            delta = datetime.datetime.utcnow() - last_written
            stale_delta = datetime.timedelta(days=1)
            if delta > stale_delta:
                return True
            else:
                return False
        except (KeyError, ValueError):
            print True

    def write_file(self):
        with open(self.tmpDir + "/businesses.csv", "w") as businesses_csv, open(self.tmpDir + "/inspections.csv", "w") as inspections_csv:
            b_writer = csv.writer(businesses_csv)
            i_writer = csv.writer(inspections_csv)
            for vendor in self.data:
                b_writer.writerow([vendor["_id"],
                                   vendor["name"],
                                   vendor["address"]
                ])

                for inspection in vendor["inspections"]:
                    i_writer.writerow([vendor["_id"],
                                       inspection["date"].strftime("%Y%m%d")])

        print "written"




