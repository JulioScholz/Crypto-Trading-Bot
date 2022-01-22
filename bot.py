from binance import Client

import numpy as np
import pandas as pd
import pandas_ta as pta
import json
import configparser
import pathlib
import time
import requests
import copy
import sys
import os
import keyboard
import socket

from tqdm import tqdm
from parameters import paraClass as para
from configupdater import ConfigUpdater
from datetime import datetime
from rich import print
from rich.table import Table
from rich.live import Live
from rich.align import Align
#import sqlalchemy as sql
from sqlalchemy import create_engine


## printing the hostname and ip_address

def eula():
    print(  "\nDeclaração de exoneração de responsabilidade\n\n" +
            "Todas as estratégias de investimento e investimentos envolvem risco de perda.\n" +
            "Nada contido neste programa, script ou código deve ser interpretado como conselho de investimento.\n" +
            "Qualquer referência ao desempenho passado ou potencial de um investimento não é, e não deve ser interpretada como recomendação ou como garantia de qualquer resultado ou lucro específico." +
            "\n[bright_yellow]Ao utilizar este programa, aceita todas as responsabilidades, e que não podem ser feitas reclamações contra os programadores, ou outros ligados ao programa.")
    #resp = input("\nSe você concorda com os termos acima, digite 1\n") # if not resp == "1":  #    sys.exit()

def setup_client():
    global client
    config_keys = configparser.ConfigParser()
    config_keys.read_file(open( str(pathlib.Path(__file__).parent.resolve()) + os.sep + 'secret.ini'))
    # Setting up connection
    if P.TEST:
        test_api_key = config_keys.get('BINANCE', 'TEST_API_KEY')
        test_secret_key = config_keys.get('BINANCE', 'TEST_SECRET_KEY')
        client = Client(test_api_key, test_secret_key)
        client.API_URL = 'https://testnet.binance.vision/api'  # To change endpoint URL for test account
    else:
        actual_api_key = config_keys.get('BINANCE', 'ACTUAL_API_KEY')
        actual_secret_key = config_keys.get('BINANCE', 'ACTUAL_SECRET_KEY')
        client = Client(actual_api_key, actual_secret_key)

    return client
    
def getminutedata(client,symbol, interval='1m', lookback='120', daterange = ' min ago UTC' ):
    try :
        frame = pd.DataFrame( client.get_historical_klines (symbol, interval, lookback + daterange))
        frame = frame.iloc[:,:6]
        frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        frame['Time'] = pd.to_datetime(frame['Time'], unit='ms')
        frame['Time'] -= pd.Timedelta(hours=3)
        frame = frame.set_index('Time')

        for col in  ['Open', 'High', 'Low', 'Close', 'Volume']:
            frame[col] = frame[col].astype(float)

        return frame

    except requests.exceptions.ReadTimeout :
        print('Something went wrong. Error occured at %s.' % (datetime.datetime.now()))
        return None

def getminutedata_v2(client,symbol, interval='1m', lookback='120', daterange = ' min ago UTC' ):
    frame = pd.DataFrame( client.get_historical_klines (symbol, interval, lookback + daterange))
    frame = frame.iloc[:,:5]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close']
    frame['Time'] = pd.to_datetime(frame['Time'], unit='ms')
    frame['Time'] -= pd.Timedelta(hours=3)

    for col in  ['Open', 'High', 'Low', 'Close']:
        frame[col] = frame[col].astype(float)

    return frame

def get_ticker(symbol):
    try:
        ticker = client.get_ticker(symbol)
        return float(ticker['lastPrice'])
    except Exception as e:
        print('Get Ticker Exception: %s' % e)

def add_row_df(df1,data):
  
    data[0] = pd.to_datetime([data[0]], unit='ms')[0]
    data[0] = pd.Timestamp(data[0]) - pd.Timedelta(hours=3)
    data[1] = float(data[1])
    data[2] = float(data[2])
    data[3] = float(data[3])
    data[4] = float(data[4])
    data[5] = float(data[5])

    tail = df1.tail(1).index.to_numpy()
    if tail[0] != data[0]:
        df1.loc[len(df1)] = data[1:]
        df1.rename(index={(df1.shape[0]-1):data[0]},inplace=True)

    return df1

def save_dict_as_json(source, target = "result.json"):
    with open(f"{pathConf}\\{target}", 'w') as file:
        json_string = json.dumps(source, default=lambda o: o.__dict__, sort_keys=True, indent=2)
        file.write(json_string)

def print_all(table1, make_table = True,run_time=None):
    if make_table:
        table1 = generate_table(table1)
       
    table_centered = Align.center(table1)
    with Live(table_centered,auto_refresh=False) as live:  # update 4 times a second to feel fluid
        live.update(table_centered)
        if run_time:
            live.console.print('[grey]'+run_time,justify="center")
        live.console.print(f"Waiting for iteration #{it}",justify="right")

def generate_table(dict_) -> Table:
    """Make a new table."""
    dict1 = copy.copy(dict_)
    my_dict = json.loads(json.dumps(dict1), parse_int=str,parse_float=str)
    table = Table()
    table = Table(title=":money_with_wings: [bright_yellow]EL TRADER BOT :money_with_wings:" )
    table.caption = f"Trading [cyan] {P.TRADE_COIN} [bright_green] {P.TRADE_MONEY}"
    if 'RESULT' in dict1:
        if (my_dict['RESULT']).isalpha() == False:  #isinstance(my_dict['RESULT'], float):
            if  float(dict1['RESULT']) > P.SELL_THRESHOLD:
                my_dict['RESULT'] = '[bright_red]'+str(my_dict['RESULT'])
            if float(dict1['RESULT']) < P.BUY_THRESHOLD:
                my_dict['RESULT'] = '[bright_green]'+str(my_dict['RESULT'])
            else:
                my_dict['RESULT'] = '[bright_yellow]'+str(my_dict['RESULT'])

    for key, value in my_dict.items():
        table.add_column(key)

    table.add_row(*list( my_dict.values() ))

    return table

def deu_mierda(client,orders):
    can_orders = []
    for ords in orders:
        if isinstance(ords, int):
            can_orders.insert( client.cancel_order(symbol=P.TRADE_PAIR,orderId = ords))
        if 'orderId' in ords:
            can_orders.insert( client.cancel_order(symbol=P.TRADE_PAIR,orderId =ords['orderId']))
            print(can_orders)
    
    return can_orders

def getAssets(info):
    #assets = []
    table = Table()
    table = Table(title=":money_with_wings: [bright_yellow]WALLET :money_with_wings:",show_lines=True )
    #table.caption = "Trading [bright_red]" + TRADE_COIN + "[bright_green]" + TRADE_MONEY

    table.add_column('[bold]Asset')
    table.add_column('[bold]Amount')
    
    #new_d = json.loads(json.dumps(my_dict), parse_int=str,parse_float=str)
    #d = {2:3, 1:89, 4:5, 3:0}
    #od = collections.OrderedDict(sorted(d.items()))
    #od
    d = []
    d_aux = []
    flag_ = True
    #assets = {}
    for index in range(len(info['balances'])):
        asset = info['balances'][index]['asset']
        amount = info['balances'][index]['free']
        if float(amount) > 0:
            if asset == "USDT":
                amount = " $ " + amount
                flag_ = False
            if asset == "BRL":
                amount = "R$ " + amount
                flag_ = False

            if asset == P.TRADE_MONEY:
                flag_ = False

            if flag_:
                d.append((asset,amount))
            else:
                d_aux.append((asset,amount))
            flag_ = True
            #table.add_row(asset,amount)
    #od = collections.OrderedDict(sorted(d.items()))
    d.sort(key=lambda x:x[0])
    d_aux.sort(key=lambda x:x[0])

    d_aux.extend(d)

    for i in d_aux:
        if i[0] == P.TRADE_COIN:
            table.add_row('[green]'+ i[0],'[green]' + i[1])
        elif i[0]== P.TRADE_MONEY:
            table.add_row('[green]' + P.TRADE_MONEY,"[green]" + i[1])
        else:
            table.add_row(str(i[0]),str(i[1]))

    table = Align.center(table)

    return table

def send_gsheets(data, debug= False):
    #https://docs.google.com/forms/d/e/1FAIpQLSfiQVw5cvsQUyLoFN5N4O9FnMhDgRc6tY_uamx6raacMPd6wg/viewform?usp=pp_url&entry.708373730=time&entry.1439661015=user&entry.427604541=amount&entry.1842940957=price
    key = '1FAIpQLSfiQVw5cvsQUyLoFN5N4O9FnMhDgRc6tY_uamx6raacMPd6wg'
    keys =['708373730', '1439661015','18808364','425542830','427604541', '1842940957', '1472867978']
    url = 'https://docs.google.com/forms/d/e/' +key+ '/formResponse'

    i = 0
    string = ''
    for k in keys:
        string = string+'&entry.'+ k + '=' + str(data[i])
        i += 1

    r = requests.post(url, params = string)
    if debug is True:
        print('Posting order on sheets: ' + str(r))

def strategy(data_mn,dDict):
    global it
    it += 1
    start = datetime.now()
    #data_mn = getminutedata(TRADE_PAIR)
    
    votes = 0
    weights = 0
    dDict = {'Time':datetime.now().strftime("%Y-%m-%d %H:%M:%S"),**dDict}
    close = data_mn.tail(1).to_numpy()[0,0]
    
    #RSI - Relative Strength Index
    if P.RSI_WEIGHT > 0:
        rsi_df = pta.rsi(data_mn['Close'], length = P.RSI_LENGTH)
        last_rsi = rsi_df[-1]
    
    #SMA - Simple Moving Average
    """ df_sma20 = pta.sma(data_mn["Close"], length = 20)
    last_sma20 = df_sma20[-1]
    df_sma50 = pta.sma(data_mn["Close"], length = 50)
    last_sma50 = df_sma50[-1]
    sma = last_sma20 - last_sma50 """
    
    

    # MACD_12_26_9  MACDh_12_26_9  MACDs_12_26_9
    if P.MACD_WEIGHT > 0:
        res_macd = -1
        df_macd = pta.macd(data_mn["Close"],P.MACD_FAST,P.MACD_SLOW,P.MACD_SIGNAL)
            #get last macd signal
        column_name = 'MACDh_'+str(P.MACD_FAST)+'_'+str(P.MACD_SLOW)+'_'+str(P.MACD_SIGNAL)
        macd_last = df_macd[column_name][-1]
            #get last but one macd signal
        macd_last1 = df_macd[column_name][df_macd.shape[0]-2]
        #sell
        if macd_last1 >= 0 and macd_last < 0:
            res_macd = 1
        #buy
        if macd_last1 < 0 and macd_last >= 0:
            res_macd = 0
        
            

    #STOCH - Stochastic Oscillator
    if P.STOCH_WEIGHT > 0 :
        df_stoch = pta.stoch(data_mn["High"],data_mn["Low"],data_mn["Close"],P.STOCH_K,P.STOCH_D)
        last_STOCH_D = (df_stoch['STOCHd_'+str(P.STOCH_K)+'_'+str(P.STOCH_D)+'_'+str(P.STOCH_SMOOTH_K)])[-1]
        last_STOCH_K = (df_stoch['STOCHk_'+str(P.STOCH_K)+'_'+str(P.STOCH_D)+'_'+str(P.STOCH_SMOOTH_K)])[-1]
        res_stoch = (last_STOCH_D+last_STOCH_K)/200

    if P.BBAND_WEIGHT > 0 :
        #BBANDS - Bollinger Bands
        df_bbands = pta.bbands(data_mn["Close"], length = P.BBAND_LENGTH, mamode=P.BBAND_MAMODE,std= P.BBAND_STD)
        #BBL_20_2.0  BBM_20_2.0  BBU_20_2.0  BBB_20_2.0
        bbands_pp =  (df_bbands.iloc[-1].to_dict())['BBP_'+str(P.BBAND_LENGTH)+'_'+str(P.BBAND_STD)]

    dDict = {**dDict, 'Close': close}
    
    if P.RSI_WEIGHT > 0 :
        votes += (last_rsi / 100) * P.RSI_WEIGHT
        dDict = {**dDict, 'RSI': last_rsi}
   
    if P.BBAND_WEIGHT > 0 :
        votes += (bbands_pp) * P.BBAND_WEIGHT
        dDict = {**dDict, 'BBAND': bbands_pp }

    if P.STOCH_WEIGHT > 0 :
        votes += res_stoch  * P.STOCH_WEIGHT
        dDict = {**dDict, 'STOCH': res_stoch}
        dDict = {**dDict , 'STOCH D': last_STOCH_D}
        dDict = {**dDict, 'STOCH K': last_STOCH_K}

    if P.MACD_WEIGHT > 0:
        dDict = {**dDict, 'MACD': res_macd}
        if res_macd != -1:
            votes += res_macd * P.MACD_WEIGHT
            weights +=  P.MACD_WEIGHT
        else:
            if votes == 0:
                votes = res_macd
         
        #dDict = {**dDict, 'MACD Last but one': macds_last1}
        #dDict = {**dDict, 'MACD Last': macds_last}
    weights += P.RSI_WEIGHT + P.BBAND_WEIGHT + P.STOCH_WEIGHT

    if weights == 0:
        weights = 1
    result = votes / weights
    
    
    #dDict = {**dDict, 'SMA 20': last_sma20}
    #dDict = {**dDict, 'SMA 50': last_sma50}
    #dDict = {**dDict, 'SMA DIF': sma}
    
    dDict = {**dDict, 'RESULT': result}

    newdict = {}
    for x in dDict:
        if isinstance(dDict[x],float):
            newdict[x] = round(dDict[x],3)
        else:
            newdict[x] = dDict[x]

    return newdict

def generate_db_backtest(client):
    global P
    
    coins = ('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','ADAUSDT','XRPUSDT','DOTUSDT', 'DOGEUSDT','SHIBUSDT','EOSUSDT')
    #data = getminutedata_v2(client,p.TRADE_PAIR,interval='5m',lookback='1',daterange= 'days ago UTC')
    #print (data)
    engine = create_engine('sqlite:///Cryptopricesnew.db')
   
    for coin in tqdm(coins):
        getminutedata_v2(client,coin,interval=P.INTERVAL,lookback='90',daterange= 'days ago UTC').to_sql(coin,engine,index=False)
    #print(sql.inspect(engine).get_table_names())

def print_openposition(curr_price,buyprice):
    ot_table = Table()
    ot_table.add_column('[blue]Close')
    ot_table.add_column('[cyan]Buy Price')
    ot_table.add_column('[green]Target')
    ot_table.add_column('[red]Stop')
    ot_table.add_row(str(curr_price),str(buyprice),str(buyprice * P.STOP_GAIN),str(buyprice * P.STOP_LOSS) )
    print_all(ot_table,False)

def main():
    
    global it
    global P

    start_money = P.AVAILABLE_MONEY
    generatedb = False
    operacao = 0
    inicio = datetime.now()
    client = setup_client()
    info = client.get_account()
    assests =  getAssets(info)
    print(assests)
    profit = 0
    argv = sys.argv[1:]
    if argv:
        if argv[0] == 'ass':
            quit()
    if P.BACKTEST is True:
        engine = create_engine('sqlite:///Cryptoprices'+ P.INTERVAL+'.db')
        if generatedb is True:
            generate_db_backtest(client)

        dataTest = pd.read_sql(P.TRADE_PAIR,engine)
        dataTest = dataTest.set_index('Time')
    #quit()
    #print(client.get_symbol_info(p.TRADE_PAIR))
    #sys.exit()
    #data_mn = getminutedata(client,TRADE_PAIR,interval=INTERVAL,lookback='100')
    #orders = client.get_open_orders()

    open_position = False
    keep_runnig = True

    #await deu_mierda(client)
    try:
        while keep_runnig is True:
           
            if P.BACKTEST is False:
                data_mn = getminutedata(client,P.TRADE_PAIR,interval=P.INTERVAL,lookback='40')
                if data_mn is None :
                    client = setup_client()
                    data_mn = getminutedata(client,P.TRADE_PAIR,interval=P.INTERVAL,lookback='80')
                    if data_mn is None:
                        break
            elif P.BACKTEST is True:
                data_mn = dataTest.iloc[it:it+40]
                
            curr_price = float(data_mn['Close'].iloc[-1])
            qty = P.AVAILABLE_MONEY / curr_price
            qty = round(qty,8)
            

            dDict = {'Current Pice' : curr_price }
            if open_position is True:
                dDict = {'Position' : '[green]Comprado' }
            else:
                dDict = {'Position' : '[red]Vendido' }
            dDict = strategy(data_mn,dDict)
          
            if P.BACKTEST is False:
                print_all(dDict,run_time='Running for ' + str((datetime.now() - inicio )).split('.')[0])
            #save_dict_as_json(dDict)
            result = float(dDict['RESULT'])
            if result <= P.BUY_THRESHOLD and result >= 0 and open_position is False:
                qty = P.AVAILABLE_MONEY / float(curr_price)
                qty = round(qty,8)
                
                if P.TEST_REAL is False:
                    print("ALERTA VOU COMPRAR!")
                    break
                    order = client.create_order(symbol=p.TRADE_PAIR, side='BUY', type='MARKET', quantity=qty)
                else:
                    order = {"symbol": P.TRADE_PAIR,
                        "orderId": 28,
                        "orderListId": -1,
                        "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                        "transactTime": 1507725176595,
                        "price": curr_price,
                        "origQty": qty,
                        "executedQty": qty,
                        "cummulativeQuoteQty": "10.00000000",
                        "status": "FILLED",
                        "timeInForce": "GTC",
                        "type": "MARKET",
                        "side": "BUY",
                        "fills": [
                        {"price": curr_price,
                        "qty": qty,
                        "commission": (curr_price*qty*0.00075),
                        "commissionAsset": "USDT"}]}
                    try:

                        #print(order)
                        
                        if 'fills' in order:
                            if order['fills'] != []:
                                buyprice = float(order['fills'][0]['price'])
                                qty_exec = order['fills'][0]['qty']
                                qty_exec = round(qty_exec,8)
                                buy_fee = order['fills'][0]['commission']
                                open_position = True
                                #Time,Side,Amount,Price
                                if P.BACKTEST is False:
                                    fields = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),P.USER,P.TRADE_PAIR,'BUY', str(qty_exec),'-' + str(buyprice), str(fee)]
                                    send_gsheets(fields)
                                elif P.BACKTEST is True and P.DEBUG_BACKTEST is True:
                                    dDict['Position'] = "[green]Buying"
                                    print_all(dDict,run_time='Running for ' + str((datetime.now() - inicio )).split('.')[0])
                                its = 5
                        #print
                               
                    except Exception as e:
                        print(e)

            if open_position:
                #df = getminutedata(client,TRADE_PAIR,'1m', lookback='2')
                df = data_mn.tail(1)
                curr_price =float(df.Close.iloc[-1] )
                if P.BACKTEST is False:
                    if its % 5 == 0:
                        print_openposition(curr_price,buyprice)
                        its = 0
                    its = its + 1

                if result > P.SELL_THRESHOLD or curr_price <= buyprice * P.STOP_LOSS or curr_price >= P.STOP_GAIN * buyprice:
                    if P.TEST_REAL is False:
                        print("ALERTA VOU COMPRAR!")
                        break
                        order = client.create_order(symbol=TRADE_PAIR, side='SELL', type='MARKET', quantity=qty)
                    else:

                        order = {"symbol": P.TRADE_PAIR,
                                "orderId": 28,
                                "orderListId": -1,
                                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                                "transactTime": 1507725176595,
                                "price": curr_price,
                                "origQty": "10.00000000",
                                "executedQty": "10.00000000",
                                "cummulativeQuoteQty": "10.00000000",
                                "status": "FILLED",
                                "timeInForce": "GTC",
                                "type": "MARKET",
                                "side": "SELL",
                                "fills": [
                                        {"price": curr_price,
                                        "qty": qty,
                                        "commission": (curr_price*qty*0.00075),
                                        "commissionAsset": "USDT"}]
                                }
                        
                        try:
                            #order = client.create_test_order(symbol=p.TRADE_PAIR, side='SELL', type='MARKET', quantity=qty_exec)
                        
                            sellprice = float(order['fills'][0]['price'])
                            qty_exec = order['fills'][0]['qty']
                            sell_fee = order['fills'][0]['commission']
                            
                            #profit += ((sellprice*qty_exec) - (buyprice*qty )) - fee
                            
                            #p.set_ava_money((sellprice*qty_exec))
                            fee = buy_fee + sell_fee
                            P.set_ava_money(P.AVAILABLE_MONEY + ((sellprice*qty_exec) - (buyprice*qty )) - fee)
                            profit =  P.AVAILABLE_MONEY  - start_money
                            operacao += 1
                           

                            if P.BACKTEST is False:
                                fields = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),P.USER,P.TRADE_PAIR,'SELL', str(qty_exec), str(sellprice), str(fee)]
                                send_gsheets(fields)
                            elif P.BACKTEST is True and P.DEBUG_BACKTEST is True:
                                dDict['Position'] = "[red]Selling"
                                print_all(dDict,run_time='Running for ' + str((datetime.now() - inicio )).split('.')[0])
                            print(f'it: {it}. op {operacao}. Profit: {profit} - Av Money: {P.AVAILABLE_MONEY}')
                            open_position = False
                        except Exception as e:
                            print(e)

            if keyboard.is_pressed('Esc'):
                print("\nyou pressed Esc, so exiting...")
                keep_runnig = False

            if keyboard.is_pressed('p'):
                input("Paused, insert enter to continue...")

            if P.BACKTEST is False:
                if it % 30 == 0:
                    P = para()
                if open_position is True:
                    time.sleep(5)
                else:
                    time.sleep(10)
            else:
                if it+100 == dataTest.shape[0]:
                    keep_runnig = False
            #keep_runnig = False
    except KeyboardInterrupt:
        print('Closing the connection!')
        client.close_connection()

if __name__ == "__main__":
    eula()

    hostname = socket.gethostname()
    ip_address = socket.gethostbyname( hostname )
    print(os.getlogin() + ' - ' + hostname + ' - ' +  ip_address)

    it = 0
    pathConf = str(  pathlib.Path(__file__).parent.resolve())
    updater = ConfigUpdater()
    updater.read(pathConf+ os.sep + 'config.ini')
    P = para()
    client = None

    main()
