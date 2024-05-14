

''' ||| The River ||| '''
''' Trading Algorithm for MetaTrader 5 '''


import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time

class River:
    def __init__(self):
        mt5.initialize()
        # self.login = *****
        # self.password = '******'
        # self.server = 'ICMarketsSC_Demo'
        # mt5.login(self.login, self.password, self.server)
        self.SYMBOL = 'EURUSD'
        self.Atr_Perc_tp = 2.2 
        self.Atr_Perc_sl = 1.6 
        self.TIMEFRAME_15M = mt5.TIMEFRAME_M15
        self.TIMEFRAME_5M = mt5.TIMEFRAME_M5 # this the being used
        self.TIMEFRAME_1H = mt5.TIMEFRAME_H1
        self.VOLUME = 0.01
        self.MAGIC = 2222
        self.Comment = 'River'

        # ==================================================== #
        # !!!IMPORTANT:
        # self.sec_to_shift is used for data allignment purposes.
        # self.sec_to_shift has a value of 14400 if you're trading in the UK.
        # This value MUST be set differently if you trade from another country with dufferent clocktime.
        # For example, if you trade from Australia, the value should be set from 14400 to 54000.
        # How to know this?
        # You should check the datetime of the most recent candle on the Metatrader chart, 
        # and your local datetime, the difference should be calculated in seconds.
        # For example if the most recent candle of a chart in Metatrader has a datetime 12 May 16:00,
        # and your local datetime is 12 May 18:00, the value should be the 2 hours difference in seconds, in this case 7200.

        # However this MUST BE TESTED FIRST!

        # At the end of the script comment out Trade.execution_main(),
        # and uncomment Trade.TEST(), then execute the bot;
        # you will see an output displaying the close price of the most recent 10 candles of the EURUSD,
        # on the Metatrader chart ensure that each of the moste recent 10 closing prices 
        # correspond to each of the last 10 prices of the output. 
        # Adjust the self.sec_to_shift accornding.
        self.sec_to_shift = 14400
        # ==================================================== #

        self.symbol_list = [{'AUDUSD':4.0}, {'EURCAD':8.0}, {'USDCAD':7.5}, {'AUDCAD':5.0}, {'AUDJPY': 500.0}, 
                            {'CADJPY': 500.0}, {'EURAUD': 8.0}, {'EURGBP': 5.0}, {'EURJPY': 750.0}, 
                            {'EURUSD': 5.5}, {'GBPAUD': 8.5}, {'GBPJPY': 800.0}, {'USDJPY': 700.0}]


    ''' H I S T O R I C A L   D A T A '''


    # GET DATA (on)
    def Historical(self, SYMBOL):
        # Get data from now to back by the numbers of candles

        number_of_candles = 500
        looknow = int(datetime.utcnow().timestamp())
        lookback = (looknow - (number_of_candles * 5)*60) # in sec
        df = pd.DataFrame(mt5.copy_rates_range(SYMBOL, self.TIMEFRAME_5M, lookback + self.sec_to_shift, looknow + self.sec_to_shift))

        # Create dataframe
        df = df.drop(['spread','real_volume'],axis=1)
        # print(df)
        return df
    

    def TEST(self):
        # Get data from now to back by the numbers of candles
        SYMBOL = self.SYMBOL

        number_of_candles = 500
        looknow = int(datetime.utcnow().timestamp())
        lookback = (looknow - (number_of_candles * 5)*60) # in sec
        df = pd.DataFrame(mt5.copy_rates_range(SYMBOL, self.TIMEFRAME_5M, lookback + self.sec_to_shift, looknow + self.sec_to_shift))

        # Create dataframe
        df = df.drop(['spread','real_volume'],axis=1)
        print(df.close.iloc[-10:])
        return df


    


    ''' C A N D L E   P A T T E R N '''

    # BULLISH ENGULFING (off)
    def Bull_Eng(self, SYMBOL):
        self.SYMBOL = SYMBOL
        df = self.Historical(SYMBOL)
        Bullish_Engulfing = df['close'].iloc[-2] > df['open'].iloc[-3] and df['open'].iloc[-2] <= df['close'].iloc[-3] and (0.8 * 0.9) > 0.8 and \
                            df['close'].iloc[-3] < df['open'].iloc[-3] and df['close'].iloc[-2] > df['open'].iloc[-2] and df['high'].iloc[-2] > df['high'].iloc[-3]
        
        return Bullish_Engulfing
    
    # BEARISH ENGULFING (off)
    def Bear_Eng(self, SYMBOL):
        self.SYMBOL = SYMBOL
        df = self.Historical(SYMBOL)
        Bearish_Engulfing = df['close'].iloc[-2] < df['open'].iloc[-3] and df['open'].iloc[-2] >= df['close'].iloc[-3] and (0.8 * 0.9) < 0.8 and \
                            df['close'].iloc[-3] > df['open'].iloc[-3] and df['close'].iloc[-2] < df['open'].iloc[-2] and df['low'].iloc[-2] < df['low'].iloc[-3]       

        return Bearish_Engulfing


    ''' I N D I C A T O R S '''

    # Avarage True Range (on)
    def ATR(self, SYMBOL):
        df = self.Historical(SYMBOL)
        # ATR
        df['H-L'] = abs(df['high'] - df['low'])
        df['H-PC'] = abs(df['high'] - df['close'].shift(1))
        df['L-PC'] = abs(df['low'] - df['close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
        df['ATR'] = df['TR'].ewm(span=6, min_periods=6).mean()
        df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)

        # Take Profit and Stop Loss for Long position
        SL_buy = df['close'].iloc[-2] - (df['ATR'].iloc[-2] * self.Atr_Perc_sl)
        TP_buy = df['close'].iloc[-2] + (df['ATR'].iloc[-2] * self.Atr_Perc_tp)

        # Take Profit and Stop Loss for Short position
        TP_sell = df['close'].iloc[-2] - (df['ATR'].iloc[-2] * self.Atr_Perc_tp)
        SL_sell = df['close'].iloc[-2] + (df['ATR'].iloc[-2] * self.Atr_Perc_sl)

        return ([SL_buy, SL_sell, TP_buy, TP_sell])

    # Relatve Strenght Index (off)
    def RSI(self, SYMBOL):
        self.SYMBOL = SYMBOL
        df = self.Historical(SYMBOL)
        # CALCULATE RSI
        alpha = 1.0 / 14
        gains = df.close.diff()
        wins = pd.Series([x if x >= 0 else 0.0 for x in gains], name='wins')
        losses = pd.Series([x * -1 if x < 0 else 0.0 for x in gains], name='losses')
        wins_rma = wins.ewm(min_periods=14, alpha=alpha).mean()
        losses_rma = losses.ewm(min_periods=14, alpha=alpha).mean()
        rs = wins_rma / losses_rma
        rs = wins_rma / losses_rma
        df['RSI'] = 100.0 - (100.0 / (1.0 + rs))

        # Return what needed
        RSI_mean_1 = df['RSI'].iloc[-2:-1].mean()
        RSI_mean_2 = df['RSI'].iloc[-3:-2].mean()
        RSI_mean_3 = df['RSI'].iloc[-4:-2].mean()

        return ([RSI_mean_1, RSI_mean_2, RSI_mean_3])
    
    # SUPPLY & DEMAND using VOLUME (off)
    def Supply_Demand_by_volume(self, SYMBOL):
        self.SYMBOL = SYMBOL
        df = self.Historical(SYMBOL)
        # Create a new column 'range' by subtracting the 'low' column from the 'high' column.
        df["range"] = df["high"] - df["low"]
        # Create a new column 'vwap' by taking the cumulative sum of the product of the 'close' and 'tick_volume' columns divided by the cumulative sum of the 'tick_volume' column.
        df["vwap"] = (df["close"] * df["tick_volume"]).cumsum() / df["tick_volume"].cumsum()
        
        # Roll them in other to understand the footprints left by the traders and so the supply and demand zones.
        df['RollRange'] = df["range"].rolling(window=22).mean()
        df["RollVwap"] = df["vwap"].rolling(window=22).mean()

        # # is supply if last closed candle:
        # Supply = df['range'].iloc[-2] < df['RollRange'].iloc[-2] and df['vwap'].iloc[-2] > df['RollVwap'].iloc[-2]
        # # is demand if last closed candle:
        # Demand = df['range'].iloc[-2] < df['RollRange'].iloc[-2] and df['vwap'].iloc[-2] < df['RollVwap'].iloc[-2]

        # # check supply and demand zones not by only the last candle but by zones
        # supply_len_50 = df[(df["range"] < df["range"].rolling(window=50).mean()) & (df["vwap"] > df["vwap"].rolling(window=50).mean())]
        # demand_len_50 = df[(df["range"] < df["range"].rolling(window=50).mean()) & (df["vwap"] < df["vwap"].rolling(window=50).mean())]

        # return the length of the zones, of one is grater than teh other, is that zone.
        # ex: 
        # 'Buy' if len(supply_len_50) > len(demand_len_50) else 'Sell' if len(demand_len_50) > len(supply_len_50)
        # return len(supply_len_50), len(demand_len_50)
        
        return df

    # SUPPLY & DEMAND using VOLUME (off)
    def Supply_Demand_by_volume_H1(self, SYMBOL):
        self.SYMBOL = SYMBOL
        # Get data from now to back by the numbers of candles
        number_of_candles = 100
        looknow = int(datetime.utcnow().timestamp())
        lookback = (looknow - (number_of_candles * 60)*60) # in sec
        df = pd.DataFrame(mt5.copy_rates_range(self.SYMBOL,self.TIMEFRAME_1H, lookback + self.sec_to_shift, looknow + self.sec_to_shift))

        # Create dataframe
        df = df.drop(['spread','real_volume'],axis=1) 
        df = df[['time','open','high','low','close','tick_volume']]
        df['time']=pd.to_datetime(df['time'], unit='s')
        df.reset_index()
        # Create a new column 'range' by subtracting the 'low' column from the 'high' column.
        df["range_H1"] = df["high"] - df["low"]
        # Create a new column 'vwap' by taking the cumulative sum of the product of the 'close' and 'tick_volume' columns divided by the cumulative sum of the 'tick_volume' column.
        df["vwap_H1"] = (df["close"] * df["tick_volume"]).cumsum() / df["tick_volume"].cumsum()
        
        # Roll them in other to understand the footprints left by the traders and so the supply and demand zones.
        df['RollRange_H1'] = df["range_H1"].rolling(window=22).mean()
        df["RollVwap_H1"] = df["vwap_H1"].rolling(window=22).mean()
        df = df.dropna()

        # pd.set_option('display.max_columns', None)
        # print(df.tail(30))
        return df

    # SUPPLY & DEMAND using HIGHS and LOWS (off)
    def Supply_Demand_by_candles(self, SYMBOL, Window):
        self.SYMBOL = SYMBOL
        df = self.Historical(SYMBOL)
        # Get the Higher High and the Lower Low 
        df["high_rolling_max"] = df["high"].rolling(window=Window).max()
        df["low_rolling_min"] = df["low"].rolling(window=Window).min()
        # Create a column to store the supply and demand zones
        df["supply_demand"] = None
        
        # Loop and define wheather is a Supply or Demand zone
        for i, row in df.iterrows():
            if row["high"] >= row["high_rolling_max"]:
                df.loc[i, "supply_demand"] = "Supply"
            elif row["low"] <= row["low_rolling_min"]:
                df.loc[i, "supply_demand"] = "Demand"
        
        return df

    # THE RIVER (on)
    def River(self, SYMBOL):
        # for SYMBOL in self.symbol_list:
        #     for key, value in SYMBOL.items():
        #         self.SYMBOL = key
        df = self.Historical(SYMBOL)
        # structure the channel
        df['UP'] = df.high.rolling(8).max()
        df['LO'] = df.low.rolling(8).min()
        df['position_in_channel'] = (df['close']-df['LO']) / (df['UP']-df['LO'])
        # df['LIQ'] = df.Liquidity * 100 # NOT JPY
        # df['LIQ'] = df.Liquidity * 100 # WITH JPY

        # Find lowest(LCC) and highest(HCC) points in the channel
        for i in range(1, len(df) - 1):
            if df['close'][i] <= df['close'][i+1] and df['close'][i] <= df['close'][i-1] and df['close'][i+1] > df['close'][i-1]:
                # found LCC
                df.loc[i-1, 'LCC'] = df.loc[i, 'close']
            elif df['close'][i] >= df['close'][i+1] and df['close'][i] >= df['close'][i-1] and df['close'][i+1] < df['close'][i-1]:
                # found HCC
                df.loc[i, 'HCC'] = df.loc[i, 'close']

        df['HCC'].fillna(0, inplace=True)
        df['LCC'].fillna(0, inplace=True)

        df = df.dropna()
        # df.reset_index(inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    # LIQUIDITY POOL (on)
    def Liquidity_pool(self, SYMBOL):
        # for SYMBOL in self.symbol_list:
        #     for key, value in SYMBOL.items():
        #         self.SYMBOL = key
        df = self.Historical(SYMBOL)

        df['Liquidity'] = (df['close'] * df['tick_volume']) / df['tick_volume'].rolling(window=22).sum()
        df['LIQ'] = df['Liquidity'] * 100

        return df


    ''' P O S I T I O N   M A N A G E R '''

    # OPEN MARKET POSITION (on)
    def open_market_position(self, SYMBOL, s_l, Volume):
        # sell 1 == ask
        # buy 0 == bid

        SL_Buy = self.ATR(SYMBOL)[0] #.astype(float)
        SL_Sell = self.ATR(SYMBOL)[1] #.astype(float)
        TP_Buy = self.ATR(SYMBOL)[2] #.astype(float)
        TP_Sell = self.ATR(SYMBOL)[3] #.astype(float)

        if (s_l == 1):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": Volume, # FLOAT
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(SYMBOL).bid,
                "sl": SL_Buy, # FLOAT
                "tp": TP_Buy, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC,
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,}

            response = mt5.order_send(request)
            return response

        if (s_l == -1):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": Volume, # FLOAT
                "type": mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(SYMBOL).ask,
                "sl": SL_Sell, # FLOAT
                "tp": TP_Sell, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC,
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,}

            response = mt5.order_send(request)
            return response

    # OPEN LIMIT POSITION (off)
    def open_limit_position(self, SYMBOL, s_l):
        # sell 1 == ask
        # buy 0 == bid

        SL_Buy = self.Historical(SYMBOL)[9] #.astype(float)
        SL_Sell = self.Historical(SYMBOL)[11] #.astype(float)

        point = mt5.symbol_info(self.SYMBOL).point 

        if (s_l == 1):
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": SYMBOL,
                "volume": self.VOLUME, # FLOAT
                "type": mt5.ORDER_TYPE_BUY_LIMIT,
                "price": mt5.symbol_info_tick(SYMBOL).ask - 10 * point,
                "sl": SL_Buy, # FLOAT
                "tp": 0.0, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC, # INTERGER
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN}

            response = mt5.order_send(request)
            return response

        if (s_l == -1):
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": SYMBOL,
                "volume": self.VOLUME, # FLOAT
                "type": mt5.ORDER_TYPE_SELL_LIMIT,
                "price": mt5.symbol_info_tick(SYMBOL).bid + 10 * point,
                "sl": SL_Sell, # FLOAT
                "tp": 0.0, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC, # INTERGER
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN}

            response = mt5.order_send(request)
            return response

    # CLOSE MARKET POSITION (on)
    def close_position(self, SYMBOL, s_l):
        # mt5.positions_get()[0][0]
        
        if (s_l == 1):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": self.VOLUME, # FLOAT
                "type": mt5.ORDER_TYPE_BUY,
                "position": mt5.positions_get(symbol=self.SYMBOL)[0][0],
                "price": mt5.symbol_info_tick(self.SYMBOL).bid,
                "sl": 0.0, # FLOAT
                "tp": 0.0, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC,
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,}

            response = mt5.order_send(request)
            return response

        if (s_l == -1):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": self.VOLUME, # FLOAT
                "type": mt5.ORDER_TYPE_SELL,
                "position": mt5.positions_get(symbol=self.SYMBOL)[0][0],
                "price": mt5.symbol_info_tick(self.SYMBOL).ask,
                "sl": 0.0, # FLOAT
                "tp": 0.0, # FLOAT
                "deviation": 20, # INTERGER
                "magic": self.MAGIC,
                "comment": self.Comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,}

            response = mt5.order_send(request)
            # print(response)
            return response

    # CLOSE ALL POSITIONS (on)
    def close_all_positions(self, SYMBOL, pos):
        self.SYMBOL = SYMBOL
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": self.SYMBOL,
            "volume": pos.volume, # FLOAT
            "type": mt5.ORDER_TYPE_BUY if pos.type == 1 else mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(self.SYMBOL).ask if pos.type == 1 else mt5.symbol_info_tick(self.SYMBOL).bid,
            "deviation": 20, # INTERGER
            "magic": self.MAGIC, # INTERGER
            "comment": self.Comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,}
        
        # To close all positions for all symbols, run the following outside this function:
        # for SYMBOL in self.symbol_list:
        #     Opened = mt5.positions_get(symbol = SYMBOL)
        #     for pos in Opened:
        #         self.close_all_positions(SYMBOL, pos)

        response = mt5.order_send(request)
        return response

    # CLOSE ALL LIMIT POSITON PENDING (off)
    def close_all_pendings(self, pos):
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": pos.ticket if pos != () else None,
            "symbol": self.SYMBOL,
            "type_filling": mt5.ORDER_FILLING_IOC,}
        
        # To close all pending positions for all symbols, run the following outside this function:
        # for SYMBOL in self.symbol_list:
        #     Pending = Pending = mt5.orders_get(symbol= SYMBOL)
        #     for pos in Pending:
        #         self.close_all_positions(SYMBOL, pos)

        response = mt5.order_send(request)
        return response
    
    # GET POSITION CURRENTLY OPEN (on)
    def get_opened_positions(self, SYMBOL):

        for SYMBOL in self.symbol_list:
            for key, value in SYMBOL.items():

                self.SYMBOL = key

                if len(mt5.positions_get(symbol = self.SYMBOL)) == 0:
                    return ''

                # 0 == buy, 1 == sell
                elif len(mt5.positions_get(symbol = self.SYMBOL)) > 0:
                    positions = pd.DataFrame(mt5.positions_get(symbol = self.SYMBOL)[0])
                    side = positions[0][5] # type, buy or sell, 0 or 1
                    entryprice = positions[0][10]
                    profit = positions[0][15]
                    ticket_ID = positions[0][0] # ID positon
                        
                    if side == 0:
                        pos = 1
                        return [pos, side, profit, entryprice, ticket_ID]

                    elif side == 1:
                        pos = -1

                        return ([pos, side, profit, entryprice, ticket_ID])
                    
                    else:
                        return 'NONE'
                else:
                    return 'NONE'

    # GET BID AND ASK LAST CANDLE (off)
    def get_SYMBOL_price_last(self):
        prices = mt5.symbol_info_tick(self.SYMBOL)._asdict()
        df = pd.DataFrame([prices], index=[0])
        bid = df.at[0,'bid']
        ask = df.at[0,'ask']
        return [bid, ask]


    ''' C H E C K   S I G N A L S '''

    def check_signal(self, SYMBOL):
        SIGNAL = 0
        CH_LMT = 0.9
        position_in_channel = self.River(SYMBOL)['position_in_channel']
        HCC = self.River(SYMBOL)['HCC']
        LCC = self.River(SYMBOL)['LCC']
        for i in range(1, len(position_in_channel)):
            if position_in_channel[i] >= CH_LMT and position_in_channel[i-1] < CH_LMT and HCC[i] != 0:
                SIGNAL = 1
                # print("Buy Signal")
                break
            elif position_in_channel[i] <= 1-CH_LMT and position_in_channel[i-1] > 1-CH_LMT and LCC[i] != 0:
                SIGNAL = -1
                # print("Sell Signal")
                break
        return SIGNAL

    # CHECK SIGNAL TO OPEN POSITION (on)
    def check_signal_1(self, SYMBOL):
        SIGNAL = 0
        CH_LMT = 0.2
        position_in_channel = self.River(SYMBOL)['position_in_channel']
        HCC = self.River(SYMBOL)['HCC']
        LCC = self.River(SYMBOL)['LCC']
        Liquidity = self.Liquidity_pool(SYMBOL)['LIQ']

        for M in self.symbol_list:
            for key, value in M.items():

                SYMBOL = key

                # DEBUG
                print(f'Symbol::{SYMBOL} HCC::{HCC.iloc[-1]}, LCC::{LCC.iloc[-1]}')
                print(f'Symbol::{SYMBOL} Pos::{position_in_channel.iloc[-1]}, Liq::{Liquidity.iloc[-1]} ')
                print('------')

                # LONG
                if position_in_channel.iloc[-1] < CH_LMT \
                    and LCC.iloc[-1] > 0.0 \
                    and Liquidity.iloc[-1] > value:
                    SIGNAL = 1
                    return SIGNAL
                # SHORT
                if position_in_channel.iloc[-1] > CH_LMT \
                    and HCC.iloc[-1] > 0.0 \
                    and Liquidity.iloc[-1] > value:
                    SIGNAL = -1
                    return SIGNAL
                
        return SIGNAL


    # CHECK A PARTIAL SIGNAL AND CLOSE THE POSITION IF True (on)
    def check_reverse_signal(self, SYMBOL):
        self.SYMBOL = SYMBOL
        SIGNAL = 0

        S_D_Volume = self.Supply_Demand_by_volume(SYMBOL)

        Range = S_D_Volume['range'].iloc[-16:-4].mean()
        Vwap = S_D_Volume['vwap'].iloc[-16:-4].mean()
        Vwap_2 = S_D_Volume['vwap'].iloc[-4:-1].mean()
        RollRange = S_D_Volume['RollRange'].iloc[-16:-4].mean()
        RollVwap = S_D_Volume['RollVwap'].iloc[-16:-4].mean()
        RollVwap_2 = S_D_Volume['RollVwap'].iloc[-4:-1].mean()

        # L O N G 
        if Range < RollRange and Vwap < RollVwap:
            if Vwap_2 > RollVwap_2:
                SIGNAL = 1

        # S H O R T
        if Range < RollRange and Vwap > RollVwap:
            if Vwap_2 < RollVwap_2:
                SIGNAL = -1

        return SIGNAL


    ''' P R O F I T   &   S T O P   L O S S E S '''

    # CHECK THE CURRENT PROFIT (off)
    def Profit_F(self, SYMBOL):
        for M in self.symbol_list:
            for key, value in M.items():
                SYMBOL = key
                Openedd = mt5.positions_get(symbol = SYMBOL)
                tot_profit = 0
                Positions_Opened = [ pos for pos in Openedd ]
                for pos in Positions_Opened:
                    tot_profit += pos.profit
                return round(tot_profit, 2)

    # REMOVE ALL STOP LOSS (on)
    def remove_sl(self, SYMBOL, pos):
        for M in self.symbol_list:
            for key, value in M.items():
                SYMBOL = key
                Openedd = mt5.positions_get(symbol = SYMBOL)
                Positions_Opened = [ pos for pos in Openedd ]
                for pos in Openedd:
                    # print(pos.ticket)
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": self.SYMBOL,
                        "position": pos.ticket,
                        "sl": 0.0 if pos.sl > 0.0 or pos.sl != "" else None,
                        "tp": pos.tp}

                    response = mt5.order_send(request)
                    return response

    # ADD ALL STOP LOSS (on)
    def add_sl(self, SYMBOL, pos):
        for M in self.symbol_list:
            for key, value in M.items():
                SYMBOL = key
                SL_Buy = self.ATR()[1] #.astype(float)
                SL_Sell = self.ATR()[3] #.astype(float)
                self.SYMBOL = SYMBOL
                Openedd = mt5.positions_get(symbol = SYMBOL)
                Positions_Opened = [ pos for pos in Openedd ]
                for pos in Openedd:
                    # print(pos.ticket)
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": self.SYMBOL,
                        "position": pos.ticket,
                        "sl": SL_Sell if pos.type == 1 else SL_Buy,
                        "tp": pos.tp}

                    response = mt5.order_send(request)
                    return response


    ''' E X E C U T I O N '''

    # BUY or SELL (on)
    def main(self, step):

        for M in self.symbol_list:
            for key, value in M.items():
                SYMBOL = key
                # ------- close all ------- #
                CLOSE_ALL = False # switch to True for execute
                if CLOSE_ALL == True:
                    Opened = mt5.positions_get(symbol = SYMBOL)
                    for pos in Opened:
                        self.close_all_positions(SYMBOL, pos)
                # ------- close all ------- #

                POSITIONS = self.get_opened_positions(SYMBOL)
                Openedd = mt5.positions_get(symbol = SYMBOL)
                Pendingg = mt5.orders_get(symbol= SYMBOL)

                # Close = self.Historical(SYMBOL)['close']
                # point = mt5.symbol_info(self.SYMBOL).point 
                # margin_buy = Close.iloc[-2] - 15 * point
                # margin_sell =  Close.iloc[-2] + 15 * point

                Tot_Profit = self.Profit_F(SYMBOL)
                Tot_Len = len(Pendingg) + len(Openedd)
                # signal_reverse = self.check_reverse_signal(SYMBOL)
                signal = self.check_signal(SYMBOL)

                if CLOSE_ALL == False:
                    # LOOKING FOR PATTERN
                    if POSITIONS == '' and len(Openedd) < 1:
                        # try:
                        if signal == 1:
                            self.open_market_position(SYMBOL, 1, self.VOLUME)
                            print(f'1L1 - Long Opened {SYMBOL}')
                        
                        elif signal == -1:
                            self.open_market_position(SYMBOL, -1, self.VOLUME)
                            print(f'1S1 - Short Opened {SYMBOL}')
                        # except:
                        #     print('Could not open nuew pos')
                        
    # CLOSE POSITION (on)
    def main_close(self):
        for M in self.symbol_list:
            for key, value in M.items():
                SYMBOL = key
                POSITIONS = self.get_opened_positions(SYMBOL)
                # signal_reverse = self.check_reverse_signal(SYMBOL)
                HCC = self.River(SYMBOL)['HCC']
                LCC = self.River(SYMBOL)['LCC']
                # print('here')
                if POSITIONS != '':
                    try:
                        
                        if POSITIONS[0] == 1: # if side is Buy
                            if HCC.iloc[-1] > 0.0:
                                self.close_position(SYMBOL, -1) 
                                print(f'3L2 - Close Long {SYMBOL} due reverse Signal')
                        
                        elif POSITIONS[0] == -1: # if side id Sell
                            if LCC.iloc[-1] > 0.0:
                                self.close_position(SYMBOL, 1) 
                                print(f'3L2 - Close Short {SYMBOL} due reverse Signal')

                    except:
                        print(f'Could not close a poaition {SYMBOL}')

    # EXECUTE MAIN - BUY or SELL (on)
    def execution_main(self):
        import datetime

        # The broker causes massive spread during the closing and open time of the market and
        # this more often burn all the stop losses of the position if using timeframe of 10min or less.
        # To avoid this, just before the market close, stop searching for signals and remove all the stop losses.
        # After about 1 hour from the open when the spread came to normal re-add the stop losses and start searching for signal.

        current_time = datetime.datetime.now().time()

        # remove all stop loss 
        if current_time > datetime.time(21, 35) and current_time <= datetime.time(22, 0):
            for S in self.symbol_list:
                for pos in S:
                    self.remove_sl(S, pos)

        # add all stop loss
        elif current_time > datetime.time(23, 11) and current_time <= datetime.time(23, 5):
            for S in self.symbol_list:
                for pos in S:
                    self.add_sl(S, pos)

        # execute
        else:
            counterr = 1
            print(f'Looking for pattern in {self.symbol_list}...')
            while True:
                # stop executing until:
                if current_time > datetime.time(21, 40) or current_time <= datetime.time(23, 12):
                    try:
                        self.main(counterr), self.main_close()
                        counterr = counterr + 1
                        if counterr > 5:
                            counterr = 1
                        time.sleep(28)
                        
                    except KeyboardInterrupt:
                        print('\n\KeyboardInterrupt. Stopping.')
                        exit()
                else:
                    print('Starting again at 23:35')
                    time.sleep(180)
                    continue



if __name__ == '__main__':
    Trade = River()

    Trade.execution_main()

    #Trade.TEST()





