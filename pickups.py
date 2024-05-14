import sys, os, datetime, re
sys.path.insert(0,os.path.expanduser('~'))
# GALAXY_WEB_Assortment
from gx_api import galaxy_api_class
from rh_atg_api import rh_atg_api
# gx = galaxy_api_class.gx_api( production = True )
gx = galaxy_api_class.gx_api( database = 'GALAXY_WEB_Assortment', production = True)
rh_atg = rh_atg_api.rh_atg_wrapper()

start_date = datetime.datetime.today().strftime("%m/%d/%Y")
delta = datetime.timedelta(90)
end_date = (datetime.datetime.today()+delta).strftime("%m/%d/%Y")
p = {
		'query':[{
		'c_WA_Launch_Date_Earliest' : f'>{start_date}',
		'wm_Product_Status' : 'In Assortment',
		'wm_ImageSource' : 'Pickup',
		'DonorProdID' : '*',
		'omit' : 'false'
	},
	{
		'c_WA_Launch_Date_Earliest' : f'>{end_date}',
		'omit' : 'true'
	}]
} 

donor_pickup_map = {}
response = gx.find_records(p, layout = 'Product_Assortment-Detail_View')
if 'response' in response and 'data' in response['response'] and len(response['response']['data']) > 0:
	for _record in response['response']['data']:
		record = _record['fieldData']
		if 'cat' in record['wm_Web_ProdID']: continue
		if record['wm_Pickup_Source'] == '': continue
		donor_prod = re.search(r'(rhbc_)?(rhtn_)?prod\d+',record['wm_Pickup_Source'])
		if donor_prod == None: continue
		donor_prod = donor_prod.group(0)
		donor_pickup_map[record['wm_Web_ProdID']] = donor_prod

final_list = []
for k,v in zip(donor_pickup_map.keys(), donor_pickup_map.values()):

	info = rh_atg.get_product_info(v)
	if not info == None and 'alternateImages' in info:
		# images = [re.sub(r'.*/',"",i['imageUrl']).replace('_RHR','') for i in info['alternateImages']]
		images = [i['imageId'] for i in info['alternateImages']]
		if len(images) == 0: continue
		else:
			final_list.append((k,",".join(images)))
output = os.path.expanduser('~/Desktop/pickups_for_bcc.csv')
if os.path.exists(output) : os.remove(output)
with open(output,'a') as csv:
	csv.write('''/atg/commerce/catalog/ProductCatalog:product\nID,images\n''')
	for item in final_list:
		csv.write(f'{item[0]},"{item[1]}"\n')


# get the ATG images from the pickup and build the bcc import doc
