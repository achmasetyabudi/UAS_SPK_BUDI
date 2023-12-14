from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class BanMotor(Base):
    __tablename__ = "pemilihan_banmotor"
    no = Column(Integer, primary_key=True)
    merek = Column(String)
    jenis = Column(String)
    ukuran = Column(String)
    tekanan = Column(String)
    harga = Column(String)
    

    def __repr__(self):
        return f"BanMotor(merek={self.merek!r}, jenis={self.jenis!r}, ukuran={self.ukuran!r}, tekanan={self.tekanan!r}, harga={self.harga!r})"
