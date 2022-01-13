from binance import Client

import numpy as np
import pandas as pd
import pandas_ta as pta

import json, configparser, pathlib, time, requests, copy, sys, os, keyboard
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
def eula():

    print(  "\nDeclaração de exoneração de responsabilidade\n\n" +
            "Todas as estratégias de investimento e investimentos envolvem risco de perda.\n" +
            "Nada contido neste programa, script ou código deve ser interpretado como conselho de investimento.\n" +
            "Qualquer referência ao desempenho passado ou potencial de um investimento não é, e não deve ser interpretada como recomendação ou como garantia de qualquer resultado ou lucro específico." +
            "\n[bright_yellow]Ao utilizar este programa, aceita todas as responsabilidades, e que não podem ser feitas reclamações contra os programadores, ou outros ligados ao programa.")
    #resp = input("\nSe você concorda com os termos acima, digite 1\n")
    # if not resp == "1":
    #    sys.exit()

eula()
print(os.getlogin() + ' - ' + os.environ['COMPUTERNAME'])
it = 0
pathConf = str(  pathlib.Path(__file__).parent.resolve())   
updater = ConfigUpdater()
updater.read(pathConf+  '\config.ini')
p = para()
client = None


def setup_client():

    configKeys = configparser.ConfigParser()
    configKeys.read_file(open( str(pathlib.Path(__file__).parent.resolve()) + '\secret.ini'))
    actual_api_key = configKeys.get('BINANCE', 'ACTUAL_API_KEY')
    actual_secret_key = configKeys.get('BINANCE', 'ACTUAL_SECRET_KEY')
    test_api_key = configKeys.get('BINANCE', 'TEST_API_KEY')
    test_secret_key = configKeys.get('BINANCE', 'TEST_SECRET_KEY')
    # Setting up connection
    if p.TEST:
        client = Client(test_api_key, test_secret_key)
        client.API_URL = 'https://testnet.binance.vision/api'  # To change endpoint URL for test account  
    else:
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
       
    table_centered = Align.center(table1);
    with Live(table_centered,auto_refresh=False) as live:  # update 4 times a second to feel fluid
        live.update(table_centered)
        if run_time:
            live.console.print('[grey]'+run_time,justify="center")
        live.console.print(f"Waiting for iteration #{it}",justify="right")

def generate_table(dict_) -> Table:
    dict1 = copy.copy(dict_)
    """Make a new table."""
    
    my_dict = json.loads(json.dumps(dict1), parse_int=str,parse_float=str)
    table = Table()
    table = Table(title=":money_with_wings: [bright_yellow]EL TRADER BOT :money_with_wings:" )
    #table.caption = "Trading [cyan]" + p.TRADE_COIN + "[bright_green]" + p.TRADE_MONEY
    table.caption = f"Trading [cyan] {p.TRADE_COIN} [bright_green] {p.TRADE_MONEY}"
    if 'RESULT' in dict1:
        if (my_dict['RESULT']).isalpha() == False:  #isinstance(my_dict['RESULT'], float):
            if  float(dict1['RESULT']) > p.SELL_THRESHOLD:
                my_dict['RESULT'] = '[bright_red]'+str(my_dict['RESULT'])
            if float(dict1['RESULT']) < p.BUY_THRESHOLD:
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
            can_orders.insert( client.cancel_order(symbol=p.TRADE_PAIR,orderId = ords))
        if 'orderId' in ords:
            can_orders.insert( client.cancel_order(symbol=p.TRADE_PAIR,orderId =ords['orderId']))
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

            if asset == p.TRADE_MONEY:
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
        if i[0] == p.TRADE_COIN:
            table.add_row('[green]'+ i[0],'[green]' + i[1])
        elif i[0]== p.TRADE_MONEY:
            table.add_row('[green]' + p.TRADE_MONEY,"[green]" + i[1])
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

def build_dict(data_mn,dDict):
    global it
    it += 1
    start = datetime.now() 
    #data_mn = getminutedata(TRADE_PAIR)
    
    votes = 0 
    dDict = {'Time':datetime.now().strftime("%Y-%m-%d %H:%M:%S"),**dDict}
    close = data_mn.tail(1).to_numpy()[0,0]
    
    #RSI - Relative Strength Index
    rsi_df = pta.rsi(data_mn['Close'], length = p.RSI_LENGTH)
    last_rsi = rsi_df[-1]
    
    #SMA - Simple Moving Average
    """ df_sma20 = pta.sma(data_mn["Close"], length = 20)
    last_sma20 = df_sma20[-1]
    df_sma50 = pta.sma(data_mn["Close"], length = 50)
    last_sma50 = df_sma50[-1]
    sma = last_sma20 - last_sma50 """
    
    #BBANDS - Bollinger Bands
    df_bbands = pta.bbands(data_mn["Close"], length = p.BBAND_LENGTH, mamode=p.BBAND_MAMODE,std= p.BBAND_STD)
    #BBL_20_2.0  BBM_20_2.0  BBU_20_2.0  BBB_20_2.0

    # MACD_12_26_9  MACDh_12_26_9  MACDs_12_26_9
    #df_macd = pta.macd(data_mn["Close"])
        #get last macd signal
    #macds_last = (df_macd['MACDs_'+str(MACD_FAST)+'_'+str(MACD_SLOW)+'_'+str(MACD_SIGNAL)])[-1]
        #get last but one macd signal
    #macds_last1 = (df_macd['MACDs_'+str(MACD_FAST)+'_'+str(MACD_SLOW)+'_'+str(MACD_SIGNAL)])[df_macd.shape[0]-2]

    #STOCH - Stochastic Oscillator
    df_stoch = pta.stoch(data_mn["High"],data_mn["Low"],data_mn["Close"],p.STOCH_K,p.STOCH_D)
    last_STOCH_D = (df_stoch['STOCHd_'+str(p.STOCH_K)+'_'+str(p.STOCH_D)+'_'+str(p.STOCH_SMOOTH_K)])[-1]
    last_STOCH_K = (df_stoch['STOCHk_'+str(p.STOCH_K)+'_'+str(p.STOCH_D)+'_'+str(p.STOCH_SMOOTH_K)])[-1]
    
    bbands_pp =  (df_bbands.iloc[-1].to_dict())['BBP_'+str(p.BBAND_LENGTH)+'_'+str(p.BBAND_STD)]

    #resultado estiver proximo a 1 - compra é recomendado
    #resultado estiver proximo a 0 - venda é recomendado
    """ if last_rsi > RSI_OVERBOUGHT:
        last_rsi = 0
    if last_rsi < RSI_OVERSOLD:
        last_rsi = 1 """

    res_stoch = (last_STOCH_D+last_STOCH_K)/200
    """ if last_STOCH_D > STOCH_OVERBOUGHT and last_STOCH_K >  STOCH_OVERBOUGHT:
        res_stoch = 0
    if last_STOCH_D < STOCH_OVERSOLD and last_STOCH_K < STOCH_OVERSOLD:
        res_stoch = 1 """

    votes += (last_rsi / 100) *p.RSI_WEIGHT
    votes += (bbands_pp) *p.BBAND_WEIGHT
    votes += res_stoch  *p.STOCH_WEIGHT
    #last_STOCH_K = df_stoch
    result = votes / (p.RSI_WEIGHT + p.BBAND_WEIGHT + p.STOCH_WEIGHT)
    
    dDict = {**dDict, 'Close': close}
    dDict = {**dDict, 'RSI': last_rsi}
    #dDict = {**dDict, 'SMA 20': last_sma20}
    #dDict = {**dDict, 'SMA 50': last_sma50}
    dDict = {**dDict, 'STOCH': res_stoch}
    #dDict = {**dDict, 'MACD Last but one': macds_last1}
    #dDict = {**dDict, 'MACD Last': macds_last}
    dDict = {**dDict, 'BBAND': bbands_pp }
    #dDict = {**dDict, 'SMA DIF': sma}
    dDict = {**dDict, 'STOCH D': last_STOCH_D}
    dDict = {**dDict, 'STOCH K': last_STOCH_K}
    dDict = {**dDict, 'RESULT': result}

    newdict = {}
    for x in dDict:
        if isinstance(dDict[x],float):
            newdict[x] = round(dDict[x],3)
        else:
            newdict[x] = dDict[x]


    return newdict

def generate_db_backtest(client):
    global p
    
    coins = ('BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','ADAUSDT','XRPUSDT','DOTUSDT', 'DOGEUSDT','SHIBUSDT','EOSUSDT')
    #data = getminutedata_v2(client,p.TRADE_PAIR,interval='5m',lookback='1',daterange= 'days ago UTC')
    #print (data)
    engine = create_engine('sqlite:///Cryptoprices.db')
   
    for coin in tqdm(coins):
        getminutedata_v2(client,coin,interval='1m',lookback='30',daterange= 'days ago UTC').to_sql(coin,engine,index=False)
    #print(sql.inspect(engine).get_table_names())

def print_openposition(curr_price,buyprice):
    ot_table = Table()
    ot_table.add_column('[blue]Close')
    ot_table.add_column('[cyan]Buy Price')
    ot_table.add_column('[green]Target')
    ot_table.add_column('[red]Stop')
    ot_table.add_row(str(curr_price),str(buyprice),str(buyprice * p.STOP_GAIN),str(buyprice * p.STOP_LOSS) )
    print_all(ot_table,False)

def main():
    
    global it
    global p
    generatedb = False

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
    if p.BACKTEST is True:
        engine = create_engine('sqlite:///Cryptoprices.db')
        if generatedb is True:
            generate_db_backtest(client)

        dataTest = pd.read_sql(p.TRADE_PAIR,engine)
        dataTest = dataTest.set_index('Time')
    #quit()
    #print(client.get_symbol_info(p.TRADE_PAIR))
    #sys.exit()
    #data_mn = getminutedata(client,TRADE_PAIR,interval=INTERVAL,lookback='100')
    #orders = client.get_open_orders()

    open_position = False
    decide =  False
    keep_runnig = True

    #await deu_mierda(client)
    try:
        while keep_runnig is True:
           
            if p.BACKTEST is False:
                data_mn = getminutedata(client,p.TRADE_PAIR,interval='5m',lookback='100')
                if data_mn is None :
                    client = setup_client()
                    data_mn = getminutedata(client,p.TRADE_PAIR,interval='5m',lookback='100')
                    if data_mn is None:
                        break;
            elif p.BACKTEST is True:
                data_mn = dataTest.iloc[it:it+100]
                
            curr_price = float(data_mn['Close'].iloc[-1])
            qty = p.AVAILABLE_MONEY / curr_price
            qty = round(qty,8)
            

            dDict = {'Current Pice' : curr_price }
            if open_position is True:
                dDict = {'Position' : '[green]Comprado' }
            else:
                dDict = {'Position' : '[red]Vendido' }
            dDict = build_dict(data_mn,dDict)
            if p.BACKTEST is False:
                print_all(dDict,run_time='Running for ' + str((datetime.now() - inicio )).split('.')[0])
            #save_dict_as_json(dDict)
            result = float(dDict['RESULT'])
            if result <= p.BUY_THRESHOLD and open_position is False:
                qty = p.AVAILABLE_MONEY / float(curr_price)
                qty = round(qty,8)
                
                if p.TEST_REAL is False:
                    print("ALERTA VOU COMPRAR!")
                    break
                    order = client.create_order(symbol=p.TRADE_PAIR, side='BUY', type='MARKET', quantity=qty)
                else:
                    order = {"symbol": p.TRADE_PAIR,
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
                                fee = order['fills'][0]['commission']
                                profit = profit - fee
                                open_position = True
                                #Time,Side,Amount,Price
                                if p.BACKTEST is False:
                                    fields = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),p.USER,p.TRADE_PAIR,'BUY', str(qty_exec),'-' + str(buyprice), str(fee)]
                                    send_gsheets(fields)
                                its = 5

                               
                    except Exception as e:
                        print(e)

            if open_position:
                #df = getminutedata(client,TRADE_PAIR,'1m', lookback='2')
                df = data_mn.tail(1)
                curr_price =float(df.Close.iloc[-1] )
                if p.BACKTEST is False:
                    if its % 5 == 0:
                        print_openposition(curr_price,buyprice)
                        its = 0
                    its = its + 1

                if result > p.SELL_THRESHOLD or curr_price <= buyprice * p.STOP_LOSS or curr_price >= p.STOP_GAIN * buyprice:
                    if p.TEST_REAL is False:
                        print("ALERTA VOU COMPRAR!")
                        break
                        order = client.create_order(symbol=TRADE_PAIR, side='SELL', type='MARKET', quantity=qty)
                    else:

                        order = {"symbol": p.TRADE_PAIR,
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
                            fee = order['fills'][0]['commission']
                            
                            profit += ((sellprice*qty_exec) - (buyprice*qty )) - fee
                            p.set_ava_money((sellprice*qty_exec))

                            print(f'Profit: {profit}')

                            if p.BACKTEST is False:
                                fields = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),p.USER,p.TRADE_PAIR,'SELL', str(qty_exec), str(sellprice), str(fee)]
                                send_gsheets(fields)
                            open_position = False
                        except Exception as e:
                            print(e)

            if keyboard.is_pressed('Esc'):
                print("\nyou pressed Esc, so exiting...")
                keep_runnig = False

            if p.BACKTEST is False:
                if it % 30 == 0:
                    p = para()
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
    main()
    