
import sys
import requests
import json

DEBUG = False

class ApiError:
  def __init__(self, code, body):
    self.code = code
    self.errors = None

    if type(body) == dict and body.has_key('errors') and len(body['errors']) > 0:
      self.errors = body['errors']
    else:
      self.errors = ["" + body]

  def __str__(self):
    ret = "CODE: " + str(self.code)

    for error in self.errors:
      ret = ret + "\n"

      if type(error) == dict and error.has_key('error') and error.has_key('error_description'):
        ret = ret + error['error'] + ": " + error['error_description']
      elif type(error) == dict and error.has_key('error_code') and error.has_key('error_message'):
        ret = ret + str(error['error_code']) + ": " + error['error_message']
      elif type(error) == str or type(error) == unicode:
        ret = ret + error
      else:
        key = Object.keys(error)[0]
        ret = ret + key + ": " + error[key]

    return ret

class FlowerPowerCloud:

  url = 'https://api-flower-power-pot.parrot.com'

  def __init__(self):
    self._token = {};
    self._isLogged = False;
    self.credentials = {};
    self.autoRefresh = False;

    api = {
      # Profile
      'getProfile': {'method': 'GET/json', 'path': '/user/v4/profile', 'auth': True},
      'getUserVersions': {'method': 'GET/json', 'path': '/user/v1/versions', 'auth': True},
      'verify': {'method': 'GET/json', 'path': '/user/v1/verify', 'auth': True},

      # Garden
      #'getSyncGarden': {'method': 'GET/json', 'path': '/sensor_data/v4/garden_locations_status', 'auth': True},
      'getConfiguration': {'method': 'GET/json', 'path': '/garden/v2/configuration', 'auth': True},
      'getGarden': {'method': 'GET/json', 'path': '/garden/v1/status', 'auth': True},
      #'getSyncData': {'method': 'GET/json', 'path': '/sensor_data/v3/sync', 'auth': True},
      #'getFirmwareUpdate': {'method': 'GET/json', 'path': '/sensor_data/v1/firmware_update', 'auth': True},
      #'getLocationSamples': {'method': 'GET/json', 'path': '/sensor_data/v2/sample/location/:location_identifier', 'auth': True},
      #'getStatistics': {'method': 'GET/json', 'path': '/sensor_data/v1/statistics/:location_identifier', 'auth': True},

      'sendSamples': {'method': 'PUT/json', 'path': '/sensor_data/v8/sample', 'auth': True},
      'sendGardenStatus': {'method': 'PUT/json', 'path': "/garden/v1/status", 'auth': True},

      # Images
      'getImageLocation': {'method': 'GET/json', 'path': '/image/v3/location/user_images/:location_identifier', 'auth': True},
    };

    for item in api:
      self.makeReqFunction(item, api[item])

  def makeReqFunction(self, name, req):

    def _method(data, callback):
      self.invoke(req, data, callback);

    setattr(self, name, _method)

  def makeHeader(self, req, data):
    options = {'headers': {}}
    verb = req['method'].split('/')[0]
    vtype = req['method'].split('/')[1]

    if vtype == 'urlencoded':
      #options.['body'] = qs.stringify(data)
      options['body'] = data
      options['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
    elif vtype == 'json':
      options['body'] = json.dumps(data)
      #options['body'] = data
      options['headers']['Content-Type'] = 'application/json'
    else:
      options['body'] = data
      options['headers']['Content-Type'] = 'text/plain'

    options['url'] = self.url + req['path']
    options['method'] = verb

    if req.has_key('auth') and req['auth']:
      options['headers']['Authorization'] = "Bearer " + self._token['access_token']
    else:
      options['headers']['Authorization'] = ""

    return options

  def makeUrl(self, req, data):

    if data is not None and data.has_key('path') and data.has_key('url'):
      for item in data['url']:
        req['path'] = req['path'].replace(':' + item, data.url[item])

      del data['url']

    #if DEBUG:
    #  self.loggerReq(req, data)
    return req

  def loggerReq(self, req, data):
    print(req.method, req.path);
    for key in data:
      print(key + ":", data[key]);

  def request(self, data, callback):

    print "Url:     ", data['url']
    print "Headers: ", data['headers']
    print "Body:    "
    print json.dumps(data["body"], indent=2, sort_keys=True)

    if data['method'] == 'GET':
      r = requests.get(data['url'], data=data['body'], headers=data['headers'])
    elif data['method'] == 'POST':
      r = requests.post(data['url'], data=data['body'], headers=data['headers'])
    elif data['method'] == 'PUT':
      r = requests.put(data['url'], data=data['body'], headers=data['headers'])

    print "Response: "
    print json.dumps(json.loads(r.text), indent=2, sort_keys=True)

    callback(self, None, r, r.text)

  def invoke(self, req, data, callback):
    options = {}

    #print "invoke", "req:", req, "data:", data, "callback:", callback

    if callable(data):
      callback = data
      data = None

    if data is not None and type(data) != dict:
      print  'Data is not a json', type(data)
      return callback(self, 'Data is not a json')

    req = self.makeUrl(req, data)
    options = self.makeHeader(req, data)

    if DEBUG:
      print "options", options

    def requestCallback(self, err, res, body):
      if type(body) == str or type(body) == unicode:
        try:
          #print "requestCallback", body
          body = json.loads(body)
        except Exception, e:
          print e
          #pass

      if err:
        callback(err, None)

      elif res.status_code != 200 or (type(body) == dict and body.has_key('errors') and len(body['errors']) > 0):
        return callback(self, ApiError(res.status_code, body), None);

      elif callback:
        results = body

        return callback(self, None, results)

      else:
        #throw "Give me a callback"
        print "Give me a callback"
        pass

    self.request(options, requestCallback)

  def login(self, data, callback):
    req = {'method': 'POST/urlencoded', 'path': '/user/v2/authenticate'}

    if data.has_key('auto-refresh') and type(data['auto-refresh']) is bool:
      self.autoRefresh = data['auto-refresh']
      del data['auto-refresh']

    self.credentials = data
    data['grant_type'] = 'password';

    def invokeCallback(self, err, res):
      if err:
        callback(self, err)
      else:
        self.setToken(res, callback)

    self.invoke(req, data, invokeCallback)

  def setToken(self, token, callback):
    self._token = token;
    self._isLogged = True;

    if self.autoRefresh:
      def scheduleCallback():
        self.refresh(token)

      #job = new schedule.Job(scheduleCallback)

      #job.schedule(new Date(Date.now() + (token['expires_in'] - 1440) * 1000));

    if callable(callback):
      callback(self, None, token)

  def refresh(self, token):
    req = {'method': 'POST/urlencoded', 'path': '/user/v2/authenticate'}

    data = {
      'client_id':  self.credentials['client_id'],
      'client_secret': self.credentials['client_secret'],
      'refresh_token': token.refresh_token,
      'grant_type': 'refresh_token'
    }

    def invokeCallback(self, err, res):
      if err: 
        callback(self, err)
      else:
        self.setToken(res)

    self.invoke(req, data, invokeCallback)

  def concatJson(self, json1, json2):
    dest = json1;

    for key in json2.keys():
      if json1.has_key(key) and type(json1[key]) == object and type(json2[key]) == object:
        dest[key] = self.concatJson(json1[key], json2[key])
      else:
        dest[key] = json2[key]

    return dest;

def main(argv):
  print "Starting"
  cloud = FlowerPowerCloud()

  credentials = json.load(open('credentials.json'))
  credentials = credentials['flowerpower']
  credentials['auto-refresh'] = False

  def loginCallback(self, err, res):
    print "BACK2"
    if err:
     print err
    else:
      #print "Head in the clouds :)", res
      pass

  def getGardenCallback(self, err, res):
    if err:
     print err
    else:
      print "Garden"
      print json.dumps(res, indent=2, sort_keys=True)
      pass

  cloud.login(credentials, loginCallback)
  cloud.getProfile(None, getGardenCallback)
  cloud.getUserVersions(None, getGardenCallback)

 # cloud.getSyncGarden(None, getGardenCallback)
  cloud.getConfiguration(None, getGardenCallback)
  cloud.getGarden(None, getGardenCallback)
  #cloud.getSyncData(None, getGardenCallback)
  #cloud.getLocationSamples(None, getGardenCallback)
  #cloud.getStatistics(None, getGardenCallback)



if __name__ == "__main__":
  main(sys.argv)