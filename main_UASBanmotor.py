import sys
from colorama import Fore, Style
from models import Base, BanMotor
from engine import engine
from tabulate import tabulate

from sqlalchemy import select
from sqlalchemy.orm import Session
from settings import DEV_SCALE

session = Session(engine)


def create_table():
    Base.metadata.create_all(engine)
    print(f'{Fore.GREEN}[Success]: {Style.RESET_ALL}Database has created!')


def review_data():
    query = select(BanMotor)
    for ban_motor in session.execute(query).scalars():
        print(ban_motor)


class BaseMethod:
    def __init__(self):
        # 1-5
        self.raw_weight = {'jenis': 4, 'ukuran': 3, 'harga': 5, 'tekanan': 4}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(BanMotor.no, BanMotor.jenis, BanMotor.ukuran, BanMotor.harga, BanMotor.tekanan)
        result = session.execute(query).fetchall()
        return [{'no': BanMotor.no, 'jenis': BanMotor.jenis, 'ukuran': BanMotor.ukuran, 'harga': BanMotor.harga,
                 'tekanan': BanMotor.tekanan} for BanMotor in result]

    @property
    def normalized_data(self):
        jenis_values = []
        ukuran_values = []
        harga_values = []
        tekanan_values = []

        for data in self.data:
            # jenis
            jenis_spec = data['jenis']
            jenis_numeric_values = [int(
                value.split()[0]) for value in jenis_spec.split() if value.split()[0].isdigit()]
            max_jenis_value = max(
                jenis_numeric_values) if jenis_numeric_values else 1
            jenis_values.append(max_jenis_value)

            # ukuran
            ukuran_numeric = float(data['ukuran'].split('/')[0])
            ukuran_values.append(ukuran_numeric)

            # harga
            harga_numeric = float(''.join(filter(str.isdigit, data['harga'])))
            harga_values.append(harga_numeric)

            # tekanan
            tekanan_numeric = float(''.join(filter(str.isdigit, data['tekanan'])))
            tekanan_values.append(tekanan_numeric)

        max_jenis = float(max(jenis_values)) if max(jenis_values) != 0 else 1  # Avoid division by zero
        max_ukuran = float(max(ukuran_values)) if max(ukuran_values) != 0 else 1
        max_tekanan = float(max(tekanan_values)) if max(tekanan_values) != 0 else 1

        return [
            {'no': data['no'],
            'jenis': jenis_normalized / max_jenis,
            'ukuran': ukuran_numeric / max_ukuran,
            'harga': float(min(harga_values)) / harga_numeric if harga_numeric != 0 else 0,
            'tekanan': tekanan_numeric / max_tekanan}
            for data, jenis_normalized, ukuran_numeric, harga_numeric, tekanan_numeric in zip(
                self.data, jenis_values, ukuran_values, harga_values, tekanan_values
            )
        ]

class WeightedProduct(BaseMethod):
    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'no': row['no'],
                'produk': row['jenis'] ** self.weight['jenis'] *
                          row['ukuran'] ** self.weight['ukuran'] *
                          row['harga'] ** self.weight['harga'] *
                          row['tekanan'] ** self.weight['tekanan']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'no': product['no'],
                'jenis': product['produk'] / self.weight['jenis'] if self.weight['jenis'] != 0 else 0,
                'ukuran': product['produk'] / self.weight['ukuran'] if self.weight['ukuran'] != 0 else 0,
                'harga': product['produk'] / self.weight['harga'] if self.weight['harga'] != 0 else 0,
                'tekanan': product['produk'] / self.weight['tekanan'] if self.weight['tekanan'] != 0 else 0,
                'score': product['produk']  # Nilai skor akhir
            }
            for product in sorted_produk
        ]
        return sorted_data


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['no']:
                  round(row['jenis'] * weight['jenis'] +
                        row['ukuran'] * weight['ukuran'] +
                        row['harga'] * weight['harga'] +
                        row['tekanan'] * weight['tekanan'], 2)
            for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result


def run_saw():
    saw = SimpleAdditiveWeighting()
    result = saw.calculate
    print(tabulate([(k, v) for k, v in result.items()], headers=['ID', 'Score'], tablefmt='pretty'))


def run_wp():
    wp = WeightedProduct()
    result = wp.calculate
    headers = result[0].keys()
    rows = [
        {k: round(v, 4) if isinstance(v, float) else v for k, v in val.items()}
        for val in result
    ]
    print(tabulate(rows, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'create_table':
            create_table()
        elif arg == 'review_data':
            review_data()
        elif arg == 'saw':
            run_saw()
        elif arg == 'wp':
            run_wp()
        else:
            print('Command not found')
    else:
        print('Please provide a command')
