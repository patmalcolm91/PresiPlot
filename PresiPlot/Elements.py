import numpy as np
import matplotlib.container
import matplotlib.collections
import matplotlib.lines
from matplotlib.colors import to_rgba
import warnings


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
        if 0 <= alpha <= 1:
            self.artist.set_alpha(alpha)
        else:
            warnings.warn("Clipping out-of-range alpha value.")
            self.artist.set_alpha(max(0, min(1, alpha)))

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
        super().__init__(None, *args, **kwargs)
        self._alpha = None
        self._data = None
        self._scale = None
        self._ref_sizes = None

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

    def set_reference_sizes(self, *sizes):
        self._ref_sizes = sizes

    def get_reference_sizes(self):
        return self._ref_sizes


class DummyElement1D(DummyElement):
    def __init__(self, horizontal=False):
        super().__init__(horizontal=horizontal)

    def set_full_data(self, data):
        self._data = data

    def set_data(self, data):
        idx = 0 if self.horizontal else 1
        self._data[idx] = data

    def get_full_data(self):
        return self._data

    def get_data(self):
        idx = 0 if self.horizontal else 1
        return self._data[idx]


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
            sizes = artist_collection.get_sizes()
            alphas = artist_collection.get_alpha()
            if len(sizes) == 1:
                sizes = np.repeat(sizes[0], len(data))
            if alphas is None:
                alphas = np.repeat(1, len(data))
            elements = [DummyElement1D(horizontal) for _ in range(len(data))]
            for i, el in enumerate(elements):
                el.set_full_data(data[i])
                el.set_scale(sizes[i])
                el.set_alpha(alphas[i])
            self.artists = [artist_collection]
        elif self._type == matplotlib.lines.Line2D:
            data = list(zip(*artist_collection.get_data()))
            alpha = artist_collection.get_alpha()
            ms = artist_collection.get_markersize()
            lw = artist_collection.get_linewidth()
            if alpha is None:
                alpha = 1
            elements = [DummyElement1D(horizontal) for _ in range(len(data))]
            for d, el in zip(data, elements):
                el.set_full_data(list(d))
                el.set_alpha(alpha)
                el.set_scale(1)
                el.set_reference_sizes(ms, lw)
            self.artists = [artist_collection]
        else:
            raise NotImplementedError("Unsupported artist collection type.")
        super().__init__(elements)

    def update(self):
        if self._type == matplotlib.collections.PathCollection:
            self._artist_collection.set_offsets([el.get_full_data() for el in self])
            self._artist_collection.set_sizes([el.get_scale() for el in self])
            colors = self._artist_collection.get_facecolor()
            if len(colors) == 1:
                colors = [colors[0] for _ in self]
            new_colors = [to_rgba(c, max(0, min(1, el.get_alpha()))) for el, c in zip(self, colors)]
            self._artist_collection.set_color(new_colors)
        elif self._type == matplotlib.lines.Line2D:
            data = zip(*[el.get_full_data() for el in self])
            self._artist_collection.set_data(*data)
            alphas = set([el.get_alpha() for el in self])
            if len(alphas) != 1:
                warnings.warn("Staggered alpha animation not supported by Line2D artist type.")
            self._artist_collection.set_alpha(next(iter(alphas)))
            scales = set([el.get_scale() for el in self])
            if len(scales) != 1:
                warnings.warn("Staggered scale animation not supported by Line2D artist type.")
            scale = next(iter(scales))
            ms, lw = self[0].get_reference_sizes()
            self._artist_collection.set_markersize(ms*scale)
            self._artist_collection.set_linewidth(lw*scale)

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

    def get_scale(self):
        return [e.get_scale() for e in self]

    def set_scale(self, scale):
        self._set_attribute("scale", scale)



