#!/usr/bin/python3


import json
import math

import fsleyes
import numpy
import scipy.ndimage
import wx


print('plugin: ablation')


ABLATION_GEOMETRY_DIAMETER_MIN = 1
ABLATION_GEOMETRY_DIAMETER_MAX = 20
ABLATION_GEOMETRY_DIAMETER_DEF = 3

ABLATION_GEOMETRY_SAFEZONE_MIN = 1
ABLATION_GEOMETRY_SAFEZONE_MAX = 50
ABLATION_GEOMETRY_SAFEZONE_DEF = 15

ABLATION_GEOMETRY_BORDER = 2


def ablation_fa(icon):
	return wx.Bitmap('fontawesome/{:s}.png'.format(icon), wx.BITMAP_TYPE_PNG)

def ablation_box(mask, distance=0., zooms=None):
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

def ablation_edt(mask, distance=1., zooms=None, box=False):
	assert distance >= 0
	if zooms is None:
		zooms = (1,) * mask.ndim
	assert len(zooms) == mask.ndim
	assert all(x > 0 for x in zooms)
	if box:
		box = ablation_box(mask, distance, zooms)
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


class AblationControlPanel(fsleyes.controls.controlpanel.ControlPanel):

	@staticmethod
	def title():
		return 'Ablation'

	def __init__(self, *args, **kwargs):
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
		self.main_window = wx.lib.scrolledpanel.ScrolledPanel(self)
		self.main_window.SetupScrolling()
		home_sizer.Add(self.main_window, 1, flag=wx.EXPAND)
		# horizontal sizer
		horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.main_window.SetSizer(horizontal_sizer)
		# horizontal spacer
		horizontal_sizer.AddSpacer(4)
		# main sizer
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		main_sizer.AddSpacer(4)
		self._init_start_items(main_sizer)
		self._init_instance_items(main_sizer)
		main_sizer.AddSpacer(4)
		horizontal_sizer.Add(main_sizer, 1)
		# horizontal spacer
		horizontal_sizer.AddSpacer(4)
		# reset
		self.reset()

	def _init_start_items(self, main_sizer):
		self.start_items = []
		# top sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('file-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('create needle list')
		handler = lambda event, load=False: self.on_instance_load_button_click(event, load)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('file-import-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('import needle list from json file')
		handler = lambda event, load=True: self.on_instance_load_button_click(event, load)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		self.start_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.start_items.append(main_sizer.AddSpacer(4))
		# link line
		self.start_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.start_items.append(main_sizer.AddSpacer(4))
		# link ctrl
		self.start_items.append(main_sizer.Add(wx.adv.HyperlinkCtrl(
			self.main_window,
			label='GitHub',
			url='https://github.com/constracti/fsleyes-plugin-ablation',
		)))
		self.start_items.append(main_sizer.AddSpacer(4))

	def _init_instance_items(self, main_sizer):
		self.instance_items = []
		# top sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('file-export-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('export needle list to json file')
		button.Bind(wx.EVT_BUTTON, self.on_instance_save_button_click)
		sizer.Add(button)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('xmark-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('close needle list')
		button.Bind(wx.EVT_BUTTON, self.on_instance_close_button_click)
		sizer.Add(button)
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# needle line
		self.instance_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# needle insert sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.main_window,
			label='needle list',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('plus-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('insert needle')
		handler = lambda event: self.on_needle_insert_button_click(event, 0)
		button.Bind(wx.EVT_BUTTON, handler)
		sizer.Add(button)
		self.insert_button = button
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# needle list sizer
		sizer = wx.FlexGridSizer(5, 4, 4)
		sizer.SetFlexibleDirection(wx.HORIZONTAL)
		sizer.AddGrowableCol(1)
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.items_sizer = sizer
		self.instance_items.append(main_sizer.AddSpacer(4))
		# form
		self._init_form_items(main_sizer)
		# geometry line
		self.instance_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# geometry title sizer
		self.geometry = {
			'diameter': None,
			'safezone': None,
		}
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.main_window,
			label='needle geometry',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('file-import-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('import geometry from json file')
		button.Bind(wx.EVT_BUTTON, self.on_geometry_import_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('file-export-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('export geometry to json file')
		button.Bind(wx.EVT_BUTTON, self.on_geometry_export_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# geometry diameter sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.main_window,
			label='needle diameter (mm)',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		spinctrl = wx.SpinCtrl(
			self.main_window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=ABLATION_GEOMETRY_DIAMETER_MIN,
			max=ABLATION_GEOMETRY_DIAMETER_MAX,
		)
		spinctrl.Bind(wx.EVT_SPINCTRL, self.on_geometry_diameter_spinctrl_change)
		sizer.Add(spinctrl, flag=wx.ALIGN_CENTER_VERTICAL)
		self.geometry['diameter'] = spinctrl
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# geometry safezone sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.main_window,
			label='safety zone radius (mm)',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		spinctrl = wx.SpinCtrl(
			self.main_window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=ABLATION_GEOMETRY_SAFEZONE_MIN,
			max=ABLATION_GEOMETRY_SAFEZONE_MAX,
		)
		spinctrl.Bind(wx.EVT_SPINCTRL, self.on_geometry_safezone_spinctrl_change)
		sizer.Add(spinctrl, flag=wx.ALIGN_CENTER_VERTICAL)
		self.geometry['safezone'] = spinctrl
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# draw line
		self.instance_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# draw sizer
		self.drawmode = {
			'value': None,
			'statictext': None,
			'buttons': {
				'none': ablation_fa('ban-solid-16'),
				'line': ablation_fa('pencil-solid-16'),
				'full': ablation_fa('fill-drip-solid-16'),
			},
		}
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		statictext = wx.StaticText(self.main_window)
		sizer.Add(statictext, flag=wx.ALIGN_CENTER_VERTICAL)
		self.drawmode['statictext'] = statictext
		sizer.AddStretchSpacer()
		for mode, bitmap in self.drawmode['buttons'].items():
			sizer.AddSpacer(4)
			button = wx.BitmapToggleButton(
				self.main_window,
				label=bitmap,
				size=wx.Size(26, 26),
			)
			button.SetToolTip(mode)
			handler = lambda event, mode=mode: self.on_drawmode_button_click(event, mode)
			button.Bind(wx.EVT_TOGGLEBUTTON, handler)
			sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.drawmode['buttons'][mode] = button
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# mask line
		self.instance_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# mask insert sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(wx.StaticText(
			self.main_window,
			label='mask list',
		), flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('plus-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('insert selected overlay to mask list')
		button.Bind(wx.EVT_BUTTON, self.on_mask_insert_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.instance_items.append(main_sizer.AddSpacer(4))
		# mask list sizer
		sizer = wx.FlexGridSizer(3, 4, 4)
		sizer.SetFlexibleDirection(wx.HORIZONTAL)
		sizer.AddGrowableCol(0)
		self.instance_items.append(main_sizer.Add(sizer, flag=wx.EXPAND))
		self.mask_sizer = sizer
		self.instance_items.append(main_sizer.AddSpacer(4))

	def _init_form_items(self, main_sizer):
		self.form_items = []
		# form line
		self.form_items.append(main_sizer.Add(wx.StaticLine(self.main_window), flag=wx.EXPAND))
		self.form_items.append(main_sizer.AddSpacer(4))
		# form title sizer
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		form_text = wx.StaticText(
			self.main_window,
			label='item',
		)
		self.form_text = form_text
		sizer.Add(form_text, flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.AddStretchSpacer()
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('floppy-disk-solid-16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('submit')
		button.Bind(wx.EVT_BUTTON, self.on_needle_submit_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.submit_button = button
		sizer.AddSpacer(4)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=ablation_fa('ban-solid-16'),
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
		self.form = {
			'coords_text': [],
			'view_button': [],
		}
		for which in ['entry', 'target']:
			# text
			table_sizer.Add(wx.StaticText(
				self.main_window,
				label=which,
				size=wx.Size(40, 16),
			), flag=wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(4, 1, 1)
			text_ctrl_list = []
			for x in range(3):
				text_ctrl = wx.TextCtrl(
					self.main_window,
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				)
				sizer.Add(text_ctrl, flag=wx.ALIGN_CENTER_VERTICAL)
				text_ctrl_list.append(text_ctrl)
			self.form['coords_text'].append(text_ctrl_list)
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('crosshairs-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('view {:s}'.format(which))
			handler = lambda event, which=which: self.on_needle_view_button_click(event, 0, which)
			button.Bind(wx.EVT_BUTTON, handler)
			sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.form['view_button'].append(button)
			table_sizer.Add(sizer, flag=wx.ALIGN_CENTER_VERTICAL)
			# mark button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('check-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('mark {:s}'.format(which))
			handler = lambda event, which=which: self.on_needle_mark_button_click(event, which)
			button.Bind(wx.EVT_BUTTON, handler)
			table_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		self.form['coords_text'] = tuple(self.form['coords_text'])
		self.form['view_button'] = tuple(self.form['view_button'])
		# form slider
		slider = wx.Slider(self.main_window)
		slider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.on_needle_slider_scroll)
		slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_needle_slider_scroll)
		self.form_items.append(main_sizer.Add(slider, flag=wx.EXPAND))
		self.needle_slider = slider
		self.form_items.append(main_sizer.AddSpacer(4))

	def destroy(self):
		self.overlayList.removeListener('overlays', self.name)
		super().destroy()

	def start_show(self):
		assert self.instance is None
		for item in self.start_items:
			item.Show(True)

	def start_hide(self):
		assert self.instance is not None
		for item in self.start_items:
			item.Show(False)

	def instance_show(self):
		assert self.instance is not None
		for item in self.instance_items:
			item.Show(True)
		self.needle_list_refresh()
		self.on_drawmode_button_click(None, 'line')

	def instance_hide(self):
		assert self.instance is None
		for item in self.instance_items:
			item.Show(False)
		self.items_sizer.Clear(True)
		self.mask_sizer.Clear(True)

	def needle_list_refresh(self):
		assert self.instance is not None
		self.items_sizer.Clear(True)
		self.instance['update_button'] = []
		self.instance['clone_button'] = []
		self.instance['delete_button'] = []
		for i, (entry_xyz, target_xyz) in enumerate(self.instance['items']):
			index = i + 1
			# index text
			self.items_sizer.Add(wx.StaticText(
				self.main_window,
				label='#{:d}'.format(index),
				size=wx.Size(40, 16),
			), flag=wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(4, 1, 1)
			coords_dict = {
				'entry': entry_xyz,
				'target': target_xyz,
			}
			for which, point_xyz in coords_dict.items():
				for value in point_xyz:
					sizer.Add(wx.TextCtrl(
						self.main_window,
						value='{:.0f}'.format(value),
						size=wx.Size(30, 24),
						style=wx.TE_READONLY|wx.TE_RIGHT,
					), flag=wx.ALIGN_CENTER_VERTICAL)
				button = wx.BitmapButton(
					self.main_window,
					bitmap=ablation_fa('crosshairs-solid-16'),
					size=wx.Size(26, 26),
				)
				button.SetToolTip('focus')
				handler = lambda event, index=index, which=which: self.on_needle_view_button_click(event, index, which)
				button.Bind(wx.EVT_BUTTON, handler)
				sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.items_sizer.Add(sizer)
			# update button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('pen-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('update needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_needle_update_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['update_button'].append(button)
			# clone button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('copy-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('clone needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_needle_insert_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['clone_button'].append(button)
			# delete button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('minus-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_needle_delete_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['delete_button'].append(button)

	def needle_list_enable(self):
		assert self.instance is not None
		assert self.index is None
		self.insert_button.Enable()
		for update_button in self.instance['update_button']:
			update_button.Enable()
		for clone_button in self.instance['clone_button']:
			clone_button.Enable()
		for delete_button in self.instance['delete_button']:
			delete_button.Enable()

	def needle_list_disable(self):
		assert self.instance is not None
		assert self.index is not None
		self.insert_button.Disable()
		for update_button in self.instance['update_button']:
			update_button.Disable()
		for clone_button in self.instance['clone_button']:
			clone_button.Disable()
		for delete_button in self.instance['delete_button']:
			delete_button.Disable()

	def form_show(self):
		assert self.instance is not None
		assert self.index is not None
		for item in self.form_items:
			item.Show(True)
		if self.index > 0:
			self.form_text.SetLabel('update needle #{:d}'.format(self.index))
		else:
			self.form_text.SetLabel('insert needle')
		self.form_refresh()

	def form_hide(self):
		assert self.instance is None or self.index is None
		for item in self.form_items:
			item.Show(False)
		self.form_text.SetLabel('')

	def form_refresh(self):
		assert self.instance is not None
		assert self.index is not None
		for point_xyz, coords_text, view_button in zip(self.form['point_xyz'], self.form['coords_text'], self.form['view_button']):
			if point_xyz is not None:
				values = ['{:.0f}'.format(v) for v in point_xyz]
			else:
				values = [''] * len(coords_text)
			for v, text_ctrl in zip(values, coords_text):
				text_ctrl.SetValue(v)
			view_button.Enable(point_xyz is not None)
		enable = all(point_xyz is not None for point_xyz in self.form['point_xyz'])
		self.submit_button.Enable(enable)
		self.needle_slider.Enable(enable)

	def mask_sizer_refresh(self):
		assert self.instance is not None
		self.mask_sizer.Clear(True)
		for overlay in self.instance['mask_list']:
			# name text
			sizer = wx.BoxSizer(wx.HORIZONTAL)
			self.mask_sizer.Add(sizer, flag=wx.EXPAND)
			statictext = wx.StaticText(
				self.main_window,
				label=overlay.name,
				style=wx.ST_ELLIPSIZE_MIDDLE,
			)
			statictext.SetToolTip(overlay.name)
			sizer.Add(statictext, 1, flag=wx.ALIGN_CENTER_VERTICAL)
			# select button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('arrow-pointer-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('select overlay')
			handler = lambda event, overlay=overlay: self.on_mask_select_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			# remove button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=ablation_fa('minus-solid-16'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove overlay from mask list')
			handler = lambda event, overlay=overlay: self.on_mask_remove_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)

	def layout(self):
		self.GetSizer().Layout()

	def draw(self, force=False):
		print('draw')
		assert self.instance is not None
		if self.drawmode['value'] == 'none' and not force:
			return
		image = self.instance['image']
		data = numpy.zeros(image.shape, dtype=int)
		if self.drawmode['value'] in ['line', 'full']:
			needles = self.instance['items'].copy()
			if self.instance['form_is_dirty']:
				assert self.index is not None
				assert all(point_xyz is not None for point_xyz in self.form['point_xyz'])
				needles.append(tuple(self.form['point_xyz']))
			for i, (entry_xyz, target_xyz) in enumerate(needles):
				index = i + 1
				from time import time
				t = time()
				mask = self.pair2mask(entry_xyz, target_xyz) # 40ms/loop
				print('msk', time() - t)
				if self.drawmode['value'] == 'line':
					data[mask] = index
				elif self.drawmode['value'] == 'full':
					t = time()
					mask = ablation_edt(
						mask,
						max(
							self.geometry['diameter'].GetValue() / 2,
							self.geometry['safezone'].GetValue(),
						) + 1e-6,
						self.instance['image'].pixdim,
						box=True,
					) # 1200ms/loop; with box: 50ms/loop
					print('edt', time() - t)
					# TODO is image.pixdim in mm?
					data[(mask > self.geometry['safezone'].GetValue() - ABLATION_GEOMETRY_BORDER) * (mask <= self.geometry['safezone'].GetValue())] = 10 * index + 1 # 20ms/loop
					print('sfz', time() - t)
					data[mask <= self.geometry['diameter'].GetValue() / 2] = 10 * index # 10ms/loop
					print('dmt', time() - t)
		image[:] = data[:] # 300ms

	def pair2mask(self, entry_xyz, target_xyz):
		assert self.instance is not None
		image = self.instance['image']
		mask = numpy.zeros(image.shape, dtype=bool)
		vector_xyz = numpy.asarray(target_xyz) - numpy.asarray(entry_xyz)
		num = numpy.dot(numpy.abs(vector_xyz), numpy.reciprocal(image.pixdim)).round().astype(int)
		print('entry', entry_xyz)
		print('target', target_xyz)
		print('count', num)
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
		print('load' if load else 'new')
		assert self.instance is None
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
				assert instance['diameter'] >= ABLATION_GEOMETRY_DIAMETER_MIN
				assert instance['diameter'] <= ABLATION_GEOMETRY_DIAMETER_MAX
				assert 'safezone' in instance and type(instance['safezone']) is int
				assert instance['safezone'] >= ABLATION_GEOMETRY_SAFEZONE_MIN
				assert instance['safezone'] <= ABLATION_GEOMETRY_SAFEZONE_MAX
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
				'diameter': ABLATION_GEOMETRY_DIAMETER_DEF,
				'safezone': ABLATION_GEOMETRY_SAFEZONE_DEF,
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
			'items': [(tuple(needle['entry']), tuple(needle['target'])) for needle in instance['needles']],
			'form_is_dirty': False,
			'mask_list': [],
		}
		self.geometry['diameter'].SetValue(instance['diameter'])
		self.geometry['safezone'].SetValue(instance['safezone'])
		self.index = None
		self.start_hide()
		self.instance_show()
		self.layout()
		self.draw()

	def on_instance_save_button_click(self, event):
		print('save')
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
			'needles': [{
				'entry': list(needle[0]),
				'target': list(needle[1]),
			} for needle in self.instance['items']],
			'diameter': self.geometry['diameter'].GetValue(),
			'safezone': self.geometry['safezone'].GetValue(),
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
		print('close')
		assert self.instance is not None
		instance = self.instance
		self.instance = None
		if fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, instance['image']):
			self.reset()
		else:
			self.instance = instance

	def on_needle_insert_button_click(self, event, index):
		print('insert', index)
		assert self.instance is not None
		assert self.index is None
		if index == 0:
			self.form['point_xyz'] = [None, None]
		else:
			assert index - 1 in range(len(self.instance['items']))
			self.form['point_xyz'] = list(self.instance['items'][index - 1])
		self.index = 0
		self.needle_list_disable()
		self.form_show()
		self.layout()

	def on_needle_update_button_click(self, event, index):
		print('update', index)
		assert self.instance is not None
		assert self.index is None
		self.index = index
		self.form['point_xyz'] = list(self.instance['items'][index - 1])
		self.needle_list_disable()
		self.form_show()
		self.layout()

	def on_needle_delete_button_click(self, event, index):
		print('delete', index)
		assert self.instance is not None
		assert self.index is None
		self.instance['items'].pop(index - 1)
		self.needle_list_refresh()
		self.layout()
		self.draw()

	def on_needle_view_button_click(self, event, index, which):
		print('view', index, which)
		assert self.instance is not None
		if index == 0:
			assert self.index is not None
			if which == 'entry':
				assert self.form['point_xyz'][0] is not None
				self.displayCtx.worldLocation.xyz = self.form['point_xyz'][0]
				self.needle_slider.SetValue(self.needle_slider.GetMin())
			elif which == 'target':
				assert self.form['point_xyz'][1] is not None
				self.displayCtx.worldLocation.xyz = self.form['point_xyz'][1]
				self.needle_slider.SetValue(self.needle_slider.GetMax())
			else:
				assert False
		else:
			assert index - 1 in range(len(self.instance['items']))
			if which == 'entry':
				self.displayCtx.worldLocation.xyz = self.instance['items'][index - 1][0]
			elif which == 'target':
				self.displayCtx.worldLocation.xyz = self.instance['items'][index - 1][1]
			else:
				assert False

	def on_needle_mark_button_click(self, event, which):
		print('mark', which)
		assert self.instance is not None
		assert self.index is not None
		if which == 'entry':
			self.form['point_xyz'][0] = tuple(self.displayCtx.worldLocation.xyz)
			self.needle_slider.SetValue(self.needle_slider.GetMin())
		elif which == 'target':
			self.form['point_xyz'][1] = tuple(self.displayCtx.worldLocation.xyz)
			self.needle_slider.SetValue(self.needle_slider.GetMax())
		else:
			assert False
		if all(point_xyz is not None for point_xyz in self.form['point_xyz']):
			self.instance['form_is_dirty'] = True
		self.form_refresh()
		if self.instance['form_is_dirty']:
			self.draw()

	def on_needle_slider_scroll(self, event):
		print('pair', event.GetEventType(), event.GetPosition())
		assert self.instance is not None
		assert self.index is not None
		entry_xyz, target_xyz = tuple(self.form['point_xyz'])
		assert entry_xyz is not None and target_xyz is not None
		slider = self.needle_slider
		t = (slider.GetValue() - slider.GetMin()) / (slider.GetMax() - slider.GetMin())
		point_xyz = numpy.average([entry_xyz, target_xyz], 0, [1-t, t])
		self.displayCtx.worldLocation.xyz = tuple(point_xyz)

	def on_needle_submit_button_click(self, event):
		print('submit')
		assert self.instance is not None
		assert self.index is not None
		entry_xyz, target_xyz = tuple(self.form['point_xyz'])
		assert entry_xyz is not None and target_xyz is not None
		if numpy.allclose(entry_xyz, target_xyz):
			wx.MessageBox(
				'Entry and target points should differ.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if self.index > 0:
			self.instance['items'][self.index - 1] = (entry_xyz, target_xyz)
		else:
			self.instance['items'].append((entry_xyz, target_xyz))
		self.index = None
		self.needle_list_refresh()
		self.needle_list_enable()
		self.form_hide()
		self.layout()
		self.instance['form_is_dirty'] = False
		self.draw()

	def on_needle_cancel_button_click(self, event):
		print('cancel')
		assert self.instance is not None
		assert self.index is not None
		self.index = None
		self.needle_list_enable()
		self.form_hide()
		self.layout()
		if self.instance['form_is_dirty']:
			self.instance['form_is_dirty'] = False
			self.draw()

	def on_geometry_import_button_click(self, event):
		print('geometry import')
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
			assert geometry['diameter'] >= ABLATION_GEOMETRY_DIAMETER_MIN
			assert geometry['diameter'] <= ABLATION_GEOMETRY_DIAMETER_MAX
			assert 'safezone' in geometry and type(geometry['safezone']) is int
			assert geometry['safezone'] >= ABLATION_GEOMETRY_SAFEZONE_MIN
			assert geometry['safezone'] <= ABLATION_GEOMETRY_SAFEZONE_MAX
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
		self.geometry['diameter'].SetValue(geometry['diameter'])
		self.geometry['safezone'].SetValue(geometry['safezone'])
		self.draw()

	def on_geometry_export_button_click(self, event):
		print('geometry export')
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
			'diameter': self.geometry['diameter'].GetValue(),
			'safezone': self.geometry['safezone'].GetValue(),
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
		print('geometry diameter', event.GetPosition())
		assert self.instance is not None
		if self.geometry['safezone'].GetValue() < self.geometry['diameter'].GetValue() / 2:
			self.geometry['safezone'].SetValue(math.ceil(self.geometry['diameter'].GetValue() / 2))
		self.draw()

	def on_geometry_safezone_spinctrl_change(self, event):
		print('geometry safety zone', event.GetPosition())
		assert self.instance is not None
		if self.geometry['diameter'].GetValue() > self.geometry['safezone'].GetValue() * 2:
			self.geometry['diameter'].SetValue(math.floor(self.geometry['safezone'].GetValue() * 2))
		self.draw()

	def on_drawmode_button_click(self, event, mode):
		print('drawmode', mode)
		assert self.instance is not None
		assert mode in self.drawmode['buttons']
		self.drawmode['value'] = mode
		self.drawmode['statictext'].SetLabel('draw mode: {:s}'.format(mode))
		for mode, button in self.drawmode['buttons'].items():
			if mode == self.drawmode['value']:
				button.Disable()
			else:
				button.Enable()
				button.SetValue(False)
		if event is not None:
			self.draw(force=True)

	def on_mask_insert_button_click(self, event):
		print('mask append')
		assert self.instance is not None
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				self.title(),
				wx.OK|wx.ICON_INFORMATION,
			)
			return
		if overlay in self.instance['mask_list']:
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
		self.instance['mask_list'].append(overlay)
		self.mask_sizer_refresh()
		self.layout()

	def on_mask_remove_button_click(self, event, overlay):
		print('mask remove', overlay.name)
		assert self.instance is not None
		self.instance['mask_list'].remove(overlay)
		self.mask_sizer_refresh()
		self.layout()

	def on_mask_select_button_click(self, event, overlay):
		print('mask select', overlay.name)
		assert self.instance is not None
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
			print('ablation image has been removed from overlay list')
			self.reset()
			return
		refresh = False
		for overlay in self.instance['mask_list']:
			if overlay not in self.overlayList:
				print('mask has been removed from overlay list')
				self.instance['mask_list'].remove(overlay)
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
