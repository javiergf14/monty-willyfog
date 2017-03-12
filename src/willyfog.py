import json
import argparse
import unidecode
import pandas as pd
import copy
from src import secrets, montydb


def main(new_csv, id_pagador, flag, debug, grupo_pagador=False):

    # Loading the format file
    if grupo_pagador: # Multiple pagadoras within a grupo_pagador file.
        format_file_path = "data/formats/grupos_pagador/format_" + str(grupo_pagador) + ".txt"
    else: # Single pagadora.
        format_file_path = "data/formats/pagadoras/format_" + str(id_pagador) + ".txt"

    with open(format_file_path, "r") as f:
        format_json = f.read()
    format_array = json.loads(format_json)

    # Database parameters
    table_name = 'TBL_SUCURSAL' 
    
    # Microsoft SQL Server connection.
    conn = montydb.connection(secrets.db_server, secrets.user, secrets.password, secrets.db_name)
    cursor = conn.cursor()
   
    # Headers definition.
#    raw_header = ["Direccion", "CodigoPostal", "Localidad", "Municipio", "Provincia", "Id_Pais", "Telefono", "Nombre", "Id_Pagador", "Fijo",
#             "Porcentaje", "CCambio", "Cambio", "CodigoOficina", "DateStamp", "FechaAlta", "CadenaPago", "LongCuentaMin", "LongCuentaMax", 
#            "CheckCuenta", "TipoCuenta", "TipoPago", "Horario", "tipoPagoAgente", "flagActualizado", "idLocalidad"]
    raw_header = ["Direccion", "CodigoPostal", "Localidad", "Municipio", "Provincia", "Telefono", "Nombre", 
                   "TipoPago", "CodigoOficina"]
    db_header = copy.deepcopy(raw_header)
    db_header.insert(0, "Id")
    db_header.append('Activado')
    db_header.append('Geocode')
    
    # Fetch current database information.
    cursor.execute('SELECT {} FROM {} WHERE Activado=1 AND ID_pagador={}'.format(','.join(db_header),table_name, int(id_pagador))) # Extract only activated rows.
    db_doc = cursor.fetchall()
    db_doc.insert(0, db_header) # Insert header at the beginning.
    
    # Load new information.
    raw_doc = pd.read_csv(new_csv, sep=";", header=None, encoding="ISO-8859-1")
    if grupo_pagador:
        raw_doc = raw_doc[raw_doc[format_array["CampoPagadora"]-1] == format_array["Pagadoras"][str(id_pagador)]]
        # Let us remove unused format fields.
        local_format_array = copy.deepcopy(format_array)
        local_format_array.pop("CampoPagadora", None)
        local_format_array.pop("Pagadoras", None)
    else:
        local_format_array = format_array
        
    raw_doc.fillna('', inplace=True)
    raw_doc = raw_doc.values.tolist() # Convert dataframe to list.
   
    # Let us remove the accents and strange letters.
    unicode_doc = []
    for row in raw_doc:
        unicode_row = []
        for elem in row:
            # Convert everything to string and replace ´ character to ''.
            s = str(elem).replace("´", "'")
            unicode_row.append(unidecode.unidecode(s))
        unicode_doc.append(unicode_row)    
    raw_doc = unicode_doc
    
    # Convert raw document to template format.
    formatted_doc = montydb.transform_to_template(raw_doc, raw_header, local_format_array) 
    
    # Detect changes between database and new doc.
    insert, remove, update = montydb.files_comparator(db_doc, formatted_doc, local_format_array)
    # Flags condition
    if flag == 1:
        remove = []
        update = []
    elif flag == 2:
        insert = []
        update = []
    
    # Insert changes in the database.
    montydb.remove_rows(remove, table_name, cursor)
    montydb.insert_rows(insert, table_name, cursor, raw_header, db_header, local_format_array, int(id_pagador))
    to_update = montydb.update_rows(update, table_name, cursor)
    # Commit changes.



    try:
        conn.commit()
    except:
        print(insert)
        print(remove)
        print(update)
   
    if debug:
        print(insert)
        print(remove)
        print(update)
    
    return insert, remove, to_update
    
if __name__ == '__main__':    
    
    parser = argparse.ArgumentParser()
    parser.add_argument("new_file", help="Fichero nuevo a comparar", nargs='?')
    parser.add_argument("id_pagador", help="Pagadora a insertar nuevos puntos de pago", 
                        type=str, nargs='?')
    parser.add_argument("flag", help="Argumento para insertar nuevos puntos de pago. 0: todos, 1: insertar, 2: borrar", 
                        type=int, default=0, nargs='?')
    parser.add_argument("debug", help="Debug option", 
                        type=int, default=0, nargs='?')
    
    args = parser.parse_args()
    

    
    # If multiple pagadoras inside the file (e.g. More)
    #if "Pagadoras" in format_array:
    #    for pagadora, id_pagador in format_array["Pagadoras"].items():
    #        main(args.new_file, id_pagador, format_array, args.flag, args.debug, pagadora)
    #else:
    #    main(args.new_file, args.id_pagador, format_array, args.flag, args.debug)