from graphviz import Digraph 

dot = Digraph('GreenSteelSystem', format='png')
dot.attr(rankdir='LR')
dot.attr('node', shape='box', style='filled', fillcolor='lightgrey')

# Input resources
dot.node('Solar', '☀️ Solar PV')
dot.node('Wind', '🌬️ Wind')
dot.node('Grid', '🔌 Grid Import')
dot.node('Water', '💧 Water')
dot.node('Ore', '⛏️ ROM Ore')
dot.node('Scrap', '♻️ Scrap')

# Energy system
dot.node('Battery', '🔋 Battery Storage')
dot.node('Electrolyser', '⚡ Electrolyser')
dot.node('FC', '🔄 Fuel Cell')

# Hydrogen subsystem
dot.node('H2_Direct', '➡️ H₂ (Direct Use)')
dot.node('H2Compress', '🧯 Compressor')
dot.node('H2Storage', '🛢️ CGH₂ Storage')
dot.node('H2Heat', '🔥 H₂ Heating')

# Ironmaking and steelmaking
dot.node('DRI', '🏭 DRI Plant')
dot.node('EAF', '🔥 EAF')
dot.node('Steel', '🔩 Liquid Steel')
dot.node('Caster', '🏗️ Continuous Caster')
dot.node('FinalProduct', '📦 Solid Steel Product')

# Outputs and impacts
dot.node('Emissions', '🌍 CO₂ Emissions')
dot.node('Land', '🌾 Land Use')

# Connections
dot.edges([
    # Energy generation
    ('Solar', 'Electrolyser'), 
    ('Wind', 'Electrolyser'), 
    ('Solar', 'Battery'), 
    ('Wind', 'Battery'),
    ('Battery', 'Electrolyser'), 
    ('Grid', 'Electrolyser'), 
    ('Water', 'Electrolyser'),

    # Hydrogen pathways
    ('Electrolyser', 'H2_Direct'),
    ('Electrolyser', 'H2Compress'),
    ('H2_Direct', 'DRI'),
    ('H2Compress', 'H2Storage'),
    ('H2Storage', 'FC'),
    ('H2Storage', 'H2Heat'),
    ('H2Heat', 'DRI'),

    # Material and thermal flows
    ('Ore', 'DRI'),
    ('DRI', 'EAF'),
    ('Scrap', 'EAF'),
    ('EAF', 'Steel'),
    ('Steel', 'Caster'),
    ('Caster', 'FinalProduct'),

    # Outputs and impacts
    ('EAF', 'Emissions'), 
    ('Solar', 'Land'), 
    ('Wind', 'Land')
])

# Render diagram
dot.render('GreenSteelSystem', view=True)