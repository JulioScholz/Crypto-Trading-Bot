
import configparser, pathlib

class paraClass:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read_file( open(str(  pathlib.Path(__file__).parent.resolve())  +  '\config.ini') )

        P = 'PARAMETERS'
        self.TEST =         bool(config['APP'].getboolean('TEST'))
        self.TEST_REAL =    bool(config['APP'].getboolean('TEST_REAL'))
        self.BACKTEST =     bool(config['APP'].getboolean('BACKTEST'))
        self.USER =         config['APP']['USER']
        self.INTERVAL =     config['APP']['INTERVAL']
        self.SELL_THRESHOLD = float(config['APP']['SELL_THRESHOLD'])
        self.BUY_THRESHOLD =  float(config['APP']['BUY_THRESHOLD'])
        self.STOP_LOSS =    float(config['APP']['STOP_LOSS'])
        self.STOP_GAIN =    float(config['APP']['STOP_GAIN'])

        self.TRADE_COIN =   config['ASSESTS']['TRADE_COIN'] 
        self.TRADE_MONEY =  config['ASSESTS']['TRADE_MONEY']
        self.TRADE_PAIR =   self.TRADE_COIN + self.TRADE_MONEY
        self.AVAILABLE_MONEY = float(config['ASSESTS']['AVAILABLE_MONEY'])

        self.RSI_LENGTH =    int(config[P]['RSI_LENGTH'])
        self.RSI_OVERBOUGHT= float(config[P]['RSI_OVERBOUGHT'] )
        self.RSI_OVERSOLD =  float(config[P]['RSI_OVERSOLD'])
        self.RSI_WEIGHT =    float(config[P]['RSI_WEIGHT'] )

        self.BBAND_LENGTH =  int(config[P]['BBAND_LENGTH'] )
        self.BBAND_STD =     float(config[P]['BBAND_STD'])
        self.BBAND_MAMODE=   config[P]['BBAND_MAMODE'] 
        self.BBAND_WEIGHT =  float(config[P]['BBAND_WEIGHT'] )

        self.STOCH_K =       int(config[P]['STOCH_K'] )
        self.STOCH_D =       int(config[P]['STOCH_D'] )
        self.STOCH_SMOOTH_K = int(config[P]['STOCH_SMOOTH_K'])
        self.STOCH_WEIGHT =  float(config[P]['STOCH_WEIGHT'] )
        self.STOCH_OVERBOUGHT = float(config[P]['STOCH_OVERBOUGHT'])
        self.STOCH_OVERSOLD = float(config[P]['STOCH_OVERSOLD'])

        self.MACD_FAST   =  int(config[P]['MACD_FAST'])
        self.MACD_SLOW   =  int(config[P]['MACD_SLOW'])
        self.MACD_SIGNAL =  int(config[P]['MACD_SIGNAL'])
        self.MACD_WEIGHT =  float(config[P]['MACD_WEIGHT'] )