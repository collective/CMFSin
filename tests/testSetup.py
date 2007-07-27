# This Python file uses the following encoding: utf-8

"""
this test suite was based on Martin Aspeli's 'borg' and David Convent's 'DIYPloneStyle' ones

tested on Zope 2.9.7 and Plone 2.5.3
"""

__author__ = 'Héctor Velarde <hvelarde@jornada.com.mx>'
__docformat__ = 'restructuredtext'
__copyright__ = 'Copyright (C) 2007  DEMOS, Desarrollo de Medios, S.A. de C.V.'
__license__  = 'The GNU General Public License version 2 or later'

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Import the base test case classes
from base import CMFSinTestCase

from Interface.Verify import verifyObject
from OFS.interfaces import ISimpleItem
from Products.CMFCore.interfaces.portal_actions import ActionProvider as IActionProvider

from Products.CMFSin.config import *

class TestInstall(CMFSinTestCase):
    """ ensure product is properly installed """

    def afterSetUp(self):
        self.skins   = self.portal.portal_skins
        self.tool    = self.portal.sin_tool

    def testSkinLayersInstalled(self):
        self.failUnless(SKIN_NAME in self.skins.objectIds())

    def testToolInstalled(self):
        self.failUnless(getattr(self.portal, 'sin_tool', None) is not None)

    def testToolInterface(self):
        t = self.tool
        self.failUnless(ISinTool.isImplementedBy(t))
        self.failUnless(verifyObject(ISinTool, t))

    def testToolNames(self):
        t = self.tool
        self.failUnlessEqual(t.meta_type, 'CMFSin Syndication Tool')
        self.failUnlessEqual(t.getId(), 'sin_tool')
        #self.failUnlessEqual(t.title, 'CMFSin Syndication Tool')
        self.failUnlessEqual(t.plone_tool, True)

    def testToolImplementsActionProvider(self):
        iface = IActionProvider
        self.failUnless(iface.isImplementedBy(self.tool))
        self.failUnless(verifyObject(iface, self.tool))

    def testToolImplementsSimpleItem(self):
        iface = ISimpleItem
        self.failUnless(iface.isImplementedBy(self.tool))
        self.failUnless(verifyObject(iface, self.tool))

class testResourceRegistrations(CMFSinTestCase):
    """ ensure CSS are registered """

    def afterSetUp(self):
        self.qitool      = self.portal.portal_quickinstaller
        self.csstool     = self.portal.portal_css
        product_settings = getattr(self.qitool, PROJECTNAME)
        self.stylesheets = product_settings.resources_css

    def testStylesheetsInstalled(self):
        """Test if new stylesheets were added to portal_css."""
        stylesheetids = self.csstool.getResourceIds()
        for css in STYLESHEETS:
            self.failUnless(css['id'] in stylesheetids)

    def testStylesheetProperties(self):
        """Test if new stylesheets have correct parameters."""
        for config in STYLESHEETS:
            res = self.csstool.getResource(config['id'])
            for key in [key for key in config.keys() if key != 'id']:
                self.assertEqual(res._data[key], config[key])

    def testStylesheetsUpdated(self):
        """Test if existing stylesheets were correctly updated."""
        for config in [c for c in STYLESHEETS
                       if c['id'] not in self.stylesheets]:
            resource = self.csstool.getResource(config['id'])
            for key in [k for k in config.keys() if k != 'id']:
                self.failUnless(resource._data.has_key('original_'+key))

class TestUninstall(CMFSinTestCase):
    """ ensure product is properly uninstalled """

    def afterSetUp(self):
        """ uninstall requieres 'Manager' role """
        self.setRoles(['Manager', 'Member'])
        self.qitool      = self.portal.portal_quickinstaller
        self.csstool     = self.portal.portal_css
        product_settings = getattr(self.qitool, PROJECTNAME)
        self.stylesheets = product_settings.resources_css
        self.qitool.uninstallProducts(products=[PROJECTNAME])

    def testProductUninstalled(self):
        self.failIf(self.qitool.isProductInstalled(PROJECTNAME))

    def testStylesheetsUninstalled(self):
        """Test if added stylesheets were removed from portal_css."""
        resourceids = self.csstool.getResourceIds()
        for css in self.stylesheets:
            self.failIf(css in resourceids)

    def testToolUninstalled(self):
        self.failIf(getattr(self.portal, 'sin_tool', None) is not None)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestInstall))
    suite.addTest(makeSuite(testResourceRegistrations))
    suite.addTest(makeSuite(TestUninstall))
    return suite

if __name__ == '__main__':
    framework()
