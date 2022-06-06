#!/usr/bin/python3


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
		self.home_sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self.home_sizer)
		self.home_sizer.AddSpacer(4)
		# new button
		self.new_button = wx.Button(self, label='new file')
		self.new_button.Bind(wx.EVT_BUTTON, self.on_new_button_click)
		self.home_sizer.Add(self.new_button, flag=wx.ALIGN_CENTER)
		# instance sizer
		self.instance_sizer = wx.BoxSizer(wx.VERTICAL)
		self.home_sizer.Add(self.instance_sizer, flag=wx.EXPAND)
		# items group
		self.items_group = wx.StaticBoxSizer(wx.VERTICAL, self, 'items')
		self.instance_sizer.Add(self.items_group, flag=wx.EXPAND)
		self.instance_sizer.AddSpacer(4)
		# items sizer
		self.items_sizer = wx.FlexGridSizer(4, 4, 4)
		self.items_sizer.SetFlexibleDirection(wx.HORIZONTAL)
		self.items_group.AddSpacer(4)
		self.items_group.Add(self.items_sizer)
		self.items_group.AddSpacer(4)
		# insert button
		self.insert_button = wx.Button(self, label='insert')
		self.insert_button.Bind(wx.EVT_BUTTON, self.on_insert_button_click)
		self.instance_sizer.Add(self.insert_button, flag=wx.ALIGN_CENTER)
		# item group
		self.item_group = wx.StaticBoxSizer(wx.VERTICAL, self)
		self.instance_sizer.Add(self.item_group, flag=wx.EXPAND)
		self.item_group.AddSpacer(4)
		item_box = self.item_group.GetStaticBox()
		# entry button
		self.entry_button = wx.Button(item_box, label='set entry')
		self.entry_button.Bind(wx.EVT_BUTTON, self.on_entry_button_click)
		self.item_group.Add(self.entry_button, flag=wx.ALIGN_CENTER)
		self.item_group.AddSpacer(4)
		# target button
		self.target_button = wx.Button(item_box, label='set target')
		self.target_button.Bind(wx.EVT_BUTTON, self.on_target_button_click)
		self.item_group.Add(self.target_button, flag=wx.ALIGN_CENTER)
		self.item_group.AddSpacer(4)
		# submit button
		self.submit_button = wx.Button(item_box, label='submit')
		self.submit_button.Bind(wx.EVT_BUTTON, self.on_submit_button_click)
		self.item_group.Add(self.submit_button, flag=wx.ALIGN_CENTER)
		self.item_group.AddSpacer(4)
		# cancel button
		self.cancel_button = wx.Button(item_box, label='cancel')
		self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel_button_click)
		self.item_group.Add(self.cancel_button, flag=wx.ALIGN_CENTER)
		self.item_group.AddSpacer(4)
		# close button
		self.close_button = wx.Button(self, label='close file')
		self.close_button.Bind(wx.EVT_BUTTON, self.on_close_button_click)
		self.instance_sizer.AddSpacer(4)
		self.instance_sizer.Add(self.close_button, flag=wx.ALIGN_CENTER)
		self.home_sizer.AddSpacer(4)
		# reset
		self.reset()

	def destroy(self):
		self.overlayList.removeListener('overlays', self.name)
		super().destroy()

	def reset(self):
		self.image = None
		self.instance = None
		self.home_sizer.Show(self.new_button)
		self.home_sizer.Hide(self.instance_sizer)
		self.build_items()
		self.home_sizer.Layout()

	def build_items(self):
		self.items_sizer.Clear(True)
		if self.instance is None:
			return
		# wipe image
		self.image[:] = numpy.zeros(self.image.shape)
		# loop items
		items_box = self.items_group.GetStaticBox()
		for index, (entry_xyz, target_xyz) in enumerate(self.instance):
			# index text
			self.items_sizer.Add(wx.StaticText(
				items_box,
				label='#{:d}'.format(index + 1),
			), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
			# coordinates
			sizer = wx.FlexGridSizer(3, 1, 1)
			for x in entry_xyz + target_xyz:
				sizer.Add(wx.TextCtrl(
					items_box,
					value='{:d}'.format(round(x)),
					size=wx.Size(30, 24),
					style=wx.TE_READONLY|wx.TE_RIGHT,
				))
			self.items_sizer.Add(sizer)
			# update button
			update_button = wx.Button(items_box, label='update')
			handler = lambda e, i=index: self.on_update_button_click(e, i)
			update_button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(update_button, flag=wx.ALIGN_CENTER_VERTICAL)
			# delete button
			delete_button = wx.Button(items_box, label='delete')
			handler = lambda e, i=index: self.on_delete_button_click(e, i)
			delete_button.Bind(wx.EVT_BUTTON, handler)
			self.items_sizer.Add(delete_button, flag=wx.ALIGN_CENTER_VERTICAL)
			# draw image
			for t in numpy.linspace(0, 1):
				coords = numpy.average([entry_xyz, target_xyz], 0, [t, 1-t])
				opts = self.displayCtx.getOpts(self.image)
				xformed = opts.transformCoords([coords], 'world', 'voxel', True)[0]
				xformed = tuple(xformed.astype(int))
				self.image[xformed] = index + 1

	def on_new_button_click(self, event):
		print('new')
		assert self.image is None
		overlay = self.displayCtx.getSelectedOverlay()
		if overlay is None:
			wx.MessageBox(
				'An overlay should be selected.',
				'Select an overlay.',
				wx.OK | wx.ICON_INFORMATION,
			)
			return
		nibimage = overlay.nibImage
		xyzt_units = nibimage.header.get_xyzt_units()
		self.image = fsleyes.actions.newimage.newImage(
			nibimage.shape,
			nibimage.header.get_zooms(),
			int,
			nibimage.affine,
			xyzt_units[0],
			xyzt_units[1],
			name='{:s}-ablation'.format(overlay.name),
		)
		self.overlayList.append(self.image)
		self.displayCtx.selectOverlay(self.image)
		self.instance = []
		self.home_sizer.Hide(self.new_button)
		self.home_sizer.Show(self.instance_sizer)
		self.instance_sizer.Hide(self.item_group)
		self.home_sizer.Layout()

	def on_insert_button_click(self, event):
		print('insert')
		assert self.image is not None and self.image in self.overlayList
		self.item_index = None
		self.entry_xyz, self.target_xyz = None, None
		self.instance_sizer.Show(self.item_group)
		self.item_group.GetStaticBox().SetLabelText('insert item')
		self.home_sizer.Layout()
		self.submit_button.Enable(self.entry_xyz is not None and self.target_xyz is not None)

	def on_update_button_click(self, event, index):
		print('update')
		assert self.image is not None and self.image in self.overlayList
		self.item_index = index
		self.entry_xyz, self.target_xyz = self.instance[index]
		self.instance_sizer.Show(self.item_group)
		self.item_group.GetStaticBox().SetLabelText('update item #{:d}'.format(index + 1))
		self.home_sizer.Layout()
		self.submit_button.Enable(self.entry_xyz is not None and self.target_xyz is not None)

	def on_delete_button_click(self, event, index):
		print('delete')
		assert self.image is not None and self.image in self.overlayList
		self.instance.pop(index)
		self.build_items()
		self.home_sizer.Layout()

	def on_entry_button_click(self, event):
		print('entry')
		assert self.image is not None and self.image in self.overlayList
		self.entry_xyz = tuple(self.displayCtx.worldLocation.xyz)
		self.submit_button.Enable(self.entry_xyz is not None and self.target_xyz is not None)

	def on_target_button_click(self, event):
		print('target')
		assert self.image is not None and self.image in self.overlayList
		self.target_xyz = tuple(self.displayCtx.worldLocation.xyz)
		self.submit_button.Enable(self.entry_xyz is not None and self.target_xyz is not None)

	def on_submit_button_click(self, event):
		print('submit')
		assert self.image is not None and self.image in self.overlayList
		if self.item_index is None:
			self.instance.append((self.entry_xyz, self.target_xyz))
		else:
			self.instance[self.item_index] = (self.entry_xyz, self.target_xyz)
		self.build_items()
		self.instance_sizer.Show(self.insert_button)
		self.instance_sizer.Hide(self.item_group)
		self.home_sizer.Layout()

	def on_cancel_button_click(self, event):
		print('cancel')
		assert self.image is not None and self.image in self.overlayList
		self.instance_sizer.Show(self.insert_button)
		self.instance_sizer.Hide(self.item_group)
		self.home_sizer.Layout()

	def on_close_button_click(self, event):
		print('close')
		assert self.image is not None and self.image in self.overlayList
		image = self.image
		self.image = None
		if fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, image):
			self.reset()
		else:
			self.image = image

	def on_overlay_list_changed(self, *args):
		if self.image is None:
			return
		if self.image in self.overlayList:
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
