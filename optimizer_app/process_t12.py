# coding: utf-8

import pandas as pd
import numpy as np

from fastapi import FastAPI
from starlette.requests import Request

from pydantic import BaseModel


class T12BaseIn(BaseModel):
    inp_location: str
    out_location: str

def process_yearly_file(infile, worksheet):
    #Part 1
    df = pd.read_excel(infile, sheet_name=0, header=0)

    ix = df.apply(lambda x: sum(x.isnull()) == 13, axis=1)
    ix = np.where(ix != True)[0]
    df = df.iloc[ix, :]

    x = ["Catg_SubCatg"]
    x.extend(df.columns[1:])

    df.columns = x

    df.Catg_SubCatg = [x.strip() for x in df.Catg_SubCatg]

    df = df[-df.Catg_SubCatg.str.startswith(tuple(["TOTAL", "NET", "INCOME", "EXPENSE"]))]

    df.reset_index(drop=True, inplace=True)  
    
    #Part 2
    #print(df.head())
    ix = np.where(df.iloc[:, 1:].apply(lambda x: sum(x.isnull())==12, axis=1))[0]

    catg_map = pd.DataFrame(df.iloc[ix,0])
    catg_map['i_start'] = catg_map.index

    i_end = list(catg_map.index[1:].values)
    i_end.append(df.shape[0])
    catg_map['i_end'] = i_end

    catg_map['repeat_cnt'] = catg_map.i_end - catg_map.i_start
    catg_map.reset_index(drop=True, inplace=True)
    
    x = catg_map.apply(lambda x: list(np.repeat(x[0].strip(), x[3])), axis=1)
    catg = [itm for sublist in x for itm in sublist]

    df['Category'] = catg
    df.drop(index=ix, inplace=True)
    df.reset_index(drop=True, inplace=True)

    #Part 3
    df.columns = ['SubCategory', '01_JAN', '02_FEB', '03_MAR', '04_APR', '05_MAY', '06_JUN', '07_JUL',
                  '08_AUG', '09_SEP', '10_OCT', '11_NOV', '12_DEC', 'Category']

    df = df[['Category', 'SubCategory', '01_JAN', '02_FEB', '03_MAR', '04_APR', '05_MAY', '06_JUN', '07_JUL',
                  '08_AUG', '09_SEP', '10_OCT', '11_NOV', '12_DEC']]

    
    #Part 4
    df = df.melt(id_vars=['Category', 'SubCategory'],
                  value_vars=['01_JAN', '02_FEB', '03_MAR', '04_APR', '05_MAY', '06_JUN', 
                              '07_JUL', '08_AUG', '09_SEP', '10_OCT', '11_NOV', '12_DEC'])
    
    
    df.columns = ['Category', 'SubCategory', 'MM', 'Value']
    df.SubCategory = [x.strip() for x in df.SubCategory]

    df['P_Year'] = worksheet
    return(df)

def processT12(inp, out):

    try:
        wb_sheets = pd.ExcelFile(inp).sheet_names

        #print(wb_sheets)

        final = []
        for itm in wb_sheets:
            print(itm)
            final.append(process_yearly_file(inp, itm))

        final_df = pd.concat(final, axis=0)

        final_df.to_csv(out, header=True, index=False)
        return(out)
    except:
        return None

## The webapp starts here
app = FastAPI()

@app.post("/processt12/")
async def reformat_t12(request: T12BaseIn):

    return (processT12(request.inp_location, request.out_location))