import pslf
import os
import sys
import time
import math
import helics as h
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
#uncomment the following functions when integrated with helics

def create_broker():
    initstring = "2 --name=mainbroker"
    broker = h.helicsCreateBroker("zmq", "", initstring)
    isconnected = h.helicsBrokerIsConnected(broker)

    if isconnected == 1:
        pass

    return broker


def create_federate(deltat=1.0, fedinitstring="--federates=1"):

    fedinfo = h.helicsFederateInfoCreate()

    status = h.helicsFederateInfoSetFederateName(fedinfo, "Value Federate")
    assert status == 0

    status = h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    assert status == 0

    status = h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    assert status == 0

    status = h.helicsFederateInfoSetTimeDelta(fedinfo, deltat)
    assert status == 0

    status = h.helicsFederateInfoSetLoggingLevel(fedinfo, 1)
    assert status == 0

    fed = h.helicsCreateValueFederate(fedinfo)

    return fed

def destroy_federate(fed, broker=None):
    status = h.helicsFederateFinalize(fed)

    status, state = h.helicsFederateGetState(fed)
    assert state == 3

    if broker:
		while (h.helicsBrokerIsConnected(broker)):
			time.sleep(1)

    h.helicsFederateFree(fed)

    h.helicsCloseLibrary()

def load_config(file_path):
	with open(file_path) as data_file:
		data = json.load(data_file)
	return data
	
# This should be the install directory of PSLF
pslf_directory = os.environ['USERPROFILE'] + r"\Documents\GE_PSLF"
print("pslf directory", pslf_directory)
#Start engine
start_return_code = pslf.core.start_pslf(pslf_directory)
print("Engine Start Code: {}".format(start_return_code))

curr_dir = os.getcwd()

config_file = curr_dir + r"\pslf_helics_config.json"
data = load_config(config_file)
fed_address = None
broker_address = None
try:
	fed_address = data['federate_address']
	broker_address = data['broker_address']
except KeyError:
	print("Broker and federate address not available in config_file")
	sys.exit()
	
# redirect all output to a file, you can uncomment the following two lines to redirect all the output message to a log file
#print ('current dir: ' + curr_dir)
#pslf.core.redirect_output(curr_dir + '\\700bus_log.txt')

# open save case of power flow in pslf format

case = curr_dir + r"\700bus.sav"
print ('open case: ' + case)
open_case_return_code = pslf.core.load_case(case)
print("Open Save Case Code: {}".format(open_case_return_code))

#Register the helics here. This example will publish bus voltage (complex type) at bus 225 in PSLF to gridlabd, 
#and get the total load from gridlabd, modify the total load (complex value) to the load at bus 225 in PSLF.
#NOTE that currently PSLF does not support any optimal power flow staff, so we could not publish the price from PSLF to gridlabd

fed_address = "tcp://130.20.153.157"
broker_address = "tcp://130.20.24.180"
initstring = "--federates=1 --broker_address={broker_address} --interface={fed_address}".format(broker_address=broker_address, fed_address=fed_address)
fed = create_federate(deltat=1.0, fedinitstring=initstring)
pubid = h.helicsFederateRegisterGlobalTypePublication (fed, "TransmissionSim/B2Voltage", h.HELICS_DATA_TYPE_COMPLEX, "")
subid = h.helicsFederateRegisterSubscription (fed, "DistributionSim_B2_G_1/totalLoad", "complex", "")
h.helicsSubscriptionSetDefaultComplex(subid, 1.00, 0.0)
h.helicsFederateEnterExecutionMode(fed)

#NOTE that currently PSLF does not support any optimal power flow staff, so we could not publish the price from PSLF to gridlabd
#so we do not need to register the endpoint (epid = h.helicsFederateRegisterEndpoint(fed, "ep1", None))

hours = 1
seconds = int(60 * 60 * hours)
grantedtime = -1
print(seconds)
for itimestep in range(0, seconds, 60 * 5):
#for itimestep in range(0, seconds):
	
	#solve power flow in pslf
	print("\nSolving case!\n")
	pslf.core.solve_case_default_parameters()
	
	time.sleep(2)
	
	#get the specified bus voltage
	ibusno = 225 #specify the bus to communicate with gridlabd is bus 225
	print("\nFinding bus number 225!")
	targetbus = pslf.queries.find_bus_by_number(ibusno)
	print(targetbus)
	busvolt_mag = targetbus._volt.vm #get bus voltage magnitude, unit per unit value, need to multiply by 132790.562 when passing to gridlabd
	busvolt_ang = targetbus._volt.va #get bus voltage angle, unit rads.
	
	busvolt_real = busvolt_mag*132790.562*math.cos(busvolt_ang*180/math.pi) #covert the voltage in complex format - real part
	busvolt_imag = busvolt_mag*132790.562*math.sin(busvolt_ang*180/math.pi) #covert the voltage in complex format - imag part
	print('bus 225 voltage magnitude: ' + str(busvolt_mag) + ' V , angle: ' + str(busvolt_ang) + ' degree')
	
	#The busvolt is the value that need to be published to the gridlabd
	
	status = h.helicsPublicationPublishComplex(pubid, busvolt_real, busvolt_imag)
	
	
	while grantedtime < itimestep:
		status, grantedtime = h.helicsFederateRequestTime (fed, itimestep)
	status, grantedtime = h.helicsFederateRequestTime (fed, itimestep)
	print ('grantedtime from HELICS is: ' + str(grantedtime))  #renke add.
	time.sleep(1)
	#The following code subscribes total load values from gridlabd, and write this load value to the load at bus 225
	status, rValue, iValue = h.helicsSubscriptionGetComplex(subid)
	
	#logger.info("Python Federate grantedtime = {}".format(grantedtime))
	#logger.info("Load value = {} MW".format(complex(rValue, iValue)/1000))
    #modify the load at bus8:
	loadscalor = 8000
	loadp = rValue/loadscalor  # I am not sure about what the scale should be, if the rValue are at the level of 1.23E+06 to 8E+06
								# the scale should be 8000, if the rValue are at the level of 1.23E+03 to 8E+03, the scale should be 8
	loadq = iValue/loadscalor  # scale same as the rValue 


	print("\nFinding the load at bus number 225 with id 99 !")
	targetload = pslf.queries.find_load_by_bus_and_id(targetbus, '99') 
	print(targetload)

	targetload.p = loadp  # modify the load value, real part in PSLF with loadp
	targetload.q = loadq  # modify the load value, iamg part in PSLF with loadp

	targetload.save()  # save the modified load value in PSLF

	#solve power flow again
	print("\nSolving case again!\n")
	pslf.core.solve_case_default_parameters()

	time.sleep(2)

	print('bus 225 voltage magnitude after load modification: ' + str(targetbus._volt.vm) )
	print ('load at bus 225 p and q after load modification: ' + str(targetload.p) + ',  ' + str(targetload.q))

	#save the case in PSLF for debugging purpose
	case = curr_dir + r"\700bus_mod" +'_%d.sav'%itimestep
	pslf.core.save_case(case)	

#Let it run through the full simulation time
while grantedtime < itimestep:
    status, grantedtime = h.helicsFederateRequestTime (fed, itimestep)
#logger.info("Destroying federate")
destroy_federate(fed)

	
print ('finished simulation!')