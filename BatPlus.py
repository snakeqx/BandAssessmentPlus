import os
import logging
from DirectoryHandler import DirectoryHandler
from DicomHandler import DicomHandler
from DatabaseHandler import DatabaseHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=r'./BatPlus.log',
                    filemode='w')
# define a stream that will show log level > Warning on screen also
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


def main():
    pass


if __name__ == '__main__':
    input_directory = DirectoryHandler(r"./test/")
    for x in DirectoryHandler.Dicom_File_Path:
        a = DicomHandler(x)
        if a.isShowImgReady:
            a.show_image()
            DatabaseHandler(a.Dicom_Station_Name,
                            a.Dicom_KVP,
                            a.Dicom_Current,
                            a.Dicom_Kernel,
                            a.Dicom_Total_Collimation,
                            a.Dicom_Slice_Thickness,
                            a.Dicom_Instance,
                            a.Image_Integration_Result,
                            a.Dicom_Date).insert_data()
