# import OR tools CP-SAT solver
import ortools.sat.python.cp_model as cp
import pandas as pd
import numpy as np

#region Task A

def logistics_problem():
    _WAREHOUSES         = "warehouses"
    _CUSTOMER_ORDERS    = "customer orders"
    _SUPPLIER_STOCK     = "supplier stock"
    _PRODUCT_SPEC       = "product spec"
    _DISTANCES          = "distances"

    _ITEM_IDS   =   ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    _LOCATIONS  =   ["athlone", "belfast", "cork", "derry", "donegal", "dublin", "dundalk", "galway", "kilkenny", "kilarney", "limerick", "portlaoise", "roscommon", "rosslare", "shannon", "sligo", "waterford", "wexford", "wicklow"]

    xlsx_names = {
        _WAREHOUSES:        ["warehouse", "supply trucks", "delivery vans"],
        _CUSTOMER_ORDERS:   ["customer_location"] + _ITEM_IDS,
        _SUPPLIER_STOCK:    ["supplier_location"] + _ITEM_IDS,
        _PRODUCT_SPEC:      ["product_id", "weight"],
        _DISTANCES:         ["location"] + _LOCATIONS,
    }

    _SUPPLY_TRUCK_MAX_WEIGHT = 15000
    _DELIVERY_VAN_MAX_WEIGHT = 3000

    logistics_df = pd.ExcelFile("assets/Assignment_DA_1_Logistics.xlsx")

    for sheet in logistics_df.sheet_names:
        print(f"Sheet: {sheet}")
        df = logistics_df.parse(sheet_name=sheet, header=1, names=xlsx_names[sheet], converters={col: (lambda x: x.strip().lower() if isinstance(x, str) else x) for col in xlsx_names[sheet]})
        print(df.head())
        print("\n")

#endregion Task A

#region Task B

def sudoku_solver():
    print("Task B")

#endregion Task B

if __name__ == "__main__":
    logistics_problem()
    sudoku_solver()