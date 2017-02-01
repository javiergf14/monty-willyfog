# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pymssql
from flask import Flask, flash, redirect, render_template, request, session, abort
from src import secrets # Script where credentials are stored.

# User-defined function section.
def select_all(cursor, parameter, table):
    sqlquery = 'SELECT {} FROM {}'.format(parameter, table)
    cursor.execute(sqlquery) 
    array = []
    row = cursor.fetchone()
    while row:
        array.append(row[0])
        row = cursor.fetchone()
    return array

def select_where(cursor, parameter, condition, value, table):
    sqlquery = "SELECT {} FROM {} WHERE {}='{}'".format(parameter, table, condition, value)
    cursor.execute(sqlquery) 
    return cursor.fetchone()[0]


def select_formas_pago(cursor, codigo_pais):
    sqlquery = "select distinct fp.id as id, fp.nombre as nombre from tbl_forma_pago fp inner join tbl_sucursal suc on fp.id = suc.tipoPagoAgente inner join tbl_pagador p    on p.id = suc.id_pagador where p.id_pais = {}".format(codigo_pais)
    cursor.execute(sqlquery) 
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[1]))
        row = cursor.fetchone()
    return array
    
def select_monedas(cursor, codigo_pais, id_forma_pago):
    sqlquery = 'select distinct mon.id as idMoneda, mon.nombre as nombreMoneda from tbl_moneda mon inner join tbl_pagador p on mon.id = p.id_moneda inner join tbl_sucursal suc on p.id = suc.id_pagador where p.id_pais = {} AND suc.tipoPagoAgente = {}'.format(codigo_pais, id_forma_pago)
    cursor.execute(sqlquery) 
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[1]))
        row = cursor.fetchone()
    return array
    
def select_pagadoras(cursor, codigo_pais, forma_pago, id_monedas, grupos_pagador):
    sqlquery = "select Empresa FROM TBL_PAGADOR WHERE Id_pais = {} AND Forma_Pago = '{}' AND Id_Moneda = {} AND Id_GrupoPagador = {}".format(codigo_pais, forma_pago, id_monedas, grupos_pagador)
    cursor.execute(sqlquery) 
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[0]))
        row = cursor.fetchone()
    return array
    
def select_puntospago(cursor, id_pagadora):
    sqlquery = "select * FROM TBL_SUCURSAL WHERE Id_pagador={}".format(id_pagadora)
    cursor.execute(sqlquery) 
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row))
        row = cursor.fetchone()
    return array
    
# FLASK section.
app = Flask(__name__)
 
@app.route("/")
def index():
    return "Flask App!"
 
@app.route("/hello/Willyfog/", methods=['GET'])
def hello():
    # Lucca connection.
    conn = pymssql.connect(server=secrets.db_server, user=secrets.user, password=secrets.password,
                           database=secrets.db_name)
    cursor = conn.cursor() 

    grupos_pagador = select_all(cursor, 'Empresa', 'TBL_GRUPOPAGADOR')
    paises = select_all(cursor, 'Nombre', 'TBL_PAIS')
    
    return render_template(
        'test.html',**locals())
    
@app.route('/hello/Willyfog/step2', methods=['POST', 'GET'])
def saludo():
    # Lucca connection.
   conn = pymssql.connect(server=secrets.db_server, user=secrets.user, password=secrets.password,
                          database=secrets.db_name)
   cursor = conn.cursor() 

   pais = request.args.get('parametroPais')
   grupos_pagador = request.args.get('parametroFormaPago')
   
   id_grupos_pagador = select_where(cursor, 'Id', 'Empresa', grupos_pagador, 'TBL_GRUPOPAGADOR')
   
    
   codigo_pais = select_where(cursor, 'Id', 'Nombre', pais, 'TBL_PAIS')
   formas_pago = select_formas_pago(cursor, codigo_pais)
   return render_template(
          'test2.html',**locals())
   
@app.route('/hello/Willyfog/step3', methods=['POST', 'GET'])
def saludo2():
    # Lucca connection.
   conn = pymssql.connect(server=secrets.db_server, user=secrets.user, password=secrets.password,
                           database=secrets.db_name)
   cursor = conn.cursor() 

   codigo_pais = request.args.get('parametroPais')
   grupos_pagador = request.args.get('parametroGrupoPagador')
   forma_pago = request.args.get('parametroFormaPago')
   
   id_forma_pago = select_where(cursor, 'Id', 'Nombre', forma_pago, 'TBL_FORMA_PAGO')
   
   monedas = select_monedas(cursor, codigo_pais, id_forma_pago)
   
  
        
    
   return render_template(
          'test3.html',**locals())
   
@app.route('/hello/Willyfog/step4', methods=['POST', 'GET'])
def saludo3():
    # Lucca connection.
   conn = pymssql.connect(server=secrets.db_server, user=secrets.user, password=secrets.password,
                           database=secrets.db_name)
   cursor = conn.cursor() 

   codigo_pais = request.args.get('parametroPais')
   grupos_pagador = request.args.get('parametroGrupoPagador')
   forma_pago = request.args.get('parametroFormaPago')
   monedas = request.args.get('parametroMoneda')
   
   id_monedas = select_where(cursor, 'Id', 'Nombre', monedas, 'TBL_MONEDA')
   
   
   pagadoras = select_pagadoras(cursor, codigo_pais, forma_pago, id_monedas, grupos_pagador)
   
        
    
   return render_template(
          'test4.html',**locals())
   
@app.route('/hello/Willyfog/step5', methods=['POST', 'GET'])
def saludo4():
    # Lucca connection.

   conn = pymssql.connect(server=secrets.db_server, user=secrets.user, password=secrets.password,
                           database=secrets.db_name)
   cursor = conn.cursor() 
   pagadora = request.args.get('parametroPagadoras')
   
   id_pagadora = select_where(cursor, 'Id', 'Empresa', pagadora, 'TBL_PAGADOR')
   
   new_file = request.args.get('parametroFichero')
   modo = request.args.get('parametroModo')
  # puntos_pago = select_puntospago(cursor, id_pagadora)
   print(id_pagadora)
   
   #insert, remove, update = temp.main(new_file, 'format.txt', id_pagadora, modo, 0)
   
        
   return render_template(
          'test5.html',**locals())

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=80)