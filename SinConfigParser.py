from ConfigParser import ConfigParser

#
# don't lowercase the options
#
class ConfigParser(ConfigParser):

    def optionxform(self, optionstr):
        return optionstr
