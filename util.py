from pricePeak import pricePeaks, macdCrossover
from dateutil.parser import parse
import ast
import json



def extractDataPts(timeFrame, interval, data):
    if (timeFrame == 'TIME_SERIES_WEEKLY_ADJUSTED'):
        dataPts = data['Weekly Adjusted Time Series']
    elif timeFrame == 'TIME_SERIES_MONTHLY_ADJUSTED':
        dataPts = data['Monthly Adjusted Time Series']
    elif timeFrame == 'TIME_SERIES_DAILY_ADJUSTED':
        dataPts = data['Time Series (Daily)']
    else:
        dataPts = data[f'Time Series ({interval})']

    close = []

    for dataPt in dataPts:
        closePt = {}
        closePt['x'] = dataPt
        closePt['y'] = float(dataPts[dataPt]['4. close'])
        close.insert(0, closePt)

    peakData = ast.literal_eval(pricePeaks(close))

    extractedPts = {
        'close': close,
        'peaks': peakData['peaks'],
        'troughs': peakData['troughs']
    }

    return json.dumps(extractedPts)





def extractBBandData(alphVantRes):
    dataPts = alphVantRes['Technical Analysis: BBANDS']
    lowerBand = []
    upperBand = []
    middleBand = []

    for pt in dataPts:
        lowPt = {}
        uppPt = {}
        midPt = {}

        lowPt['x'] = pt
        lowPt['y'] = float(dataPts[pt]['Real Lower Band'])
        uppPt['x'] = pt
        uppPt['y'] = float(dataPts[pt]['Real Upper Band'])
        midPt['x'] = pt
        midPt['y'] = float(dataPts[pt]['Real Middle Band'])

        lowerBand.insert(0, lowPt)
        upperBand.insert(0, uppPt)
        middleBand.insert(0, midPt)

    bands = {}
    bands['lowerBand'] = lowerBand
    bands['upperBand'] = upperBand
    bands['middleBand'] = middleBand

    return json.dumps(bands)


def extractMACDData(alphVantRes, timeFrame):
    dataPts = alphVantRes['Technical Analysis: MACD']
    histogram = []
    signal = []
    macd = []

    for pt in dataPts:
        histPt = {}
        sigPt = {}
        macdPt = {}

        histPt['x'] = pt
        sigPt['x'] = pt
        macdPt['x'] = pt
        if (timeFrame == "TIME_SERIES_INTRADAY"):
            histPt['x'] = pt + ":00"
            sigPt['x'] = pt + ":00"
            macdPt['x'] = pt + ":00"
        histPt['y'] = float(dataPts[pt]['MACD_Hist'])
        sigPt['y'] = float(dataPts[pt]['MACD_Signal'])
        macdPt['y'] = float(dataPts[pt]['MACD'])

        histogram.insert(0, histPt)
        signal.insert(0, sigPt)
        macd.insert(0, macdPt)

    graphs = {}
    graphs['histogram'] = histogram
    graphs['signal'] = signal
    graphs['macd'] = macd

    return json.dumps(graphs)



def weatherReportMACDData(alphVantRes, timeFrame):
    dataPts = alphVantRes['Technical Analysis: MACD']
    histogram = []
    firstPt = list(dataPts.keys())[0]

    if float(dataPts[firstPt]['MACD_Hist']) > 0:
        currentStatus = 'up'
    else:
        currentStatus = 'down'

    transitionDate = ''

    for pt in dataPts:
        histPt = {}
        histPt['x'] = pt
        if (timeFrame == "TIME_SERIES_INTRADAY"):
            histPt['x'] = pt + ":00"
        histPt['y'] = float(dataPts[pt]['MACD_Hist'])

        if float(dataPts[pt]['MACD_Hist']) > 0:
            histPt['status'] = 'up'
        else:
            histPt['status'] = 'down'

        if transitionDate == '':
            if histPt['status'] != currentStatus:
                transitionDate = histPt['x']
        histogram.append(histPt)

    graphs = {}
    graphs['histogram'] = histogram
    graphs['status'] = currentStatus
    graphs['transitionDate'] = transitionDate

    return json.dumps(graphs)




def extractRSIData(alphVantRes):
    dataPts = alphVantRes['Technical Analysis: RSI']
    rsi = []

    for pt in dataPts:
        rsiPt = {}
        rsiPt['x'] = pt
        rsiPt['y'] = float(dataPts[pt]['RSI'])
        rsi.insert(0, rsiPt)

    peakData = ast.literal_eval(pricePeaks(rsi))

    graphs = {}
    graphs['rsi'] = rsi
    graphs['peaks'] = peakData['peaks']
    graphs['troughs'] = peakData['troughs']

    return json.dumps(graphs)



def standardizeTimeScales(latestStart, prices, bbands, macd, rsi, timeFrame):
    # if timeFrame == "TIME_SERIES_INTRADAY":
    prices = ast.literal_eval(prices)
    bbands = ast.literal_eval(bbands)
    macd = ast.literal_eval(macd)
    rsi = ast.literal_eval(rsi)

    close = prices['close']
    closePeaks = prices['peaks']
    closeTroughs = prices['troughs']
    lowerBand = bbands['lowerBand']
    upperBand = bbands['upperBand']
    middleBand = bbands['middleBand']
    histogram = macd['histogram']
    signal = macd['signal']
    macd = macd['macd']
    rsiPts = rsi['rsi']
    rsiPeaks = rsi['peaks']
    rsiTroughs = rsi['troughs']

    # print('debugging price time scaling: ', close, len(close))

    for i in range(len(close) - 1):
        if close[i]['x'] == latestStart:
            print('--> --> Matching date located in CLOSE <-- <-- ', close[i], latestStart)
            close = close[i:]
            break

    for i in range(len(closePeaks) - 1):
        if parse(closePeaks[i]['x']) > parse(latestStart):
            print('--> --> Closest date located in CLOSEPEAKS <-- <-- ', closePeaks[i], latestStart)
            closePeaks = closePeaks[i:]
            break  

    for i in range(len(closeTroughs) - 1):
        if parse(closeTroughs[i]['x']) > parse(latestStart):
            print('--> --> Closest date located in CLOSETROUGHS <-- <-- ', closeTroughs[i], latestStart)
            closeTroughs = closeTroughs[i:]
            break

    for i in range(len(lowerBand) - 1):
        # 1 for loop will handle all data for bbands
        if timeFrame == "TIME_SERIES_INTRADAY":
            if (lowerBand[i]['x'] + ":00") == latestStart:
                print('--> --> Matching date located in BBAND <-- <-- ', lowerBand[i], latestStart)
                lowerBand = lowerBand[i:]
                upperBand = upperBand[i:]
                middleBand = middleBand[i:]
                break
        else:
            if lowerBand[i]['x'] == latestStart:
                print('--> --> Matching date located in BBAND <-- <-- ', lowerBand[i], latestStart)
                lowerBand = lowerBand[i:]
                upperBand = upperBand[i:]
                middleBand = middleBand[i:]
                break

    for i in range(len(macd) - 1):
        # 1 for loop will handle all data for macd
        if macd[i]['x'] == latestStart:
            print('--> --> Matching date located in MACD <-- <-- ', macd[i], latestStart)
            macd = macd[i:]
            histogram = histogram[i:]
            signal = signal[i:]
            break
    
    for i in range(len(rsiPts) - 1):
        if timeFrame == "TIME_SERIES_INTRADAY":
            if (rsiPts[i]['x'] + ":00") == latestStart:
                print('--> --> Matching date located in RSI <-- <-- ', rsiPts[i], latestStart)
                rsiPts = rsiPts[i:]
                break
        else:
            if rsiPts[i]['x'] == latestStart:
                print('--> --> Matching date located in RSI <-- <-- ', rsiPts[i], latestStart)
                rsiPts = rsiPts[i:]
                break

    for i in range(len(rsiPeaks) - 1):
        if parse(rsiPeaks[i]['x']) > parse(latestStart):
            print('--> --> Closest date located in RSIPEAKS <-- <-- ', rsiPeaks[i], latestStart)
            rsiPeaks = rsiPeaks[i:]
            break

    for i in range(len(rsiTroughs) - 1):
        if parse(rsiTroughs[i]['x']) > parse(latestStart):
            print('--> --> Closest date located in RSITROUGHS <-- <-- ', rsiTroughs[i], latestStart)
            rsiTroughs = rsiTroughs[i:]
            break


    priceResult = {}
    priceResult['close'] = close
    priceResult['peaks'] = closePeaks
    priceResult['troughs'] = closeTroughs
    
    bbandResult = {}
    bbandResult['lowerBand'] = lowerBand
    bbandResult['upperBand'] = upperBand
    bbandResult['middleBand'] = middleBand

    macdResult = {}
    macdResult['macd'] = macd
    macdResult['histogram'] = histogram
    macdResult['signal'] = signal

    rsiResult = {}
    rsiResult['rsi'] = rsiPts
    rsiResult['peaks'] = rsiPeaks
    rsiResult['troughs'] = rsiTroughs

    result = {}
    result['prices'] = priceResult
    result['bbands'] = bbandResult
    result['macd'] = macdResult
    result['rsi'] = rsiResult
    return json.dumps(result)
