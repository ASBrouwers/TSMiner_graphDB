import os
import subprocess
from timeit import default_timer as timer

from graphviz import Digraph
from neo4j import GraphDatabase

# SETTINGS -------------------------------------
neo4j_address = "bolt://localhost:7687"
username = "neo4j"
password = "1234"
CLI = True  # Enable CLI to set parameters, else use below values
abstrs = [1, 2]  # Abstractions to use if CLI == false: 1 = List, 2 = Set
ks = [3]  # ks to use if CLI == false

DOT = True  # Render dot to PNG

# END SETTINGS ---------------------------------

c_white = "#ffffff"
c_black = "#000000"

c5_red = '#d73027'
c5_orange = '#fc8d59'
c5_yellow = '#fee090'
c5_light_blue = '#e0f3f8'
c5_medium_blue = '#91bfdb'
c5_dark_blue = '#4575b4'

def reset(tx):
    # Remove nodes & relationships created by TS query
    q_reset = ["MATCH ()-[r:DF_ABS]->() DELETE r",
               "MATCH ()-[r:E_ABS]->() DELETE r",
               "MATCH (l:TS_node) DELETE l"]

    for q in q_reset:
        print(q)
        tx.run(q)


def create_start_nodes(tx):
	q_start = """
		MATCH (e:Event)
		WHERE NOT (() -[:DF]-> (e))
		MATCH (e) -[:E_EN]-> (en:Entity)
		WITH e, en.EntityType AS entityType
		MATCH (e) -[:E_ABS]-> (a)
		MERGE (st:TS_node {Events: ["Start"], Name: "Start", TS_nodeID: "Start", Type: a.Type, EntityType: entityType})
		MERGE (st) -[d:DF_ABS {Activity: e.Activity}]-> (a)
	"""

	print(q_start)
	return tx.run(q_start)

def create_end_nodes(tx):
    q_end = """
        MATCH (e:Event)
        WHERE NOT ((e) -[:DF]-> ())
        MATCH (e) -[:E_EN]-> (en:Entity)
        WITH e, en.EntityType AS entityType
        MATCH (e) -[:E_ABS]-> (a)
        MERGE (ed:TS_node {Events: ["End"], Name: "End", TS_nodeID: "End", Type: a.Type, EntityType: entityType})
        MERGE (a) -[d:DF_ABS {Activity: ""}]-> (ed)
    """

    print(q_end)
    return tx.run(q_end)


def create_list_df(tx):
    q_classes = """ 
        // EVENT TO LIST:
        MATCH (e:Event)
        MATCH path=(e_first:Event) -[:DF*0..]-> (e)
        // Check path length here so we can use parameter
        WHERE length(path)  <= $k-1  AND ((NOT ()-[:DF]->(e_first)) OR size(relationships(path)) = $k-1)
        UNWIND nodes(path) as n
        WITH collect(n.Activity) AS activities, path, e 
        WITH path, REDUCE(s = HEAD(activities), n IN TAIL(activities) | s + '-' + n) AS listName, e, activities
        MERGE ( l:TS_node { Name:e.Activity, Type:"Activity_Past_" + $k + "_List", TS_nodeID: listName, Activities: activities})
        CREATE (e) -[ecl:E_ABS]-> (l)
        """

    q_link_df = """
        // Push DF from event to list:
        MATCH (e1:Event) -[:DF]-> (e2:Event), (e1) -[:E_ABS]-> (l1), (e2) -[:E_ABS]-> (l2)
        MERGE (l1) -[df:DF_ABS {Activity: e2.Activity}]-> (l2)
        RETURN l1, df, l2
        """

    print(q_classes)
    tx.run(q_classes, k=k)
    print(q_link_df)
    return tx.run(q_link_df, t=f"List-{k}")


def create_set_df(tx):
    q_classes = """ 
        // EVENT TO SET:
        MATCH (e:Event)
        MATCH path=(e_first:Event) -[:DF*0..]-> (e)
        // Check path length here so we can use parameter
        WHERE length(path)  <= $k-1  AND ((NOT ()-[:DF]->(e_first)) OR size(relationships(path)) = $k-1)
        UNWIND nodes(path) as n 
        WITH e, path, n ORDER BY n.Activity
        WITH collect(DISTINCT n.Activity) AS activities, path, e 
        WITH path, REDUCE(s = HEAD(activities), n IN TAIL(activities) | s + '-' + n) AS listName, e, activities
        MERGE ( l:TS_node { Name:listName, Type:"Activity_Past_" + $k + "_Set", TS_nodeID: listName, Activities: activities})
        CREATE (e) -[ecl:E_ABS]-> (l)
        """

    q_link_df = """
        // Push DF from event to list:
        MATCH (e1:Event) -[:DF]-> (e2:Event), (e1) -[:E_ABS]-> (l1), (e2) -[:E_ABS]-> (l2)
        MERGE (l1) -[df:DF_ABS {Activity: e2.Activity}]-> (l2)
        RETURN l1, df, l2
        """

    print(q_classes)
    tx.run(q_classes, k=k)
    print(q_link_df)
    return tx.run(q_link_df, t=f"List-{k}")


def get_node_label_event(name):
    return name[2:7]


def get_dfc_nodes(tx, dot, entity_prefix, entity_name, clusternumber, color, fontcolor):
    q = f'''
        MATCH (l1:TS_node) -[df:DF_ABS]- ()
        return distinct l1
        '''
    print(q)

    dot.attr("node", shape="ellipse", fixedsize="false", width="0.4", height="0.4", fontname="Helvetica", fontsize="8",
             margin="0.05")
    c_entity = Digraph(name="cluster" + str(clusternumber))
    c_entity.attr(rankdir="LR", style="invis")

    for record in tx.run(q):
        l1_id = str(record["l1"].id)
        if record["l1"]["Name"][0:2] == entity_prefix:
            l1_name = ", ".join([ev[2:7] for ev in record["l1"]["Activities"]])
            c_entity.node(l1_id, l1_name, color=color, style="filled", fillcolor=color, fontcolor=fontcolor)

    q = f'''
        MATCH (l1:TS_node)
        WHERE NOT (:TS_node)-[:DF_ABS]->(l1)
        return distinct l1
        '''
    print(q)
    for record in tx.run(q):
        if record["l1"]["Name"][0:2] == entity_prefix:
            l1_id = str(record["l1"].id)
            dot.node(entity_name, entity_name, shape="rectangle", fixedsize="false", color=color, style="filled",
                     fillcolor=color, fontcolor=fontcolor)
            dot.edge(entity_name, l1_id, style="dashed", arrowhead="none", color=color)

    dot.subgraph(c_entity)


def get_dfc_edges(tx, dot, edge_color):
    q = f'''
        MATCH (l1:TS_node) -[df:DF_ABS]-> (l2:TS_node)
        return distinct l1,df,l2
        '''
    print(q)

    dot.attr("node", shape="circle", fixedsize="true", width="0.4", height="0.4", fontname="Helvetica", fontsize="8",
             margin="0")
    dot.attr("edge", fontname="Helvetica", fontsize="8")
    for record in tx.run(q):
        l1_id = str(record["l1"].id)
        l2_id = str(record["l2"].id)
        xlabel = str(record["df"]["Activity"])
        penwidth = 1

        dot.edge(l1_id, l2_id, xlabel=xlabel, fontcolor=edge_color, color=edge_color, penwidth=str(penwidth))

def run(cmd):
    subprocess.run(["powershell", "-Command", cmd])


driver = GraphDatabase.driver(neo4j_address, auth=(username, password))
types = ['list', 'set']

functions = [create_list_df, create_set_df]
if CLI:
    r = input("Input subfolder name")
    abstrs = [int(input("Input abstraction type:\n1: List \n2: Set\n"))]
    ks = [int(input("Input k:\n"))]
else:
    r = input("Input subfolder name")


for abstr in abstrs:
    abstr_name = types[abstr - 1]
    abstr_func = functions[abstr - 1]

    for k in ks:
        print(f"abs: {abstr_name}, k: {k}")
        dot = Digraph(comment='Query Result')
        dot.attr("graph", rankdir="TB", margin="0", compound="true")

        start = timer()

        with driver.session() as session:
            session.write_transaction(reset)
            result = session.write_transaction(abstr_func)
            session.write_transaction(create_start_nodes)
            session.write_transaction(create_end_nodes)
            session.read_transaction(get_dfc_nodes, dot, "A_", "Application", 0, c5_yellow, c_black)
            session.read_transaction(get_dfc_nodes, dot, "W_", "Workflow", 1, c5_medium_blue, c_black)
            session.read_transaction(get_dfc_nodes, dot, "O_", "Offer", 2, c5_orange, c_black)
            session.read_transaction(get_dfc_edges, dot, "#555555")

        end = timer()

        # print(dot.source)
        print(f"Execution time: {end - start} seconds")
        filename_dot = f"./{abstr_name}{k}/{r}/ts_{abstr_name.lower()}_{k}.dot"
        filename_time = f"./{abstr_name}{k}/{r}/ts_{abstr_name.lower()}_{k}_time.txt"
        os.makedirs(os.path.dirname(filename_dot), exist_ok=True)
        os.makedirs(os.path.dirname(filename_time), exist_ok=True)

        with open(filename_dot, "w") as file:
            file.write(dot.source)

        with open(filename_time, "w") as file:
            file.write(f"{end - start} seconds")

        if DOT:
            run(f"cd .\\{abstr_name}{k}\\{r}; rm {abstr_name}_{k}*.png; ccomps -x .\\ts_{abstr_name}_{k}.dot | dot -Grankdir=TB -Tpng -O; mv noname.gv.png {abstr_name}_{k}_A.png; mv noname.gv.2.png {abstr_name}_{k}_W.png; mv noname.gv.3.png {abstr_name}_{k}_O.png")
