import sys, os, datetime, re
sys.path.insert(0,os.path.expanduser('~'))
# GALAXY_WEB_Assortment
from gx_api import galaxy_api_class
from rh_atg_api import rh_atg_api
from box_api import box_api_class
# gx = galaxy_api_class.gx_api( production = True )
gx = galaxy_api_class.gx_api( database = 'GALAXY_WEB_Assortment', production = True)
rh_atg = rh_atg_api.rh_atg_wrapper()

start_date = datetime.datetime.today().strftime("%m/%d/%Y")
delta = datetime.timedelta(180)
end_date = (datetime.datetime.today()+delta).strftime("%m/%d/%Y")
p = {
		'query':[{
		'c_WA_Launch_Date_Earliest' : f'>={start_date}',
		'wm_Product_Status' : 'In Assortment',
		'wm_ImageSource' : 'Pickup',
		# 'DonorProdID' : '*',
		'wm_Pickup_Source':'*',
		'omit' : 'false'
	},
	{
		'c_WA_Launch_Date_Earliest' : f'>{end_date}',
		'omit' : 'true'
	}]
} 

donor_pickup_map = []
response = gx.find_records(p, layout = 'Product_Assortment-Detail_View')
if 'response' in response and 'data' in response['response'] and len(response['response']['data']) > 0:
	for _record in response['response']['data']:
		is_swatch = False
		record = _record['fieldData']
		if 'cat' in record['wm_Web_ProdID']: continue
		if record['wm_Pickup_Source'] == '': continue
		donor_prod = re.search(r'(rhbc_)?(rhtn_)?prod\d+',record['wm_Pickup_Source'])
		swatch_donor = None
		if donor_prod == None:
			if re.match(r'\d+',record['wm_Pickup_Source']) is not None:
				swatch_donor = record['wm_Pickup_Source']
			else:
				swatch_donor = re.search(r'_\d+_', record['wm_Pickup_Source'])
				if swatch_donor is not None:
					swatch_donor = swatch_donor.group(0).replace('_','')
		if donor_prod == None and swatch_donor == None: continue
		if donor_prod != None:
			donor_prod = donor_prod.group(0)
		else:
			donor_prod = swatch_donor
			is_swatch = True
		res = {}
		res['prod_id'] = record['wm_Web_ProdID']
		res['is_swatch'] = is_swatch
		res['donor'] = donor_prod
		donor_pickup_map.append(res)

final_list_prod = []
final_list_swatches = []
for item in donor_pickup_map:
	if item['is_swatch']:
		info = rh_atg.get_swatch_image(item['donor'])
	else:
		info = rh_atg.get_product_info(item['donor'])
	if not info == None:
		if 'alternateImages' in info:
		# images = [re.sub(r'.*/',"",i['imageUrl']).replace('_RHR','') for i in info['alternateImages']]
			images = [i['imageId'] for i in info['alternateImages']]
		else:
			images = [info,]
		if len(images) == 0: continue
		else:
			if item['is_swatch']:
				final_list_swatches.append((item['prod_id'],",".join(images)))
			else:
				final_list_prod.append((item['prod_id'],",".join(images)))

def write_and_upload_output_files(l: list, output:str) -> None:
	'''
	take a list of pickups and a file path
	write the appropriate things to the file
	return a the new name for the output path
	'''
	swatch_prod = None
	if 'prod' in output:
		swatch_prod = 'product'
		with open(output,'w') as csv:
			csv.write('''/atg/commerce/catalog/ProductCatalog:product\nID,images\n''')
	else:
		swatch_prod = 'swatch'
		with open(output,'w') as csv:
			csv.write('''/atg/commerce/catalog/ProductCatalog:swatch\nID,images\n''')
	with open(output,'a') as csv:
		for item in l:
			csv.write(f'{item[0]},"{item[1]}"\n')
	t = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	new_path = os.path.expanduser(f'~/Desktop/{swatch_prod}_pickups_{t}.csv')
	os.rename(output, new_path)
	box = box_api_class.box_api()
	box.upload(new_path,265081413296)
	os.remove(new_path)

product_output = os.path.expanduser('~/Desktop/prod_pickups_for_bcc.csv')
swatch_output = os.path.expanduser('~/Desktop/swatch_pickups_for_bcc.csv')
write_and_upload_output_files(final_list_prod,product_output)
write_and_upload_output_files(final_list_swatches,swatch_output)