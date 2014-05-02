""" Class to load configuration file."""

import yaml
import operator
from Error import PluginNonExistError


class Config:
	"""Reads YAML config file and allows easy accessor to config attributes"""
	def __init__(self, configFileName):
		"""Initlize config from YAML file"""
		self.config = yaml.load(open(configFileName, "r"))

	def getPluginClassNames(self):
		"""Get the default set of plugin class names"""
		# force sorting by default order
		return sorted(self.config['plugins'], 
			key=lambda x: (self.config['plugins'][x]['defaultOrder']))

	def getPluginConfig(self, pluginClassName):
		"""Get config associated with a plugin"""
		try:
			return self.config['plugins'][pluginClassName]
		except:
			raise PluginNonExistError(pluginClassName, "Plugin doesn't exist in this config")

	def getWindowFrameSize(self):
		"""Get the number of frames in a sliding window"""
		return self.config['window']['frame']['size']

	def getWindowFrameSpacing(self):
		"""Get the spacing between frames in a sliding window"""
		return self.config['window']['frame']['spacing']

	def getPluginClassNameForSelectingSingleFrame(self):
		"""Get the plugin class name for the plugin which limits frame selection to 1"""
		return 'SelectSingleFrame'

	def getPluginClassNameForModelDetection(self):
		"""Get the plugin class name for the plugin which limits frame selection to 1"""
		return 'ModelDetection'
	
	def getCampaignId(self):
		"""Get the campaign id - used for saving results, etc """
		return self.config['campaign']['id']

	def __str__(self):
		"""Return a nice string representation of the object."""
		return str(self.config)
