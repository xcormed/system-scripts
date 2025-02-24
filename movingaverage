from collections import deque

class MovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = deque(maxlen=window_size)  # Fixed-size deque
        self.total = 0  # To keep track of the sum of elements in the window

    def add(self, value):
        if len(self.window) == self.window_size:  # If the window is full
            self.total -= self.window[0]  # Subtract the value that will be removed
        self.window.append(value)  # Add the new value to the window
        self.total += value  # Update the total with the new value
        return self.total / len(self.window)  # Return the current average
