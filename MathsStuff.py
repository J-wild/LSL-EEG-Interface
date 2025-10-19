import numpy as np


class NumpyBuffer:
    def __init__(self, max_size=10000, num_channels=8):
        self.max_size = max_size
        self.num_channels = num_channels
        self.time_buffer = np.full(max_size, np.nan, dtype=np.float32)
        self.data_buffer = np.full((max_size, num_channels), np.nan, dtype=np.float32)
        self.current_idx = 0
        self.is_full = False
        
    def add_data(self, timestamps, eeg_data):
        """Add new data using numpy rolling approach"""

        timestamps = np.array(timestamps)
        eeg_data = np.array(eeg_data)  # Convert list to numpy array
        num_new_samples = len(timestamps)

        
        for i in range(num_new_samples):
            # Add to buffers
            self.time_buffer[self.current_idx] = timestamps[i]
            self.data_buffer[self.current_idx, :] = eeg_data[i, :]
            
            # Update index
            self.current_idx += 1
            if self.current_idx >= self.max_size:
                self.current_idx = 0
                self.is_full = True
                
    def get_all_data(self):
        """Get all valid data in correct order"""
        if self.is_full:
            # Buffer is full, return everything in chronological order
            time_data = np.roll(self.time_buffer, -self.current_idx)
            data = np.roll(self.data_buffer, -self.current_idx, axis=0)
        else:
            # Buffer not full, return only valid data
            time_data = self.time_buffer[:self.current_idx]
            data = self.data_buffer[:self.current_idx, :]
            
        return time_data, data
    
    def get_channel_data(self, channel_idx):
            """Direct channel access without full data copy"""

            if self.is_full:
                # Roll only the specific channel to avoid copying all channels
                time_data = np.roll(self.time_buffer, -self.current_idx)
                channel_data = np.roll(self.data_buffer[:, channel_idx], -self.current_idx)
            else:
                time_data = self.time_buffer[:self.current_idx]
                channel_data = self.data_buffer[:self.current_idx, channel_idx]
                
            return time_data, channel_data
