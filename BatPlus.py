import logging
from DirectoryHandler import DirectoryHandler
from ImageHandler import ImageHandler

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
    input_directory = DirectoryHandler(r"/Users/qianxin/Downloads")
    for x in DirectoryHandler.Dicom_File_Path:
        a = ImageHandler(x)
        a.rescale_image((1, 100))
        a.save_image()

