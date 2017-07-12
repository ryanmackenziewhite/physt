from __future__ import absolute_import
import numpy as np
from bqplot import Figure, Bars, Axis, LinearScale, LogScale, Hist, Lines

types = ("bar", "line")

dims = {
    "bar": [1],
    "line": [1]
}


def _get_scales_and_axes(kwargs):
    x_scale = LinearScale()
    y_scale = LinearScale()
    ax_x = Axis(scale=x_scale)
    ax_y = Axis(scale=y_scale, orientation="vertical")

    scales = {"x": x_scale, "y": y_scale}
    axes = [ax_x, ax_y]

    return scales, axes


def bar(h1, figure=None, **kwargs):
    """

    :type h1: physt.histogram1d.Histogram1D
    :type figure: Option[Figure]
    :param kwargs:
    :rtype: Figure
    """

    # TODO: Somehow support irregulat bins

    scales, axes = _get_scales_and_axes(kwargs)

    plot = Bars(x=h1.bin_centers, y=h1.frequencies, scales=scales,
                color_mode='element')
    plot.padding = 0

    figure = Figure(marks=[plot], axes=axes)
    return figure


def line(h1, figure=None, **kwargs):
    """

    :type h1: physt.histogram1d.Histogram1D
    :type figure: Option[Figure]
    :param kwargs:
    :rtype: Figure
    """

    scales, axes = _get_scales_and_axes(kwargs)

    plot = Lines(x=h1.bin_centers, y=h1.frequencies, scales=scales)

    figure = Figure(marks=[plot], axes=axes)
    return figure