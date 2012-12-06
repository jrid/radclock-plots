#/usr/bin/env python
#
# -----------------------------------------------------------------------------
# Copyright (C) 2012 Julien Ridoux <julien@synclab.org>
# -----------------------------------------------------------------------------

import exceptions
import pandas as pd
import matplotlib.pyplot as plt

from common import *



# -----------------------------------------------------------------------------
# Compute down-sampling interval 
# -----------------------------------------------------------------------------
def sample_data(df, sampling, path):
	"""
	Heuristic to Sample DataFrame or TimeSeries. If aim at saving in a
	rasterized format, delegate the job to the renderer. Otherwise, cap number
	of points to something reasonable.
	If sampling is not None, heuristic is overwritten. If sampling is a scalar,
	ends up with deterministic sampling (1/sampling). If sampling is a string,
	the output is binned in time windows (sampling='5Min'), which may not
	reflects data density (all bins end up with one or zero points).
	This function returns a copy of the df passed to it.
	"""

	idx = df.index

	# The user rules, if sampling is an integer, do range sampling, otherwise
	# assumes we do timeseries sampling
	if sampling != None:
		if isinstance(sampling, str):
			data = df.resample(sampling, how='median')
			# Not quite sure why name is not kept in the case of a Series. Seems
			# pandas converts one column dataframe into series
			if isinstance(data, pd.Series):
				data.name = df.name
		elif isinstance(sampling, int):
			# Check if sampling disabled.
			if sampling == 0:
				return df
			size = df.count().max()
			idx = range(0,size,sampling)
			data = df.ix[idx]
		else:
			error('sampling parameter is not a scalar or string')
		return data

	# Quick test to see if we auto-sample, interactive mode, or vector output.
	autosample = False
	if plt.isinteractive():
		autosample = True
	vector_fmt_extensions = ('.svg', '.ps', '.eps', '.pdf')
	if path.lower().endswith(vector_fmt_extensions):
		autosample = True

	# Need to calibrate MAXSIZE
	MAXSIZE = 2000
	size = df.count().max()
	if autosample == True and size > MAXSIZE:
		sampling = int(size / MAXSIZE) 
		idx = range(0,size,sampling)
		data = df.ix[idx]
	else:
		data = df

	return data



# -----------------------------------------------------------------------------
# Plot timeseries
# -----------------------------------------------------------------------------
def tseries(df, styles=None, ax=None, title='Title',
		xlabel='Xlabel', ylabel='Ylabel', path=None,
		ptile_range=(1,99), sampling=None):
	"""
	Takes a pandas.Series or pandas.DataFrame timeseries as input and plot.
	sampling can be an integer or a time period such as '5Min'. If sampling is
	0, auto-sampling is disabled.
	"""

	# Test that ts is a pandas DataFrame object
	if (not isinstance(df, pd.Series) and
		not isinstance(df, pd.DataFrame)):
		print "Data passed to histogram is not a pandas DataFrame object"
		raise exceptions.TypeError
		return

	# Check that style dictionary keys match df column names
	if styles != None:
		if isinstance(df, pd.Series):
			dkeys = set([df.name])	
		elif isinstance(df, pd.DataFrame):
			dkeys = set(df.columns)
		else:
			raise exceptions.TypeError
			return
		skeys = set(styles.keys())
		if not dkeys.issubset(skeys):
			print dkeys
			print skeys
			print "styles and dataframe column do not match in tseries"
			raise exceptions.KeyError

	# Get stats for this data as a DataFrame
	stats = custom_stats(df, ptile_range)

	# Compute how to auto-scale data 
	ymax = stats.ix['upper_bound'].max()
	ymin = stats.ix['lower_bound'].min()
	spread = ymax - ymin
	scale, unit = scale_data(spread)

	# Scale stats 
	scaledstats = stats * scale

	# Sample data to save resources. Note that the stats are computed on full
	# dataset.
	# NOTE: that this requires pandas >= 0.9 to work.
	plot_data = sample_data(df, sampling, path)

	# Get reasonable figure and axis
	# NOTE: saving to a file takes precedence on axis being specified
	# TODO: xlabels are cut off when specifying dimensions???
	if path != None or ax == None:
		fig = plt.figure(figsize=(8.0, 3.0)) # in inches!
		ax = fig.gca()

	# Plot all timeseries
	# if plot_data is timeseries, style has to be a string
	if isinstance(plot_data, pd.Series):
		style = styles[plot_data.name]
	else:
		style = styles

	(plot_data * scale).plot(ax=ax, style=style,
			alpha=0.3)

	# Esthetics
	ax.grid(which='major', axis='both')
	ax.set_ylim(ymin*scale,ymax*scale)
	ax.set_title(title)
	ax.set_ylabel(ylabel+' '+unit)
	# To have ticks and labels display nicely
	fig.tight_layout()

	# Saving on file
	if path != None:
		fig.savefig(path)

	return stats

