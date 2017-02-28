import pymssql
import daff


def connection(server, user, password, database):
    """
    Connection to a Microsoft SQL Server database.

    Parameters
    ----------
    server
        database host.
    user
        database user to connect as.
    password
         user’s password.
    database
        the database to initially connect to.

    Return
    ------
    Connection
        a MSSQL database connection.
    """

    return pymssql.connect(server=server, user=user, password=password, database=database)      


def transform_to_template(raw_doc, raw_header, format_array):   
    """
    Transform a raw document into a default template given a format.

    Parameters
    ----------
    raw_doc
        raw document to transform.
    raw_header
        headers of the raw document.
    format_array
        instrucctions on how to transform the raw document to.

    Return
    ------
    Array
        the formatted document.
    """ 

    # Dummy rows at the beginning of the file.
    offset = format_array["Offset"]
    format_array.pop("Offset", None)
    
    formatted_doc = []
    formatted_doc.append(raw_header)
    for cont, raw_row in enumerate(raw_doc):
        if cont < offset: continue
        if raw_row == ['']*len(raw_header): continue  # blank line

        row = ['']*len(raw_header)
        for key, value in format_array.items():
            row[raw_header.index(key)] = str(raw_row[value-1])       
        formatted_doc.append(row)
    return formatted_doc
   

def files_comparator(current_file, new_file, format_array):
    """
    Comparing two tables using the `daff` library.

    The `daff` library is optimized for comparing tables that share a common origin, 
    in other words multiple versions of the "same" table.

    More info: http://paulfitz.github.io/daff/

    Parameters
    ----------
    current_file
        last version of the table.
    new_file
        new version of the table.
    format_array
        instrucctions on how the new version has been transformed to.

    Return
    ------
    insert
        new rows to instert.
    remove
        old rows to remove.
    update
        old rows to update.
    """
       
    table1 = daff.PythonTableView(current_file)
    table2 = daff.PythonTableView(new_file)   
    
    flags = daff.CompareFlags()    
    # Set columns to ignore
    if "TipoPago" not in format_array:
        flags.ignoreColumn("TipoPago")    
    # Set primary keys
    if  "CodigoOficina" in format_array: # Unique office code.  
        flags.addPrimaryKey("CodigoOficina")
    else: # TODO: agree in primary key when CodigoOficina is null.
        flags.addPrimaryKey("Direccion")
        flags.addPrimaryKey("Municipio")
        
    table_diff = daff.diff(table1, table2, flags)
    filter_list = ['', '...', ':', '!'] # Ignore these flags.
    
    data = [x for x in table_diff.getData() if x[0] not in filter_list] 
    
    insert = []
    remove = []
    update = []

    for elem in data:
        if elem[0] == "@@":
            header = elem
        elif elem[0] == "+++": # Add the whole row. 
            insert.append(elem[2:]) 
        elif elem[0] == "---": # Add just the id.
            remove.append(elem[1]) 
        elif elem[0] == "->": # Add id, column name and new column value.
            for cont, i in enumerate(elem[1:]):
                if("->" in str(i)):               
                    aux = i.split("->")[1]                
                    update.append((elem[1], header[cont+1], aux)) # +1 because of @@ header.
    return insert, remove, update
  

def remove_rows(rows, table_name, cursor):
    """
    Remove rows from the database. Actually, we just desactivate them.

    Parameters
    ----------
    rows
        rows to remove.
    table_name
        name of the table where the rows will be removed.
    cursor
        connection to the MSSQL database.
    """
    
    for elem in rows:
        cursor.execute('UPDATE {} SET Activado=0 WHERE Id={}'.format(table_name, elem))
   

def insert_rows(rows, table_name,  cursor, raw_header, db_header, format_array, id_pagador): 
    """
    Insert rows to the database. 

    If the row has already existed in the database, we activate it.
    Else, we insert this new row.

    Parameters
    ----------
    rows
        rows to insert.
    table_name
        name of the table where the rows will be inserted.
    cursor
        connection to the MSSQL database.
    raw_header
        headers of the new document.
    db_header
        headers of the database.
    format_array
         instrucctions on how the new version has been transformed to.
    id_pagador
        id of the pagadora.
    """

    for elem in rows:
        # Constructing a row with the database format in order to check if the row does already exist.
        condition = ''
        for cont, i in enumerate(raw_header):
            if elem[cont]:
                # Replace single quotes to double quotes (if not, error when inserting)
                elem[cont] = elem[cont].replace("'", "''")
                condition += i+"='"+elem[cont].replace("'", "''")+"' AND "
        condition += "Activado='0'"
        
        # Check if the row does exist.
        msg = 'SELECT * FROM {} WHERE {}'.format(table_name, condition)

        resp = ""
        try:
            cursor.execute(msg)
            resp = cursor.fetchone()
        except Exception as e:
            print(msg)
            print(e)

        if resp: # If the row exists, activate it.      
            cursor.execute('UPDATE {} SET Activado=1 WHERE Id={}'.format(table_name, resp[0]))
        
        else: # If not, create the new row.
            try:
                db_header.pop(db_header.index("Id")) # Remove the ID field.
            except:
                pass
            
             # Needed because TipoPago cannot be null in the database.
            if "TipoPago" not in format_array:
                elem.insert(db_header.index("TipoPago"), '0')
                
            # Create new row fitting the db headers.            
            row = ["''"]*len(db_header)
            for cont, i in enumerate(elem):
                if i:
                    row[cont] = "'"+i+"'"         
            row[db_header.index("Activado")] = "'1'"
            
            msg = "INSERT INTO {} ({}, DateStamp, CheckCuenta, tipoPagoAgente, Id_Pagador) VALUES ({}, GETDATE(), " \
                  "'com.bjs.util.checkAccountGeneral', '9', {})".format(table_name, ','.join(db_header), ','.join(row),
                                                                        id_pagador)

            cursor.execute(msg)

     

def update_rows(rows, table_name, cursor):
    """
    Update rows from the database. 

    Parameters
    ----------
    rows
        rows to update.
    table_name
        name of the table where the rows will be updated.
    cursor
        connection to the MSSQL database.
    """

    to_update = []
    for elem in rows:  

        msg = 'SELECT Id, {} FROM {} WHERE Id={}'.format(elem[1], table_name, "'"+str(elem[0])+"'")
        cursor.execute(msg)
        resp = cursor.fetchone()
        old_value = [resp[0], elem[1], resp[1]]
        new_value = elem

        # In the future, we will ask if we indeed want to change the value.
        #print("Old value:", old_value)
        #print("New value", new_value)        
        #input_var = input("Cual de las alternativas quieres introducir? 0 (old value), 1 (new value) o introduce tu propio valor:")
        input_var = 1
        new_var = []
        if input_var == 0:
            new_var = old_value
        elif input_var == 1:
            new_var = new_value
        else:
            new_var = [elem[0], elem[1], input_var]
            
        to_update.append(new_var)
        msg = 'UPDATE {} SET {}={} WHERE Id={}'.format(table_name, new_var[1], "'"+str(new_var[2])+"'", "'"+str(new_var[0])+"'")
        cursor.execute(msg)
    return to_update



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


def select_monedas(cursor, codigo_pais):
    sqlquery = 'select distinct mon.id as idMoneda, mon.nombre as nombreMoneda from tbl_moneda mon inner join ' \
               'tbl_pagador p on mon.id = p.id_moneda where ' \
               'p.id_pais = {}'.format(codigo_pais)
    cursor.execute(sqlquery)
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[1]))
        row = cursor.fetchone()
    return array


def select_pagadora(cursor, grupos_pagador=None, codigo_pais=None, id_monedas=None, forma_pago=None):
    first_and = False
    sqlquery = "select Empresa FROM TBL_PAGADOR WHERE "
    if grupos_pagador:
        sqlquery += "Id_GrupoPagador =" + str(grupos_pagador)
        first_and = True
    if codigo_pais:
        sqlquery += first_and * "AND " + "Id_pais =" + str(codigo_pais)
        first_and = True
    if id_monedas:
        sqlquery += first_and * "AND " + "Id_Moneda =" + str(id_monedas)
        first_and = True
    if forma_pago:
        sqlquery += first_and * "AND " + "Forma_Pago =" + "'"+str(forma_pago)+"'"

    cursor.execute(sqlquery)
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[0]))
        row = cursor.fetchone()
    return array


def select_pagadora_id(cursor, grupos_pagador=None, codigo_pais=None, id_monedas=None, forma_pago=None):
    first_and = False
    sqlquery = "select Id, Empresa FROM TBL_PAGADOR WHERE "
    if grupos_pagador:
        sqlquery += "Id_GrupoPagador =" + str(grupos_pagador)
        first_and = True
    if codigo_pais:
        sqlquery += first_and * "AND " + "Id_pais =" + str(codigo_pais)
        first_and = True
    if id_monedas:
        sqlquery += first_and * "AND " + "Id_Moneda =" + str(id_monedas)
        first_and = True
    if forma_pago:
        sqlquery += first_and * "AND " + "Forma_Pago =" + "'"+str(forma_pago)+"'"

    cursor.execute(sqlquery)
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[0], row[1]))
        row = cursor.fetchone()
    return array


def select_pagadoras_complete(cursor, grupos_pagador):
    sqlquery = "select pais.Nombre, pag.Forma_Pago, mon.Nombre FROM TBL_PAGADOR pag " \
               "inner join tbl_pais pais on pais.id = pag.Id_Pais inner join tbl_moneda mon on mon.id = pag.Id_Moneda " \
               "WHERE pag.Id_GrupoPagador = {}".format(grupos_pagador)

    cursor.execute(sqlquery)
    array = []
    row = cursor.fetchone()
    while row:
        array.append((row[0], row[1], row[2]))
        row = cursor.fetchone()
    return array