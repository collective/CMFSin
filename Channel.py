from OFS.SimpleItem import SimpleItem
from DateTime import DateTime

FAIL_THRESHOLD = 3
FAIL_DELAY     = 60 * 60

TIME_KEY =  {
    'h' : 'hourly',
    'd' : 'daily',
    'w' : 'weekly',
    'm' : 'monthly',
    'y' : 'yearly',
    }
    

TIME_SCALE = {
    'hourly' : 60 * 60,
    'daily'  : 60 * 60 * 24,
    'weekly' : 60 * 60 * 24 * 7,
    'monthly': 60 * 60 * 24 * 7 * 4,
    'yearly' : 60 * 60 * 24 * 7 * 4 * 12,
    }

class Channel(SimpleItem):
    def __init__(self, id, uri, **kwargs):
        self.id = id
        self.title = id
        self.uri  = uri

        self.updateBase      = None
        self.updatePeriod    = TIME_KEY[kwargs.get('period', 'd')]
        self.updateFrequency = int(kwargs.get('frequency', 1))
        self._v_failCount    = 0
        self._v_failTime     = None
        
        self.last = None

    def update(self, data=None):
        """update a channel with new data"""
        self.last = DateTime()
        if data:
            # Parse what we can from the data,
            # esp. the syn: info
            info, data = data
            try:
                updateBase      = DateTime(info.get('updateBase'))
            except:
                self.updateBase = self.last

            #For now I let this get overridden by the channel, but it should
            #be the otherway prolly
            self.updatePeriod    = info.get('updatePeriod', self.updatePeriod)
            self.updateFrequency = int(info.get('updateFrequency', self.updateFrequency))
            self.title           = info.get('title', self.id)
            

    def failed(self):
        """set a channel failure"""
        if self._v_failCount == FAIL_THRESHOLD:
            self._v_failTime = DateTime().timeTime() + FAIL_DELAY
        self._v_failCount += 1

    def clear(self):
        """clear any errors"""
        self._v_failCount = 0
        self._v_failTime  = None
        

    def nextUpdateSeconds(self):
        """The next update"""
        if self.last:
            last = self.last.timeTime()
        else:
            last = 0

        #Find if we exceeded the delta
        seconds = self.updateFrequency * TIME_SCALE[self.updatePeriod]
        
        return seconds + last

    def nextUpdate(self):
        """next update time"""
        return DateTime(self.nextUpdateSeconds())

    def requireUpdate(self):
        #Check if the channel is down
        now  = DateTime().timeTime()

        if not hasattr(self, '_v_failCount'):
            self._v_failCount = 0
            self._v_failTime  = None
            
        if self._v_failCount > FAIL_THRESHOLD:
            if self._v_failTime < now:
                self.clear()
        
        if self.nextUpdateSeconds() < now:
            return 1
        return 0
        
        
        
    
    
