# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from flask import Flask, flash, redirect, render_template, request, session, abort
from src import secrets
from src.montydb import connection, select_all, select_where, select_formas_pago, select_monedas, \
    select_pagadoras, select_puntospago, select_monedas2, select_pagadoras2, select_pagadoras3, select_pagadoras4
from src.willyfog import main


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

    return render_template('1grupo_pagador_page.html', **locals())


@app.route('/Willyfog/step2', methods=['POST', 'GET'])
def paises_page():
    grupos_pagador = request.args.get('parametroGrupoPagador')
    paises = select_all(cursor, 'Nombre', 'TBL_PAIS')

    return render_template('2paises_page.html', **locals())

@app.route('/Willyfog/step3', methods=['POST', 'GET'])
def moneda_page():
    grupos_pagador = request.args.get('parametroGrupoPagador')
    pais = request.args.get('parametroPais')
    codigo_pais = select_where(cursor, 'Id', 'Nombre', pais, 'TBL_PAIS')

    monedas = select_monedas2(cursor, codigo_pais)

    return render_template('3moneda_page.html', **locals())


@app.route('/Willyfog/step4', methods=['POST', 'GET'])
def pagadora_page():
    codigo_pais = request.args.get('parametroPais')
    grupos_pagador = request.args.get('parametroGrupoPagador')
    id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')
    monedas = request.args.get('parametroMoneda')

    if monedas:
        id_monedas = select_where(cursor, 'Id', 'Nombre', monedas, 'TBL_MONEDA')
        pagadoras = select_pagadoras2(cursor, codigo_pais, id_monedas, id_grupos_pagador)
    else:
        pagadoras = select_pagadoras3(cursor, id_grupos_pagador)

    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')

    return render_template('4pagadora_page.html', **locals())


@app.route('/Willyfog/step5', methods=['POST', 'GET'])
def filter_page():
    grupos_pagador = request.args.get('parametroGrupoPagador')
    id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')
    pagadoras_info = select_pagadoras4(cursor, id_grupos_pagador)

    paises = set()
    formas_pago = set()
    monedas = set()
    for p in pagadoras_info:
        paises.add(p[0])
        formas_pago.add(p[1])
        monedas.add(p[2])

    paises = list(paises)
    formas_pago = list(formas_pago)
    monedas = list(monedas)
    return render_template('5filter_page.html', **locals())


@app.route('/Willyfog/step6', methods=['POST', 'GET'])
def results_page():
    raw_pagadoras = request.args.get('parametroPagadoras')
    raw_pagadoras = raw_pagadoras.split(",")

    pagadoras = []
    for p in raw_pagadoras:
        id_pagadora = select_where(cursor, 'Id', 'Empresa', p, 'TBL_PAGADOR')
        pagadoras.append([p, id_pagadora])

    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')

    for p in pagadoras:
        insert, remove, update = main('data/processed/'+new_file, p[1], mode, 0)
    return render_template('6results_page.html', **locals())




if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80)
