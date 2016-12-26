import pymssql
import daff

def connection(server, user, password, database):
    return pymssql.connect(server=server, user=user, password=password, database=database)      


def transform_to_template(raw_doc, raw_header, format_array):    
    offset = format_array["Offset"]
    format_array.pop("Offset", None)
    
    formatted_doc = []
    formatted_doc.append(raw_header)
    for cont, raw_row in enumerate(raw_doc):
        if cont < offset: continue # Dummy rows at the beginning of the file.
        row = ['']*len(raw_header)
        for key, value in format_array.items():
            row[raw_header.index(key)] = str(raw_row[value-1])       
        formatted_doc.append(row)
    return formatted_doc
   

def files_comparator(current_file, new_file, format_array):
       
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
    # We do not remove rows, we desactivate them.
    for elem in rows:
        cursor.execute('UPDATE {} SET Activado=0 WHERE Id={}'.format(table_name, elem))
   

def insert_rows(rows, table_name, raw_header, db_header, format_array, cursor, id_pagador): 
    for elem in rows: 
        # To check if the row does already exist.
        condition = ''
        for cont, i in enumerate(raw_header):
            if elem[cont]:
                condition += i+"='"+elem[cont]+"' AND "
        condition += "Activado='0'"
        
        msg = 'SELECT * FROM {} WHERE {}'.format(table_name, condition)
        cursor.execute(msg)
        resp = cursor.fetchone() 
        
        if resp: # If the row exists, activate it.      
            cursor.execute('UPDATE {} SET Activado=1 WHERE Id={}'.format(table_name, resp[0]))
        
        else: # If not, create the row.
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
            
            msg = "INSERT INTO {} ({}, DateStamp, CheckCuenta, tipoPagoAgente, Id_Pagador) VALUES ({}, GETDATE(), 'com.bjs.util.checkAccountGeneral', '9', {})".format(table_name, ','.join(db_header), ','.join(row), id_pagador)
            cursor.execute(msg)
     

def update_rows(rows, table_name, cursor):
    to_update = []
    for elem in rows:    
        msg = 'SELECT Id, {} FROM {} WHERE Id={}'.format(elem[1], table_name, "'"+str(elem[0])+"'")
        cursor.execute(msg)
        resp = cursor.fetchone()
        old_value = [resp[0], elem[1], resp[1]]
        new_value = elem
        #print("Old value:", old_value)
        #print("New value", new_value)
        input_var = 1
        #input_var = input("Cual de las alternativas quieres introducir? 0 (old value), 1 (new value) o introduce tu propio valor:")
        
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