#!/usr/bin/python3


import fsleyes
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
			'ablation',
			self.on_overlay_list_changed,
			immediate=True,
		)
		# sizer
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		# create button
		self.create_button = wx.Button(self, label='create')
		self.create_button.Bind(wx.EVT_BUTTON, self.on_create_button_click)
		sizer.Add(self.create_button)
		# entry button
		self.entry_button = wx.Button(self, label='set entry')
		self.entry_button.Bind(wx.EVT_BUTTON, self.on_entry_button_click)
		sizer.Add(self.entry_button)
		# target button
		self.target_button = wx.Button(self, label='set target')
		self.target_button.Bind(wx.EVT_BUTTON, self.on_target_button_click)
		sizer.Add(self.target_button)
		# destroy button
		self.destroy_button = wx.Button(self, label='destroy')
		self.destroy_button.Bind(wx.EVT_BUTTON, self.on_destroy_button_click)
		sizer.Add(self.destroy_button)
		# reset
		self.reset()

	def reset(self):
		self.image = None
		self.create_button.Enable()
		self.entry_button.Disable()
		self.target_button.Disable()
		self.destroy_button.Disable()

	def on_create_button_click(self, event):
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
		self.create_button.Disable()
		self.entry_button.Enable()
		self.target_button.Enable()
		self.destroy_button.Enable()

	def on_entry_button_click(self, event):
		assert self.image is not None and self.image in self.overlayList
		opts = self.displayCtx.getOpts(self.image)
		coords = self.displayCtx.worldLocation.xyz
		xformed = opts.transformCoords([coords], 'world', 'voxel', True)[0]
		xformed = tuple(xformed.astype(int))
		print(xformed)
		print('before', self.image[xformed])
		self.image[xformed] = 1
		print('after', self.image[xformed])

	def on_target_button_click(self, event):
		assert self.image is not None and self.image in self.overlayList

	def on_destroy_button_click(self, event):
		assert self.image is not None and self.image in self.overlayList
		image = self.image
		self.image = None
		if not fsleyes.actions.removeoverlay.removeOverlay(self.overlayList, self.displayCtx, self.image):
			return
		self.reset()

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
		return [fsleyes.views.orthopanel.OrthoPanel]


"""
class MyAction(fsleyes.actions.Action):

	def __init__(self, overlayList, displayCtx, frame):
		super().__init__(overlayList, displayCtx, self.run)
		return None

	def run(self):
		print('action run')
"""
