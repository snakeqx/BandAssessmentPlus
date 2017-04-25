import logging
import sqlite3
import os


class DatabaseHandler:
    """
    Create a Sqlite3 handler to store the data.
    for the integration result, it will be converted to string and then store into database.
    So when extracting data, the string should be converted back to list or numpy array before doing calculation
    """
    Database_Name = "BandAssessment.sqlite3.db"

    def __init__(self, name, kvp, current, kernel, total_col, slice_thick,
                 instance, integration, date, dicom_store, comment=None):
        self.Dicom_Station_Name = name
        self.Dicom_KVP = kvp
        self.Dicom_Current = current
        self.Dicom_Kernel = kernel
        self.Dicom_Total_Collimation = total_col
        self.Dicom_Slice_Thickness = slice_thick
        self.Dicom_Instance = instance
        self.Integration_Result = integration
        self.Dicom_Date = date
        self.Dicom_Store = dicom_store
        self.Comment = comment
        if not os.path.isfile(self.Database_Name):
            self.create_database()

    def create_database(self):
        try:
            con = sqlite3.connect(self.Database_Name)
        except sqlite3.Error as e:
            logging.debug(str(e))
        sql_cursor = con.cursor()
        sql_string = '''create table BandAssessment(
                           uid INTEGER PRIMARY KEY AUTOINCREMENT,
                           serial_number INTEGER NOT NULL,
                           tube_voltage REAL NOT NULL,
                           tube_current INTEGER NOT NULL,
                           kernel TEXT,
                           total_collimation REAL NOT NULL,
                           slice_thickness REAL NOT NULL,
                           instance INTEGER NOT NULL,
                           integration_result TEXT NOT NULL,
                           date TEXT NOT NULL,
                           dicom_file BLOB NOT NULL,
                           comment TEXT);'''
        try:
            sql_cursor.execute(sql_string)
            logging.info(r"Database and Table created")
        except sqlite3.Error as e:
            logging.debug(str(e))
        con.close()

    def insert_data(self):
        try:
            con = sqlite3.connect(self.Database_Name)
        except sqlite3.Error as e:
            logging.debug(str(e))
            return
        # convert numpy into string to store in sqlite3
        int_result_string = ';'.join([str(x) for x in self.Integration_Result])
        # set up for store in sql
        sql_cursor = con.cursor()
        sql_string = r"insert into BandAssessment values (?,?,?,?,?,?,?,?,?,?,?,?);"
        try:
            sql_cursor.execute(sql_string,
                               (None, self.Dicom_Station_Name, self.Dicom_KVP, self.Dicom_Current, self.Dicom_Kernel,
                                self.Dicom_Total_Collimation, self.Dicom_Slice_Thickness, self.Dicom_Instance,
                                int_result_string, self.Dicom_Date, self.Dicom_Store, self.Comment))
        except sqlite3.Error as e:
            logging.error(str(e))
            con.close()
            return
        con.commit()
        logging.info(r"Insert record done.")
        con.close()


if __name__ == '__main__':
    print("please do not use it individually unless of debugging.")
    # below codes for debug
    # define the logging config, output in file
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename=r'./log/DirectoryHandler.log',
                        filemode='w')
    # define a stream that will show log level > Warning on screen also
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

