from Acquisition import aq_base
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

        self._v_updateBase      = None
        self.updatePeriod    = TIME_KEY[kwargs.get('period', 'd')]
        self.updateFrequency = int(kwargs.get('frequency', 1))
        self._v_failCount    = 0
        self._v_failTime     = None

        self._v_lastUpdate = None


    def update(self, data=None, force=None):
        """update a channel with new data"""
        self._v_lastUpdate = DateTime()
        if data:
            # Parse what we can from the data,
            # esp. the syn: info
            info, data = data
            try:
                self._v_updateBase      = DateTime(info.get('updateBase'))
            except:
                self._v_updateBase = self._v_lastUpdate

            #For now I let this get overridden by the channel, but it should
            #be the otherway prolly
            if force:
                period = info.get('updatePeriod', self.updatePeriod)
                if period != self.updatePeriod:
                    self.updatePeriod  = period
                freq = int(info.get('updateFrequency', self.updateFrequency))
                if freq != self.updateFrequency:
                    self.updateFrequency = freq
                title = info.get('title', self.id)
                if title != self.title:
                    self.title = title

    def failed(self):
        """set a channel failure"""
        if self._v_failCount == FAIL_THRESHOLD:
            self._v_failTime = DateTime(DateTime().timeTime() + FAIL_DELAY)
        self._v_failCount += 1

    def clear(self):
        """clear any errors"""
        self._v_failCount = 0
        self._v_failTime  = None

    def nextUpdateSeconds(self):
        """The next update"""
        last = self.lastUpdateSeconds()
        delta = self.updateFrequency * TIME_SCALE[self.updatePeriod]
        next = last + delta
        if hasattr(aq_base(self), '_v_failTime') and self._v_failTime:
            fail = self._v_failTime.timeTime()
            next = (cmp(fail, next) < 0) and fail or next
            print last, next, fail

        return next

    def lastUpdate(self):
        """last update time"""
        last = 0
        if hasattr(aq_base(self), '_v_lastUpdate') and self._v_lastUpdate:
            last = self._v_lastUpdate.timeTime()
        if last == 0:
            aged = self.updateFrequency * TIME_SCALE[self.updatePeriod] + 300
            self._v_lastUpdate = DateTime(DateTime().timeTime() - aged)
            last = self._v_lastUpdate.timeTime()
        return DateTime(last)

    def lastUpdateSeconds(self):
        return self.lastUpdate().timeTime()

    def nextUpdate(self):
        """next update time"""
        return DateTime(self.nextUpdateSeconds())

    def requireUpdate(self):
        #Check if the channel is down
        now  = DateTime().timeTime()

        if not hasattr(aq_base(self), '_v_failCount'):
            self._v_failCount = 0
            self._v_failTime  = None

        if self._v_failCount > FAIL_THRESHOLD:
            if self._v_failTime < now:
                self.clear()

        if self.nextUpdateSeconds() < now:
            return 1
        return 0





