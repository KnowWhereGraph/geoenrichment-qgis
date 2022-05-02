# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kwg_geoenrichment
                                 A QGIS plugin
 KWG Geoenrichment plugin
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-04
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Rushiraj Nenuji, University of California Santa Barbara
        email                : nenuji@nceas.ucsb.edu
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
import json
import logging
import os.path
from configparser import ConfigParser
from qgis.PyQt.QtCore import QTranslator, QSettings, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QLineEdit, QComboBox, QHeaderView
from qgis.core import QgsFeature, QgsProject, QgsGeometry, \
    QgsCoordinateTransform, QgsCoordinateTransformContext, QgsMapLayer, \
    QgsFeatureRequest, QgsVectorLayer, QgsLayerTreeGroup, QgsRenderContext, \
    QgsCoordinateReferenceSystem, QgsMessageLog, Qgis, QgsFields, QgsField, QgsVectorFileWriter, QgsLayerTreeLayer

from typing import re
import statistics

# Import QDraw settings
from .drawtools import DrawPolygon, \
    SelectPoint
from .kwg_plugin_dialog import kwg_pluginDialog
from .kwg_plugin_enrichment_dialog import kwg_pluginEnrichmentDialog
from .kwg_sparqlquery import kwg_sparqlquery
from .kwg_sparqlutil import kwg_sparqlutil
from .kwg_util import kwg_util as UTIL
from .qdrawsettings import QdrawSettings

# Initialize Qt resources from file resources.py
# Import the code for the dialog

_SPARQL_ENDPOINT_DICT = {
    "prod": {
        "KWG-V2": "https://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V2",
        "KWG-V3": "https://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG-V3",
        "KWG": "https://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG",
    },
    "test": {
        "plume_soil_wildfire": "http://stko-roy.geog.ucsb.edu:7202/repositories/plume_soil_wildfire",
    }
}


class kwg_geoenrichment:
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
            'kwg_geoenrichment_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&KnowWhereGraph')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        # QDraw specific configs
        self.sb = self.iface.statusBarIface()
        self.tool = None
        self.toolname = None
        self.toolbar = self.iface.addToolBar('KWG Geoenrichment')
        self.toolbar.setObjectName('KWG Geoenrichment')
        self.bGeom = None
        self.settings = QdrawSettings()

        self.path = os.path.dirname(os.path.abspath(__file__))

        # Set up the config file
        conf = ConfigParser()
        self._config = conf.read('config.ini')
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)  # or whatever
        self.path = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(self.path + "/logs"):
            os.makedirs(self.path + "/logs")
        handler = logging.FileHandler(self.path + '/logs/kwg_geoenrichment.log', 'w+', 'utf-8')  # or whatever
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')  # or whatever
        handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
        self.logger.addHandler(handler)

        self.sparqlQuery = kwg_sparqlquery()
        self.sparqlUtil = kwg_sparqlutil()
        self.eventPlaceTypeDict = dict()
        self.kwg_endpoint_dict = _SPARQL_ENDPOINT_DICT

        self.contentCounter = 0
        self.mergeRuleDict = {
            "1 - Get the first value found": "first",
            "2 - Concate values together with a '|'": "concat",
            "3 - Get the number of values found": "count",
            "4 - Get the average of all values(numeric)": "avg",
            "5 - Get the highest value (numeric)": "high",
            "6 - Get the lowest value (numeric)": "low",
            "7 - Get the standard deviation of all values (numeric)": "stdev",
            "8 - Get the total of all values (numeric)": "total",
        }

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
        return QCoreApplication.translate('kwg_geoenrichment', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            checkable=False,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            menu=None,
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
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if menu is not None:
            action.setMenu(menu)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # self.app.setStylesheet(open("style.qss", "r").read())

        # will be set False in run()
        self.first_start = True

        icon_path = self.path + "/resources/graph_Query.png"
        if self.first_start:
            self.add_action(
                QIcon(icon_path),
                text=self.tr(u'&Geoenrichment'),
                callback=self.run,
                parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&KnowWhereGraph'),
                action)
            self.iface.removeToolBarIcon(action)
            del self.toolbar

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False

        self.dlg = kwg_pluginDialog()

        self.enrichmentObjBuffer = []

        # show the dialog
        self.dlg.show()

        # get the geometry from the user
        self.dlg.pushButton_polygon.clicked.connect(self.drawPolygon)

        # get contents (open another dialog box)
        self.dlg.pushButton_content.clicked.connect(self.addContent)

        self.dlg.pushButton_run.clicked.connect(self.handleRun)

        # show the table
        self.setUPMergeTable()

        # Run the dialog event loop
        result = self.dlg.exec_()
        return

    def drawPolygon(self, sender=None):
        if self.tool:
            self.tool.reset()
        self.tool = DrawPolygon(self.iface, self.settings.getColor())
        # self.tool.setAction(self.actions[4])
        if sender == "explore":
            self.tool.selectionDone.connect(lambda: self.drawExplore())
        else:
            self.tool.selectionDone.connect(lambda: self.draw())
        self.tool.move.connect(self.updateSB)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawPolygon'
        self.resetSB()

    def drawBuffer(self):
        self.bGeom = None
        if self.tool:
            self.tool.reset()
        self.tool = SelectPoint(self.iface, self.settings.getColor())
        self.actions[5].setIcon(
            QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawT.png'))
        self.actions[5].setText(
            self.tr('Buffer drawing tool on the selected layer'))
        self.actions[5].triggered.disconnect()
        self.actions[5].triggered.connect(self.drawBuffer)
        self.actions[5].menu().actions()[0].setIcon(
            QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawTP.png'))
        self.actions[5].menu().actions()[0].setText(
            self.tr('Polygon buffer drawing tool on the selected layer'))
        self.actions[5].menu().actions()[0].triggered.disconnect()
        self.actions[5].menu().actions()[0].triggered.connect(
            self.drawPolygonBuffer)
        self.tool.setAction(self.actions[5])
        self.tool.select.connect(self.selectBuffer)
        self.tool.selectionDone.connect(self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawBuffer'
        self.resetSB()

    def drawPolygonBuffer(self):
        self.bGeom = None
        if self.tool:
            self.tool.reset()
        self.tool = DrawPolygon(self.iface, self.settings.getColor())
        self.actions[5].setIcon(
            QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawTP.png'))
        self.actions[5].setText(
            self.tr('Polygon buffer drawing tool on the selected layer'))
        self.actions[5].triggered.disconnect()
        self.actions[5].triggered.connect(self.drawPolygonBuffer)
        self.actions[5].menu().actions()[0].setIcon(
            QIcon(':/plugins/kwg_geoenrichment/resources/icon_DrawT.png'))
        self.actions[5].menu().actions()[0].setText(
            self.tr('Buffer drawing tool on the selected layer'))
        self.actions[5].menu().actions()[0].triggered.disconnect()
        self.actions[5].menu().actions()[0].triggered.connect(self.drawBuffer)
        self.tool.setAction(self.actions[5])
        self.tool.selectionDone.connect(self.selectBuffer)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawBuffer'
        self.resetSB()

    def showSettingsWindow(self):
        self.settings.settingsChanged.connect(self.settingsChangedSlot)
        self.settings.show()

    # triggered when a setting is changed
    def settingsChangedSlot(self):
        if self.tool:
            self.tool.rb.setColor(self.settings.getColor())

    def resetSB(self):
        message = {
            'drawPoint': 'Left click to place a point.',
            'drawLine': 'Left click to place points. Right click to confirm.',
            'drawRect': 'Maintain the left click to draw a rectangle.',
            'drawCircle': 'Maintain the left click to draw a circle. \
Simple Left click to give a perimeter.',
            'drawPolygon': 'Left click to place points. Right click to \
confirm.',
            'drawBuffer': 'Select a vector layer in the Layer Tree, \
then select an entity on the map.'
        }
        self.sb.showMessage(self.tr(message[self.toolname]))

    def updateSB(self):
        g = self.geomTransform(
            self.tool.rb.asGeometry(),
            self.iface.mapCanvas().mapSettings().destinationCrs(),
            QgsCoordinateReferenceSystem.fromEpsgId(2154))
        if self.toolname == 'drawLine':
            if g.length() >= 0:
                self.sb.showMessage(
                    self.tr('Length') + ': ' + str("%.2f" % g.length()) + " m")
            else:
                self.sb.showMessage(self.tr('Length') + ': ' + "0 m")
        else:
            if g.area() >= 0:
                self.sb.showMessage(
                    self.tr('Area') + ': ' + str("%.2f" % g.area()) + " m" + u'²')
            else:
                self.sb.showMessage(self.tr('Area') + ': ' + "0 m" + u'²')
        self.iface.mapCanvas().mapSettings().destinationCrs().authid()

    def geomTransform(self, geom, crs_orig, crs_dest):
        g = QgsGeometry(geom)
        crsTransform = QgsCoordinateTransform(
            crs_orig, crs_dest, QgsCoordinateTransformContext())  # which context ?
        g.transform(crsTransform)
        return g

    def selectBuffer(self):
        rb = self.tool.rb
        if isinstance(self.tool, DrawPolygon):
            rbSelect = self.tool.rb
        else:
            rbSelect = self.tool.rbSelect
        layer = self.iface.layerTreeView().currentLayer()
        if layer is not None and layer.type() == QgsMapLayer.VectorLayer \
                and self.iface.layerTreeView().currentNode().isVisible():
            # rubberband reprojection
            g = self.geomTransform(
                rbSelect.asGeometry(),
                self.iface.mapCanvas().mapSettings().destinationCrs(),
                layer.crs())
            features = layer.getFeatures(QgsFeatureRequest(g.boundingBox()))
            rbGeom = []
            for feature in features:
                geom = feature.geometry()
                try:
                    if g.intersects(geom):
                        rbGeom.append(feature.geometry())
                except:
                    # there's an error but it intersects
                    # fix_print_with_import
                    print('error with ' + layer.name() + ' on ' + str(feature.id()))
                    rbGeom.append(feature.geometry())
            if len(rbGeom) > 0:
                for geometry in rbGeom:
                    if rbGeom[0].combine(geometry) is not None:
                        if self.bGeom is None:
                            self.bGeom = geometry
                        else:
                            self.bGeom = self.bGeom.combine(geometry)
                rb.setToGeometry(self.bGeom, layer)
        if isinstance(self.tool, DrawPolygon):
            self.draw()

    def draw(self):
        rb = self.tool.rb
        g = rb.asGeometry()

        ok = True
        warning = False
        errBuffer_noAtt = False
        errBuffer_Vertices = False

        layer = self.iface.layerTreeView().currentLayer()
        if self.toolname == 'drawBuffer':
            if self.bGeom is None:
                warning = True
                errBuffer_noAtt = True
            else:
                perim, ok = QInputDialog.getDouble(
                    self.iface.mainWindow(), self.tr('Perimeter'),
                    self.tr('Give a perimeter in m:')
                    + '\n' + self.tr('(works only with metric crs)'),
                    min=0)
                g = self.bGeom.buffer(perim, 40)
                rb.setToGeometry(g, QgsVectorLayer(
                    "Polygon?crs=" + layer.crs().authid(), "", "memory"))
                if g.length() == 0 and ok:
                    warning = True
                    errBuffer_Vertices = True

        if self.toolname == 'drawCopies':
            if g.length() < 0:
                warning = True
                errBuffer_noAtt = True

        if ok and not warning:

            name = "geo_enrichment_polygon"
            pjt = QgsProject.instance()
            if pjt.layerTreeRoot().findGroup(self.tr('Geometry')) is not None:
                group = pjt.layerTreeRoot().findGroup(
                    self.tr('Geometry'))

                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        QgsProject.instance().removeMapLayer(child.layerId())

            # save the buffer
            if self.drawShape == 'point':
                layer = QgsVectorLayer(
                    "Point?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
                        'Geometry') + ":string(255)", name, "memory")
                g = g.centroid()  # force geometry as point
            elif self.drawShape == 'XYpoint':
                layer = QgsVectorLayer(
                    "Point?crs=" + self.XYcrs.authid() + "&field=" + self.tr('Geometry') + ":string(255)", name,
                    "memory")
                g = g.centroid()
            elif self.drawShape == 'line':
                layer = QgsVectorLayer(
                    "LineString?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
                        'Geometry') + ":string(255)", name, "memory")
                # fix_print_with_import
                print(
                    "LineString?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
                        'Geometry') + ":string(255)")
            else:
                layer = QgsVectorLayer(
                    "Polygon?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
                        'Geometry') + ":string(255)", name, "memory")

            layer.startEditing()
            symbols = layer.renderer().symbols(QgsRenderContext())  # todo which context ?
            symbols[0].setColor(self.settings.getColor())
            feature = QgsFeature()
            feature.setGeometry(g)
            feature.setAttributes([name])
            layer.dataProvider().addFeatures([feature])
            layer.commitChanges()


            pjt.addMapLayer(layer, False)
            if pjt.layerTreeRoot().findGroup(self.tr('Geometry')) is None:
                pjt.layerTreeRoot().insertChildNode(
                    0, QgsLayerTreeGroup(self.tr('Geometry')))
            group = pjt.layerTreeRoot().findGroup(
                self.tr('Geometry'))
            group.insertLayer(0, layer)
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
            self.iface.mapCanvas().refresh()
            QgsMessageLog.logMessage("Your polygon has been saved to a layer", "kwg_geoenrichment", level=Qgis.Info)

        self.tool.reset()
        self.resetSB()
        self.bGeom = None

    def getInputs(self):
        params = {}
        endPointKey, endPointVal = self.dlg.comboBox_endPoint.currentText().split(" - ")
        params["end_point"] = self.kwg_endpoint_dict[endPointVal[1:-1]][endPointKey]
        params["relation_type"] = self.dlg.comboBox_spatialRelationshipFilter.currentText()

        # get the function
        geosparql_func = list()
        if params["relation_type"] == "CONTAINS + INTERSECTS":
            geosparql_func = ["geo:sfContains", "geo:sfIntersects"]
        elif params["relation_type"] == "CONTAINS":
            geosparql_func = ["geo:sfContains"]
        elif params["relation_type"] == "WITHIN":
            geosparql_func = ["geo:sfWithin"]
        elif params["relation_type"] == "INTERSECTS":
            geosparql_func = ["geo:sfIntersects"]
        else:
            QgsMessageLog.logMessage("The spatial relation is not supported!", "kwg_geoenrichment", level=Qgis.Critical)

        params["wkt_literal"] = self.performWKTConversion()

        params["geosparql_func"] = geosparql_func

        return params

    def setUPMergeTable(self):
        self.dlg.tableWidget.setColumnCount(2)
        self.dlg.tableWidget.verticalHeader().setVisible(False)
        self.dlg.tableWidget.horizontalHeader().setVisible(False)
        self.dlg.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def addContent(self):

        params = self.getInputs()
        params["ifaceObj"] = self.iface
        contentItems = {}

        self.enrichmentObjBuffer.append(kwg_pluginEnrichmentDialog())

        self.enrichmentObjBuffer[self.contentCounter].show()
        self.enrichmentObjBuffer[self.contentCounter].setParams(params)
        self.enrichmentObjBuffer[self.contentCounter].execute()
        self.enrichmentObjBuffer[self.contentCounter].pushButton_save.clicked.connect(self.saveContent)

        self.contentCounter += 1

        return

    def saveContent(self):
        i = self.enrichmentObjBuffer[self.contentCounter - 1].degreeCount
        selectedVal = []
        for it in range(i):
            selectedVal.append(self.enrichmentObjBuffer[self.contentCounter - 1].tableWidget.cellWidget(it, 0).currentText())
            selectedVal.append(self.enrichmentObjBuffer[self.contentCounter - 1].tableWidget.cellWidget(it, 1).currentText())
        selectedVal.append(self.enrichmentObjBuffer[self.contentCounter - 1].tableWidget.cellWidget(i - 1, 2).currentText())

        stringVal = " - ".join(selectedVal)

        self.enrichmentObjBuffer[self.contentCounter - 1].close()
        self.dlg.listWidget.addItem(stringVal)
        objectName = self.enrichmentObjBuffer[self.contentCounter - 1].tableWidget.cellWidget(i - 1, 2).currentText()
        if objectName is None or objectName == "--- SELECT ---" or objectName == "LITERAL":
            objectName = self.enrichmentObjBuffer[self.contentCounter - 1].tableWidget.cellWidget(i - 1,
                                                                                                  1).currentText()
        self.updatePropMergeItem(objName=objectName)
        return

    def updatePropMergeItem(self, objName):
        self.dlg.tableWidget.insertRow(self.contentCounter - 1)
        objLine = QLineEdit()
        objLine.setText(objName)
        comboBox_M = QComboBox()
        for txt in [
                "1 - Get the first value found",
                "2 - Concate values together with a '|'",
                "3 - Get the number of values found",
                "4 - Get the average of all values (numeric)",
                "5 - Get the highest value (numeric)",
                "6 - Get the lowest value (numeric)",
                "7 - Get the standard deviation of all values (numeric)",
                "8 - Get the total of all values (numeric)"
            ]:
            comboBox_M.addItem(txt)

        self.dlg.tableWidget.setCellWidget(self.contentCounter - 1, 0, objLine)
        self.dlg.tableWidget.setCellWidget(self.contentCounter - 1, 1, comboBox_M)

    def handleRun(self):
        for i in range(self.contentCounter):
            results = self.enrichmentObjBuffer[i].getResults()
            degreeCount = self.enrichmentObjBuffer[i].getDegree()

            objName = self.dlg.tableWidget.cellWidget(i, 0).text()
            layerName = self.dlg.lineEdit_layerName.text()
            mergeRule = self.dlg.tableWidget.cellWidget(i, 1).currentText()
            mergeRuleName = self.mergeRuleDict[mergeRule]
            mergeRuleNo = int(mergeRule.split(" - ")[0])

            self.createGeoPackage(results, objName, layerName, mergeRuleName, degreeCount, mergeRule=mergeRuleNo, out_path=self.path)
        self.dlg.close()
        self.contentCounter = 0

    def performWKTConversion(self):
        layers = QgsProject.instance().mapLayers().values()

        # crs = QgsCoordinateReferenceSystem("EPSG:4326")
        for layer in layers:
            if layer.name() == "geo_enrichment_polygon":
                feat = layer.getFeatures()
                for f in feat:
                    geom = f.geometry()

                    # TODO: handle the CRS
                    # geom = self.transformSourceCRStoDestinationCRS(geom)
                    wkt = geom.asWkt()
                break

        wkt_literal_list = wkt.split(" ", 1)
        wkt_rep = ""
        wkt_rep = wkt_literal_list[0].upper() + wkt_literal_list[1]

        return wkt_rep

    def transformSourceCRStoDestinationCRS(self, geom, src=3857, dest=4326):
        src_crs = QgsCoordinateReferenceSystem(src)
        dest_crs = QgsCoordinateReferenceSystem(dest)
        geom_converter = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
        geom_reproj = geom_converter.transform(geom)
        return geom_reproj

    def createGeoPackage(self, GeoQueryResult, objName="O", layerName="geo_results", mergeRuleName="first", degreeCount = 0, mergeRule = 1,
                         out_path=None):
        '''
        GeoQueryResult: a sparql query result json obj serialized as a list of dict()
                    SPARQL query like this:
                    select distinct ?place ?placeLabel ?placeFlatType ?wkt
                    where
                    {...}
        out_path: the output path for the create geo feature class
        inPlaceType: the label of user spercified type IRI
        selectedURL: the user spercified type IRI
        isDirectInstance: True: use placeFlatType as the type of geo-entity
                          False: use selectedURL as the type of geo-entity
        '''
        # a set of unique WKT for each found places
        out_path += objName + ".gpkg"
        objIRISet = set()
        objList = []
        geom_type = None

        util_obj = UTIL()

        objIRISet, entityDict = self.generateRecord(GeoQueryResult, mergeRule)

        for gtype in entityDict:

            layerFields = QgsFields()
            layerFields.append(QgsField('entity', QVariant.String))
            layerFields.append(QgsField('entityLabel', QVariant.String))
            layerFields.append(QgsField(objName, QVariant.String))

            objList = []
            for entity in entityDict[gtype]:
                objList.append(
                    [entity, entityDict[gtype][entity]["label"], entityDict[gtype][entity]["o"], entityDict[gtype][entity]["wkt"]])

            vl = QgsVectorLayer(gtype + "?crs=epsg:4326", "%s_%s_%s"%(layerName, objName, gtype), "memory")
            pr = vl.dataProvider()
            pr.addAttributes(layerFields)
            vl.updateFields()

            if len(objList) == 0:
                QgsMessageLog.logMessage("No results found!",
                                         level=Qgis.Info)
            else:

                if out_path == None:
                    QgsMessageLog.logMessage("No data will be added to the map document.", level=Qgis.Info)
                else:
                    vl.startEditing()
                    for item in objList:
                        entity_iri, entity_label, o, wkt_literal = item
                        wkt = wkt_literal.replace("<http://www.opengis.net/def/crs/OGC/1.3/CRS84>", "")

                        feat = QgsFeature()
                        geom = QgsGeometry.fromWkt(wkt)

                        feat.setGeometry(geom)
                        feat.setAttributes(item[0:3])

                        vl.addFeature(feat)
                    vl.endEditCommand()
                    vl.commitChanges()
                    vl.updateExtents()

                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.layerName = "%s_%s_%s"%(layerName, objName, gtype)
                    context = QgsProject.instance().transformContext()
                    error = QgsVectorFileWriter.writeAsVectorFormatV2(vl, out_path, context, options)
                    QgsProject.instance().addMapLayer(vl)

        return error[0] == QgsVectorFileWriter.NoError


    def generateRecord(self, GeoQueryResult = {}, mergeRule = 1):

        util_obj = UTIL()
        objIRISet = set()
        entityDict= {}

        for idx, item in enumerate(GeoQueryResult):
            wkt_literal = item["wkt"]["value"]
            geom_type = util_obj.get_geometry_type_from_wkt(wkt_literal)
            entityVal = item["entity"]["value"]

            if len(objIRISet) == 0 or entityVal not in objIRISet:
                objIRISet.add(entityVal)

            entityLabelVal = item["entityLabel"]["value"]
            entityOVal = item['o']["value"]
            if geom_type != "0":
                if geom_type not in entityDict:
                    entityDict[geom_type] = {}
                if entityVal not in entityDict[geom_type]:
                    entityDict[geom_type][entityVal] = {}
                    entityDict[geom_type][entityVal]["label"] = entityLabelVal
                    entityDict[geom_type][entityVal]["o"] = []
                    entityDict[geom_type][entityVal]["o"].append(entityOVal)
                    entityDict[geom_type][entityVal]["wkt"] = wkt_literal
                else:
                    entityDict[geom_type][entityVal]["label"] = entityLabelVal
                    entityDict[geom_type][entityVal]["o"].append(entityOVal)
                    entityDict[geom_type][entityVal]["wkt"] = wkt_literal
            else:
                self.logger.info("Geometry not found; expunging record")
        entityDict = self.generateFormattedEntityDict(entityDict, mergeRule)
        return objIRISet, entityDict


    def generateFormattedEntityDict(self, entityDict = {}, mergeRule = 1):
        for gtype in entityDict:
            for eVal in entityDict[gtype]:
                if mergeRule == 1:
                    entityDict[gtype][eVal]["o"] = entityDict[gtype][eVal]["o"][0]
                if mergeRule == 2:
                    entityDict[gtype][eVal]["o"] = " | ".join(entityDict[gtype][eVal]["o"])
                if mergeRule == 3:
                    entityDict[gtype][eVal]["o"] = len(entityDict[gtype][eVal]["o"])
                if mergeRule == 4:
                    temp_li = []
                    for idx, val in enumerate(entityDict[gtype][eVal]["o"]):
                        try:
                            temp_li.append(self.parse_str(val))
                        except:
                            continue
                    entityDict[gtype][eVal]["o"] = sum(temp_li) / len(temp_li)
                if mergeRule == 5:
                    temp_li = []
                    for idx, val in enumerate(entityDict[gtype][eVal]["o"]):
                        try:
                            temp_li.append(self.parse_str(val))
                        except:
                            continue
                    entityDict[gtype][eVal]["o"] = max(temp_li)
                if mergeRule == 6:
                    temp_li = []
                    for idx, val in enumerate(entityDict[gtype][eVal]["o"]):
                        try:
                            temp_li.append(self.parse_str(val))
                        except:
                            continue
                    entityDict[gtype][eVal]["o"] = min(temp_li)
                if mergeRule == 7:
                    temp_li = []
                    for idx, val in enumerate(entityDict[gtype][eVal]["o"]):
                        try:
                            temp_li.append(self.parse_str(val))
                        except:
                            continue
                    entityDict[gtype][eVal]["o"] = statistics.stdev(temp_li)
                if mergeRule == 8:
                    temp_li = []
                    for idx, val in enumerate(entityDict[gtype][eVal]["o"]):
                        try:
                            temp_li.append(self.parse_str(val))
                        except:
                            continue
                    entityDict[gtype][eVal]["o"] = sum(temp_li)

        return entityDict

    def parse_str(self, num):
        """
        Parse a string that is expected to contain a number.
        :param num: str. the number in string.
        :return: float or int. Parsed num.
        """
        if not isinstance(num, str):  # optional - check type
            raise TypeError('num should be a str. Got {}.'.format(type(num)))
        if re.compile('^\s*\d+\s*$').search(num):
            return int(num)
        if re.compile('^\s*(\d*\.\d+)|(\d+\.\d*)\s*$').search(num):
            return float(num)
        raise ValueError('num is not a number. Got {}.'.format(num))  # optional