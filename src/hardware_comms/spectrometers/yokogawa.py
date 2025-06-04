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
# import VISAObjects as vo
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
   
    # @vo._auto_connect
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

    # @vo._auto_connect
    def spectrum(self, active_trace=None):
        ''' 
        Records existing OSA spectrum

        returns: ndarray[x bins, intensities]
        '''
        if (active_trace!=None):
            self.active_trace=active_trace
        y_trace = self.query_list(':TRAC:DATA:Y? {:}'.format(self.active_trace))
        x_trace = self.query_list(':TRAC:DATA:X? {:}'.format(self.active_trace))
        x_trace = (np.array(x_trace)*1e9).tolist()
        data = np.array([x_trace ,y_trace])
        return data

    # @vo._auto_connect
    def get_new_single(self, active_trace=None, get_parameters=False):
    # Active Trace
        if (active_trace!=None):
            self.active_trace(set_trace=active_trace)
    # Prepare OSA
        if (self.sweep_mode() != 'SING'):
            self.sweep_mode('SING')
        time.sleep(.05)
        self.write(':ABORt')
        time.sleep(.05)
        self.write('*WAI')
        time.sleep(.05)
        wait_for_setup = True
        while wait_for_setup:
            time.sleep(.05)
            try:
                wait_for_setup = not(int(self.query('*OPC?').strip()))
            except pyvisa.VisaIOError as visa_err:
                if (visa_err.error_code == -1073807339): #timeout error
                    pass
                else:
                    raise visa_err
    # Initiate Sweep
        self.write(':INITiate:IMMediate')
        time.sleep(.05)
    # Wait for sweep to finish
        wait_for_sweep = True
        while wait_for_sweep:
            time.sleep(.05)
            try:
                wait_for_sweep = not(int(self.query('*OPC?').strip()))
            except pyvisa.VisaIOError as visa_err:
                if (visa_err.error_code == -1073807339): #timeout error
                    pass
                else:
                    raise visa_err
    # Get Data
        data = self.spectrum()
        return data
#    # Get Parameters
#        if (get_parameters == True):
#            params = self.sweep_parameters()
#        else:
#            params = {}
#    # Return
#        return {'data':data, 'params':params}
    
    def initiate_sweep(self):
        self.write(':INITiate:IMMediate')
    
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
        chopper = self.chop_map[int(self.query(":SENSe:CHOPper?").strip())]
        return {'sense': sens, 'chop': chopper}

    @sensitivity.setter
    def sensitivity(self, set_sens):
        if set_sens['sense'] in self.sens_map.values():
            self.write(f":SENSe:SENSe {set_sens['sense']}")
        else:
            raise ValueError(f"Unrecognized sensitivity setting {set_sens['sense']}")

        if set_sens['chop'] in self.chop_map.values(): 
            self.write(f":SENSe:CHOPper {set_sens['chop']}")
        else:
            raise ValueError(f"Unrecognized chopper setting {set_sens['chop']}")

  
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
            
    def set_trace_status(self, set_type, active_trace=None):
        if (active_trace is not None):
            self.active_trace = active_trace

        if set_type['mode'] in self.trace_status_map.values():
            self.write(f':TRACe:ATTRibute:{self.active_trace} {set_type['mode']}')

            if ((set_type['mode'] == 'RAVG') and ('avg' in set_type)):
                self.write(f':TRACe:ATTRibute:RAVG {int(set_type['avg'])}')
        else:
            raise Exception('Unrecognized trace type {:}'.format(set_type))
            
    def read_trace_status(self, active_trace=None):
        if (active_trace is not None):
            self.active_trace = active_trace

        trace = self.query(f':TRACE:ATTRIBUTE:{self.active_trace}?').strip()
        trace = self.trace_status_map[int(trace)]
        if (trace == 'RAVG'):
            avg_cnt = int(self.query(':TRACe:ATTRibute:RAVG?').strip())
        else:
            avg_cnt = 1
        return {'mode':trace, 'avg':avg_cnt}
    

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
    
    # def fix_all(self, fix=None):
    #     if (fix == None):
    #         fixed = True
    #         for trace in ['TRA', 'TRB', 'TRC', 'TRD', 'TRE', 'TRF', 'TRG']:
    #             trace_type = self.trace_type(active_trace=trace)
    #             fixed *= (trace_type['mode'] == 'FIX')
    #         return bool(fixed)
    #     elif (fix == True):
    #         for trace in ['TRA', 'TRB', 'TRC', 'TRD', 'TRE', 'TRF', 'TRG']:
    #             self.trace_type(set_type={'mode':'FIX'}, active_trace=trace)
    
    # @vo._auto_connect
    def __set_command_format(self):
        """Sets the OSA's formatting to AQ6370 style, should always be 1"""
        self.write('CFORM1')
