import ortools.sat.python.cp_model as cp
import pandas as pd
from ortools.sat.python import cp_model


# region Task A

def logistics_problem():
    _WAREHOUSES = "warehouses"
    _CUSTOMER_ORDERS = "customer orders"
    _SUPPLIER_STOCK = "supplier stock"
    _PRODUCT_SPEC = "product spec"
    _DISTANCES = "distances"

    _ITEM_IDS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                 "u", "v", "w", "x", "y", "z"]
    _LOCATIONS = ["athlone", "belfast", "cork", "derry", "donegal", "dublin", "dundalk", "galway", "kilkenny",
                  "kilarney", "limerick", "portlaoise", "roscommon", "rosslare", "shannon", "sligo", "waterford",
                  "wexford", "wicklow"]

    # format is first column is the ID of the warehouse/customer/supplier/location, and the rest are numbers
    xlsx_names = {
        _WAREHOUSES: ["warehouse", "supply trucks", "delivery vans"],
        _CUSTOMER_ORDERS: ["customer_location"] + _ITEM_IDS,
        _SUPPLIER_STOCK: ["supplier_location"] + _ITEM_IDS,
        _PRODUCT_SPEC: ["product_id", "weight"],
        _DISTANCES: ["location"] + _LOCATIONS,
    }

    _SUPPLY_TRUCK_MAX_WEIGHT = 15000
    _DELIVERY_VAN_MAX_WEIGHT = 3000

    logistics_df = pd.ExcelFile("assets/Assignment_DA_1_Logistics.xlsx")
    dfs = {}

    for sheet in logistics_df.sheet_names:
        dfs[sheet] = logistics_df.parse(
            sheet_name=sheet,
            header=0,
            names=xlsx_names[sheet],
            converters={col: (lambda x: x.strip().lower() if isinstance(x, str) else x)
                        for col in xlsx_names[sheet]}
        )

    warehouses = dfs[_WAREHOUSES].set_index("warehouse")
    orders = dfs[_CUSTOMER_ORDERS].set_index("customer_location")[_ITEM_IDS].fillna(0).astype(int)
    suppliers = dfs[_SUPPLIER_STOCK].set_index("supplier_location")[_ITEM_IDS].fillna(0).astype(int)
    products = dfs[_PRODUCT_SPEC].set_index("product_id")["weight"].fillna(0).astype(int)
    distances = dfs[_DISTANCES].set_index("location")[_LOCATIONS].fillna(0).astype(int)

    # ignoring the route for now, just checking if the logic works and i'll add the route later
    def add_route(source, destination, distance):
        distances.loc[source, destination] = distance
        distances.loc[destination, source] = distance

    # initialise the CP-SAT model
    model = cp.CpModel()

    # declare variables

    # keep track of the number of items ordered from each supplier to each warehouse
    supplier_truck_order_vars = {
        (supplier, warehouse, item):
            model.new_int_var(0, 1000, f"truck_order_{supplier}_{warehouse}_{item}")
        for supplier in suppliers.index
        for warehouse in warehouses.index
        for item in _ITEM_IDS
    }

    # keep track of the number of items delivered from each warehouse to each customer
    warehouse_delivery_order_vars = {
        (warehouse, customer, item):
            model.new_int_var(0, 1000, f"delivery_order_{warehouse}_{customer}_{item}")
        for warehouse in warehouses.index
        for customer in orders.index
        for item in _ITEM_IDS
    }

    # create the constraints

    for supplier in suppliers.index:
        for warehouse in warehouses.index:
            # make sure the weight of items ordered from each supplier to each warehouse is less than the max weight of the supply truck
            model.add(
                sum(supplier_truck_order_vars[(supplier, warehouse, item)] * products.loc[item] for item in
                    _ITEM_IDS) <= _SUPPLY_TRUCK_MAX_WEIGHT
            )
        for item in _ITEM_IDS:
            # make sure the number of items ordered from each supplier to each warehouse is less than the stock available at the supplier
            model.add(
                sum(supplier_truck_order_vars[(supplier, warehouse, item)] for warehouse in warehouses.index) <=
                suppliers.loc[supplier, item]
            )

    for warehouse in warehouses.index:
        # make sure the weight of items delivered from each warehouse to each customer is less than the max weight of the delivery van
        model.add(
            sum(warehouse_delivery_order_vars[(warehouse, customer, item)] * int(products[item]) for customer in
                orders.index for item in
                _ITEM_IDS) <= _DELIVERY_VAN_MAX_WEIGHT * int(warehouses.loc[warehouse, "delivery vans"])
        )
        for item in _ITEM_IDS:
            model.add(
                sum(warehouse_delivery_order_vars[(warehouse, customer, item)] for customer in orders.index)
                <= sum(supplier_truck_order_vars[(supplier, warehouse, item)] for supplier in suppliers.index)
            )
            for customer in orders.index:
                # make sure the number of items delivered from each warehouse to each customer is less than the number of items ordered from each supplier to each warehouse
                model.add(
                    warehouse_delivery_order_vars[(warehouse, customer, item)] <= sum(
                        supplier_truck_order_vars[(supplier, warehouse, item)] for supplier in suppliers.index)
                )

    for customer in orders.index:
        for item in _ITEM_IDS:
            # make sure the number of items delivered from each warehouse to each customer is equal to the number of items ordered by the customer
            model.add(
                sum(warehouse_delivery_order_vars[(warehouse, customer, item)] for warehouse in
                    warehouses.index) == int(orders.loc[customer, item])
            )

    # create the objective function
    model.minimize(
        # minimise the total distance travelled by the supply trucks and delivery vans
        sum(
            distances.loc[supplier, warehouse] * supplier_truck_order_vars[(supplier, warehouse, item)] +
            distances.loc[warehouse, customer] * warehouse_delivery_order_vars[(warehouse, customer, item)]
            for supplier in suppliers.index
            for warehouse in warehouses.index
            for customer in orders.index
            for item in _ITEM_IDS
        ) +
        # minimise the total number of trucks and vans used
        sum(
            supplier_truck_order_vars[(supplier, warehouse, item)] +
            warehouse_delivery_order_vars[(warehouse, customer, item)]
            for supplier in suppliers.index
            for warehouse in warehouses.index
            for customer in orders.index
            for item in _ITEM_IDS
        )
    )

    # call the solver
    solver = cp_model.CpSolver()

    status = solver.Solve(model)

    # print the results
    print(solver.status_name(status))
    if status == cp_model.OPTIMAL:
        print("Optimal solution found")
    else:
        print("No optimal solution found")

    print(solver.solution_info())
    print("Supplier to Warehouse Orders:")
    for supplier in suppliers.index:
        for warehouse in warehouses.index:
            for item in _ITEM_IDS:
                if solver.Value(supplier_truck_order_vars[(supplier, warehouse, item)]) > 0:
                    print(
                        f"Supplier: {supplier}, Warehouse: {warehouse}, Item: {item}, Quantity: {solver.Value(supplier_truck_order_vars[(supplier, warehouse, item)])}")

    for warehouse in warehouses.index:
        for customer in orders.index:
            for item in _ITEM_IDS:
                if solver.Value(warehouse_delivery_order_vars[(warehouse, customer, item)]) > 0:
                    print(
                        f"Warehouse: {warehouse}, Customer: {customer}, Item: {item}, Quantity: {solver.Value(warehouse_delivery_order_vars[(warehouse, customer, item)])}")


# endregion Task A

# region Task B

def sudoku_solver():
    print("Task B")


# endregion Task B

if __name__ == "__main__":
    logistics_problem()
    sudoku_solver()
