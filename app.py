from math import cos, asin, sqrt
from flask import Flask, jsonify, request
import pandas as pd
import json

app = Flask(__name__)

@app.route('/jetblue/api/get_deal', methods=['POST'])
def get_deal():
	content = request.get_json()
	currTags = content['entities'] 
	print currTags
	#currTags = ["skyscraper", "city"] #need image tag
	targetAirport = str(getAirport(currTags))
	#print targetAirport
	deal = getDeal(targetAirport, content['lat'], content['lon'])
	keys = ["OriginAirportCode", "DestinationAirportCode", "FlightType", "FareType", "FinalScore", "FareDollarAmount", "TaxDollarAmount", "FarePointsAmount", "TaxPointsAmount"]
	deal_dict = dict(zip(keys, deal))
	print json.dumps(deal_dict)
	return json.dumps(deal_dict)
	#print jsonify({getDeal(targetAirport, content['lat'], content['lon'])})
	#return jsonify({getDeal(targetAirport, content['lat'], content['lon'])}) #need curr location

def main():
	'''currTags = ["skyscraper", "city"] #need image tag
	targetAirport = str(getAirport(currTags))
	print targetAirport
	print getDeal(targetAirport, 60, 160) #need curr location'''

def getDeal(targetAirport, lat, lon):
	labels_df = pd.read_csv("Deals.csv")
	cols = ["BatchId", "OriginAirportCode", "DestinationAirportCode", "FlightDate", "FlightType", "FareType", "FinalScore", "FareDollarAmount", "TaxDollarAmount", "FarePointsAmount", "TaxPointsAmount", "IsDomesticRoute", "IsHotDeal", "IsPriceDrop", "PriceDropFromDollarAmount", "LastDayOfFare", "DaysOfWeek", "IsNewPriceDrop"]
		
	dropCols = [0, 3, 11, 12, 13, 14, 15, 16, 17]
	for dropCol in dropCols:
		labels_df = labels_df.drop(cols[dropCol], axis=1)
		
	#print labels_df
	
	labels_df = returnAirports(labels_df, targetAirport)
	#print 'new labels '
	#print labels_df
	originAirports = labels_df['OriginAirportCode'].values
	#print 'origin airports ' + originAirports
	closestAirport = findClosestAirport(originAirports, lat, lon)
	#print 'closest airport ' + closestAirport
	lables_df = findMatch(labels_df, targetAirport, closestAirport)
	labels_df = highestScore(labels_df)
	return labels_df.values.tolist()

def getAirport(currTags):
	airport_df = pd.read_csv("airportEntities.csv")
	highestMatchCount = 0
	highestMatchAirport = ''
	for index, row in airport_df.iterrows():
		airportTagsStr = row['entities']
		airportTags = airportTagsStr.split(",")   
		tagCount = getMatchingTagCount(currTags, airportTags)
		if (tagCount > highestMatchCount):
			highestMatchCount = tagCount
			highestMatchAirport = index
	return airport_df.iloc[[highestMatchAirport]]['airport code'].values[0]
	
def getMatchingTagCount(currTags, airportTags):
	count = 0
	for airportTag in airportTags:
		if airportTag in currTags:
			count += 1
	return count

def findCoordinate(locName):
	code_df = pd.read_csv("airportcodes.csv")
	code_df = code_df.loc[code_df['locationID'] == locName]
	return code_df['Latitude'].values, code_df['Longitude'].values
	
def findDistance(lat1, lon1, lat2, lon2):
	p = 0.017453292519943295     #Pi/180
	a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
	return 12742 * asin(sqrt(a)) #2*R*asin

def findMatch(labels_df, originCode, destinationCode):
	labels_df = labels_df.loc[labels_df['DestinationAirportCode'] == destinationCode]
	labels_df = labels_df.loc[labels_df['OriginAirportCode'] == originCode]
	return labels_df

def findClosestAirport(allLoc, currLocationLat, currLocationLon):
	lat1, lon1 = findCoordinate(allLoc[0])
	closestDistance = findDistance(lat1, lon1, currLocationLat, currLocationLon)
	closestAirport = allLoc[0]
	for i in range(1, len(allLoc)):
		lat1, lon1 = findCoordinate(allLoc[i])
		currDistance = findDistance(lat1, lon1, currLocationLat, currLocationLon)
		if (currDistance < closestDistance):
			closestDistance = currDistance
			closestAirport = allLoc[0]
	return closestAirport
	

def returnAirports(labels_df, destinationCode):
	#print labels_df.loc[labels_df['DestinationAirportCode'] == destinationCode]
	return labels_df.loc[labels_df['DestinationAirportCode'] == destinationCode]

def highestScore(labels_df):
	#print labels_df.loc[labels_df['FinalScore'].idxmax()]
	return labels_df.loc[labels_df['FinalScore'].idxmax()]

if __name__ == '__main__':
	#main()
	app.run(debug=True)
	get_deal()
