from sqlalchemy import Column, Integer, Text, Float, PickleType
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from ImageHandler import ImageHandler
import logging


Base = declarative_base()


class DbModel(Base):
    # table name
    __tablename__ = 'dicoms'
    # table structure
    uid = Column(Text, primary_key=True, nullable=False)
    serial_number = Column(Integer, nullable=False)
    modality = Column(Text, nullable=False)
    tube_voltage = Column(Float, nullable=False)
    tube_current = Column(Integer, nullable=False)
    kernel = Column(Text, nullable=False)
    total_collimation = Column(Float, nullable=False)
    slice_thickness = Column(Float, nullable=False)
    instance = Column(Integer, nullable=False)
    integration_result = Column(Text, nullable=False)
    date_time = Column(Text, nullable=False)
    dicom_save = Column(PickleType, nullable=False)
    comment = Column(Text)


class DatabaseHandler(DbModel):
    def __init__(self):
        self.Engine = create_engine(r"sqlite:///./dicom.sqlite3", echo=True)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.Engine)
        self.CurrentSession = self.Session()
        Base.metadata.create_all(self.Engine)
        self.StoredUid = self.CurrentSession.query(DbModel.uid).all()

    def insert_data(self, image: ImageHandler):
        # judge if the image has already been in database
        # pay attention that the return list is a tuple ('uid',)
        if (image.Uid,) in self.StoredUid:
            logging.warning("The image" + image.Uid +
                            "has already been in database." +
                            "Scan mode is " + image.ScanMode + " Skip inserting.")
            return
        _data = DbModel(uid=image.Uid,
                        serial_number=image.SerialNumber,
                        modality=image.Modality,
                        tube_voltage=image.KVP,
                        tube_current=image.Current,
                        kernel=image.Kernel,
                        total_collimation=image.TotalCollimation,
                        slice_thickness=image.SliceThickness,
                        instance=image.Instance,
                        integration_result=image.Image_Median_Filter_Result,
                        date_time=image.DateTime,
                        dicom_save=image)
        # append the list for next time usage
        self.StoredUid.append((image.Uid,))
        self.CurrentSession.add(_data)
        try:
            self.CurrentSession.commit()
        except Exception as e:
            logging.error("There are error during inserting data!")
            logging.error(str(e))
            return


if __name__ == '__main__':
    a = DatabaseHandler()


