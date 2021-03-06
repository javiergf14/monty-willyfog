# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from flask import Flask, flash, redirect, render_template, request, session, abort
from src import secrets
from src.montydb import connection, select_all, select_where, select_formas_pago, select_monedas, \
    select_pagadoras, select_puntospago

# FLASK section.
app = Flask(__name__)

# Lucca connection.
conn = connection(secrets.db_server, secrets.user, secrets.password, secrets.db_name)
cursor = conn.cursor()


@app.route("/")
def index():
    return "WillyFog Flask App!"


@app.route("/Willyfog/", methods=['GET'])
def grupo_pagador_page():
    grupos_pagador = select_all(cursor, 'Empresa', 'TBL_GRUPOPAGADOR')
    paises = select_all(cursor, 'Nombre', 'TBL_PAIS')

    return render_template('grupo_pagador_page.html', **locals())


@app.route('/Willyfog/step2', methods=['POST', 'GET'])
def forma_pago_page():
    pais = request.args.get('parametroPais')
    grupos_pagador = request.args.get('parametroFormaPago')

    id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')

    codigo_pais = select_where(cursor, 'Id', 'Nombre', pais, 'TBL_PAIS')
    formas_pago = select_formas_pago(cursor, codigo_pais)
    return render_template('forma_pago_page.html', **locals())


@app.route('/Willyfog/step3', methods=['POST', 'GET'])
def moneda_page():
    codigo_pais = request.args.get('parametroPais')
    grupos_pagador = request.args.get('parametroGrupoPagador')
    forma_pago = request.args.get('parametroFormaPago')

    id_forma_pago = select_where(cursor, 'Id', 'Nombre', forma_pago, 'TBL_FORMA_PAGO')

    monedas = select_monedas(cursor, codigo_pais, id_forma_pago)

    return render_template('moneda_page.html', **locals())


@app.route('/Willyfog/step4', methods=['POST', 'GET'])
def pagadora_page():
    codigo_pais = request.args.get('parametroPais')
    grupos_pagador = request.args.get('parametroGrupoPagador')
    forma_pago = request.args.get('parametroFormaPago')
    monedas = request.args.get('parametroMoneda')
    id_monedas = select_where(cursor, 'Id', 'Nombre', monedas, 'TBL_MONEDA')

    pagadoras = select_pagadoras(cursor, codigo_pais, forma_pago, id_monedas, grupos_pagador)

    return render_template('pagadora_page.html', **locals())


@app.route('/Willyfog/step5', methods=['POST', 'GET'])
def results_page():
    pagadoras = request.args.get('parametroPagadoras')
    id_pagadora = select_where(cursor, 'Id', 'Empresa', pagadoras, 'TBL_PAGADOR')
    #new_file = request.args.get('parametroFichero')
    #modo = request.args.get('parametroModo')
    # puntos_pago = select_puntospago(cursor, id_pagadora)
    #print(id_pagadora)

    # insert, remove, update = temp.main(new_file, 'format.txt', id_pagadora, modo, 0)
    return render_template('results_page.html', **locals())


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80)
