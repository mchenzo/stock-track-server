from flask import Flask
from flask_cors import CORS
import requests
from flask import jsonify
from flask import request
from pymongo import MongoClient
import ast
import json
import datetime
from dateutil.parser import parse
from pricePeak import pricePeaks, macdCrossover
from util import extractBBandData, extractDataPts, extractMACDData, extractRSIData, standardizeTimeScales, weatherReportMACDData

db_user = 'mchenzo'
db_pass = '02aae49721%'
MONGO_URI = 'mongodb://chen:scootruin3@ds113853.mlab.com:13853/stockings'

app = Flask(__name__)
client = MongoClient(MONGO_URI)
CORS(app)


API_KEY = 'SBEC9GQRUPSS4MAA'


@app.route('/')
def index():
    return 'listening...'



# ===========================================================
#           Stock Price Route and Data Pt Extraction
# ===========================================================



@app.route('/stock-data', methods=['POST'])
def retrieveAllData():
    req = ast.literal_eval(request.data.decode("utf-8"))
    symbol = req['symbol']
    timeFrame = req['timeFrame']
    interval = req['interval']

    priceData = retrieveStockData(symbol, timeFrame, interval)
    bbandData = retrieveStockBBand(symbol, timeFrame, interval)
    macdData = retrieveStockMACD(symbol, timeFrame, interval)
    rsiData = retrieveStockRSI(symbol, timeFrame, interval)

    allData = {}
    trendData = macdCrossover(ast.literal_eval(macdData)['histogram'], ast.literal_eval(priceData)['close'])
    allData['trends'] = ast.literal_eval(trendData)

    earliestPrice = ast.literal_eval(priceData)['close'][0]['x']
    earliestBand = ast.literal_eval(bbandData)['lowerBand'][0]['x']
    earliestMacd = ast.literal_eval(macdData)['histogram'][0]['x']
    earliestRsi = ast.literal_eval(rsiData)['rsi'][0]['x']
    latestDate = max([earliestPrice, earliestBand, earliestMacd, earliestRsi])
    print('>>>>>>>>> LATEST DATE: ', earliestPrice, earliestBand, earliestMacd, earliestRsi, latestDate)
    timeScaledData = ast.literal_eval(standardizeTimeScales(latestDate, priceData, bbandData, macdData, rsiData, timeFrame))

    allData['prices'] = timeScaledData['prices']
    allData['bband'] = timeScaledData['bbands']
    allData['macd'] = timeScaledData['macd']
    allData['rsi'] = timeScaledData['rsi']

    return json.dumps(allData)



def retrieveStockData(sym, time, interval):
    queryURL = 'https://www.alphavantage.co/query?'

    queryURL += f'function={time}'
    queryURL += f'&symbol={sym}'
    queryURL += f'&interval={interval}'
    queryURL += f'&apikey={API_KEY}'

    res = requests.get(queryURL).json()
    return extractDataPts(time, interval, res)





# ===========================================================
#           BBand Route and Data Pt Extraction
# ===========================================================
# function = BBANDS
# symbol = i.e. ANET
# interval =
def retrieveStockBBand(symbol, timeFrame, interval):
    queryURL = 'https://www.alphavantage.co/query?function=BBANDS'
    queryURL += f'&symbol={symbol}'

    if timeFrame == 'TIME_SERIES_INTRADAY':
        queryURL += f'&interval={interval}'
    elif timeFrame == 'TIME_SERIES_DAILY_ADJUSTED':
        queryURL += '&interval=daily'
    elif timeFrame == 'TIME_SERIES_WEEKLY_ADJUSTED':
        queryURL += '&interval=weekly'
    else:
        queryURL += '&interval=monthly'

    queryURL += f'&time_period=20'

    closeQueryURL = queryURL + f'&series_type=close&apikey={API_KEY}'
    closeRes = requests.get(closeQueryURL).json()

    return extractBBandData(closeRes)





# ===========================================================
#           MACD Route and Data Pt Extraction
# ===========================================================


def retrieveStockMACD(symbol, timeFrame, interval):
    queryURL = 'https://www.alphavantage.co/query?function=MACD'
    queryURL += f'&symbol={symbol}'

    if timeFrame == 'TIME_SERIES_INTRADAY':
        queryURL += f'&interval={interval}'
    elif timeFrame == 'TIME_SERIES_DAILY_ADJUSTED':
        queryURL += '&interval=daily'
    elif timeFrame == 'TIME_SERIES_WEEKLY_ADJUSTED':
        queryURL += '&interval=weekly'
    else:
        queryURL += '&interval=monthly'

    closeQueryURL = queryURL + f'&series_type=close&apikey={API_KEY}'
    closeRes = requests.get(closeQueryURL).json()

    return extractMACDData(closeRes, timeFrame)



# ===========================================================
#           RSI Route and Data Pt Extraction
# ===========================================================


# @app.route('/stock-rsi', methods=['POST'])
def retrieveStockRSI(symbol, timeFrame, interval):
    queryURL = 'https://www.alphavantage.co/query?function=RSI'
    queryURL += f'&symbol={symbol}'

    if timeFrame == 'TIME_SERIES_INTRADAY':
        queryURL += f'&interval={interval}'
    elif timeFrame == 'TIME_SERIES_DAILY_ADJUSTED':
        queryURL += '&interval=daily'
    elif timeFrame == 'TIME_SERIES_WEEKLY_ADJUSTED':
        queryURL += '&interval=weekly'
    else:
        queryURL += '&interval=monthly'

    queryURL += '&time_period=14'

    closeQueryURL = queryURL + f'&series_type=close&apikey={API_KEY}'
    closeRes = requests.get(closeQueryURL).json()

    return extractRSIData(closeRes)



# P/E Ratio calculations using data provided by IEX
# https://api.iextrading.com/1.0
# /deep/official-price?symbols=snap for official price
# ['earnings']['actualEPS']
# /stock/aapl/earnings for EPS
# [SYMBOL]['price']
# /stock/aapl/stats for market cap
# ['marketcap']
@app.route('/stock-stats', methods=['POST'])
def calculatePriceEarningsRatio():
    req = ast.literal_eval(request.data.decode("utf-8"))
    sym = req['symbol']
    queryURL = f'https://api.iextrading.com/1.0'
    priceURL = queryURL + f'/stock/{sym}/price'
    capURL = queryURL + f'/stock/{sym}/stats'

    currentPrice = requests.get(priceURL).text
    stats = requests.get(capURL).json()
    marketCap = stats['marketcap']
    actualEPS = stats['latestEPS']

    try: 
        peRatio = "%.2f" % (float(currentPrice) / actualEPS)
    except:
        peRatio = f'Error Calculating PE: price: {currentPrice}, EPS: {actualEPS}'

    result = {}
    result['marketcap'] = marketCap
    result['p/e'] = peRatio
    result['company'] = stats['companyName']

    # print('Hitting the IEX endpoint: ', currentPrice, actualEPS, marketCap)
    return json.dumps(result)




@app.route('/weather-report', methods=['POST'])
def weatherReport():
    stockings = client.stockings
    reports = stockings.reports
    todays_report = reports.find_one({ "date":f'{(datetime.date.today())}' })

    if (todays_report == None):
        req = ast.literal_eval(request.data.decode("utf-8"))

        reportSet = req['data']
        for i in range(len(reportSet)):
            monthlyMACD = ast.literal_eval(weatherReportMACD(reportSet[i]['sector'], 'TIME_SERIES_MONTHLY_ADJUSTED', ''))
            monthlyStatus = monthlyMACD['status']
            monthlyTrans = monthlyMACD['transitionDate']

            weeklyMACD = ast.literal_eval(weatherReportMACD(reportSet[i]['sector'], 'TIME_SERIES_WEEKLY_ADJUSTED', ''))
            weeklyStatus = weeklyMACD['status']
            weeklyTrans = weeklyMACD['transitionDate']

            dailyMACD = ast.literal_eval(weatherReportMACD(reportSet[i]['sector'], 'TIME_SERIES_DAILY_ADJUSTED', ''))
            dailyStatus = dailyMACD['status']
            dailyTrans = dailyMACD['transitionDate']

            print('^^^^^^^ETF: ', monthlyMACD['histogram'][0], weeklyMACD['histogram'][0], dailyMACD['histogram'][0])
            print('^^^^^^^Status: ', i, reportSet[i], monthlyStatus, monthlyTrans, weeklyStatus, weeklyTrans, dailyStatus, dailyTrans)
            reportSet[i]['monthStatus'] = monthlyStatus
            reportSet[i]['monthDur'] = f'{(datetime.datetime.now() - parse(monthlyTrans)).days} days'
            reportSet[i]['weekStatus'] = weeklyStatus
            reportSet[i]['weekDur'] = f'{(datetime.datetime.now() - parse(weeklyTrans)).days} days'
            reportSet[i]['dailyStatus'] = dailyStatus
            reportSet[i]['dailyDur'] = f'{(datetime.datetime.now() - parse(dailyTrans)).days} days'

        dbUpdate = {}
        dbUpdate['report'] = reportSet
        dbUpdate['date'] = f'{(datetime.date.today())}'
        
        print(MONGO_URI)
        addReport(dbUpdate)
        return json.dumps(reportSet)
    else:
        print('>>>>>> Report already generated for today.')
        return json.dumps(todays_report['report'])



def addReport(report):
    stockings = client.stockings
    reports = stockings.reports
    reports.insert_one(report)
    return jsonify({'ok': True, 'message': 'Weather report logged successfully'}), 200



def weatherReportMACD(symbol, timeFrame, interval):
    queryURL = 'https://www.alphavantage.co/query?function=MACD'
    queryURL += f'&symbol={symbol}'

    if timeFrame == 'TIME_SERIES_INTRADAY':
        queryURL += f'&interval={interval}'
    elif timeFrame == 'TIME_SERIES_DAILY_ADJUSTED':
        queryURL += '&interval=daily'
    elif timeFrame == 'TIME_SERIES_WEEKLY_ADJUSTED':
        queryURL += '&interval=weekly'
    else:
        queryURL += '&interval=monthly'

    closeQueryURL = queryURL + f'&series_type=close&apikey={API_KEY}'
    closeRes = requests.get(closeQueryURL).json()

    return weatherReportMACDData(closeRes, timeFrame)
