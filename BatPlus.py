import os
import logging
from DirectoryHandler import DirectoryHandler
from DicomHandler import DicomHandler
from DatabaseHandler import DatabaseHandler

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


if __name__ == '__main__':
    input_directory = DirectoryHandler(r"./test/")
    b = DicomHandler(input_directory.Dicom_File_Path[0])
    b.show_image()
