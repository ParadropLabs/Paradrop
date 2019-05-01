from __future__ import print_function
import struct
from datetime import datetime

from twisted.internet.fdesc import setNonBlocking


class SpectrumReader(object):

    # spectral scan packet format constants
    hdrsize = 3
    pktsize = 17 + 56

    # ieee 802.11 constants
    sc_wide = 0.3125  # in MHz

    def __init__(self, path):
        self.fp = file(path)
        if not self.fp:
            raise Exception("Cant open file '%s'" % path)

        setNonBlocking(self.fp.fileno())

    def read_samples(self):
        data = self.fp.read()
        if (data):
            ts = datetime.now()
            return ts, data
        else:
            return None, None

    def flush(self):
        self.fp.read()

    @staticmethod
    def decode(data):
        """
        For information about the decoding of spectral samples see:
        https://wireless.wiki.kernel.org/en/users/drivers/ath9k/spectral_scan
        https://github.com/erikarn/ath_radar_stuff/tree/master/lib
        and your ath9k implementation in e.g.
        /drivers/net/wireless/ath/ath9k/common-spectral.c
        """
        pos = 0
        while pos < len(data) - SpectrumReader.hdrsize + 1:

            (stype, slen) = struct.unpack_from(">BH", data, pos)

            if not (stype == 1 and slen == SpectrumReader.pktsize):
                print("skip malformed packet")
                break  # header malformed, discard data. This event is very unlikely (once in ~3h)
                # On the other hand, if we buffer the sample in a primitive way, we consume too much cpu
                # for only one or two "rescued" samples every 2-3 hours

            # We only support 20 MHz
            if stype == 1:
                if pos >= len(data) - SpectrumReader.hdrsize - SpectrumReader.pktsize + 1:
                    break
                pos += SpectrumReader.hdrsize

                packet = data[pos: pos + SpectrumReader.pktsize]
                pos += SpectrumReader.pktsize

                yield packet

                '''
                (max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, tsf) = \
                    struct.unpack_from(">BHbbHBBQ", data, pos)
                pos += 17

                sdata = struct.unpack_from("56B", data, pos)
                pos += 56

                yield (tsf, max_exp, freq, rssi, noise, max_mag, max_index, bitmap_weight, sdata)

                # calculate power in dBm
                sumsq_sample = 0
                samples = []
                for raw_sample in sdata:
                    if raw_sample == 0:
                        sample = 1
                    else:
                        sample = raw_sample << max_exp
                    sumsq_sample += sample*sample
                    samples.append(sample)

                if sumsq_sample == 0:
                    sumsq_sample = 1
                sumsq_sample = 10 * math.log10(sumsq_sample)

                sc_total = 56  # HT20: 56 OFDM subcarriers

                #first_sc = freq - SpectrumReader.sc_wide * (sc_total/2 + 0.5)
                pwr = {}
                for i, sample in enumerate(samples):
                    subcarrier_freq = 0
                    if i < 28:
                        subcarrier_freq = freq - SpectrumReader.sc_wide * (28 - i)
                    else:
                        subcarrier_freq = freq + SpectrumReader.sc_wide * (i - 27)

                    #subcarrier_freq = first_sc + i*SpectrumReader.sc_wide

                    sigval = noise + rssi + 20 * math.log10(sample) - sumsq_sample
                    pwr[subcarrier_freq] = sigval

                yield (tsf, freq, noise, rssi, pwr)
                '''
