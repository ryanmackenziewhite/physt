"""Different binning algorithms/schemas for the histograms."""

import numpy as np
from .bin_utils import make_bin_array, is_consecutive, to_numpy_bins, is_rising, is_bin_subset

# TODO: Reduce number of classes + change construct into functions
# TODO: Locking and edit operations (like numpy read-only)


class BinningBase(object):
    """Abstract base class for binning.

    Inheriting
    ----------
    - define at least one of the following properties: bins, numpy_bins (cached intercomputation exists)
    - if you modify the bins, be sure to put _bins and _numpy_bins into proper state (in some cases, None is sufficient)
    - the construct method should prepare bins etc.
    - checking of proper bins should be done in __init__
    - if you want to support adaptive histogram, override _force_bin_existence
    """
    def __init__(self, bins=None, numpy_bins=None, includes_right_edge=False, integrity_check=True, adaptive=False):
        # TODO: Incorporate integrity_check parameter
        self._consecutive = None
        if bins is not None:
            if numpy_bins is not None:
                raise RuntimeError("Cannot specify numpy_bins and bins at the same time.")
            bins = make_bin_array(bins)
            if not is_rising(bins):
                raise RuntimeError("Bins must be in rising order.")
            # TODO: Test for consecutiveness?
        elif numpy_bins is not None:
            numpy_bins = to_numpy_bins(numpy_bins)
            if not np.all(numpy_bins[1:] > numpy_bins[:-1]):
                raise RuntimeError("Bins must be in rising order.")
            self._consecutive = True
        self._bins = bins
        self._numpy_bins = numpy_bins
        self._includes_right_edge = includes_right_edge
        if adaptive and not self.adaptive_allowed:
            raise RuntimeError("Adaptivity not allowed for {0}".format(self.__class__.__name__))
        if adaptive and includes_right_edge:
            raise RuntimeError("Adaptivity does not work together with right-edge inclusion.")
        self._adaptive = adaptive

    adaptive_allowed = False
    inconsecutive_allowed = False
    # TODO: adding allowed?

    @property
    def includes_right_edge(self):
        return self._includes_right_edge

    def is_consecutive(self, rtol=1.e-5, atol=1.e-8):
        if self.inconsecutive_allowed:
            if self._consecutive is None:
                if self._numpy_bins is not None:
                    self._consecutive = True
                self._consecutive = is_consecutive(self.bins, rtol, atol)
            return self._consecutive
        else:
            return True

    def is_adaptive(self):
        return self._adaptive

    def force_bin_existence(self, values):
        """Change schema so that there is a bin for value

        Parameters
        ----------
        values: np.ndarray
            All values we want bins for.

        Returns
        -------
        bin_map: Iterable[tuple] or None
            None => There was no change in bins
            Otherwise => the iterable contains tuples (old bin index, new bin index)
        """
        # TODO: Rename to something less evil
        if not self.is_adaptive():
            raise RuntimeError("Histogram is not adaptive")
        else:
            return self._force_bin_existence(values)

    def _force_bin_existence(self, values):
        # TODO: in-place
        raise NotImplementedError()

    def adapt(self, other):
        """

        Parameters
        ----------
        other: BinningBase

        Returns
        -------

        """
        # TODO: in-place arg
        if self.bins == other.bins:
            return None, None
        elif is_bin_subset(other.bins, self.bins):
            indices = np.searchsorted(other.bins[:,0], self.bins[:,0])
            return None, enumerate(indices)
        elif not self.is_adaptive():
            raise RuntimeError("Cannot adapt non-adaptive binning.")
        else:
            return self._adapt(other)

    def _adapt(self, other):
        raise RuntimeError("Cannot adapt binning.")

    # def union(self, other, inplace=False):
    #     """Change schema so that it becomes a superset of another.
    #
    #     Parameters
    #     ----------
    #     other: BinningBase
    #     inplace: bool
    #
    #     Returns
    #     -------
    #     BinningBase | None
    #     """
    #     # TODO: Real
    #     raise NotImplementedError()

    @property
    def bins(self):
        if self._bins is None:
            self._bins = make_bin_array(self.numpy_bins)
        return self._bins

    @property
    def bin_count(self):
        return self.bins.shape[0]

    @property
    def numpy_bins(self):
        if self._numpy_bins is None:
            self._numpy_bins = to_numpy_bins(self.bins)
        return self._numpy_bins

    @property
    def first_edge(self):
        return self._bins[0][0]

    @property
    def last_edge(self):
        return self._bins[-1][1]

    def as_static(self, copy=True):
        """Convert binning to a static form.

        Parameters
        ----------
        copy: bool
            Ensure that we receive another object

        Returns
        -------
        StaticBinning
            A new static binning with a copy of bins.
        """
        return StaticBinning(bins=self.bins.copy(), includes_right_edge=self.includes_right_edge)

    def as_fixed_width(self, copy):
        """Convert binning to recipe with fixed width.

        Parameters
        ----------
        copy: bool
            Ensure that we receive another object

        Returns
        -------
        FixedWidthBinning
        """
        if self.bin_count == 0:
            raise RuntimeError("Cannot guess binning width with zero bins")
        elif self.bin_count == 1 or self.is_consecutive() and np.allclose(np.diff(self.bins[1] - self.bins[0]), 0.0):
            return FixedWidthBinning(min=self.bins[0][0], bin_count=self.bin_count, bin_width=self.bins[1] - self.bins[0])
        else:
            raise RuntimeError("Cannot create fixed-width binning from differing bin widths.")

    def copy(self):
        """
        Returns
        -------
        BinningBase
        """
        raise NotImplementedError()


class StaticBinning(BinningBase):
    inconsecutive_allowed = True

    def as_static(self, copy=True):
        """Convert binning to a static form.

        Returns
        -------
        StaticBinning
            A new static binning with a copy of bins.
        """
        if copy:
            return StaticBinning(bins=self.bins.copy(), includes_right_edge=self.includes_right_edge)
        else:
            return self

    def copy(self):
        return self.as_static(True)

    def __getitem__(self, item):
        copy = self.copy()
        copy._bins = self._bins[item]
        # TODO: check for the right_edge??
        return copy


class NumpyBinning(BinningBase):
    """Binning schema working as numpy.histogram.
    """
    def __init__(self, numpy_bins, includes_right_edge=True):
        # Check: rising
        super(NumpyBinning, self).__init__(numpy_bins=numpy_bins, includes_right_edge=includes_right_edge)

    @property
    def numpy_bins(self):
        return self._numpy_bins

    def copy(self):
        return NumpyBinning(numpy_bins=self.numpy_bins, includes_right_edge=self.includes_right_edge)


class FixedWidthBinning(BinningBase):
    """Binning schema with predefined bin width."""
    adaptive_allowed = True

    def __init__(self, bin_width, bin_count=0, min=-np.nan, includes_right_edge=False, adaptive=False, shift=0.0,
                 align=True):
        super(FixedWidthBinning, self).__init__(adaptive=adaptive, includes_right_edge=includes_right_edge)

        if bin_width <= 0:
            raise RuntimeError("Bin width must be > 0.")
        self._bin_width = float(bin_width)
        self._align = align

        if bin_count < 0:
            raise RuntimeError("Bin count must be >= 0.")
        self._bin_count = int(bin_count)
        self._min = min
        self._bins = None
        self._numpy_bins = None
        self._shift = shift or 0.0     # TODO: shift implies align?

    def _force_bin_existence_single(self, value, includes_right_edge=None):
        if includes_right_edge is None:
            includes_right_edge = self.includes_right_edge

        if self._bin_count == 0:
            if self._align:
                self._min = np.floor((value - self._shift) / self.bin_width) * self.bin_width + self._shift  # TODO: who' abou' alignment?
            else:
                self._min = value
                self._shift = np.mod(self._min, self._bin_width)
            self._bin_count = 1
            self._bins = None
            self._numpy_bins = None
            return ()
        else:
            original_count = self.bin_count
            add_left = add_right = 0
            if value < self.numpy_bins[0]:
                add_left = int(np.ceil((self.numpy_bins[0] - value) / self.bin_width))
                self._min -= add_left * self.bin_width
                self._bin_count += add_left
            elif value >= self.numpy_bins[-1]:
                add_right = (value - self.numpy_bins[-1]) /  self.bin_width
                if add_right - np.floor(add_right) == 0 and not includes_right_edge:
                    add_right = int(add_right + 1)
                else:
                    add_right = int(np.ceil(add_right))
                self._bin_count += add_right
            if add_left or add_right:
                self._bins = None
                self._numpy_bins = None
                return ((i, i + add_left) for i in range(original_count))
            else:
                return None

    def _force_bin_existence(self, values, includes_right_edge=None):
        if np.isscalar(values):
            return self._force_bin_existence_single(values, includes_right_edge=includes_right_edge)
        else:
            min, max = np.min(values), np.max(values)
            result = self._force_bin_existence_single(min, includes_right_edge=includes_right_edge)
            self._force_bin_existence_single(max, includes_right_edge=includes_right_edge)
            return result

    @property
    def numpy_bins(self):
        if self._numpy_bins is None:
            if self._bin_count == 0:
                return np.zeros((0, 2), dtype=float)
            self._numpy_bins = self._min + self._bin_width * np.arange(self._bin_count + 1)
        return self._numpy_bins

    @property
    def bin_count(self):
        return self._bin_count

    def copy(self):
        return FixedWidthBinning(
            bin_width=self._bin_width,
            bin_count=self._bin_count,
            min=self._min,
            align=self._align,
            includes_right_edge=self.includes_right_edge,
            shift=self._shift,
            adaptive=self._adaptive)

    @property
    def bin_width(self):
        return self._bin_width

    @property
    def first_edge(self):
        return self._min

    @property
    def last_edge(self):
        return self._min + self._bin_count * self.bin_width

    def _adapt(self, other):
        """

        Parameters
        ----------
        other: BinningBase
        """
        other = other.as_fixed_width()
        if self.bin_width != other.bin_width:
            raise RuntimeError("Cannot adapt fixed-width histograms with different widths")
        if self.shift != other.shift:
            raise RuntimeError("Cannot adapt shifted fixed-width histograms")
        # Following operations modify schemas
        other = other.copy()
        bin_map1 = self._force_bin_existence([other.first_edge, other.last_edge], includes_right_edge=False)
        bin_map2 = other._force_bin_existence([self.first_edge, self.last_edge], includes_right_edge=False)
        return bin_map1, bin_map2

    @property
    def shift(self):
        return self._shift

    def as_fixed_width(self, copy=True):
        if copy:
            return self.copy()
        else:
            return self


class ExponentialBinning(BinningBase):
    """Binning schema with exponentially distributed bins."""
    adaptive_allowed = False

    # TODO: Implement adaptivity

    def __init__(self, log_min, log_width, bin_count, includes_right_edge=False, adaptive=False):
        super(ExponentialBinning, self).__init__(includes_right_edge=includes_right_edge, adaptive=adaptive)
        self._log_min = log_min
        self._log_width = log_width
        self._bin_count = bin_count

    @property
    def numpy_bins(self):
        if self._bin_count == 0:
            return np.ndarray((0), dtype=float)
        if self._numpy_bins is None:
            log_bins = self._log_min + np.arange(self._bin_count + 1) * self._log_width
            self._numpy_bins = 10 ** log_bins
        return self._numpy_bins

    def copy(self):
        return ExponentialBinning(self._log_min, self._log_width, self._bin_count, self.includes_right_edge)


def numpy_binning(data, bins=10, range=None, *args, **kwargs):
    """Construct binning schema compatible with numpy.histogram

    Parameters
    ----------
    data: array_like, optional
        This is optional if both bins and range are set
    bins: int or array_like
    range: Optional[tuple]
        (min, max)
    includes_right_edge: Optional[bool]
        default: True

    Returns
    -------
    numpy.ndarray

    See Also
    --------
    numpy.histogram
    """
    if isinstance(bins, int):
        if range:
            bins = np.linspace(range[0], range[1], bins + 1)
        else:
            start = data.min()
            stop = data.max()
            bins = np.linspace(start, stop, bins + 1)
    elif np.iterable(bins):
        bins = np.asarray(bins)
    else:
        # Some numpy edge case
        _, bins = np.histogram(data, bins, **kwargs)
    return NumpyBinning(bins)


def human_binning(data=None, bins=None, range=None, **kwargs):
    """Construct fixed-width ninning schema with bins automatically optimized to human-friendly widths.

    Typical widths are: 1.0, 25,0, 0.02, 500, 2.5e-7, ...

    Parameters
    ----------
    bins: Optional[int]
        Number of bins
    range: Optional[tuple]
        (min, max)

    Returns
    -------
    numpy.ndarray
    """
    subscales = np.array([0.5, 1, 2, 2.5, 5, 10])

    if bins is None:
        bins = ideal_bin_count(data)
    # TODO data or range check
    min_ = range[0] if range else data.min()
    max_ = range[1] if range else data.max()
    bw = (max_ - min_) / bins

    power = np.floor(np.log10(bw)).astype(int)
    best_index = np.argmin(np.abs(np.log(subscales * (10 ** power) / bw)))
    bin_width = (10 ** power) * subscales[best_index]
    return fixed_width_binning(bin_width=bin_width, data=data, range=range, **kwargs)


def quantile_binning(data=None, bins=10, qrange=(0.0, 1.0), **kwargs):
    """Binning schema based on quantile ranges.

    This binning finds equally spaced quantiles. This should lead to
    all bins having roughly the same frequencies.

    Note: weights are not (yet) take into account for calculating
    quantiles.

    Parameters
    ----------
    bins: sequence or Optional[int]
        Number of bins
    qrange: Optional[tuple]
        Two floats as minimum and maximum quantile (default: 0.0, 1.0)

    Returns
    -------
    numpy.ndarray
    """

    if np.isscalar(bins):
        bins = np.linspace(qrange[0] * 100, qrange[1] * 100, bins + 1)
    bins = np.percentile(data, bins)
    return static_binning(bins=make_bin_array(bins), includes_right_edge=True)


def static_binning(data=None, bins=None, **kwargs):
    """Construct static binning with whatever bins."""
    return StaticBinning(bins=bins, **kwargs)


def integer_binning(data=None, **kwargs):
    """Construct fixed-width binning schema with bins centered around integers.

    Parameters
    ----------
    range: Optional[Tuple[int]]
        min (included) and max integer (excluded) bin

     Returns
    -------
    numpy.ndarray
    """
    if "range" in kwargs:
        kwargs["range"] = tuple(r - 0.5 for r in kwargs["range"])
    return fixed_width_binning(data=data, bin_width=1, align=True, shift=0.5, **kwargs)


def fixed_width_binning(data=None, bin_width=1, range=None, includes_right_edge=False, **kwargs):
    """Construct fixed-width binning schema.

    Parameters
    ----------
    bin_width: float
    range: Optional[tuple]
        (min, max)
    align: Optional[float]
        Must be multiple of bin_width

    Returns
    -------
    FixedWidthBinning
    """
    result = FixedWidthBinning(bin_width=bin_width, includes_right_edge=includes_right_edge, **kwargs)
    if range:
        result._force_bin_existence(range[0])
        result._force_bin_existence(range[1], includes_right_edge=True)
        if not kwargs.get("adaptive"):
            return result  # Otherwise we want to adapt to data
    if data is not None:
        result._force_bin_existence(np.min(data))
        result._force_bin_existence(np.max(data))
    return result


def exponential_binning(data=None, bins=None, range=None, **kwargs):
    """Construct exponential binning schema.

    Parameters
    ----------
    bins: Optional[int]
        Number of bins
    range: Optional[tuple]
        (min, max)

    Returns
    -------
    numpy.ndarray

    See also
    --------
    numpy.logspace - note that our range semantics is different
    """
    if bins is None:
        bins = ideal_bin_count(data)

    if range:
        range = (np.log10(range[0]), np.log10(range[1]))
    else:
        range = (np.log10(data.min()), np.log10(data.max()))
    log_width = (range[1] - range[0]) / bins
    return ExponentialBinning(log_min=range[0], log_width=log_width, bin_count=bins, **kwargs)

# def union(schema1, schema2):
#     """
#     Parameters
#     ----------
#     schema1: BinningBase
#     schema2: BinningBase
#
#     Returns
#     -------
#     new_schema: BinningBase
#     bin_map1: Iterable[tuple] or None
#     bin_map2: Iterable[tuple] or None
#     """
#     if schema1.bins == schema2.bins:     # TODO: perhaps a more
#         return schema1, None, None
#
#     # 1) Fixed-width variant for a more simple
#     try:
#         schema1 = schema1.as_fixed_width(copy=True)
#         schema2 = schema2.as_fixed_width(copy=True)
#
#         return
#     except:
#         pass
#
#     # 2)
#     schema1 = schema1.as_static(copy=True)
#     schema2 = schema2.as_static(copy=True)


def calculate_bins(array, _=None, *args, **kwargs):
    """Find optimal binning from arguments.

    Parameters
    ----------
    array: arraylike
        Data from which the bins should be decided (sometimes used, sometimes not)
    _: int or str or Callable or arraylike or Iterable
        To-be-guessed parameter that specifies what kind of binning should be done
    check_nan: bool
        Check for the presence of nan's in array? Default: True
    range: tuple
        Limit values to a range. Some of the binning methods also (subsequently)
        use this parameter for the bin shape.

    Returns
    -------
    BinningBase
        A two-dimensional array with pairs of bin edges (not necessarily consecutive).

    """
    if kwargs.pop("check_nan", True):
        if np.any(np.isnan(array)):
            raise RuntimeError("Cannot calculate bins in presence of NaN's.")
    if "range" in kwargs:   # TODO: re-consider the usage of this parameter
        array = array[(array >= kwargs["range"][0]) & (array <= kwargs["range"][1])]
    if _ is None:
        bin_count = kwargs.pop("bins", ideal_bin_count(data=array))
        binning = numpy_binning(array, bin_count, *args, **kwargs)
    elif isinstance(_, int):
        binning =  numpy_binning(array, _, *args, **kwargs)
    elif isinstance(_, str):
        # What about the ranges???
        if _ in bincount_methods:
            bin_count = ideal_bin_count(array, method=_)
            binning = numpy_binning(array, bin_count, *args, **kwargs)
        elif _ in binning_dict:
            method = binning_dict[_]
            binning = method(array, *args, **kwargs)
        else:
            raise RuntimeError("No binning method {0} available.".format(_))
    elif callable(_):
        binning = _(array, *args, **kwargs)
    elif np.iterable(_):
        binning = static_binning(array, _, *args, **kwargs)
    else:
        raise RuntimeError("Binning {0} not understood.".format(_))
    return binning


def calculate_bins_nd(array, bins=None, *args, **kwargs):
    """Find optimal binning from arguments (n-dimensional variant)

    Usage similar to `calculate_bins`.
    """
    if kwargs.pop("check_nan", True):
        if np.any(np.isnan(array)):
            raise RuntimeError("Cannot calculate bins in presence of NaN's.")
    n, dim = array.shape

    # Prepare bins
    if isinstance(bins, (list, tuple)):
        if len(bins) != dim:
            raise RuntimeError("List of bins not understood.")
    else:
        bins = [bins] * dim

    # Prepare arguments
    args = list(args)
    range_ = kwargs.pop("range", None)
    if range_:
        range_n = np.asarray(range_)
        if range_n.shape == (2,):
            range_ = dim * [range_]
        elif range_n.shape == (dim, 2):
            range_ = range_
        else:
            raise RuntimeError("1 or d tuples expected for the range")
    for i in range(len(args)):
        if isinstance(args[i], (list, tuple)):
            if len(args[i]) != dim:
                raise RuntimeError("Argument not understood.")
        else:
            args[i] = dim * [args[i]]
    for key in list(kwargs.keys()):
        if isinstance(kwargs[key], (list, tuple)):
            if len(kwargs[key]) != dim:
                raise RuntimeError("Argument not understood.")
        else:
            kwargs[key] = dim * [kwargs[key]]

    if range_:
        kwargs["range"] = range_

    bins = [
        calculate_bins(array[:, i], bins[i],
                       *(arg[i] for arg in args),
                       **{k : kwarg[i] for k, kwarg in kwargs.items()})
        for i in range(dim)
        ]
    return bins


# TODO: Rename
binning_dict = {
    "numpy" : numpy_binning,
    "exponential" : exponential_binning,
    "quantile": quantile_binning,
    "fixed_width": fixed_width_binning,
    "integer": integer_binning,
    "human" : human_binning
}

# TODO: Change astropys to ...
# try:
#     from astropy.stats.histogram import histogram, knuth_bin_width, freedman_bin_width, scott_bin_width, bayesian_blocks
#     import warnings
#     warnings.filterwarnings("ignore", module="astropy\..*")
#
#     def astropy_bayesian_blocks(data, range=None, **kwargs):
#         """Binning schema based on Bayesian blocks (from astropy).
#
#         Computationally expensive for large data sets.
#
#         Parameters
#         ----------
#         data: arraylike
#         range: Optional[tuple]
#
#         Returns
#         -------
#         numpy.ndarray
#
#         See also
#         --------
#         astropy.stats.histogram.bayesian_blocks
#         astropy.stats.histogram.histogram
#         """
#         if range is not None:
#             data = data[(data >= range[0]) & (data <= range[1])]
#         edges = bayesian_blocks(data)
#         return edges
#
#     def astropy_knuth(data, range=None, **kwargs):
#         """Binning schema based on Knuth's rule (from astropy).
#
#         Computationally expensive for large data sets.
#
#         Parameters
#         ----------
#         data: arraylike
#         range: Optional[tuple]
#
#         Returns
#         -------
#         numpy.ndarray
#
#         See also
#         --------
#         astropy.stats.histogram.knuth_bin_width
#         astropy.stats.histogram.histogram
#         """
#         if range is not None:
#             data = data[(data >= range[0]) & (data <= range[1])]
#         _, edges = knuth_bin_width(data, True)
#         return edges
#
#     def astropy_scott(data, range=None, **kwargs):
#         """Binning schema based on Scott's rule (from astropy).
#
#         Parameters
#         ----------
#         data: arraylike
#         range: Optional[tuple]
#
#         Returns
#         -------
#         numpy.ndarray
#
#         See also
#         --------
#         astropy.stats.histogram.scott_bin_width
#         astropy.stats.histogram.histogram
#         """
#         if range is not None:
#             data = data[(data >= range[0]) & (data <= range[1])]
#         _, edges = scott_bin_width(data, True)
#         return edges
#
#     def astropy_freedman(data, range=None, **kwargs):
#         """Binning schema based on Freedman-Diaconis rule (from astropy).
#
#         Parameters
#         ----------
#         data: arraylike
#         range: Optional[tuple]
#
#         Returns
#         -------
#         numpy.ndarray
#
#         See also
#         --------
#         astropy.stats.histogram.freedman_bin_width
#         astropy.stats.histogram.histogram
#         """
#         if range is not None:
#             data = data[(data >= range[0]) & (data <= range[1])]
#         _, edges = freedman_bin_width(data, True)
#         return edges
#
#     binning_methods["astropy_blocks"] = astropy_bayesian_blocks
#     binning_methods["astropy_knuth"] = astropy_knuth
#     binning_methods["astropy_scott"] = astropy_scott
#     binning_methods["astropy_freedman"] = astropy_freedman
# except:
#     pass     # astropy is not required


def ideal_bin_count(data, method="default"):
    """A theoretically ideal bin count.

    Parameters
    ----------
    data: array_like or None
        Data to work on. Most methods don't use this.
    method: str
        Name of the method to apply, available values:
          - default
          - sqrt
          - sturges
          - doane
        See https://en.wikipedia.org/wiki/Histogram for the description

    Returns
    -------
    int
        Number of bins, always >= 1
    """
    n = data.size
    if n < 1:
        return 1
    if method == "default":
        if n <= 32:
            return 7
        else:
            return ideal_bin_count(data, "sturges")
    elif method == "sqrt":
        return int(np.ceil(np.sqrt(n)))
    elif method == "sturges":
        return int(np.ceil(np.log2(n)) + 1)
    elif method == "doane":
        if n < 3:
            return 1
        from scipy.stats import skew
        sigma = np.sqrt(6 * (n-2) / (n + 1) * (n + 3))
        return int(np.ceil(1 + np.log2(n) + np.log2(1 + np.abs(skew(data)) / sigma)))
    elif method == "rice":
        return int(np.ceil(2 * np.power(n, 1 / 3)))


bincount_methods = ["default", "sturges", "rice", "sqrt", "doane"]