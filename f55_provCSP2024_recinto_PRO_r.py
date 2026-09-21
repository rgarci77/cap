# **********************************
# Programa: calcula el valor medio por recinto para 2024- Lidar3
# Salida: tabla
#
# Fecha : octubre-2021
# Autor: masm, bvm
#
# ************************************

#%% proceso 1

# -*- coding: utf-8 -*-
# ArcGIS Pro 3.7 / Python 3.x
# Adaptación del script original de ArcMap.
# La lógica de cálculo se mantiene; se actualizan llamadas ArcPy, parser PYTHON3
# y elementos incompatibles con Python 3.
# **********************************
# Programa: calcula el valor medio por recinto para 2024- Lidar3
# Salida: tabla
#
# Fecha : octubre-2021
# Autor: masm, bvm
#
# ************************************


#%% carga librerias

import io
import os
import time

import arcpy
from arcpy.sa import *


def borrar_temporal(ruta, intentos=5, espera=2):
    """
    Intenta eliminar un dataset de ArcGIS liberando previamente
    referencias y cache. Reintenta si ArcGIS mantiene un lock.
    """
    for intento in range(1, intentos + 1):
        try:

            arcpy.management.ClearWorkspaceCache()

            if arcpy.Exists(ruta):
                arcpy.management.Delete(ruta)
     
            if not arcpy.Exists(ruta):
                return True

        except Exception as e:
            arcpy.AddMessage( time.ctime() + " No se pudo eliminar '{}' (intento {}/{}): {}".format(ruta, intento, intentos, e))  # noqa: UP032

        time.sleep(espera)

    arcpy.AddWarning(time.ctime() + " No se pudo eliminar el temporal después de {} intentos: {}".format(intentos, ruta))  # noqa: UP032
    return False


if not arcpy.GetParameterAsText(0) or "jupyter" in arcpy.GetParameterAsText(0).lower():
    print("--- EJECUTANDO MODO DESARROLLO EN VS CODE ---")
    dirPrin = r"D:\Pastos\CAP2023_Lidar3\RASTERS_CSP"
    shp_rec = r"D:\Pastos\CAP2023_Lidar3\RASTERS_CSP\prov11\Recinto_clip.shp"
    bd_rec = r"D:\Pastos\CAP2023_Lidar3\RASTERS_CSP\prov11\ATRIRECI.dbf"
    mun_ini = '1'
    codProv = '11'
    repgeo = False

else:
    print("--- EJECUTANDO MODO TOOLBOX ARCGIS PRO ---")
    dirPrin = arcpy.GetParameterAsText(0)
    shp_rec = arcpy.GetParameterAsText(1)
    bd_rec = arcpy.GetParameterAsText(2)
    mun_ini = arcpy.GetParameterAsText(3)
    codProv = arcpy.GetParameterAsText(4)
    repgeo = arcpy.GetParameterAsText(5)
   
# para que machaque si existen
arcpy.env.overwriteOutput = True

# CONSTRUCCIÓN DE RUTAS Y CONTROL DE EXISTENCIA
carpeta_prov = os.path.join(dirPrin, "prov" + codProv)
gdb_trabajo  = os.path.join(carpeta_prov, "prov" + codProv + ".gdb")
carpeta_proye = os.path.join(gdb_trabajo, "PROYE")
ruta_temp = os.path.join(gdb_trabajo, "temp")

spatial_checkout = False

temporales = [
            "gsigp_muni",
            "gsigp_muni2",
            "gsigp_muni3",
            "gsigp_muni4",
            "PROYE\\sigp_muni",
            "PROYE\\sigp_muni2",
            "PROYE\\sigp_muni3",
            "PROYE\\sigp_muni4",
            "sta1",
            "sta2",
            "sta3",
            "sta4",
            "sta5",
            "sta6",
            "sta7",
            "sta8",
            "sta9",
            "sta10",
            "sta11",
            "sta12",
            "sta13",
            "temp",
            "recfe_txt2",
            "recfe_txt3","sigp_muni",
            "sigp_muni2",
            "SolapesSigp_" + str(codProv),
            "SolapesSigp_frq_" + str(codProv),
            "SolapesSigp_frq2_" + str(codProv),
        ]

#%%  Proceso principal

try:
    
    # Estado de la licencia
    arcpy.AddMessage(time.ctime() + " Comprobando disponibilidad de licencia Spatial Analyst...")
    
    estado = arcpy.CheckExtension("Spatial")

  # Cojo la licencia de Spatial
    if arcpy.CheckExtension("Spatial") == "Available":

        resultado_licencia = arcpy.CheckOutExtension("Spatial")

        if resultado_licencia == "CheckedOut":

            spatial_checkout = True
            
            arcpy.AddMessage(
                time.ctime() + " Licencia 'Spatial Analyst' habilitada correctamente."
            )
        else:
            arcpy.AddError(
                time.ctime() + " ERROR: No se ha podido coger la licencia 'Spatial Analyst'. Estado: "
                + str(resultado_licencia)
            )
            raise RuntimeError("No se pudo obtener la licencia Spatial Analyst.")

    else:
        arcpy.AddError(
            time.ctime() + " Licencia 'Spatial Analyst' no disponible. Abortando."
        )
        raise RuntimeError("Licencia Spatial Analyst no disponible.")

    if not arcpy.Exists(gdb_trabajo):
        arcpy.AddError(time.ctime() + " ERROR CRÍTICO: No existe la Geodatabase de trabajo: " + str(gdb_trabajo))
        raise SystemExit

    existe_GFESPDE = arcpy.Exists("GFESPDE_" + codProv)
    existe_GFESPES = arcpy.Exists("GFESPES_" + codProv)
    existe_GFESP   = arcpy.Exists("GFESP_" + codProv)

    # 1. CONTROL DE ERRORES: Comprobamos si la carpeta de la provincia existe
    if not os.path.exists(carpeta_prov):
        arcpy.AddError(time.ctime() + " ERROR: No existe la carpeta de la provincia seleccionada: " + carpeta_prov)
        raise SystemExit

    # 2. CONTROL DE ERRORES: Comprobamos si la File Geodatabase (.gdb) existe
    if not arcpy.Exists(gdb_trabajo):
        arcpy.AddError(time.ctime() + " ERROR: No existe la Geodatabase de trabajo: "+ gdb_trabajo)
        raise SystemExit
    
    # Si pasa los controles anteriores, configuramos el entorno de forma segura
    arcpy.env.workspace = gdb_trabajo
    ruta_log = os.path.join(carpeta_prov, "log_timeF55.txt")

    # El bloque 'with' abrirá el archivo de log sin problemas porque ya validamos la carpeta antes
    with io.open(ruta_log, "a", encoding="utf-8") as fictime:
        arcpy.AddMessage(
            time.ctime() + " Comienzan los procesos en la provincia: " + codProv
        )

        fictime.write(u'*******************************\n')  # noqa: UP025
        fictime.write(time.ctime() + ' Inicio la provincia ' + codProv + '\n')

        # configuro directorio de trabajo
        arcpy.env.workspace = gdb_trabajo

        #*********************************
        # configuro entornoS

        prov_ras = os.path.join(gdb_trabajo, "GLIMITE_" + codProv)
        dsc = arcpy.Describe(prov_ras)
        coord_sys = dsc.spatialReference
        
        del dsc

        #se asegura de trabajar en = proyeccion que los grid
        arcpy.env.outputCoordinateSystem = coord_sys #proyeccion

        #recinto sigpac
        if int(mun_ini)  == 1:
            arcpy.AddMessage(
                time.ctime() + " Los procesos comienzan desde el municipio 1. Se genera una capa precfe_"+codProv+" nueva"
            )
            

            arcpy.management.Delete(os.path.join(carpeta_proye, "precfe_" + codProv))
            vshp_recp = arcpy.conversion.FeatureClassToFeatureClass(shp_rec, carpeta_proye, "precfe_" + codProv).getOutput(0) # por si distinta proyeccion
            arcpy.management.JoinField(vshp_recp, "DN_OID", bd_rec, "DN_OID")

           
        else:
            arcpy.AddMessage(
                time.ctime() + " Los procesos comienzan desde el municipio "+ mun_ini + ". Se rellenará la capa precfe existente."
            )
            vshp_recp = os.path.join(carpeta_proye, "precfe_" + codProv)
            arcpy.management.RemoveIndex(vshp_recp, ["iID_UNICO"])
            
        #extension con un margen de 100m
        desc = arcpy.Describe(vshp_recp)
        xmin = (int (desc.extent.XMin / 5) * 5) - 100
        ymin = (int (desc.extent.YMin / 5) * 5) - 100
        xmax = ((int (desc.extent.XMax / 5) * 5) + 5) + 100
        ymax = ((int (desc.extent.YMax / 5) * 5) + 5) + 100
        
        del desc

        arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax)) #extension
        arcpy.env.snapRaster = prov_ras  # cuadra los raster
        arcpy.env.mask = prov_ras   # mascara
        arcpy.env.cellSize = prov_ras   #tama?o celda

        #***************************************************
        # preparo raster

        arcpy.AddMessage(time.ctime() + " Preparando los rasters...")
        fictime.write(str(time.ctime() + " Preparando los rasters..." + '\n'))

        vgalt = Raster("gmdt_" + str(codProv)) #20221020
        vgpte = Raster("gpte_" + str(codProv)) #20211116

        vgcsp = Raster("gcsp_" + str(codProv))

        vgfsue = Raster("gfsue_" + str(codProv))
        vgfpte = Raster("gfpte_" + str(codProv))
        vgfveg = Raster("gfveg_" + str(codProv))
        vgfveges = Raster("gfvegesp_" + str(codProv))
        vgfinc = Raster("gfinc_" + str(codProv))

        if existe_GFESPDE: #20211111
            # arcpy.AddMessage("Existe Fdehesa")
            # fictime.write('Existe Fdehesa ' + '\n')
            gtemp_deh = Con(IsNull("GDEH_" + codProv),0,1) #20211125
            gtemp_fespde = Con(IsNull("GFESPDE_" + codProv),0,1)

        if existe_GFESPES: #20211111
            # arcpy.AddMessage("Existe Fespecie CCAA")
            # fictime.write('Existe Fespecie CCAA ' + '\n')
            gtemp_esp = Con(IsNull("GESP_" + codProv),0,1) #20211125
            gtemp_fespes = Con(IsNull("GFESPES_" + codProv),0,1)

        if existe_GFESP: #20211111
            # arcpy.AddMessage("Existe Fespecie total")
            # fictime.write('Existe Fespecie total ' + '\n')    
            gtemp_fesp = Con(IsNull("GFESP_" + codProv),0,1)

        #************************************************
        # preparo shape

        arcpy.AddMessage(time.ctime() + " Preparando los vectoriales...")
        fictime.write(str(time.ctime() + " Preparando los vectoriales..." + '\n'))

        if int(mun_ini)  == 1:
            # preparo campos de salida
            arcpy.management.AddField(vshp_recp,"ID_UNICO","LONG")
            arcpy.management.AddField(vshp_recp,"ALT_NEW","DOUBLE",10,6) #20221020
            arcpy.management.AddField(vshp_recp,"PTE","DOUBLE",10,6) #20211116
            arcpy.management.AddField(vshp_recp,"CSP","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"F_SUE","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"F_PTE","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"F_VEG","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"POR_DEH","DOUBLE",10,6) #20211125
            arcpy.management.AddField(vshp_recp,"POR_FESPDE","DOUBLE",10,6) #20211111
            arcpy.management.AddField(vshp_recp,"POR_ESP","DOUBLE",10,6) #20211125
            arcpy.management.AddField(vshp_recp,"POR_FESPES","DOUBLE",10,6) #20211111
            arcpy.management.AddField(vshp_recp,"POR_FESP","DOUBLE",10,6) #20211111
            arcpy.management.AddField(vshp_recp,"F_VEGES","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"F_INC","DOUBLE",10,6)
            arcpy.management.AddField(vshp_recp,"CSPI","LONG")
            arcpy.management.AddField(vshp_recp,"CSP_RES","DOUBLE")
            arcpy.management.AddField(vshp_recp,"TMP1","SHORT")
            arcpy.management.AddField(vshp_recp,"TMP2","SHORT")
            arcpy.management.AddField(vshp_recp,"TMP3","DOUBLE",10,6)

            arcpy.management.AddField(vshp_recp,"SOLAPES","LONG")
            arcpy.management.AddField(vshp_recp,"SOLAPES2","LONG")

            # inicializo a -1    
            #arcpy.management.MakeFeatureLayer(vshp_recp, "lyshprec")

            arcpy.management.CalculateField(vshp_recp,"ID_UNICO","!OBJECTID!", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"ALT_NEW","-1", "PYTHON3") #20221020
            arcpy.management.CalculateField(vshp_recp,"PTE","-1", "PYTHON3") #20211116
            arcpy.management.CalculateField(vshp_recp,"CSP","-1", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"F_SUE","-1", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"F_PTE","-1", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"F_VEG","-1", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"POR_DEH","0", "PYTHON3") #20211125
            arcpy.management.CalculateField(vshp_recp,"POR_FESPDE","0", "PYTHON3") #20211111
            arcpy.management.CalculateField(vshp_recp,"POR_ESP","0", "PYTHON3") #20211125
            arcpy.management.CalculateField(vshp_recp,"POR_FESPES","0", "PYTHON3") #20211111
            arcpy.management.CalculateField(vshp_recp,"POR_FESP","0", "PYTHON3") #20211111
            arcpy.management.CalculateField(vshp_recp,"F_VEGES","-1", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"F_INC","-1", "PYTHON3") 
            arcpy.management.CalculateField(vshp_recp,"CSP_RES","-1", "PYTHON3")

            arcpy.management.CalculateField(vshp_recp,"SOLAPES","0", "PYTHON3")
            arcpy.management.CalculateField(vshp_recp,"SOLAPES2","0", "PYTHON3")
        
        
        arcpy.AddMessage("Valor de repgeo: " + (repgeo))
        arcpy.AddMessage("Tipo de repgeo: " + str(type(repgeo)))

        # chequea y repara geometria           
        if repgeo == "true":
            errores_geom = os.path.join(arcpy.env.scratchGDB, "errores_temporales")
            while True:
                # Comprobar geometría
                if arcpy.Exists(errores_geom):
                    arcpy.management.Delete(errores_geom)

                arcpy.management.CheckGeometry(vshp_recp, errores_geom)
                conteo = int(arcpy.management.GetCount(errores_geom)[0])

                # Si no hay errores, salir del bucle
                if conteo == 0:
                    arcpy.AddMessage(time.ctime() + " La capa de recintos ya es geometricamente consistente. No es necesario realizar mas reparaciones.")
                    break

                # Hay errores: intentar repararlos
                arcpy.AddMessage(time.ctime() + " Se detectaron errores geometricos. Reparando geometria...")
                arcpy.management.RepairGeometry(vshp_recp)
        else:
            arcpy.AddMessage(time.ctime() + " Se ha elegido no completar procesos de reparacion sobre la capa de recintos...")
            
        try:
            # meto las coordenada del geocentro # nuevo 20230601
            arcpy.management.AddGeometryAttributes(vshp_recp, "CENTROID_INSIDE","#","#","GEOGCS['GCS_ETRS_1989',DATUM['D_ETRS_1989',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]") #20230601
        
        except Exception as e:
            arcpy.AddError(time.ctime() + " Revisa la capa de recintos. Se produjo un error al generar los centroides probablemente debido a errores topologicos no resueltos")
        
        #hago la layer
        arcpy.management.MakeFeatureLayer(vshp_recp, "lyshprec")
        arcpy.management.AddIndex("lyshprec", "ID_UNICO", "iID_UNICO", "UNIQUE","ASCENDING")

        nreg1 = int(arcpy.management.GetCount("lyshprec").getOutput(0))
        # arcpy.AddMessage("Recintos totales de la provincia :" + str(nreg1))

        # saco el listado de municipios - RECFE_TXT2
        arcpy.analysis.Frequency("lyshprec", "recfe_txt2",["MUNICIPIO"])
        nunmun = int(arcpy.management.GetCount("recfe_txt2").getOutput(0)) 
        arcpy.AddMessage(time.ctime() + " Numero de municipios:" + str(nunmun))
        fictime.write(str(time.ctime() + ' Numero de municipios del fichero: ' + str(nunmun) + '\n'))
   
        with arcpy.da.SearchCursor("recfe_txt2", ["OBJECTID", "MUNICIPIO"]) as cur:
            for rec, mun in cur:
                if int(mun) >= int(mun_ini):
                    arcpy.AddMessage(time.ctime() + " ** Procesando " + str(rec) + " de " + str(nunmun) + " - Municipio: " + str(mun) + " a las " + time.ctime())
                    fictime.write(str(time.ctime() + " ** Procesando " + str(rec) + " de " + str(nunmun) + " - Municipio: " + str(mun) + " a las " + '\n'))

                    # genero Fc con el municipio a procesar
                    arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"MUNICIPIO\" =" +  str(mun) )  

                    nrec_municipio = int(arcpy.management.GetCount("lyshprec").getOutput(0))

                    if nrec_municipio > 0:
                        arcpy.AddMessage(time.ctime() + " Numero de recintos: " + str(nrec_municipio))
                        fictime.write(str(time.ctime() + ' Numero de recintos: ' + str(nrec_municipio) + '\n'))
                        
                        vshp_mun = arcpy.conversion.FeatureClassToFeatureClass("lyshprec", carpeta_proye, "sigp_muni").getOutput(0)
                        arcpy.management.MakeFeatureLayer(vshp_mun, "lyshprec2")
                        
                        # detecto solapes
                        arcpy.AddMessage( time.ctime() + " Inicio bucle de solapes")
                        RecSol = 1
                        RecVue = 1
                        while RecSol > 0:
                            RecSol = 0
                            arcpy.AddMessage (time.ctime() + " Inicio vuelta: " + str(RecVue))
                            
                            arcpy.management.SelectLayerByAttribute("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0") 
                            arcpy.analysis.PolygonNeighbors("lyshprec2", ruta_temp, "ID_UNICO", "AREA_OVERLAP","","0.001")

                            arcpy.management.MakeTableView("temp", "lytemp")
                            arcpy.management.SelectLayerByAttribute("lytemp", "NEW_SELECTION", "\"AREA\" > 0") 
                            nreg1 = int(arcpy.management.GetCount("lytemp").getOutput(0)) 
                            #arcpy.AddMessage("solapan :" + str(nreg1))
                            if nreg1 > 0:

                                arcpy.management.CopyRows("lytemp", os.path.join(gdb_trabajo, "SolapesSigp_" + str(codProv)))

                                # arcpy.AddError("PRUEBA: FORZANDO ERROR PARA COMPROBAR LIMPIEZA")
                                # raise Exception("PRUEBA DE LIMPIEZA DE TEMPORALES")

                                #saco numero solapes
                                arcpy.analysis.Frequency("SolapesSigp_" + str(codProv), "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO")
                                nreg2 = int(arcpy.management.GetCount("SolapesSigp_frq_" + str(codProv)).getOutput(0))
                                # arcpy.AddMessage("solapan :" + str(nreg2))

                                #vuelco los solapes en el shape
                                try:
                                    arcpy.management.AddJoin("lyshprec", "ID_UNICO", "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO","KEEP_COMMON")
                                                                 
                                    if RecVue == 1:
                                        arcpy.management.CalculateField("lyshprec","SOLAPES","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON3")
                                
                                finally:
                                    arcpy.management.RemoveJoin ("lyshprec", "SolapesSigp_frq_" + str(codProv))

                                try:
                                    arcpy.management.AddJoin("lyshprec2", "ID_UNICO", "SolapesSigp_frq_" + str(codProv), "src_ID_UNICO","KEEP_COMMON")
                                    
                                    if RecVue == 1:
                                        arcpy.management.CalculateField("lyshprec2","SOLAPES","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON3")
                                        
                                    arcpy.management.CalculateField("lyshprec2","SOLAPES2","!SolapesSigp_frq_" + str(codProv) +".FREQUENCY!", "PYTHON3")
                                    
                                finally:
                                    arcpy.management.RemoveJoin ("lyshprec2", "SolapesSigp_frq_" + str(codProv))

                                #si solape 1 me quedo con uno de ellos
                                arcpy.management.JoinField("SolapesSigp_" + str(codProv), "src_ID_UNICO","SolapesSigp_frq_" + str(codProv),  "src_ID_UNICO", ["FREQUENCY",])
                                
                                arcpy.management.MakeTableView("SolapesSigp_" + str(codProv), "lysolapes")
                                arcpy.management.SelectLayerByAttribute("lysolapes", "NEW_SELECTION", "\"FREQUENCY\" = 1")
                                nreg11 = int(arcpy.management.GetCount("lysolapes").getOutput(0))
                                #arcpy.AddMessage("Con solape 1:" + str(nreg11))
                                if nreg11 > 0:
                                    arcpy.analysis.Statistics("lysolapes", "SolapesSigp_frq2_" + str(codProv), [["src_ID_UNICO", "FIRST"]], "AREA")
                                    
                                    try:
                                        arcpy.management.AddJoin("lyshprec2", "ID_UNICO", "SolapesSigp_frq2_" + str(codProv), "FIRST_src_ID_UNICO","KEEP_COMMON")
                                        # arcpy.AddMessage(int(arcpy.management.GetCount("lyshprec2").getOutput(0)))
                                        arcpy.management.CalculateField("lyshprec2","SOLAPES2","0", "PYTHON3")
                                        
                                    finally:
                                        arcpy.management.RemoveJoin ("lyshprec2", "SolapesSigp_frq2_" + str(codProv))

                                else:                                                                                                      
                                    with arcpy.da.SearchCursor(
                                        "SolapesSigp_" + str(codProv),
                                        ["src_ID_UNICO"],
                                        sql_clause=(None, "ORDER BY FREQUENCY ASC")) as cur2:
                                        for row2 in cur2:
                                            recid = row2[0]
                                            # arcpy.AddMessage(row2[0])

                                    arcpy.management.SelectLayerByAttribute(
                                        "lyshprec2",
                                        "NEW_SELECTION",
                                        "\"ID_UNICO\" =" + str(recid)
                                    ) 

                                    nreg12 = int(arcpy.management.GetCount("lyshprec2").getOutput(0))
                                    # arcpy.AddMessage(nreg12)   
                                                                             
                                    if nreg12 > 0:                                                                                        
                                        arcpy.management.CalculateField("lyshprec2","SOLAPES2","0", "PYTHON3")                              

                                   
                                #limpio
                                
                                if arcpy.Exists("lytemp"):
                                    arcpy.management.Delete("lytemp")

                                if arcpy.Exists("lysolapes"):
                                    arcpy.management.Delete("lysolapes")
    
                                if arcpy.Exists("temp"):
                                    arcpy.management.Delete("temp")
                                if arcpy.Exists("SolapesSigp_frq_" + str(codProv)):
                                    arcpy.management.Delete("SolapesSigp_frq_" + str(codProv))
                                if arcpy.Exists("SolapesSigp_frq2_" + str(codProv)):
                                    arcpy.management.Delete("SolapesSigp_frq2_" + str(codProv))
                                if arcpy.Exists("SolapesSigp_" + str(codProv)):
                                    arcpy.management.Delete("SolapesSigp_" + str(codProv))
                
                            ##*************************************************************************************************************
                            ## TODOS NO SOLAPAN - paso recintos a raster y calculo estadisticas por municipio
                            ## ************************************************************************************************************

                            arcpy.AddMessage(time.ctime() + " Se inicia el bucle de los recintos que NO solapan")

                            #selecciono lo que se procesa - NO SOLAPAN
                            arcpy.management.SelectLayerByAttribute("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0") 
                            nreg2 = int(arcpy.management.GetCount("lyshprec2").getOutput(0)) 
                            arcpy.AddMessage(time.ctime() + " Numero de recintos que no solapan :" + str(nreg2))
                            
                            if nreg2 > 0:
                                # METODO 1 - paso recintos a raster y calculo estadisticas de todo el municipio a la vez
                                # ********************************************************************************************
                                # arcpy.AddMessage ("Inicio METODO 1")
                                # arcpy.AddMessage( "Hora: " + time.ctime())

                                # miro su extension y calculo para pasar a grid
                                descf = arcpy.Describe("sigp_muni")
                                xmin = (int(descf.extent.XMin / 5)) * 5
                                ymin = (int(descf.extent.YMin / 5)) * 5
                                xmax = ((int(descf.extent.XMax / 5)) * 5) + 10
                                ymax = ((int(descf.extent.YMax / 5)) * 5) + 10
                                            
                                arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax))

                                #paso a raster
                                arcpy.conversion.PolygonToRaster("lyshprec2", "ID_UNICO","gsigp_muni","CELL_CENTER", "", 1) #tama o de celda 1
                                arcpy.management.BuildRasterAttributeTable("gsigp_muni", "Overwrite")

                                #chequeo que tenga valores y si tiene calculo estadisticas por recinto
                                grdmean = arcpy.GetRasterProperties_management("gsigp_muni", "UNIQUEVALUECOUNT")
                                
                                vacio = grdmean.getOutput(0)
                                #vacio = 0
                                if int(vacio) > 0: #== 0:
                                    #arcpy.management.BuildRasterAttributeTable("gsigp_muni", "Overwrite")
                                                                    
                                    arcpy.env.extent = "gsigp_muni"  #extension
                                    arcpy.env.snapRaster = "gsigp_muni" # cuadrar los raster
                                    arcpy.env.mask = "gsigp_muni" # mascara
                                    arcpy.env.cellSize = 1 #tama o celda

                                    #pauso para que desbloque los ficheros, 5m
                                    #arcpy.AddMessage("Ante de dormir " + time.ctime())
                                    #time.sleep(120)
                                    #arcpy.AddMessage("Despues de dormir " + time.ctime())
                                                
                                    arcpy.AddMessage (time.ctime() + " Calculando estadisticas...")
                                    STAT_TXT13 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgalt, "sta13", "NODATA", "MEAN") #20221020
                                    arcpy.management.AddIndex("sta13", "Value", "sta13_Value", "UNIQUE","ASCENDING") #20221020
                                    STAT_TXT10 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgpte, "sta10", "NODATA", "MEAN") #20211116
                                    arcpy.management.AddIndex("sta10", "Value", "sta10_Value", "UNIQUE","ASCENDING") #20211116
                                    STAT_TXT1 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgcsp, "sta1", "NODATA", "MEAN")
                                    arcpy.management.AddIndex("sta1", "Value", "sta1_Value", "UNIQUE","ASCENDING")
                                    STAT_TXT2 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfsue, "sta2", "NODATA", "MEAN")
                                    arcpy.management.AddIndex("sta2", "Value", "sta2_Value", "UNIQUE","ASCENDING")
                                    STAT_TXT3 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfpte, "sta3", "NODATA", "MEAN")
                                    arcpy.management.AddIndex("sta3", "Value", "sta3_Value", "UNIQUE","ASCENDING")
                                    STAT_TXT4 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfveg, "sta4", "NODATA", "MEAN")
                                    arcpy.management.AddIndex("sta4", "Value", "sta4_Value", "UNIQUE","ASCENDING")
                                    STAT_TXT5 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfveges, "sta5", "NODATA", "MEAN")
                                    arcpy.management.AddIndex("sta5", "Value", "sta5_Value", "UNIQUE","ASCENDING")
                                    STAT_TXT6 = ZonalStatisticsAsTable("gsigp_muni", "Value",vgfinc, "sta6", "NODATA", "MEAN") 
                                    arcpy.management.AddIndex("sta6", "Value", "sta6_Value", "UNIQUE","ASCENDING")
                                    if existe_GFESPDE: #20211111
                                        STAT_TXT11 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_deh, "sta11", "DATA", "MEAN") #20211125 
                                        arcpy.management.AddIndex("sta11", "Value", "sta11_Value", "UNIQUE","ASCENDING") #20211125
                                        STAT_TXT7 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fespde, "sta7", "DATA", "MEAN") #20211111 
                                        arcpy.management.AddIndex("sta7", "Value", "sta7_Value", "UNIQUE","ASCENDING") #20211111
                                    if existe_GFESPES: #20211111
                                        STAT_TXT12 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_esp, "sta12", "DATA", "MEAN") #20211125 
                                        arcpy.management.AddIndex("sta12", "Value", "sta12_Value", "UNIQUE","ASCENDING") #20211125
                                        STAT_TXT8 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fespes, "sta8", "DATA", "MEAN") #20211111 
                                        arcpy.management.AddIndex("sta8", "Value", "sta8_Value", "UNIQUE","ASCENDING") #20211111
                                    if existe_GFESP: #20211111
                                        STAT_TXT9 = ZonalStatisticsAsTable("gsigp_muni", "Value",gtemp_fesp, "sta9", "DATA", "MEAN") #20211111 
                                        arcpy.management.AddIndex("sta9", "Value", "sta9_Value", "UNIQUE","ASCENDING") #20211111
    
                                    # cargo en el shape de recintos inicial 
                                    arcpy.AddMessage (time.ctime() + " Copiando el resultado a la feature class precfe")

                                    arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION")
                                                                                                    
                                    try:
                                        
                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta1","Value","KEEP_COMMON")                                                                 
                                        arcpy.management.CalculateField("lyshprec","CSP","!sta1.MEAN! / 10000", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta2","Value","KEEP_COMMON")
                                        arcpy.management.CalculateField("lyshprec","F_SUE","!sta2.MEAN! / 100", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta3","Value","KEEP_COMMON")
                                        arcpy.management.CalculateField("lyshprec","F_PTE","!sta3.MEAN! / 100", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta4","Value","KEEP_COMMON")
                                        arcpy.management.CalculateField("lyshprec","F_VEG","!sta4.MEAN! / 100", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta5","Value","KEEP_COMMON")
                                        arcpy.management.CalculateField("lyshprec","F_VEGES","!sta5.MEAN! / 100", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta6","Value","KEEP_COMMON")
                                        arcpy.management.CalculateField("lyshprec","F_INC","!sta6.MEAN!", "PYTHON3")

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta10","Value","KEEP_COMMON") #20211116
                                        arcpy.management.CalculateField("lyshprec","PTE","!sta10.MEAN!", "PYTHON3") #20211116

                                        arcpy.management.AddJoin("lyshprec","ID_UNICO","sta13","Value","KEEP_COMMON") #20221020
                                        arcpy.management.CalculateField("lyshprec","ALT_NEW","!sta13.MEAN!", "PYTHON3") #20221020

                                        if existe_GFESPDE: #20211111
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta11","Value","KEEP_COMMON") #20211125
                                            arcpy.management.CalculateField("lyshprec","POR_DEH","!sta11.MEAN! * 100", "PYTHON3")  #20211125
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta7","Value","KEEP_COMMON") #20211111
                                            arcpy.management.CalculateField("lyshprec","POR_FESPDE","!sta7.MEAN! * 100", "PYTHON3")  #20211111

                                        if existe_GFESPES: #20211111
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta12","Value","KEEP_COMMON") #20211125
                                            arcpy.management.CalculateField("lyshprec","POR_ESP","!sta12.MEAN! * 100", "PYTHON3")  #20211125
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta8","Value","KEEP_COMMON") #20211111
                                            arcpy.management.CalculateField("lyshprec","POR_FESPES","!sta8.MEAN! * 100", "PYTHON3")  #20211111

                                        if existe_GFESP: #20211111
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta9","Value","KEEP_COMMON") #20211111
                                            arcpy.management.CalculateField("lyshprec","POR_FESP","!sta9.MEAN! * 100", "PYTHON3")  #20211111

                                    finally:
                                        
                                        arcpy.management.RemoveJoin("lyshprec")

                                    arcpy.env.mask = None
                                    arcpy.env.snapRaster = None
                              
                                # METODO 2 -  se rasterizan a 0,5 metros los recintos de superficie menor de 50 m2 o que no se han procesado
                                # ********************************************************************************************
                                # arcpy.AddMessage ("Inicio METODO 2")
                                # arcpy.AddMessage( "Hora: " + time.ctime())

                                #saco los recintos menores de 50m2
                                #arcpy.management.MakeFeatureLayer("sigp_muni","lyshprec2")
                                arcpy.management.SelectLayerByAttribute("lyshprec2", "NEW_SELECTION", "Shape_Area <= 50 and \"SOLAPES2\" = 0" )
                                            
                                Nrec2 = arcpy.management.GetCount("lyshprec2").getOutput(0)

                                if int(Nrec2) > 0:
                                    arcpy.AddMessage (time.ctime() + " Numero de recintos menores de 50 m2: " + str(Nrec2))
                                    fictime.write(str(time.ctime() + ' Numero de recintos menores de 50 m2: ' + (Nrec2) + u'\n'))
                                    vshp_mun2 = arcpy.conversion.FeatureClassToFeatureClass("lyshprec2", carpeta_proye, "sigp_muni2").getOutput(0)                                    

                                    # miro su extension y calculo para pasar a grid
                                    descf = arcpy.Describe("sigp_muni2")
                                    xmin = (int(descf.extent.XMin / 5)) * 5
                                    ymin = (int(descf.extent.YMin / 5)) * 5
                                    xmax = ((int(descf.extent.XMax / 5)) * 5) + 10
                                    ymax = ((int(descf.extent.YMax / 5)) * 5) + 10

                                    arcpy.env.extent = arcpy.Extent(int(xmin), int(ymin), int(xmax), int(ymax))
                    
                                    #paso a raster
                                    arcpy.conversion.PolygonToRaster("sigp_muni2", "ID_UNICO","gsigp_muni2","CELL_CENTER", "", 0.5) #tama o de celda 0.5
                                    arcpy.management.BuildRasterAttributeTable("gsigp_muni2", "Overwrite")

                                    #chequeo que tenga valores y si tiene calculo estadisticas por recinto
                                    grdmean = arcpy.GetRasterProperties_management("gsigp_muni2", "UNIQUEVALUECOUNT")
                                    
                                    vacio = grdmean.getOutput(0)
                                    #vacio = 0
                                    if int(vacio) > 0: #== 0:
                                        #arcpy.management.BuildRasterAttributeTable("gsigp_muni2", "Overwrite")
                                                                    
                                        arcpy.env.extent = "gsigp_muni2"  #extension
                                        arcpy.env.snapRaster = "gsigp_muni2" # cuadrar los raster
                                        arcpy.env.mask = "gsigp_muni2" # mascara
                                        arcpy.env.cellSize = 0.5 #tama o celda
                                    
                                        arcpy.AddMessage (time.ctime() + " Calculando estadisticas...")
                                        STAT_TXT13 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgalt, "sta13", "NODATA", "MEAN") #20221020
                                        arcpy.management.AddIndex("sta13", "Value", "sta13_Value", "UNIQUE","ASCENDING") #20221020
                                        STAT_TXT10 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgpte, "sta10", "NODATA", "MEAN") #20211116
                                        arcpy.management.AddIndex("sta10", "Value", "sta10_Value", "UNIQUE","ASCENDING") #20211116
                                        STAT_TXT1 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgcsp, "sta1", "NODATA", "MEAN")
                                        arcpy.management.AddIndex("sta1", "Value", "sta1_Value", "UNIQUE","ASCENDING")
                                        STAT_TXT2 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfsue, "sta2", "NODATA", "MEAN")
                                        arcpy.management.AddIndex("sta2", "Value", "sta2_Value", "UNIQUE","ASCENDING")
                                        STAT_TXT3 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfpte, "sta3", "NODATA", "MEAN")
                                        arcpy.management.AddIndex("sta3", "Value", "sta3_Value", "UNIQUE","ASCENDING")
                                        STAT_TXT4 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfveg, "sta4", "NODATA", "MEAN")
                                        arcpy.management.AddIndex("sta4", "Value", "sta4_Value", "UNIQUE","ASCENDING")
                                        STAT_TXT5 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfveges, "sta5", "NODATA", "MEAN")
                                        arcpy.management.AddIndex("sta5", "Value", "sta5_Value", "UNIQUE","ASCENDING")
                                        STAT_TXT6 = ZonalStatisticsAsTable("gsigp_muni2", "Value",vgfinc, "sta6", "NODATA", "MEAN") 
                                        arcpy.management.AddIndex("sta6", "Value", "sta6_Value", "UNIQUE","ASCENDING")

                                        if existe_GFESPDE: #20211111
                                            STAT_TXT11 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_deh, "sta11", "DATA", "MEAN") #20211125 
                                            arcpy.management.AddIndex("sta11", "Value", "sta11_Value", "UNIQUE","ASCENDING") #20211125
                                            STAT_TXT7 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fespde, "sta7", "DATA", "MEAN") #20211111 
                                            arcpy.management.AddIndex("sta7", "Value", "sta7_Value", "UNIQUE","ASCENDING") #20211111
                                        if existe_GFESPES: #20211111
                                            STAT_TXT12 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_esp, "sta12", "DATA", "MEAN") #20211125 
                                            arcpy.management.AddIndex("sta12", "Value", "sta12_Value", "UNIQUE","ASCENDING") #20211125
                                            STAT_TXT8 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fespes, "sta8", "DATA", "MEAN") #20211111 
                                            arcpy.management.AddIndex("sta8", "Value", "sta8_Value", "UNIQUE","ASCENDING") #20211111
                                        if existe_GFESP: #20211111
                                            STAT_TXT9 = ZonalStatisticsAsTable("gsigp_muni2", "Value",gtemp_fesp, "sta9", "DATA", "MEAN") #20211111 
                                            arcpy.management.AddIndex("sta9", "Value", "sta9_Value", "UNIQUE","ASCENDING") #20211111
                                        
                                        
                                        # cargo en el shape de recintos inicial 
                                        arcpy.AddMessage (time.ctime() + " Copiando el resultado a la feature class precfe")

                                        arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION")

                                        try:
                                            
                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta1","Value","KEEP_COMMON")
                                            # arcpy.AddMessage("seleccion para calcular: " + arcpy.management.GetCount("lyshprec").getOutput(0))
                                            arcpy.management.CalculateField("lyshprec","CSP","!sta1.MEAN! / 10000", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta2","Value","KEEP_COMMON")
                                            arcpy.management.CalculateField("lyshprec","F_SUE","!sta2.MEAN! / 100", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta3","Value","KEEP_COMMON")
                                            arcpy.management.CalculateField("lyshprec","F_PTE","!sta3.MEAN! / 100", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta4","Value","KEEP_COMMON")
                                            arcpy.management.CalculateField("lyshprec","F_VEG","!sta4.MEAN! / 100", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta5","Value","KEEP_COMMON")
                                            arcpy.management.CalculateField("lyshprec","F_VEGES","!sta5.MEAN! / 100", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta6","Value","KEEP_COMMON")
                                            arcpy.management.CalculateField("lyshprec","F_INC","!sta6.MEAN!", "PYTHON3")

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta10","Value","KEEP_COMMON") #20211116
                                            arcpy.management.CalculateField("lyshprec","PTE","!sta10.MEAN!", "PYTHON3") #20211116

                                            arcpy.management.AddJoin("lyshprec","ID_UNICO","sta13","Value","KEEP_COMMON") #20221020
                                            arcpy.management.CalculateField("lyshprec","ALT_NEW","!sta13.MEAN!", "PYTHON3") #20221020

                                            if existe_GFESPDE: #20211111
                                                arcpy.management.AddJoin("lyshprec","ID_UNICO","sta11","Value","KEEP_COMMON") #20211125
                                                arcpy.management.CalculateField("lyshprec","POR_DEH","!sta11.MEAN! * 100", "PYTHON3")  #20211125
                                                arcpy.management.AddJoin("lyshprec","ID_UNICO","sta7","Value","KEEP_COMMON") #20211111
                                                arcpy.management.CalculateField("lyshprec","POR_FESPDE","!sta7.MEAN! * 100", "PYTHON3")  #20211111

                                            if existe_GFESPES: #20211111
                                                arcpy.management.AddJoin("lyshprec","ID_UNICO","sta12","Value","KEEP_COMMON") #20211125
                                                arcpy.management.CalculateField("lyshprec","POR_ESP","!sta12.MEAN! * 100", "PYTHON3")  #20211125
                                                arcpy.management.AddJoin("lyshprec","ID_UNICO","sta8","Value","KEEP_COMMON") #20211111
                                                arcpy.management.CalculateField("lyshprec","POR_FESPES","!sta8.MEAN! * 100", "PYTHON3")  #20211111

                                            if existe_GFESP: #20211111
                                                arcpy.management.AddJoin("lyshprec","ID_UNICO","sta9","Value","KEEP_COMMON") #20211111
                                                arcpy.management.CalculateField("lyshprec","POR_FESP","!sta9.MEAN! * 100", "PYTHON3")  #20211111
                                        
                                        finally:
                                            arcpy.management.RemoveJoin("lyshprec")
                                                                   
                                else:
                                    arcpy.AddMessage (time.ctime() + " No se ha encontrado ningun recinto < 50m2")
                                        
                                #fin if de NO solapes
                                #****************************************************************
                                
                                arcpy.management.SelectLayerByAttribute("lyshprec2", "NEW_SELECTION", "\"SOLAPES2\" = 0 or \"SOLAPES2\" = 99")
                                # arcpy.AddMessage("seleccion para 99: " + arcpy.management.GetCount("lyshprec2").getOutput(0))
                                arcpy.management.CalculateField("lyshprec2","SOLAPES2","99", "PYTHON3")
                                arcpy.management.SelectLayerByAttribute("lyshprec2", "SWITCH_SELECTION")

                                nrec_seleccion_0 = int(arcpy.management.GetCount("lyshprec2").getOutput(0))                  
                                # arcpy.AddMessage("seleccion para 0: " + str(nrec_seleccion_0))

                                if nrec_seleccion_0  > 0:
                                    arcpy.management.CalculateField("lyshprec2","SOLAPES2","0", "PYTHON3")
                                    RecSol = 1
                                    RecVue = RecVue + 1
                            else:
                                RecSol = 0

                        # fin del whilw
                        
                        # limpio seleccion del municipio
                        arcpy.env.extent = vgcsp  #extension

                        # arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "")
                        
                        arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION")
                    
                    fictime.write(str(time.ctime() + ' Termino el municipio  ' + str(mun) + '\n'))

                    arcpy.AddMessage(time.ctime() + " Termino el municipio " + str(mun))
                
                    # Se procede con la limpieza de elementos generados para el municipio
                    arcpy.env.mask = None
                    arcpy.env.snapRaster = None
                    arcpy.management.ClearWorkspaceCache()
                    
                else:
                    arcpy.AddMessage (time.ctime() + " Ya estaba Procesando " + str(rec) + " de " + str(nunmun) + " - Municipio: " + str(mun))
                
                if arcpy.Exists("lyshprec2"):
                    arcpy.management.Delete("lyshprec2")
                if arcpy.Exists("gsigp_muni"):
                    arcpy.management.Delete("gsigp_muni")
                if arcpy.Exists("gsigp_muni2"):
                    arcpy.management.Delete("gsigp_muni2")
                if arcpy.Exists("PROYE\\sigp_muni"):
                    arcpy.management.Delete("PROYE\\sigp_muni")
                if arcpy.Exists("PROYE\\sigp_muni2"):
                    arcpy.management.Delete("PROYE\\sigp_muni2")
                    
            # if 'vgalt' in locals(): del vgalt
            # if 'vgpte' in locals(): del vgpte
            # if 'vgcsp' in locals(): del vgcsp
            # if 'vgfsue' in locals(): del vgfsue
            # if 'vgfpte' in locals(): del vgfpte
            # if 'vgfveg' in locals(): del vgfveg
            # if 'vgfveges' in locals(): del vgfveges
            # if 'vgfinc' in locals(): del vgfinc
            
            # if 'gtemp_deh' in locals(): del gtemp_deh
            # if 'gtemp_fespde' in locals(): del gtemp_fespde
            # if 'gtemp_esp' in locals(): del gtemp_esp
            # if 'gtemp_fespes' in locals(): del gtemp_fespes
            # if 'gtemp_fesp' in locals(): del gtemp_fesp
            
        fictime.write(str(time.ctime() + ' Termine el procesado municipio a municipio sin solapes a las ' + time.ctime()+ '\n'))
        # fictime.write('*****************************************\n')
        
        arcpy.AddMessage(time.ctime() + " Se termino el procesamiento de todos los municipios")
          
                                
        # fin del for del municipio

        #ajusto
        arcpy.AddMessage(time.ctime() + " Procesando ajustes finales...")
        fictime.write(str(time.ctime() + ' Inicio ajustes \n'))

        # se calcula el atributo csp_res
    
        if codProv in ['15', '27', '32', '36', '04', '11', '14', '18', '21', '23', '29', '41', '31', '06', '10', '01', '20', '48', '02', '13', '16', '19', '45', '07']:
            arcpy.AddMessage(time.ctime() + " Redondeo de 10 en 10 desde 20 a 90- Andalucia, Galicia, Navarra, Pais Vasco, Extremadura, CasMan, Baleares ")
            fictime.write(str(time.ctime() + ' Redondeo de 10 en 10 desde 20 a 90 - Andalucia, Galicia, Navarra, Pais Vasco, Extremadura, CasMan, Baleares ' + time.ctime()+ '\n'))
        
            #redondeo seg n metodolog a del 2015
            # paso a entero
            # csp < 20 cap_res = 0, csp >= 90 csp_res = 100
            # intervalos de 10 puntos
            
            #paso a entero
            arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "")
            arcpy.management.CalculateField("lyshprec","CSPI","!CSP!", "PYTHON3")

            #redondeo a intervalos
            arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 0")
            arcpy.management.CalculateField("lyshprec","CSP_RES","0", "PYTHON3")
            
            arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20")
            if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                    arcpy.management.CalculateField("lyshprec","CSP_RES","!CSPI! / 10", "PYTHON3")
                    arcpy.management.CalculateField("lyshprec","CSP_RES","!CSP_RES! * 10 + 5", "PYTHON3")
                    arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90")
                    if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                        arcpy.management.CalculateField("lyshprec","CSP_RES","100", "PYTHON3")
            arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "")
            
        elif codProv in ['33', '28', '03', '12', '46']:
            arcpy.AddMessage(time.ctime() + " Redondeo de 5 en 5 desde 20 a 90- Asturias, Madrid, CValenciana ")
            fictime.write(str(time.ctime() + ' Redondeo de 5 en 5 desde 20 a 90- Asturias, Madrid, CValenciana ' + time.ctime()+ '\n'))
            
            # redondeo de 5 en 5 - cambian intervalos desde 13/01/2022 (>=20 a <22,5 valor 20.......)
            # csp < 20 csp_res = 0, csp >= 90 csp_res = 100

            #paso a entero
            arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "")
            arcpy.management.CalculateField("lyshprec","CSPI","!CSP!", "PYTHON3") #cambia 20230519

            #redondeo a intervalos
            arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 0") #cambia 20230519
            arcpy.management.CalculateField("lyshprec","CSP_RES","0", "PYTHON3")
            
            arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20 and \"CSPI\" < 90") #cambia 20230519
            if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                arcpy.management.CalculateField("lyshprec","TMP3","!CSP! + 2.5", "PYTHON3")
                arcpy.management.CalculateField("lyshprec","TMP1","int(!TMP3! / 5)", "PYTHON3")
                arcpy.management.CalculateField("lyshprec","CSP_RES","!TMP1! * 5", "PYTHON3")
                                                    
            arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90") #cambia 20230519
            if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                arcpy.management.CalculateField("lyshprec","CSP_RES","100", "PYTHON3")
            arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "")
            
        else:
            arcpy.AddMessage(time.ctime() + " Redondeo a la unidad regla del 5 desde 20 a 90- FEGA: Aragon, Murcia, CasLeon, Rioja, Cantabria, Canarias de 10 a 90, Catalu a de 20 a 100")
            fictime.write(str(time.ctime() + ' Redondeo a la unidad regla del 5 desde 20 a 90- FEGA: Aragon, Murcia, CasLeon, Rioja, Cantabria, Canarias de 10 a 90, Catalu a de 20 a 100)' + time.ctime()+ '\n'))
            
            # redondeo al entero m s pr ximo con la regla del 5
            # csp < 20 csp_res = 0, csp >= 90 csp_res = 100
            # Csp >= 20 y csp >= 20,5 csp_res = 20
            # csp > 20,5 y csp <= 21,5 csp_res = 21 y as  sucesivamente

            #paso a entero
            arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION", "") #cambia 20230519
            arcpy.management.CalculateField("lyshprec","CSPI","!CSP!", "PYTHON3") #cambia 20230519
            
            # intervalo inferior
            if codProv in ['35', '38']:
                arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" < 10") #cambia 20230519
            else:
                arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" < 20") #cambia 20230519
            if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                arcpy.management.CalculateField("lyshprec","CSP_RES","0", "PYTHON3")
        
            # medio, de uno en uno    
            if codProv in ['35', '38']:
                arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 10") #cambia 20230519
            else:
                arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 20") #cambia 20230519
            if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                arcpy.management.CalculateField("lyshprec","CSP_RES","int(!CSP! + 0.5)", "PYTHON3")
                arcpy.management.CalculateField("lyshprec","TMP1","!CSP! * 10", "PYTHON3")
                ## arcpy.management.CalculateField("lyshprec","TMP2","Right(!TMP1!,1)", "PYTHON3")
                arcpy.management.CalculateField("lyshprec","TMP2","int(str(!TMP1!)[-1])", "PYTHON3")
                arcpy.management.CalculateField("lyshprec","TMP3","!TMP1! / 10", "PYTHON3")
                
                arcpy.management.SelectLayerByAttribute("lyshprec", "SUBSET_SELECTION", "\"TMP2\" = 5 AND \"CSP\" = \"TMP3\"")
                if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                    arcpy.management.CalculateField("lyshprec","CSP_RES","!CSP_RES! - 1", "PYTHON3")

            #intervalo superior
            if codProv in ['08', '17', '25', '43']:
                arcpy.AddMessage(time.ctime() + " Soy Cataluña, no tengo intervalo superior")
            else:
                arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSPI\" >= 90") #cambia 20230519
                if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
                    arcpy.management.CalculateField("lyshprec","CSP_RES","100", "PYTHON3")

        # no calculo
        arcpy.management.SelectLayerByAttribute("lyshprec", "NEW_SELECTION", "\"CSP\" = -1")
        if int(arcpy.management.GetCount("lyshprec").getOutput(0)) > 0:
            arcpy.management.CalculateField("lyshprec","CSP_RES","- 1", "PYTHON3")
            arcpy.management.CalculateField("lyshprec","POR_DEH","- 1", "PYTHON3") #20211125
            arcpy.management.CalculateField("lyshprec","POR_FESPDE","- 1", "PYTHON3") #20211111
            arcpy.management.CalculateField("lyshprec","POR_ESP","- 1", "PYTHON3") #20211125
            arcpy.management.CalculateField("lyshprec","POR_FESPES","- 1", "PYTHON3") #20211111
            arcpy.management.CalculateField("lyshprec","POR_FESP","- 1", "PYTHON3") #20211111
            
        arcpy.management.SelectLayerByAttribute("lyshprec", "CLEAR_SELECTION")

        if arcpy.Exists("lyshprec"):
            arcpy.management.Delete("lyshprec")

        # elimina los temporales
        for temporal in temporales:
            if arcpy.Exists(temporal):
                arcpy.management.Delete(temporal)

        fictime.write(str(time.ctime() + ' Termine todo a las ' + time.ctime() + '\n'))
        fictime.write(u'*******************************\n')
        fictime.close()
        
        arcpy.AddMessage(time.ctime() + " Se han terminado todos los procesos correctamente")
        arcpy.AddMessage("!!Acuerdate de revisar los ficheros de salida. Borra el de errores geometrico si das por terminado el calculo !!" )

except arcpy.ExecuteError:
    arcpy.AddError("ERROR DE ARCPY:")
    arcpy.AddError(arcpy.GetMessages(2))
    raise

except Exception as e:
    arcpy.AddError("ERROR NO CONTROLADO: " + (str(e)))
    raise

finally:
    
    # Liberar objetos Raster
    for nombre in [
        "vgalt", "vgpte", "vgcsp",
        "vgfsue", "vgfpte", "vgfveg",
        "vgfveges", "vgfinc",
        "gtemp_deh", "gtemp_fespde",
        "gtemp_esp", "gtemp_fespes",
        "gtemp_fesp"
    ]:
        if nombre in locals():
            try:
                del locals()[nombre]
            except:  # noqa: E722, S110
                pass
        
    # Borrar temporales con reintentos
    for temporal in temporales:
        borrar_temporal(temporal, intentos=5, espera=2)
    
    if spatial_checkout:
        arcpy.CheckInExtension("Spatial")
        arcpy.AddMessage(time.ctime() + " Licencia Spatial Analyst liberada correctamente")
        
    # limpio el cache
    arcpy.management.ClearWorkspaceCache()
    arcpy.AddMessage(time.ctime() + " Limpiando la cache...")

print("script completado totalmente")


# %%






