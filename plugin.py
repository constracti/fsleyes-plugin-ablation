#!/usr/bin/python3


import json
import math

import fsleyes
import numpy
import wx


print('plugin: ablation')


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
		home_sizer.SetMinSize(240, 0)
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
		# open sizer
		open_sizer = wx.BoxSizer(wx.HORIZONTAL)
		new_button = wx.Button(self.main_window, label='new file')
		handler = lambda event, load=False: self.on_load_button_click(event, load)
		new_button.Bind(wx.EVT_BUTTON, handler)
		open_sizer.Add(new_button)
		open_sizer.Add(4, 0, 1)
		load_button = wx.Button(self.main_window, label='load file')
		handler = lambda event, load=True: self.on_load_button_click(event, load)
		load_button.Bind(wx.EVT_BUTTON, handler)
		open_sizer.Add(load_button)
		self.start_items.append(main_sizer.Add(open_sizer, flag=wx.EXPAND))
		self.start_items.append(main_sizer.AddSpacer(4))

	def _init_instance_items(self, main_sizer):
		self.instance_items = []
		# close sizer
		close_sizer = wx.BoxSizer(wx.HORIZONTAL)
		save_button = wx.Button(self.main_window, label='save file')
		save_button.Bind(wx.EVT_BUTTON, self.on_save_button_click)
		close_sizer.Add(save_button)
		close_sizer.Add(4, 0, 1)
		close_button = wx.Button(self.main_window, label='close file')
		close_button.Bind(wx.EVT_BUTTON, self.on_close_button_click)
		close_sizer.Add(close_button)
		self.instance_items.append(main_sizer.Add(close_sizer, flag=wx.EXPAND))
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
		sizer.Add(4, 0, 1)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=fsleyes.icons.loadBitmap('add24'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('insert needle')
		handler = lambda event: self.on_insert_button_click(event, 0)
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
		sizer.Add(4, 0, 1)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=fsleyes.icons.loadBitmap('folder16'),
			size=wx.Size(26, 26),
		)
		button.SetToolTip('import geometry from json file')
		button.Bind(wx.EVT_BUTTON, self.on_geometry_import_button_click)
		sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(4, 0, 0)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=fsleyes.icons.loadBitmap('floppydisk16'),
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
		sizer.Add(4, 0, 1)
		spinctrl = wx.SpinCtrl(
			self.main_window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=1,
			max=20,
		)
		spinctrl.SetValue(3)
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
		sizer.Add(4, 0, 1)
		spinctrl = wx.SpinCtrl(
			self.main_window,
			size=wx.Size(56, 24),
			style=wx.ALIGN_RIGHT,
			min=1,
			max=50,
		)
		spinctrl.SetValue(15)
		spinctrl.Bind(wx.EVT_SPINCTRL, self.on_geometry_safezone_spinctrl_change)
		sizer.Add(spinctrl, flag=wx.ALIGN_CENTER_VERTICAL)
		self.geometry['safezone'] = spinctrl
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
		sizer.Add(4, 0, 1)
		button = wx.BitmapButton(
			self.main_window,
			bitmap=fsleyes.icons.loadBitmap('add24'),
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
		# form text
		form_text = wx.StaticText(self.main_window, label='item')
		self.form_items.append(main_sizer.Add(form_text))
		self.form_text = form_text
		self.form_items.append(main_sizer.AddSpacer(4))
		# pair sizer
		pair_sizer = wx.FlexGridSizer(4, 4, 4)
		pair_sizer.SetFlexibleDirection(wx.HORIZONTAL)
		self.form_items.append(main_sizer.Add(pair_sizer))
		self.form_items.append(main_sizer.AddSpacer(4))
		# pair sizer head
		pair_sizer.Add(
			wx.StaticText(self.main_window, label='point'),
			flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self.main_window, label='coordinates'),
			flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self.main_window, label='mark'),
			flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self.main_window, label='view'),
			flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
		)
		# pair sizer body
		self.form = {
			'coords_text': [],
			'view_button': [],
		}
		mark_bitmap = fsleyes.icons.loadBitmap('floppydisk16')
		view_bitmap = fsleyes.icons.loadBitmap('eye16')
		for which in ['entry', 'target']:
			# which text
			pair_sizer.Add(
				wx.StaticText(self.main_window, label=which),
				flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
			)
			# coordinates
			sizer = wx.FlexGridSizer(3, 1, 1)
			text_ctrl_list = []
			for x in range(sizer.GetCols()):
				text_ctrl = wx.TextCtrl(
					self.main_window,
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				)
				sizer.Add(text_ctrl)
				text_ctrl_list.append(text_ctrl)
			pair_sizer.Add(sizer)
			self.form['coords_text'].append(text_ctrl_list)
			# mark button
			bitmap_button = wx.BitmapButton(self.main_window, bitmap=mark_bitmap)
			handler = lambda event, which=which: self.on_mark_button_click(event, which)
			bitmap_button.Bind(wx.EVT_BUTTON, handler)
			pair_sizer.Add(
				bitmap_button,
				flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
			)
			# view button
			bitmap_button = wx.BitmapButton(self.main_window, bitmap=view_bitmap)
			handler = lambda event, which=which: self.on_view_button_click(event, 0, which)
			bitmap_button.Bind(wx.EVT_BUTTON, handler)
			pair_sizer.Add(
				bitmap_button,
				flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
			)
			self.form['view_button'].append(bitmap_button)
		self.form['coords_text'] = tuple(self.form['coords_text'])
		self.form['view_button'] = tuple(self.form['view_button'])
		# pair slider
		pair_slider = wx.Slider(self.main_window)
		pair_slider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.on_pair_slider_scroll)
		pair_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_pair_slider_scroll)
		self.form_items.append(main_sizer.Add(pair_slider, flag=wx.EXPAND))
		self.pair_slider = pair_slider
		self.form_items.append(main_sizer.AddSpacer(4))
		# submit sizer
		submit_sizer = wx.BoxSizer(wx.HORIZONTAL)
		submit_button = wx.Button(self.main_window, label='submit')
		submit_button.Bind(wx.EVT_BUTTON, self.on_submit_button_click)
		submit_sizer.Add(submit_button)
		self.submit_button = submit_button
		submit_sizer.Add(4, 0, 1)
		cancel_button = wx.Button(self.main_window, label='cancel')
		cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel_button_click)
		submit_sizer.Add(cancel_button)
		self.form_items.append(main_sizer.Add(submit_sizer, flag=wx.EXPAND))
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
			), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
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
					bitmap=fsleyes.icons.loadBitmap('eye24'),
					size=wx.Size(26, 26),
				)
				button.SetToolTip('focus')
				handler = lambda event, index=index, which=which: self.on_view_button_click(event, index, which)
				button.Bind(wx.EVT_BUTTON, handler)
				sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.items_sizer.Add(sizer)
			# update button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=fsleyes.icons.loadBitmap('pencil24'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('update needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_update_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['update_button'].append(button)
			# clone button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=fsleyes.icons.loadBitmap('new24'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('clone needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_insert_button_click(event, index)
			button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			self.instance['clone_button'].append(button)
			# delete button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=fsleyes.icons.loadBitmap('remove24'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove needle #{:d}'.format(index))
			handler = lambda event, index=index: self.on_delete_button_click(event, index)
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
			self.form_text.SetLabelText('update needle #{:d}'.format(self.index))
		else:
			self.form_text.SetLabelText('insert needle')
		self.form_refresh()

	def form_hide(self):
		assert self.instance is None or self.index is None
		for item in self.form_items:
			item.Show(False)
		self.form_text.SetLabelText('')

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
		self.pair_slider.Enable(enable)

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
				bitmap=fsleyes.icons.loadBitmap('eye24'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('select overlay')
			handler = lambda event, overlay=overlay: self.on_mask_select_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)
			# remove button
			button = wx.BitmapButton(
				self.main_window,
				bitmap=fsleyes.icons.loadBitmap('remove24'),
				size=wx.Size(26, 26),
			)
			button.SetToolTip('remove overlay from mask list')
			handler = lambda event, overlay=overlay: self.on_mask_remove_button_click(event, overlay)
			button.Bind(wx.EVT_BUTTON, handler)
			self.mask_sizer.Add(button, flag=wx.ALIGN_CENTER_VERTICAL)

	def layout(self):
		self.GetSizer().Layout()

	def draw(self):
		print('draw')
		assert self.instance is not None
		image = self.instance['image']
		data = numpy.zeros(image.shape, dtype=int)
		for i, (entry_xyz, target_xyz) in enumerate(self.instance['items']):
			index = i + 1
			mask = self.pair2mask(entry_xyz, target_xyz) # 40ms/loop
			data[mask] = index
		if self.index is not None:
			entry_xyz, target_xyz = tuple(self.form['point_xyz'])
			if entry_xyz is not None and target_xyz is not None:
				index = len(self.instance['items']) + 1
				mask = self.pair2mask(entry_xyz, target_xyz) # 40ms
				data[mask] = index
		image[:] = data[:] # 270ms

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

	def on_load_button_click(self, event, load):
		print('load' if load else 'new')
		assert self.instance is None
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		path = None
		items = []
		if load:
			with wx.FileDialog(self, self.title(), wildcard='JSON files (.json)|*.json', style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST) as file_dialog:
				if file_dialog.ShowModal() == wx.ID_CANCEL:
					return
				path = file_dialog.GetPath()
				try:
					with open(path, 'r') as fp:
						items = json.load(fp)
					assert type(items) is list
					for item in items:
						assert type(item) is list and len(item) == 2
						for point_xyz in item:
							assert type(point_xyz) is list and len(point_xyz) == 3
							for value in point_xyz:
								assert type(value) is float
					items = [tuple(tuple(point_xyz) for point_xyz in item) for item in items]
				except IOError as error:
					wx.MessageBox(
						str(error),
						self.title(),
						wx.OK | wx.ICON_ERROR,
					)
					return
				except json.JSONDecodeError as error:
					wx.MessageBox(
						str(error),
						self.title(),
						wx.OK | wx.ICON_ERROR,
					)
					return
				except AssertionError:
					wx.MessageBox(
						'Input file should have compatible content.',
						self.title(),
						wx.OK | wx.ICON_ERROR,
					)
					return
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
			'items': items,
			'form_is_dirty': False,
			'mask_list': [],
		}
		self.index = None
		self.start_hide()
		self.instance_show()
		self.layout()
		self.draw()

	def on_save_button_click(self, event):
		print('save')
		assert self.instance is not None
		with wx.FileDialog(self, self.title(), wildcard='JSON files (.json)|*.json', style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT) as file_dialog:
			if self.instance['path'] is not None:
				file_dialog.SetPath(self.instance['path'])
			if file_dialog.ShowModal() == wx.ID_CANCEL:
				return
			path = file_dialog.GetPath()
			try:
				with open(path, 'w') as fp:
					json.dump(self.instance['items'], fp, indent="\t")
			except IOError as error:
				wx.MessageBox(
					str(error),
					self.title(),
					wx.OK | wx.ICON_ERROR,
				)
				return
		wx.MessageBox(
			'File saved successfully.',
			self.title(),
			wx.OK | wx.ICON_INFORMATION,
		)

	def on_close_button_click(self, event):
		print('close')
		assert self.instance is not None
		instance = self.instance
		self.instance = None
		if fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, instance['image']):
			self.reset()
		else:
			self.instance = instance

	def on_insert_button_click(self, event, index):
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

	def on_update_button_click(self, event, index):
		print('update', index)
		assert self.instance is not None
		assert self.index is None
		self.index = index
		self.form['point_xyz'] = list(self.instance['items'][index - 1])
		self.needle_list_disable()
		self.form_show()
		self.layout()

	def on_delete_button_click(self, event, index):
		print('delete', index)
		assert self.instance is not None
		assert self.index is None
		self.instance['items'].pop(index - 1)
		self.needle_list_refresh()
		self.layout()
		self.draw()

	def on_mark_button_click(self, event, which):
		print('mark', which)
		assert self.instance is not None
		assert self.index is not None
		if which == 'entry':
			self.form['point_xyz'][0] = tuple(self.displayCtx.worldLocation.xyz)
			self.pair_slider.SetValue(self.pair_slider.GetMin())
		elif which == 'target':
			self.form['point_xyz'][1] = tuple(self.displayCtx.worldLocation.xyz)
			self.pair_slider.SetValue(self.pair_slider.GetMax())
		else:
			assert False
		if all(point_xyz is not None for point_xyz in self.form['point_xyz']):
			self.instance['form_is_dirty'] = True
		self.form_refresh()
		if self.instance['form_is_dirty']:
			self.draw()

	def on_view_button_click(self, event, index, which):
		print('view', index, which)
		assert self.instance is not None
		if index == 0:
			assert self.index is not None
			if which == 'entry':
				assert self.form['point_xyz'][0] is not None
				self.displayCtx.worldLocation.xyz = self.form['point_xyz'][0]
				self.pair_slider.SetValue(self.pair_slider.GetMin())
			elif which == 'target':
				assert self.form['point_xyz'][1] is not None
				self.displayCtx.worldLocation.xyz = self.form['point_xyz'][1]
				self.pair_slider.SetValue(self.pair_slider.GetMax())
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

	def on_pair_slider_scroll(self, event):
		print('pair', event.GetEventType(), event.GetPosition())
		assert self.instance is not None
		assert self.index is not None
		entry_xyz, target_xyz = tuple(self.form['point_xyz'])
		assert entry_xyz is not None and target_xyz is not None
		slider = self.pair_slider
		t = (slider.GetValue() - slider.GetMin()) / (slider.GetMax() - slider.GetMin())
		point_xyz = numpy.average([entry_xyz, target_xyz], 0, [1-t, t])
		self.displayCtx.worldLocation.xyz = tuple(point_xyz)

	def on_submit_button_click(self, event):
		print('submit')
		assert self.instance is not None
		assert self.index is not None
		entry_xyz, target_xyz = tuple(self.form['point_xyz'])
		assert entry_xyz is not None and target_xyz is not None
		if numpy.allclose(entry_xyz, target_xyz):
			wx.MessageBox(
				'Entry and target points should differ.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
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
		self.draw()

	def on_cancel_button_click(self, event):
		print('cancel')
		assert self.instance is not None
		assert self.index is not None
		self.index = None
		self.needle_list_enable()
		self.form_hide()
		self.layout()
		if self.instance['form_is_dirty']:
			self.draw()
			self.instance['form_is_dirty'] = False

	def on_geometry_import_button_click(self, event):
		print('geometry import')
		assert self.instance is not None
		print('TODO import')

	def on_geometry_export_button_click(self, event):
		print('geometry export')
		assert self.instance is not None
		print('TODO export')

	def on_geometry_diameter_spinctrl_change(self, event):
		print('geometry diameter', event.GetPosition())
		assert self.instance is not None
		if self.geometry['safezone'].GetValue() < self.geometry['diameter'].GetValue() / 2:
			self.geometry['safezone'].SetValue(math.ceil(self.geometry['diameter'].GetValue() / 2))

	def on_geometry_safezone_spinctrl_change(self, event):
		print('geometry safety zone', event.GetPosition())
		assert self.instance is not None
		if self.geometry['diameter'].GetValue() > self.geometry['safezone'].GetValue() * 2:
			self.geometry['diameter'].SetValue(math.floor(self.geometry['safezone'].GetValue() * 2))

	def on_mask_insert_button_click(self, event):
		print('mask append')
		assert self.instance is not None
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		if overlay in self.instance['mask_list']:
			wx.MessageBox(
				'The selected overlay is already in the list.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		if overlay.shape != self.instance['image'].shape:
			wx.MessageBox(
				'Selected overlay and base image should have identical shapes.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		if not numpy.allclose(overlay.voxToWorldMat, self.instance['image'].voxToWorldMat):
			wx.MessageBox(
				'Selected overlay and base image should have identical affine transformations.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
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
