from neo4j import GraphDatabase
from graphviz import Digraph

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
    q_reset = ["MATCH ()-[r:DF_LI]->() DELETE r",
               "MATCH ()-[r:E_LI]->() DELETE r",
               "MATCH (l:TS_node) DELETE l"]

    for q in q_reset:
        print(q)
        tx.run(q)


def create_list_df(tx):
    q_classes = """ 
        // EVENT TO LIST:
        MATCH (e:Event)
        MATCH path=(e_first:Event) -[:DF*0..]-> (e)
        // Check path length here so we can use parameter
        WHERE length(path)  <= $k-1  AND ((NOT ()-[:DF]->(e_first)) OR size(relationships(path)) = $k-1)
        UNWIND nodes(path) as n
        WITH collect(n.Activity) AS events, path, e 
        WITH path, REDUCE(s = HEAD(events), n IN TAIL(events) | s + '-' + n) AS listName, e, events
        MERGE ( l:TS_node { Name:e.Activity, Type:"Activity_Past_" + $k + "_List", TS_nodeID: listName, Events: events})
        CREATE (e) -[ecl:E_LI]-> (l)
        """

    q_link_df = """
        // Push DF from event to list:
        MATCH (e1:Event) -[:DF]-> (e2:Event), (e1) -[:E_LI]-> (l1), (e2) -[:E_LI]-> (l2)
        MERGE (l1) -[df:DF_LI {Activity: e2.Activity}]-> (l2)
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
        UNWIND nodes(path) as n
        WITH n, path, e, e_first ORDER BY n.Activity
        WITH collect(distinct n.Activity) AS events, path, e, e_first
        WHERE size(events) <= $k AND ((NOT ()-[:DF]->(e_first)) OR size(events) = $k)
        WITH path, REDUCE(s = HEAD(events), n IN TAIL(events) | s + '-' + n) AS listName, e, events
        MERGE ( l:TS_node { Name:events[0], Type:"Activity_Past_" + $k + "_Set", TS_nodeID: listName, Events: events})
        CREATE (e) -[ecl:E_LI]-> (l)
        """

    q_link_df = """
        // Push DF from event to list:
        MATCH (e1:Event) -[:DF]-> (e2:Event), (e1) -[:E_LI]-> (l1), (e2) -[:E_LI]-> (l2)
        MERGE (l1) -[df:DF_LI {Activity: e2.Activity}]-> (l2)
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
        MATCH (l1:TS_node) -[df:DF_LI]- ()
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
            l1_name = ", ".join([ev[2:6] for ev in record["l1"]["Events"]])
            c_entity.node(l1_id, l1_name, color=color, style="filled", fillcolor=color, fontcolor=fontcolor)

    q = f'''
        MATCH (l1:TS_node)
        WHERE NOT (:TS_node)-[:DF_LI]->(l1)
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
        MATCH (l1:TS_node) -[df:DF_LI]-> (l2:TS_node)
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


driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1234"))
types = ['list', 'set']

functions = [create_list_df, create_set_df]
print("Input abstraction type:\n1: List \n2: Set")
type = int(input())


abstr_name = types[type-1]
abstr_func = functions[type-1]

print(f"Selected abstraction: {abstr_name}")
print("Input k:")
k = int(input())

dot = Digraph(comment='Query Result')
dot.attr("graph", rankdir="LR", margin="0", compound="true")

with driver.session() as session:
    session.write_transaction(reset)
    result = session.write_transaction(abstr_func)
    session.read_transaction(get_dfc_nodes, dot, "A_", "Application", 0, c5_yellow, c_black)
    session.read_transaction(get_dfc_nodes, dot, "W_", "Workflow", 1, c5_medium_blue, c_black)
    session.read_transaction(get_dfc_nodes, dot, "O_", "Offer", 2, c5_orange, c_black)
    session.read_transaction(get_dfc_edges, dot, "#555555")

print(dot.source)
file = open(f"ts_{abstr_name.lower()}_{k}.dot", "w")
file.write(dot.source)
file.close()
