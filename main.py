import ortools.sat.python.cp_model as cp
import pandas as pd
from ortools.sat.python import cp_model


# region Task A

def logistics_problem():
    """
    TASK A (logistics problem, 30 points)
    In this task you will develop a constrained programming model and use the OR-Tools CP-SAT solver
    to find a solution for a logistics and distribution scenario. The input data is available on Canvas in the
    Excel file Assignment_DA_1_Logistics.xlsx.
    In this scenario, you are optimising four warehouses each of which is operating several trucks
    bringing in products from suppliers to be processed, repackaged, and then shipped to customers
    using smaller delivery vans. The number of supply trucks and delivery vans available at each
    warehouse is provided in the warehouses table of the input file.
    The customers are grouped into delivery locations and for each location the customer orders table
    indicates the quantity for each product (A-Z) that must be delivered there. Similar, the supplier stock
    table shows for each location how much of each product is available for collection there. Note, that
    everything must be processed through the warehouses, so even if a product is available in the same
    location as a customer order, it must be collected by a supply truck first, transported back to the
    warehouse, before it can be delivered to the customer in a delivery van.
    The capacity of supply trucks and delivery vans is limited. Supply trucks can carry a maximum of
    15,000kg and delivery vans are limited to carrying no more than 3,000kg of product. The weight of
    each product type (in kg) is provided in the product spec table.
    ￼
    The goal is to find optimal tours for each of the supply trucks as well as the delivery vans. To
    facilitate this, the distances table contains the mutual distances between all locations.
    1. Identify the decision variables for the problem, then create a CP-SAT model and add the
    necessary variables to the model. [5 points]
    2. Identify the constraints of the problem and add them to the model. Clearly describe the
    purpose of each of your constraints and reference it in your code. [10 points]
    3. Optimising the total distance travelled by each vehicle is likely infeasible. As an
    approximation, introduce an auxiliary variable for each vehicle containing its radius, i.e. the
    distance between the warehouse and the furthest location the vehicle is serving. Then use
    the solver to minimise the maximum of all these radii. [5 points]
    4. Using the optimal solution from the previous task, build CP-SAT models for each of the
    vehicles individually to determine optimal tours that minimise the total distance travelled
    while visiting all locations they serve. [5 points]
    5. Output for each product how much of it is processed in each warehouse, on which trucks it
    is arriving, and on which vans it is departing. Also output for each of the vehicles, the route it
    is travelling and what quantities of which product it is collecting from or delivering to each of
    the locations on its route. [5 points]
    :return: None
    """
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

    distance_vars = {
        (supplier, warehouse, customer, item, distance):
            model.new_int_var(0, 100000, f"distance_{supplier}_{warehouse}_{customer}_{item}_{distance}")
        for supplier in suppliers.index
        for warehouse in warehouses.index
        for customer in orders.index
        for item in _ITEM_IDS
        for distance in distances.index
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
                for supplier in suppliers.index:
                    # make sure the correct distance is calculated for each item delivered from each supplier to each warehouse to each customer
                    model.add(
                        distance_vars[(supplier, warehouse, customer, item, supplier)] ==
                        supplier_truck_order_vars[(supplier, warehouse, item)] * distances.loc[supplier, warehouse] +
                        warehouse_delivery_order_vars[(warehouse, customer, item)] * distances.loc[warehouse, customer]
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
        # minimise the total number of trucks and vans used
        sum(
            supplier_truck_order_vars[(supplier, warehouse, item)] +
            warehouse_delivery_order_vars[(warehouse, customer, item)]
            for supplier in suppliers.index
            for warehouse in warehouses.index
            for customer in orders.index
            for item in _ITEM_IDS
        ) +
        # minimise the total distance travelled by the supply trucks and delivery vans
        sum(
            distance_vars[(supplier, warehouse, customer, item, distance)] * distances.loc[supplier, warehouse] +
            distance_vars[(supplier, warehouse, customer, item, distance)] * distances.loc[warehouse, customer]
            for supplier in suppliers.index
            for warehouse in warehouses.index
            for customer in orders.index
            for item in _ITEM_IDS
            for distance in distances.index
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
            for customer in orders.index:
                for item in _ITEM_IDS:
                    if solver.Value(supplier_truck_order_vars[(supplier, warehouse, item)]) > 0:
                        print(
                            f"S {supplier} (weight carried by truck: {solver.Value(supplier_truck_order_vars[(supplier, warehouse, item)]) * products.loc[item]}) "
                            f"-> W {warehouse} (weight carried by van: {solver.Value(warehouse_delivery_order_vars[(warehouse, customer, item)]) * products.loc[item]}) "
                            f"-> C {customer} "
                            f"-> I {item}: {solver.Value(supplier_truck_order_vars[(supplier, warehouse, item)])}. "
                            f"Total Distance: "
                            f"{solver.Value(distance_vars[(supplier, warehouse, customer, item, supplier)]) +
                               solver.Value(distance_vars[(supplier, warehouse, customer, item, warehouse)])}"
                        )


# endregion Task A

# region Task B

def sudoku_solver():
    """
    TASK B (sudoku solver, 20 points)
    In this task you will develop a constraint programming solver to find the solution for the following
    sudoku puzzle. Do not use the OR Tools library but instead implement the solver from scratch.

    4|8|0 | 0|0|0 | 0|0|5
    0|0|2 | 0|0|8 | 0|4|6
    0|0|6 | 0|9|5 | 0|0|0

    0|0|3 | 0|2|4 | 0|8|9
    6|2|4 | 0|0|0 | 0|5|0
    8|0|5 | 6|7|1 | 0|0|0

    0|0|1 | 0|0|0 | 0|0|0
    5|0|0 | 0|0|0 | 0|0|0
    0|0|9 | 0|6|0 | 0|2|0

    1. Create a data structure that can represent the necessary decision variables and their
    respective domains for a sudoku puzzle and initialise it with the values above. [5 points]
    2. Implement an algorithm to efficiently propagate the all-different constraint over a subset of
    these decision variables. Make sure that the propagator you implement is monotonic and
    idempotent and provide an argument why this is the case. [5 points]
    3. Implement a function that uses the all-different propagator to propagate the constraints of
    the sudoku puzzle, i.e. that no digit occurs twice in any of the rows, in any of the columns, or
    in any of the 3x3 sub-grids. [5 points]
    4. Implement a backtracking search algorithm that alternates between propagation and
    branching. Choose an effective branching strategy and provide an argument why this
    strategy is most suitable for your propagator implementation. Output the solution for the
    sudoku problem above. [5 points]
    :return:
    """
    sudoku_problem = [
        [4, 8, 0, 0, 0, 0, 0, 0, 5],
        [0, 0, 2, 0, 0, 8, 0, 4, 6],
        [0, 0, 6, 0, 9, 5, 0, 0, 0],
        [0, 0, 3, 0, 2, 4, 0, 8, 9],
        [6, 2, 4, 0, 0, 0, 0, 5, 0],
        [8, 0, 5, 6, 7, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0],
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 9, 0, 6, 0, 0, 2, 0]
    ]


# endregion Task B

if __name__ == "__main__":
    logistics_problem()
    sudoku_solver()
