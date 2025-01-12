# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 16:31:07 2024

@author: Patinnio
Código para "transacciones" -> compra y venta de aciones

"""

import numpy as np
import pandas as pd
from decimal import Decimal

pd.set_option('mode.chained_assignment', None) # elimina mensajes de error de pandas. Mirar si es necesario

AUTO_FX = Decimal('0.0025')

def read_csv_to_dataframe(file_path):
    """
    Reads a CSV file and stores it in a pandas DataFrame.
    
    Args:
    file_path (str): The path to the CSV file.
    
    Returns:
    pd.DataFrame: The DataFrame containing the data from the CSV file.
    """
    df = pd.read_csv(file_path)
    return df

def get_year_data(dataframe, year):
    """
    Cuando yo descargo en degiro un año al completo 01/01/20XX - 31/12/20XX la columna
    que marca esta información es "Fecha". Aunque después nos quedemos "Fecha valor"

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.
    year : TYPE
        DESCRIPTION.

    Returns
    -------
    dataframe : TYPE
        DESCRIPTION.

    """
    start_date = pd.to_datetime("01-01-" + str(year), format='%d-%m-%Y')
    end_date = pd.to_datetime("31-12-" + str(year), format='%d-%m-%Y')
    
    dataframe["Fecha"] = pd.to_datetime(dataframe["Fecha"], format='%d-%m-%Y')
    dataframe = dataframe[(dataframe["Fecha"] >= start_date) &
                          (dataframe["Fecha"] <= end_date)]
    
    return dataframe
    
def delete_column(dataframe, column_name):
    del dataframe[column_name]
    
def delete_empty_rows(dataframe):
    dataframe = dataframe.dropna(how='all')
    
    return dataframe

def convert_money_to_decimal(dataframe):
    dataframe = delete_empty_rows(dataframe)
    dataframe["Precio"] = dataframe["Precio"].apply(lambda x: Decimal(str(x)))
    dataframe["Valor local"] = dataframe["Valor local"].apply(lambda x: Decimal(str(x)))
    dataframe["Valor"] = dataframe["Valor"].apply(lambda x: Decimal(str(x)))
    dataframe["Tipo de cambio"] = dataframe["Tipo de cambio"].apply(lambda x: Decimal(str(x)))
    dataframe["Costes de transacción"] = dataframe["Costes de transacción"].apply(lambda x: Decimal(str(x)))
    dataframe["Total"] = dataframe["Total"].apply(lambda x: Decimal(str(x)))
    
    return dataframe
    
def clean_dataframe(dataframe):
    delete_column(dataframe, "Hora")
    delete_column(dataframe, "Bolsa de")
    delete_column(dataframe, "Centro de ejecución")
    delete_column(dataframe, "ID Orden")
    
    dataframe = convert_money_to_decimal(dataframe)
    
    return dataframe

def filtro_by_expecific_column(dataframe, column_name, values_filter):
    """
    Filtra la información especificandole una columna en concreto y busca el 
    valor o valores enviados por values_filter.

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.
    column_name : TYPE
        DESCRIPTION.
    values_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    filtro : TYPE
        DESCRIPTION.

    """
    filtro = dataframe[dataframe[column_name].isin(values_filter)]
    filtro.reset_index(drop=True, inplace=True)
    
    return filtro

def order_by_date(dataframe, column_name_date):
    """
    Ordenamos la información por fecha

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.
    column_name_date : TYPE
        DESCRIPTION.

    Returns
    -------
    dataframe : TYPE
        DESCRIPTION.

    """
    dataframe[column_name_date] = pd.to_datetime(dataframe[column_name_date], 
                                               format='%d-%m-%Y')
    dataframe = dataframe.sort_values(by=column_name_date, ascending=False)
    dataframe.reset_index(drop=True, inplace=True)
    return dataframe

def get_money_countries(dataframe):
    """
    Retorna cada una de las monedas en las que se ha comprado.

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.

    Returns
    -------
    coins : String array
        DESCRIPTION.

    """
    coins = dataframe['Variación'].unique()
    
    return coins

def organize_foreigner_money(dataframe, order):
    index = 0
    while index < len(dataframe):
        row = dataframe.iloc[index]
        if row["Variación"] == "EUR":
            index += 1
        elif row["Variación"] != "EUR" and row["Descripción"] == order[0]: # hay que ver si es un ETF
            if dataframe.iloc[index + 2]["Variación"] == "EUR" or dataframe.iloc[index + 1]["Producto"] != dataframe.iloc[index + 2]["Producto"]:
                index += 2
            else:
                index += 3 # está bien ordenada la información. No hacer nada  
        
        else:
            if dataframe.iloc[index + 1]["Descripción"] == order[0]:
                dataframe.iloc[index] = dataframe.iloc[index + 1]
                dataframe.iloc[index + 1] = row
                
            elif dataframe.iloc[index + 2]["Descripción"] == order[0]:
                dataframe.iloc[index] = dataframe.iloc[index + 2]
                dataframe.iloc[index + 2] = row
                
    return dataframe
            
def fill_money_gaps(df, order):
    for index, row in df.iterrows():
        if pd.isna(row[order[0]]):
            df.at[index, order[0]] = 1.0
            
    for index, row in df.iterrows():
        if pd.isna(row[order[1]]):
            df.at[index, order[1]] = 0
            
    return df
  
def delete_RCD(df, keep_values):
    """
    Elimina todas las filas que tengan Retirada Cambio de Divisa en la Descripción.

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    keep_values : TYPE
        DESCRIPTION.

    Returns
    -------
    filtro : TYPE
        DESCRIPTION.

    """
    filtro = df[df["Descripción"].isin(keep_values)]
    return filtro

def add_columns_and_fill(df):
    """
    Calcula los costes del cambio de moneda al trabajar con monedas extrangeras 
    distintas al euro.
    """
    df["Coste Auto Fx"] = Decimal("0.0")
    
    for index, row in df.iterrows():
        if row["Unnamed: 8"] != "EUR": # si no son euros
            df.at[index, "Coste Auto Fx"] = -1 * np.abs(AUTO_FX * row["Valor"])

    return df

def calculoHacienda(df, values):
    """
    Se tienen 3 casillas ha rellenar en hacienda:
        > Ingresos íntegros
        > Retenciones
        > Gastos de administración y deposito

    Parameters
    ----------
    addColumns : TYPE
        DESCRIPTION.
    values : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    ingresosIntegros = 0
    retenciones = 0
    for index, row in df.iterrows():
        if row["Descripción"] == values[1] and row["Variación"] == "EUR":
            retenciones += row["Variación €"]
        elif row["Descripción"] != values[1]:
            ingresosIntegros += row["Variación €"]
    
    print("Ingresos Integros:", ingresosIntegros)
    print("Retenciones:", retenciones)
    
    """Recuperación de la doble imposición
        Cuota resultante de la autoliquidación
            > Por doble imposicion internaciona por razón de las rentas obtenidas y gravas en el extranjero
                -Rentas incluidas en la base del ahorro -> al lapiz
                    +Rendimientos netos reducidos del capital mobiliario 
                    obtenidos en el extrasnjero incluidos en la base del ahorro
                    +Impuesto satisfecho en el extranjero
    """
    rendimientosCapitalMobiliario = 0
    impuestoExtranjero = 0
    for index, row in df.iterrows():
        if row["Descripción"] == values[0] and row["Variación"] != "EUR":
            rendimientosCapitalMobiliario += row["Variación €"]
        elif row["Descripción"] == values[1] and row["Variación"] != "EUR":
            impuestoExtranjero += row["Recuperación €"]
    
    print("Rendieminetos Capital Mobiliario:", rendimientosCapitalMobiliario)
    print("Impuestos Extranjero:", impuestoExtranjero)
                        
def fix_total(df):    
    for index, row in df.iterrows():
        df.at[index, "Total"] = Decimal(str(row["Valor"])) + Decimal(str(row["Coste Auto Fx"])) + Decimal(str(row["Costes de transacción"]))

    return df

def get_from_year_and_before(dataframe, year):
    """
    Dependiendo del año que se vaya a analizar se tiene que eliminar la info 
    al año fiscal. 

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.
    year : TYPE
        DESCRIPTION.

    Returns
    -------
    dataframe : TYPE
        DESCRIPTION.
        
    """
    # start_date = pd.to_datetime("01-01-" + "1900", format='%d-%m-%Y')
    end_date = pd.to_datetime("31-12-" + str(year), format='%d-%m-%Y')
    
    dataframe["Fecha"] = pd.to_datetime(dataframe["Fecha"], format='%d-%m-%Y')
    dataframe = dataframe[(dataframe["Fecha"] <= end_date)]
    
    return dataframe

def get_year_data(dataframe, year):
    """
    Cuando yo descargo en degiro un año al completo 01/01/20XX - 31/12/20XX la columna
    que marca esta información es "Fecha". Aunque después nos quedemos "Fecha valor"

    Parameters
    ----------
    dataframe : TYPE
        DESCRIPTION.
    year : TYPE
        DESCRIPTION.

    Returns
    -------
    dataframe : TYPE
        DESCRIPTION.
        
    """
    start_date = pd.to_datetime("01-01-" + str(year), format='%d-%m-%Y')
    end_date = pd.to_datetime("31-12-" + str(year), format='%d-%m-%Y')
    
    dataframe["Fecha"] = pd.to_datetime(dataframe["Fecha"], format='%d-%m-%Y')
    dataframe = dataframe[(dataframe["Fecha"] >= start_date) &
                          (dataframe["Fecha"] <= end_date)]
    
    return dataframe

def get_name_stock_sold_in_the_year(df, year):
    stockSoldName = []
    df_aux = get_year_data(df, year)
    
    for index, row in df_aux.iterrows():
        if row["Número"] < 0:
            stockSoldName.append(row["Producto"])
            
    return list(set(stockSoldName))

def get_transations(df, stocksName):
    """
    Coge los valores del df y los almacena en un diccinario con su correspondiente
    información. Si alguna celda tiene un cero como número de acciones no es válido
    así que se evita cogerla.

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    stocksName : TYPE
        DESCRIPTION.

    Returns
    -------
    my_transactions : TYPE
        DESCRIPTION.

    """
    my_transactions = {} # map
    
    for stock_name in stocksName:
        df_aux = df[(df["Producto"] == stock_name) & (df["Número"] != 0)]
        df_aux = df_aux.reset_index(drop=True)
        my_transactions[stock_name] = df_aux
        
    return my_transactions

def get_year(date):
    return date.year

def is_there_a_row_above_of_same_year(row_before, year):
    is_it_same_year = False
    
    if get_year(row_before["Fecha"]) == year:
        is_it_same_year = True
    
    return is_it_same_year

def delete_unnecessary_above_rows(my_transaction, year):
    for index, row in my_transaction.iterrows():
        if (get_year(row["Fecha"]) > year):
            my_transaction.drop(index, axis=0, inplace=True)
        elif (get_year(row["Fecha"]) == year and row["Número"] >= 0):
            my_transaction.drop(index, axis=0, inplace=True)
        else:
            break
    
    return my_transaction
    
def process_transaction(my_transaction, year):
    """
    Se le pasa el par clave y valor para que procese la información para el 
    periodo fiscal. Retorna esta misma información en el formato más comprimido 
    posible. Se actualizan los valores de las acciones que quedan por ejecutar.
    Parameters
    ----------
    my_transaction : Pandas
        DESCRIPTION.

    Returns
    -------
    None.

    """
    my_transaction = delete_unnecessary_above_rows(my_transaction, year)
    
    for index, row in my_transaction.iloc[::-1].iterrows(): # recorrer del revés
        if (row["Número"] < 0) and (get_year(row["Fecha"]) != year):
           while my_transaction.iloc[index]["Número"] < 0: # mientras sea negativo
               if (my_transaction.iloc[index]["Número"] + my_transaction.iloc[-1]["Número"]) < 0:
                   my_transaction.iloc[index, my_transaction.columns.get_loc("Número")] += my_transaction.iloc[-1]["Número"]
                   my_transaction.drop(my_transaction.index[-1], inplace=True)
               else:
                   num_strocks_before = my_transaction.iloc[-1]["Número"]
                   my_transaction.iloc[-1, my_transaction.columns.get_loc("Número")] += my_transaction.iloc[index]["Número"]
                   my_transaction.iloc[-1, my_transaction.columns.get_loc("Valor local")] = -1 * my_transaction.iloc[-1]["Número"] * my_transaction.iloc[-1]["Precio"]
                   my_transaction.iloc[-1, my_transaction.columns.get_loc("Valor")] = -1 * my_transaction.iloc[-1]["Número"] * my_transaction.iloc[-1]["Precio"]
                   my_transaction.iloc[-1, my_transaction.columns.get_loc("Costes de transacción")] = my_transaction.iloc[-1]["Número"] * (my_transaction.iloc[-1]["Costes de transacción"]/num_strocks_before)
                   my_transaction.iloc[-1, my_transaction.columns.get_loc("Total")] = (-1 * my_transaction.iloc[-1]["Número"] * my_transaction.iloc[-1]["Precio"]) + Decimal(str(my_transaction.iloc[-1]["Costes de transacción"]))
                   
                   my_transaction.drop(my_transaction.index[index], inplace=True) 
                   my_transaction.reset_index(drop=True, inplace=True) 
                   if my_transaction.iloc[-1]["Número"] == 0:
                       my_transaction.drop(my_transaction.index[-1], inplace=True) 
                   
                   break
        elif get_year(row["Fecha"]) == year:
            break

def process_all_transactions(stockSoldName, my_transactions, year):
    for stockName in stockSoldName:
        process_transaction(my_transactions[stockName], year)

def calculate_taxes_per_stock(stockName, my_transaction):
    stocks = my_transaction["Número"].sum()
    if stocks == 0:
        print(stockName, "=", my_transaction["Total"].sum())
    else:
        totalStocksSold = my_transaction["Número"].apply(lambda x: x if x < 0 else 0).sum()
        moneyEarned = my_transaction["Total"].apply(lambda x: x if x > 0 else 0).sum()
        for index, row in my_transaction.iloc[::-1].iterrows(): # recorrer del revés
            if row["Número"] + totalStocksSold < 0: # consumo todo el bloque de acciones compradas 
                moneyEarned += row["Total"]
                totalStocksSold += row["Número"]
            else:
                moneyEarned += totalStocksSold*row["Precio"] + row["Costes de transacción"] # los costes de transacción se ponen en hacienda del tirón. El resto de años no se amortizan
                print(stockName, "=", moneyEarned)
                break
            
def calculate_all_taxes(stockSoldName, my_transactions):
    for stockName in stockSoldName:
        calculate_taxes_per_stock(stockName, my_transactions[stockName])

def main():
    # Main
    year = 2024
    
    # This variable has two functions. As values to filter and pattern to order a column
    values_pattern = ["Tipo de cambio", "Costes de transacción"]
    rawEstadoCuenta = read_csv_to_dataframe("D:\Bolsa Py\Transactions.csv")
    
    estadoCuenta = clean_dataframe(rawEstadoCuenta)
    fillMoneyGaps = fill_money_gaps(estadoCuenta, values_pattern)
    addColumns = add_columns_and_fill(fillMoneyGaps)
    fixTotal = fix_total(addColumns)
    # necesito función que le paso el año a analizar, que haga el calculo de los años atrás para ver qué
    # posiciones se cerraron con cuales FIFO e ir eliminando información no útil
    fiscalYearInformation = get_from_year_and_before(fixTotal, year)
    stockSoldName = get_name_stock_sold_in_the_year(fiscalYearInformation, year)
    my_transactions = get_transations(fiscalYearInformation, stockSoldName)
    process_all_transactions(stockSoldName, my_transactions, year)
    calculate_all_taxes(stockSoldName, my_transactions)
    
    
if __name__ == "__main__":
    main()
    
    
    
    
