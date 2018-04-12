"""
===============================================================================
                        MONTE CARLO LOAD SIMULATOR
===============================================================================
                        Version 1.0 using Python 3.6   
===============================================================================
                            Most recent update:
                                12 April 2018
===============================================================================
INFORMATION

Made by:
    Philip Sandwell
Copyright:
    Philip Sandwell, 2018
For more information, please email:
    philip.sandwell@googlemail.com
    
===============================================================================
INTRODUCTION

This code uses a Monte Carlo simulation process to statistically model the load
of a system, composed of a number of devices. It relies on binomial statistics
to simulate the number of devices of each type which are on and off at a given
time (hour of the day and month of the year). This can be used, for example, to
estimate the variation in load demanded as part of a minigrid system. 

More information about this mondelling process is available here:
    P Sandwell, C Chambon, A Saraogi, A Chabenat, M Mazur, N Ekins-Daukes,
    and J Nelson, Analysis of energy access and impact of modern energy sources
    in unelectrified villages in Uttar Pradesh, Energy Sustain Dev, 35, 67-79, 
    2016. https://doi.org/10.1016/j.esd.2016.09.002

Please cite this paper as a reference when using the results of this work. 

===============================================================================
QUICKSTART GUIDE
    Get your load values as .csv outputs (kWh per hour)
        1. Update device list
        2. Update utilisation profiles
        3. Select the number of trials and percentile value
        4. Run this file
        5. Type the following into the console:
                Load_Simulator().quickstart()
        6. Wait for the simulation to complete
        7. Collect output files from "Outputs" folder     
===============================================================================
QUICKPLOT GUIDE
    Visualise the energy demand for each month (kWh per day)
        1. Use the steps in the QUICKSTART GUIDE
        2. Type the following into the console:
                Load_Simulator().quickplot()
        3. Wait for the simulation to complete
        4. Collect output files from "Outputs" folder   
===============================================================================
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class Load_Simulator():
    def __init__(self):
        self.months = ['Jan','Feb','Mar','Apr','May','Jun',
                       'Jul','Aug','Sep','Oct','Nov','Dec']
        self.load_inputs = pd.read_csv('Device list.csv' ,
                                       index_col=0).round(decimals=3)
        self.times_folder = 'Utilisation profiles/'
        self.outputs_folder = 'Outputs/'
        self.trials = 100       # for each month
        self.percentile = 90    # e.g. 90 means 90% of loads below the output value given
        
# =============================================================================
#      Make and save results automatically
# =============================================================================
    def quickstart(self):
        """
        Function: 
            Automatically generates all of the outputs as .csv files. Use this 
            to quickly get the results you  need: means, standard deviations, 
            variabilities and percentile values for each hour of each month of the year
        Inputs: 
            None
        """
        print('\nAutomatically generating results!')
        print('\nNumber of Monte Carlo trials: '+str(self.trials)+' for each month')
        print('\nGenerating values for the mean, percentage variability, standard deviation and '
              +str(self.percentile)+'th percentile of monthly system load demand.')
        self.save_results(self.make_results())
        print('\nSimulation complete!\n \nCheck the \"Outputs\" folder for your results.')
        
# =============================================================================
#      Get the utilisation profile of the device
# =============================================================================
    def get_utilisation_times(self,device):
        """
        Function:
            Finds the utilisation of a device for each hour of each month
        Inputs:
            Device
        Requires:
            "[device]_times.csv" in "Utilisation times" folder
        """
        return pd.read_csv(self.times_folder+device+'_times.csv',header=None)
    
# =============================================================================
#      Get the utilisation profile of the device for a given month
# =============================================================================
    def get_utilisation_times_month(self,device,month):
        """
        Function:
            Finds the utilisation of a device for each hour of a given month
        Inputs:
            Device, month
        """
        return pd.DataFrame(self.get_utilisation_times(device)[month].values)
    
# =============================================================================
#      Find the total number of each device owned by the community 
# =============================================================================
    def get_number_of_devices(self,device):
        """
        Function:
            Finds the number of a given device type in the community
        Inputs:
            Device
        Requires:
            "Device list.csv" in folder
        """
        device_info = self.load_inputs.loc[device]
        if device_info['Available']=='Y':
            ownership = device_info['Number']
        elif device_info['Available']=='N':
            ownership = 0
        return ownership  

# =============================================================================
#      Get a randomised device load
# =============================================================================
    def device_load_profile_month_random(self,device,month):
        """
        Function:
            Finds the load (kW) of a given device for each hour of a given month
        Inputs:
            Device, month
        Requires:
            "Device list.csv" in folder            
        """
        devices = self.get_number_of_devices(device)
        utilisation_profile = self.get_utilisation_times_month(device,month)
        devices_on = pd.DataFrame(np.random.binomial(devices, utilisation_profile))
        device_load = self.load_inputs.loc[device]['Power (W)']
        return devices_on * device_load * 0.001 # convert to kW for compatibility with HOMER

# =============================================================================
#      Get a randomised system load
# =============================================================================
    def system_load_month_random(self,month):
        """
        Function:
            Find the load (kW) for the entire system, a single trial of the 
            Monte Carlo simulation
        Inputs:
            Month
        """
        device_list = self.load_inputs.index
        system_load = pd.DataFrame([0.0])
        for device in device_list:
            system_load =  pd.DataFrame(
                    system_load.values + self.device_load_profile_month_random(device,month))
        return system_load
    
# =============================================================================
#      Get a random system load, for as many trials as you have specified
# =============================================================================
    def system_load_month_monte_carlo(self,month):
        """
        Function:
            Performs a Monte Carlo simulation of many trials for the given month
        Inputs:
            Month
        """
        output = pd.DataFrame([])
        for t in range(self.trials):
            system_load = self.system_load_month_random(month)
            output = pd.concat([output, system_load],axis=1)
        return output
    
# =============================================================================
#      Find percentile value of system load
# =============================================================================
    def get_hourly_percentile_value(self,monte_carlo_month_results):
        '''
        Function:
            Finds the load value (kW) at the specified percentile 
        Inputs:
            Results of the Monte Carlo simulation (all trials)
        '''
        hourly_values = []
        for hour in range(24):
            hourly_values.append(np.percentile(
                    monte_carlo_month_results.iloc[hour],self.percentile))
        return pd.DataFrame(hourly_values)
    
# =============================================================================
#      Find mean value, standard deviation, variability and percentile value of system load
# =============================================================================
    def make_results(self):
        '''
        Function:
            Perform the Monte Carlo simulation automatically and output the 
            results (mean, standard deviation, variability and percentile values)
            for each hour of each month of the year
        Inputs:
            None
        '''
        means = pd.DataFrame([])
        std_devs = pd.DataFrame([])
        percentage_variability = pd.DataFrame([])
        percentiles = pd.DataFrame([])
        for month in range(12):
#   Generate results for this month
            monte_carlo_results_month = self.system_load_month_monte_carlo(month)
#   Find results for this month
            monthly_means = pd.DataFrame(monte_carlo_results_month.mean(axis=1))
            monthly_std_devs = pd.DataFrame(monte_carlo_results_month.std(axis=1))
            monthly_percentage_variability = pd.DataFrame(
                    monthly_std_devs.values / monthly_means.values)
            monthly_percentiles = self.get_hourly_percentile_value(monte_carlo_results_month)
#   Title columns with months
            monthly_means.columns = [self.months[month]]
            monthly_std_devs.columns = [self.months[month]]
            monthly_percentage_variability.columns = [self.months[month]]
            monthly_percentiles.columns = [self.months[month]]
#   Add to the outputs            
            means = pd.concat([means,monthly_means],axis=1)
            std_devs = pd.concat([std_devs,monthly_std_devs],axis=1)
            percentage_variability = pd.concat(
                    [percentage_variability,monthly_percentage_variability],axis=1)
            percentiles = pd.concat([percentiles,monthly_percentiles],axis=1)
#   Return outputs 
        return means,std_devs,percentage_variability,percentiles       
        
# =============================================================================
#      Save mean value, standard deviations and percentile value of system load
# =============================================================================
    def save_results(self,results_dataframe):
        '''
        Function:
            Save the results of Load_Simulator().make_results() to appropriately
            named .csv files in the "Outputs" folder
        Inputs:
            Dataframes of mean, standard deviation, variability and percentile 
            values for each hour of each month of the year
        '''
        means,std_devs,percentage_variability,percentiles = results_dataframe
        file_suffix = '_system_load_values.csv'
        means.round(decimals=3).to_csv(self.outputs_folder+'mean'+file_suffix)
        std_devs.round(decimals=3).to_csv(self.outputs_folder
                      +'standard_deviation'+file_suffix)
        percentage_variability.round(decimals=3).to_csv(self.outputs_folder
                                    +'percentage_variability'+file_suffix)        
        percentiles.round(decimals=3).to_csv(self.outputs_folder
                         +str(self.percentile)+'_percentile'+file_suffix)

# =============================================================================
#      Monte Carlo simulation, with the output dataframe transposed
# =============================================================================
    def system_load_month_monte_carlo_transposed(self,month):
        """
        Function:
            Performs the Monte Carlo simulation for a given month but also 
            assigns the month and daily sum of energy to the trial
        Inputs:
            Month
        """
        output = pd.DataFrame([])
        for t in range(self.trials):
            system_load = pd.DataFrame(self.system_load_month_random(month).values.transpose())
            output = pd.concat([output, system_load],axis=0)
        output = output.reset_index(drop=True)
        output['Daily sum (kWh)'] = output.sum(axis=1)
        output['Month'] = self.months[month]
        return output
# =============================================================================
#      Visualise the cumulative energy demand per day for each month
# ============================================================================= 
    def quickplot(self):
        """
        Function:
            Automatically creates a boxplot of the daily energy demand of the 
            system for each month of the year
        Inputs:
            None
        """
        print('\nAutomatically generating results!')
        print('\nNumber of Monte Carlo trials: '+str(self.trials)+' for each month')
        print('\nGenerating values of system load demand.')        
        output = pd.DataFrame([])
        for month in range(12):
            monthly_output = self.system_load_month_monte_carlo_transposed(month)
            output = pd.concat([output,monthly_output],axis=0)
        output = output.reset_index(drop=True)
        sns.boxplot(data=output,
                    x =output['Month'],y=output['Daily sum (kWh)'])
        plt.ylabel('Total system energy demand (kWh per day)')
        plt.savefig(self.outputs_folder+'Total system energy demand (kWh per day).png',
                    bbox_inches='tight',dpi=600)
        print('\nSimulation complete!\n \nCheck the \"Outputs\" folder for your graph.')

# =============================================================================
#      Detailed output of device loads, times, months, trial etc.
# =============================================================================
    def detailed_output(self):
        '''
        Function:
            Gives a detailed breakdown of the load value for each device,
            hour, month and simulation trial for further analysis using (for 
            example) .groupby functions. Manually save as a variable.
        Inputs:
            None
        Requires:
            "[device]_times.csv" in "Utilisation times" folder
            "Device list.csv" in folder
        '''
#   Initialises variables for outputs 
        output_trial = []
        output_device = []
        output_month = []
        output_hour = []
        output_device_load = []
        output_device_type = []
        device_list = self.load_inputs.index
#   Monte Carlo simulation, iterating over all variables
        print('\nAutomatically generating results!')
        print('\nNumber of Monte Carlo trials: '+str(self.trials)+' for each month')
        print('\nGenerating values of load demand for each device, month and hour.')  
        for trial in range(int(self.trials)):
            for device in device_list:
                device_power = self.load_inputs.loc[device]['Power (W)']
                device_type = self.load_inputs.loc[device]['Type']
                number_of_devices = self.get_number_of_devices(device)
                for month in range(12):
                    utilisation_profile = self.get_utilisation_times_month(device,month)
                    for hour in range(24):
                        devices_on = np.random.binomial(
                        number_of_devices, utilisation_profile.iloc[hour][0])
                        device_load = devices_on * device_power * 0.01
                        output_trial.append(trial)
                        output_device.append(device)
                        output_month.append(self.months[month])
                        output_hour.append(hour)
                        output_device_load.append(device_load)
                        output_device_type.append(device_type)
#   Put the outputs in the correct format
        output_trial = pd.DataFrame(output_trial)
        output_trial.columns = ['Trial']
        output_device = pd.DataFrame(output_device)
        output_device.columns = ['Device']
        output_month = pd.DataFrame(output_month)
        output_month.columns = ['Month']
        output_hour = pd.DataFrame(output_hour)
        output_hour.columns = ['Hour']
        output_device_load = pd.DataFrame(output_device_load)
        output_device_load.columns= ['Load (kWh)']
        output_device_type = pd.DataFrame(output_device_type)
        output_device_type.columns = ['Type']
        print('\nSimulation complete!\n')
#   Returns outputs
        return pd.concat([output_trial,output_device,output_month,
                          output_hour,output_device_load,output_device_type],axis=1)
