import numpy as np 
from dateutil.parser import parse
import json


def pricePeaks(timeSeriesData):
    peaks = []
    troughs = []

    for i in range(len(timeSeriesData) - 3):
        if (timeSeriesData[i + 1]['y'] > timeSeriesData[i]['y']) & (timeSeriesData[i + 1]['y'] > timeSeriesData[i + 2]['y']):
            peaks.append(timeSeriesData[i + 1])
        elif (timeSeriesData[i + 1]['y'] < timeSeriesData[i]['y']) & (timeSeriesData[i + 1]['y'] < timeSeriesData[i + 2]['y']):
            troughs.append(timeSeriesData[i + 1])

    peakData = {}
    peakData['peaks'] = peaks
    peakData['troughs'] = troughs
    return json.dumps(peakData)



def macdCrossover(histogramData, priceData):
    uptrendPeriods = []
    downtrendPeriods = []

    for i in range(len(histogramData) - 2):
        if (histogramData[i]['y'] < 0) & (histogramData[i + 1]['y'] > 0):
            start = {"date": histogramData[i + 1]['x'], "type": "start", "hist": histogramData[i + 1]['y']}
            end = {"date": histogramData[i]['x'], "type": "end", "hist": histogramData[i]['y']}
            uptrendPeriods.append(start)
            downtrendPeriods.append(end)
            # print('++++ Starting uptrend. Added two dates to the trend periods: ', start['date'], end['date'])

        elif (histogramData[i]['y'] > 0) & (histogramData[i + 1]['y'] < 0):
            start = {"date": histogramData[i + 1]['x'], "type": "start", "hist": histogramData[i + 1]['y']}
            end = {"date": histogramData[i]['x'], "type": "end", "hist": histogramData[i]['y']}
            uptrendPeriods.append(end)
            downtrendPeriods.append(start)
            # print('++++ Starting downtrend. Added two dates to the trend periods: ', end['date'], start['date'])

    try:
        if uptrendPeriods[0]['type'] == "end":
            del uptrendPeriods[0]
        elif downtrendPeriods[0]['type'] == "end":
            del downtrendPeriods[0]

        if uptrendPeriods[-1]['type'] == "start":
            del uptrendPeriods[-1]
        if downtrendPeriods[-1]['type'] == "start":
            del downtrendPeriods[-1]
    except (IndexError):
        print('Empty trend period array', IndexError)
        pass

    trendData = {}
    trendData['numUpTrends'] = len(uptrendPeriods) // 2
    trendData['numDownTrends'] = len(downtrendPeriods) // 2
    trendData['upTrendPeriods'] = uptrendPeriods
    trendData['downTrendPeriods'] = downtrendPeriods

    if len(uptrendPeriods) > 0:
        uptrendAnalysis = processPeriods(uptrendPeriods, priceData, '-- Uptrend --')
        trendData['UpTrendAnalysis'] = uptrendAnalysis
    else: 
        trendData['UpTrendAnalysis'] = "Null"
        print('--> No uptrend data')

    if len(downtrendPeriods) > 0:
        downtrendAnalysis = processPeriods(downtrendPeriods, priceData, '-- Downtrend --')
        trendData['DownTrendAnalysis'] = downtrendAnalysis
    else:
        trendData['DownTrendAnalysis'] = "Null"
        print('--> No downtrend data')
    
    return json.dumps(trendData)



def processPeriods(trendPeriods, priceData, trendType):
    # print('-------Analyzing Trend: ', trendType, trendPeriods[:5])
    trendAnalysis = []

    for i in range(0, len(trendPeriods) - 1, 2):
        start = trendPeriods[i]
        end = trendPeriods[i + 1]
        # print('~~~~~~~~ start/end dates looking for: ', start['date'], end['date'])

        startPrice = -1
        endPrice = -1

        for dataPt in priceData:
            if dataPt['x'] == start['date']:
                # print('$$$ Found start: ', dataPt['y'], start['date'])
                startPrice = dataPt['y']
            if dataPt['x'] == end['date']:
                # print('$$$ Found end: ', dataPt['y'], end['date'])
                endPrice = dataPt['y']

        trendPeriod = {}
        trendPeriod['start'] = start['date']
        trendPeriod['end'] = end['date']
        trendPeriod['duration'] = calculateDuration(start['date'], end['date'], trendType)
        if (startPrice != -1) & (endPrice != -1):
            trendPeriod['priceChange'] = calculatePriceChange(startPrice, endPrice, trendType)
        else:
            trendPeriod['priceChange'] = 'No data available'
        trendAnalysis.append(trendPeriod)

    # print('>>>>>>>>>>>> Trend Analysis Complete: <<<<<<<<<<<<<<<< ', trendType, trendAnalysis)
    return trendAnalysis


def calculateDuration(startString, endString, trendType):
    return (parse(endString) - parse(startString)).days


def calculatePriceChange(startPrice, endPrice, trendType):
    return endPrice - startPrice

