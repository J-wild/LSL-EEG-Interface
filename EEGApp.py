
import dearpygui.dearpygui as dpg
import threading
import pylsl
import numpy as np
from MathsStuff import NumpyBuffer

class EEG_Application:
    def __init__(self):
      self.UPT = threading.Thread(target = self.update_eeg_plots, name = "UPT", daemon=True)
      self.stream = stream()
      
      self.setup_ui()
      


    def setup_ui(self):
        
        dpg.create_context()
        dpg.create_viewport(title='GraphEEG', width=600, height=400)
        with dpg.window(label="Control Pannel", tag="Main", min_size=(200,200)):
           
            dpg.add_button(label="Scan Streams", callback= self.start_streams) # button to Scan for streams
            dpg.add_slider_int(label = "Polling Rate Hz", width= 400, callback=self.change_polling_rate, default_value= 10,  min_value= 1, max_value= 100, tag = "polling_slider")
        
        dpg.add_window(label= "EEG Data", tag = "data_window", show = False, autosize= False, width= 800, pos=(200, 0))
        dpg.setup_dearpygui()
        dpg.show_viewport()
    
    def change_polling_rate(self):
        prate = dpg.get_value("polling_slider")
        print(prate)
        self.stream.set_poll_rate(prate)

    def start_streams(self):
        
        self.stream.scan_streams()
        if self.stream.streaming:
            self.create_eeg_plots()
            self.UPT.start()

    def create_eeg_plots(self):

        inf = self.stream.inlet.info() 
        channel_count = inf.channel_count()

        dpg.show_item("data_window")
        
        # Store references to buffers for each channel
        
        self.plot_tags = []
        self.series_tags = []

        with dpg.plot(
            label=f"SinglePlot",
            height=500,
            width=-1,
            tag="SinglePlot",
            parent="data_window"

            ):
              
              
                x_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, 
                    label="Time (s)", 
                    auto_fit= True
                )
                
                # Create Y-axis (amplitude)
                y_axis = dpg.add_plot_axis(
                        dpg.mvYAxis, 
                        label="Amplitude (µV)", 
                        auto_fit= True

                    )
                for i in range(channel_count):
                      series = dpg.add_line_series(
                    [],      # Start with empty X data
                    [],      # Start with empty Y data
                    parent=y_axis,
                    tag= f"singleplot_series_{i}"
                )
                    



        for i in range(channel_count):
            # Create unique tags for each channel
            plot_tag = f"plot_channel_{i}"
            x_axis_tag = f"x_axis_{i}"
            y_axis_tag = f"y_axis_{i}"
            series_tag = f"series_{i}"
            
            # Store the tags for later use
            self.plot_tags.append(plot_tag)
            self.series_tags.append(series_tag)
            
            # Initialize buffers for this channel
            
            with dpg.plot(
                label=f"EEG Channel {i+1}",
                height=150,
                width=-1,
                tag=plot_tag,
                parent="data_window"
                
            ):
                # Create X-axis (time)
                x_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, 
                    label="Time (s)", 
                    tag= x_axis_tag,
                    auto_fit= True
                )
                
                # Create Y-axis (amplitude)
                y_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, 
                    label="Amplitude (µV)", 
                    tag=y_axis_tag,
                    auto_fit= True

                )
                
                # Create the line series for this channel with empty data
                series = dpg.add_line_series(
                    [],      # Start with empty X data
                    [],      # Start with empty Y data
                    parent=y_axis,
                    tag=series_tag
                )
        


            
            
      
    def update_eeg_plots(self):
        while self.stream.streaming:
            

           
            inf = self.stream.inlet.info() 
            channel_count = inf.channel_count()

            for i in range(channel_count):
            
                time_buffer , channel_A_buffer = self.stream.get_buffer(i)
                time_buffer = np.ascontiguousarray(time_buffer)
                channel_A_buffer = np.ascontiguousarray(channel_A_buffer)
                dpg.set_value(f'series_{i}', [time_buffer, channel_A_buffer])
                dpg.set_value(f'singleplot_series_{i}', [time_buffer, channel_A_buffer])
                

        
        #print(len(channel_A_buffer))
        

    def run(self):
        
        
        #secondary main loop for inputs
        while dpg.is_dearpygui_running():

            

            dpg.render_dearpygui_frame()
        
        
        self.stream.stop_stream()
        self.UPT.join()
        dpg.destroy_context()
    
class stream:
    def __init__(self):

        self.DAT = threading.Thread(target = self.data_acquisition_loop, name = "DAT")
        self.inlet = None
        self.streaming = False
        self.EEGBuffer = NumpyBuffer()
        self.data_poll_rate = 100
        
    def set_poll_rate(self, rate):
        self.data_poll_rate = rate

    def get_buffer(self, channel_num):
        
        return self.EEGBuffer.get_channel_data(channel_num)
    
    def scan_streams(self):
    
        streams = pylsl.resolve_streams(wait_time=1)
        if not streams:
            print(f"No EEG streams found. Please connect the headset through the NIC software and ensure the Data streaming through LSL is selected")
            return
        

        for i, stream in enumerate(streams):
            
            inlet = pylsl.StreamInlet(stream)
            inf = inlet.info()
            inlet.close_stream()
            print("Found stream '%s' of type '%s'" % (inf.name(), inf.type()))
            print("  with %d channels at %.2f Hz" % (inf.channel_count(),inf.nominal_srate()))
            print("---------------------------------")

        for i, stream in enumerate(streams):
            inlet = pylsl.StreamInlet(stream)
            inf = inlet.info()
            inlet.close_stream()

            if inf.nominal_srate() >= 100 :
                self.start_stream(stream)
                
    def start_stream(self, stream):

        self.inlet = pylsl.StreamInlet(stream)
        inf = self.inlet.info()
        
        self.streaming = True
        print("Using stream '%s' of type '%s' at '%.2f'Hz" % (inf.name(), inf.type(), inf.nominal_srate()))
        
        self.initialize_buffers()

        self.DAT.start()
    
    def stop_stream(self):
        
        self.streaming = False
        self.DAT.join()
        
    def initialize_buffers(self):

       print("buffer initialized")

    def data_acquisition_loop(self):
        """Background thread for acquiring EEG data"""
        print("Starting EEG data acquisition...")
        
        while self.streaming:
            chunk, timestamps = self.inlet.pull_chunk(1/self.data_poll_rate)

            self.time_buffer = np.array(timestamps)
            
            if timestamps:
                #print("new chunk\n")
                
                #print(np_chunk.T)
                    #self.channel_buffers[i].putInBuf(chunk[i])
                self.EEGBuffer.add_data(timestamps, chunk)
                

app = EEG_Application()
app.run()











