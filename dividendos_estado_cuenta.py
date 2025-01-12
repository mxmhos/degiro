# -*- coding: utf-8 -*-
"""
Created on Fri May 31 20:41:07 2024

@author: Patinnio
Código para "estado de la cuenta" -> dividendos
Rendimiento del capital mobiliario a integrar en la base imponible del ahorro
 > 0029 - Dividendos y demás rendimientos por la participación en fondos propios de entidades

"""

import numpy as np
import pandas as pd

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
    
def clean_dataframe(dataframe):
    delete_column(dataframe, "Fecha")
    delete_column(dataframe, "Hora")
    delete_column(dataframe, "Saldo")
    delete_column(dataframe, "Unnamed: 10")
    delete_column(dataframe, "ID Orden")
    
    dataframe = delete_empty_rows(dataframe)
    
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
    aux_money = 0.0
    for index, row in df.iterrows():
        if row["Variación"] == "EUR":
            df.at[index, "Tipo"] = 1.0
            
        elif row["Descripción"] == order[0]: # es retirada cambio de divisa?
            aux_money = row["Tipo"]
            
        else:
            df.at[index, "Tipo"] = aux_money
            
    
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
    df["Variación €"] = None
    df["Recuperación €"] = None
    
    for index, row in df.iterrows():
        df.at[index, "Variación €"] = row["Unnamed: 8"] / row["Tipo"]
    
    for index, row in df.iterrows():
        if row["Variación"] == "EUR" or row["Producto"] == "VANGUARD S&P 500 UCITS ETF USD" or row["Producto"] == "iShares MSCI China A UCITS ETF USD":
            df.at[index, "Recuperación €"] = 0.0
        else:
            df.at[index, "Recuperación €"] = row["Unnamed: 8"] / row["Tipo"]

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
                        

def main():
    # Main
    # This variable has two functions. As values to filter and pattern to order a column
    values_pattern = ["Retirada Cambio de Divisa", "Dividendo", "Retención del dividendo"]
    rawEstadoCuenta = read_csv_to_dataframe("D:\Bolsa Py\estadoCuenta.csv")
    
    estadoCuenta = get_year_data(rawEstadoCuenta, 2023)
    estadoCuenta = clean_dataframe(estadoCuenta)
    estadoFiltro = filtro_by_expecific_column(estadoCuenta, "Descripción", values_pattern)
    coins_bought = get_money_countries(estadoFiltro)
    estadoFiltro_ordenado = order_by_date(estadoFiltro, "Fecha valor")
    finalOrganization = organize_foreigner_money(estadoFiltro_ordenado, values_pattern)
    fillMoneyGaps = fill_money_gaps(finalOrganization, values_pattern)
    deleteRCD = delete_RCD(fillMoneyGaps, values_pattern[1:])
    addColumns = add_columns_and_fill(deleteRCD)
    calculoHacienda(addColumns, values_pattern[1:])
    
    a = 1
    
if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    