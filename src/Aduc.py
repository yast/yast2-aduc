#!/usr/bin/env python

from ycp import *
import gettext
from gettext import textdomain
textdomain('mysql')

import_module('Progress')
import_module('Report')
import_module('Message')
import_module('Wizard')


import time
from ycp import *

def Read():

    	#/* aduc read dialog caption */
    	caption = 'Initializing the aduc Configuration'

    	steps = 2

    	Progress.New( caption, ' ', steps, [
		'Read the current aduc configuration',
		'Read the current aduc state'
	  ], [

		"Reading the current aduc configuration...",

	    	"Reading the current aduc state...",

	    	Message.Finished()
	  ],
	  ''
    	)

    	if False: 
	    return False
    	Progress.NextStage()
    	#/* Error message */
    	if False: 
	    Report.Error(Message.CannotReadCurrentSettings())
    	time.sleep(1)

    	if False: 
	    return False
    
    	Progress.NextStep()
    	#/* Error message */
    	if False:
	     Report.Error('Cannot read the current aduc state.')
    	time.sleep(1)

    	if False: 
	    return False
    
    	Progress.NextStage ()
    	time.sleep(1)
   
    	return True



def Write() :
    	#/* aduc read dialog caption */
    	caption = 'Saving the aduc Configuration'

    	steps = 2
    
    	Progress.New(caption, ' ', steps, [
	    	#/* Progress stage 1/2 */
	    	'Write the aduc settings',
	    	#/* Progress stage 2/2 */
	    	'Adjust the aduc service'
	   ], [
	    	#/* Progress step 1/2 */
	    	'Writing the aduc settings...',
	    	#/* Progress step 2/2 */
	    	'Adjusting the aduc service...',
	    	Message.Finished()	
	   ],
	   ''
    	)

    	time.sleep(1)

    	if False: 
		return False
    	Progress.NextStage()
    	#/* Error message */
    	if False: 
		Report.Error ('Cannot write the aduc settings.')
    	time.sleep(1)

    	if False: 
		return False
    	Progress.NextStage ()
    	#/* Error message */
    	if False: 
		Report.Error (Message.CannotAdjustService('aduc'))
    	time.sleep(1)

    	Progress.NextStage ()
    	time.sleep(1)

    	return True


def ReadDialog():
	ret = Read()
	if ret:
		return Symbol('next')
	else:
		return Symbol('abort')


def WriteDialog() :
	ret = Write()
	if ret:
		return Symbol('next')
	else:
		return Symbol('abort')

