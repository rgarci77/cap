# **********************************
# Programa: calcula el valor medio por recinto para 2024- Lidar3
# Salida: tabla
#
# Fecha : octubre-2021
# Autor: masm, bvm
#
# ************************************
import arcpy
from arcpy.sa import *
import os
import time

#coje los parametros de la herramienta
dirPrin = arcpy.GetParameterAsText(0) # directorio generar donde estan las provincias con los rasters
shp_rec = arcpy.GetParameterAsText(1) # shape del sigpac
bd_rec = arcpy.GetParameterAsText(2) # fichero con uso sigpac
mun_ini = arcpy.GetParameterAsText(3) # numero de municipio a partir del que se quiere procesar
codProv = arcpy.GetParameterAsText(4) # provincia a procesar
repgeo = arcpy.GetParameterAsText(5) # reparar geometria
# arcpy.AddMessage(repgeo)

arcpy.AddMessage(codProv)


# para que machaque si existen
arcpy.env.overwriteOutput = True

# Cojo la licencia de Spatial
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
    arcpy.AddMessage(f"{time.ctime()} - Licencia 'Spatial Analyst' disponible")
else:
    arcpy.AddError("Licencia 'Spatial Analyst' no disponible. Abortando.")
    raise SystemExit

#abre el fichero de tiempos
arcpy.env.workspace = dirPrin
fictime = open(dirPrin + "\prov" + codProv + "\log_timeF55.txt","a")
fictime.write('*******************************\n')

arcpy.AddMessage( "Inicio la provincia: " + codProv + " el " + time.ctime())
fictime.write('Inicio la provincia ' + codProv + ' el ' + time.ctime() + '\n')

# configuro directorio de trabajo
gdb_trabajo = os.path.join(dirPrin, f"prov{codProv}", f"prov{codProv}.gdb")
arcpy.env.workspace = gdb_trabajo

#*********************************
# configuro entornoS

prov_ras = dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\GLIMITE_" + codProv
dsc = arcpy.Describe(prov_ras)
coord_sys = dsc.spatialReference

#se asegura de trabajar en = proyeccion que los grid
arcpy.env.outputCoordinateSystem = coord_sys #proyeccion

#recinto sigpac
if int(mun_ini)  == 1:
    arcpy.AddMessage("muni_ini = 1")
    #arcpy.MakeFeatureLayer_management(shp_rec, "shp_layer")#20211114
    #arcpy.AddJoin_management("shp_layer","DN_OID",bd_rec,"DN_OID")#20211114
    #arcpy.CopyFeatures_management("shp_layer", dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE\\precfe_" + codProv)#20211114
    #vshp_recp = dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE\\precfe_" + codProv

    vshp_recp = arcpy.FeatureClassToFeatureClass_conversion(shp_rec,dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE","precfe_" + codProv ) #por si distinta proyeccion
    arcpy.JoinField_management(vshp_recp, "DN_OID", bd_rec, "DN_OID")

else:
    arcpy.AddMessage("muni_ini distinto de 1")
    vshp_recp = dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE\\precfe_" + codProv
    arcpy.RemoveIndex_management(vshp_recp, ["iID_UNICO"])

#extension con un margen de 100m
desc = arcpy.Describe(vshp_recp)
xmin = (int (desc.extent.XMin / 5) * 5) - 100
ymin = (int (desc.extent.YMin / 5) * 5) - 100
xmax = ((int (desc.extent.XMax / 5) * 5) + 5) + 100
ymax = ((int (desc.extent.YMax / 5) * 5) + 5) + 100

arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax)) #extension
arcpy.env.snapRaster = prov_ras  # cuadra los raster
arcpy.env.mask = prov_ras   # mascara
arcpy.env.cellSize = prov_ras   #tama?o celda

#***************************************************
# preparo raster

arcpy.AddMessage( "Preparo rasters a las " + time.ctime())
fictime.write('preparo rasters a las ' + time.ctime() + '\n')

vgalt = Raster("gmdt_" + str(codProv)) #20221020
vgpte = Raster("gpte_" + str(codProv)) #20211116

vgcsp = Raster("gcsp_" + str(codProv))

vgfsue = Raster("gfsue_" + str(codProv))
vgfpte = Raster("gfpte_" + str(codProv))
vgfveg = Raster("gfveg_" + str(codProv))
vgfveges = Raster("gfvegesp_" + str(codProv))
vgfinc = Raster("gfinc_" + str(codProv))

if arcpy.Exists("GFESPDE_" + codProv): #20211111
    arcpy.AddMessage("Existe Fdehesa")
    fictime.write('Existe Fdehesa ' + '\n')
    gtemp_deh = Con(IsNull("GDEH_" + codProv),0,1) #20211125
    gtemp_fespde = Con(IsNull("GFESPDE_" + codProv),0,1)

if arcpy.Exists("GFESPES_" + codProv): #20211111
    arcpy.AddMessage("Existe Fespecie CCAA")
    fictime.write('Existe Fespecie CCAA ' + '\n')
    gtemp_esp = Con(IsNull("GESP_" + codProv),0,1) #20211125
    gtemp_fespes = Con(IsNull("GFESPES_" + codProv),0,1)

if arcpy.Exists("GFESP_" + codProv): #20211111
    arcpy.AddMessage("Existe Fespecie total")
    fictime.write('Existe Fespecie total ' + '\n')
    gtemp_fesp = Con(IsNull("GFESP_" + codProv),0,1)


#************************************************
# preparo shape

arcpy.AddMessage( "Preparo vectorial a las " + time.ctime())
fictime.write('preparo vectorial a las ' + time.ctime() + '\n')

if int(mun_ini)  == 1:
    # preparo campos de salida
    arcpy.AddField_management(vshp_recp,"ID_UNICO","LONG")
    arcpy.AddField_management(vshp_recp,"ALT_NEW","DOUBLE",10,6) #20221020
    arcpy.AddField_management(vshp_recp,"PTE","DOUBLE",10,6) #20211116
    arcpy.AddField_management(vshp_recp,"CSP","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"F_SUE","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"F_PTE","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"F_VEG","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"POR_DEH","DOUBLE",10,6) #20211125
    arcpy.AddField_management(vshp_recp,"POR_FESPDE","DOUBLE",10,6) #20211111
    arcpy.AddField_management(vshp_recp,"POR_ESP","DOUBLE",10,6) #20211125
    arcpy.AddField_management(vshp_recp,"POR_FESPES","DOUBLE",10,6) #20211111
    arcpy.AddField_management(vshp_recp,"POR_FESP","DOUBLE",10,6) #20211111
    arcpy.AddField_management(vshp_recp,"F_VEGES","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"F_INC","DOUBLE",10,6)
    arcpy.AddField_management(vshp_recp,"CSPI","LONG")
    arcpy.AddField_management(vshp_recp,"CSP_RES","DOUBLE")
    arcpy.AddField_management(vshp_recp,"TMP1","SHORT")
    arcpy.AddField_management(vshp_recp,"TMP2","SHORT")
    arcpy.AddField_management(vshp_recp,"TMP3","DOUBLE",10,6)

    arcpy.AddField_management(vshp_recp,"SOLAPES","LONG")
    arcpy.AddField_management(vshp_recp,"SOLAPES2","LONG")


    # inicializo a -1
    #arcpy.MakeFeatureLayer_management(vshp_recp, "lyshprec")

    arcpy.CalculateField_management(vshp_recp,"ID_UNICO","!OBJECTID!", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"ALT_NEW","-1", "PYTHON") #20221020
    arcpy.CalculateField_management(vshp_recp,"PTE","-1", "PYTHON") #20211116
    arcpy.CalculateField_management(vshp_recp,"CSP","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"F_SUE","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"F_PTE","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"F_VEG","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"POR_DEH","0", "PYTHON") #20211125
    arcpy.CalculateField_management(vshp_recp,"POR_FESPDE","0", "PYTHON") #20211111
    arcpy.CalculateField_management(vshp_recp,"POR_ESP","0", "PYTHON") #20211125
    arcpy.CalculateField_management(vshp_recp,"POR_FESPES","0", "PYTHON") #20211111
    arcpy.CalculateField_management(vshp_recp,"POR_FESP","0", "PYTHON") #20211111
    arcpy.CalculateField_management(vshp_recp,"F_VEGES","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"F_INC","-1", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"CSP_RES","-1", "PYTHON")

    arcpy.CalculateField_management(vshp_recp,"SOLAPES","0", "PYTHON")
    arcpy.CalculateField_management(vshp_recp,"SOLAPES2","0", "PYTHON")

# reparo geometria
if repgeo == "true":
    arcpy.AddMessage( "Reparo geometria")
    arcpy.CheckGeometry_management(vshp_recp, dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\ErrGeoSigp_" + str(codProv))

    arcpy.RepairGeometry_management(vshp_recp)
else:
    arcpy.AddMessage( "NO Reparo geometria")

# meto las coordenada del geocentro # nuevo 20230601
arcpy.AddGeometryAttributes_management(vshp_recp, "CENTROID_INSIDE","#","#","GEOGCS['GCS_ETRS_1989',DATUM['D_ETRS_1989',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]") #20230601


#hago la layer
arcpy.MakeFeatureLayer_management(vshp_recp, "lyshprec")
arcpy.AddIndex_management("lyshprec", "ID_UNICO", "iID_UNICO", "UNIQUE","ASCENDING")

nreg1 = int(arcpy.GetCount_management("lyshprec").getOutput(0))
arcpy.AddMessage("Recintos totales de la provincia :" + str(nreg1))

# saco el listado de municipios - RECFE_TXT2
arcpy.Frequency_analysis("lyshprec", "recfe_txt2",["MUNICIPIO"])
nunmun = int(arcpy.GetCount_management("recfe_txt2").getOutput(0))
arcpy.AddMessage(" Número de municipios del fichero:" + str(nunmun))
fictime.write('Número de municipios del fichero: ' + str(nunmun) + '\n')

#inicio cursor por municipio
cur = arcpy.SearchCursor("recfe_txt2")
for row in cur:
    rec = row.getValue("OBJECTID")
    mun = row.getValue("MUNICIPIO")
    if int(mun) >= int(mun_ini):
        arcpy.AddMessage("***************************************")
        arcpy.AddMessage("Procesando " + str(rec) + " de " + str(nunmun) + " - Municipio: " + str(mun) + " a las " + time.ctime())
        arcpy.AddMessage("***************************************")
        fictime.write('Procesando ' + str(rec) + ' de ' + str(nunmun) + ' - Municipio: ' + str(mun) + ' a las ' + time.ctime() + '\n')

        # genero Fc con el municipio a procesar
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"MUNICIPIO\" =" +  str(mun) )
        if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
            arcpy.AddMessage ("Número de recintos: " + str(arcpy.GetCount_management("lyshprec").getOutput(0)))
            fictime.write('Número de recintos: ' + str(arcpy.GetCount_management("lyshprec").getOutput(0) + '\n'))

            vshp_mun = arcpy.FeatureClassToFeatureClass_conversion("lyshprec", dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE", "sigp_muni")
            arcpy.MakeFeatureLayer_management(vshp_mun, "lyshprec2")

            # detecto solapes
            arcpy.AddMessage( "Inicio bucle de solapes")
            RecSol = 1
            RecVue = 1
            while RecSol > 0:
                RecSol = 0
                arcpy.AddMessage ("******************************")
                arcpy.AddMessage ("Inicio vuelta: " + str(RecVue))

                arcpy.SelectLayerByAttribute_management("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0")
                arcpy.PolygonNeighbors_analysis("lyshprec2", dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\temp", "ID_UNICO", "AREA_OVERLAP","","0.001")

                arcpy.MakeTableView_management("temp", "lytemp")
                arcpy.SelectLayerByAttribute_management("lytemp", "NEW_SELECTION", "\"AREA\" > 0")
                nreg1 = int(arcpy.GetCount_management("lytemp").getOutput(0))
                #arcpy.AddMessage("solapan :" + str(nreg1))
                if nreg1 > 0:
                    arcpy.CopyRows_management("lytemp", dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\SolapesSigp_" + str(codProv))

                    #saco numero solapes
                    arcpy.Frequency_analysis("SolapesSigp_" + str(codProv), "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO")
                    nreg2 = int(arcpy.GetCount_management("SolapesSigp_frq_" + str(codProv)).getOutput(0))
                    # arcpy.AddMessage("solapan :" + str(nreg2))

                    #vuelco los solapes en el shape
                    arcpy.AddJoin_management("lyshprec", "ID_UNICO", "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO","KEEP_COMMON")
                    if RecVue == 1:
                        arcpy.CalculateField_management("lyshprec","SOLAPES","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON")
                    #arcpy.CalculateField_management("lyshprec","SOLAPES2","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON")
                    arcpy.RemoveJoin_management ("lyshprec", "SolapesSigp_frq_" + str(codProv))

                    arcpy.AddJoin_management("lyshprec2", "ID_UNICO", "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO","KEEP_COMMON")
                    if RecVue == 1:
                        arcpy.CalculateField_management("lyshprec2","SOLAPES","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON")
                    arcpy.CalculateField_management("lyshprec2","SOLAPES2","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON")
                    arcpy.RemoveJoin_management ("lyshprec2", "SolapesSigp_frq_" + str(codProv))

                    #si solape 1 me quedo con uno de ellos
                    arcpy.JoinField_management("SolapesSigp_" + str(codProv), "src_ID_UNICO","SolapesSigp_frq_" + str(codProv),  "src_ID_UNICO", ["FREQUENCY",])

                    arcpy.MakeTableView_management("SolapesSigp_" + str(codProv), "lysolapes")
                    arcpy.SelectLayerByAttribute_management("lysolapes", "NEW_SELECTION", "\"FREQUENCY\" = 1")
                    nreg11 = int(arcpy.GetCount_management("lysolapes").getOutput(0))
                    #arcpy.AddMessage("Con solape 1:" + str(nreg11))
                    if nreg11 > 0:
                        arcpy.Statistics_analysis("lysolapes", "SolapesSigp_frq2_" + str(codProv), [["src_ID_UNICO", "FIRST"]], "AREA")

                        arcpy.AddJoin_management("lyshprec2", "ID_UNICO", "SolapesSigp_frq2_" + str(codProv), "FIRST_src_ID_UNICO","KEEP_COMMON")
                        # arcpy.AddMessage(int(arcpy.GetCount_management("lyshprec2").getOutput(0)))
                        arcpy.CalculateField_management("lyshprec2","SOLAPES2","0", "PYTHON")
                        arcpy.RemoveJoin_management ("lyshprec2", "SolapesSigp_frq2_" + str(codProv))

                    else:                                                                                                      #nuevo 20220523
                            arcpy.AddMessage(int(arcpy.GetCount_management("SolapesSigp_" + str(codProv)).getOutput(0)))        #nuevo 20220523
                            cur2 = arcpy.SearchCursor("SolapesSigp_" + str(codProv), sort_fields="FREQUENCY A")                 #nuevo 20220523
                            for row2 in cur2:                                                                                      #nuevo 20220523
                                recid = row2.getValue("src_ID_UNICO")                                                                #nuevo 20220523
                                arcpy.AddMessage(row2.getValue("src_ID_UNICO"))                                                      #nuevo 20220523
                            arcpy.SelectLayerByAttribute_management("lyshprec2", "NEW_SELECTION", "\"ID_UNICO\" =" + str(recid))   #nuevo 20220523
                            nreg12 = int(arcpy.GetCount_management("lyshprec2").getOutput(0))                                      #nuevo 20220523
                            arcpy.AddMessage(nreg12)                                                                               #nuevo 20220523
                            if nreg12 > 0:                                                                                         #nuevo 20220523
                                arcpy.CalculateField_management("lyshprec2","SOLAPES2","0", "PYTHON")                              #nuevo 20220523

                    #limpio
                    if arcpy.Exists("temp"):
                        arcpy.Delete_management("temp")
                    if arcpy.Exists("SolapesSigp_frq_" + str(codProv)):
                        arcpy.Delete_management("SolapesSigp_frq_" + str(codProv))
                    if arcpy.Exists("SolapesSigp_frq2_" + str(codProv)):
                        arcpy.Delete_management("SolapesSigp_frq2_" + str(codProv))
                    if arcpy.Exists("SolapesSigp_" + str(codProv)):
                        arcpy.Delete_management("SolapesSigp_" + str(codProv))


                ##*************************************************************************************************************
                ## TODOS NO SOLAPAN - paso recintos a raster y calculo estadisticas por municipio
                ## ************************************************************************************************************
                arcpy.AddMessage("*************************")
                arcpy.AddMessage("inicio todos los que NO solapan")

                #selecciono lo que se procesa - NO SOLAPAN
                arcpy.SelectLayerByAttribute_management("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0")
                nreg2 = int(arcpy.GetCount_management("lyshprec2").getOutput(0))
                arcpy.AddMessage("Recintos no solapan :" + str(nreg2))
                if nreg2 > 0:
                    # METODO 1 - paso recintos a raster y calculo estadisticas de todo el municipio a la vez
                    # ********************************************************************************************
                    arcpy.AddMessage ("Inicio METODO 1")
                    arcpy.AddMessage( "Hora: " + time.ctime())

                    # miro su extension y calculo para pasar a grid
                    descf = arcpy.Describe("sigp_muni")
                    xmin = (int(descf.extent.XMin / 5)) * 5
                    ymin = (int(descf.extent.YMin / 5)) * 5
                    xmax = ((int(descf.extent.XMax / 5)) * 5) + 10
                    ymax = ((int(descf.extent.YMax / 5)) * 5) + 10

                    arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax))

                    #paso a raster
                    arcpy.PolygonToRaster_conversion("lyshprec2", "ID_UNICO","gsigp_muni","CELL_CENTER", "", 1) #tamaño de celda 1
                    arcpy.BuildRasterAttributeTable_management("gsigp_muni", "Overwrite")

                    #chequeo que tenga valores y si tiene calculo estadisticas por recinto
                    grdmean = arcpy.GetRasterProperties_management("gsigp_muni", "UNIQUEVALUECOUNT")

                    vacio = grdmean.getOutput(0)
                    #vacio = 0
                    if int(vacio) > 0: #== 0:
                        #arcpy.BuildRasterAttributeTable_management("gsigp_muni", "Overwrite")

                        arcpy.env.extent = "gsigp_muni"  #extension
                        arcpy.env.snapRaster = "gsigp_muni" # cuadrar los raster
                        arcpy.env.mask = "gsigp_muni" # mascara
                        arcpy.env.cellSize = 1 #tamaño celda

                        #pauso para que desbloque los ficheros, 5m
                        #arcpy.AddMessage("Ante de dormir " + time.ctime())
                        #time.sleep(120)
                        #arcpy.AddMessage("Despues de dormir " + time.ctime())

                        arcpy.AddMessage ("Estadisticas")
                        STAT_TXT13 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgalt, "sta13", "NODATA", "MEAN") #20221020
                        arcpy.AddIndex_management("sta13", "Value", "sta13_Value", "UNIQUE","ASCENDING") #20221020
                        STAT_TXT10 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgpte, "sta10", "NODATA", "MEAN") #20211116
                        arcpy.AddIndex_management("sta10", "Value", "sta10_Value", "UNIQUE","ASCENDING") #20211116
                        STAT_TXT1 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgcsp, "sta1", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta1", "Value", "sta1_Value", "UNIQUE","ASCENDING")
                        STAT_TXT2 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfsue, "sta2", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta2", "Value", "sta2_Value", "UNIQUE","ASCENDING")
                        STAT_TXT3 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfpte, "sta3", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta3", "Value", "sta3_Value", "UNIQUE","ASCENDING")
                        STAT_TXT4 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfveg, "sta4", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta4", "Value", "sta4_Value", "UNIQUE","ASCENDING")
                        STAT_TXT5 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfveges, "sta5", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta5", "Value", "sta5_Value", "UNIQUE","ASCENDING")
                        STAT_TXT6 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfinc, "sta6", "NODATA", "MEAN")
                        arcpy.AddIndex_management("sta6", "Value", "sta6_Value", "UNIQUE","ASCENDING")
                        if arcpy.Exists("GFESPDE_" + codProv): #20211111
                            STAT_TXT11 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_deh, "sta11", "DATA", "MEAN") #20211125
                            arcpy.AddIndex_management("sta11", "Value", "sta11_Value", "UNIQUE","ASCENDING") #20211125
                            STAT_TXT7 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fespde, "sta7", "DATA", "MEAN") #20211111
                            arcpy.AddIndex_management("sta7", "Value", "sta7_Value", "UNIQUE","ASCENDING") #20211111
                        if arcpy.Exists("GFESPES_" + codProv): #20211111
                            STAT_TXT12 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_esp, "sta12", "DATA", "MEAN") #20211125
                            arcpy.AddIndex_management("sta12", "Value", "sta12_Value", "UNIQUE","ASCENDING") #20211125
                            STAT_TXT8 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fespes, "sta8", "DATA", "MEAN") #20211111
                            arcpy.AddIndex_management("sta8", "Value", "sta8_Value", "UNIQUE","ASCENDING") #20211111
                        if arcpy.Exists("GFESP_" + codProv): #20211111
                            STAT_TXT9 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fesp, "sta9", "DATA", "MEAN") #20211111
                            arcpy.AddIndex_management("sta9", "Value", "sta9_Value", "UNIQUE","ASCENDING") #20211111

                        # cargo en el shape de recintos inicial
                        arcpy.AddMessage ("Paso el resultado al fc precfe")

                        arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")

##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta1","Value","KEEP_COMMON")
##                        arcpy.AddMessage("seleccion para calcular: " + arcpy.GetCount_management("lyshprec").getOutput(0))
##                        arcpy.CalculateField_management("lyshprec","CSP","!sta1.MEAN! / 10000", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta2","Value","KEEP_COMMON")
##                        arcpy.CalculateField_management("lyshprec","F_SUE","!sta2.MEAN! / 100", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta3","Value","KEEP_COMMON")
##                        arcpy.CalculateField_management("lyshprec","F_PTE","!sta3.MEAN! / 100", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta4","Value","KEEP_COMMON")
##                        arcpy.CalculateField_management("lyshprec","F_VEG","!sta4.MEAN! / 100", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta5","Value","KEEP_COMMON")
##                        arcpy.CalculateField_management("lyshprec","F_VEGES","!sta5.MEAN! / 100", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta6","Value","KEEP_COMMON")
##                        arcpy.CalculateField_management("lyshprec","F_INC","!sta6.MEAN!", "PYTHON")
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta10","Value","KEEP_COMMON") #20211116
##                        arcpy.CalculateField_management("lyshprec","PTE","!sta10.MEAN!", "PYTHON") #20211116
##
##                        arcpy.AddJoin_management("lyshprec","ID_UNICO","sta13","Value","KEEP_COMMON") #20221020
##                        arcpy.CalculateField_management("lyshprec","ALT_NEW","!sta13.MEAN!", "PYTHON") #20221020
##
##                        if arcpy.Exists("GFESPDE_" + codProv): #20211111
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta11","Value","KEEP_COMMON") #20211125
##                            arcpy.CalculateField_management("lyshprec","POR_DEH","!sta11.MEAN! * 100", "PYTHON")  #20211125
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta7","Value","KEEP_COMMON") #20211111
##                            arcpy.CalculateField_management("lyshprec","POR_FESPDE","!sta7.MEAN! * 100", "PYTHON")  #20211111
##
##                        if arcpy.Exists("GFESPES_" + codProv): #20211111
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta12","Value","KEEP_COMMON") #20211125
##                            arcpy.CalculateField_management("lyshprec","POR_ESP","!sta12.MEAN! * 100", "PYTHON")  #20211125
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta8","Value","KEEP_COMMON") #20211111
##                            arcpy.CalculateField_management("lyshprec","POR_FESPES","!sta8.MEAN! * 100", "PYTHON")  #20211111
##
##                        if arcpy.Exists("GFESP_" + codProv): #20211111
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta9","Value","KEEP_COMMON") #20211111
##                            arcpy.CalculateField_management("lyshprec","POR_FESP","!sta9.MEAN! * 100", "PYTHON")  #20211111
##
##                        arcpy.RemoveJoin_management("lyshprec")

                        if "lyshprec_ID_UNICO" not in [idx.name for idx in arcpy.ListIndexes("lyshprec")]:
                            arcpy.AddIndex_management("lyshprec", "ID_UNICO", "lyshprec_ID_UNICO", "UNIQUE","ASCENDING")

                        #arcpy.AddIndex_management("lyshprec", "ID_UNICO", "lyshprec_ID_UNICO", "UNIQUE","ASCENDING")
                        arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta1", "Value", ["MEAN", "COUNT"])
                        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"COUNT\" <> 0")
                        arcpy.AddMessage("seleccion para calcular: " + arcpy.GetCount_management("lyshprec").getOutput(0))
                        arcpy.CalculateField_management("lyshprec","CSP","!MEAN! / 10000", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN", "COUNT"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta2", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","F_SUE","!MEAN! / 100", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta3", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","F_PTE","!MEAN! / 100", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta4", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","F_VEG","!MEAN! / 100", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta5", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","F_VEGES","!MEAN! / 100", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta6", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","F_INC","!MEAN!", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta10", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","PTE","!MEAN!", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta13", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","ALT_NEW","!MEAN!", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESPDE_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta7", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESPDE","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta11", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_DEH","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESPES_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta8", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESPES","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta12", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_ESP","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESP_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta9", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESP","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")

                    # METODO 2 -  se rasterizan a 0,5 metros los recintos de superficie menor de 50 m2 o que no se han procesado
                    # ********************************************************************************************
                    arcpy.AddMessage ("Inicio METODO 2")
                    arcpy.AddMessage( "Hora: " + time.ctime())

                    #saco los recintos menores de 50m2
                    #arcpy.MakeFeatureLayer_management("sigp_muni","lyshprec2")
                    arcpy.SelectLayerByAttribute_management("lyshprec2", "NEW_SELECTION", "Shape_Area <= 50 and \"SOLAPES2\" = 0" )

                    Nrec2 = arcpy.GetCount_management("lyshprec2").getOutput(0)
                    if int(Nrec2) > 0:
                        arcpy.AddMessage ("Número de recintos menores de 50 m2: " + str(arcpy.GetCount_management("lyshprec2").getOutput(0)))
                        fictime.write('Número de recintos menores de 50 m2: ' + str(arcpy.GetCount_management("lyshprec2").getOutput(0) + '\n'))

                        vshp_mun2 = arcpy.FeatureClassToFeatureClass_conversion("lyshprec2", dirPrin + "\\prov" + codProv + "\\prov" + codProv + ".gdb\\PROYE", "sigp_muni2")

                        # miro su extension y calculo para pasar a grid
                        descf = arcpy.Describe("sigp_muni2")
                        xmin = (int(descf.extent.XMin / 5)) * 5
                        ymin = (int(descf.extent.YMin / 5)) * 5
                        xmax = ((int(descf.extent.XMax / 5)) * 5) + 10
                        ymax = ((int(descf.extent.YMax / 5)) * 5) + 10

                        arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax))

                        #paso a raster
                        arcpy.PolygonToRaster_conversion("sigp_muni2", "ID_UNICO","gsigp_muni2","CELL_CENTER", "", 0.5) #tamaño de celda 0.5
                        arcpy.BuildRasterAttributeTable_management("gsigp_muni2", "Overwrite")

                        #chequeo que tenga valores y si tiene calculo estadisticas por recinto
                        grdmean = arcpy.GetRasterProperties_management("gsigp_muni2", "UNIQUEVALUECOUNT")

                        vacio = grdmean.getOutput(0)
                        #vacio = 0
                        if int(vacio) > 0: #== 0:
                            #arcpy.BuildRasterAttributeTable_management("gsigp_muni2", "Overwrite")

                            arcpy.env.extent = "gsigp_muni2"  #extension
                            arcpy.env.snapRaster = "gsigp_muni2" # cuadrar los raster
                            arcpy.env.mask = "gsigp_muni2" # mascara
                            arcpy.env.cellSize = 0.5 #tamaño celda

                            #pauso para que desbloque los ficheros, 5m
                            #arcpy.AddMessage("Ante de dormir " + time.ctime())
                            #time.sleep(120)
                            #arcpy.AddMessage("Despues de dormir " + time.ctime())

                            arcpy.AddMessage ("Estadisticas")
                            STAT_TXT13 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgalt, "sta13", "NODATA", "MEAN") #20221020
                            arcpy.AddIndex_management("sta13", "Value", "sta13_Value", "UNIQUE","ASCENDING") #20221020
                            STAT_TXT10 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgpte, "sta10", "NODATA", "MEAN") #20211116
                            arcpy.AddIndex_management("sta10", "Value", "sta10_Value", "UNIQUE","ASCENDING") #20211116
                            STAT_TXT1 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgcsp, "sta1", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta1", "Value", "sta1_Value", "UNIQUE","ASCENDING")
                            STAT_TXT2 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfsue, "sta2", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta2", "Value", "sta2_Value", "UNIQUE","ASCENDING")
                            STAT_TXT3 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfpte, "sta3", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta3", "Value", "sta3_Value", "UNIQUE","ASCENDING")
                            STAT_TXT4 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfveg, "sta4", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta4", "Value", "sta4_Value", "UNIQUE","ASCENDING")
                            STAT_TXT5 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfveges, "sta5", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta5", "Value", "sta5_Value", "UNIQUE","ASCENDING")
                            STAT_TXT6 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfinc, "sta6", "NODATA", "MEAN")
                            arcpy.AddIndex_management("sta6", "Value", "sta6_Value", "UNIQUE","ASCENDING")
                            if arcpy.Exists("GFESPDE_" + codProv): #20211111
                                STAT_TXT11 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_deh, "sta11", "DATA", "MEAN") #20211125
                                arcpy.AddIndex_management("sta11", "Value", "sta11_Value", "UNIQUE","ASCENDING") #20211125
                                STAT_TXT7 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fespde, "sta7", "DATA", "MEAN") #20211111
                                arcpy.AddIndex_management("sta7", "Value", "sta7_Value", "UNIQUE","ASCENDING") #20211111
                            if arcpy.Exists("GFESPES_" + codProv): #20211111
                                STAT_TXT12 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_esp, "sta12", "DATA", "MEAN") #20211125
                                arcpy.AddIndex_management("sta12", "Value", "sta12_Value", "UNIQUE","ASCENDING") #20211125
                                STAT_TXT8 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fespes, "sta8", "DATA", "MEAN") #20211111
                                arcpy.AddIndex_management("sta8", "Value", "sta8_Value", "UNIQUE","ASCENDING") #20211111
                            if arcpy.Exists("GFESP_" + codProv): #20211111
                                STAT_TXT9 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fesp, "sta9", "DATA", "MEAN") #20211111
                                arcpy.AddIndex_management("sta9", "Value", "sta9_Value", "UNIQUE","ASCENDING") #20211111

                            # cargo en el shape de recintos inicial
                            arcpy.AddMessage ("Paso el resultado al fc precfe")

                            arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")

##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta1","Value","KEEP_COMMON")
##                            arcpy.AddMessage("seleccion para calcular: " + arcpy.GetCount_management("lyshprec").getOutput(0))
##                            arcpy.CalculateField_management("lyshprec","CSP","!sta1.MEAN! / 10000", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta2","Value","KEEP_COMMON")
##                            arcpy.CalculateField_management("lyshprec","F_SUE","!sta2.MEAN! / 100", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta3","Value","KEEP_COMMON")
##                            arcpy.CalculateField_management("lyshprec","F_PTE","!sta3.MEAN! / 100", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta4","Value","KEEP_COMMON")
##                            arcpy.CalculateField_management("lyshprec","F_VEG","!sta4.MEAN! / 100", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta5","Value","KEEP_COMMON")
##                            arcpy.CalculateField_management("lyshprec","F_VEGES","!sta5.MEAN! / 100", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta6","Value","KEEP_COMMON")
##                            arcpy.CalculateField_management("lyshprec","F_INC","!sta6.MEAN!", "PYTHON")
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta10","Value","KEEP_COMMON") #20211116
##                            arcpy.CalculateField_management("lyshprec","PTE","!sta10.MEAN!", "PYTHON") #20211116
##
##                            arcpy.AddJoin_management("lyshprec","ID_UNICO","sta13","Value","KEEP_COMMON") #20221020
##                            arcpy.CalculateField_management("lyshprec","ALT_NEW","!sta13.MEAN!", "PYTHON") #20221020
##
##                            if arcpy.Exists("GFESPDE_" + codProv): #20211111
##                                arcpy.AddJoin_management("lyshprec","ID_UNICO","sta11","Value","KEEP_COMMON") #20211125
##                                arcpy.CalculateField_management("lyshprec","POR_DEH","!sta11.MEAN! * 100", "PYTHON")  #20211125
##                                arcpy.AddJoin_management("lyshprec","ID_UNICO","sta7","Value","KEEP_COMMON") #20211111
##                                arcpy.CalculateField_management("lyshprec","POR_FESPDE","!sta7.MEAN! * 100", "PYTHON")  #20211111
##
##                            if arcpy.Exists("GFESPES_" + codProv): #20211111
##                                arcpy.AddJoin_management("lyshprec","ID_UNICO","sta12","Value","KEEP_COMMON") #20211125
##                                arcpy.CalculateField_management("lyshprec","POR_ESP","!sta12.MEAN! * 100", "PYTHON")  #20211125
##                                arcpy.AddJoin_management("lyshprec","ID_UNICO","sta8","Value","KEEP_COMMON") #20211111
##                                arcpy.CalculateField_management("lyshprec","POR_FESPES","!sta8.MEAN! * 100", "PYTHON")  #20211111
##
##                            if arcpy.Exists("GFESP_" + codProv): #20211111
##                                arcpy.AddJoin_management("lyshprec","ID_UNICO","sta9","Value","KEEP_COMMON") #20211111
##                                arcpy.CalculateField_management("lyshprec","POR_FESP","!sta9.MEAN! * 100", "PYTHON")  #20211111
##
##                            arcpy.RemoveJoin_management("lyshprec")

                            #arcpy.AddIndex_management("lyshprec", "ID_UNICO", "lyshprec_ID_UNICO", "UNIQUE","ASCENDING")

                            arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")
                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta1", "Value", ["MEAN", "COUNT"])
                            arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"COUNT\" <> 0")
                            arcpy.AddMessage("seleccion para calcular: " + arcpy.GetCount_management("lyshprec").getOutput(0))
                            arcpy.CalculateField_management("lyshprec","CSP","!MEAN! / 10000", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN", "COUNT"])

                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta2", "Value", ["MEAN"])
                            arcpy.CalculateField_management("lyshprec","F_SUE","!MEAN! / 100", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN"])

                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta3", "Value", ["MEAN"])
                            arcpy.CalculateField_management("lyshprec","F_PTE","!MEAN! / 100", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN"])

                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta4", "Value", ["MEAN"])
                            arcpy.CalculateField_management("lyshprec","F_VEG","!MEAN! / 100", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN"])

                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta5", "Value", ["MEAN"])
                            arcpy.CalculateField_management("lyshprec","F_VEGES","!MEAN! / 100", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN"])

                            arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta6", "Value", ["MEAN"])
                            arcpy.CalculateField_management("lyshprec","F_INC","!MEAN!", "PYTHON")
                            arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta10", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","PTE","!MEAN!", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta13", "Value", ["MEAN"])
                        arcpy.CalculateField_management("lyshprec","ALT_NEW","!MEAN!", "PYTHON")
                        arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESPDE_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta7", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESPDE","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta11", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_DEH","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESPES_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta8", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESPES","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta12", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_ESP","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        if arcpy.Exists("GFESP_" + codProv): #20211111
                          arcpy.JoinField_management("lyshprec", "ID_UNICO", "sta9", "Value", ["MEAN"])
                          arcpy.CalculateField_management("lyshprec","POR_FESP","!MEAN! * 100", "PYTHON")
                          arcpy.DeleteField_management("lyshprec", ["MEAN"])

                        arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION")

                    else:
                        arcpy.AddMessage ("no selecciono ningun recinto < 50m2")

                    #fin if de NO solapes
                    #****************************************************************

                    arcpy.SelectLayerByAttribute_management("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0 or \"SOLAPES2\" = 99")
                    arcpy.AddMessage("seleccion para 99: " + arcpy.GetCount_management("lyshprec2").getOutput(0))
                    arcpy.CalculateField_management("lyshprec2","SOLAPES2","99", "PYTHON")
                    arcpy.SelectLayerByAttribute_management("lyshprec2", "SWITCH_SELECTION")
                    arcpy.AddMessage("seleccion para 0: " + arcpy.GetCount_management("lyshprec2").getOutput(0))
                    if int(arcpy.GetCount_management("lyshprec2").getOutput(0)) > 0:
                        arcpy.CalculateField_management("lyshprec2","SOLAPES2","0", "PYTHON")
                        RecSol = 1
                        RecVue = RecVue + 1
                else:
                    RecSol = 0

            # fin del whilw

            # limpio seleccion del municipio
            arcpy.env.extent = vgcsp  #extension
            arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")

        fictime.write('TERMINÉ el municipio  ' + str(mun) + '\n')
        fictime.write('*****************************************\n')
        arcpy.AddMessage("TERMINÉ el municipio " + str(mun))
        arcpy.AddMessage("***********************")

    else:
        arcpy.AddMessage ("Ya estaba Procesando " + str(rec) + " de " + str(nunmun) + " - Municipio: " + str(mun))

    if arcpy.Exists("gsigp_muni"):
        arcpy.Delete_management("gsigp_muni")
    if arcpy.Exists("gsigp_muni2"):
        arcpy.Delete_management("gsigp_muni2")


    if arcpy.Exists("PROYE\\sigp_muni"):
        arcpy.Delete_management("PROYE\\sigp_muni")
    if arcpy.Exists("PROYE\\sigp_muni2"):
        arcpy.Delete_management("PROYE\\sigp_muni2")

fictime.write('TERMINÉ el procesado municipio a municipio sin solapes a las ' + time.ctime()+ '\n')
fictime.write('*****************************************\n')
arcpy.AddMessage("TERMINÉ el procesado municipio a municipio sin solapes a las " + time.ctime())

# fin del for del municipio

arcpy.AddMessage("FIN ESTADISTICAS ************************")
fictime.write('FIN ESTADISTICAS ********************' + '\n')

#***********************************************
#ajusto

arcpy.AddMessage("inicio ajustes finales")
fictime.write('inicio ajustes finales a las ' + time.ctime()+ '\n')

# se calcula el atributo csp_res

if codProv in ['15', '27', '32', '36', '04', '11', '14', '18', '21', '23', '29', '41', '31', '06', '10', '01', '20', '48', '02', '13', '16', '19', '45', '07']:
    arcpy.AddMessage("Redondeo de 10 en 10 desde 20 a 90- Andalucia, Galicia, Navarra, Pais Vasco, Extremadura, CasMan, Baleares ")
    fictime.write('Redondeo de 10 en 10 desde 20 a 90 - Andalucia, Galicia, Navarra, Pais Vasco, Extremadura, CasMan, Baleares ' + time.ctime()+ '\n')

    #redondeo según metodología del 2015
    # paso a entero
    # csp < 20 cap_res = 0, csp >= 90 csp_res = 100
    # intervalos de 10 puntos

    #paso a entero
    arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")
    arcpy.CalculateField_management("lyshprec","CSPI","!CSP!", "PYTHON")

    #redondeo a intervalos
    arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 0")
    arcpy.CalculateField_management("lyshprec","CSP_RES","0", "PYTHON")

    arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20")
    if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
            arcpy.CalculateField_management("lyshprec","CSP_RES","math.trunc(!CSPI! / 10)", "PYTHON")
            arcpy.CalculateField_management("lyshprec","CSP_RES","!CSP_RES! * 10 + 5", "PYTHON")
            arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90")
            if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
                arcpy.CalculateField_management("lyshprec","CSP_RES","100", "PYTHON")
    arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")

elif codProv in ['33', '28', '03', '12', '46']:
    arcpy.AddMessage("Redondeo de 5 en 5 desde 20 a 90- Asturias, Madrid, CValenciana ")
    fictime.write('Redondeo de 5 en 5 desde 20 a 90- Asturias, Madrid, CValenciana ' + time.ctime()+ '\n')

    # redondeo de 5 en 5 - cambian intervalos desde 13/01/2022 (>=20 a <22,5 valor 20.......)
    # csp < 20 csp_res = 0, csp >= 90 csp_res = 100

    #paso a entero
    arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")
    arcpy.CalculateField_management("lyshprec","CSPI","!CSP!", "PYTHON") #cambia 20230519

    #redondeo a intervalos
    arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 0") #cambia 20230519
    arcpy.CalculateField_management("lyshprec","CSP_RES","0", "PYTHON")

    arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20 and \"CSPI\" < 90") #cambia 20230519
    if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
        arcpy.CalculateField_management("lyshprec","TMP3","!CSP! + 2.5", "PYTHON")
        arcpy.CalculateField_management("lyshprec","TMP1","int(!TMP3! / 5)", "PYTHON")
        arcpy.CalculateField_management("lyshprec","CSP_RES","!TMP1! * 5", "PYTHON")

    arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90") #cambia 20230519
    if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
        arcpy.CalculateField_management("lyshprec","CSP_RES","100", "PYTHON")
    arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")

else:
    arcpy.AddMessage("Redondeo a la unidad regla del 5 desde 20 a 90- FEGA: Aragon, Murcia, CasLeon, Rioja, Cantabria, Canarias de 10 a 90, Cataluña de 20 a 100")
    fictime.write('Redondeo a la unidad regla del 5 desde 20 a 90- FEGA: Aragon, Murcia, CasLeon, Rioja, Cantabria, Canarias de 10 a 90, Cataluña de 20 a 100)' + time.ctime()+ '\n')

    # redondeo al entero más próximo con la regla del 5
    # csp < 20 csp_res = 0, csp >= 90 csp_res = 100
    # Csp >= 20 y csp >= 20,5 csp_res = 20
    # csp > 20,5 y csp <= 21,5 csp_res = 21 y así sucesivamente

    #paso a entero
    arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "") #cambia 20230519
    arcpy.CalculateField_management("lyshprec","CSPI","!CSP!", "PYTHON") #cambia 20230519

    # intervalo inferior
    if codProv in ['35', '38']:
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" < 10") #cambia 20230519
    else:
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" < 20") #cambia 20230519
    if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
        arcpy.CalculateField_management("lyshprec","CSP_RES","0", "PYTHON")

    # medio, de uno en uno
    if codProv in ['35', '38']:
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 10") #cambia 20230519
    else:
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20") #cambia 20230519
    if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
        arcpy.CalculateField_management("lyshprec","CSP_RES","round(!CSP!)", "PYTHON")
        arcpy.CalculateField_management("lyshprec","TMP1","!CSP! * 10", "PYTHON")
        ## arcpy.CalculateField_management("lyshprec","TMP2","Right(!TMP1!,1)", "PYTHON")
        arcpy.CalculateField_management("lyshprec","TMP2","str(!TMP1!)[-1]", "PYTHON")
        arcpy.CalculateField_management("lyshprec","TMP3","!TMP1! / 10", "PYTHON")

        arcpy.SelectLayerByAttribute_management("lyshprec", "SUBSET_SELECTION", "\"TMP2\" = 5 AND \"CSP\" = \"TMP3\"")
        if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
            arcpy.CalculateField_management("lyshprec","CSP_RES","!CSP_RES! - 1", "PYTHON")

    #intervalo superior
    if codProv in ['08', '17', '25', '43']:
        arcpy.AddMessage("Soy Cataluña, no tengo intervalo superior")
    else:
        arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90") #cambia 20230519
        if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
            arcpy.CalculateField_management("lyshprec","CSP_RES","100", "PYTHON")

# no calculo
arcpy.SelectLayerByAttribute_management("lyshprec", "NEW_SELECTION", "\"CSP\" = -1")
if int(arcpy.GetCount_management("lyshprec").getOutput(0)) > 0:
    arcpy.CalculateField_management("lyshprec","CSP_RES","- 1", "PYTHON")
    arcpy.CalculateField_management("lyshprec","POR_DEH","- 1", "PYTHON") #20211125
    arcpy.CalculateField_management("lyshprec","POR_FESPDE","- 1", "PYTHON") #20211111
    arcpy.CalculateField_management("lyshprec","POR_ESP","- 1", "PYTHON") #20211125
    arcpy.CalculateField_management("lyshprec","POR_FESPES","- 1", "PYTHON") #20211111
    arcpy.CalculateField_management("lyshprec","POR_FESP","- 1", "PYTHON") #20211111

arcpy.SelectLayerByAttribute_management("lyshprec", "CLEAR_SELECTION", "")

# ****************************************
#saco a una tabla
#tab_sal = dirPrin + "\\prov" + codProv + "\\CSPrecintos_" + codProv + ".dbf"
#arcpy.Frequency_analysis(vshp_recp,tab_sal,["ID_UNICO", "PROVINCIA", "MUNICIPIO", "AGREGADO", "ZONA", "POLIGONO", "PARCELA", "RECINTO", "F_SUE", "F_PTE", "F_VEG", "F_ESP", "F_VEGES", "F_INC", "CSP", "CSP_RES" ]) #20211111

#limpio

#arcpy.DeleteField_management(vshp_recp,["TMP1", "TMP2", "TMP3", "CSPI", "SOLAPES2"])

if arcpy.Exists("gsigp_muni"):
    arcpy.Delete_management("gsigp_muni")
if arcpy.Exists("gsigp_muni2"):
    arcpy.Delete_management("gsigp_muni2")
if arcpy.Exists("gsigp_muni3"):
    arcpy.Delete_management("gsigp_muni3")
if arcpy.Exists("gsigp_muni4"):
    arcpy.Delete_management("gsigp_muni4")

if arcpy.Exists("PROYE\\sigp_muni"):
    arcpy.Delete_management("PROYE\\sigp_muni")
if arcpy.Exists("PROYE\\sigp_muni2"):
    arcpy.Delete_management("PROYE\\sigp_muni2")
if arcpy.Exists("PROYE\\sigp_muni3"):
    arcpy.Delete_management("PROYE\\sigp_muni3")
if arcpy.Exists("PROYE\\sigp_muni4"):
    arcpy.Delete_management("PROYE\\sigp_muni4")

if arcpy.Exists("sta1"):
    arcpy.Delete_management("sta1")
if arcpy.Exists("sta2"):
    arcpy.Delete_management("sta2")
if arcpy.Exists("sta3"):
    arcpy.Delete_management("sta3")
if arcpy.Exists("sta4"):
    arcpy.Delete_management("sta4")
if arcpy.Exists("sta5"):
    arcpy.Delete_management("sta5")
if arcpy.Exists("sta6"):
    arcpy.Delete_management("sta6")
if arcpy.Exists("sta7"): #20211111
    arcpy.Delete_management("sta7") #20211111
if arcpy.Exists("sta8"): #20211111
    arcpy.Delete_management("sta8") #20211111
if arcpy.Exists("sta9"): #20211111
    arcpy.Delete_management("sta9") #20211111
if arcpy.Exists("sta10"): #20211111
    arcpy.Delete_management("sta10") #20211111
if arcpy.Exists("sta11"): #20211111
    arcpy.Delete_management("sta11") #20211111
if arcpy.Exists("temp"):
    arcpy.Delete_management("temp")

if arcpy.Exists("recfe_txt2"):
    arcpy.Delete_management("recfe_txt2")
if arcpy.Exists("recfe_txt3"):
    arcpy.Delete_management("recfe_txt3")



fictime.write('TERMIN? TODO a las ' + time.ctime() + '\n')
fictime.write('*****************************************\n')
fictime.close()
arcpy.AddMessage("TERMIN? TODO a las " + time.ctime())
arcpy.AddMessage("??Acuerdate de revisar los ficheros de salida. Borra el de errores geometrico si das por terminado el calculo !!" )









