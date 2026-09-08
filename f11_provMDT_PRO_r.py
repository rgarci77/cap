# -*- coding: utf-8 -*-

# **********************************
# Programa: calcula el raster de MDT , rellenando con 2014 si se le indica
# Salida: GMDT_prov y GPTE_prov
#
# Fecha : mayo-2021
# Autor: bvm
#
# ************************************
import arcpy
from arcpy.sa import *
import os
import time

#coje los parametros de la herramienta
dirPrin = arcpy.GetParameterAsText(0) # directorio donde estan las provincias con limite a calcular
ficOri = arcpy.GetParameterAsText(1) # Datos de partida (tif de fotointerpretación)

fcRecorta = arcpy.GetParameterAsText(2) # fc con el límite por el que se recorta zona Lidar2
dirOld = arcpy.GetParameterAsText(3) # directorio con los datos Lidar2
fcProvOld = arcpy.GetParameterAsText(4) # FC con la division provincias Lidar2

totProvp = arcpy.GetParameterAsText(5) # provincias a procesar
totProv = totProvp.split(";")
arcpy.AddMessage(totProv)

# para que machaque si exiten
arcpy.env.overwriteOutput = True

#cojo la licencia de Spatial
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")

# inicio bucle de provincias elegidas
for codProv in totProv:

    #abre el fichero de tiempos
    arcpy.env.workspace = dirPrin
    fictime = open(dirPrin + "\prov" + codProv + "\log_timeF11.txt","a")
    fictime.write('*******************************\n')

    arcpy.AddMessage( "Inicio la provincia: " + codProv + " el " + time.ctime())
    fictime.write('Inicio la provincia ' + codProv + ' el ' + time.ctime() + '\n')

    # configuro directorio de trabajo
    arcpy.env.workspace = dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb"

    #pasa a raster de GDB el MDT
    arcpy.AddMessage("inicio generacion MDT "  + time.ctime())
    arcpy.AddMessage(ficOri)

    if arcpy.Exists("GMDT_ini_" + codProv):
        arcpy.AddMessage("Ya existe GMDT_ini_" + codProv)
    else:
        gtemp = Float(ficOri)
        gtemp.save("GMDT_ini_" + codProv)

    #defino la proyeccion
    dsc = arcpy.Describe("GLIMITE_B210_" + codProv)
    coord_sys = dsc.spatialReference

    arcpy.DefineProjection_management("GMDT_ini_" + codProv, coord_sys)

    #configuro entornoS con buffer
    prov_vec = "GLIMITE_B210_" + codProv
    arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_vec).spatialReference #proyeccion
    arcpy.env.extent = prov_vec  # extension
    arcpy.env.snapRaster = prov_vec  # cuadra los raster
    arcpy.env.mask = prov_vec   # mascara
    arcpy.env.cellSize = prov_vec   #tamaño celda

    # meto informacion del Lidar2 si existe FC limite de recorte
    if fcRecorta:
        arcpy.AddMessage("****************** ")
        arcpy.AddMessage("Meto informacion Lidar2 ")
        fictime.write('Meto informacion Lidar2 ' + '\n')

        # calculo las provincias afectadas
        arcpy.AddMessage("calculo hojas afectadas")
        fictime.write('calculo hojas afectadas ' + '\n')
        arcpy.Identity_analysis (fcRecorta, fcProvOld, "\\PROYE\\mmdt_l2_" + codProv,"ALL","0.001")
        arcpy.Frequency_analysis("\\PROYE\\mmdt_l2_" + codProv,"mdt_l2_frq",["PROVINCIA"])

        #trabajo en cada provincia que intersecta
        cur = arcpy.SearchCursor("mdt_l2_frq")
        for row in cur:
            nL2Prov = row.PROVINCIA
            arcpy.AddMessage("Hoja: " + str(nL2Prov))
            fictime.write('Hoja: ' + str(nL2Prov))

            Raster1 = dirOld + "\\prov" + str(nL2Prov)
            gtemp = ExtractByMask(Raster1, fcRecorta )

            arcpy.AddMessage("Hago mosaico")
            arcpy.Mosaic_management(gtemp,"GMDT_ini_" + codProv,"FIRST")

    #genero raster ajustado a limite
    arcpy.AddMessage("genero MDT final "  + time.ctime())

    if arcpy.Exists("GMDT_" + codProv):
        arcpy.AddMessage("Ya existe GMDT_" + codProv)
    else:
        gtemp = Con(IsNull("GMDT_ini_" + codProv),0,"GMDT_ini_" + codProv)
        gtemp.save("GMDT_" + codProv)

    #genero para comprobar si tiene huecos o falta en borde
    arcpy.AddMessage("genero para comprobar "  + time.ctime())
    fictime.write('genero para comprobar ' + time.ctime() + '\n')

    if arcpy.Exists("gcompru_mdt"):
        arcpy.AddMessage("Ya existe gcompru_mdt")
    else:
        gtemp = Con(IsNull("GMDT_ini_" + codProv),0,1)
        gtemp.save("gcompru_mdt")

    temp = arcpy.RasterToPolygon_conversion("gcompru_mdt","\\PROYE\\temp","NO_SIMPLiFY","VALUE")
    templ = arcpy.FeatureToLine_management(temp, "\\PROYE\\templ", "0.001 Meters", "ATTRIBUTES")
    tempp = arcpy.FeatureToPoint_management(temp, "\\PROYE\\tempp", "INSIDE")
    arcpy.FeatureToPolygon_management(templ, "\\PROYE\\compru_mdt_" + codProv,"0.001 Meters","", tempp)

    #limpio
    if arcpy.Exists("GMDT_ini_" + codProv):
        arcpy.Delete_management("GMDT_ini_" + codProv)
    if arcpy.Exists("temp"):
        arcpy.Delete_management("temp")
    if arcpy.Exists("templ"):
        arcpy.Delete_management("templ")
    if arcpy.Exists("tempp"):
        arcpy.Delete_management("tempp")




fictime.write('TERMINÉ TODO a las ' + time.ctime() + '\n')
fictime.write('*****************************************\n')
fictime.close()
arcpy.AddMessage("TERMINÉ TODO a las " + time.ctime())
arcpy.AddMessage("¡¡Acuerdate de revisar los huecos rellenado a 0 - compru_mdt!!" )










