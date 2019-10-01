"""
Methods for preprocessing of inertial data.

Lukas Adamowicz
Pfizer
2019
"""
from numpy import around, mean, diff, timedelta64
from numpy.linalg import norm
from scipy.signal import butter, filtfilt
import pywt
from pandas import to_datetime

from pysit2stand.utility import mov_stats


class AccFilter:
    """
    Object for filtering and reconstructing raw acceleration data

    Parameters
    ----------
    reconstruction_method : {'moving average', 'dwt'}, optional
        Method for computing the reconstructed acceleration. Default is 'moving average', which takes the moving
        average over the specified window. Other option is 'dwt', which uses the discrete wavelet transform to
        deconstruct and reconstruct the signal while filtering noise out.
    lowpass_order : int, optional
        Initial low-pass filtering order. Default is 4.
    lowpass_cutoff : float, optional
        Initial low-pass filtering cuttoff, in Hz. Default is 5Hz.
    window : float, optional
        Window to use for moving average, in seconds. Default is 0.25s. Ignored if reconstruction_method is 'dwt'.
    discrete_wavelet : str, optional
        Discrete wavelet to use if reconstruction_method is 'dwt'. Default is 'dmey'. See
        pywt.wavelist(kind='discrete') for a complete list of options. Ignored if reconstruction_method is
        'moving average'.
    extension_mode : str, optional
        Signal extension mode to use in the DWT de- and re-construction of the signal. Default is 'constant', see
        pywt.Modes.modes for a list of options. Ignored if reconstruction_method is 'moving average'.
    reconstruction_level : int, optional
        Reconstruction level of the DWT processed signal. Default is 1. Ignored if reconstruction_method is
        'moving average'.
    """
    def __init__(self, reconstruction_method='moving average', lowpass_order=4, lowpass_cutoff=5,
                 window=0.25, discrete_wavelet='dmey', extension_mode='constant', reconstruction_level=1):
        if reconstruction_method == 'moving average' or reconstruction_method == 'dwt':
            self.method = reconstruction_method
        else:
            raise ValueError('reconstruction_method is not recognized. Options are "moving average" or "dwt".')

        self.lp_ord = lowpass_order
        self.lp_cut = lowpass_cutoff

        self.window = window

        self.dwave = discrete_wavelet
        self.ext_mode = extension_mode
        self.recon_level = reconstruction_level

    def apply(self, accel, fs):
        """
        Apply the desired filtering to the provided signal.

        Parameters
        ----------
        accel : numpy.ndarray
            (N, 3) array of raw acceleration values.
        fs : float, optional
            Sampling frequency for the acceleration data.

        Returns
        -------
        mag_acc_f : numpy.ndarray
            (N, ) array of the filtered (low-pass only) acceleration magnitude.
        mag_acc_r : numpy.ndarray
            (N, ) array of the reconstructed acceleration magnitude. This is either filtered and then moving averaged,
            or filtered, and then passed through the DWT and inverse DWT with more filtering, depending on the
            reconstruction_method specified.
        """
        # compute the acceleration magnitude
        macc = norm(accel, axis=1)

        # setup the filter, and filter the acceleration magnitude
        fc = butter(self.lp_ord, 2 * self.lp_cut / fs, btype='low')
        macc_f = filtfilt(fc[0], fc[1], macc)

        if self.method == 'dwt':
            # deconstruct the filtered acceleration magnitude
            coefs = pywt.wavedec(macc_f, self.dwave, mode=self.ext_mode)

            # set all but the desired level of coefficients to be 0s
            if (len(coefs) - self.recon_level) < 1:
                print(f'Chosen reconstruction level is too high, setting reconstruction level to {len(coefs) - 1}')
                ind = 1
            else:
                ind = len(coefs) - self.recon_level

            for i in range(1, len(coefs)):
                if i != ind:
                    coefs[i][:] = 0

            macc_r = pywt.waverec(coefs, self.dwave, mode=self.ext_mode)
        elif self.method == 'moving average':
            n_window = int(around(fs * self.window))  # compute the length in samples of the moving average
            macc_r, _, _ = mov_stats(macc_f, n_window)  # compute the moving average

        return macc_f, macc_r[:macc_f.size]


def process_timestamps(times, accel, time_units=None, conv_kw=None, window=False, hours=('08:00', '20:00')):
    """
    Convert timestamps into pandas datetime64 objects, and window as appropriate.

    Parameters
    ----------
    times : array_like
        N-length array of timestamps to convert.
    accel : {numpy.ndarray, pd.Series}
        (N, 3) array of acceleration values. They will be windowed the same way as the timestamps if `window` is set
        to True.
    time_units : {None, str}, optional
        Time units. Useful if conversion is from unix timestamps in seconds (s), milliseconds (ms), microseconds (us),
        or nanoseconds (ns). If not None, will override the value in conv_kw, though one or the other must be provided.
        Default is None.
    conv_kw : {None, dict}, optional
        Additional key-word arguments for the pandas.to_datetime function. If time_units is not None, that value
        will be used and overwrite the value in conv_kw. If the timestamps are in unix time, it is unlikely this
        argument will be necessary. Default is None.
    window : bool, optional
        Window the timestamps into the selected hours per day.
    hours : array_like, optional
        Length two array_like of hours (24-hour format) as strings, defining the start (inclusive) and end (exclusive)
        times to include in the processing. Default is ('08:00', '20:00').

    Returns
    -------
    timestamps : {pandas.DatetimeIndex, pandas.Series}
        Array_like of timestamps. DatetimeIndex if times was a numpy.ndarray, or list. pandas.Series with a dtype of
        'datetime64' if times was a pandas.Series. If `window` is set to True, these are the timestamps falling between
        the hours selected.
    dt : float
        Sampling time in seconds.
    accel : {numpy.ndarray, pd.Series}, optional
        Acceleration windowed the same way as the timestamps, if `window` is True. If `window` is False, then the
        acceleration is not returned.
    """
    if conv_kw is not None:
        if time_units is not None:
            conv_kw['unit'] = time_units
    else:
        if time_units is not None:
            conv_kw = {'unit': time_units}
        else:
            raise ValueError('Either (time_units) must be defined, or "unit" must be a key of (conv_kw).')

    # convert using pandas
    timestamps = to_datetime(times, **conv_kw)

    # find the sampling time
    dt = mean(diff(timestamps)) / timedelta64(1, 's')  # convert to seconds

    # windowing
    if window:
        hour_inds = timestamps.indexer_between_time(hours[0], hours[1])

        timestamps = timestamps[hour_inds]
        accel = accel[hour_inds]

        return timestamps, dt, accel
    else:
        return timestamps, dt


