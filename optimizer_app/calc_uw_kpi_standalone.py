from fastapi import FastAPI
from starlette.requests import Request
from typing import Union

from pydantic import BaseModel, validator
from typing import Optional

import pandas as pd
import numpy as np
from datetime import date, time, timedelta
from pyxirr import xirr

class UWBaseIn(BaseModel):
    Exit_Yr: int

    C_CAP_NOI: str

    C_No_of_Units: float
    C_Capital_Reserve_Per_Unit: float
    C_NRSF: float
    C_MarketRent_Per_SF: float
    C_NRI: float
    C_Other_Income_Yr0: float
    C_Market_Exp_Per_SF: float
    C_Market_Exp_Per_SF_Yr1: float
    C_Sponsor_Promote_Co_Invest: float
    C_Terminal_Cap_Rate: float
    C_Selling_Expenses: float
    C_YM: float
    C_Exit_Pct: float
    C_LTV: float
    C_DCR : float

    #Assumptions
    C_Yr_of_Refinance: int
    C_Co_Invest: float
    C_Cash_Out_Refinance: float
    C_Promote_Wtd_Avg: float
    C_Asset_Mgmt_Fee: float
    C_Prop_Mgmt_Fee: float
    C_Prof_Svc: float
    C_Preferred_Return: float
    C_Terminal_Cap_Rate: float
    C_Loan_Constant: float
    C_Financing_Cost: float

    #Sources
    C_Debt_Balance: float
    C_Sub_Debt: float
    C_Preferred_Equity: float

    #Uses
    C_Purchase_Price: float
    C_Closing_Costs: float
    C_Capex: float
    C_Interest_Reserve: float
    C_Misc: float

    #Growth Rate
    C_Rental_Income: list
    
    C_Expense_Escalators: list
        
    #Monthly Lease by Year
    C_Other_Income_Y1: list
    C_Other_Income_Y2 : list
    C_Other_Income: list
        
    C_Loss_to_Lease_Y0: float
    C_Loss_to_Lease_Y1: list
    C_Loss_to_Lease_Y2: list
    C_Loss_to_Lease_Y3: list
    C_Loss_to_Lease_Y3_Future: float

    C_Econ_Vacancy_Y1: list
    C_Econ_Vacancy: list
        
    Cstm_Yr_Input: Optional[int] = 0
    Cstm_Scenario: str
        
    Cstm_Mkt_Rent_SF: Optional[float] = 0.0
    Cstm_Econ_Vacancy: Optional[float] = 0.0
    Cstm_Rental_Income: Optional[float] = 0.0
    Cstm_Other_Income: Optional[float] = 0.0
    Cstm_Expense_Esc: Optional[float] = 0.0 

mortg_acq = pd.read_csv("/app/Mortgage_Acq.csv", header=0)
mortg_refi = pd.read_csv("/app/Mortgage_refi.csv", header=0)

scenario_data = {
    "Base": {
        "scenario_display_name": "Base",
        
        "Rent_SF": 0.0,
        "Econ_Vacancy":	0.0,
        "Rental_Income": 0.0,
        "Other_Income":	0.0,
        "Expense_Escalators": 0.0
        
    },

    "Luke": {
        "scenario_display_name": "Mild Recession",

        "Rent_SF": -0.12,
        "Econ_Vacancy":	0.07,
        "Rental_Income": -0.05,
        "Other_Income":	-0.03,
        "Expense_Escalators": 0.05
        
    },

    "Han": {
        "scenario_display_name": "Recession - Supply Side Shock",
       
        "Rent_SF": -0.03,
        "Econ_Vacancy":	0.05,
        "Rental_Income": -0.06,
        "Other_Income":	-0.05,
        "Expense_Escalators": 0.065
        
    },

    "Obi": {
        "scenario_display_name": "2008 Recession",

        "Rent_SF": -0.1,
        "Econ_Vacancy":	0.10,
        "Rental_Income": -0.10,
        "Other_Income":	-0.08,
        "Expense_Escalators": 0.08
        
    },

    "Custom": {
        "scenario_display_name": "Custom User Input",

        "Rent_SF": 0.0,
        "Econ_Vacancy":	0.0,
        "Rental_Income": 0.0,
        "Other_Income":	0.0,
        "Expense_Escalators": 0.0
        

    }
}


#[57]:


#Calculated Fields
def GPR(C_NRSF, C_MarketRent_Per_SF):
    return(C_NRSF * C_MarketRent_Per_SF) * 12 #C24=(C18*C19)*12


#[58]:


#Compute Gross Potential Rental Income (Growth Rate)

def GPRI(C_GPR, C_Rental_Income):
    Gross_Potential_Rental_Income = [] #H6

    val = C_GPR
    Gross_Potential_Rental_Income.append(val)
    for n in C_Rental_Income:
        val = (val*(1+n))
        Gross_Potential_Rental_Income.append(val)
        
    return(Gross_Potential_Rental_Income)


#[59]:


#Compute Econ Vacancy - PF Row 16 
def econ_vacancy(Gross_Potential_Rental_Income, C_Econ_Vacancy, C_GPR, C_NRI):
    
    PF_Econ_Vacancy = []
    PF_Econ_Vacancy.append(C_GPR - C_NRI) #Year 0
    #PF_Econ_Vacancy.append(Gross_Potential_Rental_Income[1] * np.mean(C_Econ_Vacancy_Y1))
    
    for ix, itm in enumerate(Gross_Potential_Rental_Income[1:]):
        #print(ix)
        PF_Econ_Vacancy.append(itm * C_Econ_Vacancy[ix+1])

    return (PF_Econ_Vacancy)


#[60]:


#Compute Other Income
def other_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy, C_Other_Income_Yr0, C_Other_Income):
    
    PF_Other_Income = []
    PF_Other_Income.append(C_Other_Income_Yr0)
    PF_Other_Income.append((Gross_Potential_Rental_Income[1] - PF_Econ_Vacancy[1]) * C_Other_Income[1])
    PF_Other_Income.append((Gross_Potential_Rental_Income[2] - PF_Econ_Vacancy[2]) * C_Other_Income[2])

    val = PF_Other_Income[2]

    for n in C_Other_Income[3:]:
        val = val*(1+n)

        PF_Other_Income.append(val) #N23

    return (PF_Other_Income)

#[62]:


#Compute Net Rental Income
def net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy):
    PF_Net_Rental_Income = []
    for i in range(10):
        PF_Net_Rental_Income.append(Gross_Potential_Rental_Income[i] - PF_Econ_Vacancy[i])

    return (PF_Net_Rental_Income)


#[63]:


#Compute Gross Operating Income N26 **** check logic
def gross_operating_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy, PF_Other_Income, PF_Net_Rental_Income):
    PF_Gross_Operating_Income = []
    PF_Gross_Operating_Income.append(PF_Other_Income[0] + PF_Net_Rental_Income[0])
    for i in range(1,11):
        #print(i)
        PF_Gross_Operating_Income.append(Gross_Potential_Rental_Income[i] - PF_Econ_Vacancy[i] + PF_Other_Income[i])

    return (PF_Gross_Operating_Income)


#[64]:


#Compute Operating Expenses N38

def operating_expense(C_NRSF, C_Market_Exp_Per_SF, C_Market_Exp_Per_SF_Yr1, C_Expense_Escalators):
    
    PF_Operating_Expenses = []
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF)
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF_Yr1)
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF_Yr1*(1+C_Expense_Escalators[2]))

    val = PF_Operating_Expenses[2]
    for n in C_Expense_Escalators[2:]:
        val = val*(1+n)
        PF_Operating_Expenses.append(val) 

    return (PF_Operating_Expenses)

#[65]:

#Compute Total Sources K27
def total_sources(C_Purchase_Price, C_Closing_Costs, C_Capex, C_Interest_Reserve, \
                    C_Misc, C_Debt_Balance, C_Sponsor_Promote_Co_Invest, C_Sub_Debt, C_Preferred_Equity):
    C_Uses_Total = C_Purchase_Price + C_Closing_Costs + C_Capex + C_Interest_Reserve + C_Misc
    C_LP_Equity = (C_Uses_Total - C_Debt_Balance) * (1 - C_Sponsor_Promote_Co_Invest)
    C_GP_Equity = (C_Uses_Total - C_Debt_Balance) * (C_Sponsor_Promote_Co_Invest)

    C_Sources_Total = C_Debt_Balance + C_Sub_Debt + C_Preferred_Equity + C_LP_Equity + C_GP_Equity
    return (C_Sources_Total, C_LP_Equity, C_GP_Equity)


#[66]:


#Compute Net Operating Income N39 = N26 - N38
def net_operating_income(PF_Gross_Operating_Income, PF_Operating_Expenses):
    
    PF_Net_Operating_Income = []

    for i in range(11):
        #print(i)
        PF_Net_Operating_Income.append(PF_Gross_Operating_Income[i] - PF_Operating_Expenses[i])

    return (PF_Net_Operating_Income)


#[67]:


#Compute Captial Expenditures/Reserves N41
def capital_exp_res(C_No_of_Units, C_Capital_Reserve_Per_Unit):    
    Capital_Exp_Res = C_No_of_Units * C_Capital_Reserve_Per_Unit
    return (Capital_Exp_Res)


#[68]:


def compute_fees(PF_Gross_Operating_Income, C_Prof_Svc, C_Asset_Mgmt_Fee):
    Prof_Svc = []
    Prof_Svc.append(0)
    for i in range(1,11):
        Prof_Svc.append(PF_Gross_Operating_Income[i] * C_Prof_Svc)

    Asset_Mgmt_Fee = []
    Asset_Mgmt_Fee.append(0)
    for i in range(1,11):
        Asset_Mgmt_Fee.append(PF_Gross_Operating_Income[i] * C_Asset_Mgmt_Fee)
        
    return (Prof_Svc, Asset_Mgmt_Fee)


#[69]:


def total_mortgage_payments(C_Yr_of_Refinance, mortg_refi, mortg_acq):
    #Total Mortgage Payments
    Total_Mortgage_Payments = []
    Total_Mortgage_Payments.append(0)

    for i in range(1,11):

        if (C_Yr_of_Refinance != 0 & i >= C_Yr_of_Refinance):
            Total_Mortgage_Payments.append(sum(mortg_refi[mortg_refi.Year == i]['Payment ']))
        else:
            Total_Mortgage_Payments.append(sum(mortg_acq[mortg_acq.Year == i]['Payment ']))
            
    return(Total_Mortgage_Payments)


#[70]:


def gross_cash_flow(PF_Net_Operating_Income, Capital_Exp_Res, Prof_Svc, \
                    Asset_Mgmt_Fee, Total_Mortgage_Payments):
    
    Gross_Cash_Flow = []
    Gross_Cash_Flow.append(0)
    for i in range(1,11):
        Gross_Cash_Flow.append(PF_Net_Operating_Income[i] - Capital_Exp_Res -   \
            Prof_Svc[i] - Asset_Mgmt_Fee[i] - Total_Mortgage_Payments[i])
                    
    return (Gross_Cash_Flow)


#[71]:


def partnership_cash_flow(PF_Gross_Cash_Flow, C_Preferred_Return, C_Promote_Wtd_Avg):

    Partnership_Cash_Flow = []
    Partnership_Cash_Flow.append(0)
    for i in range(1,11):
        Partnership_Cash_Flow.append((PF_Gross_Cash_Flow[i] - C_Preferred_Return)/(1 - C_Promote_Wtd_Avg) + C_Preferred_Return)

    return Partnership_Cash_Flow


#[116]:


def property_val_term_cap(PF_Net_Operating_Income, Capital_Exp_Res, C_Terminal_Cap_Rate, C_CAP_NOI):
    Property_Val_Term_Cap = []
    Property_Val_Term_Cap.append(0)
    
    if C_CAP_NOI == 'Forward':
        for i in range(1,10):
            Property_Val_Term_Cap.append((PF_Net_Operating_Income[i+1] - Capital_Exp_Res)/C_Terminal_Cap_Rate)
        Property_Val_Term_Cap.append(Property_Val_Term_Cap[-1])
    else:
        for i in range(1,11):
            Property_Val_Term_Cap.append((PF_Net_Operating_Income[i] - Capital_Exp_Res)/C_Terminal_Cap_Rate)
    
    
    return Property_Val_Term_Cap


#[117]:


def refinance_ln_amt_max(C_Financing_Cost, Property_Val_Term_Cap, C_LTV, PF_Net_Operating_Income,                          C_DCR, C_Loan_Constant, C_CAP_NOI):
    Refinance_Loan_Amount_Max = []
    Refinance_Loan_Amount_Max.append(0)
    
    if C_CAP_NOI == 'Forward':
        for i in range(1,10):
            Refinance_Loan_Amount_Max.append((1 - C_Financing_Cost) * min(Property_Val_Term_Cap[i+1] *                                     C_LTV, PF_Net_Operating_Income[i]/C_DCR/C_Loan_Constant))
            
        Refinance_Loan_Amount_Max.append(Refinance_Loan_Amount_Max[-1])
        
    else:
        for i in range(1,11):
            Refinance_Loan_Amount_Max.append((1 - C_Financing_Cost) * min(Property_Val_Term_Cap[i] *                                     C_LTV, PF_Net_Operating_Income[i]/C_DCR/C_Loan_Constant))
            
    return Refinance_Loan_Amount_Max


#[137]:


def calc_mortgage_1_balance(C_Yr_of_Refinance):
    #Calculate Mortgage_1_Bal
    Mortgage_1_Bal = []
    Mortgage_1_Bal.append(0)
    
    for i in range(1,11):
        if (C_Yr_of_Refinance != 0 & C_Yr_of_Refinance < i):
            Mortgage_1_Bal.append(mortg_refi[mortg_refi.Period == (i - C_Yr_of_Refinance + 1)*12]['Ending Balance'].values[0])
        else:
            Mortgage_1_Bal.append(mortg_acq[mortg_refi.Period == i*12]['Ending Balance'].values[0])
    
    return Mortgage_1_Bal


#[182]:


def calc_gross_equity_position(Property_Val_Term_Cap, C_Co_Invest, C_Selling_Expenses, Mortgage_1_Bal):
    
    Mortgage_2_Bal = 0
    Yield_Maintenance = 0
    
    Gross_Equity_Position = []
    Gross_Equity_Position.append(0)
    
    Adjusted_Projected_Sales_Price = []
    Adjusted_Projected_Sales_Price.append(0)
    
    Partnership_Equity_Position = []
    Partnership_Equity_Position.append(0)
    
    for i in range(1,11):
        Adjusted_Projected_Sales_Price.append(Property_Val_Term_Cap[i] * (1 - C_Selling_Expenses))

    for i in range(1,11):
        Gross_Equity_Position.append(Adjusted_Projected_Sales_Price[i] - Mortgage_1_Bal[i] -                             Mortgage_2_Bal + Yield_Maintenance)
        
    for i in range(1,11):
        Partnership_Equity_Position.append(Gross_Equity_Position[i] * (1 - C_Co_Invest))

    return (Gross_Equity_Position, Adjusted_Projected_Sales_Price, Partnership_Equity_Position)


#[183]:

def calc_IRR_base(Exit_Yr, C_LP_Equity, C_GP_Equity, PF_Partnership_Cash_Flow, Gross_Equity_Position):
    IRR_Base = {}
    
    dt = date.today()
    
    IRR_Base[dt] = -(C_LP_Equity + C_GP_Equity)
    
    for i in range(1,Exit_Yr+1):
        for itm in np.repeat(PF_Partnership_Cash_Flow[i]/12, 12):
            dt = ((dt.replace(day=1) + timedelta(days=32)).replace(day=1))
            IRR_Base[dt] = itm
    
    dt = ((dt.replace(day=1) + timedelta(days=32)).replace(day=1))
    IRR_Base[dt] = Gross_Equity_Position[Exit_Yr + 1] + PF_Partnership_Cash_Flow[Exit_Yr + 1]/12
        
    return IRR_Base

def apply_scenarios(uw_data):
    
    #Defaults
    uw_data.C_Econ_Vacancy[1] = np.mean(uw_data.C_Econ_Vacancy_Y1)
    
    uw_data.C_Other_Income[1] = np.mean(uw_data.C_Other_Income_Y1)
    uw_data.C_Other_Income[2] = np.mean(uw_data.C_Other_Income_Y2)
    
    #Scenario Override
    if uw_data.Cstm_Yr_Input > 0:
        if uw_data.Cstm_Scenario not in ["Base", "Custom"]:

            uw_data.C_MarketRent_Per_SF = \
                    uw_data.C_MarketRent_Per_SF * (1 + scenario_data[uw_data.Cstm_Scenario]["Rent_SF"])

            uw_data.C_Econ_Vacancy[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Econ_Vacancy[uw_data.Cstm_Yr_Input] + \
                        scenario_data[uw_data.Cstm_Scenario]["Econ_Vacancy"]

            uw_data.C_Rental_Income[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Rental_Income[uw_data.Cstm_Yr_Input] + \
                        scenario_data[uw_data.Cstm_Scenario]["Rental_Income"]

            uw_data.C_Other_Income[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Other_Income[uw_data.Cstm_Yr_Input] + \
                        scenario_data[uw_data.Cstm_Scenario]["Rental_Income"]

            uw_data.C_Expense_Escalators[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Expense_Escalators[uw_data.Cstm_Yr_Input] + \
                        scenario_data[uw_data.Cstm_Scenario]["Expense_Escalators"]

        #Custom Scenarios
        elif uw_data.Cstm_Scenario ==  "Custom":
            uw_data.C_MarketRent_Per_SF = uw_data.C_MarketRent_Per_SF * (1 + uw_data.Cstm_Mkt_Rent_SF)

            uw_data.C_Econ_Vacancy[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Econ_Vacancy[uw_data.Cstm_Yr_Input] + uw_data.Cstm_Econ_Vacancy

            uw_data.C_Rental_Income[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Rental_Income[uw_data.Cstm_Yr_Input] + uw_data.Cstm_Rental_Income

            uw_data.C_Other_Income[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Other_Income[uw_data.Cstm_Yr_Input] + uw_data.Cstm_Other_Income

            uw_data.C_Expense_Escalators[uw_data.Cstm_Yr_Input] = \
                    uw_data.C_Expense_Escalators[uw_data.Cstm_Yr_Input] + uw_data.Cstm_Expense_Esc


def compute_basic_terms(uw_data):
    global C_GPR
    global PF_Net_Rental_Income
    global Gross_Potential_Rental_Income
    global PF_Econ_Vacancy
    global PF_Other_Income
    global PF_Net_Operating_Income
    global PF_Gross_Operating_Income
    global PF_Operating_Expenses
    global C_Sources_Total
    global PF_Net_Operating_Income
    global Capital_Exp_Res
    global Prof_Svc
    global Asset_Mgmt_Fee
    global C_LP_Equity
    global C_GP_Equity
    global Total_Mortgage_Payments
    global PF_Gross_Cash_Flow
    global PF_Partnership_Cash_Flow
    global Refinance_Loan_Amount_Max
    global Property_Val_Term_Cap
    global Projected_Sales_Price_Capitalized_Value
    global Mortgage_1_Bal
    global Gross_Equity_Position
    global Adjusted_Projected_Sales_Price
    global Partnership_Equity_Position
    global IRR_Base
    
    apply_scenarios(uw_data)

    C_GPR = GPR(uw_data.C_NRSF, uw_data.C_MarketRent_Per_SF)
    
    Gross_Potential_Rental_Income = GPRI(C_GPR, uw_data.C_Rental_Income)
    
    PF_Econ_Vacancy = econ_vacancy(Gross_Potential_Rental_Income, uw_data.C_Econ_Vacancy, C_GPR, uw_data.C_NRI)  
    
    PF_Other_Income = other_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy, \
                                   uw_data.C_Other_Income_Yr0, uw_data.C_Other_Income)
    
    PF_Net_Operating_Income = net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy)
    
    PF_Net_Rental_Income = net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy)
    
    PF_Gross_Operating_Income = gross_operating_income(Gross_Potential_Rental_Income,     \
                                                           PF_Econ_Vacancy, PF_Other_Income, PF_Net_Rental_Income)
    
    PF_Operating_Expenses = operating_expense(uw_data.C_NRSF, uw_data.C_Market_Exp_Per_SF, uw_data.C_Market_Exp_Per_SF_Yr1,  \
                                                     uw_data.C_Expense_Escalators)
    
    C_Sources_Total, C_LP_Equity, C_GP_Equity = total_sources(uw_data.C_Purchase_Price, uw_data.C_Closing_Costs, \
        uw_data.C_Capex, uw_data.C_Interest_Reserve, uw_data.C_Misc, uw_data.C_Debt_Balance, \
              uw_data.C_Sponsor_Promote_Co_Invest, uw_data.C_Sub_Debt,       \
                uw_data.C_Preferred_Equity)
    
    PF_Net_Operating_Income = net_operating_income(PF_Gross_Operating_Income, PF_Operating_Expenses)
    
    Capital_Exp_Res = capital_exp_res(uw_data.C_No_of_Units, uw_data.C_Capital_Reserve_Per_Unit)
    
    Prof_Svc, Asset_Mgmt_Fee = compute_fees(PF_Gross_Operating_Income, uw_data.C_Prof_Svc, uw_data.C_Asset_Mgmt_Fee)
    
    Total_Mortgage_Payments = total_mortgage_payments(uw_data.C_Yr_of_Refinance, mortg_refi, mortg_acq)
    
    PF_Gross_Cash_Flow = gross_cash_flow(PF_Net_Operating_Income, Capital_Exp_Res, Prof_Svc, Asset_Mgmt_Fee, \
        Total_Mortgage_Payments)
    
    PF_Partnership_Cash_Flow = partnership_cash_flow(PF_Gross_Cash_Flow, uw_data.C_Preferred_Return, \
        uw_data.C_Promote_Wtd_Avg)
    
    Property_Val_Term_Cap = property_val_term_cap(PF_Net_Operating_Income, Capital_Exp_Res,  \
                             uw_data.C_Terminal_Cap_Rate, uw_data.C_CAP_NOI)
    
    Refinance_Loan_Amount_Max = refinance_ln_amt_max(uw_data.C_Financing_Cost, Property_Val_Term_Cap, \
                                                       uw_data.C_LTV, PF_Net_Operating_Income, \
                                                        uw_data.C_DCR, uw_data.C_Loan_Constant, uw_data.C_CAP_NOI)
    
    #Pro Forma row 62
    
    Mortgage_1_Bal = calc_mortgage_1_balance(uw_data.C_Yr_of_Refinance)

    Gross_Equity_Position, Adjusted_Projected_Sales_Price, Partnership_Equity_Position =  calc_gross_equity_position(Property_Val_Term_Cap, uw_data.C_Co_Invest, uw_data.C_Selling_Expenses, Mortgage_1_Bal)

    IRR_Base = calc_IRR_base(uw_data.Exit_Yr, C_LP_Equity, C_GP_Equity, PF_Partnership_Cash_Flow, \
                             Gross_Equity_Position)

#Compute C_Exit_Yield_On_Cost
def compute_exit_yield_on_cost(Exit_Yr):
    return((PF_Net_Operating_Income[Exit_Yr] - Capital_Exp_Res)*100/C_Sources_Total)

#Compute Net Profit

def compute_net_profit(Exit_Yr, Partnership_Equity_Position, C_LP_Equity, C_GP_Equity):
     
    #Refinance_Loan_Amount_Max = (1 - C_Financing_Cost) * min(p_v_t_c * C_LTV, PF_Net_Operating_Income[Exit_Yr]/C_DCR/C_Loan_Constant)
    Cash_Out_Refinance = 0

    #Finally Net Profit
    Net_Profit = Partnership_Equity_Position[Exit_Yr] + sum(PF_Partnership_Cash_Flow[:Exit_Yr+1]) +                     Cash_Out_Refinance - C_LP_Equity - C_GP_Equity
    
    print(Net_Profit)

    return (np.round(Net_Profit))


#[191]:

# The webapp starts here
app = FastAPI()

@app.post("/calcUWkpi/")
async def calc_uw_kpi(uw_data: UWBaseIn):

    compute_basic_terms(uw_data)

    o_exit_yield_on_cost = compute_exit_yield_on_cost(uw_data.Exit_Yr)
    o_net_profit = compute_net_profit(uw_data.Exit_Yr, Partnership_Equity_Position,  \
                                         C_LP_Equity, C_GP_Equity)

    ctr = 0
    for key, val in IRR_Base.items():
        if val < 0:
            ctr += 1

    if ctr > 1:
        o_project_irr = "err"
    else:
        o_project_irr = np.round(xirr(IRR_Base) * 100, 2)

    out = {'Exit_Yield_On_Cost': o_exit_yield_on_cost,
           'Net_Profit': o_net_profit,
           'IRR': o_project_irr}

    return (out)