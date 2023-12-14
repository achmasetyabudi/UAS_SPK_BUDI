from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import BanMotor as BanMotorModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)


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
        query = select(BanMotorModel.no, BanMotorModel.merek,BanMotorModel.jenis, BanMotorModel.ukuran, BanMotorModel.harga, BanMotorModel.tekanan)
        result = session.execute(query).fetchall()
        return [{'no': BanMotor.no, 'merek': BanMotor.merek,'jenis': BanMotor.jenis, 'ukuran': BanMotor.ukuran, 'harga': BanMotor.harga,
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
    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

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
                'ID': product['no'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'BanMotor': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'ID': row['no'],
                'Score': round(row['jenis'] * weight['jenis'] +
                        row['ukuran'] * weight['ukuran'] +
                        row['harga'] * weight['harga'] +
                        row['tekanan'] * weight['tekanan'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'BanMotor': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value


class BanMotor(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(BanMotorModel).order_by(BanMotorModel.no)
        result_set = query.all()
        data = [{'no': row.no, 'merek': row.merek,'jenis': row.jenis, 'ukuran': row.ukuran, 'harga': row.harga,
                'tekanan': row.tekanan}
                for row in result_set]
        return self.get_paginated_result('BanMotor/', data, request.args), 200


api.add_resource(BanMotor, '/BanMotor')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)