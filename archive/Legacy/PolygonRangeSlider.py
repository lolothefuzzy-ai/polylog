#!/usr/bin/env python3
"""Interactive range slider for polygon parameters."""

class PolygonRangeSlider:
    def __init__(self, min_value=0, max_value=100):
        self.min_value = min_value
        self.max_value = max_value
        
    def get_range(self):
        return (self.min_value, self.max_value)
