import pandas as pd
import rustic_pathways
import teenlife_crawler
import summer_discovery

def get_data():
	'''
	Imports all the data from the crawlers and makes them into pandas dataframes
	Inputs:
		none
	Returns:
		List of dataframes
	'''
	df_teenlife = teenlife_crawler.crawler()
	df_rustic = rustic_pathways.crawler()
	df_summer = summer_discovery.crawler()
	return [df_teenlife, df_rustic, df_summer]


states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

lower_states = []
for i in states:
	lower_states.append(i.lower())

dictionary_na = {'ages': '0', 'description' : 'No description specified',
					 'category': 'No subject specified', 'destinations': 'No country specified',
					 'location': 'No city specified', 'minimum cost': 0, 'website': 'No url specified',
					 'title': 'No title specified'}

rename_rustic = {'service types' : 'category', 'countries': 'destinations', 'minimum_cost': 'minimum cost'}

rename_summer = {'program':'title', }



def clean_data(df):
	'''
	Cleans the data of a dataframe
	Inputs:
		df: Pandas dataframe to be cleaned
	Returns:
		Cleaned df
	'''
	min_ages = []
	max_ages = []
	columns_to_drop = []
	destinations = []
	for i in df.columns:
		if i in rename_rustic:
			df = df.rename(columns = rename_rustic)
		if i in rename_summer:
			df = df.rename(columns = rename_summer)
		if i not in dictionary_na:
			columns_to_drop.append(i)
	if 'destinations' not in df.columns:
		for i, row in df.iterrows():
			if row['location'][-2:] in lower_states or row['location'][-2:] in states:
				destinations.append('usa')
			else:
				destinations.append('other')
		df['destinations'] = destinations
	if 'service types' in columns_to_drop:
		columns_to_drop.remove('service types')
		columns_to_drop.remove('countries')
		columns_to_drop.remove('minimum_cost')
	if 'program' in columns_to_drop:
		columns_to_drop.remove('program')
	df = df.fillna(dictionary_na)
	for index, row in df.iterrows():
		if row['title'][-13:] == ' on teenlife':
			row['title'] = row['title'][16:-13]
		if row['title'][-16] == ' rustic pathways':
			row['title'] = row['title'][:-16]
		if row['ages'] != '0':
			min_ages.append(int(df.at[index, 'ages'][0]))
			max_ages.append(int(df.at[index, 'ages'][-1]))
		else:
			min_ages.append(0)
			max_ages.append(0)
		if row['destinations'][0] == '[' or row['destinations'][-1] == ']' or type(row['destinations']) == list:
			destination = 'multiple countries'
		else:
			destination = row['destinations']
		df.at[index, 'destinations'] = destination
	df['min_ages'] = min_ages
	df['max_ages'] = max_ages
	columns_to_drop.append('ages')
	df = df.drop(columns = columns_to_drop)
	return df

def write_to_csv(file_path):
	'''
	Takes a file path and merges all the data frames from the crawler and writes them to a csv
	Input:
		File path: the file path that you want to write the csv (we wrote it to 'mysite/data.csv')
	Returns: none
	'''
	list_df = get_data()
	good_df = []
	for i in list_df:
		good_df.append(clean_data(i))
	df = pd.concat(good_df, ignore_index = True)
	df.to_csv(file_path)
