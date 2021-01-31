import numpy as np
import matplotlib.container
import matplotlib.collections


class Element:
    """Base class for an Element, which provides a standard interface for setting properties of various artist types."""
    def __init__(self, artist, horizontal=False):
        self.artist = artist
        self.horizontal=horizontal

    def get_alpha(self):
        """Get the transparency value of the artist."""
        return self.artist.get_alpha()

    def set_alpha(self, alpha):
        """Set the transparency value of the artist."""
        self.artist.set_alpha(alpha)

    def get_data(self):
        """Get the data value of the artist."""
        raise NotImplementedError("Method not implemented by child class.")

    def set_data(self, data):
        """Set the data value of the artist."""
        raise NotImplementedError("Method not implemented by child class.")

    def get_scale(self):
        """Get the scale of the artist about its center."""
        raise NotImplementedError("Method not implemented by child class.")

    def set_scale(self, scale):
        """Scale the artist about its center."""
        raise NotImplementedError("Method not implemented by child class.")


class BarElement(Element):
    def __init__(self, bar, horizontal=False):
        super().__init__(bar, horizontal)
        self._ref_w = bar.get_width()
        self._ref_h = bar.get_height()
        self._centroid = bar.get_xy() + 0.5 * np.array([self._ref_w, self._ref_h])
        self._scale = 1

    def get_data(self):
        return self.artist.get_width() if self.horizontal else self.artist.get_height()

    def set_data(self, data):
        if self.horizontal:
            self.artist.set_width(data)
        else:
            self.artist.set_height(data)

    def set_scale(self, scale):
        cx, cy = self._centroid
        x = cx - scale * self._ref_w / 2
        y = cy - scale * self._ref_h / 2
        self.artist.set_xy((x, y))
        self.artist.set_width(scale * self._ref_w)
        self.artist.set_height(scale * self._ref_h)
        self._scale = scale

    def get_scale(self):
        return self._scale


class DummyElement(Element):
    def __init__(self, *args, **kwargs):
        super().__init__(None)
        self._alpha = None
        self._data = None
        self._scale = None

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, alpha):
        self._alpha = alpha

    def get_data(self):
        return self._data

    def set_data(self, data):
        self._data = data

    def get_scale(self):
        return self._scale

    def set_scale(self, scale):
        self._scale = scale


class ElementSeries(list):
    def __init__(self, artist_collection, horizontal=False):
        self.horizontal = horizontal
        self._artist_collection = artist_collection
        self._type = type(artist_collection)
        if self._type == matplotlib.container.BarContainer:
            elements = [BarElement(bar, horizontal) for bar in artist_collection]
            self.artists = artist_collection
        elif self._type == matplotlib.collections.PathCollection:
            data = artist_collection.get_offsets()
            elements = [DummyElement() for _ in range(len(data))]
            for i, el in enumerate(elements):
                el.set_data(data[i])
            self.artists = [artist_collection]
        else:
            raise NotImplementedError("Unsupported artist collection type.")
        super().__init__(elements)

    def _set_attribute(self, attribute, value):
        if type(value) in [int, float]:
            value = [value for _ in self]
        elif len(value) != len(self):
            raise ValueError("Length of input values does not match length of ElementSeries.")
        for i, v in enumerate(value):
            getattr(self[i], "set_"+attribute)(v)


    def get_alpha(self):
        return [e.get_alpha() for e in self]

    def set_alpha(self, alpha):
        self._set_attribute("alpha", alpha)

    def get_data(self):
        return [e.get_data() for e in self]

    def set_data(self, data):
        self._set_attribute("data", data)
        if self._type == matplotlib.collections.PathCollection:
            self._artist_collection.set_offsets([el.get_data() for el in self])

    def get_scale(self):
        return [e.get_scale() for e in self]

    def set_scale(self, scale):
        self._set_attribute("scale", scale)



