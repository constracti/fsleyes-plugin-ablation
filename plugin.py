#!/usr/bin/python3


import json
import fsleyes
import numpy
import wx


print('plugin: ablation')


"""
print(fsleyes.icons.getIconDir())
/usr/local/fsl/fslpython/envs/fslpython/lib/python3.7/site-packages/fsleyes/assets/icons
"""


MAX_ITEMS = 5


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
		container_sizer = wx.BoxSizer(wx.HORIZONTAL)
		container_sizer.SetMinSize(208, 0)
		self.SetSizer(container_sizer)
		container_sizer.AddSpacer(4)
		home_sizer = wx.BoxSizer(wx.VERTICAL)
		home_sizer.AddSpacer(4)
		self._init_start_items(home_sizer)
		self._init_instance_items(home_sizer)
		self._init_form_items(home_sizer)
		container_sizer.Add(home_sizer, 1)
		container_sizer.AddSpacer(4)
		self.reset()

	def _init_start_items(self, home_sizer):
		self.start_items = []
		# open sizer
		open_sizer = wx.BoxSizer(wx.HORIZONTAL)
		new_button = wx.Button(self, label='new file')
		handler = lambda event, load=False: self.on_load_button_click(event, load)
		new_button.Bind(wx.EVT_BUTTON, handler)
		open_sizer.Add(new_button)
		open_sizer.Add(4, 0, 1)
		load_button = wx.Button(self, label='load file')
		handler = lambda event, load=True: self.on_load_button_click(event, load)
		load_button.Bind(wx.EVT_BUTTON, handler)
		open_sizer.Add(load_button)
		self.start_items.append(home_sizer.Add(open_sizer, flag=wx.EXPAND))
		self.start_items.append(home_sizer.AddSpacer(4))

	def _init_instance_items(self, home_sizer):
		self.instance_items = []
		# close sizer
		close_sizer = wx.BoxSizer(wx.HORIZONTAL)
		save_button = wx.Button(self, label='save file')
		save_button.Bind(wx.EVT_BUTTON, self.on_save_button_click)
		close_sizer.Add(save_button)
		close_sizer.Add(4, 0, 1)
		close_button = wx.Button(self, label='close file')
		close_button.Bind(wx.EVT_BUTTON, self.on_close_button_click)
		close_sizer.Add(close_button)
		self.instance_items.append(home_sizer.Add(close_sizer, flag=wx.EXPAND))
		self.instance_items.append(home_sizer.AddSpacer(4))
		# items line
		self.instance_items.append(home_sizer.Add(wx.StaticLine(self)))
		self.instance_items.append(home_sizer.AddSpacer(4))
		# items text
		self.instance_items.append(home_sizer.Add(wx.StaticText(self, label='items')))
		self.instance_items.append(home_sizer.AddSpacer(4))
		# items sizer
		items_sizer = wx.FlexGridSizer(4, 4, 4)
		items_sizer.SetFlexibleDirection(wx.HORIZONTAL)
		self.instance_items.append(home_sizer.Add(items_sizer))
		self.items_sizer = items_sizer
		self.instance_items.append(home_sizer.AddSpacer(4))
		# insert button
		insert_button = wx.Button(self, label='insert')
		insert_button.Bind(wx.EVT_BUTTON, self.on_insert_button_click)
		self.instance_items.append(home_sizer.Add(insert_button, flag=wx.ALIGN_CENTER))
		self.insert_button = insert_button
		self.instance_items.append(home_sizer.AddSpacer(4))

	def _init_form_items(self, home_sizer):
		self.form_items = []
		# form line
		self.form_items.append(home_sizer.Add(wx.StaticLine(self)))
		self.form_items.append(home_sizer.AddSpacer(4))
		# form text
		form_text = wx.StaticText(self, label='item')
		self.form_items.append(home_sizer.Add(form_text))
		self.form_text = form_text
		self.form_items.append(home_sizer.AddSpacer(4))
		# pair sizer
		pair_sizer = wx.FlexGridSizer(4, 4, 4)
		pair_sizer.SetFlexibleDirection(wx.HORIZONTAL)
		self.form_items.append(home_sizer.Add(pair_sizer))
		self.form_items.append(home_sizer.AddSpacer(4))
		# pair sizer head
		pair_sizer.Add(
			wx.StaticText(self, label='point'),
			flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self, label='coordinates'),
			flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self, label='mark'),
			flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
		)
		pair_sizer.Add(
			wx.StaticText(self, label='view'),
			flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
		)
		# pair sizer body
		self.form = {
			'coords_text': [],
			'view_button': [],
		}
		mark_bitmap = fsleyes.icons.loadBitmap('floppydisk16')
		view_bitmap = fsleyes.icons.loadBitmap('eye16')
		for w, which in enumerate(['entry', 'target']):
			# which text
			pair_sizer.Add(
				wx.StaticText(self, label=which),
				flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,
			)
			# coordinates
			sizer = wx.FlexGridSizer(3, 1, 1)
			text_ctrl_list = []
			for x in range(sizer.GetCols()):
				text_ctrl = wx.TextCtrl(
					self,
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				)
				sizer.Add(text_ctrl)
				text_ctrl_list.append(text_ctrl)
			pair_sizer.Add(sizer)
			self.form['coords_text'].append(text_ctrl_list)
			# mark button
			bitmap_button = wx.BitmapButton(self, bitmap=mark_bitmap)
			handler = lambda e, w=w: self.on_mark_button_click(e, w)
			bitmap_button.Bind(wx.EVT_BUTTON, handler)
			pair_sizer.Add(
				bitmap_button,
				flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
			)
			# view button
			bitmap_button = wx.BitmapButton(self, bitmap=view_bitmap)
			handler = lambda e, w=w: self.on_view_button_click(e, w)
			bitmap_button.Bind(wx.EVT_BUTTON, handler)
			pair_sizer.Add(
				bitmap_button,
				flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL,
			)
			self.form['view_button'].append(bitmap_button)
		self.form['coords_text'] = tuple(self.form['coords_text'])
		self.form['view_button'] = tuple(self.form['view_button'])
		# submit sizer
		submit_sizer = wx.BoxSizer(wx.HORIZONTAL)
		submit_button = wx.Button(self, label='submit')
		submit_button.Bind(wx.EVT_BUTTON, self.on_submit_button_click)
		submit_sizer.Add(submit_button)
		self.submit_button = submit_button
		submit_sizer.Add(4, 0, 1)
		cancel_button = wx.Button(self, label='cancel')
		cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel_button_click)
		submit_sizer.Add(cancel_button)
		self.form_items.append(home_sizer.Add(submit_sizer, flag=wx.EXPAND))
		self.form_items.append(home_sizer.AddSpacer(4))

	def destroy(self):
		self.overlayList.removeListener('overlays', self.name)
		super().destroy()

	def reset(self):
		self.instance = None
		self.refresh(True)

	def refresh(self, build=False):
		for item in self.start_items:
			item.Show(self.instance is None)
		for item in self.instance_items:
			item.Show(self.instance is not None)
		for item in self.form_items:
			item.Show(self.instance is not None and self.item_index is not None)
		if self.instance is not None:
			self.insert_button.Enable(len(self.instance['items']) < MAX_ITEMS)
		if build:
			self._build_items()
		if self.instance is not None and self.item_index is not None:
			for point_xyz, coords_text, view_button in zip(self.form['point_xyz'], self.form['coords_text'], self.form['view_button']):
				view_button.Enable(point_xyz is not None)
				if point_xyz is not None:
					values = ['{:.0f}'.format(v) for v in point_xyz]
				else:
					values = [''] * len(coords_text)
				for v, text_ctrl in zip(values, coords_text):
					text_ctrl.SetValue(v)
			self.submit_button.Enable(all(point_xyz is not None for point_xyz in self.form['point_xyz']))
		self.GetSizer().Layout()

	def _build_items(self):
		self.items_sizer.Clear(True)
		if self.instance is None:
			return
		image = self.instance['image']
		# wipe image
		image[:] = numpy.zeros(image.shape)
		update_bitmap = fsleyes.icons.loadBitmap('pencil24')
		delete_bitmap = fsleyes.icons.loadBitmap('eraser24')
		# loop items
		for index, (entry_xyz, target_xyz) in enumerate(self.instance['items']):
			# index text
			self.items_sizer.Add(wx.StaticText(
				self,
				label='#{:d}'.format(index + 1),
			), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(3, 1, 1)
			for x in entry_xyz + target_xyz:
				sizer.Add(wx.TextCtrl(
					self,
					value='{:.0f}'.format(x),
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				))
			self.items_sizer.Add(sizer)
			# update button
			update_button = wx.BitmapButton(self, bitmap=update_bitmap)
			handler = lambda e, i=index: self.on_update_button_click(e, i)
			update_button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(update_button, flag=wx.ALIGN_CENTER_VERTICAL)
			# delete button
			delete_button = wx.BitmapButton(self, bitmap=delete_bitmap)
			handler = lambda e, i=index: self.on_delete_button_click(e, i)
			delete_button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(delete_button, flag=wx.ALIGN_CENTER_VERTICAL)
			# draw image
			mask = numpy.zeros(image.shape, dtype=bool)
			print('entry', entry_xyz)
			print('target', target_xyz)
			vector_xyz = numpy.asarray(target_xyz) - numpy.asarray(entry_xyz)
			num = numpy.dot(numpy.abs(vector_xyz), numpy.reciprocal(image.pixdim)).round().astype(int)
			print('count', num)
			for t in numpy.linspace(0, 1, num):
				point_xyz = numpy.average([entry_xyz, target_xyz], 0, [1-t, t])
				point_ijk = self.world2voxel(point_xyz)
				mask[point_ijk] = True
			image[mask] = index + 1

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
					assert type(items) is list and len(items) <= MAX_ITEMS
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
		}
		self.item_index = None
		self.refresh(True)

	def on_insert_button_click(self, event):
		print('insert')
		assert self.instance is not None
		self.item_index = -1
		self.form['point_xyz'] = [None, None]
		self.form_text.SetLabelText('insert item')
		self.refresh()

	def on_update_button_click(self, event, index):
		print('update', index)
		assert self.instance is not None
		self.item_index = index
		self.form['point_xyz'] = list(self.instance['items'][index])
		self.form_text.SetLabelText('update item #{:d}'.format(index + 1))
		self.refresh()

	def on_delete_button_click(self, event, index):
		print('delete', index)
		assert self.instance is not None
		self.instance['items'].pop(index)
		self.refresh(True)

	def on_mark_button_click(self, event, which):
		print('mark', which)
		assert self.instance is not None
		assert self.item_index is not None
		assert which in [0, 1]
		self.form['point_xyz'][which] = tuple(self.displayCtx.worldLocation.xyz)
		self.refresh()

	def on_view_button_click(self, event, which):
		print('view', which)
		assert self.instance is not None
		assert self.item_index is not None
		assert which in [0, 1]
		assert self.form['point_xyz'][which] is not None
		self.displayCtx.worldLocation.xyz = self.form['point_xyz'][which]

	def on_submit_button_click(self, event):
		print('submit')
		assert self.instance is not None
		assert self.item_index is not None
		entry_xyz, target_xyz = tuple(self.form['point_xyz'])
		assert entry_xyz is not None and target_xyz is not None
		if numpy.allclose(entry_xyz, target_xyz):
			wx.MessageBox(
				'Entry and target points should differ.',
				self.title(),
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		if self.item_index >= 0:
			self.instance['items'][self.item_index] = (entry_xyz, target_xyz)
		else:
			self.instance['items'].append((entry_xyz, target_xyz))
		self.item_index = None
		self.refresh(True)

	def on_cancel_button_click(self, event):
		print('cancel')
		assert self.instance is not None
		assert self.item_index is not None
		self.item_index = None
		self.refresh()

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

	def on_close_button_click(self, event):
		print('close')
		assert self.instance is not None
		instance = self.instance
		self.instance = None
		if fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, instance['image']):
			self.reset()
		else:
			self.instance = instance

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
		if self.instance['image'] in self.overlayList:
			return
		print('ablation image has been removed from the overlay list')
		self.reset()

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
