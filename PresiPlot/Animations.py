import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import easing_functions as ef
from PresiPlot.Elements import ElementSeries
import itertools


class Stagger:
    def __init__(self, start_time, interval):
        self._times = itertools.count(start_time, interval)

    def __iter__(self):
        return self._times


class Animation:
    def __init__(self, element, start, duration, start_value, end_value, easer=None, initialize=True):
        self.element = element
        self.start_time = start
        self.duration = duration
        self.end_time = start + duration
        self.start_value = start_value
        self.end_value = end_value
        self.easer = easer if easer is not None else ef.LinearInOut()
        if initialize:
            self.initialize()

    def initialize(self):
        raise NotImplementedError("Animation subclass must implement initialize() method.")

    def _get_value_at_time(self, t):
        alpha = self.easer((t - self.start_time) / self.duration)
        return self.start_value + alpha * (self.end_value - self.start_value)

    def tick(self, t):
        raise NotImplementedError("Animation subclass must implement tick() method.")


class DataAnimation(Animation):
    def initialize(self):
        self.element.set_data(self.start_value)

    def tick(self, t):
        if self.start_time < t <= self.end_time:
            self.element.set_data(self._get_value_at_time(t))


class Grow(DataAnimation):
    def __init__(self, element, start, duration, start_value=0, end_value=None, easer=None, initialize=True):
        end_value = element.get_data() if end_value is None else end_value
        super().__init__(element, start, duration, start_value, end_value, easer, initialize)


class SeriesAnimation:
    def __init__(self, artists, start_time, duration, easer, animation_class, horizontal=False, **kwargs):
        self.elements = ElementSeries(artists, horizontal=horizontal)
        self._artists = self.elements.artists
        if type(duration) in [int, float]:
            duration = [duration for _ in self.elements]
        if type(start_time) in [int, float]:
            start_time = [start_time for _ in self.elements]
        if type(easer) not in [list, tuple]:
            easer = [easer for _ in self.elements]
        self.animations = [animation_class(element=el, start=st, duration=d, easer=ea, **kwargs) for
                           el, st, d, ea in zip(self.elements, start_time, duration, easer)]

    def tick(self, t):
        for anim in self.animations:
            anim.tick(t)
        self.elements.update()
        return self._artists


if __name__ == "__main__":
    bars = plt.bar([1, 2, 3, 4], [3, 2, 5, 8])
    bar_anim = SeriesAnimation(bars, Stagger(0, 20), 100, ef.ElasticEaseOut(), Grow)
    a = FuncAnimation(plt.gcf(), bar_anim.tick, frames=500, interval=20, blit=True, repeat=False)
    plt.show()

    pts = plt.scatter([1, 2, 3, 4], [3, 2, 5, 8], s=20)
    scatter_anim = SeriesAnimation(pts, Stagger(0, 20), 100, ef.ElasticEaseOut(), Grow)
    a = FuncAnimation(plt.gcf(), scatter_anim.tick, frames=500, interval=20, blit=True, repeat=False)
    plt.show()
