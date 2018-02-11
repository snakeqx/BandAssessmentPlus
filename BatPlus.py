from bat.DatabaseHandler import SQL3Handler
from bat.DirectoryHandler import DirectoryHandler
from bat.ImageHandler import ImageHandler
import logging

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


if __name__ == '__main__':
    files = DirectoryHandler(r'./test')
    for _file in files.Dicom_File_Path:
        _image = ImageHandler(_file)
        if _image.isImageComplete:
            _image.save_image()
            _image.evaluate_iq(10,2)
            SQL3Handler(_image).insert_data()


