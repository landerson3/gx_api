'''
GALAXY FM API Documentation - https://galaxy.restorationhardware.com/fmi/data/apidoc/
username: fmapi
password: BA91gxD!
database: web_images
host: galaxysb.rh.com
'''



## need to deal with "code 953 - Invalid Filemaker Data API Token" (reauthenticate)
import requests,json, time, logging
from base64 import b64encode

# logging.basicConfig(filename = "galaxy_api_class.log", encoding = "utf-8", level = logging.DEBUG)

class gx_api():
	def __init__(self, database = 'web_images', production = False):
		logging.info(f'Initializing GX with production = {production}')
		self.database = database
		self.version = 'vLatest'
		if production:
			self.username = "fmapi"
			self.password = "#hRC9LNfQvc"
			self.host = "https://galaxy.restorationhardware.com"
		else:
			self.username = "fmapi"
			self.password = "BA91gxD!"
			self.host = "https://galaxysb.rh.com"

		self.authenticate()
		self.get_layouts()
		self._max_attempts = 5
		self._attempts = 0
		self.authheader = {
			"Authorization":f"Bearer {self.token}",
			"Content-Type":"application/json"
		}

	def authenticate(self):
		self.auth_code = self.generate_auth_code()
		self.get_token()
		logging.debug(f"Galaxy_API_Class.gx_api().authenticate() :: Authcode set to {self.auth_code}")
		logging.debug(f"Galaxy_API_Class.gx_api().authenticate() :: Token is {self.token}")

	def get_layouts(self): #TODO
		pass

	def generate_auth_code(self):
		bytes_code = b64encode(bytes(f"{self.username}:{self.password}",'utf-8'))
		return bytes_code.decode('ascii')

	def logout(self):
		logging.info("Logging out of GX.")
		r = requests.delete(f'{self.host}/fmi/data/{self.version}/databases/{self.database}/sessions/{self.token}',)

	def find_records(self,params, layout = "RT_API_View", offset = 0, limit = 500):
		if self.database == 'GALAXY_WEB_Assortment' and layout == 'RT_API_View':
			layout = 'Product_Assortment-Detail_View'
		# if self._find_result = []
		# find records matching the provided parameters and return the files as a json
		# https://galaxy.restorationhardware.com/fmi/data/apidoc/#operation/find
		if params == None or len(params) == 0:
			raise ValueError('No value provided for params')
		headers = {
			"Authorization":f"Bearer {self.token}",
			"Content-Type":"application/json"
		}
		params['limit'] = limit
		# params['offset'] = offset
		# print(params)
		if not type(params) == str(): params = json.dumps(params)
		response = requests.post(f'{self.host}/fmi/data/{self.version}/databases/{self.database}/layouts/{layout}/_find',
			headers = headers,
			data = params
			)
		
		logging.debug(f"{len(response.request.body)+len(response.request.headers)} bytes outboud to GX")
		# print(len(response.content))
		logging.debug(f"{len(response.content)} bytes inbound from GX")
		
		# logging.debug(f"Requesting records from GX. {response.re}")
		if response.status_code < 400:
			res = json.loads(response.content)
			# if res['response']['data']['portalData']
			return res
		else:
			return response

	def get_token(self):
		headers = {
			'Content-Type':'application/json',
			'Authorization':f'Basic {self.auth_code}'
		}
		response = requests.post(f'{self.host}/fmi/data/{self.version}/databases/{self.database}/sessions',
			headers = headers
		)
		token = json.loads(response.content)['response']['token']
		self.token = token
	

	def update_record(self,recordID, data,layout="Retoucher_DetailView"):
		url = f"{self.host}/fmi/data/{self.version}/databases/{self.database}/layouts/{layout}/records/{recordID}"
		headers = {
			"Authorization":f"Bearer {self.token}",
			"Content-Type":"application/json"
		}
		# print("GX Headers:", headers)
		# print("GX data", data)
		full_data = json.dumps({
			"fieldData": data,
			"portalData": { },
			}
		)
		r = requests.patch(url, headers=headers, data=full_data)
		## check for status of 301 (user stepping on record) && 952 (expired token)
		response_code = r.json()['messages'][0]['code']
		logging.debug(f"{len(r.request.body)+len(r.request.headers)} bytes outboud to GX")
		# print(len(r.content))
		logging.debug(f"{len(r.content)} bytes inbound from GX")
		logging.debug(f"Galaxy_API_Class.gx_api().update_record() :: Response code is {response_code}")
		if response_code in [301, "301"] and self._attempts < self._max_attempts:
			time.sleep(3)
			self._attempts +=1
			self.update_record(recordID, data, layout="Retoucher_DetailView")

		elif response_code in [301, "301"] and self._attempts > self._max_attempts:
			self._attempts +=1
			## 301 code means someone is "stepping" on the record
			return r
		elif response_code in [952, "952"]:
			logging.debug(f"Galaxy_API_Class.gx_api().update_record() :: Code 952 :: Updating Authentication")
			self.authenticate()
			return self.update_record(recordID, data)
		else:
			print(f'updating record with {r.content}')
			return r

	def update_records(self, recordIDs, data, layout="Retoucher_DetailView"):
		## need to add check for response 301
		omni_data = False
		if type(data) is not type(list()):
			omni_data = True
		for i,recordID in enumerate(recordIDs):
			if omni_data:
				self.update_record(recordID,data)
			elif type(data) is type(list()):
				self.update_record(recordID, data[i])
		return

# gx = gx_api()
# params = {
# 		'query':[{
# 			'cRetoucher_ ImageName':'MarbellaTeak_Table_Dining_Round_TeakNatural_prod14360356_E910507779_F_CC.tif'
# 		}]
# 	}
# # print(gx.find_records(params,layout='Retoucher_DetailView'))