# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from flask import Flask, flash, redirect, render_template, request, session, abort
from src import secrets
from src.montydb import connection, select_all, select_where, \
    select_monedas, select_pagadora, select_pagadoras_complete, select_pagadora_id
from src.willyfog import main
import json


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
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')
    paises = select_all(cursor, 'Nombre', 'TBL_PAIS')

    return render_template('2paises_page.html', **locals())

@app.route('/Willyfog/step3', methods=['POST', 'GET'])
def moneda_page():
    grupos_pagador = request.args.get('parametroGrupoPagador')
    pais = request.args.get('parametroPais')
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')
    codigo_pais = select_where(cursor, 'Id', 'Nombre', pais, 'TBL_PAIS')

    monedas = select_monedas(cursor, codigo_pais)

    return render_template('3moneda_page.html', **locals())


@app.route('/Willyfog/step4', methods=['POST', 'GET'])
def pagadora_page():
    codigo_pais = request.args.get('parametroPais')
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')
    grupos_pagador = request.args.get('parametroGrupoPagador')
    id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')
    monedas = request.args.get('parametroMoneda')

    if monedas:
        id_monedas = select_where(cursor, 'Id', 'Nombre', monedas, 'TBL_MONEDA')
        pagadoras = select_pagadora(cursor,  id_grupos_pagador, codigo_pais, id_monedas)
    else:
        pagadoras = select_pagadora(cursor, id_grupos_pagador)

    return render_template('4pagadora_page.html', **locals())


@app.route('/Willyfog/step5', methods=['POST', 'GET'])
def filter_page():
    grupos_pagador = request.args.get('parametroGrupoPagador')
    id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')
    pagadoras_info = select_pagadoras_complete(cursor, id_grupos_pagador)
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')

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
def filter_pagadoras_page():
    id_grupos_pagador = request.args.get('parametroGrupoPagador')
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')
    paises = request.args.get('parametroPaises')
    forma_pago = request.args.get('parametroFormaPago')
    monedas = request.args.get('parametroMonedas')

    codigo_pais = None
    if(paises):
        codigo_pais = select_where(cursor, 'Id', 'Nombre', paises, 'TBL_PAIS')

    id_monedas = None
    if(monedas):
        id_monedas = select_where(cursor, 'Id', 'Nombre', monedas, 'TBL_MONEDA')

    pagadoras = select_pagadora_id(cursor, id_grupos_pagador, codigo_pais=codigo_pais, id_monedas=id_monedas, forma_pago=forma_pago)

    with open("data/formats/grupos_pagador/format_" + str(id_grupos_pagador) + ".txt", "r") as f:
        format_json = f.read()
    format_array = json.loads(format_json)

    pagadoras_in_file_ids =  list(format_array['Pagadoras'].keys())
    pagadoras_in_file_ids = [int(id) for id in pagadoras_in_file_ids]

    pagadoras_filter_names = []
    pagadoras_filter_values = []
    for id, p in pagadoras:
       if id in pagadoras_in_file_ids:
           pagadoras_filter_names.append(p)
           pagadoras_filter_values.append(id)

    return render_template('6filter_pagadoras_page.html', **locals())



@app.route('/Willyfog/step7a', methods=['POST', 'GET'])
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
    return render_template('7aresults_page.html', **locals())



@app.route('/Willyfog/step7b', methods=['POST', 'GET'])
def results_page2():
    new_file = request.args.get('parametroFichero')
    mode = request.args.get('parametroModo')
    id_grupos_pagador = request.args.get('parametroGrupoPagador')

    id_filtered_pagadoras = request.args.get('parametroPagadoras').split(",")
    id_filtered_pagadoras = [int(id) for id in id_filtered_pagadoras]

    with open("data/formats/grupos_pagador/format_" + str(id_grupos_pagador) + ".txt", "r") as f:
        format_json = f.read()
    format_array = json.loads(format_json)

    pagadoras_in_file_ids =  list(format_array['Pagadoras'].keys())
    pagadoras_in_file_ids = [int(id) for id in pagadoras_in_file_ids]

    pagadoras_selected = []
    for id in pagadoras_in_file_ids:
        if id not in list(id_filtered_pagadoras):
            pagadoras_selected.append(id)
            insert, remove, update = main('data/processed/' + new_file, id, mode, 0, id_grupos_pagador)

    return render_template('7bresults_page.html', **locals())

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80)
