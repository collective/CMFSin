from OFS.SimpleItem import SimpleItem
from DateTime import DateTime

FAIL_THRESHOLD = 3
FAIL_DELAY     = 60 * 60

TIME_SCALE = {
    'hourly' : 60 * 60,
    'daily'  : 60 * 60 * 24,
    'weekly' : 60 * 60 * 24 * 7,
    'monthly': 60 * 60 * 24 * 7 * 4,
    'yearly' : 60 * 60 * 24 * 7 * 4 * 12,
    }

class Channel(SimpleItem):
    def __init__(self, id, uri):
        self.id = id
        self.title = id
        self.uri  = uri

        self.updateBase      = DateTime()
        self.updatePeriod    = 'daily'
        self.updateFrequency = 1
        self._v_failCount    = 0
        self._v_failTime     = None
        
        self.last = None
        

    def update(self, data=None):
        self.last = DateTime()
        if data:
            # Parse what we can from the data,
            # esp. the syn: info
            info, data = data
            self.updateBase      = info.get('updateBase', self.last)
            self.updatePeriod    = info.get('updatePeriod', 'daily')
            self.updateFrequency = info.get('updateFrequency', 1)
            self.title           = info.get('title', self.id)
    

    def failed(self):
        if self._v_failCount == FAIL_THRESHOLD:
            self._v_failTime = DateTime().timeTime() + FAIL_DELAY
        self._v_failCount += 1

    def clear(self):
        self._v_failCount = 0
        self._v_failTime  = None
        
    
    def requireUpdate(self):
        now  = DateTime().timeTime()
        if self.last:
            last = self.last.timeTime()
        else:
            last = 0

        #Check if the channel is down
        if not hasattr(self, '_v_failCount'):
            self._v_failCount = 0
            self._v_failTime  = None
            
        if self._v_failCount > FAIL_THRESHOLD:
            if self._v_failTime < now:
                self.clear()
        

        #Find if we exceeded the delta
        seconds = self.updateFrequency * TIME_SCALE[self.updatePeriod]

        if (last + seconds) < now:
            return 1
        return 0
        
        
        
    
    
