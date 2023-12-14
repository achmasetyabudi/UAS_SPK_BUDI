from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BanMotor(Base):
    __tablename__ = "pemilihan_banmotor"
    no = Column(Integer, primary_key=True)
    jenis = Column(String(255))
    ukuran = Column(String(255))
    harga = Column(String(255))
    tekanan = Column(String(255))

    def __init__(self, jenis, ukuran, baterai, harga, tekanan):
        self.jenis = jenis
        self.ukuran = ukuran
        self.harga = harga
        self.tekanan = tekanan

    def calculate_score(self, dev_scale):
        score = 0
        score += self.jenis * dev_scale['jenis']
        score += self.ukuran * dev_scale['ukuran']
        score -= self.harga * dev_scale['harga']
        score += self.tekanan * dev_scale['tekanan']
        
        return score

    def __repr__(self):
        return f"BanMotor(id={self.id!r}, jenis={self.jenis!r}, ukuran={self.ukuran!r}, harga={self.harga!r}, tekanan={self.ukuranlayar!r})"
