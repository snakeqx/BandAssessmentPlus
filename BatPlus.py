from DatabaseHandler import *
from DirectoryHandler import DirectoryHandler

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


class GetDicom:
    def __init__(self, path):
        logging.debug("Now gonna get dicoms to store into database")
        self.InputDirectory = DirectoryHandler(path)
        self.Database = DatabaseHandler()
        for _dicom in self.InputDirectory.Dicom_File_Path:
            _image = ImageHandler(_dicom)
            self.Database.insert_data(_image)

if __name__ == '__main__':
    GetDicom(r"/Users/qianxin/Downloads")



