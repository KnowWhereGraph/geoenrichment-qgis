# Geoenrichment QGIS

### Download the plugin

1. Navigate to [Releases](https://github.com/KnowWhereGraph/geoenrichment-qgis/releases) to download the latest version
2. Download and extract the zip file on your machine

### Installing the plugin

1. In QGIS, go to menu `Settings` -> `User profiles` -> `Open active profile folder`
2. Next, go to `python` -> `plugins`. That's the plugin folder for QGIS. 
    1. If `plugins` directory does not exist, create one with the same name.
3. Copy the `kwg_geoenrichment` directory from the zip to the plugin directory
4. Restart QGIS
5. Go to menu `Plugins` -> `Manage and Install plugins...` -> `Installed` -> Enable `KWG Geoenrichment`

### Using the plugin

1. Create/open a project (`EPSG:4326 - WGS 84`)
2. Create a new layer in the project for `Open Street Map`
    1.  Open Project Browser
    2.  Select `XYZ Tiles` > `OpenStreetMap`
3. Update `CRS` to `EPSG 4326` (_required_)
4. Open the plugin either from the `Plugins` menu or the `toolbar`

### Report an issue
- If you encounter any issue with the tool or have any feedback, please report on the [Github repository](https://github.com/KnowWhereGraph/geoenrichment-qgis/issues)
