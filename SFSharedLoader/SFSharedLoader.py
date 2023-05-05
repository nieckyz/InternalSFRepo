# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SFSharedLoader
                                 A QGIS plugin
 Common shared tab loader for RF Planner SF
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-05-04
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Dicky/Smartfren
        email                : nieckyz@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import PyQt5.QtCore
import pandas
import pydrive
import pandas as pd
import io
import os
import time
import requests
from qgis.core import QgsField, QgsVectorLayer, QgsPointXY, QgsFeature, QgsGeometry, QgsCoordinateReferenceSystem, Qgis, QgsWkbTypes, QgsFeatureRequest, QgsProject, QgsFields
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.oauth2.credentials import Credentials
from qgis.PyQt.QtCore import QVariant
from PyQt5.QtCore import Qt
from qgis.PyQt.QtWidgets import QDockWidget

# Initialize Qt resources from file resources.py
from .resources import *
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from httplib2 import socks
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Import the code for the DockWidget
from .SFSharedLoader_dockwidget import SFSharedLoaderDockWidget
import os.path

class SFSharedLoader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SFSharedLoader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SFSharedLoader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SFSharedLoader')
        self.toolbar.setObjectName(u'SFSharedLoader')

        #print "** INITIALIZING SFSharedLoader"

        self.pluginIsActive = False
        self.dockwidget = None

        import subprocess
        import time
        osgeo4w_path = r'C:\Program Files\QGIS 3.26.3\OSGeo4W.bat'
        subprocess.call(['pip', 'install', 'pydrive'])

        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SFSharedLoader', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SFSharedLoader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Common Tab Loader'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING SFSharedLoader"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD SFSharedLoader"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SFSharedLoader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        
        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING SFSharedLoader"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SFSharedLoaderDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            import PyQt5.QtWidgets as QtWidgets

            msgBox = QtWidgets.QMessageBox()
            msgBox.setText("Please follow the instructions below::")
            msgBox.setInformativeText("1. If your internet behind proxy and failed to download pydrive, please use normal internet connection\n\n2. Copy JSON files in C:\\\n\n3. Create folder \"C:\\Temp\\\" and copy \"Filelist.xlsx\" previously provided\n\n4. In \"Filelist.xlsx\" copy all files you want to upload that uploaded in your google drive shared folder and make sure you provide all data in each column. You can't use your own google drive unless google drive API is activated and JSON files ID in code changed.\n\nNote :\nIf link is https://docs.google.com/spreadsheets/d/17abJ6NMs2S6V6gfLTv1ItWc2JnM1cgyQ/edit?usp=sharing&ouid=104463821634212213640&rtpof=true&sd=true, then you can copy only \"17abJ6NMs2S6V6gfLTv1ItWc2JnM1cgyQ\"\n\n6. If you don't have permission to google drive or file, please request access to Admin")
            msgBox.setWindowTitle("READ THIS!")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.exec_()
        
            # set proxy
            proxies = {
                "http": "jkt-proxy01.smartfren.com', port=8080",
                "https": "jkt-proxy01.smartfren.com', port=8080",
            }

            try:
                gauth = GoogleAuth()
                gauth.settings['client_config_file'] = 'c:\client_secret_970748199042-po36ri803vbr5c5l545aptfqsabevp7v.apps.googleusercontent.com.json'
                drive = GoogleDrive(gauth)
                if proxies is not None:
                    gauth.LocalWebserverAuth(server_host='localhost', server_port=8080, proxy=proxies)
            except Exception as e:
                proxies = None
                gauth.LocalWebserverAuth()

            drive = GoogleDrive(gauth)
                                        
            #Save mycred.txt if not exist
            if not os.path.isfile('mycreds.txt'):
                gauth = GoogleAuth()
                gauth.settings['client_config_file'] = 'c:\client_secret_970748199042-po36ri803vbr5c5l545aptfqsabevp7v.apps.googleusercontent.com.json'
                drive = GoogleDrive(gauth)
                gauth.LocalWebserverAuth()
                gauth.SaveCredentialsFile("mycreds.txt")
            else:
                gauth = GoogleAuth()
                gauth.LoadCredentialsFile("mycreds.txt")
                drive = GoogleDrive(gauth)

            # Read filest
            filelist_path = r'C:\Temp\Filelist.xlsx'
            filelist_df = pd.read_excel(filelist_path)
            filelist_mod_time = os.path.getmtime(filelist_path)
            if os.path.getmtime(filelist_path) > filelist_mod_time:
                filelist_df = pd.read_excel(filelist_path)

            for index, row in filelist_df.iterrows():

                file_id = row['FileID']

                sheet_name = row['SheetName']
                FileName = "Temp "+row['NameExpected']

                file = drive.CreateFile({'id': file_id})
                file.GetContentFile(f'{FileName}.xlsx')

                df = pd.read_excel(f'{FileName}.xlsx', sheet_name=sheet_name)
                csv_path = os.path.join(r'C:\Temp', f"{os.path.splitext(os.path.basename(FileName))[0]}.csv")
                df.to_csv(csv_path, index=False)

                uri = f'file:///{csv_path}?delimiter={{}}&xField={row["LongField"]}&yField={row["LatField"]}'
                layer_name = row['NameExpected']
                layer = QgsVectorLayer(uri.format(','), layer_name, 'delimitedtext')
                layer.dataProvider().addAttributes([QgsField('Nominal_Long', QVariant.Double), QgsField('Nominal_Lat', QVariant.Double)])
                False
                layer.updateFields()
                QgsProject.instance().addMapLayer(layer)
                if os.path.exists(FileName + ".xlsx"):
                    os.remove(FileName + ".xlsx")