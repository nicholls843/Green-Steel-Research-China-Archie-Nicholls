import pyomo.environ as pyo
from pyomo.environ import *
import pandas as pd

def create_complete_green_steel_model(ycase, scase, ROM_grade_val, f_scrap_val, f_t=1.0, objective='cost'):
    model = pyo.ConcreteModel()
    
    # ======================
    # SET DEFINITIONS 
    # ======================
    model.T = pyo.Set(initialize=range(1, 8761))  # Hours t1*t8760
    
    # Technology years and scrap cases
    model.Ycase = pyo.Set(initialize=[ycase])
    model.Scase = pyo.Set(initialize=[scase])
    
    # RE sources
    model.I = pyo.Set(initialize=['s', 'w'])  # Solar (s) and wind (w)
    
    # Technologies
    model.em_tech = pyo.Set(initialize=['s', 'w', 'bat', 'ely', 'FC'])
    
    # ======================
    # PARAMETERS 
    # ======================
    # Demand parameters
    model.f_t = pyo.Param(mutable=True, initialize=f_t)  # Time factor 
    model.dem_SFS_annual = pyo.Param(mutable=True, initialize=1e6)  # Annual demand for steel (t)
    model.dem_SFS = pyo.Expression(expr=lambda m: m.dem_SFS_annual * m.f_t)  # Scaled demand profile
    model.T_t = 8760  # Total hours
    
    # Ore parameters
    model.ROM_grade = pyo.Param(model.Ycase, initialize={ycase: ROM_grade_val})
    model.f_scrap = pyo.Param(model.Scase, initialize={scase: f_scrap_val})
    model.ore_grade_DRI = 0.67  # Minimum DR-grade ore Fe content
    
    # Mass balances and yields
    model.mass_aly = 0.011  # Alloy mass demand (t/t LS)
    model.mass_eld = 0.002  # Electrode mass demand (t/t LS)
    model.mass_lime = pyo.Param(model.Scase, initialize=lambda m, s: (50 - 20*m.f_scrap[s])/1000)
    model.f_met = pyo.Param(model.Scase, initialize=lambda m, s: 0.0894*m.f_scrap[s] + 0.8483)
    
    # Ore preparation mass losses
    model.mloss_crs = 0.19  # Crushing and screening
    model.mloss_pel = 0.03  # Pelletizing
    model.mloss_con = pyo.Param(model.Ycase, initialize=lambda m, y: 
        0.0268*(m.ore_grade_DRI - m.ROM_grade[y] - 0.01)*100 if m.ROM_grade[y] <= 0.66 else 0.0268*0.01*100)
    
    # Energy consumption parameters (MWh/tonne unless noted)
    model.alpha_drill = 0.00128  # Drilling and blasting
    model.alpha_load = 0.2558  # Loading and hauling
    model.alpha_crs = 0.00642  # Crushing and screening
    model.alpha_com = 0.02736  # Comminution
    model.alpha_con = 0.85  # Concentration (per ∆Fe%)
    model.alpha_pel = 0.20828  # Pelletizing
    model.alpha_stk = 0.00128  # Stacking and reclaiming
    
    model.alpha_cmp2b = 0.065  # 2 bar compressor
    model.alpha_cmp200b = 2.87  # 200 bar compressor
    model.alpha_cmpbr = 0.00632  # Briquette compressor
    model.alpha_DRI = 0.04759  # H2 consumption for DRI (t H2/t DRI)
    model.alpha_H2heat = 0.4461  # H2 heating 
    model.alpha_cst = 0.0103  # Continuous caster
    model.alpha_HBIheat = 152.78  # HBI heating
    model.alpha_CDRIheat = 152.78  # CDRI heating
    model.LHV_H2 = 120000  # MJ per tonne

    # Technology Parameters
    ely_values = {'YCurrent': 51.2, 'Y2030': 49.020, 'Y2040': 46.620, 'Y2050': 44.444}
    FC_values = {'YCurrent': 0.052, 'Y2030': 0.050, 'Y2040': 0.048, 'Y2050': 0.047}
    model.var_alpha_ely = pyo.Param(model.Ycase, initialize={ycase: ely_values[ycase]})
    model.var_alpha_FC = pyo.Param(model.Ycase, initialize={ycase: FC_values[ycase]})
    
    # Efficiencies
    model.eff_el = 0.9  # Electrical heating
    model.eff_th = 0.85  # Thermal heating
    model.eff_inv = 0.95  # Inverter
    model.eff_bat = 0.92  # Battery round-trip
    
    # Economic parameters
    model.r = 0.08  # Discount rate
    model.n = 20  # Project lifetime
    model.f_CR = model.r*(1+model.r)**model.n/((1+model.r)**model.n-1)  # CRF
    model.f_maint = 0.02  # Maintenance factor
    model.rep = 2  # Replacements needed

    # Capacity bounds
    model.max_EAF_capacity = pyo.Param(initialize=500)  # realistic upper bound in t/hour
    
    # Prices ($/tonne)
    model.price_pel = 160 # Pellets
    model.price_lmp = 120 # Lump ore
    model.price_scr = 268  # Scrap
    model.price_lime = 139  # Lime
    model.price_alloys = 2397  # Alloys
    model.price_electrode = 5395  # Electrodes
    model.transport_cost_per_tonne = 3.93 # CHANGE Transport cost per tonne of ore ($/t) 
    model.grid_price = pyo.Param(mutable=True, initialize=100)  # Grid import penalty price ($/MWh)
    
    # Labour costs ($/tonne)
    model.lab_DRI = 13  # Ironmaking labour
    model.lab_EAF_cst = 36  # Steelmaking labour
    
    # Storage parameters
    model.h_bat = 4  # Battery duration (hours)
    
    # Scenario-specific initialization for var_ucost
    ucost_data = {
        's': {'YCurrent': 0.672,'Y2030': 0.562, 'Y2040': 0.503, 'Y2050': 0.415},
        'w': {'YCurrent': 0.986,'Y2030': 0.907, 'Y2040': 0.862, 'Y2050': 0.816},
        'bat': {'YCurrent': 0.655, 'Y2030': 0.594, 'Y2040': 0.569, 'Y2050': 0.552},
        'ely': {'YCurrent': 0.600, 'Y2030': 0.385, 'Y2040': 0.340, 'Y2050': 0.295},
        'FC': {'YCurrent': 0.14, 'Y2030': 0.139, 'Y2040': 0.09, 'Y2050': 0.086},
    }
    model.var_ucost = pyo.Param(
        model.Ycase, model.em_tech,
        initialize={(ycase, tech): ucost_data[tech][ycase] for tech in model.em_tech}
    )
    
    model.VRE_prod = pyo.Param(model.T, model.I, 
                             mutable=True, 
                             default=0.0,
                             doc='Renewable energy production profiles [MW/MW installed]')
    
    # ======================
    # VARIABLES 
    # ======================
   # RE variables
    model.P_RE = pyo.Var(model.T, model.I, within=NonNegativeReals) 
    model.P_RE_surplus = pyo.Var(model.T, within=NonNegativeReals)
    model.P_RE_di_cons = pyo.Var(model.T, within=NonNegativeReals)
    model.P_curtail = pyo.Var(model.T, within=NonNegativeReals)
    model.P_cons = pyo.Var(model.T, within=NonNegativeReals)
    model.P_cons_AC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_cons_DC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_grid_import = pyo.Var(model.T, within=NonNegativeReals)
    
    # Power flow variables
    model.P_w_AC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_w_inv = pyo.Var(model.T, within=NonNegativeReals)
    model.P_w_DC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_s_DC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_s_inv = pyo.Var(model.T, within=NonNegativeReals)
    model.P_s_AC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_bat_DC = pyo.Var(model.T, within=NonNegativeReals)
    model.P_bat_inv = pyo.Var(model.T, within=NonNegativeReals)
    model.P_bat_AC = pyo.Var(model.T, within=NonNegativeReals)
    
    # Battery variables
    model.P_bat = pyo.Var(model.T, within=NonNegativeReals)
    model.L_bat_st = pyo.Var(model.T, within=NonNegativeReals)
    model.Lmax_bat_st = pyo.Var(within=NonNegativeReals)

    # Battery storage peak and valley
    model.L_bat_st_peak = pyo.Var(within=NonNegativeReals)
    model.L_bat_st_valley = pyo.Var(within=NonNegativeReals)
    
    # Hydrogen variables
    model.H2_ely = pyo.Var(model.T, within=NonNegativeReals)
    model.H2_DRI = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.H2_ely_DRI = pyo.Var(model.T, within=NonNegativeReals)
    model.CGH2_in_st = pyo.Var(model.T, within=NonNegativeReals)
    model.CGH2_DRI = pyo.Var(model.T, within=NonNegativeReals)
    model.CGH2_FC = pyo.Var(model.T, within=NonNegativeReals)
    model.CGH2_H2heat = pyo.Var(model.T, within=NonNegativeReals)
    model.L_CGH2_st = pyo.Var(model.T, within=NonNegativeReals)
    model.Lmax_CGH2_st = pyo.Var(within=NonNegativeReals)
    model.En_H2heat = pyo.Var(model.T, model.Scase, within=NonNegativeReals)

    # CGH2 storage peak and valley
    model.L_CGH2_st_peak = pyo.Var(within=NonNegativeReals)
    model.L_CGH2_st_valley = pyo.Var(within=NonNegativeReals)
    
    # Process variables
    model.DRI_out_DRP = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.DRI_in_EAF = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.scr_in_EAF = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.lime_in_EAF = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.aly_in_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.eld_in_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.slag_out_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.LS_out_EAF = pyo.Var(model.T, within=NonNegativeReals)
    
    # Power flows
    model.P_di_ely = pyo.Var(model.T, within=NonNegativeReals)
    model.P_di_H2heat = pyo.Var(model.T, within=NonNegativeReals)
    model.P_di_cmp200b = pyo.Var(model.T, within=NonNegativeReals)
    model.P_cmp2b = pyo.Var(model.T, model.Scase, within=NonNegativeReals)
    model.P_cmpbr = pyo.Var(model.T, within=NonNegativeReals)
    model.P_HBIheat = pyo.Var(model.T, within=NonNegativeReals)
    model.P_CDRIheat = pyo.Var(model.T, within=NonNegativeReals)
    model.P_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.P_cst = pyo.Var(model.T, within=NonNegativeReals)
    model.P_FC = pyo.Var(model.T, within=NonNegativeReals, doc='Power from fuel cells [MWh]')
    model.P_ely_inv = pyo.Var(model.T, within=NonNegativeReals)
    
    # Storage flows
    model.HBI_in_st = pyo.Var(model.T, within=NonNegativeReals)
    model.HBI_in_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.HDRI_in_EAF = pyo.Var(model.T, within=NonNegativeReals)
    model.CDRI_in_st = pyo.Var(model.T, within=NonNegativeReals)
    model.CDRI_in_EAF = pyo.Var(model.T, within=NonNegativeReals)
    
    # Capacity variables
    model.c_RE = pyo.Var(model.I, within=NonNegativeReals)
    model.c_RE_s = pyo.Var(within=NonNegativeReals)
    model.c_RE_w = pyo.Var(within=NonNegativeReals)
    model.c_ely = pyo.Var(within=NonNegativeReals)
    model.c_FC = pyo.Var(within=NonNegativeReals)
    model.c_EAF = pyo.Var(within=NonNegativeReals, bounds=(0, model.max_EAF_capacity))
    model.CGH2_in_st_max = pyo.Var(within=NonNegativeReals)
    model.LS_out_EAF_max = pyo.Var(within=NonNegativeReals)
    
    # Economic variables
    model.CAPEX_s = pyo.Var(model.Ycase, within=NonNegativeReals)
    model.CAPEX_w = pyo.Var(model.Ycase, within=NonNegativeReals)
    model.CAPEX_bat = pyo.Var(model.Ycase, within=NonNegativeReals)
    model.CAPEX_ely = pyo.Var(model.Ycase, within=NonNegativeReals)
    model.CAPEX_FC = pyo.Var(model.Ycase, within=NonNegativeReals)
    model.CAPEX_DRP = pyo.Var(within=NonNegativeReals)
    model.CAPEX_cmp2b = pyo.Var(within=NonNegativeReals)
    model.CAPEX_CGH2 = pyo.Var(within=NonNegativeReals)
    model.CAPEX_EAF = pyo.Var(within=NonNegativeReals)
    model.CAPEX_cst = pyo.Var(within=NonNegativeReals)
    model.T_CAPEX = pyo.Var(within=NonNegativeReals)
    
    model.aCAPEX_s = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_w = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_bat = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_ely = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_FC = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_DRP = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_cmp2b = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_CGH2 = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_EAF = pyo.Var(within=NonNegativeReals)
    model.aCAPEX_cst = pyo.Var(within=NonNegativeReals)
    model.T_aCAPEX = pyo.Var(within=NonNegativeReals)
    
    model.aOPEX_maint = pyo.Var(within=NonNegativeReals)
    model.aOPEX_pel = pyo.Var(within=NonNegativeReals)
    model.aOPEX_lmp = pyo.Var(within=NonNegativeReals)
    model.aOPEX_scr = pyo.Var(within=NonNegativeReals)
    model.aOPEX_lime = pyo.Var(within=NonNegativeReals)
    model.aOPEX_aly = pyo.Var(within=NonNegativeReals)
    model.aOPEX_eld = pyo.Var(within=NonNegativeReals)
    model.aOPEX_labour = pyo.Var(within=NonNegativeReals)
    model.T_aOPEX = pyo.Var(within=NonNegativeReals)
    
    # Total annual flows
    model.T_RE = pyo.Var(within=NonNegativeReals)
    model.T_P_curtail = pyo.Var(within=NonNegativeReals)
    model.T_P_cons = pyo.Var(within=NonNegativeReals)
    model.T_P_ely = pyo.Var(within=NonNegativeReals)
    model.T_P_H2heat = pyo.Var(within=NonNegativeReals)
    model.T_P_cmp2b = pyo.Var(within=NonNegativeReals)
    model.T_P_cmp200b = pyo.Var(within=NonNegativeReals)
    model.T_P_CDRIheat = pyo.Var(within=NonNegativeReals)
    model.T_P_EAF = pyo.Var(within=NonNegativeReals)
    model.T_P_cst = pyo.Var(within=NonNegativeReals)
    model.T_H2 = pyo.Var(within=NonNegativeReals)
    model.T_CGH2 = pyo.Var(within=NonNegativeReals)
    model.T_CGH2_DRI = pyo.Var(within=NonNegativeReals)
    model.T_CGH2_FC = pyo.Var(within=NonNegativeReals)
    model.T_HBI = pyo.Var(within=NonNegativeReals)
    model.T_HDRI = pyo.Var(within=NonNegativeReals)
    model.T_CDRI = pyo.Var(within=NonNegativeReals)
    model.T_P_grid_import = pyo.Var(within=NonNegativeReals)
    model.T_P_FC = pyo.Var(within=NonNegativeReals)
    
    # Split total renewable generation by source
    model.T_RE_solar = pyo.Expression(expr=sum(model.P_RE[t, 's'] for t in model.T))
    model.T_RE_wind  = pyo.Expression(expr=sum(model.P_RE[t, 'w'] for t in model.T))
    
    # Material flow parameters (calculated during initialization)
    model.T_DRI = pyo.Param(model.Scase, mutable=True, default=0)
    model.T_DR_ore = pyo.Param(model.Scase, mutable=True, default=0)
    model.T_DR_pel = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.T_DR_lmp = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.T_scr = pyo.Param(model.Scase, mutable=True, default=0)
    model.T_lime = pyo.Param(model.Scase, mutable=True, default=0)
    model.T_aly = pyo.Param(mutable=True, default=0)
    model.T_eld = pyo.Param(mutable=True, default=0)

    # Ore subsystem material balances
    model.T_fines_in_pel = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.T_ore_in_ben = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.T_ore_out_crs = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.T_ore_ROM = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    
    # Energy consumption parameters
    model.T_En_ore = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.alpha_EAF = pyo.Param(model.Scase, mutable=True, default=0)

    # Ore subsystem energy breakdown
    model.En_mng = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_crs = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_com = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_con = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_pel = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_stkp = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)
    model.P_stkl = pyo.Param(model.Ycase, model.Scase, mutable=True, default=0)

    
    # ======================
    # EQUATIONS 
    # ======================
    
    # 1. ENERGY CONSUMPTION EQUATIONS
    def rule_P_cons1(m, t, s):
        return m.P_cmp2b[t,s] == m.alpha_cmp2b * m.DRI_out_DRP[t,s]
    model.P_cons1 = pyo.Constraint(model.T, model.Scase, rule=rule_P_cons1)
    
    def rule_P_cons2(m, t, y):
        return m.P_di_ely[t] == m.var_alpha_ely[y] * m.H2_ely[t]
    model.P_cons2 = pyo.Constraint(model.T, model.Ycase, rule=rule_P_cons2)
    
    def rule_P_cons3(m, t):
        return m.P_di_cmp200b[t] == m.alpha_cmp200b * m.CGH2_in_st[t]
    model.P_cons3 = pyo.Constraint(model.T, rule=rule_P_cons3)
    
    def rule_P_cons4(m, t):
        return m.P_cmpbr[t] == m.alpha_cmpbr * m.HBI_in_st[t]
    model.P_cons4 = pyo.Constraint(model.T, rule=rule_P_cons4)
    
    def rule_P_cons5(m, t):
        return m.P_HBIheat[t] == m.alpha_HBIheat * m.HBI_in_EAF[t]
    model.P_cons5 = pyo.Constraint(model.T, rule=rule_P_cons5)
    
    def rule_P_cons6(m, t):
        return m.P_CDRIheat[t] == m.alpha_CDRIheat * m.CDRI_in_EAF[t]
    model.P_cons6 = pyo.Constraint(model.T, rule=rule_P_cons6)
    
    def rule_P_cons7(m, t):
        return m.P_cst[t] == m.alpha_cst * m.LS_out_EAF[t]
    model.P_cons7 = pyo.Constraint(model.T, rule=rule_P_cons7)
    
    def rule_H2_cons1(m, t, y):
        return m.CGH2_FC[t] == m.var_alpha_FC[y] * m.P_FC[t] / m.eff_inv
    model.H2_cons1 = pyo.Constraint(model.T, model.Ycase, rule=rule_H2_cons1)
    
    def rule_H2_cons2(m, t, s):
        return m.H2_DRI[t,s] == m.alpha_DRI * m.DRI_out_DRP[t,s]
    model.H2_cons2 = pyo.Constraint(model.T, model.Scase, rule=rule_H2_cons2)
    
    def rule_En_cons1(m, t, s):
        return m.En_H2heat[t,s] == m.alpha_H2heat * m.DRI_out_DRP[t,s]
    model.En_cons1 = pyo.Constraint(model.T, model.Scase, rule=rule_En_cons1)

    def rule_H2Heat_Supply(m, t, s):
        return m.En_H2heat[t,s] == m.CGH2_H2heat[t] * m.LHV_H2 + m.P_di_H2heat[t] * 3600
    model.H2Heat_Supply = pyo.Constraint(model.T, model.Scase, rule=rule_H2Heat_Supply)
    
    # 2. ENERGY BALANCE EQUATIONS

    def rule_P_RE_balance_strict(m, t):
        return sum(m.P_RE[t,i] for i in m.I) == m.P_RE_di_cons[t]
    model.P_RE_balance_strict = pyo.Constraint(model.T, rule=rule_P_RE_balance_strict)
    
    def rule_P_Sum1(m, t):
        return m.P_cons[t] == m.P_cons_AC[t] + m.P_cons_DC[t]
    model.P_Sum1 = pyo.Constraint(model.T, rule=rule_P_Sum1)
    
    def rule_P_Balance_AC1(m, t):
        return m.P_cons_AC[t] == (
        m.P_w_AC[t]
        + m.P_s_AC[t]
        + m.P_FC[t]
        + m.P_bat_AC[t]
        + m.P_grid_import[t]
    )
    model.P_Balance_AC1 = pyo.Constraint(model.T, rule=rule_P_Balance_AC1)
    
    def rule_P_Balance_AC2(m, t):
        return m.P_cons_AC[t] == (
        m.P_di_cmp200b[t]
        + m.P_di_H2heat[t]
        + sum(m.P_cmp2b[t,s] for s in m.Scase)
        + m.P_cmpbr[t]
        + m.P_HBIheat[t]
        + m.P_CDRIheat[t]
        + m.P_EAF[t]
        + m.P_cst[t]
        + m.P_ely_inv[t]
    )

    model.P_Balance_AC2 = pyo.Constraint(model.T, rule=rule_P_Balance_AC2)
    
    def rule_P_Balance_DC1(m, t):
        return m.P_cons_DC[t] == m.P_w_DC[t] + m.P_s_DC[t] + m.P_bat_DC[t]
    model.P_Balance_DC1 = pyo.Constraint(model.T, rule=rule_P_Balance_DC1)
    
    def rule_P_Balance_DC2(m, t):
        return m.P_cons_DC[t] == m.P_di_ely[t]
    model.P_Balance_DC2 = pyo.Constraint(model.T, rule=rule_P_Balance_DC2)

    def rule_ely_power_source_strict(m, t):
        return m.P_di_ely[t] == m.P_w_DC[t] + m.P_s_DC[t] + m.P_bat_DC[t] + m.P_FC[t]
    model.ely_power_source_strict = pyo.Constraint(model.T, rule=rule_ely_power_source_strict)

    def rule_total_H2_balance(m):
        return sum(m.H2_ely[t] for t in m.T) == (
        sum(m.CGH2_in_st[t] for t in m.T)
        + sum(m.H2_DRI[t,s] for t in m.T for s in m.Scase)
    )
    model.total_H2_balance = pyo.Constraint(rule=rule_total_H2_balance)

    def rule_RE_dispatch_limit(m, t, i):
        return m.P_RE[t,i] == m.VRE_prod[t,i] * m.c_RE[i]
    model.RE_dispatch_limit = pyo.Constraint(model.T, model.I, rule=rule_RE_dispatch_limit)

    def rule_hourly_power_balance(m, t):
        return (
        sum(m.P_RE[t,i] for i in m.I)
        + m.P_bat_inv[t]
        + m.P_FC[t]
        + m.P_grid_import[t]
        == m.P_cons_AC[t] + m.P_cons_DC[t]
    )
    model.hourly_power_balance = pyo.Constraint(model.T, rule=rule_hourly_power_balance)

    # --- Inverter Power Conversion Constraints ---
    def rule_inv_s(m, t):
        return m.P_s_inv[t] == m.P_s_AC[t] / m.eff_inv
    model.inv_s = pyo.Constraint(model.T, rule=rule_inv_s)

    def rule_inv_w(m, t):
        return m.P_w_inv[t] == m.P_w_DC[t] / m.eff_inv
    model.inv_w = pyo.Constraint(model.T, rule=rule_inv_w)

    def rule_inv_bat(m, t):
        return m.P_bat_inv[t] == m.P_bat_AC[t] / m.eff_inv
    model.inv_bat = pyo.Constraint(model.T, rule=rule_inv_bat)

    def rule_inv_ely(m, t):
        return m.P_ely_inv[t] == m.P_di_ely[t] / m.eff_inv
    model.inv_ely = pyo.Constraint(model.T, rule=rule_inv_ely)

    # 3. MASS BALANCE EQUATIONS
    def rule_EAF_in_out(m, t, s):
        return (m.DRI_in_EAF[t,s] + m.scr_in_EAF[t,s] + m.lime_in_EAF[t,s] + 
                m.aly_in_EAF[t] + m.eld_in_EAF[t] == 
                m.LS_out_EAF[t] + m.slag_out_EAF[t])
    model.EAF_in_out = pyo.Constraint(model.T, model.Scase, rule=rule_EAF_in_out)
    
    def rule_flow_DRI_scr1(m, t, s):
        return m.DRI_in_EAF[t,s] == (((m.LS_out_EAF[t] - m.aly_in_EAF[t])/
                                    m.f_met[s]) - m.scr_in_EAF[t,s])/0.93
    model.flow_DRI_scr1 = pyo.Constraint(model.T, model.Scase, rule=rule_flow_DRI_scr1)
    
    def rule_flow_DRI_scr2(m, t, s):
        if abs(1 - m.f_scrap[s]) < 1e-6:
            return pyo.Constraint.Skip
        return m.scr_in_EAF[t,s] == m.DRI_in_EAF[t,s] * m.f_scrap[s]/(1 - m.f_scrap[s])
    model.flow_DRI_scr2 = pyo.Constraint(model.T, model.Scase, rule=rule_flow_DRI_scr2)
    
    def rule_flow_lime(m, t, s):
        return m.lime_in_EAF[t,s] == m.mass_lime[s] * m.LS_out_EAF[t]
    model.flow_lime = pyo.Constraint(model.T, model.Scase, rule=rule_flow_lime)
    
    def rule_flow_aly(m, t):
        return m.aly_in_EAF[t] == m.mass_aly * m.LS_out_EAF[t]
    model.flow_aly = pyo.Constraint(model.T, rule=rule_flow_aly)
    
    def rule_DRI_split1(m, t, s):
        return m.DRI_out_DRP[t,s] == m.HBI_in_st[t] + m.CDRI_in_st[t] + m.HDRI_in_EAF[t]
    model.DRI_split1 = pyo.Constraint(model.T, model.Scase, rule=rule_DRI_split1)
    
    def rule_DRI_split2(m, t, s):
        return m.DRI_in_EAF[t,s] == m.HBI_in_EAF[t] + m.CDRI_in_EAF[t] + m.HDRI_in_EAF[t]
    model.DRI_split2 = pyo.Constraint(model.T, model.Scase, rule=rule_DRI_split2)
    
    def rule_DRI_cons(m):
        return sum(m.DRI_out_DRP[t,s] for t in m.T for s in m.Scase) == \
               sum(m.DRI_in_EAF[t,s] for t in m.T for s in m.Scase)
    model.DRI_cons = pyo.Constraint(rule=rule_DRI_cons)

    def rule_Stop_HBI(m, t):
        return m.HBI_in_EAF[t] == 0
    model.Stop_HBI = pyo.Constraint(model.T, rule=rule_Stop_HBI)

    # 4. STORAGE DYNAMICS

    def rule_bat_t1(m):
        return m.L_bat_st[1] == (m.P_w_inv[1] + m.P_s_inv[1])*m.eff_bat - (m.P_bat[1]/m.eff_bat)
    model.bat_t1 = pyo.Constraint(rule=rule_bat_t1)

    def rule_bat_mb(m, t):
        if t >= 2:
            return m.L_bat_st[t] == m.L_bat_st[t-1] + (m.P_w_inv[t] + m.P_s_inv[t])*m.eff_bat - (m.P_bat[t]/m.eff_bat)
        return pyo.Constraint.Skip
    model.bat_mb = pyo.Constraint(model.T, rule=rule_bat_mb)
    
    def rule_CGH2_t1(m):
        return m.L_CGH2_st[1] == m.CGH2_in_st[1] - m.CGH2_DRI[1] - m.CGH2_FC[1] - m.CGH2_H2heat[1]
    model.CGH2_t1 = pyo.Constraint(rule=rule_CGH2_t1)
    
    def rule_CGH2_mb(m, t):
        if t >= 2:
            return m.L_CGH2_st[t] == m.L_CGH2_st[t-1] + m.CGH2_in_st[t] - m.CGH2_DRI[t] - m.CGH2_FC[t] - m.CGH2_H2heat[t]
        return pyo.Constraint.Skip
    model.CGH2_mb = pyo.Constraint(model.T, rule=rule_CGH2_mb)

    def rule_bat_st_lower(m, t):
            return m.L_bat_st_valley <= m.L_bat_st[t]
    model.bat_st_lower = pyo.Constraint(model.T, rule=rule_bat_st_lower)

    def rule_bat_st_upper(m, t):
            return m.L_bat_st[t] <= m.L_bat_st_peak
    model.bat_st_upper = pyo.Constraint(model.T, rule=rule_bat_st_upper)

    def rule_CGH2_st_lower(m, t):
            return m.L_CGH2_st_valley <= m.L_CGH2_st[t]
    model.CGH2_st_lower = pyo.Constraint(model.T, rule=rule_CGH2_st_lower)

    def rule_CGH2_st_upper(m, t):
            return m.L_CGH2_st[t] <= m.L_CGH2_st_peak
    model.CGH2_st_upper = pyo.Constraint(model.T, rule=rule_CGH2_st_upper)

    def rule_bat_capacity(m):
        return m.Lmax_bat_st == m.L_bat_st_peak - m.L_bat_st_valley
    model.bat_capacity = pyo.Constraint(rule=rule_bat_capacity)

    def rule_CGH2_capacity(m):
        return m.Lmax_CGH2_st == m.L_CGH2_st_peak - m.L_CGH2_st_valley
    model.CGH2_capacity = pyo.Constraint(rule=rule_CGH2_capacity)
    
    # 5. CAPACITY CONSTRAINTS
    def rule_maxH2_ely(m, t, y):
        return m.H2_ely[t]*m.var_alpha_ely[y] <= m.c_ely
    model.maxH2_ely = pyo.Constraint(model.T, model.Ycase, rule=rule_maxH2_ely)
    
    def rule_maxH2_FC(m, t, y):
        return m.CGH2_FC[t] <= m.c_FC*m.var_alpha_FC[y]
    model.maxH2_FC = pyo.Constraint(model.T, model.Ycase, rule=rule_maxH2_FC)
    
    def rule_maxH2_CGH2(m, t):
        return m.CGH2_in_st[t] <= m.CGH2_in_st_max
    model.maxH2_CGH2 = pyo.Constraint(model.T, rule=rule_maxH2_CGH2)
    
    def rule_maxLS(m, t):
        return m.LS_out_EAF[t] <= m.LS_out_EAF_max
    model.maxLS = pyo.Constraint(model.T, rule=rule_maxLS)

    def rule_EAF_capacity_link(m):
        return m.LS_out_EAF_max <= m.c_EAF
    model.EAF_capacity_link = pyo.Constraint(rule=rule_EAF_capacity_link)    
    
    def rule_max_s(m):
        return m.c_RE_s == m.c_RE['s']
    model.max_s = pyo.Constraint(rule=rule_max_s)
    
    def rule_max_w(m):
        return m.c_RE_w == m.c_RE['w']
    model.max_w = pyo.Constraint(rule=rule_max_w)

    # 6. TOTAL ANNUAL FLOWS
    def rule_tp1(m):
        return m.T_RE == sum(m.P_RE[t,i] for t in m.T for i in m.I)
    model.tp1 = pyo.Constraint(rule=rule_tp1)
    
    def rule_tp2(m):
        return m.T_P_curtail == sum(m.P_curtail[t] for t in m.T)
    model.tp2 = pyo.Constraint(rule=rule_tp2)
    
    def rule_tp3(m):
        return m.T_P_cons == sum(m.P_cons[t] for t in m.T)
    model.tp3 = pyo.Constraint(rule=rule_tp3)
    
    def rule_tp4(m):
        return m.T_P_ely == sum(m.P_di_ely[t] for t in m.T)
    model.tp4 = pyo.Constraint(rule=rule_tp4)

    def rule_tp_FC(m):
        return m.T_P_FC == sum(m.P_FC[t] for t in m.T)
    model.tp_FC = pyo.Constraint(rule=rule_tp_FC)
 
    def rule_tp5(m):
        return m.T_P_H2heat == sum(m.P_di_H2heat[t] for t in m.T)
    model.tp5 = pyo.Constraint(rule=rule_tp5)
    
    def rule_tp6(m):
        return m.T_P_cmp2b == sum(m.P_cmp2b[t,s] for t in m.T for s in m.Scase)
    model.tp6 = pyo.Constraint(rule=rule_tp6)
    
    def rule_tp7(m):
        return m.T_P_cmp200b == sum(m.P_di_cmp200b[t] for t in m.T)
    model.tp7 = pyo.Constraint(rule=rule_tp7)
    
    def rule_tp8(m):
        return m.T_P_CDRIheat == sum(m.P_CDRIheat[t] for t in m.T)
    model.tp8 = pyo.Constraint(rule=rule_tp8)
    
    def rule_tp9(m):
        return m.T_P_EAF == sum(m.P_EAF[t] for t in m.T)
    model.tp9 = pyo.Constraint(rule=rule_tp9)
    
    def rule_tp10(m):
        return m.T_P_cst == sum(m.P_cst[t] for t in m.T)
    model.tp10 = pyo.Constraint(rule=rule_tp10)
    
    def rule_mp1(m):
        return m.T_H2 == sum(m.H2_ely[t] for t in m.T)
    model.mp1 = pyo.Constraint(rule=rule_mp1)
    
    def rule_mp2(m):
        return m.T_CGH2 == sum(m.CGH2_in_st[t] for t in m.T)
    model.mp2 = pyo.Constraint(rule=rule_mp2)
    
    def rule_mp3(m):
        return m.T_CGH2_DRI == sum(m.CGH2_DRI[t] for t in m.T)
    model.mp3 = pyo.Constraint(rule=rule_mp3)
    
    def rule_mp4(m):
        return m.T_CGH2_FC == sum(m.CGH2_FC[t] for t in m.T)
    model.mp4 = pyo.Constraint(rule=rule_mp4)
    
    def rule_mp5(m):
        return m.T_HBI == sum(m.HBI_in_EAF[t] for t in m.T)
    model.mp5 = pyo.Constraint(rule=rule_mp5)
    
    def rule_mp6(m):
        return m.T_HDRI == sum(m.HDRI_in_EAF[t] for t in m.T)
    model.mp6 = pyo.Constraint(rule=rule_mp6)
    
    def rule_mp7(m):
        return m.T_CDRI == sum(m.CDRI_in_EAF[t] for t in m.T)
    model.mp7 = pyo.Constraint(rule=rule_mp7)

    def rule_total_grid_import(m):
        return m.T_P_grid_import == sum(m.P_grid_import[t] for t in m.T)
    model.total_grid_import = pyo.Constraint(rule=rule_total_grid_import)

    # 6A. ANNUAL BALANCE CONSTRAINTS

    def rule_CGH2_annual(m):
        return sum(m.CGH2_in_st[t] for t in m.T) == \
           sum(m.CGH2_DRI[t] + m.CGH2_FC[t] + m.CGH2_H2heat[t] for t in m.T)
    model.CGH2_annual = pyo.Constraint(rule=rule_CGH2_annual)

    def rule_CDRI_annual(m):
        return sum(m.CDRI_in_st[t] for t in m.T) == \
           sum(m.CDRI_in_EAF[t] for t in m.T)
    model.CDRI_annual = pyo.Constraint(rule=rule_CDRI_annual)

    def rule_demand_constraint(m):
        return sum(m.LS_out_EAF[t] for t in m.T) == m.dem_SFS
    model.demand_constraint = pyo.Constraint(rule=rule_demand_constraint)

    def rule_annual_scrap_ratio(m, s):
        return sum(m.scr_in_EAF[t,s] for t in m.T) == sum(m.DRI_in_EAF[t,s] for t in m.T) * m.f_scrap[s]/(1 - m.f_scrap[s])
    model.annual_scrap_ratio = pyo.Constraint(model.Scase, rule=rule_annual_scrap_ratio)

    def rule_renewable_share(m):
        return m.T_RE >= 1.0 * (m.T_P_cons + m.T_P_grid_import)
    model.renewable_share = pyo.Constraint(rule=rule_renewable_share)

    # ==== Transport cost expressions ====

    # Total ore tonnes purchased (ROM ore)
    def total_ore_demand_rule(m):
        return sum(m.T_ore_ROM[y, s] for y in m.Ycase for s in m.Scase)
    model.total_ore_tonnes = pyo.Expression(rule=total_ore_demand_rule)

    # Annual transport cost in USD
    model.total_transport_cost_USD = pyo.Expression(
        expr=model.total_ore_tonnes * model.transport_cost_per_tonne
    )

    # Annual transport cost in million USD/year (for OPEX sum)
    model.aOPEX_transport = pyo.Expression(
        expr=model.total_transport_cost_USD / 1e6
    )

    # Transport cost per tonne of steel
    model.transport_cost_addition_per_tonne = pyo.Expression(
        expr=model.total_transport_cost_USD / model.dem_SFS
    )

    # 7. ECONOMIC EQUATIONS
    def rule_CAPEX1(m, y):
        return m.CAPEX_s[y] == m.var_ucost[y,'s'] * m.c_RE['s']
    model.CAPEX1 = pyo.Constraint(model.Ycase, rule=rule_CAPEX1)
    
    def rule_CAPEX2(m, y):
        return m.CAPEX_w[y] == m.var_ucost[y,'w'] * m.c_RE['w']
    model.CAPEX2 = pyo.Constraint(model.Ycase, rule=rule_CAPEX2)
    
    def rule_CAPEX3(m, y):
        return m.CAPEX_bat[y] == m.var_ucost[y,'bat'] * m.rep * m.Lmax_bat_st/m.h_bat
    model.CAPEX3 = pyo.Constraint(model.Ycase, rule=rule_CAPEX3)
    
    def rule_CAPEX4(m, y):
        return m.CAPEX_ely[y] == m.var_ucost[y,'ely'] * m.c_ely * m.rep
    model.CAPEX4 = pyo.Constraint(model.Ycase, rule=rule_CAPEX4)
    
    def rule_CAPEX5(m, y):
        return m.CAPEX_FC[y] == m.var_ucost[y,'FC'] * m.c_FC * m.rep
    model.CAPEX5 = pyo.Constraint(model.Ycase, rule=rule_CAPEX5)
    
    def rule_CAPEX6(m):
        return m.CAPEX_DRP == 0.00031 * sum(m.T_DRI[s] for s in m.Scase) * (8760/m.T_t)
    model.CAPEX6 = pyo.Constraint(rule=rule_CAPEX6)
    
    def rule_CAPEX7(m):
        return m.CAPEX_cmp2b == (8.4074 * sum(m.T_DRI[s] for s in m.Scase) * (8760/m.T_t)/1e6 + 4.5351)
    model.CAPEX7 = pyo.Constraint(rule=rule_CAPEX7)
    
    def rule_CAPEX8(m):
        return m.CAPEX_CGH2 == 2.064 * m.CGH2_in_st_max + 0.7 * m.Lmax_CGH2_st
    model.CAPEX8 = pyo.Constraint(rule=rule_CAPEX8)
    
    def rule_CAPEX9(m):
        return m.CAPEX_EAF == 1.8728 * m.c_EAF + 68.75
    model.CAPEX9 = pyo.Constraint(rule=rule_CAPEX9)
    
    def rule_CAPEX10(m):
        return m.CAPEX_cst == 0.945 * m.LS_out_EAF_max
    model.CAPEX10 = pyo.Constraint(rule=rule_CAPEX10)
    
    def rule_aCAPEX1(m):
        return m.aCAPEX_s == sum(m.f_CR * m.CAPEX_s[y] for y in m.Ycase) * m.f_t
    model.aCAPEX1 = pyo.Constraint(rule=rule_aCAPEX1)
    
    def rule_aCAPEX2(m):
        return m.aCAPEX_w == sum(m.f_CR * m.CAPEX_w[y] for y in m.Ycase) * m.f_t
    model.aCAPEX2 = pyo.Constraint(rule=rule_aCAPEX2)
    
    def rule_aCAPEX3(m):
        return m.aCAPEX_bat == sum(m.f_CR * m.CAPEX_bat[y] for y in m.Ycase) * m.f_t
    model.aCAPEX3 = pyo.Constraint(rule=rule_aCAPEX3)
    
    def rule_aCAPEX4(m):
        return m.aCAPEX_ely == sum(m.f_CR * m.CAPEX_ely[y] for y in m.Ycase) * m.f_t
    model.aCAPEX4 = pyo.Constraint(rule=rule_aCAPEX4)
    
    def rule_aCAPEX5(m):
        return m.aCAPEX_FC == sum(m.f_CR * m.CAPEX_FC[y] for y in m.Ycase) * m.f_t
    model.aCAPEX5 = pyo.Constraint(rule=rule_aCAPEX5)
    
    def rule_aCAPEX6(m):
        return m.aCAPEX_DRP == m.f_CR * m.CAPEX_DRP * m.f_t
    model.aCAPEX6 = pyo.Constraint(rule=rule_aCAPEX6)
    
    def rule_aCAPEX7(m):
        return m.aCAPEX_cmp2b == m.f_CR * m.CAPEX_cmp2b * m.f_t
    model.aCAPEX7 = pyo.Constraint(rule=rule_aCAPEX7)
    
    def rule_aCAPEX8(m):
        return m.aCAPEX_CGH2 == m.f_CR * m.CAPEX_CGH2 * m.f_t
    model.aCAPEX8 = pyo.Constraint(rule=rule_aCAPEX8)
    
    def rule_aCAPEX9(m):
        return m.aCAPEX_EAF == m.f_CR * m.CAPEX_EAF * m.f_t
    model.aCAPEX9 = pyo.Constraint(rule=rule_aCAPEX9)
    
    def rule_aCAPEX10(m):
        return m.aCAPEX_cst == m.f_CR * m.CAPEX_cst * m.f_t
    model.aCAPEX10 = pyo.Constraint(rule=rule_aCAPEX10)
    
    def rule_aOPEX1(m):
        return m.aOPEX_maint == sum(m.CAPEX_s[y] + m.CAPEX_w[y] + m.CAPEX_bat[y] + 
                                  m.CAPEX_ely[y] + m.CAPEX_FC[y] for y in m.Ycase) * m.f_maint * m.f_t + \
               (m.CAPEX_DRP + m.CAPEX_cmp2b + m.CAPEX_CGH2 + m.CAPEX_EAF + m.CAPEX_cst) * m.f_maint * m.f_t
    model.aOPEX1 = pyo.Constraint(rule=rule_aOPEX1)

    def rule_aOPEX3(m):
        return m.aOPEX_pel == sum(m.T_DR_pel[y,s] for y in m.Ycase for s in m.Scase) * 0.000160
    model.aOPEX3 = pyo.Constraint(rule=rule_aOPEX3)
    
    def rule_aOPEX4(m):
        return m.aOPEX_lmp == sum(m.T_DR_lmp[y,s] for y in m.Ycase for s in m.Scase) * 0.000120
    model.aOPEX4 = pyo.Constraint(rule=rule_aOPEX4)
    
    def rule_aOPEX5(m):
        return m.aOPEX_scr == sum(m.T_scr[s] for s in m.Scase) * 0.000265
    model.aOPEX5 = pyo.Constraint(rule=rule_aOPEX5)
    
    def rule_aOPEX6(m):
        return m.aOPEX_lime == sum(m.T_lime[s] for s in m.Scase) * 0.000121
    model.aOPEX6 = pyo.Constraint(rule=rule_aOPEX6)
    
    def rule_aOPEX7(m):
        return m.aOPEX_aly == m.T_aly * 0.002397
    model.aOPEX7 = pyo.Constraint(rule=rule_aOPEX7)
    
    def rule_aOPEX8(m):
        return m.aOPEX_eld == m.T_eld * 0.005395
    model.aOPEX8 = pyo.Constraint(rule=rule_aOPEX8)
    
    def rule_aOPEX9(m):
        return m.aOPEX_labour == (0.000019 * sum(m.T_DRI[s] for s in m.Scase) + 
                                0.00005319 * m.dem_SFS)
    model.aOPEX9 = pyo.Constraint(rule=rule_aOPEX9)
    
    def rule_T_aCAPEX(m):
        return m.T_aCAPEX == (m.aCAPEX_s + m.aCAPEX_w + m.aCAPEX_bat + m.aCAPEX_ely + 
                             m.aCAPEX_FC + m.aCAPEX_DRP + m.aCAPEX_cmp2b + 
                             m.aCAPEX_CGH2 + m.aCAPEX_EAF + m.aCAPEX_cst)
    model.T_aCAPEX_cons = pyo.Constraint(rule=rule_T_aCAPEX)
    
    def rule_T_aOPEX(m):
        return m.T_aOPEX == (
            m.aOPEX_maint + m.aOPEX_pel + m.aOPEX_lmp + 
            m.aOPEX_scr + m.aOPEX_lime + m.aOPEX_aly + 
            m.aOPEX_eld + m.aOPEX_labour + m.aOPEX_transport
        )
    model.T_aOPEX_cons = pyo.Constraint(rule=rule_T_aOPEX)
    
    # 8. OBJECTIVE FUNCTION
    def rule_obj(m):
        return m.T_aCAPEX + m.T_aOPEX
    model.T_grid_cost = pyo.Expression(expr=model.T_P_grid_import * model.grid_price)
    model.T_cost = pyo.Expression(expr=model.T_aCAPEX + model.T_aOPEX + model.T_grid_cost)
    
    model.T_energy = pyo.Expression(
    expr=model.T_RE
         + sum(model.T_En_ore[y, s] for y in model.Ycase for s in model.Scase)
         + model.T_P_ely
         + model.T_P_H2heat
         + model.T_P_cmp2b
         + model.T_P_cmp200b
         + model.T_P_CDRIheat
         + model.T_P_EAF
         + model.T_P_cst
)

    model.obj = pyo.Objective(expr=model.T_cost * 1e6 / model.dem_SFS, sense=minimize)
    
    # ===== Energy consumption rates (MWh/t SFS) =====
    model.rE_RE = pyo.Expression(expr=model.T_RE / model.dem_SFS)
    model.rE_ore = pyo.Expression(expr=sum(model.T_En_ore[y,s] for y in model.Ycase for s in model.Scase) / model.dem_SFS)
    model.rE_curtail = pyo.Expression(expr=model.T_P_curtail / model.dem_SFS)
    model.rE_cons = pyo.Expression(expr=model.T_P_cons / model.dem_SFS)
    model.rE_ely = pyo.Expression(expr=model.T_P_ely / model.dem_SFS)
    model.rE_H2heat = pyo.Expression(expr=model.T_P_H2heat / model.dem_SFS)
    model.rE_cmp2b = pyo.Expression(expr=model.T_P_cmp2b / model.dem_SFS)
    model.rE_cmp200b = pyo.Expression(expr=model.T_P_cmp200b / model.dem_SFS)
    model.rE_CDRIheat = pyo.Expression(expr=model.T_P_CDRIheat / model.dem_SFS)
    model.rE_EAF = pyo.Expression(expr=model.T_P_EAF / model.dem_SFS)
    model.rE_cst = pyo.Expression(expr=model.T_P_cst / model.dem_SFS)

    # ===== Shares and composition expressions =====
    model.share_solar_in_RE = pyo.Expression(expr=100 * model.T_RE_solar / model.T_RE)
    model.share_wind_in_RE = pyo.Expression(expr=100 * model.T_RE_wind / model.T_RE)

    model.share_grid_in_total_energy = pyo.Expression(expr=100 * model.T_P_grid_import / model.T_energy)

    model.plant_capacity_factor = pyo.Expression(
        expr=sum(model.LS_out_EAF[t] for t in model.T) / (model.c_EAF * model.T_t)
    )

    # Land use expressions
    model.land_solar = pyo.Expression(expr=0.02 * model.c_RE['s'])  # km2
    model.land_wind = pyo.Expression(expr=0.12 * model.c_RE['w'])   # km2
    model.total_land = pyo.Expression(expr=model.land_solar + model.land_wind)

    #Emissions expressions
    model.CO2_solar = pyo.Expression(expr=48 / 1e6 * model.T_RE_solar)  # tonnes CO2-e
    model.CO2_wind = pyo.Expression(expr=12 / 1e6 * model.T_RE_wind)    # tonnes CO2-e
    model.total_CO2 = pyo.Expression(expr=model.CO2_solar + model.CO2_wind)
    model.CO2_per_tonne_steel = pyo.Expression(
        expr=model.total_CO2 / model.dem_SFS
    )

    # ===== LCOS Expressions =====

    # Ore cost only
    model.ore_cost_mUSD = pyo.Expression(
        expr=model.aOPEX_pel + model.aOPEX_lmp
    )

    # LCOS including ore
    model.LCOS_inc_ore = pyo.Expression(
        expr=model.T_cost * 1e6 / model.dem_SFS
    )

    # LCOS excluding ore
    model.LCOS_exc_ore = pyo.Expression(
        expr=(model.T_cost - model.ore_cost_mUSD) * 1e6 / model.dem_SFS
    )

    # Ore cost addition in $/tonne steel
    model.ore_cost_addition = pyo.Expression(
        expr=model.ore_cost_mUSD * 1e6 / model.dem_SFS
    )

    # ===== Hydrogen cost attribution expressions =====
    model.share_ely_in_total_energy = pyo.Expression(
        expr=100 * model.T_P_ely / model.T_energy
    )
    model.cost_ely_electricity = pyo.Expression(
        expr=model.T_cost * (model.T_P_ely / model.T_energy)
    )
    model.total_H2_cost_mUSD = pyo.Expression(
        expr=model.aCAPEX_ely + model.cost_ely_electricity
    )
    model.LCOH_USD_per_kg = pyo.Expression(
        expr=(model.total_H2_cost_mUSD * 1e6) / (model.T_H2 * 1000)
    )

    # ===== LCOE Expressions =====

    # Sum of annualised CAPEX for energy assets (million USD/year)
    model.T_aCAPEX_energy = pyo.Expression(
        expr=model.aCAPEX_s + model.aCAPEX_w + model.aCAPEX_bat + model.aCAPEX_ely + model.aCAPEX_FC
    )

    # Annualised maintenance OPEX for energy assets only (million USD/year)
    model.aOPEX_maint_energy = pyo.Expression(
        expr=model.f_maint * (
            sum(model.CAPEX_s[y] + model.CAPEX_w[y] + model.CAPEX_bat[y] + model.CAPEX_ely[y] + model.CAPEX_FC[y]
                for y in model.Ycase)
        ) * model.f_t
    )

    # Numerator: Annualised energy system cost (million USD/year)
    model.LCOE_numerator_mUSD_per_year = pyo.Expression(
        expr=model.T_aCAPEX_energy + model.aOPEX_maint_energy
    )

    # LCOE in USD/MWh
    model.LCOE_USD_per_MWh = pyo.Expression(
        expr=(model.LCOE_numerator_mUSD_per_year * 1e6) / model.T_RE
    )

    # ===== Total Energy Spend for Steel Plant =====

    # Total cost of all energy inputs to the steel plant (million USD/year)
    model.Total_Energy_Spend_mUSD_per_year = pyo.Expression(
        expr=model.T_aCAPEX_energy + model.aOPEX_maint_energy + model.T_grid_cost
    )

    return model

def solve_all_scenarios():
    Ycases = ['YCurrent', 'Y2030', 'Y2040', 'Y2050']
    Scases = ['S1', 'S2', 'S3']
    objectives = ['cost']

    results_list = []

    for obj in objectives:
        for y in Ycases:
            for s in Scases:
                print(f"\n Solving for Objective={obj}, Ycase={y}, Scase={s}")

                # 1. Create fresh model for this scenario
                # Look up scenario-specific values
                ROM_grade_val = 0.62  # you can change this ore purity value as needed
                f_scrap_lookup = {'S1': 0, 'S2': 0.25, 'S3': 0.5}
                f_scrap_val = f_scrap_lookup[s]

                # Create model for this scenario
                model = create_complete_green_steel_model(
                    ycase=y,
                    scase=s,
                    ROM_grade_val=ROM_grade_val,
                    f_scrap_val=f_scrap_val,
                    objective=obj
                )

                # 2. Initialise parameters for this scenario
                initialize_model_parameters(model, y, s)

                # 3. Solve
                solver = pyo.SolverFactory('gurobi')
                results = solver.solve(model, tee=True)

                if results.solver.termination_condition == TerminationCondition.optimal:
                    print(f"\n Optimal solution for Objective={obj}, ({y}, {s})")
                    model.solutions.load_from(results)
                    print_results(model)

                    # 4. Store results
                    results_list.append({
                        'Objective': obj,
                        'Ycase': y,
                        'Scase': s,
                        'TotalCost': pyo.value(model.T_cost),
                        'Cost_per_tonne': pyo.value(model.T_cost) * 1e6 / pyo.value(model.dem_SFS),
                        'Total_H2_t_per_t_steel': pyo.value(model.T_H2) / pyo.value(model.dem_SFS),
                        'LCOE_USD_per_MWh': pyo.value(model.LCOE_USD_per_MWh),

                        # Annualised CAPEX
                        'Total_aCAPEX_mUSD_per_year': pyo.value(model.T_aCAPEX),
                        'aCAPEX_s': pyo.value(model.aCAPEX_s),
                        'aCAPEX_w': pyo.value(model.aCAPEX_w),
                        'aCAPEX_bat': pyo.value(model.aCAPEX_bat),
                        'aCAPEX_ely': pyo.value(model.aCAPEX_ely),
                        'aCAPEX_FC': pyo.value(model.aCAPEX_FC),
                        'aCAPEX_DRP': pyo.value(model.aCAPEX_DRP),
                        'aCAPEX_cmp2b': pyo.value(model.aCAPEX_cmp2b),
                        'aCAPEX_CGH2': pyo.value(model.aCAPEX_CGH2),
                        'aCAPEX_EAF': pyo.value(model.aCAPEX_EAF),
                        'aCAPEX_cst': pyo.value(model.aCAPEX_cst),

                        # Annualised OPEX
                        'Total_aOPEX_mUSD_per_year': pyo.value(model.T_aOPEX),
                        'aOPEX_maint': pyo.value(model.aOPEX_maint),
                        'aOPEX_pel': pyo.value(model.aOPEX_pel),
                        'aOPEX_lmp': pyo.value(model.aOPEX_lmp),
                        'aOPEX_scr': pyo.value(model.aOPEX_scr),
                        'aOPEX_lime': pyo.value(model.aOPEX_lime),
                        'aOPEX_aly': pyo.value(model.aOPEX_aly),
                        'aOPEX_eld': pyo.value(model.aOPEX_eld),
                        'aOPEX_labour': pyo.value(model.aOPEX_labour),
                        'LCOS_inc_ore': pyo.value(model.LCOS_inc_ore),
                        'LCOS_exc_ore': pyo.value(model.LCOS_exc_ore),
                        'Ore_cost_addition': pyo.value(model.ore_cost_addition),
                        'TotalTransportCost_mUSD': pyo.value(model.aOPEX_transport),
                        'TransportCost_per_tonne_steel': pyo.value(model.transport_cost_addition_per_tonne),

                        # Installed capacities
                        'Solar': pyo.value(model.c_RE['s']),
                        'Wind': pyo.value(model.c_RE['w']),
                        'Electrolyzer': pyo.value(model.c_ely),
                        'FuelCell': pyo.value(model.c_FC),
                        'EAF': pyo.value(model.c_EAF),

                        # RE oversizing factors
                        'Solar_oversizing_factor': (
                            pyo.value(model.c_RE['s']) / (pyo.value(model.T_RE_solar) / 8760)
                            if pyo.value(model.T_RE_solar) > 0 else 0
                        ),
                        'Wind_oversizing_factor': (
                            pyo.value(model.c_RE['w']) / (pyo.value(model.T_RE_wind) / 8760)
                            if pyo.value(model.T_RE_wind) > 0 else 0
                        ),

                        # Annual flows
                        'H2_Production': pyo.value(model.T_H2),
                        'CGH2_Storage': pyo.value(model.T_CGH2),
                        'CGH2_DRI': pyo.value(model.T_CGH2_DRI),
                        'CGH2_FC': pyo.value(model.T_CGH2_FC),
                        'DRI': sum(pyo.value(model.T_DRI[s]) for s in model.Scase),
                        'Scrap': sum(pyo.value(model.T_scr[s]) for s in model.Scase),
                        'CGH2_t_per_t_steel': pyo.value(model.T_CGH2) / pyo.value(model.dem_SFS),
                        'Pct_CGH2_of_total_H2': 100 * pyo.value(model.T_CGH2) / pyo.value(model.T_H2),
                        'HDRI_t_per_t_steel': pyo.value(model.T_HDRI) / pyo.value(model.dem_SFS),
                        'CDRI_t_per_t_steel': pyo.value(model.T_CDRI) / pyo.value(model.dem_SFS),
                        'Pct_CDRI_of_total_DRI': (
                            100 * pyo.value(model.T_CDRI) / (pyo.value(model.T_HDRI) + pyo.value(model.T_CDRI))
                            if (pyo.value(model.T_HDRI) + pyo.value(model.T_CDRI)) > 0 else 0
                        ),
                        'Ely_oversizing_factor': (
                            pyo.value(model.c_ely) / (pyo.value(model.T_P_ely) / 8760)
                            if pyo.value(model.T_P_ely) > 0 else 0
                        ),
                        'EAF_oversizing_factor': (
                            pyo.value(model.c_EAF) / (pyo.value(model.dem_SFS) / 8760)
                        if pyo.value(model.dem_SFS) > 0 else 0
                        ),
                        'Plant_capacity_factor_pct': pyo.value(model.plant_capacity_factor) * 100,

                        # Grid Import
                        'GridImport': pyo.value(model.T_P_grid_import),

                        # Shares
                        'CAPEX_share_pct': 100 * pyo.value(model.T_aCAPEX) / pyo.value(model.T_cost),
                        'OPEX_share_pct': 100 * pyo.value(model.T_aOPEX) / pyo.value(model.T_cost),
                        'share_solar_in_RE': pyo.value(model.share_solar_in_RE),
                        'share_wind_in_RE': pyo.value(model.share_wind_in_RE),
                        'share_grid_in_total_energy': pyo.value(model.share_grid_in_total_energy),

                        # VRE Generation
                        'Total_VRE_Generation': pyo.value(model.T_RE),
                        'Solar_VRE_Generation': pyo.value(model.T_RE_solar),
                        'Wind_VRE_Generation': pyo.value(model.T_RE_wind),

                        # Battery
                        'Battery_storage_capacity_MWh': pyo.value(model.Lmax_bat_st),

                        # Fuel Cell
                        'FuelCell_Annual_Generation_MWh': pyo.value(model.T_P_FC),
                        
                        # Land use
                        'Land_Solar_km2': pyo.value(model.land_solar),
                        'Land_Wind_km2': pyo.value(model.land_wind),
                        'Total_Land_km2': pyo.value(model.total_land),
                        
                        # Emissions
                        'CO2_Solar_tonnes': pyo.value(model.CO2_solar),
                        'CO2_Wind_tonnes': pyo.value(model.CO2_wind),
                        'Total_VRE_CO2_tonnes': pyo.value(model.total_CO2),
                        'CO2_per_tonne_steel': pyo.value(model.CO2_per_tonne_steel),
                        
                        # Electrolyzer 
                        'LCOH_USD_per_kg': pyo.value(model.LCOH_USD_per_kg),
                        'Ely_energy_share_pct': pyo.value(model.share_ely_in_total_energy),

                        'Cost_Ely_Electricity_mUSD_per_year': pyo.value(model.cost_ely_electricity),
                        'Total_H2_Cost_mUSD_per_year': pyo.value(model.total_H2_cost_mUSD)

                    })

                else:
                    print(f"\n No optimal solution for Objective={obj}, ({y}, {s})")

    # 5. Export to CSV
    df = pd.DataFrame(results_list)
    df.to_csv('all_scenario_results.csv', index=False)
    print("\n All scenario results saved to 'all_scenario_results.csv'.")

def initialize_model_parameters(model, ycase, scase):
    # 1. Load and initialize VRE profiles from CSV
    vre_data = pd.read_csv(r'C:\Users\archi\Final Cities\Zhangjiakou\Zhangjiakou_2019.csv')
    time_mapping = {f't{i}': i for i in range(1, 8761)}
    for _, row in vre_data.iterrows():
        t = time_mapping[row['t']]
        model.VRE_prod[t, 's'] = row['s']
        model.VRE_prod[t, 'w'] = row['w']

    # 2. Initialize parameters for the chosen scenario
    s = scase
    y = ycase

    model.T_DRI[s] = model.dem_SFS * (1 - model.f_scrap[s]) / 0.94
    model.T_scr[s] = model.dem_SFS * model.f_scrap[s]
    model.T_lime[s] = model.dem_SFS * model.mass_lime[s]
    model.T_DR_ore[s] = model.T_DRI[s] * 1.382

    if model.ROM_grade[y] >= 0.66:
        model.T_DR_lmp[y, s] = model.T_DR_ore[s] * 0.3
    else:
        model.T_DR_lmp[y, s] = 0
    model.T_DR_pel[y, s] = model.T_DR_ore[s] - model.T_DR_lmp[y, s]

    # 3. Ore subsystem mass balances and energy
    for y in model.Ycase:
        for s in model.Scase:
            # --- Fines in pellet plant
            T_fines_in_pel = model.T_DR_pel[y, s] / (1 - model.mloss_pel)
            model.T_fines_in_pel[y, s] = T_fines_in_pel

            # --- Delta Fe required
            if model.ROM_grade[y] < 0.66:
                delta_Fe = model.ore_grade_DRI - model.ROM_grade[y]
            else:
                delta_Fe = 0.01
            delta_Fe_con = delta_Fe - 0.01
            mloss_con = 0.0268 * delta_Fe_con * 100

            # --- Ore in beneficiation
            T_ore_in_ben = T_fines_in_pel / (1 - mloss_con)
            model.T_ore_in_ben[y, s] = T_ore_in_ben

            # --- Ore out of crushing
            T_ore_out_crs = T_ore_in_ben + model.T_DR_lmp[y, s]
            model.T_ore_out_crs[y, s] = T_ore_out_crs

            # --- ROM ore demand
            T_ore_ROM = T_ore_out_crs / (1 - model.mloss_crs)
            model.T_ore_ROM[y, s] = T_ore_ROM

            # --- Ore energy subsystem
            En_mng = (model.alpha_drill + model.alpha_load) * T_ore_out_crs / 3600
            P_crs = model.alpha_crs * T_ore_out_crs
            P_com = model.alpha_com * T_ore_in_ben
            P_con = model.alpha_con * delta_Fe_con * 100 * T_ore_in_ben
            P_pel = model.alpha_pel * T_fines_in_pel
            P_stkp = model.alpha_stk * model.T_DR_pel[y, s]
            P_stkl = model.alpha_stk * model.T_DR_lmp[y, s]

            model.En_mng[y, s] = En_mng
            model.P_crs[y, s] = P_crs
            model.P_com[y, s] = P_com
            model.P_con[y, s] = P_con
            model.P_pel[y, s] = P_pel
            model.P_stkp[y, s] = P_stkp
            model.P_stkl[y, s] = P_stkl

            T_En_ore = En_mng + P_crs + P_com + P_con + P_pel + P_stkp + P_stkl
            model.T_En_ore[y, s] = T_En_ore

        En_mng = (model.alpha_drill + model.alpha_load) * T_ore_out_crs / 3600
        P_crs = model.alpha_crs * T_ore_out_crs
        P_com = model.alpha_com * T_ore_in_ben
        P_con = model.alpha_con * delta_Fe_con * 100 * T_ore_in_ben
        P_pel = model.alpha_pel * T_fines_in_pel
        P_stkp = model.alpha_stk * model.T_DR_pel[y, s]
        P_stkl = model.alpha_stk * model.T_DR_lmp[y, s]

        T_En_ore = En_mng + P_crs + P_com + P_con + P_pel + P_stkp + P_stkl

        model.T_En_ore[y, s] = T_En_ore

    model.T_aly = model.dem_SFS * model.mass_aly
    model.T_eld = model.dem_SFS * model.mass_eld

    # 4. Variable EAF electricity consumption (MWh/t LS)
    f_HBIadjust = 0.85 * 3.6 * (1 - model.f_scrap[s]) / 10
    alpha_EAF = (2.4 + f_HBIadjust) / 3.6
    model.alpha_EAF[s] = alpha_EAF

def print_results(model):
    print("\nOptimal Solution Results:")
    print(f"Total annual cost: ${pyo.value(model.T_cost):,.2f} million")
    print(f"Cost per tonne steel: ${pyo.value(model.T_cost)*1e6 / pyo.value(model.dem_SFS):,.2f}")
    HDRI_per_tonne_steel = pyo.value(model.T_HDRI) / pyo.value(model.dem_SFS)
    print(f" - HDRI per tonne steel: {HDRI_per_tonne_steel:.4f} t/t steel")

    CDRI_per_tonne_steel = pyo.value(model.T_CDRI) / pyo.value(model.dem_SFS)
    print(f" - CDRI per tonne steel: {CDRI_per_tonne_steel:.4f} t/t steel")

    total_DRI = pyo.value(model.T_HDRI) + pyo.value(model.T_CDRI)
    if total_DRI > 0:
        pct_CDRI_of_total_DRI = 100 * pyo.value(model.T_CDRI) / total_DRI
    else:
        pct_CDRI_of_total_DRI = 0
    print(f" - % CDRI of total DRI: {pct_CDRI_of_total_DRI:.2f}%")

    avg_ely_load = pyo.value(model.T_P_ely) / 8760
    if avg_ely_load > 0:
        ely_oversizing_factor = pyo.value(model.c_ely) / avg_ely_load
    else:
        ely_oversizing_factor = 0
    print(f" - Electrolyser oversizing factor: {ely_oversizing_factor:.2f}")

    avg_steel_hourly = pyo.value(model.dem_SFS) / 8760
    if avg_steel_hourly > 0:
        EAF_oversizing_factor = pyo.value(model.c_EAF) / avg_steel_hourly
    else:
        EAF_oversizing_factor = 0
    print(f" - EAF oversizing factor: {EAF_oversizing_factor:.2f}")

    print("\nInstalled Capacities:")
    print(f"Solar PV: {pyo.value(model.c_RE['s']):.2f} MW")
    print(f"Wind: {pyo.value(model.c_RE['w']):.2f} MW")
    print(f"Electrolyzer: {pyo.value(model.c_ely):.2f} MW")
    print(f"Fuel Cell: {pyo.value(model.c_FC):.2f} MW")
    print(f"EAF: {pyo.value(model.c_EAF):.2f} tonnes/hour")

    print("\nAnnual Material Flows:")
    print(f"H2 production: {pyo.value(model.T_H2):,.2f} tonnes")
    print(f"CGH2 storage: {pyo.value(model.T_CGH2):,.2f} tonnes")
    print(f"DRI production: {sum(pyo.value(model.T_DRI[s]) for s in model.Scase):,.2f} tonnes")
    print(f"Scrap usage: {sum(pyo.value(model.T_scr[s]) for s in model.Scase):,.2f} tonnes")
    print(f"Grid Import (annual): {pyo.value(model.T_P_grid_import):,.2f} MWh")

    print("\nAnnual Renewable Generation:")
    print(f"Total VRE: {pyo.value(model.T_RE):,.2f} MWh")
    print(f"  - Solar: {pyo.value(model.T_RE_solar):,.2f} MWh")
    print(f"  - Wind:  {pyo.value(model.T_RE_wind):,.2f} MWh")

    if pyo.value(model.T_RE_solar) > 0:
        Solar_oversizing_factor = pyo.value(model.c_RE['s']) / (pyo.value(model.T_RE_solar) / 8760)
    else:
        Solar_oversizing_factor = 0

    if pyo.value(model.T_RE_wind) > 0:
        Wind_oversizing_factor = pyo.value(model.c_RE['w']) / (pyo.value(model.T_RE_wind) / 8760)
    else:
        Wind_oversizing_factor = 0

    print(f" - Solar oversizing factor: {Solar_oversizing_factor:.2f}")
    print(f" - Wind oversizing factor: {Wind_oversizing_factor:.2f}")
    print(f"Plant capacity factor: {pyo.value(model.plant_capacity_factor) * 100:.2f}%")

    print("\nAnnualised CAPEX breakdown ($ million/year):")
    print(f"\n Total annualised CAPEX: ${pyo.value(model.T_aCAPEX):,.2f} million/year")
    print(f"  Solar: {pyo.value(model.aCAPEX_s):,.2f}")
    print(f"  Wind: {pyo.value(model.aCAPEX_w):,.2f}")
    print(f"  Battery: {pyo.value(model.aCAPEX_bat):,.2f}")
    print(f"  Electrolyzer: {pyo.value(model.aCAPEX_ely):,.2f}")
    print(f"  Fuel Cell: {pyo.value(model.aCAPEX_FC):,.2f}")
    print(f"  DRP: {pyo.value(model.aCAPEX_DRP):,.2f}")
    print(f"  Compressors: {pyo.value(model.aCAPEX_cmp2b):,.2f}")
    print(f"  CGH2 Storage: {pyo.value(model.aCAPEX_CGH2):,.2f}")
    print(f"  EAF: {pyo.value(model.aCAPEX_EAF):,.2f}")
    print(f"  Caster: {pyo.value(model.aCAPEX_cst):,.2f}")

    print("\nAnnualised OPEX breakdown ($ million/year):")
    print(f" Total annualised OPEX:  ${pyo.value(model.T_aOPEX):,.2f} million/year")
    print(f"  Maintenance: {pyo.value(model.aOPEX_maint):,.2f}")
    print(f"  Pellets: {pyo.value(model.aOPEX_pel):,.2f}")
    print(f"  Lump ore: {pyo.value(model.aOPEX_lmp):,.2f}")
    print(f"  Scrap: {pyo.value(model.aOPEX_scr):,.2f}")
    print(f"  Lime: {pyo.value(model.aOPEX_lime):,.2f}")
    print(f"  Alloys: {pyo.value(model.aOPEX_aly):,.2f}")
    print(f"  Electrodes: {pyo.value(model.aOPEX_eld):,.2f}")
    print(f"  Labour: {pyo.value(model.aOPEX_labour):,.2f}")
    print(f"  Transport: {pyo.value(model.aOPEX_transport):,.2f}")
    print(f"Ore cost addition: ${pyo.value(model.ore_cost_addition):,.2f} /t steel")
    print(f"Transport cost addition: ${pyo.value(model.transport_cost_addition_per_tonne):,.2f} /t steel")

    print("\nLCOS (USD/t steel):")
    print(f"LCOS (including ore): ${pyo.value(model.LCOS_inc_ore):,.2f} /t steel")
    print(f"LCOS (excluding ore): ${pyo.value(model.LCOS_exc_ore):,.2f} /t steel")

    print(f"\nGrid import cost: {pyo.value(model.T_grid_cost):,.2f} $ million/year")

    print(f"Battery storage capacity: {pyo.value(model.Lmax_bat_st):.2f} MWh")

    print(f"Fuel Cell annual generation: {pyo.value(model.T_P_FC):,.2f} MWh")

    print(f"LCOE (USD/MWh): {pyo.value(model.LCOE_USD_per_MWh):,.2f} USD/MWh")
    print(f"Total annual energy spend: ${pyo.value(model.Total_Energy_Spend_mUSD_per_year):,.2f} million/year")

    print("\nRenewable Energy Shares:")
    print(f"  - Solar in VRE: {pyo.value(model.share_solar_in_RE):.2f}%")
    print(f"  - Wind in VRE: {pyo.value(model.share_wind_in_RE):.2f}%")
    print(f"  - Grid Import in Total Energy: {pyo.value(model.share_grid_in_total_energy):.2f}%")

    print("\nLand Use:")
    print(f"  Solar PV land: {pyo.value(model.land_solar):.2f} km2")
    print(f"  Wind land: {pyo.value(model.land_wind):.2f} km2")
    print(f"  Total land: {pyo.value(model.total_land):.2f} km2")

    print("\nLifecycle Emissions (VRE construction):")
    print(f"  Solar PV emissions: {pyo.value(model.CO2_solar):,.2f} tonnes CO2-e")
    print(f"  Wind emissions: {pyo.value(model.CO2_wind):,.2f} tonnes CO2-e")
    print(f"  Total VRE emissions: {pyo.value(model.total_CO2):,.2f} tonnes CO2-e")
    print(f"  CO2 per tonne of steel: {pyo.value(model.CO2_per_tonne_steel):,.4f} t CO2-e/t steel")
    
    print("\nHydrogen Production Cost Estimates:")
    print(f" - Total annual H2 production: {pyo.value(model.T_H2):,.2f} tonnes")

    H2_per_tonne_steel = pyo.value(model.T_H2) / pyo.value(model.dem_SFS)
    print(f" - Total H2 per tonne steel: {H2_per_tonne_steel:.4f} t/t steel")

    CGH2_per_tonne_steel = pyo.value(model.T_CGH2) / pyo.value(model.dem_SFS)
    print(f" - CGH2 per tonne steel: {CGH2_per_tonne_steel:.4f} t/t steel")

    CGH2_pct_of_total_H2 = 100 * pyo.value(model.T_CGH2) / pyo.value(model.T_H2)
    print(f" - % CGH2 of total H2: {CGH2_pct_of_total_H2:.2f}%")

    print(f" - Electrolyzer energy share: {pyo.value(model.share_ely_in_total_energy):.2f}%")
    print(f" - Electrolyzer CAPEX annualised: ${pyo.value(model.aCAPEX_ely):,.2f} million")
    print(f" - Electricity cost share: ${pyo.value(model.cost_ely_electricity):,.2f} million")
    print(f" - Total H2 cost attributed: ${pyo.value(model.total_H2_cost_mUSD):,.2f} million")
    print(f" - Levelised Cost of Hydrogen (LCOH): ${pyo.value(model.LCOH_USD_per_kg):,.2f} /kg")

if __name__ == "__main__":
    solve_all_scenarios()