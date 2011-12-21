'''
blindSqli.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
from functools import partial

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.sql_tools.blind_sqli_response_diff import \
    blind_sqli_response_diff
from core.controllers.sql_tools.blind_sqli_time_delay import \
    blind_sqli_time_delay
from core.data.options.option import option
from core.data.options.optionList import optionList
import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb


class blindSqli(baseAuditPlugin):
    '''
    Find blind SQL injection vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._bsqli_response_diff = blind_sqli_response_diff()
        self._blind_sqli_time_delay = blind_sqli_time_delay()
        
        # User configured variables
        self._equalLimit = 0.9
        self._equAlgorithm = 'setIntersection'

    def audit(self, freq):
        '''
        Tests an URL for blind Sql injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug('blindSqli plugin is testing: ' + freq.getURL())
        
        bsqli_resp_diff = self._bsqli_response_diff
        kb_has_no_bsqli = partial(
                              self._hasNoBug,
                              'blindSqli',
                              'blindSqli',
                              freq.getURL()
                              )
        
        for parameter in freq.getDc():
            
            # Try to identify the vulnerabilities using response
            # string differences
            bsqli_resp_diff.setUrlOpener(self._urlOpener)
            bsqli_resp_diff.setEqualLimit(self._equalLimit)
            bsqli_resp_diff.setEquAlgorithm(self._equAlgorithm)
            # FIXME: what about repeated parameter names?
            vuln_resp_diff = bsqli_resp_diff.is_injectable(freq, parameter)
            
            if vuln_resp_diff is not None and \
                kb_has_no_bsqli(vuln_resp_diff.getVar()):
                om.out.vulnerability(vuln_resp_diff.getDesc())
                kb.kb.append(self, 'blindSqli', vuln_resp_diff)
            else:
                # And I also check for Blind SQL Injections using time delays
                self._blind_sqli_time_delay.setUrlOpener(self._urlOpener)
                time_delay = \
                    self._blind_sqli_time_delay.is_injectable(freq, parameter)
                if time_delay is not None and \
                    kb_has_no_bsqli(vuln_resp_diff.getVar()):
                    om.out.vulnerability(time_delay.getDesc())
                    kb.kb.append(self, 'blindSqli', time_delay)
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'The algorithm to use in the comparison of true and false response for blind sql.'
        h1 = 'The options are: "stringEq" and "setIntersection". '
        h1 += 'Read the long description for details.'
        o1 = option('equAlgorithm', self._equAlgorithm, d1, 'string', help=h1)
        
        d2 = 'Set the equal limit variable'
        h2 = 'Two pages are equal if they match in more than equalLimit. Only used when '
        h2 += 'equAlgorithm is set to setIntersection.'
        o2 = option('equalLimit', self._equalLimit, d2, 'float', help=h2)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._equAlgorithm = optionsMap['equAlgorithm'].getValue()
        self._equalLimit = optionsMap['equalLimit'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ ]

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds blind SQL injections.
        
        Two configurable parameters exist:
            - equAlgorithm
            - equalLimit
        
        The equAlgorithm parameter configures how the comparison of pages is done, the options for equAlgorithm are:
            - stringEq
            - setIntersection
            
        The classic way of matching two strings is "stringEq" , in Python this is "string1 == string2" , but other ways have been
        developed for sites that have changing banners and random data on their HTML response. "setIntersection" will create
        two different sets with the words inside the two HTML responses, and do an intersection. If number of words that are
        in the intersection set divided by the total words are more than "equalLimit", then the responses are equal.
        '''
