import json
import os
from datetime import datetime, timedelta
from dateutil import parser
import csv
import zipfile
import pymongo


class LivesDataExporter:

    def __init__(self, collection, locality, data_dir=os.path.join(os.path.dirname(__file__), "livesData")):
        """
        :type self: LivesDataExporter
        :param collection: pymongo.collection.Collection
        :param locality: str
        :param data_dir: str
        """
        assert isinstance(collection, pymongo.collection.Collection)
        self.collection = collection
        assert isinstance(locality, str)
        self.locality = locality
        assert isinstance(data_dir, str)
        self.data_dir = data_dir

        self.tmp_dir = os.path.join(data_dir, "tmp")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            os.makedirs(self.tmp_dir)

        self.metadata_file = os.path.join(data_dir, self.locality + ".json")
        self.metadata = None
        self.__load_metadata()

        self.results = None

    @property
    def data_dir(self):
        """get path to data export directory
        :rtype : str
        """
        return self.data_dir

    def __load_metadata(self):
        """loads metadata about the status of this export from filesystem
        saves a new metadata file if none exists
        :rtype : None
        """
        try:
            with open(self.metadata_file, "r") as metadata_file:
                metadata = json.load(metadata_file)
        except IOError:
            # couldn't read it, so write it
            metadata = dict(path="lives-file/" + self.locality, available=False)
            self.save_metadata()

        self.metadata = metadata
        return None

    @property
    def has_results(self):
        """tell us if the provided locality has any data to export
        :rtype : bool
        """
        return self.collection.find_one({"locality": self.locality}) is not None

    @property
    def is_stale(self):
        """tell us if the exported data was exported along enough ago to be considered stale
        currently, 1 day old is stale
        :rtype : bool
        """
        try:
            last_written = parser.parse(self.metadata["last_written"])
            delta = datetime.utcnow() - last_written
            stale_delta = timedelta(days=1)
            if delta > stale_delta:
                return True
            else:
                return False
        except (KeyError, ValueError):
            # if last_written isn't set, it's stale
            return True

    @property
    def is_writing(self):
        """tell us if the export for this local is currently writing
        :rtype : bool
        """
        try:
            status = self.metadata["status"]
        except KeyError:
            status = None

        return status == "writing"

    def set_write_lock(self):
        """set export status to 'writing'
        :rtype : None
        """
        self.metadata["status"] = "writing"
        self.save_metadata()
        return None

    def save_metadata(self):
        """persist metatdata about file export
        :rtype : None
        """
        with open(self.metadata_file, "w") as metadata_file:
            json.dump(self.metadata, metadata_file)

        return None

    def load_results(self):
        """load results for locality
        :rtype : pymongo.cursor
        """
        return self.collection.find({"locality": self.locality})

    def write_file(self):
        """write the exported data to filesystem
        :rtype : None
        """
        businesses_path_tmp = os.path.join(self.tmp_dir, self.locality + "_businesses.csv")
        inspections_path_tmp = os.path.join(self.tmp_dir, self.locality + "_inspections.csv")
        with open(businesses_path_tmp, "w") as businesses_csv, \
                open(inspections_path_tmp, "w") as inspections_csv:
            b_writer = csv.writer(businesses_csv)
            i_writer = csv.writer(inspections_csv)
            results = self.load_results()
            for vendor in results:
                b_writer.writerow([vendor["_id"],
                                   vendor["name"],
                                   vendor["address"]
                ])

                for inspection in vendor["inspections"]:
                    i_writer.writerow([vendor["_id"],
                                       inspection["date"].strftime("%Y%m%d")])

        zip_path = os.path.join(self.data_dir, self.locality + ".zip")
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(businesses_path_tmp, os.path.join(self.locality, "businesses.csv"))
            zip_file.write(inspections_path_tmp, os.path.join(self.locality, "inspections.csv"))

        # delete tmp files
        os.remove(businesses_path_tmp)
        os.remove(inspections_path_tmp)

        #update metadata
        self.metadata["status"] = "complete"
        self.metadata["last_written"] = datetime.utcnow().strftime("%c")
        self.metadata["available"] = True
        self.save_metadata()

        print "Done writing " + self.locality + ".zip"
        return None

    @staticmethod
    def format_locality_string(locality):
        print locality
