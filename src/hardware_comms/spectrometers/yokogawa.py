# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 07:26:32 2017

"""

# %% Modules ------------------------------------------------------------------

import time

#3rd party imports
import numpy as np
import pyvisa
from ..devices import PyvisaDevice

#Astrocomb imports
from .spectrometer import Spectrometer

# %% OSA ----------------------------------------------------------------------
class YokogawaOSA(PyvisaDevice):
    """Holds Yokogawa OSA's attributes and method library."""
#General Methods
    def __init__(self, resource_address):
        PyvisaDevice.__init__(self, resource_address)
        if self.resource is None:
            print('Could not create OSA instrument!')
        self.__set_command_format()
        self.set_maps()
    
    # @vo._auto_connect
    def reset(self):
        """Stops current machine operation and returns OSA to default values"""
        self.write('*RST')
        self.__set_command_format()

    def set_maps(self):
        self.trace_status_map = {0:"WRITE", 1:"FIX", 2:"MAX HOLD", 3:"MIN HOLD", 4:"ROLL AVG", 5:"CALC"}
        self.sens_map = {0:'NHLD', 1:'NAUT', 2:'MID', 3:'HIGH1', 4:'HIGH2', 5:'HIGH3', 6:'NORM'}
        self.chop_map = {0:'OFF', 2:'SWITCH'}
        self.sweep_map = {1:'SING', 2:'REP', 3:'AUTO', 4:'SEGM'}
        self.trace_map = {0:'TRA', 1:'TRB', 2:'TRC', 3:'TRD', 4:'TRE', 5:'TRF', 6:'TRG'}
        self.scale_map = {0: 'LOG', 1: 'LIN'}
        

#Query Methods
   
    def sweep_parameters(self):
        """Returns sweep parameters as a dictionary

        dictionary keys: center_wl, span_wl, res_wl, sensitivity
        wavelengths are in nm

        Sensitivites:
              0     |      1      |    2   |  3  |    4   |    5   |    6   |
        Normal Hold | Normal Auto | Normal | Mid | High 1 | High 2 | High 3 |
        """
        # Active Trace and Mode
        trace = self.query(":TRACe:ACTive?").strip()
        mode = self.query(':TRACe:ATTRibute:{:}?'.format(trace)).strip()
        mode = self.trace_status_map[int(mode)]
        avg_cnt = int(self.query(":TRACe:ATTRibute:RAVG?").strip())
        if (mode in ["WRITE", "FIX", "MAX HOLD", "MIN HOLD", "CALC"]):
            avg_cnt = 1
        t_list_keys = ["active_trace", "trace_mode", "avg_count"]
        t_list_values = [trace, mode, avg_cnt]
        trace_dict = {key:value for (key, value) in zip(t_list_keys, t_list_values)}
        # Wavelength
        start_wvl = float(self.query(":SENSe:WAVelength:STARt?").strip())*1e9
        stop_wvl = float(self.query(":SENSe:WAVelength:STOP?").strip())*1e9
        wvl_res = float(self.query(":SENSe:BANDwidth:RESolution?").strip())*1e9
        samp_cnt = int(self.query(":SENSe:SWEep:POINts?").strip())
        t_list_keys = ["start", "stop", "resolution", "points"]
        t_list_values = [start_wvl, stop_wvl, wvl_res, samp_cnt]
        wvl_dict = {key:value for (key, value) in zip(t_list_keys, t_list_values)}
        # Level
        ref_lvl = self.query(":DISPlay:WINDow:TRACe:Y1:SCALe:RLEVel?").strip()
        level_unit = self.query(":DISPlay:WINDow:TRACe:Y1:SCALe:UNIT?").strip()
        level_unit = {0:'dBm',1:'W',2:'dBm',3:'W'}[int(level_unit)]
        sens = self.query(":SENSe:SENSe?").strip()
        sens = {0:'NORMAL HOLD',1:'NORMAL AUTO',2:'MID',3:'HIGH1',4:'HIGH2',5:'HIGH3',6:'NORMAL'}[int(sens)]
        chopper = self.query(":SENSe:CHOPper?").strip()
        chopper = {0:'OFF',2:'SWITCH'}[int(chopper)]
        t_list_keys = ["ref_level", "level_unit", "sensitivity", "chopper"]
        t_list_values = [ref_lvl, level_unit, sens, chopper]
        level_dict = {key:value for (key, value) in zip(t_list_keys, t_list_values)}
        # Return Values
        t_list_keys = ['trace','wavelength','level']
        t_list_values = [trace_dict, wvl_dict, level_dict]
        return {key:value for (key, value) in zip(t_list_keys, t_list_values)}

    def spectrum(self):
        ''' 
        Records existing OSA spectrum

        returns: ndarray[x bins, intensities]
        '''
        y_trace = self.query_list(':TRAC:DATA:Y? {:}'.format(self.active_trace))
        x_trace = self.query_list(':TRAC:DATA:X? {:}'.format(self.active_trace))*1e9
        data = np.array([x_trace ,y_trace])
        return data

    def get_new_single(self):
    # Prepare OSA
        self.sweep_mode='SING'
    # Initiate Sweep
        self.initiate_sweep()
        # time.sleep(.05)
    # Wait for sweep to finish
        self.__wait_until_free()
    # Get Data
        data = self.spectrum()
        return data
    
    def initiate_sweep(self):
        self.write(':INITiate:IMMediate')
        self.__wait_until_free()
    
    def __wait_until_free(self):
        busy = True
        while busy:
            time.sleep(.05)
            try:
                busy = not(int(self.query('*OPC?').strip().split(";")[0]))
            except pyvisa.VisaIOError as visa_err:
                if (visa_err.error_code == -1073807339): #timeout error
                    pass
                else:
                    raise visa_err
        
    
#Set Methods
    # @vo._auto_connect
    @property
    def wavelength_span(self) -> tuple:
        '''
        Reads the current wavelength span in nanometers.
        
        returns: tuple of (start, end)
        '''
        start_wvl = float(self.query(":SENSe:WAVelength:STARt?").strip())*1e9
        stop_wvl = float(self.query(":SENSe:WAVelength:STOP?").strip())*1e9
        return (start_wvl, stop_wvl)

    @wavelength_span.setter
    def wavelength_span(self, range: tuple):
        '''
        Sets the wavelength span in nanometers
        
        range: tuple of (start, end)
        '''
        cmd_str = "SENSe:WAVelength:STARt {:}NM; STOP {:}NM".format(range[0],range[1])
        self.write(cmd_str)
        
    @property
    def resolution(self):
        '''
        Returns the current resolution in nanometers.
        
        2NM, 1NM, 0.5NM, 0.2NM, 0.1NM, 0.05NM, 0.02NM
        '''
        res = float(self.query(':SENSE:BANDWIDTH?').strip()) * 1e9
        return res

    @resolution.setter
    def resolution(self, set_res):
        self.write(f':SENSE:BANDWIDTH:RESOLUTION {set_res:.2f}NM')
    
    @property
    def sensitivity(self):
        '''
        set_sens={'sense':<sensitivity>, 'chop':<chopper action>}
        
        NHLD = NORMAL HOLD
        NAUT = NORMAL AUTO
        NORM = NORMAL
        MID = MID
        HIGH1 = HIGH1 
        HIGH2 = HIGH2
        HIGH3 = HIGH3
        '''

        sens = self.sens_map[int(self.query(":SENSe:SENSe?").strip())]
        # chopper = self.chop_map[int(self.query(":SENSe:CHOPper?").strip())]
        return sens

    @sensitivity.setter
    def sensitivity(self, set_sens):
        if set_sens in self.sens_map.values():
            self.write(f":SENSe:SENSe {set_sens}")
        else:
            raise ValueError(f"Unrecognized sensitivity setting {set_sens}")


    @property 
    def chopper_on(self):
        chopper = self.chop_map[int(self.query(":SENSe:CHOPper?").strip())]
    
    @chopper_on.setter
    def chopper_on(self, status):
        if status in self.chop_map.values(): 
            self.write(f":SENSe:CHOPper {status}")
        else:
            raise ValueError(f"Unrecognized chopper setting {status}")
        
  
    @property
    def sweep_mode(self):
        '''
        SINGle = SINGLE sweep mode
        REPeat = REPEAT sweep mode
        AUTO = AUTO sweep mode
        SEGMent = SEGMENT
        Response    1 = SINGle
                    2 = REPeat
                    3 = AUTO
                    4 = SEGMent
        '''
        mode = int(self.query(":INITiate:SMODe?").strip())
        return self.sweep_map[mode]

    @sweep_mode.setter
    def sweep_mode(self, set_mode):
        if set_mode in self.sweep_map.values():
            self.write(f":INITiate:SMODe {set_mode}")
            time.sleep(.05)
            self.write(':ABORt')
            time.sleep(.05)
            self.write('*WAI')
            time.sleep(.05)
            self.__wait_until_free()
        else:
            raise ValueError(f"Unrecognized sweep mode {set_mode}")

    @property
    def active_trace(self):
        return self.query(':TRACe:ACTive?').strip()

    @active_trace.setter
    def active_trace(self, set_trace):
        if set_trace in self.trace_map.values():
            self.write(f':TRACE:ACTIVE {set_trace}')
        else:
            raise ValueError(f"Unrecognized trace {set_trace}") 
            
            
    @property
    def active_trace_status(self): 
        trace = self.query(f':TRACE:ATTRIBUTE:{self.active_trace}?').strip()
        trace = self.trace_status_map[int(trace)]
        #TODO
        # if (trace == 'RAVG'):
        #     avg_cnt = int(self.query(':TRACe:ATTRibute:RAVG?').strip())
        # else:
        #     avg_cnt = 1
        return trace

    @active_trace_status.setter
    def active_trace_status(self, set_type):
        if set_type in self.trace_status_map.values():
            self.write(f':TRACe:ATTRibute:{self.active_trace} {set_type}')

            # TODO add averaging property
            # if ((set_type == 'RAVG') and ('avg' in set_type)):
                # self.write(f':TRACe:ATTRibute:RAVG {int(set_type['avg'])}')
        else:
            raise Exception(f'Unrecognized trace type {set_type}')
    
    def read_trace_status(self, trace):
        status = self.query(f':TRACE:ATTRIBUTE:{trace}?').strip()
        status = self.trace_status_map[int(status)]
        # TODO
        # if (status == 'RAVG'):
        #     avg_cnt = int(self.query(':TRACe:ATTRibute:RAVG?').strip())
        # else:
        #     avg_cnt = 1
        return status

    def set_trace_status(self, trace, status):
        if status in self.trace_status_map.values():
            self.write(f':TRACe:ATTRibute:{trace} {status}')
            # TODO add averaging property
            # if ((set_type == 'RAVG') and ('avg' in set_type)):
                # self.write(f':TRACe:ATTRibute:RAVG {int(set_type['avg'])}')
        else:
            raise Exception(f'Unrecognized trace type {status}')

    @property
    def level_scale(self):
        mode = int(self.query(':DISPlay:WINDow:TRACe:Y1:SCALe:SPACing?').strip())
        return self.scale_map[mode]

    @level_scale.setter
    def level_scale(self, set_mode):
        if set_mode in self.scale_map.values():
            self.write(f':DISPLAY:TRACE:Y1:SPACING {set_mode}')
        else:
            raise ValueError(f"Unrecognized level scale {set_mode}") 
    
    def fix_all(self):
        for trace in self.trace_map.values():
            self.set_trace_status(trace, "FIX")
    
    # @vo._auto_connect
    def __set_command_format(self):
        """Sets the OSA's formatting to AQ6370 style, should always be 1"""
        self.write('CFORM1')
