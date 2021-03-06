#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 15:25:20 2018

@author: jbuckley
"""
import os
import pandas as pd
import pygsheets
from IPython.display import display, clear_output
from ipywidgets import Layout, Button, Box, VBox, Label, ToggleButtons, HBox


def get_data(csv_directory, latest_csv):
        """
        Authorizes Google API use based on client_secret file. 
        x = user directory that contains that file
        directory ex: '/Users/jbuckley/Google Drive/Dashboard_lite/data_files_STAYOUT'
        latest_csv ex: '2018_01_07_db_full.csv'
        """
        os.chdir(csv_directory)
        df_all = pd.read_csv(latest_csv,dtype={'int sessions':float})
        df_all = df_all.drop('Unnamed: 0', 1)

        column_order = ['site', 'Date', 'Advertiser', 'Order', 'Ad unit', 'Line item ID',
           'Line item', 'Creative ID', 'Creative', 'placement', 'device',
           'DFP Creative ID Impressions', 'DFP Creative ID Clicks',
           'Normalized 3P Impressions', 'Normalized 3P Clicks',
           'Ad server Active View viewable impressions', 'result_5', 'result_75',
           'result_90', 'result_100', 'int sessions', 'interactions',
           'creative.type', 'creative.name', 'version', 'creative.name.version',
           'adunit']
        test = list(df_all.columns == column_order)

        if False in test:
            number = test.index(False)
            print("Columns out of order, starting with: ",column_order[number])
            try:
                df_all = df_all[column_order]
                print("Status: Fixed")
            except:
                return("Status: Not fixed")
        else: 
            None

        return(df_all)
        

def orders_in_date_range(df,start_date,end_date):
    """
    Only returns list of Advertisers and Orders live during this date range
    start_date = '2018-01-01'
    end_date = '2018-01-07'
    """
    client_list=[]
    order_list=[]
    dft = df[(df['Date']>=start_date) & (df['Date']<=end_date)].copy()
    
    for campaign in set(dft['Order']):
        if 'TEST' in campaign.upper():
            pass    # continue here
        else:
            dftc = dft[dft['Order']==campaign]
            Advert = list(set(dftc['Advertiser']))
            client_list.extend(Advert)
            order_list.append(campaign)
    order_list = sorted(order_list)
    client_list = sorted(list(set(client_list)))
    print(str(len(order_list))+" clients")
    return(client_list,order_list)

def log_progress(sequence, every=None, size=None, name='Advertiser Progress'):
    from ipywidgets import IntProgress, HTML, VBox
    from IPython.display import display

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    progress.value = index
                    label.value = u'{name}: {index} / {size}'.format(
                        name=name,
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}".format(
            name=name,
            index=str(index or '?')
        )
        
def google_order_write(df,order,gc):
    """
    Feed dataframe into function. Function slices advertiser and order, finds google sheet,
    and slots data into the data tab.
    """
    dft = []
    dft = df[df['Order']==order].copy()
    advert = list(set(dft['Advertiser']))[0]
    
    if 'TEST' in order.upper():
        pass    # continue here
    else:
        #dft['creative.name'] = dft.fillna('no match')
        dft = dft.sort_values('int sessions',ascending=False)
        dft = dft.fillna('')
        dft['int sessions'] = dft['int sessions'].replace('',0)
        try:
            google_sheet = gc.open(advert +' '+ order + '.xlsx')
            data = google_sheet.worksheet('title','data')
            data.clear()
            try:
                google_sheet.del_worksheet(google_sheet.worksheet_by_title('producer'))
            except:
                pass
            try:
                google_sheet.del_worksheet(google_sheet.worksheet_by_title('creative'))
            except:
                pass
            try:
                google_sheet.del_worksheet(google_sheet.worksheet_by_title('line item'))
            except:
                pass
            data.set_dataframe(dft,'A1',copy_head=True)
            print("Success:",advert,order)
        except:
            print("Try again:",advert,order)
            try:
                data.add_rows(100)
                data.set_dataframe(dft,'A1',copy_head=True)
                print("Success:",advert,order)
            except:
                print("Failure:",advert,order)
                pass

#client_list, order_list = orders_in_date_range(df,'2018-01-07','2018-01-07')
item_layout = Layout(height='50px', min_width='100px')
box_layout = Layout(overflow_x='scroll',
     border='3px solid black',
     width='100%',
     height='100%',
     flex_direction='column',
     display='flex')

def on_client_clicked(b):
    clear_output()
    df = data
    dfx = df[df['Advertiser']==b.description].copy()
    y = sorted(list(set(dfx['Order'])))
    camp_layout = Layout(height='50px', min_width='300px')
    camp_buttons = [Button(layout=camp_layout, description=str(campaign), button_style='info') for campaign in y]
    for button in camp_buttons:
        button.on_click(on_order_clicked)
    carousel = Box(children=camp_buttons, layout=box_layout)
    return(display(carousel))
    
def button_creator(client_list):
    client_items = [Button(layout=item_layout, description=str(client), button_style='info') for client in client_list]
    box_1 = HBox(client_items[0:9])
    box_2 = HBox(client_items[9:18])
    box_3 = HBox(client_items[18:27])
    box_4 = HBox(client_items[27:36])
    box_5 = HBox(client_items[36:45])
    box_6 = HBox(client_items[45:54])
    boxes = [Label('Choose client:'),box_1, box_2,box_3,box_4,box_5,box_6]
    for button in client_items:
        button.on_click(on_client_clicked)
    client_updates=VBox(boxes)
    return(client_updates)
    
def on_order_clicked(b):
    clear_output()
    df = get_data(csv_data_dir,latest_csv)
    dfx = df[df['Order']==b.description].copy()
    try:
        advert = list(set(dfx['Advertiser']))[0]
    except:
        print("no advert for "+ b.description)
    
    dfx['creative.name'] = dfx.fillna('no match')
    dfx = dfx.sort_values('int sessions',ascending=False)
    dfx = dfx.fillna('')
    dfx['int sessions'] = dfx['int sessions'].replace('',0)
    try:
        google_sheet = gc.open(advert +' '+ b.description + '.xlsx')
        data = google_sheet.worksheet('title','data')
        data.clear()
        try:
            google_sheet.del_worksheet(google_sheet.worksheet_by_title('producer'))
        except:
            pass
        try:
            google_sheet.del_worksheet(google_sheet.worksheet_by_title('creative'))
        except:
            pass
        try:
            google_sheet.del_worksheet(google_sheet.worksheet_by_title('line item'))
        except:
            pass
        data.set_dataframe(dfx,'A1',copy_head=True)
        print("Success:",advert,b.description)
    except:
        print("Try again:",advert,b.description)
        try:
            data.add_rows(100)
            data.set_dataframe(dfx,'A1',copy_head=True)
            print("Success:",advert,b.description)
        except:
            print("Failure:",advert,b.description)
            pass
    return(display(dfx))

 