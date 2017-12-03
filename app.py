from math import cos, asin, sqrt
from flask import Flask, jsonify, request
import pandas as pd
import json
import requests

app = Flask(__name__)

@app.route('/jetblue/api/get_deal', methods=['POST'])
def get_deal():
	content = request.get_json()
	currTags = content['entities']
	targetAirport = str(getAirport(currTags))
	deal = getDeal(targetAirport, content['lat'], content['lon'])
	keys = ["OriginAirportCode", "DestinationAirportCode", "FlightType", "FareType", "FinalScore", "FareDollarAmount", "TaxDollarAmount", "FarePointsAmount", "TaxPointsAmount"]
	deal_dict = dict(zip(keys, deal))
	return json.dumps(deal_dict)
	
@app.route('/jetblue/api/get_photos', methods=['POST'])
def get_photos():
	content = request.get_json()
	currTags = content['entities'] 
	targetAirport = str(getAirport(currTags))
	deal = getDeal(targetAirport, content['lat'], content['lon'])
	lat, lon = findCoordinate(str(deal[1]))
	info = getNearbyPlaces(str(lat), str(lon))
	return info
	
def getNearbyPlaces(lat, lon):
	key = 'AIzaSyDjOV_yQ0Dfxzz6HIO5Z0nzSsh4MIDOrvY'
	url0 = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=' + lat + ',' + lon + '&radius=1000&key=' + key
	response0 = requests.get(url0)
	responseJson0 = response0.json()
	print responseJson0
	datas = []
	for i in range(0, len(responseJson0['results'])):
		if 'photos' in responseJson0['results'][i]:
			photo_reference = responseJson0['results'][i]['photos'][0]['photo_reference']
			url1 = 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=' + photo_reference + '&key=' + key
			data = {
				'name':responseJson0['results'][i]['name'],
				'vicinity':responseJson0['results'][i]['vicinity'],
				'photos':url1
			}
			datas.append(data)
	return json.dumps(datas)

def getDeal(targetAirport, lat, lon):
	labels_df = pd.read_csv("Deals.csv")
	cols = ["BatchId", "OriginAirportCode", "DestinationAirportCode", "FlightDate", "FlightType", "FareType", "FinalScore", "FareDollarAmount", "TaxDollarAmount", "FarePointsAmount", "TaxPointsAmount", "IsDomesticRoute", "IsHotDeal", "IsPriceDrop", "PriceDropFromDollarAmount", "LastDayOfFare", "DaysOfWeek", "IsNewPriceDrop"]
		
	dropCols = [0, 3, 11, 12, 13, 14, 15, 16, 17]
	for dropCol in dropCols:
		labels_df = labels_df.drop(cols[dropCol], axis=1)
	
	labels_df = returnAirports(labels_df, targetAirport)
	originAirports = labels_df['OriginAirportCode'].values
	closestAirport = findClosestAirport(originAirports, lat, lon)
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
	key = 'AIzaSyDjOV_yQ0Dfxzz6HIO5Z0nzSsh4MIDOrvY'
	url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query=' + locName + '&key=' + key
	response = requests.get(url)
	responseJson = response.json()
	if responseJson['status'] == 'OK':
		return responseJson['results'][0]['geometry']['location']['lat'], responseJson['results'][0]['geometry']['location']['lng']
	else:
		return 1, 1
	
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
	return labels_df.loc[labels_df['DestinationAirportCode'] == destinationCode]

def highestScore(labels_df):
	return labels_df.loc[labels_df['FinalScore'].idxmax()]

if __name__ == '__main__':
	#main()
	app.run(debug=True)
	get_deal()
	get_photos()
