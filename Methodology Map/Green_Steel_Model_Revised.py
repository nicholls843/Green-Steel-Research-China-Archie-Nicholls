import os
from graphviz import Digraph

# Graphviz binary path
os.environ["PATH"] += os.pathsep + r"C:\\Users\\archi\\Methodology\\Graphviz\\bin"

# Folder containing icons
icon_folder = r"C:/Users/archi/Methodology/Icons"

# ===================== MAIN DIAGRAM =====================
dot = Digraph(comment='Green Hydrogen-Based Steel Production Model')
dot.attr(rankdir='TB', fontname='Helvetica', nodesep='1', ranksep='1.2')

# Helper function
def add_html_box_node(graph, name, label, icon_filename, bgcolor):
    icon_path = f"{icon_folder}/{icon_filename}".replace('\\', '/')

    # Special case for Scrap Scenarios to fix indentation
    if name == 'sc1':
        graph.node(name, f"""<
            <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="4" CELLPADDING="6" BGCOLOR="{bgcolor}" STYLE="rounded">
                <TR><TD FIXEDSIZE="TRUE" WIDTH="90" HEIGHT="90"><IMG SRC="{icon_path}" SCALE="TRUE"/></TD></TR>
                <TR><TD><FONT FACE="Helvetica" POINT-SIZE="24"><B>Scrap Scenarios</B></FONT></TD></TR>
                <TR><TD><FONT FACE="Helvetica" POINT-SIZE="20"><B>S1: 0%</B></FONT></TD></TR>
                <TR><TD><FONT FACE="Helvetica" POINT-SIZE="20"><B>S2: 25%</B></FONT></TD></TR>
                <TR><TD><FONT FACE="Helvetica" POINT-SIZE="20"><B>S3: 50%</B></FONT></TD></TR>
            </TABLE>
        >""", shape='none')

    else:
        safe_label = label.replace('&', '&amp;').replace('CO₂', 'CO&#8322;').replace('\n', '<BR ALIGN="LEFT"/>')
        graph.node(name, f"""<
            <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="4" CELLPADDING="6" BGCOLOR="{bgcolor}" STYLE="rounded">
                <TR><TD FIXEDSIZE="TRUE" WIDTH="90" HEIGHT="90"><IMG SRC="{icon_path}" SCALE="TRUE"/></TD></TR>
                <TR><TD><FONT FACE="Helvetica" POINT-SIZE="24"><B>{safe_label}</B></FONT></TD></TR>
            </TABLE>
        >""", shape='none')

# ===================== GENERAL INPUTS =====================
with dot.subgraph(name='cluster_general_inputs') as s:
    s.attr(label='General Inputs', fontname='Helvetica', style='dashed', fontsize='26', rank='same')
    add_html_box_node(s, 'inp1', 'China Cost Inputs\n(Equipment, Labour, Materials)', 'workers.png', '#E0E0E0')
    add_html_box_node(s, 'inp3', 'Ore Characteristics\n(Grade, Scrap Share)', 'Iron ore.png', '#E0E0E0')
    add_html_box_node(s, 'inp4', 'Technology Performance\n(Efficiencies & Limits)', 'efficiency.png', '#E0E0E0')
    add_html_box_node(s, 'inp5', 'Financial Assumptions\n(Discount Rate, CRF)', 'discount.png', '#E0E0E0')

# ===================== LOCATION-SPECIFIC INPUTS =====================
with dot.subgraph(name='cluster_location_inputs') as s:
    s.attr(label='Location-Specific Inputs', fontname='Helvetica', style='dashed', fontsize='26', rank='same')
    add_html_box_node(s, 'inp2', 'Renewable Energy Data\n(Renewables.ninja)', 'solar-energy.png', '#DCEEFF')
    add_html_box_node(s, 'inp6', 'Geographic Scope\n(Green Steel Cities in China)', 'china.png', '#DCEEFF')
    add_html_box_node(s, 'inp7', 'Variable Transport Costs\n(Province-Based)', 'transport.png', '#DCEEFF')

# ===================== SCENARIO INPUTS =====================
with dot.subgraph(name='cluster_scenarios') as s:
    s.attr(label='Scenario Inputs', fontname='Helvetica', style='dashed', fontsize='26', rank='same')
    add_html_box_node(s, 'sc1', 'Scrap Scenarios\nS1: 0%\nS2: 25%\nS3: 50%', 'scrap.png', '#FFD8B1')
    add_html_box_node(s, 'sc2', 'Timeframes\nYCurrent, Y2030, Y2040, Y2050', 'time.png', '#FFD8B1')

# ===================== CORE MODEL =====================
add_html_box_node(dot, 'mod1', 'Model Framework\n(Inputs, Variables, Constraints)', 'code.png', '#FFFACD')
add_html_box_node(dot, 'mod2', 'Energy Supply Model\n(RE, Grid Use, Curtailment)', 'wind-farm.png', '#FFFACD')
add_html_box_node(dot, 'mod3', 'Hydrogen Model\n(Production, Storage, Use)', 'hydrogen.png', '#FFFACD')
add_html_box_node(dot, 'mod4', 'Material Flow Model\n(Iron Inputs, Steel Output)', 'iron-ore-pellets.png', '#FFFACD')
add_html_box_node(dot, 'mod5', 'Energy Storage Model\n(Batteries, Hydrogen Storage)', 'battery.png', '#FFFACD')
add_html_box_node(dot, 'mod6', 'Technical Limits\n(Capacity Constraints)', 'Capacity.png', '#FFFACD')

# ===================== SOLVER =====================
add_html_box_node(dot, 'solver', 'Solver\n(Pyomo + GUROBI)', 'problem-solving.png', '#D9EAD3')

# ===================== OUTPUTS =====================
with dot.subgraph() as s:
    s.attr(rank='same')
    add_html_box_node(s, 'out1', 'Levelised Costs\n(Steel, Hydrogen, Electricity)', 'Cost calculation.png', '#AED9E0')
    add_html_box_node(s, 'out2', 'Hydrogen Use per Tonne\nof Steel Produced', 'steel.png', '#AED9E0')
    add_html_box_node(s, 'out3', 'Energy Mix\n(RE, Grid, Curtailment)', 'electricity.png', '#AED9E0')
    add_html_box_node(s, 'out4', 'Installed Capacity\n(Solar, Wind, Electrolysers)', 'electrolyser.png', '#AED9E0')
    add_html_box_node(s, 'out5a', 'CO2 Emissions', 'Co2.png', '#AED9E0')
    add_html_box_node(s, 'out5b', 'Land Requirements', 'land.png', '#AED9E0')
    add_html_box_node(s, 'out6', 'Economic Outputs\n(CAPEX, OPEX, LCOS)', 'Cost calculation.png', '#AED9E0')

# ===================== CONNECTIONS =====================
# Connect all input nodes to core model
for input_node in ['inp1', 'inp2', 'inp3', 'inp4', 'inp5', 'inp6', 'inp7', 'sc1', 'sc2']:
    dot.edge(input_node, 'mod1')

# Connect model components to solver
for mod_node in ['mod1', 'mod2', 'mod3', 'mod4', 'mod5', 'mod6']:
    dot.edge(mod_node, 'solver')

# Internal model structure
dot.edge('mod1', 'mod2')
dot.edge('mod1', 'mod3')
dot.edge('mod1', 'mod4')
dot.edge('mod1', 'mod5')
dot.edge('mod1', 'mod6')

# Solver to outputs
for out_node in ['out1', 'out2', 'out3', 'out4', 'out5a', 'out5b', 'out6']:
    dot.edge('solver', out_node)

# ===================== RENDER MAIN DIAGRAM =====================
dot.render('green_steel_model_icon_boxes_location_category', format='png', cleanup=True)
# dot.render('green_steel_model_icon_boxes_location_category', format='svg', cleanup=True)

# ===================== LEGEND ONLY PNG =====================
legend_only = Digraph(name='LegendOnly')
legend_only.attr(rankdir='TB', fontname='Helvetica')  # Top to bottom layout

def legend_entry_only(name, color, label):
    legend_only.node(name, f"""<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" BGCOLOR="{color}">
            <TR><TD><FONT FACE="Helvetica" POINT-SIZE="14"><B>{label}</B></FONT></TD></TR>
        </TABLE>
    >""", shape='none')

legend_entry_only('leg_inp', '#E0E0E0', 'General Input')
legend_entry_only('leg_loc', '#DCEEFF', 'Location-Specific Input')
legend_entry_only('leg_scenario', '#FFD8B1', 'Scenario Input')
legend_entry_only('leg_mod', '#FFFACD', 'Model Component')
legend_entry_only('leg_sol', '#D9EAD3', 'Solver')
legend_entry_only('leg_out', '#AED9E0', 'Output')

legend_only.render('green_steel_model_legend_only_vertical', format='png', cleanup=True)
# legend_only.render('green_steel_model_legend_only', format='svg', cleanup=True)