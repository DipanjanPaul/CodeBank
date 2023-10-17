# coding: utf-8

from fastapi import FastAPI
from starlette.requests import Request
from typing import Union

from pydantic import BaseModel

import pandas as pd
import numpy as np

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
    C_Other_Income: list
    C_Expense_Escalators: list
    #Monthly Lease by Year
    C_Other_Income_Y1: list
    C_Other_Income_Y2 : list
    C_Loss_to_Lease_Y0: float
    C_Loss_to_Lease_Y1: list
    C_Loss_to_Lease_Y2: list
    C_Loss_to_Lease_Y3: list
    C_Loss_to_Lease_Y3_Future: float

    C_Econ_Vacancy_Y1: list
    C_Econ_Vacancy_Y2: list
    C_Econ_Vacancy_Y3: list
    C_Econ_Vacancy: float


mortg_refi = pd.read_csv("mortgage_refi.csv", header=0)
mortg_acq = pd.read_csv("mortgage_acq.csv", header=0)

#Calculated Fields
def GPR(C_NRSF, C_MarketRent_Per_SF):
    return(C_NRSF * C_MarketRent_Per_SF) * 12 #C24=(C18*C19)*12

#Compute Gross Potential Rental Income (Growth Rate)
def GPRI(C_GPR, C_Rental_Income):
    Gross_Potential_Rental_Income = [] #H6

    val = C_GPR
    Gross_Potential_Rental_Income.append(val)
    for n in C_Rental_Income:
        val = (val*(1+n))
        Gross_Potential_Rental_Income.append(val)
        
    return(Gross_Potential_Rental_Income)

#Compute Econ Vacancy - PF Row 16 
def econ_vacancy(Gross_Potential_Rental_Income, C_Econ_Vacancy_Y1, C_Econ_Vacancy_Y2, C_Econ_Vacancy_Y3, C_Econ_Vacancy, C_GPR, C_NRI):
    
    PF_Econ_Vacancy = []
    PF_Econ_Vacancy.append(C_GPR - C_NRI) #Year 0
    PF_Econ_Vacancy.append(Gross_Potential_Rental_Income[1] * np.mean(C_Econ_Vacancy_Y1))
    PF_Econ_Vacancy.append(Gross_Potential_Rental_Income[2] * np.mean(C_Econ_Vacancy_Y2)) #H16
    PF_Econ_Vacancy.append(Gross_Potential_Rental_Income[3] * np.mean(C_Econ_Vacancy_Y3)) #H16

    for itm in Gross_Potential_Rental_Income[4:]:
        #print(itm)
        PF_Econ_Vacancy.append(itm * C_Econ_Vacancy)

    return (PF_Econ_Vacancy)

#Compute Other Income
def other_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy, C_Other_Income_Yr0, C_Other_Income_Y1, C_Other_Income_Y2, C_Other_Income):
    
    PF_Other_Income = []
    PF_Other_Income.append(C_Other_Income_Yr0)
    PF_Other_Income.append((Gross_Potential_Rental_Income[1] - PF_Econ_Vacancy[1]) * np.mean(C_Other_Income_Y1))
    PF_Other_Income.append((Gross_Potential_Rental_Income[2] - PF_Econ_Vacancy[2]) * np.mean(C_Other_Income_Y2))

    val = PF_Other_Income[2]

    for n in C_Other_Income[2:]:
        val = val*(1+n)

        PF_Other_Income.append(val) #N23

    return (PF_Other_Income)

#Compute Net Rental Income
def net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy):
    PF_Net_Rental_Income = []
    for i in range(10):
        PF_Net_Rental_Income.append(Gross_Potential_Rental_Income[i] - PF_Econ_Vacancy[i])

    return (PF_Net_Rental_Income)

#Compute Gross Operating Income N26 **** check logic
def gross_operating_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy, PF_Other_Income, PF_Net_Rental_Income):
    PF_Gross_Operating_Income = []
    PF_Gross_Operating_Income.append(PF_Other_Income[0] + PF_Net_Rental_Income[0])
    for i in range(1,11):
        #print(i)
        PF_Gross_Operating_Income.append(Gross_Potential_Rental_Income[i] - PF_Econ_Vacancy[i] + PF_Other_Income[i])

    return (PF_Gross_Operating_Income)

#Compute Operating Expenses N38
def operating_expense(C_NRSF, C_Market_Exp_Per_SF, C_Market_Exp_Per_SF_Yr1, C_Expense_Escalators):
    
    PF_Operating_Expenses = []
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF)
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF_Yr1)
    PF_Operating_Expenses.append(C_NRSF * C_Market_Exp_Per_SF_Yr1*(1+C_Expense_Escalators[2]))

    val = PF_Operating_Expenses[2]
    for n in C_Expense_Escalators[2:]:
        val = val*(1+n)
        PF_Operating_Expenses.append(val) #N23

    return (PF_Operating_Expenses)

#Compute Total Sources K27
def total_sources(C_Purchase_Price, C_Closing_Costs, C_Capex, C_Interest_Reserve, C_Misc, C_Debt_Balance, \
                      C_Sponsor_Promote_Co_Invest, C_Sub_Debt, C_Preferred_Equity):
    C_Uses_Total = C_Purchase_Price + C_Closing_Costs + C_Capex + C_Interest_Reserve + C_Misc
    C_LP_Equity = (C_Uses_Total - C_Debt_Balance) * (1 - C_Sponsor_Promote_Co_Invest)
    C_GP_Equity = (C_Uses_Total - C_Debt_Balance) * (C_Sponsor_Promote_Co_Invest)

    C_Sources_Total = C_Debt_Balance + C_Sub_Debt + C_Preferred_Equity + C_LP_Equity + C_GP_Equity
    return (C_Sources_Total, C_LP_Equity, C_GP_Equity)

#Compute Net Operating Income N39 = N26 - N38
def net_operating_income(PF_Gross_Operating_Income, PF_Operating_Expenses):
    
    PF_Net_Operating_Income = []

    for i in range(11):
        #print(i)
        PF_Net_Operating_Income.append(PF_Gross_Operating_Income[i] - PF_Operating_Expenses[i])

    return (PF_Net_Operating_Income)

#Compute Captial Expenditures/Reserves N41
def capital_exp_res(C_No_of_Units, C_Capital_Reserve_Per_Unit):    
    Capital_Exp_Res = C_No_of_Units * C_Capital_Reserve_Per_Unit
    return (Capital_Exp_Res)

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

# Compute basic and common items
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
    
    C_GPR = GPR(uw_data.C_NRSF, uw_data.C_MarketRent_Per_SF)
    
    Gross_Potential_Rental_Income = GPRI(C_GPR, uw_data.C_Rental_Income)
    
    PF_Econ_Vacancy = econ_vacancy(Gross_Potential_Rental_Income, uw_data.C_Econ_Vacancy_Y1, uw_data.C_Econ_Vacancy_Y2, \
                                           uw_data.C_Econ_Vacancy_Y3, uw_data.C_Econ_Vacancy, \
                                            C_GPR, uw_data.C_NRI)
    
    PF_Other_Income = other_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy,  \
                                          uw_data.C_Other_Income_Yr0, uw_data.C_Other_Income_Y1, \
                                            uw_data.C_Other_Income_Y2, uw_data.C_Other_Income)
    
    PF_Net_Operating_Income = net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy)
    
    PF_Net_Rental_Income = net_rental_income(Gross_Potential_Rental_Income, PF_Econ_Vacancy)
    
    PF_Gross_Operating_Income = gross_operating_income(Gross_Potential_Rental_Income,                                                        PF_Econ_Vacancy,                                                        PF_Other_Income, PF_Net_Rental_Income)
    
    PF_Operating_Expenses = operating_expense(uw_data.C_NRSF, uw_data.C_Market_Exp_Per_SF, \
                                                      uw_data.C_Market_Exp_Per_SF_Yr1, uw_data.C_Expense_Escalators)
    
    C_Sources_Total, C_LP_Equity, C_GP_Equity = total_sources(uw_data.C_Purchase_Price, uw_data.C_Closing_Costs, uw_data.C_Capex,                                     uw_data.C_Interest_Reserve, uw_data.C_Misc, uw_data.C_Debt_Balance,                                     uw_data.C_Sponsor_Promote_Co_Invest, uw_data.C_Sub_Debt,                                     uw_data.C_Preferred_Equity)
    
    PF_Net_Operating_Income = net_operating_income(PF_Gross_Operating_Income, PF_Operating_Expenses)
    
    Capital_Exp_Res = capital_exp_res(uw_data.C_No_of_Units, uw_data.C_Capital_Reserve_Per_Unit)
    
    Prof_Svc, Asset_Mgmt_Fee = compute_fees(PF_Gross_Operating_Income, uw_data.C_Prof_Svc, uw_data.C_Asset_Mgmt_Fee)

#Compute C_Exit_Yield_On_Cost
def compute_exit_yield_on_cost(Exit_Yr):
    return((PF_Net_Operating_Income[Exit_Yr] - Capital_Exp_Res)*100/C_Sources_Total)

#Compute Net Profit
def compute_net_profit(C_CAP_NOI, Exit_Yr, C_Terminal_Cap_Rate, C_Selling_Expenses, C_Yr_of_Refinance, \
                           C_Preferred_Return, C_Promote_Wtd_Avg, C_Co_Invest, C_Financing_Cost, C_LTV, C_DCR, \
                            C_Loan_Constant, C_LP_Equity, C_GP_Equity):

    if C_CAP_NOI == "Forward":
        Property_Val_Term_Cap = (PF_Net_Operating_Income[Exit_Yr+1] - Capital_Exp_Res)/C_Terminal_Cap_Rate
    else:
        Property_Val_Term_Cap = (PF_Net_Operating_Income[Exit_Yr] - Capital_Exp_Res)/C_Terminal_Cap_Rate

    Projected_Sales_Price_Capitalized_Value = Property_Val_Term_Cap

    Selling_Expense = Projected_Sales_Price_Capitalized_Value * C_Selling_Expenses

    Adjusted_Projected_Sales_Price = Projected_Sales_Price_Capitalized_Value - Selling_Expense

    #Calculate Mortgage_1_Bal
    Mortgage_1_Bal = 0
    if (C_Yr_of_Refinance != 0 & C_Yr_of_Refinance < Exit_Yr):
        Mortgage_1_Bal = mortg_refi[mortg_refi.Period == (Exit_Yr - C_Yr_of_Refinance + 1)*12]['Ending Balance']
    else:
        Mortgage_1_Bal = mortg_acq[mortg_refi.Period == Exit_Yr*12]['Ending Balance']

    Mortgage_2_Bal = 0
    Yield_Maintenance = 0

    Gross_Equity_Position = Adjusted_Projected_Sales_Price - Mortgage_1_Bal - Mortgage_2_Bal + Yield_Maintenance

    Sponsor_Equity_Position = Gross_Equity_Position * C_Co_Invest

    #Part 1 of Net Profit (Based on Exit_Yr)
    Partnership_Equity_Position = Gross_Equity_Position - Sponsor_Equity_Position

    ##Part 2 of Net Profit

    #Total Mortgage Payments
    Total_Mortgage_Payments = []
    Total_Mortgage_Payments.append(0)

    for i in range(1,11):

        if (C_Yr_of_Refinance != 0 & i >= C_Yr_of_Refinance):
            Total_Mortgage_Payments.append(sum(mortg_refi[mortg_refi.Year == i]['Payment ']))
        else:
            Total_Mortgage_Payments.append(sum(mortg_acq[mortg_acq.Year == i]['Payment ']))

    Gross_Cash_Flow = []
    Gross_Cash_Flow.append(0)
    for i in range(1,11):
        Gross_Cash_Flow.append(PF_Net_Operating_Income[i] - Capital_Exp_Res - Prof_Svc[i] - Asset_Mgmt_Fee[i] - Total_Mortgage_Payments[i])

    Partnership_Cash_Flow = []
    Partnership_Cash_Flow.append(0)
    for i in range(1,11):
        Partnership_Cash_Flow.append((Gross_Cash_Flow[i] - C_Preferred_Return)/(1 - C_Promote_Wtd_Avg) + C_Preferred_Return)

    ##Part 3 of Net Profit

    if C_CAP_NOI == "Forward":
        Property_Val_Term_Cap = (PF_Net_Operating_Income[Exit_Yr + 1] - Capital_Exp_Res)/C_Terminal_Cap_Rate
    else:
        Property_Val_Term_Cap = (PF_Net_Operating_Income[Exit_Yr] - Capital_Exp_Res)/C_Terminal_Cap_Rate


    Refinance_Loan_Amount_Max = (1 - C_Financing_Cost) * min(Property_Val_Term_Cap * C_LTV, PF_Net_Operating_Income[Exit_Yr]/C_DCR/C_Loan_Constant)
    Cash_Out_Refinance = 0

    #Finally Net Profit
    Net_Profit = Partnership_Equity_Position + sum(Partnership_Cash_Flow[:Exit_Yr+1]) + Cash_Out_Refinance - C_LP_Equity - C_GP_Equity

    return (np.round(Net_Profit.values[0]))


## The webapp starts here
app = FastAPI()

@app.post("/calcUWkpi/")
async def calc_uw_kpi(uw_data: UWBaseIn):

    compute_basic_terms(uw_data)

    o_exit_yield_on_cost = compute_exit_yield_on_cost(uw_data.Exit_Yr)
    o_net_profit = compute_net_profit(uw_data.C_CAP_NOI, uw_data.Exit_Yr, uw_data.C_Terminal_Cap_Rate, \
                                        uw_data.C_Selling_Expenses, uw_data.C_Yr_of_Refinance, uw_data.C_Preferred_Return, \
                                            uw_data.C_Promote_Wtd_Avg, uw_data.C_Co_Invest, uw_data.C_Financing_Cost, \
                                                uw_data.C_LTV, uw_data.C_DCR, uw_data.C_Loan_Constant, C_LP_Equity, C_GP_Equity)

    out = {'Exit_Yield_On_Cost': o_exit_yield_on_cost,
           'Net_Profit': o_net_profit}

    return (out)