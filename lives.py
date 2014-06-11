import json
import os
import datetime
from dateutil import parser
import csv
import zipfile


class Lives:

    dataDir = "livesData"

    def __init__(self, db, locality):
        self.db = db
        self.locality = locality
        self.tmp_dir = Lives.dataDir + "/tmp"
        self.metadata_file = Lives.dataDir + "/" + self.locality + ".json"
        self.data = self.db.va.find({"locality": locality})

        if not os.path.exists(Lives.dataDir):
            os.makedirs(Lives.dataDir)
            os.makedirs(self.tmp_dir)

        self.metadata = self.__fetch_metadata()

    @property
    def has_results(self):
        return self.data.count() > 0

    @property
    def is_stale(self):
        try:
            last_written = parser.parse(self.metadata['last_written'])
            delta = datetime.datetime.utcnow() - last_written
            stale_delta = datetime.timedelta(days=1)
            if delta > stale_delta:
                return True
            else:
                return False
        except (KeyError, ValueError):
            # if last_written isn't set, it's stale
            return True

    def __fetch_metadata(self):
        try:
            with open(self.metadata_file, "r") as file:
                metadata = json.load(file)
        except IOError:
            # couldn't read it, so write it
            metadata = dict(path="lives-file/" + self.locality, available=False)
            self.__update_metadata(metadata)

        return metadata

    def __update_metadata(self, metadata):
        with open(self.metadata_file, "w") as file:
            json.dump(metadata, file)

    @property
    def is_writing(self):
        try:
            status = self.metadata['status']
        except KeyError:
            status = None

        return status == "writing"

    def set_write_lock(self):
        self.metadata['status'] = "writing"
        self.__update_metadata(self.metadata)

    def write_file(self):
        businesses_path = self.tmp_dir + "/" + self.locality + "_businesses.csv"
        inspections_path = self.tmp_dir + "/" + self.locality + "_inspections.csv"

        with open(businesses_path, "w") as businesses_csv, \
                open(inspections_path, "w") as inspections_csv:
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

        with zipfile.ZipFile(Lives.dataDir + "/" + self.locality + ".zip", 'w') as zip:
            zip.write(businesses_path, self.locality + "/businesses.csv")
            zip.write(inspections_path, self.locality + "/inspections.csv")

        os.remove(businesses_path)
        os.remove(inspections_path)

        self.metadata["status"] = "complete"
        self.metadata["last_written"] = datetime.datetime.utcnow().strftime("%c")
        self.metadata["available"] = True
        self.__update_metadata(self.metadata)

        print "Done writing " + self.locality + ".zip"
