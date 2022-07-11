#!/usr/bin/python3


import json
import math

import fsleyes
import numpy
import scipy.ndimage
import wx


try:
	import colorama
except ModuleNotFoundError:
	colorama = None

def debug(*objects, sep=' ', end='\n', mode=None):
	# IDEA verbosity
	prefix = None
	suffix = None
	if mode is not None and colorama is not None:
		if mode == 'info':
			prefix = colorama.Fore.BLUE
		elif mode == 'warning':
			prefix = colorama.Fore.YELLOW
		elif mode == 'success':
			prefix = colorama.Fore.GREEN
		elif mode == 'failure':
			prefix = colorama.Fore.RED
		if prefix is not None:
			suffix = colorama.Fore.RESET
	if prefix is None:
		prefix = ''
	if suffix is None:
		suffix = ''
	print(prefix, end='')
	print('ablation:', *objects, sep=sep, end='')
	print(suffix, end=end)

debug('plugin loaded', mode='success')


GEOMETRY_DIAMETER_MIN = 1
GEOMETRY_DIAMETER_MAX = 20
GEOMETRY_DIAMETER_DEF = 3

GEOMETRY_SAFEZONE_MIN = 1
GEOMETRY_SAFEZONE_MAX = 50
GEOMETRY_SAFEZONE_DEF = 15

GEOMETRY_BORDER = 2


def fa(icon):
	return wx.Bitmap('fontawesome/{:s}.png'.format(icon), wx.BITMAP_TYPE_PNG)

def edt_box(mask, distance=0., zooms=None):
	assert distance >= 0
	if zooms is None:
		zooms = (1,) * mask.ndim
	assert len(zooms) == mask.ndim
	assert all(x > 0 for x in zooms)
	S = distance * numpy.reciprocal(zooms)
	S = numpy.round(S).astype(int)
	I = numpy.argwhere(mask)
	LL = numpy.zeros(mask.ndim, dtype=int)
	L = I.min(axis=0) - S
	L = numpy.maximum(L, LL)
	UU = numpy.asarray(mask.shape) + 1
	U = I.max(axis=0) + S + 1
	U = numpy.minimum(U, UU)
	if numpy.array_equal(L, LL) and numpy.array_equal(U, UU):
		return None
	else:
		return tuple(slice(l,u) for l, u in zip(L, U))

def edt(mask, distance=1., zooms=None, box=False):
	assert distance >= 0
	if zooms is None:
		zooms = (1,) * mask.ndim
	assert len(zooms) == mask.ndim
	assert all(x > 0 for x in zooms)
	if box:
		box = edt_box(mask, distance, zooms)
	else:
		box = None
	if box is None:
		temp = mask
	else:
		temp = mask[box]
	temp = scipy.ndimage.distance_transform_edt(~temp, zooms)
	if box is None:
		mask = temp
	else:
		mask = numpy.full(mask.shape, distance)
		mask[box] = temp
	return mask


"""

self.window : window

self.init_items : sizeritem[]
self.main_items : sizeritem[]
self.form_items : sizeritem[]

self.needle_sizer : sizer
self.form_insert : bitmapbutton
self.form_title : statictext
self.form_submit : bitmapbutton
self.form_slider : slider
self.form_coordinates : dict
	entry : tuple of textctrl
	target : tuple of textctrl
self.form_buttons : dict
	entry : bitmapbutton
	target : bitmapbutton
self.geometry_diameter : spinctrl
self.geometry_safezone : spinctrl
self.drawmode_title : statictext
self.drawmode_buttons : dict
	none : bitmaptogglebutton
	line : bitmaptogglebutton
	full : bitmaptogglebutton
self.mask_sizer : sizer

self.instance : dict|none
	path : str|none
	image : image
	needles : dict[]
		entry : tuple of float
		target : tuple of float
	buttons : dict
		update : bitmapbutton[]
		clone : bitmapbutton[]
		delete : bitmapbutton[]
	form : dict|none
		index : int
		point : dict
			entry : (tuple of float)|none
			target : (tuple of float)|none
		dirty : bool
	geometry_diameter : int
	geometry_safezone : int
	drawmode : str
	mask_array : ndarray|none
	mask_overlays : overlay[]
	mask_bitmaps : staticbitmap[]

"""


class AblationControlPanel(fsleyes.controls.controlpanel.ControlPanel):

	@staticmethod
	def title():
		return 'Ablation'

	def __init__(self, *args, **kwargs):
		debug('creating panel', mode='info')
		super().__init__(*args, **kwargs)
		self.overlayList.addListener(
			'overlays',
			self.name,
			self.on_overlay_list_changed,
			immediate=True,
		)
		# home sizer
		home_sizer = wx.BoxSizer(wx.VERTICAL)
		home_sizer.SetMinSize(280, 0)
		self.SetSizer(home_sizer)
		# main window
		self.window = wx.lib.scrolledpanel.ScrolledPanel(self)
		self.window.SetupScrolling()
		home_sizer.Add(self.window, 1, flag=wx.EXPAND)
		# horizontal sizer
		horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.window.SetSizer(horizontal_sizer)
		# horizontal spacer
		horizontal_sizer.AddSpacer(4)
		# main sizer
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.AddSpacer(4)
		self.build_init_items(main_sizer)
		self.build_main_items(main_sizer)
		main_sizer.AddSpacer(4)
		horizontal_sizer.Add(main_sizer, 1)
		# horizontal spacer
		horizontal_sizer.AddSpacer(4)
		# reset
		self.reset()

	def build_init_items(self, main_sizer):
		self.init_items = []
		# top sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('file-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('create needle list')
		handler = lambda event, load=False: \
			self.on_instance_load_button_click(event, load)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('file-import-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('import needle list from json file')
		handler = lambda event, load=True: \
			self.on_instance_load_button_click(event, load)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		self.init_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.init_items.append(main_sizer.AddSpacer(4))
		# link line
		self.init_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.init_items.append(main_sizer.AddSpacer(4))
		# link ctrl
		self.init_items.append(main_sizer.Add(wx.adv.HyperlinkCtrl(
			self.window,
			label='GitHub',
			url='https://github.com/constracti/fsleyes-plugin-ablation',
		)))
		self.init_items.append(main_sizer.AddSpacer(4))

	def build_main_items(self, main_sizer):
		self.main_items = []
		# top sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('file-export-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('export needle list to json file')
		button.Bind(wx.EVT_BUTTON, self.on_instance_save_button_click)
		sizer.Add(button)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('xmark-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('close needle list')
		button.Bind(wx.EVT_BUTTON, self.on_instance_close_button_click)
		sizer.Add(button)
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# needle line
		self.main_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# needle title sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.window,
			label='needle list',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('plus-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('insert needle')
		handler = lambda event: \
			self.on_needle_insert_button_click(event, 0)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		self.form_insert = button
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# needle list sizer
		sizer = wx.FlexGridSizer(5, 4, 4)
		sizer.SetFlexibleDirection(wx.HORIZONTAL)
		sizer.AddGrowableCol(1)
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.needle_sizer = sizer
		self.main_items.append(main_sizer.AddSpacer(4))
		# form
		self.build_form_items(main_sizer)
		# geometry line
		self.main_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# geometry title sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.window,
			label='needle geometry',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('file-import-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('import geometry from json file')
		button.Bind(wx.EVT_BUTTON, self.on_geometry_import_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('file-export-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('export geometry to json file')
		button.Bind(wx.EVT_BUTTON, self.on_geometry_export_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# geometry diameter sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.window,
			label='needle diameter (mm)',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		spinctrl = wx.SpinCtrl(
			self.window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=GEOMETRY_DIAMETER_MIN,
			max=GEOMETRY_DIAMETER_MAX,
		)
		spinctrl.Bind(wx.EVT_SPINCTRL, self.on_geometry_diameter_spinctrl_change)
		sizer.Add(spinctrl, flag=wx.ALIGN_CENTER_VERTICAL)
		self.geometry_diameter = spinctrl
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# geometry safezone sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.window,
			label='safety zone radius (mm)',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		spinctrl = wx.SpinCtrl(
			self.window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=GEOMETRY_SAFEZONE_MIN,
			max=GEOMETRY_SAFEZONE_MAX,
		)
		spinctrl.Bind(wx.EVT_SPINCTRL, self.on_geometry_safezone_spinctrl_change)
		sizer.Add(spinctrl, flag=wx.ALIGN_CENTER_VERTICAL)
		self.geometry_safezone = spinctrl
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# drawmode line
		self.main_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# drawmode sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		statictext = wx.StaticText(self.window)
		sizer.Add(statictext, flag=wx.ALIGN_CENTER_VERTICAL)
		self.drawmode_title = statictext
		sizer.AddStretchSpacer()
		self.drawmode_buttons = {
			'none': fa('ban-solid-16'),
			'line': fa('pencil-solid-16'),
			'full': fa('fill-drip-solid-16'),
		}
		for mode, bitmap in self.drawmode_buttons.items():
			sizer.AddSpacer(4)
			button = wx.BitmapToggleButton(
				self.window,
				label=bitmap,
				size=wx.Size(26, 26),
			)
			button.SetToolTip(mode)
			handler = lambda event, mode=mode: \
				self.on_drawmode_button_click(event, mode)
			button.Bind(wx.EVT_TOGGLEBUTTON, handler)
			sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.drawmode_buttons[mode] = button
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# mask line
		self.main_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# mask title sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.window,
			label='mask list',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('plus-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('insert selected overlay to mask list')
		button.Bind(wx.EVT_BUTTON, self.on_mask_insert_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.main_items.append(main_sizer.AddSpacer(4))
		# mask list sizer
		sizer = wx.FlexGridSizer(4, 4, 4)
		sizer.SetFlexibleDirection(wx.HORIZONTAL)
		sizer.AddGrowableCol(1)
		self.main_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.mask_sizer = sizer
		self.main_items.append(main_sizer.AddSpacer(4))

	def build_form_items(self, main_sizer):
		self.form_items = []
		# form line
		self.form_items.append(main_sizer.Add(wx.StaticLine(self.window), flag=wx.EXPAND))
		self.form_items.append(main_sizer.AddSpacer(4))
		# form title sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		statictext = wx.StaticText(
			self.window,
			label='item',
		)
		sizer.Add(statictext, flag=wx.ALIGN_CENTER_VERTICAL)
		self.form_title = statictext
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('floppy-disk-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('submit')
		button.Bind(wx.EVT_BUTTON, self.on_needle_submit_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.form_submit = button
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.window,
			bitmap=fa('ban-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('cancel')
		button.Bind(wx.EVT_BUTTON, self.on_needle_cancel_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.form_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.form_items.append(main_sizer.AddSpacer(4))
		# form table sizer
		table_sizer = wx.FlexGridSizer(3, 4, 4)
		table_sizer.SetFlexibleDirection(wx.HORIZONTAL)
		table_sizer.AddGrowableCol(1)
		self.form_items.append(main_sizer.Add(table_sizer, flag=wx.EXPAND))
		self.form_items.append(main_sizer.AddSpacer(4))
		self.form_coordinates = {
			'entry': [],
			'target': [],
		}
		self.form_buttons = {
			'entry': None,
			'target': None,
		}
		for which in ['entry', 'target']:
			# text
			table_sizer.Add(wx.StaticText(
				self.window,
				label=which,
				size=wx.Size(40, 16),
			), flag=wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(4, 1, 1)
			text_ctrl_list = []
			for d in range(3):
				textctrl = wx.TextCtrl(
					self.window,
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				)
				sizer.Add(textctrl, flag=wx.ALIGN_CENTER_VERTICAL)
				self.form_coordinates[which].append(textctrl)
			self.form_coordinates[which] = tuple(self.form_coordinates[which])
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('crosshairs-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('view {:s}'.format(which))
			handler = lambda event, which=which: \
				self.on_needle_view_button_click(event, 0, which)
			button.Bind(wx.EVT_BUTTON, handler)
			sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.form_buttons[which] = button
			table_sizer.Add(sizer, flag=wx.ALIGN_CENTER_VERTICAL)
			# mark button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('check-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('mark {:s}'.format(which))
			handler = lambda event, which=which: \
				self.on_needle_mark_button_click(event, which)
			button.Bind(wx.EVT_BUTTON, handler)
			table_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		# form slider
		slider = wx.Slider(self.window)
		slider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.on_needle_slider_scroll)
		slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_needle_slider_scroll)
		self.form_items.append(main_sizer.Add(slider, flag=wx.EXPAND))
		self.form_slider = slider
		self.form_items.append(main_sizer.AddSpacer(4))

	def destroy(self):
		debug('destroying panel', mode='info')
		self.overlayList.removeListener('overlays', self.name)
		super().destroy()

	def start_show(self):
		assert self.instance is None
		for item in self.init_items:
			item.Show(True)

	def start_hide(self):
		assert self.instance is not None
		assert self.instance['form'] is None
		for item in self.init_items:
			item.Show(False)

	def instance_show(self):
		assert self.instance is not None
		assert self.instance['form'] is None
		for item in self.main_items:
			item.Show(True)
		self.needle_sizer_refresh()
		self.geometry_diameter.SetValue(self.instance['geometry_diameter'])
		self.geometry_safezone.SetValue(self.instance['geometry_safezone'])
		self.on_drawmode_button_click(None, 'line')

	def instance_hide(self):
		assert self.instance is None
		for item in self.main_items:
			item.Show(False)
		self.needle_sizer.Clear(True)
		self.mask_sizer.Clear(True)

	def needle_sizer_refresh(self):
		assert self.instance is not None
		assert self.instance['form'] is None
		self.needle_sizer.Clear(True)
		self.instance['buttons']['update'].clear()
		self.instance['buttons']['clone'].clear()
		self.instance['buttons']['delete'].clear()
		for i, needle in enumerate(self.instance['needles']):
			index = i + 1
			# index text
			self.needle_sizer.Add(wx.StaticText(
				self.window,
				label='#{:d}'.format(index),
				size=wx.Size(40, 16),
			), flag=wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(4, 1, 1)
			for which, point in needle.items():
				for x in point:
					sizer.Add(wx.TextCtrl(
						self.window,
						value='{:.0f}'.format(x),
						size=wx.Size(30, 24),
						style=wx.TE_READONLY|wx.TE_RIGHT,
					), flag=wx.ALIGN_CENTER_VERTICAL)
				button = wx.BitmapButton(
					self.window,
					bitmap=fa('crosshairs-solid-16'),
					size=wx.Size(26, 26),
				)
				button.SetToolTip('focus')
				handler = lambda event, index=index, which=which: \
					self.on_needle_view_button_click(event, index, which)
				button.Bind(wx.EVT_BUTTON, handler)
				sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.needle_sizer.Add(sizer)
			# update button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('pen-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('update needle #{:d}'.format(index))
			handler = lambda event, index=index: \
				self.on_needle_update_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.needle_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['buttons']['update'].append(button)
			# clone button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('copy-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('clone needle #{:d}'.format(index))
			handler = lambda event, index=index: \
				self.on_needle_insert_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.needle_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['buttons']['clone'].append(button)
			# delete button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('minus-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove needle #{:d}'.format(index))
			handler = lambda event, index=index: \
				self.on_needle_delete_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.needle_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['buttons']['delete'].append(button)

	def needle_list_enable(self):
		assert self.instance is not None
		assert self.instance['form'] is None
		self.form_insert.Enable()
		for buttons in self.instance['buttons'].values():
			for button in buttons:
				button.Enable()

	def needle_list_disable(self):
		assert self.instance is not None
		assert self.instance['form'] is not None
		self.form_insert.Disable()
		for buttons in self.instance['buttons'].values():
			for button in buttons:
				button.Disable()

	def form_show(self):
		assert self.instance is not None
		assert self.instance['form'] is not None
		for item in self.form_items:
			item.Show(True)
		index = self.instance['form']['index']
		if index > 0:
			self.form_title.SetLabel('update needle #{:d}'.format(index))
		else:
			self.form_title.SetLabel('insert needle')
		self.form_refresh()

	def form_hide(self):
		assert self.instance is None or self.instance['form'] is None
		for item in self.form_items:
			item.Show(False)
		self.form_title.SetLabel('')

	def form_refresh(self):
		assert self.instance is not None
		assert self.instance['form'] is not None
		for which in ['entry', 'target']:
			point = self.instance['form']['point'][which]
			coordinates = self.form_coordinates[which]
			button = self.form_buttons[which]
			if point is not None:
				values = ['{:.0f}'.format(x) for x in point]
			else:
				values = [''] * len(coordinates)
			for value, textctrl in zip(values, coordinates):
				textctrl.SetValue(value)
			button.Enable(point is not None)
		enable = all(
			point is not None
			for point in self.instance['form']['point'].values()
		)
		self.form_submit.Enable(enable)
		self.form_slider.Enable(enable)

	def mask_sizer_refresh(self):
		assert self.instance is not None
		self.instance['mask_bitmaps'].clear()
		self.mask_sizer.Clear(True)
		for overlay in self.instance['mask_overlays']:
			# bitmap
			staticbitmap = wx.StaticBitmap(
				self.window,
				size=wx.Size(26, 26),
			)
			self.mask_overlay_bitmap(overlay, staticbitmap)
			self.mask_sizer.Add(staticbitmap, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['mask_bitmaps'].append(staticbitmap)
			# name text
			sizer = wx.BoxSizer(wx.HORIZONTAL)
			self.mask_sizer.Add(sizer, flag=wx.EXPAND)
			statictext = wx.StaticText(
				self.window,
				label=overlay.name,
				style=wx.ST_ELLIPSIZE_MIDDLE,
			)
			statictext.SetToolTip(overlay.name)
			sizer.Add(statictext, 1, flag=wx.ALIGN_CENTER_VERTICAL)
			# select button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('arrow-pointer-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('select overlay')
			handler = lambda event, overlay=overlay: \
				self.on_mask_select_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			# remove button
			button = wx.BitmapButton(
				self.window,
				bitmap=fa('minus-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove overlay from mask list')
			handler = lambda event, overlay=overlay: \
				self.on_mask_remove_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)

	def mask_overlay_bitmap(self, overlay, staticbitmap):
		icon = 'circle-check-solid-16'
		if self.instance['mask_array'] is not None:
			if numpy.any(overlay.data * self.instance['mask_array']):
				icon = 'triangle-exclamation-solid-16'
		staticbitmap.SetBitmap(fa(icon))

	def layout(self):
		self.GetSizer().Layout()

	def draw(self, force=False):
		debug('draw', mode='info')
		assert self.instance is not None
		if self.instance['drawmode'] == 'none' and not force:
			return
		image = self.instance['image']
		data = numpy.zeros(image.shape, dtype=int)
		if self.instance['drawmode'] in ['line', 'full']:
			needles = self.instance['needles'].copy()
			if self.instance['form'] is not None and self.instance['form']['dirty']:
				assert all(
					point is not None
					for point in self.instance['form']['point'].values()
				)
				needles.append(self.instance['form']['point'])
			self.instance['mask_array'] = numpy.zeros(image.shape, dtype=bool)
			for i, needle in enumerate(needles):
				index = i + 1
				mask_pass = True
				if self.instance['form'] is not None and self.instance['form']['dirty'] and self.instance['form']['index'] == index:
					mask_pass = False
				mask = self.pair2mask(needle['entry'], needle['target']) # 40ms/loop
				if self.instance['drawmode'] == 'line':
					data[mask] = index
					if mask_pass:
						self.instance['mask_array'][mask] = True
				elif self.instance['drawmode'] == 'full':
					mask = edt(
						mask,
						max(
							self.instance['geometry_diameter'] / 2,
							self.instance['geometry_safezone'],
						) + 1e-6,
						self.instance['image'].pixdim,
						box=True,
					) # 1200ms/loop; with box: 50ms/loop
					# TODO is image.pixdim in mm?
					sz1 = mask > self.instance['geometry_safezone'] - GEOMETRY_BORDER
					sz2 = mask <= self.instance['geometry_safezone']
					data[sz1 * sz2] = 10 * index + 1 # 20ms/loop
					dm2 = mask <= self.instance['geometry_diameter'] / 2
					data[dm2] = 10 * index # 10ms/loop
					if mask_pass:
						self.instance['mask_array'][sz2] = True
		else:
			self.instance['mask_array'] = None
		image[:] = data[:] # 300ms
		for overlay, staticbitmap in zip(self.instance['mask_overlays'], self.instance['mask_bitmaps']):
			self.mask_overlay_bitmap(overlay, staticbitmap)

	def pair2mask(self, entry_xyz, target_xyz):
		assert self.instance is not None
		image = self.instance['image']
		mask = numpy.zeros(image.shape, dtype=bool)
		vector_xyz = numpy.asarray(target_xyz) - numpy.asarray(entry_xyz)
		num = numpy.dot(numpy.abs(vector_xyz), numpy.reciprocal(image.pixdim))
		num = round(num) + 1
		debug('count', num)
		for t in numpy.linspace(0, 1, num):
			point_xyz = numpy.average([entry_xyz, target_xyz], 0, [1-t, t])
			point_ijk = self.world2voxel(point_xyz)
			mask[point_ijk] = True
		return mask

	def reset(self):
		self.instance = None
		self.start_show()
		self.instance_hide()
		self.form_hide()
		self.layout()

	def on_instance_load_button_click(self, event, load):
		debug('load' if load else 'new', mode='info')
		assert self.instance is None
		assert type(load) is bool
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		path = None
		if load:
			with wx.FileDialog(
				self,
				self.title(),
				wildcard='JSON files (.json)|*.json',
				style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST,
			) as file_dialog:
				if file_dialog.ShowModal() == wx.ID_CANCEL:
					return
				path = file_dialog.GetPath()
			try:
				with open(path, 'r') as fp:
					instance = json.load(fp)
				assert type(instance) is dict
				assert 'needles' in instance and type(instance['needles']) is list
				for needle in instance['needles']:
					assert type(needle) is dict
					for which in ['entry', 'target']:
						assert which in needle and type(needle[which]) is list
						assert len(needle[which]) == 3
						assert all(type(value) is float for value in needle[which])
				assert 'diameter' in instance and type(instance['diameter']) is int
				assert instance['diameter'] >= GEOMETRY_DIAMETER_MIN
				assert instance['diameter'] <= GEOMETRY_DIAMETER_MAX
				assert 'safezone' in instance and type(instance['safezone']) is int
				assert instance['safezone'] >= GEOMETRY_SAFEZONE_MIN
				assert instance['safezone'] <= GEOMETRY_SAFEZONE_MAX
				assert instance['diameter'] <= 2 * instance['safezone']
			except IOError as error:
				wx.MessageBox(
					str(error),
					self.title(),
					wx.OK|wx.ICON_ERROR,
				)
				return
			except json.JSONDecodeError as error:
				wx.MessageBox(
					str(error),
					self.title(),
					wx.OK|wx.ICON_ERROR,
				)
				return
			except AssertionError:
				wx.MessageBox(
					'Input file should have compatible content.',
					self.title(),
					wx.OK|wx.ICON_ERROR,
				)
				return
		else:
			instance = {
				'needles': [],
				'diameter': GEOMETRY_DIAMETER_DEF,
				'safezone': GEOMETRY_SAFEZONE_DEF,
			}
		nibimage = overlay.nibImage
		xyzt_units = nibimage.header.get_xyzt_units()
		image = fsleyes.actions.newimage.newImage(
			nibimage.shape,
			nibimage.header.get_zooms(),
			int,
			nibimage.affine,
			xyzt_units[0],
			xyzt_units[1],
			name='{:s}-ablation'.format(overlay.name),
		)
		self.overlayList.append(image)
		self.displayCtx.selectOverlay(image)
		self.instance = {
			'path': path,
			'image': image,
			'needles': [{
				'entry': tuple(needle['entry']),
				'target': tuple(needle['target']),
			} for needle in instance['needles']],
			'buttons': {
				'update': [],
				'clone': [],
				'delete': [],
			},
			'form': None,
			'geometry_diameter': instance['diameter'],
			'geometry_safezone': instance['safezone'],
			'drawmode': None,
			'mask_array': None,
			'mask_overlays': [],
			'mask_bitmaps': [],
		}
		self.start_hide()
		self.instance_show()
		self.layout()
		self.draw()

	def on_instance_save_button_click(self, event):
		debug('save', mode='info')
		assert self.instance is not None
		path = None
		with wx.FileDialog(
			self,
			self.title(),
			wildcard='JSON files (.json)|*.json',
			style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
		) as file_dialog:
			if self.instance['path'] is not None:
				file_dialog.SetPath(self.instance['path'])
			if file_dialog.ShowModal() == wx.ID_CANCEL:
				return
			path = file_dialog.GetPath()
		instance = {
			'needles': self.instance['needles'],
			'diameter': self.instance['geometry_diameter'],
			'safezone': self.instance['geometry_safezone'],
		}
		try:
			with open(path, 'w') as fp:
				json.dump(instance, fp, indent='\t')
				fp.write('\n')
		except IOError as error:
			wx.MessageBox(
				str(error),
				self.title(),
				wx.OK|wx.ICON_ERROR,
			)
			return
		wx.MessageBox(
			'File saved successfully.',
			self.title(),
			wx.OK|wx.ICON_INFORMATION,
		)

	def on_instance_close_button_click(self, event):
		debug('close', mode='info')
		assert self.instance is not None
		if fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, self.instance['image']):
			self.reset()

	def on_needle_insert_button_click(self, event, index):
		debug('insert', index, mode='info')
		assert self.instance is not None
		assert self.instance['form'] is None
		if index == 0:
			point = {
				'entry': None,
				'target': None,
			}
		else:
			assert index - 1 in range(len(self.instance['needles']))
			point = self.instance['needles'][index - 1].copy()
		self.instance['form'] = {
			'index': 0,
			'point': point,
			'dirty': False,
		}
		self.needle_list_disable()
		self.form_show()
		self.layout()

	def on_needle_update_button_click(self, event, index):
		debug('update', index, mode='info')
		assert self.instance is not None
		assert self.instance['form'] is None
		assert index - 1 in range(len(self.instance['needles']))
		self.instance['form'] = {
			'index': index,
			'point': self.instance['needles'][index - 1].copy(),
			'dirty': False,
		}
		self.needle_list_disable()
		self.form_show()
		self.layout()

	def on_needle_delete_button_click(self, event, index):
		debug('delete', index, mode='info')
		assert self.instance is not None
		assert self.instance['form'] is None
		assert index - 1 in range(len(self.instance['needles']))
		self.instance['needles'].pop(index - 1)
		self.needle_sizer_refresh()
		self.layout()
		self.draw()

	def on_needle_view_button_click(self, event, index, which):
		debug('view', index, which, mode='info')
		assert self.instance is not None
		assert which in ['entry', 'target']
		if index == 0:
			assert self.instance['form'] is not None
			self.displayCtx.worldLocation.xyz = self.instance['form']['point'][which]
			if which == 'entry':
				value = self.form_slider.GetMin()
			else:
				value = self.form_slider.GetMax()
			self.form_slider.SetValue(value)
		else:
			assert index - 1 in range(len(self.instance['needles']))
			self.displayCtx.worldLocation.xyz = self.instance['needles'][index - 1][which]

	def on_needle_mark_button_click(self, event, which):
		debug('mark', which, mode='info')
		assert self.instance is not None
		assert self.instance['form'] is not None
		assert which in ['entry', 'target']
		self.instance['form']['point'][which] = tuple(self.displayCtx.worldLocation.xyz)
		if which == 'entry':
			value = self.form_slider.GetMin()
		else:
			value = self.form_slider.GetMax()
		self.form_slider.SetValue(value)
		if all(point is not None for point in self.instance['form']['point'].values()):
			self.instance['form']['dirty'] = True
		self.form_refresh()
		if self.instance['form']['dirty']:
			self.draw()

	def on_needle_slider_scroll(self, event):
		debug('slide', event.GetEventType(), event.GetPosition(), mode='info')
		assert self.instance is not None
		assert self.instance['form'] is not None
		assert all(point is not None for point in self.instance['form']['point'].values())
		entry, target = tuple(self.instance['form']['point'].values())
		slider = self.form_slider
		t = (slider.GetValue() - slider.GetMin()) / (slider.GetMax() - slider.GetMin())
		point = numpy.average([entry, target], 0, [1-t, t])
		self.displayCtx.worldLocation.xyz = tuple(point)

	def on_needle_submit_button_click(self, event):
		debug('submit', mode='info')
		assert self.instance is not None
		assert self.instance['form'] is not None
		assert all(point is not None for point in self.instance['form']['point'].values())
		if numpy.allclose(*tuple(self.instance['form']['point'].values())):
			wx.MessageBox(
				'Entry and target points should differ.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if self.instance['form']['index'] > 0:
			self.instance['needles'][self.instance['form']['index'] - 1] = self.instance['form']['point']
		else:
			self.instance['needles'].append(self.instance['form']['point'])
		self.instance['form'] = None
		self.needle_sizer_refresh()
		self.needle_list_enable()
		self.form_hide()
		self.layout()
		self.draw()

	def on_needle_cancel_button_click(self, event):
		debug('cancel', mode='info')
		assert self.instance is not None
		assert self.instance['form'] is not None
		dirty = self.instance['form']['dirty']
		self.instance['form'] = None
		self.needle_list_enable()
		self.form_hide()
		self.layout()
		if dirty:
			self.draw()

	def on_geometry_import_button_click(self, event):
		debug('geometry import', mode='info')
		assert self.instance is not None
		path = None
		with wx.FileDialog(
			self,
			self.title(),
			wildcard='JSON files (.json)|*.json',
			style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST,
		) as file_dialog:
			if file_dialog.ShowModal() == wx.ID_CANCEL:
				return
			path = file_dialog.GetPath()
		try:
			with open(path, 'r') as fp:
				geometry = json.load(fp)
			assert type(geometry) is dict
			assert 'diameter' in geometry and type(geometry['diameter']) is int
			assert geometry['diameter'] >= GEOMETRY_DIAMETER_MIN
			assert geometry['diameter'] <= GEOMETRY_DIAMETER_MAX
			assert 'safezone' in geometry and type(geometry['safezone']) is int
			assert geometry['safezone'] >= GEOMETRY_SAFEZONE_MIN
			assert geometry['safezone'] <= GEOMETRY_SAFEZONE_MAX
			assert geometry['diameter'] <= 2 * geometry['safezone']
		except IOError as error:
			wx.MessageBox(
				str(error),
				self.title(),
				wx.OK|wx.ICON_ERROR,
			)
			return
		except json.JSONDecodeError as error:
			wx.MessageBox(
				str(error),
				self.title(),
				wx.OK|wx.ICON_ERROR,
			)
			return
		except AssertionError:
			wx.MessageBox(
				'Input file should have compatible content.',
				self.title(),
				wx.OK|wx.ICON_ERROR,
			)
			return
		self.instance['geometry_diameter'] = geometry['diameter']
		self.instance['geometry_safezone'] = geometry['safezone']
		self.geometry_diameter.SetValue(self.instance['geometry_diameter'])
		self.geometry_safezone.SetValue(self.instance['geometry_safezone'])
		self.draw()

	def on_geometry_export_button_click(self, event):
		debug('geometry export', mode='info')
		assert self.instance is not None
		path = None
		with wx.FileDialog(
			self,
			self.title(),
			defaultFile='geometry.json',
			wildcard='JSON files (.json)|*.json',
			style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT,
		) as file_dialog:
			if file_dialog.ShowModal() == wx.ID_CANCEL:
				return
			path = file_dialog.GetPath()
		geometry = {
			'diameter': self.instance['geometry_diameter'],
			'safezone': self.instance['geometry_safezone'],
		}
		try:
			with open(path, 'w') as fp:
				json.dump(geometry, fp, indent='\t')
				fp.write('\n')
		except IOError as error:
			wx.MessageBox(
				str(error),
				self.title(),
				wx.OK|wx.ICON_ERROR,
			)
			return
		wx.MessageBox(
			'Needle geometry exported successfully.',
			self.title(),
			wx.OK|wx.ICON_INFORMATION,
		)

	def on_geometry_diameter_spinctrl_change(self, event):
		debug('geometry diameter', event.GetPosition(), mode='info')
		assert self.instance is not None
		self.instance['geometry_diameter'] = self.geometry_diameter.GetValue()
		if self.instance['geometry_safezone'] < self.instance['geometry_diameter'] / 2:
			self.instance['geometry_safezone'] = math.ceil(self.instance['geometry_diameter'] / 2)
			self.geometry_safezone.SetValue(self.instance['geometry_safezone'])
		self.draw()

	def on_geometry_safezone_spinctrl_change(self, event):
		debug('geometry safety zone', event.GetPosition(), mode='info')
		assert self.instance is not None
		self.instance['geometry_safezone'] = self.geometry_safezone.GetValue()
		if self.instance['geometry_diameter'] > self.instance['geometry_safezone'] * 2:
			self.instance['geometry_diameter'] = math.floor(self.instance['geometry_safezone'] * 2)
			self.geometry_diameter.SetValue(self.instance['geometry_diameter'])
		self.draw()

	def on_drawmode_button_click(self, event, mode):
		debug('drawmode', mode, mode='info')
		assert self.instance is not None
		assert mode in self.drawmode_buttons
		self.instance['drawmode'] = mode
		self.drawmode_title.SetLabel('draw mode: {:s}'.format(mode))
		for mode, button in self.drawmode_buttons.items():
			if mode == self.instance['drawmode']:
				button.SetValue(True)
				button.Disable()
			else:
				button.SetValue(False)
				button.Enable()
		if event is not None:
			self.draw(force=True)

	def on_mask_insert_button_click(self, event):
		debug('mask append', mode='info')
		assert self.instance is not None
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if overlay in self.instance['mask_overlays']:
			wx.MessageBox(
				'The selected overlay is already in the list.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if overlay.shape != self.instance['image'].shape:
			wx.MessageBox(
				'Selected overlay and base image should have identical shapes.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if not numpy.allclose(overlay.voxToWorldMat, self.instance['image'].voxToWorldMat):
			wx.MessageBox(
				'Selected overlay and base image should have identical affine transformations.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		self.instance['mask_overlays'].append(overlay)
		self.mask_sizer_refresh()
		self.layout()

	def on_mask_remove_button_click(self, event, overlay):
		debug('mask remove', overlay.name, mode='info')
		assert self.instance is not None
		assert overlay in self.instance['mask_overlays']
		self.instance['mask_overlays'].remove(overlay)
		self.mask_sizer_refresh()
		self.layout()

	def on_mask_select_button_click(self, event, overlay):
		debug('mask select', overlay.name, mode='info')
		assert self.instance is not None
		assert overlay in self.instance['mask_overlays']
		overlay = self.displayCtx.selectOverlay(overlay)

	def world2voxel(self, coords):
		assert self.instance is not None
		image = self.instance['image']
		coords = numpy.asarray(coords)
		assert coords.ndim == 1 and coords.size == image.ndim
		opts = self.displayCtx.getOpts(image)
		coords = [coords]
		xformed = opts.transformCoords(coords, 'world', 'voxel', True)
		xformed = xformed[0]
		return tuple(xformed.astype(int))

	def voxel2world(self, coords):
		assert self.instance is not None
		image = self.instance['image']
		coords = numpy.asarray(coords)
		assert coords.ndim == 1 and coords.size == image.ndim
		opts = self.displayCtx.getOpts(image)
		coords = [coords]
		xformed = opts.transformCoords(coords, 'voxel', 'world')
		xformed = xformed[0]
		return tuple(xformed)

	def on_overlay_list_changed(self, *args):
		if self.instance is None:
			return
		if self.instance['image'] not in self.overlayList:
			debug('image has been removed from overlay list', mode='warning')
			self.reset()
			return
		refresh = False
		for overlay in self.instance['mask_overlays']:
			if overlay not in self.overlayList:
				debug('mask has been removed from overlay list', mode='warning')
				self.instance['mask_overlays'].remove(overlay)
				refresh = True
		if refresh:
			self.mask_sizer_refresh()
			self.layout()

	@staticmethod
	def defaultLayout():
		return {
			'location': wx.RIGHT,
		}

	@staticmethod
	def supportedViews():
		return [
			fsleyes.views.orthopanel.OrthoPanel,
		]
