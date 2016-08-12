from __future__ import absolute_import

# This is just a proof of concept

from altair import Chart


types = ("bar", "line", "scatter")

dims = {
    "bar": [1],
    "line": [1],
    "scatter": [1]
}


def _make_chart(h1, method, **kwargs):
    df = h1.to_dataframe()
    axis_name = h1.axis_name or h1.name or "x"
    df[axis_name] = h1.bin_centers
    chart = Chart(df)
    attr = getattr(chart, method)
    kwargs.update({
        "x": axis_name,
        "y": "frequency"
    })
    return attr().encode(
        **kwargs
    )


def bar(h1, **kwargs):
    """Simple bar plot

    Parameters
    ----------
    h1 : physt.Histogram1D
    """
    return _make_chart(h1, "mark_bar")


def line(h1, **kwargs):
    return _make_chart(h1, "mark_line")


def scatter(h1, **kwargs):
    return _make_chart(h1, "mark_point")



