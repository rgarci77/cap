# **********************************
# Programa: actualiza los rasters CAP2023, del mes elegido para 2023
# Salida: rasters
#
# Fecha : abril-2023
# Autor: bvm
#
# ************************************
import arcpy
from arcpy.sa import *
import os
import time
from time import gmtime, strftime

#coje los parametros de la herramienta
dirPrin = arcpy.GetParameterAsText(0) # directorio de trabajo (ACTUALIZA_rasters)
dirIni =  arcpy.GetParameterAsText(1) # directorio donde provincias con datos iniciales (Ruth-16_Cambios_mensuales)
dirFin = arcpy.GetParameterAsText(2) # directorio con provincias que actualiza (RASTERS_CAP)
dirLimp = arcpy.GetParameterAsText(3) # directorio donde prepara GDBs para geoprocesos (fss)

dirSem = arcpy.GetParameterAsText(4) # directorio con provincias con datos semilla
dirSemg = dirSem + "\\programas\\semillas\\estructura_GDBs"
dirSemf = dirSem + "\\programas\\semillas\\control_cambios"

dirHist = arcpy.GetParameterAsText(5) # directorio para historicos Valentin Beato
FFiltros = arcpy.GetParameterAsText(6) #fichero de filtros irregulares

provIni = arcpy.GetParameterAsText(7) # numero de provincia partir del que se quiere procesar

anio = arcpy.GetParameterAsText(8) # año a procesar
codMes = arcpy.GetParameterAsText(9) # mes a procesar

Prepara = arcpy.GetParameterAsText(10) # para que ejecute el bloque de preparacion
Procesa = arcpy.GetParameterAsText(11) # para que ejecute el bloque de procesamiento
Proinc = arcpy.GetParameterAsText(12) # para que ejecute el bloque de incendios
Prosue = arcpy.GetParameterAsText(13) # para que ejecute el bloque de suelo
Proveg = arcpy.GetParameterAsText(14) # para que ejecute el bloque de vegetacion
Provegfil = arcpy.GetParameterAsText(15) # para que ejecute el bloque de filtro de veg
Prodeh = arcpy.GetParameterAsText(16) # para que ejecute el bloque de dehesa
ProespCA = arcpy.GetParameterAsText(17) # para que ejecute el bloque de especie CA
Proesp = arcpy.GetParameterAsText(18) # para que ejecute el bloque de especie total
Provegesp = arcpy.GetParameterAsText(19) # para que ejecute el bloque de vegetacion con especie
Proca = arcpy.GetParameterAsText(20) # para que ejecute el bloque de CA
ProGDB = arcpy.GetParameterAsText(21) # prepara GDB limpia
ProFin = arcpy.GetParameterAsText(22) # prepara cambios final


# para que machaque si existen
arcpy.env.overwriteOutput = True

#cojo la licencia de Spatial
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")

cambiaveg = 0
cambiaesp = 0
cambiainc = 0

#****************************************
# BLOQUE DE PREPARACION
#*************************************

if Prepara == "true":
    arcpy.AddMessage("Ejecuto el bloque de PREPARACIÓN (genera carpetas, copia datos iniciales,...")
    arcpy.AddMessage("****************************************************************************")

    # chequea si existe directorio en datos ori para este mes y si no crea
    if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes):
        arcpy.AddMessage ("Ya existe en datos ori este mes")
    else:
        os.mkdir(dirPrin + "\\datos_ori\\M" + anio + codMes)

    # chequea si existe directorio en PROYE para este mes y si no crea
    if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes):
        arcpy.AddMessage ("Ya existe en PROYE este mes")
    else:
        os.mkdir(dirPrin + "\\PROYE\\M" + anio + codMes)

    # chequea si existe directorio en LIMPIO para este mes y si no crea
    if arcpy.Exists(dirLimp + "\\M" + anio + codMes):
        arcpy.AddMessage ("Ya existe en LIMPIO este mes")
    else:
        os.mkdir(dirLimp + "\\M" + anio + codMes)

    #*************************************************
    #abre el fichero de tiempos
        
    fictime = open(dirPrin + "\\PROYE\\M" + anio + codMes + "\log_timeF10.txt","a")
    fictime.write('*******************************\n')

    arcpy.AddMessage( "Inicio el MES: " + anio + codMes + " el " + time.ctime())
    fictime.write('Inicio el MES ' + anio + codMes + ' el ' + time.ctime() + '\n')

    # copia plantilla de control_cambios si no existe
    if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\Temp_CC.dbf"):
        arcpy.AddMessage ("Ya existe el fichero de Control de cambios")
    else:
        arcpy.Copy_management(dirSemf + "\\Actualiza_rasters.dbf", dirPrin + "\\PROYE\\M" + anio + codMes + "\\Temp_CC.dbf")

    #**************************
    # inicio bucle de datos iniciales -provincias
    
    arcpy.env.workspace = dirIni
    provt = arcpy.ListWorkspaces("PROV_*", "Folder")

    for prov in provt:
        codprov = prov[len(prov)-2:]

        arcpy.AddMessage( "****************************************************")  
        arcpy.AddMessage( "Preparo provincia: " + codprov + " el " + time.ctime())
        fictime.write('preparo provincia ' + codprov + ' el ' + time.ctime() + '\n')

        #chequeo provincias que se quieren procesar
        if codprov < provIni:
            arcpy.AddMessage ("Provincia ya hecha - No se prepara")
        else:
            arcpy.env.workspace = dirIni + "\\PROV_" + codprov

            #chequea que la provincia tenga algun shape con informacion
            cuentarec = 0
            shapet = arcpy.ListFeatureClasses()

            for shape in shapet:
                arcpy.AddMessage(shape)
                fictime.write(shape + '\n')
                arcpy.AddMessage(arcpy.GetCount_management(shape).getOutput(0))
                if int(arcpy.GetCount_management(shape).getOutput(0)) > 0:
                    cuentarec = cuentarec + int(arcpy.GetCount_management(shape).getOutput(0))
            arcpy.AddMessage("La provincia " + codprov + " tiene numero de recintos: " + str(cuentarec) )
            fictime.write('La provincia ' + codprov + ' tiene numero de recintos: ' + str(cuentarec) + '\n')

            #***********************************************
            # Inicia copiado y preparacion provincia con datos

            if cuentarec > 0:

                # preparo la carpeta de la provinci y copia (solo si tiene informacion) los shapes en datos_ori
                if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov):
                    arcpy.AddMessage ("Ya existe la provincia en datos_ori de este mes")
                else:
                    os.mkdir(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov)

                    shapet = arcpy.ListFeatureClasses()
                    for shape in shapet:
                        if int(arcpy.GetCount_management(shape).getOutput(0)) > 0:
                            arcpy.Copy_management(shape, dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\" + shape)

                # prepara la carpeta y gdb de la provincia en PROYE
                arcpy.env.workspace = dirPrin

                if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov):
                    arcpy.AddMessage ("Ya existe la provincia en PROYE de este mes")
                else:
                    os.mkdir("PROYE\\M" + anio + codMes + "\\prov" + codprov)

                    arcpy.Copy_management(dirSemg + "\\prov" + codprov + "\\prov" + codprov + ".gdb", "PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb" )

                # prepara la carpeta y gdb de la provincia en LIMPIA
                if arcpy.Exists(dirLimp + "\\M" + anio + codMes + "\\prov" + codprov):
                    arcpy.AddMessage ("Ya existe la provincia en LIMPIA de este mes")
                else:
                    os.mkdir(dirLimp + "\\M" + anio + codMes + "\\prov" + codprov)

    fictime.close()

#****************************************
# BLOQUE DE PROCESADO
#*************************************

if Procesa == "true":
    arcpy.AddMessage ("***************************************")
    arcpy.AddMessage("Ejecuto el bloque de PROCESADO (actualiza los rasters, genera fichero de cambios,...")
    arcpy.AddMessage("****************************************************************************")

    
    #abre el fichero de tiempos
    fictime = open(dirPrin + "\\PROYE\\M" + anio + codMes + "\log_timeF10.txt","a")
    fictime.write('*******************************\n')

    arcpy.AddMessage( "Inicio el MES: " + anio + codMes + " el " + time.ctime())
    fictime.write('Inicio el MES ' + anio + codMes + ' el ' + time.ctime() + '\n')

    fictime.close()

    # configura
    arcpy.env.workspace = dirPrin + "\\datos_ori\\M" + anio + codMes

    provt = arcpy.ListWorkspaces("prov*", "Folder")
    for prov in provt:
        codprov = prov[len(prov)-2:]

        fictime = open(dirPrin + "\\PROYE\\M" + anio + codMes + "\log_timeF10.txt","a")

        arcpy.AddMessage( "*********************************************************************")    
        arcpy.AddMessage( "Inicio procesado provincia: " + codprov + " el " + time.ctime())
        fictime.write('Inicio procesado provincia ' + codprov + ' el ' + time.ctime() + '\n')

        #chequeo provincias que se quieren procesar
        if codprov < provIni:
            arcpy.AddMessage ("Provincia ya hecha - No se procesa")
        else:
            
            #configuro entorno de trabajo
            prov_ras = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\glimite_" + codprov
            arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_ras).spatialReference #proyeccion

            arcpy.env.extent = prov_ras  # extension
            arcpy.env.snapRaster = prov_ras  # cuadra los raster
            arcpy.env.mask = prov_ras   # mascara
            arcpy.env.cellSize = prov_ras   #tama?o celda

            # configuro directorio de trabajo
            arcpy.env.workspace = dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb"
            dirTrab = dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb"

            #preparo fichero de cambios
            arcpy.MakeTableView_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\Temp_CC.dbf", "cc_lyr")   
            arcpy.SelectLayerByAttribute_management("cc_lyr", "NEW_SELECTION", "\"PROV\" = " + codprov)

            #*****************************
            # preparo el rasters de FINC si existe # se genera nuevo a partir del parametro
            #**************************************************************************************

            if Proinc == "true":
                arcpy.AddMessage("** Proceso bloque de Incendios " + time.ctime())
                fictime.write('Proceso bloque de Incendios ' + time.ctime() + '\n')
                cambiainc = 0
                
                if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\SupInc.shp"):
                    cambiainc = 0

                    #preparo el vectorial de cambios
                    shp_finc = dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\SupInc.shp"
                    shp_clip = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\limite_" + codprov
                    shp_incp = arcpy.Clip_analysis(shp_finc, shp_clip , "\\PROYE\\pf_inc", 0.001)
                    
                    if int(arcpy.GetCount_management(shp_incp).getOutput(0)) > 0:
                        arcpy.AddMessage("Hay recintos de cambios de incendios en la provincia ")
                        fictime.write('Hay recintos de cambios de incendios en la provincia ' + '\n')

                        shp_incpd = arcpy.Dissolve_management(shp_incp, "\\PROYE\\pf_inc1",["PROV", "MUN"], "", "SINGLE_PART","DISSOLVE_LINES")

                        arcpy.AddField_management("\\PROYE\\pf_inc1", "TIPO_INC", "TEXT", "","",3)
                        arcpy.AddField_management("\\PROYE\\pf_inc1", "MES_INC", "TEXT", "","",4)

                        arcpy.CalculateField_management("\\PROYE\\pf_inc1", "TIPO_INC","'INC'", "PYTHON")
                        arcpy.CalculateField_management("\\PROYE\\pf_inc1", "MES_INC","\"" + anio + codMes + "\"", "PYTHON")

                        #comparo con antiguo si existe
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov):
                            arcpy.AddMessage("hay capa de incendios de antes")
                            
                            shp_fincold = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov
                            arcpy.Union_analysis(["\\PROYE\\pf_inc1", shp_fincold],"\\PROYE\\pf_inc2", "", 0.001)
                            arcpy.MakeFeatureLayer_management("\\PROYE\\pf_inc2","pfinc_lyr")
                            arcpy.SelectLayerByAttribute_management("pfinc_lyr", "NEW_SELECTION", "PROV = 0 or PROV_1 = 0")
                            
                            if int(arcpy.GetCount_management("pfinc_lyr").getOutput(0)) > 0:
                                cambiainc = 1 # hay antiguo y nuevo
                                arcpy.AddMessage("Hay cambios en incendios- " + arcpy.GetCount_management("pfinc_lyr").getOutput(0))
                                
                                arcpy.FeatureClassToFeatureClass_conversion("pfinc_lyr", dirTrab + "\\PROYE", "cambia_inc")
                                
                                arcpy.AddMessage("Inicio grid GFINC ")
                                fictime.write('Inicio grid GFINC ' + '\n')
                                
                                arcpy.PolygonToRaster_conversion(shp_incp,"PROV","GFINC_REC","MAXIMUM_COMBINED_AREA","NONE",5) # 
             
                                gtemp1 = Con (IsNull("GFINC_REC"), 1, 0) # rellena nulos a 1 # 
                                gtemp1.save("GFINC_" + codprov) #
                                arcpy.BuildRasterAttributeTable_management("GFINC_" + codprov, "Overwrite")
 
                                #sustituyo en dirFin 
                                #if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov):
                                arcpy.AddMessage("Sustituyo en DirFin porque cambia")

                                #raster                      
                                arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov + "_M" + str(anio + codMes) )
                                arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov)
                            
                                arcpy.CopyRaster_management("GFINC_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov)

                                #vectorial
                                arcpy.Copy_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov + "_M" + str(anio + codMes) )
                                arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov)
                            
                                arcpy.Copy_management("\\PROYE\\pf_inc1", dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov)

                                # cargo en CAMBIOS_Mxx - en espana
                                arcpy.AddMessage("Cargo en CambiosInc")

                                if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp"):
                                    arcpy.Append_management(["\\PROYE\\cambia_inc"],dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp", "NO_TEST")
                                    arcpy.CalculateField_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp", "Shape_Area","!shape.Area!", "PYTHON")
                                else:
                                    arcpy.env.outputCoordinateSystem = arcpy.Describe(dirFin + "\\prov28\\prov28.gdb\\GLIMITE_28").spatialReference # proyecciopn obliga a huso30
                                    arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\cambia_inc",  dirPrin + "\\PROYE\\M" + anio + codMes, "CambiosInc_M" + anio + codMes + ".shp")
                                    arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_ras).spatialReference #proyeccion de la provincia
 
                                #relleno control_cambios
                                fec = strftime("%d/%m/%Y",gmtime())
                                arcpy.AddMessage(fec)
                                arcpy.CalculateField_management("cc_lyr","GFINC","\"" + fec + "\"","PYTHON")
                                arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")
                                
                            else:
                                arcpy.AddMessage("NO Hay cambios en incendios")

                        else:
                            arcpy.AddMessage("NO hay capa de incendios de antes")
                            cambiainc = 2 #solo hay nuevo
                            
                            arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\pf_inc1", dirTrab + "\\PROYE", "cambia_inc")
                            arcpy.AddField_management("\\PROYE\\pf_inc1", "TIPO_INC_1", "TEXT", "","",3)
                            arcpy.AddField_management("\\PROYE\\pf_inc1", "MES_INC_1", "TEXT", "","",4)

                            arcpy.AddMessage("Inicio grid GFINC ")
                            fictime.write('Inicio grid GFINC ' + '\n')
                            
                            arcpy.PolygonToRaster_conversion(shp_incp,"PROV","GFINC_REC","MAXIMUM_COMBINED_AREA","NONE",5) # 
             
                            gtemp1 = Con (IsNull("GFINC_REC"), 1, 0) # rellena nulos a 1 # 
                            gtemp1.save("GFINC_" + codprov) #
                            arcpy.BuildRasterAttributeTable_management("GFINC_" + codprov, "Overwrite")

                            #sustituyo en dirFin                            
                            arcpy.AddMessage("Meto en DirFin por primera vez")
                            
                            #raster
                            arcpy.CopyRaster_management("GFINC_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov)

                            #vectorial
                            arcpy.Copy_management("\\PROYE\\pf_inc1", dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\Incendios_" + codprov)
                            
                            # cargo en CAMBIOS_Mxx - en espana
                            arcpy.AddMessage("Cargo en CambiosInc")
                            
                            if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp"):
                                arcpy.Append_management(["\\PROYE\\cambia_inc"],dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp", "NO_TEST")
                                arcpy.CalculateField_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosInc_M" + anio + codMes + ".shp", "Shape_Area","!shape.Area!", "PYTHON")
                            else:
                                arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\cambia_inc",  dirPrin + "\\PROYE\\M" + anio + codMes, "CambiosInc_M" + anio + codMes + ".shp")

                            #relleno control_cambios
                            fec = strftime("%d/%m/%Y",gmtime())
                            arcpy.AddMessage(fec)
                            arcpy.CalculateField_management("cc_lyr","GFINC","\"" + fec + "\"","PYTHON")
                            arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                        #limpio
                        #if arcpy.Exists("GFINC_" + codprov):
                            #arcpy.Delete_management("GFINC_" + codprov)
                        if arcpy.Exists(dirTrab + "\\PROYE\\pf_inc"):
                            arcpy.Delete_management(dirTrab + "\\PROYE\\pf_inc")
                        if arcpy.Exists(dirTrab + "\\PROYE\\pf_inc1"):
                            arcpy.Delete_management(dirTrab + "\\PROYE\\pf_inc1")
                        if arcpy.Exists(dirTrab + "\\PROYE\\pf_inc2"):
                            arcpy.Delete_management(dirTrab + "\\PROYE\\pf_inc2")

                    else:
                        arcpy.AddMessage("No hay fichero de Incendios")

            #*****************************
            # preparo el rasters de FSUEP y FSUE, si existen cambios # CAMBIOS del parametro
            #**************************************************************************************

            if Prosue == "true":
                arcpy.AddMessage("** Proceso bloque de Suelo " + time.ctime())
                fictime.write('Proceso bloque de Suelo ' + time.ctime() + '\n')
                               
                if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\FactSue.shp"):
                    arcpy.AddMessage("Inicio grid GFSUEP y GFSUE "  )
                    fictime.write('Inicio grid GFSUEP y GFSUE ' + '\n')

                    shp_fsue = dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\FactSue.shp"
                    shp_suep = arcpy.FeatureClassToFeatureClass_conversion(shp_fsue,dirTrab + "\\PROYE","pf_sue" ) #aseguro proyeccion y extension 
                    if int(arcpy.GetCount_management(shp_suep).getOutput(0)) > 0:
                        arcpy.PolygonToRaster_conversion(shp_suep,"FACT_SUE","GFSUE_REC","MAXIMUM_COMBINED_AREA","",5)
                        
                        # meto en el antiguo del geoproceso
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\gfsuep_" + codprov):
                            arcpy.MosaicToNewRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\gfsuep_" + codprov + ";GFSUE_REC",dirTrab , "GFSUEP_" + codprov,"","","",1,"LAST")
                            arcpy.BuildRasterAttributeTable_management("GFSUEP_" + codprov, "Overwrite")
                        else:
                            arcpy.CopyRaster_management("GFSUE_REC", "GFSUEP_" + codprov)

                        # meto en el antiguo de suelo total
                        arcpy.MosaicToNewRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\gfsue_" + codprov + ";GFSUE_REC",dirTrab, "GFSUE_" + codprov,"","","",1,"LAST")
                        arcpy.BuildRasterAttributeTable_management("GFSUE_" + codprov, "Overwrite")

                        # sustituyo en dirFin
                        arcpy.AddMessage("Sustituyo en DirFin")
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUEP_" + codprov):
                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUEP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUEP_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUEP_" + codprov)
                        
                        arcpy.CopyRaster_management("GFSUEP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUEP_" + codprov)

                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov):
                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov)
                        
                        arcpy.CopyRaster_management("GFSUE_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov)

                        # cargo en CAMBIOS_Mxx - 
                        arcpy.AddMessage("Cargo en CambiosSue")
                        arcpy.Dissolve_management(shp_suep, "\\PROYE\\cambia_sue",["PROV", "MUN"], "", "SINGLE_PART","DISSOLVE_LINES")
        
                        arcpy.AddField_management("\\PROYE\\cambia_sue", "TIPO_SUE", "TEXT", "", "", 3)
                        arcpy.AddField_management("\\PROYE\\cambia_sue", "MES_SUE", "TEXT", "","", 4)
        
                        arcpy.CalculateField_management("\\PROYE\\cambia_sue", "TIPO_SUE","'SUE'", "PYTHON")
                        arcpy.CalculateField_management("\\PROYE\\cambia_sue", "MES_SUE","\"" + anio + codMes + "\"", "PYTHON")
        
                        if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosSue_M" + anio + codMes + ".shp"):
                            arcpy.Append_management(["\\PROYE\\cambia_sue"],dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosSue_M" + anio + codMes + ".shp", "NO_TEST")
                            arcpy.CalculateField_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosSue_M" + anio + codMes + ".shp", "Shape_Area","!shape.Area!", "PYTHON")
                        else:
                            arcpy.env.outputCoordinateSystem = arcpy.Describe(dirFin + "\\prov28\\prov28.gdb\\GLIMITE_28").spatialReference # proyecciopn obliga a huso30
                            arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\cambia_sue",  dirPrin + "\\PROYE\\M" + anio + codMes, "CambiosSue_M" + anio + codMes + ".shp")
                            arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_ras).spatialReference #proyeccion de la provincia

                        #relleno control_cambios
                        fec = strftime("%d/%m/%Y",gmtime())
                        arcpy.AddMessage(fec)
                        arcpy.CalculateField_management("cc_lyr","GFSUEP","\"" + fec + "\"","PYTHON")
                        arcpy.CalculateField_management("cc_lyr","GFSUE","\"" + fec + "\"","PYTHON")
                        arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                        # sustituyo en historicos
                        arcpy.AddMessage("Sustituyo en Históricos de Beato")
                        if arcpy.Exists(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov):
                            arcpy.CopyRaster_management(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov, dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov)
                        
                        arcpy.CopyRaster_management("GFSUE_" + codprov, dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov)

                        #limpio
                        #if arcpy.Exists("GFSUEP_" + codprov):
                        #    arcpy.Delete_management("GFSUEP_" + codprov)
                        #if arcpy.Exists("GFSUE_" + codprov):
                        #    arcpy.Delete_management("GFSUE_" + codprov)
                            
                        if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\pf_sue"):
                            arcpy.Delete_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\pf_sue")

                else:
                    arcpy.AddMessage("No hay fichero de cambios de Suelo")

            #*****************************
            # preparo el rasters de VEGP y VEG, si existen cambios # CAMBIOS del parametro
            #**************************************************************************************
            cambiaveg = 0
          
            if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\TipoVeg.shp"):
                arcpy.AddMessage("Inicio para ver si cambia la Vegetacion a las "  + time.ctime())
                fictime.write('Inicio para ver si cambia la Vegetacion a las' + time.ctime() + '\n')
                
                if arcpy.Exists("GVEG_" + codprov):
                    arcpy.AddMessage("Ya se ha procesado y existe GVEG con cambioa")
                    cambiaveg = 1
                else:
       
                    shp_tveg = dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\TipoVeg.shp"
                    shp_vegp = arcpy.FeatureClassToFeatureClass_conversion(shp_tveg,dirTrab + "\\PROYE","pf_veg" ) #aseguro proyeccion y extension

                    arcpy.MakeFeatureLayer_management(shp_vegp,"lyrVeg")
                    arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_SUE\" <> 1 or \"C_MAT\" <> 2 or \"C_ARB\" <> 3 or \"C_EDI\" <> 4 or \"C_AGU\" <> 5") # hace solo si viene algún cambio
                    arcpy.AddMessage("Recintos con cambios en vege: " + arcpy.GetCount_management("lyrVeg").getOutput(0))
                    if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                                                    
                        #genero los 5 rasters de cambio tipo de vegetacion a partir del shape
                        # sue
                        arcpy.AddMessage("veg_suelo")
                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_SUE\" >= 0 and \"C_SUE\" <> 1 ")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrVeg").getOutput(0))
                        if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrVeg", "C_SUE", "GVegSU", "MAXIMUM_COMBINED_AREA","NONE",5)

                        # mat
                        arcpy.AddMessage("veg_matorral")
                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_MAT\" >= 0 and \"C_MAT\" <> 2")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrVeg").getOutput(0))
                        if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrVeg", "C_MAT", "GVegMA", "MAXIMUM_COMBINED_AREA","NONE",5)

                        # arbolado
                        arcpy.AddMessage("veg_arbolado")
                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_ARB\" >= 0 and \"C_ARB\" <> 3")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrVeg").getOutput(0))
                        if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrVeg", "C_ARB" , "GVegAR", "MAXIMUM_COMBINED_AREA","NONE",5)
                            
                        # edificacion
                        arcpy.AddMessage("veg_edificacion")
                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_EDI\" >= 0 and \"C_EDI\" <> 4")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrVeg").getOutput(0))
                        if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrVeg", "C_EDI", "GVegED", "MAXIMUM_COMBINED_AREA","NONE",5)

                        # agua
                        arcpy.AddMessage("veg_agua")
                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_AGU\" >= 0 and \"C_AGU\" <> 5")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrVeg").getOutput(0))
                        if int(arcpy.GetCount_management("lyrVeg").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrVeg", "C_AGU", "GVegAG", "MAXIMUM_COMBINED_AREA","NONE",5)

                        arcpy.SelectLayerByAttribute_management("lyrVeg" , "CLEAR_SELECTION", "")

                        # genero la nueva vegetacion zona de cambios
                        arcpy.AddMessage("Inicio calculo de los cambios en Vege ")

                        arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov, "GVEG_OLD")
                        arcpy.BuildRasterAttributeTable_management("GVEG_OLD", "Overwrite")
                        ras2 = Raster("GVEG_OLD")
                        
                        entrada = ""
                        #suelo
                        arcpy.AddMessage("suelo")
                        if arcpy.Exists("GVegSU"):
                            ras1 = Raster("GVegSU")
                            gtemp1 = Con(((ras1 > 0) & (ras2 == 1)),ras1)
                            gtemp1.save("gtemp_vegsue")

                            #chequeo que tenga valores y si tiene añado para el mosaico
                            arcpy.BuildRasterAttributeTable_management("gtemp_vegsue", "Overwrite")
                            grdmean = arcpy.GetRasterProperties_management("gtemp_vegsue", "UNIQUEVALUECOUNT")
                            vacio = grdmean.getOutput(0)
                            if int(vacio) > 0: #== 0:
                                arcpy.AddMessage("Cambia suelo")
                                entrada = ";gtemp_vegsue"

                        #matorral
                        arcpy.AddMessage("matorral")
                        if arcpy.Exists("GVegMA"):
                            ras1 = Raster("GVegMA")
                            gtemp2 = Con(((ras1 > 0) & (ras2 == 2)),ras1)
                            gtemp2.save("gtemp_vegmat")

                            #chequeo que tenga valores y si tiene añado para el mosaico
                            arcpy.BuildRasterAttributeTable_management("gtemp_vegmat", "Overwrite")
                            grdmean = arcpy.GetRasterProperties_management("gtemp_vegmat", "UNIQUEVALUECOUNT")
                            vacio = grdmean.getOutput(0)
                            if int(vacio) > 0: #== 0:
                                arcpy.AddMessage("Cambia matorral")
                                entrada = entrada + ";gtemp_vegmat" 

                        #arbolado
                        arcpy.AddMessage("arbolado")
                        if arcpy.Exists("GVegAR"):
                            ras1 = Raster("GVegAR")
                            gtemp3 = Con(((ras1 > 0) & (ras2 == 3)),ras1)
                            gtemp3.save("gtemp_vegarb")

                            #chequeo que tenga valores y si tiene añado para el mosaico
                            arcpy.BuildRasterAttributeTable_management("gtemp_vegarb", "Overwrite")
                            grdmean = arcpy.GetRasterProperties_management("gtemp_vegarb", "UNIQUEVALUECOUNT")
                            vacio = grdmean.getOutput(0)
                            if int(vacio) > 0: #== 0:
                                arcpy.AddMessage("Cambia arbolado")
                                entrada = entrada + ";gtemp_vegarb" 

                        #edificacion
                        arcpy.AddMessage("edificacion")
                        if arcpy.Exists("GVegED"):
                            ras1 = Raster("GVegED")
                            gtemp4 = Con(((ras1 > 0) & (ras2 == 4)),ras1)
                            gtemp4.save("gtemp_vegedi")

                            #chequeo que tenga valores y si tiene añado para el mosaico
                            arcpy.BuildRasterAttributeTable_management("gtemp_vegedi", "Overwrite")
                            grdmean = arcpy.GetRasterProperties_management("gtemp_vegedi", "UNIQUEVALUECOUNT")
                            vacio = grdmean.getOutput(0)
                            if int(vacio) > 0: #== 0:
                                arcpy.AddMessage("cambia edificacion")
                                entrada = entrada + ";gtemp_vegedi" 

                        #agua
                        arcpy.AddMessage("agua")
                        if arcpy.Exists("GVegAG"):
                            ras1 = Raster("GVegAG")
                            gtemp5 = Con(((ras1 > 0) & (ras2 == 5)), ras1)
                            gtemp5.save("gtemp_vegagu")

                            #chequeo que tenga valores y si tiene añado para el mosaico
                            arcpy.BuildRasterAttributeTable_management("gtemp_vegagu", "Overwrite")
                            grdmean = arcpy.GetRasterProperties_management("gtemp_vegagu", "UNIQUEVALUECOUNT")
                            vacio = grdmean.getOutput(0)
                            if int(vacio) > 0: #== 0:
                                arcpy.AddMessage("cambia agua")
                                entrada = entrada + ";gtemp_vegagu" 
                        
                        #uno los 5 en - GVEG_REC, GVEGP_xx, GVEG_xx 
                        if entrada <> "":  # CAMBIA la VEG
                            arcpy.AddMessage("Cambia la vegetacion")
                            cambiaveg = 1 
                            entrada = entrada[1:]    
                            arcpy.AddMessage(entrada)
                            fictime.write(entrada + '\n')

                            if Proveg == "true":
                                arcpy.AddMessage("** Proceso bloque de Vegetación " + time.ctime())
                                fictime.write('Proceso bloque de Vegetación ' + time.ctime() + '\n')

                                arcpy.AddMessage("GVEG_REC")
                                arcpy.MosaicToNewRaster_management(entrada,dirTrab,"GVEG_REC", "","", "", "1", "FIRST")
                                arcpy.BuildRasterAttributeTable_management("GVEG_REC", "Overwrite")

                                arcpy.AddMessage("GVEGP")
                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov):
                                    ras3 = Raster(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov)
                                    gtemp = Con(IsNull("GVEG_REC"),ras3,"GVEG_REC")
                                    gtemp.save("GVEGP_" + codprov)
                                    arcpy.BuildRasterAttributeTable_management("GVEGP_" + codprov, "Overwrite")
                                else:
                                    arcpy.MosaicToNewRaster_management(entrada, dirTrab,"GVEGP_" + codprov, "","", "", "1", "FIRST")
                                    arcpy.BuildRasterAttributeTable_management("GVEGP_" + codprov, "Overwrite")

                                arcpy.AddMessage("GVEG")
                                gtemp = Con(IsNull("GVEG_REC"),"GVEG_OLD","GVEG_REC")
                                gtemp.save("GVEG_" + codprov)
                                arcpy.BuildRasterAttributeTable_management("GVEG_" + codprov, "Overwrite")
                  
                                # sustituyo en dirFin
                                arcpy.AddMessage("Sustituyo en DirFin")
                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov):
                                    arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov + "_M" + str(anio + codMes) )
                                    arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov)
                                
                                arcpy.CopyRaster_management("GVEGP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGP_" + codprov)

                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov):
                                    arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov + "_M" + str(anio + codMes) )
                                    arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov)
                                
                                arcpy.CopyRaster_management("GVEG_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov)

                                # cargo en CAMBIOS_Mxx - 
                                arcpy.AddMessage("Cargo en CambiosVeg")
                                arcpy.SelectLayerByAttribute_management("lyrVeg" , "NEW_SELECTION", "\"C_SUE\" <> 1 or \"C_MAT\" <> 2 or \"C_ARB\" <> 3 or \"C_EDI\" <> 4 or \"C_AGU\" <> 5") # hace solo si viene algún cambio
                                arcpy.Dissolve_management("lyrVeg", "\\PROYE\\cambia_veg",["PROV", "MUN"], "", "SINGLE_PART","DISSOLVE_LINES")
                
                                arcpy.AddField_management("\\PROYE\\cambia_veg", "TIPO_VEG", "TEXT", "","", 3)
                                arcpy.AddField_management("\\PROYE\\cambia_veg", "MES_VEG", "TEXT", "","", 4)
                
                                arcpy.CalculateField_management("\\PROYE\\cambia_veg", "TIPO_VEG","'VEG'", "PYTHON")
                                arcpy.CalculateField_management("\\PROYE\\cambia_veg", "MES_VEG","\"" + anio + codMes + "\"", "PYTHON")
                
                                if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosVeg_M" + anio + codMes + ".shp"):
                                    arcpy.Append_management(["\\PROYE\\cambia_veg"],dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosVeg_M" + anio + codMes + ".shp", "NO_TEST")
                                    arcpy.CalculateField_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosVeg_M" + anio + codMes + ".shp", "Shape_Area","!shape.Area!", "PYTHON")
                                else:
                                    arcpy.env.outputCoordinateSystem = arcpy.Describe(dirFin + "\\prov28\\prov28.gdb\\GLIMITE_28").spatialReference # proyecciopn obliga a huso30
                                    arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\cambia_veg",  dirPrin + "\\PROYE\\M" + anio + codMes, "CambiosVeg_M" + anio + codMes + ".shp")
                                    arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_ras).spatialReference #proyeccion de la provincia

                                #relleno control_cambios
                                fec = strftime("%d/%m/%Y",gmtime())
                                arcpy.AddMessage(fec)
                                arcpy.CalculateField_management("cc_lyr","GVEGP","\"" + fec + "\"","PYTHON")
                                arcpy.CalculateField_management("cc_lyr","GVEG","\"" + fec + "\"","PYTHON")
                                arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                                # sustituyo en historicos de Beato
                                arcpy.AddMessage("Sustituyo en Históricos de Beato")
                                if arcpy.Exists(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov):
                                    arcpy.CopyRaster_management(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov, dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov + "_M" + str(anio + codMes) )
                                    arcpy.Delete_management(dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov)
                                
                                arcpy.CopyRaster_management("GVEG_" + codprov, dirHist + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov)

                            #limpio
                            if arcpy.Exists("gtemp_vegarb"):
                                arcpy.Delete_management("gtemp_vegarb")
                            if arcpy.Exists("gtemp_vegmat"):
                                arcpy.Delete_management("gtemp_vegmat")
                            if arcpy.Exists("gtemp_vegsue"):
                                arcpy.Delete_management("gtemp_vegsue")
                            if arcpy.Exists("gtemp_vegedi"):
                                arcpy.Delete_management("gtemp_vegedi")
                            if arcpy.Exists("gtemp_vegagu"):
                                arcpy.Delete_management("gtemp_vegagu")

                            #*****************************
                            # preparo el rasters de GVEGF y GFVEG, si existen cambios # CAMBIOS del parametro
                            #**************************************************************************************

                            if Provegfil == "true":
                                arcpy.AddMessage("** Proceso bloque de Filtro de vegetacion " + time.ctime())
                                fictime.write('Proceso bloque de Filtro de vegetación ' + time.ctime() + '\n')

                                arcpy.AddMessage("Inicio grid GVEGF y GFVEG ")
                                fictime.write('Inicio grid GVEGF y GFVEG ' + '\n')

                                if codprov in ['01', '20', '48']:
                                    arcpy.AddMessage("soy Pais Vasco - NO filtro")

                                    #genero GVEGF
                                    arcpy.AddMessage("genero GVEGF")
                                    arcpy.CopyRaster_management("GVEG_" + codprov,"GVEGF_" + codprov)

                                    #calculo factor vegetacion 
                                    arcpy.AddMessage("calculo GFVEG") 
                                    gtemp = Reclassify("GVEG_" + codprov, "Value",RemapValue([[1,100],[2,0],[3,0],[4,0],[5,0]])) 
                                    gtemp.save("GFVEG_" + codprov) 

                                else:
                                    arcpy.AddMessage("NO soy Pais Vasco - SI filtro")
                                    #saco suelo
                                    arcpy.AddMessage( "Saco suelo ")
                                    gtemp = Reclassify("GVEG_" + codprov, "Value",RemapValue([[1,1],[2,0],[3,0],[4,0],[5,0]]))
                                    gtemp.save("Suelo_temp") # gtemp.save("gvgf2_suelo") 

                                    # miro los lados - suelo aislado irregular # no funciona en ArcGis 10.2.2
                                    gtemp = FocalStatistics("Suelo_temp", NbrIrregular(FFiltros),"SUM", "DATA") 
                                    gtemp.save("FStSue") 

                                    # preparo matorral
                                    arcpy.AddMessage( "Preparo matorral ")
                                    gtemp = Reclassify("GVEG_" + codprov, "Value",RemapValue([[1,0],[2,1],[3,0],[4,0],[5,0]]))
                                    gtemp.save("Mat_temp") 

                                    # miro los lados - matorral aislado irregular # no funciona en ArcGis 10.2.2
                                    gtemp = FocalStatistics("Mat_temp", NbrIrregular(FFiltros),"SUM", "DATA") 
                                    gtemp.save("FStMat") 

                                    # combino los raster de filtros y el inicial
                                    arcpy.AddMessage( "Combine y clasificacion ")
                                    gtemp = Combine(["GVEG_" + codprov, "FStSue", "FStMat"]) #cambia 01022023
                                    gtemp.save("gvgf2_arb2")

                                    arcpy.AddField_management("gvgf2_arb2", "gveg_rec", "SHORT")
                                    arcpy.AddField_management("gvgf2_arb2", "Fveg", "SHORT")

                                    arcpy.MakeRasterLayer_management("gvgf2_arb2", "lyrarb", "#", "", "1")
                                    arcpy.CalculateField_management("lyrarb" ,"gveg_rec","!GVEG_" + codprov + "!", "PYTHON")
                                    
                                    arcpy.SelectLayerByAttribute_management("lyrarb" , "NEW_SELECTION", "\"GVEG_" + codprov + " \" = 1")
                                    if int(arcpy.GetCount_management("lyrarb").getOutput(0)) > 0:
                                        arcpy.CalculateField_management("lyrarb" ,"Fveg",'100', "PYTHON")
                                        
                                    arcpy.SelectLayerByAttribute_management("lyrarb" , "NEW_SELECTION", "\"GVEG_" + codprov + "\" <> 1")
                                    if int(arcpy.GetCount_management("lyrarb").getOutput(0)) > 0:
                                        arcpy.CalculateField_management("lyrarb" ,"Fveg",'0', "PYTHON")

                                    # arbolado de borde que no contacte con matorra y si con suelo - 31
                                    arcpy.SelectLayerByAttribute_management("lyrarb" , "NEW_SELECTION", "\"FStSue\" <> 0 AND \"FStMat\" = 0 AND \"GVEG_" + codprov + "\" = 3") 
                                    if int(arcpy.GetCount_management("lyrarb").getOutput(0)) > 0:
                                        arcpy.CalculateField_management("lyrarb" ,"gveg_rec",'31', "PYTHON")
                                        arcpy.CalculateField_management("lyrarb" ,"Fveg",'50', "PYTHON")

                                    arcpy.SelectLayerByAttribute_management("lyrarb" , "CLEAR_SELECTION", "")

                                    gtemp = Lookup("lyrarb","gveg_rec")
                                    gtemp.save("GVEGF_" + codprov)

                                    gtemp = Lookup("lyrarb","Fveg")
                                    gtemp.save("GFVEG_" + codprov)

                                    #limpio
                                    del gtemp
                                    if arcpy.Exists("gvgf2_arb2"):
                                        arcpy.Delete_management("gvgf2_arb2")

                                # sustituyo en dirFin
                                arcpy.AddMessage("Sustituyo en DirFin")
                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGF_" + codprov):
                                    arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGF_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGF_" + codprov + "_M" + str(anio + codMes) )
                                    arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGF_" + codprov)
                                
                                arcpy.CopyRaster_management("GVEGF_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEGF_" + codprov)

                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov):
                                    arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov + "_M" + str(anio + codMes) )
                                    arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov)
                                
                                arcpy.CopyRaster_management("GFVEG_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov)

                                #relleno control_cambios
                                fec = strftime("%d/%m/%Y",gmtime())
                                arcpy.AddMessage(fec)
                                arcpy.CalculateField_management("cc_lyr","GVEGF","\"" + fec + "\"","PYTHON")
                                arcpy.CalculateField_management("cc_lyr","GFVEG","\"" + fec + "\"","PYTHON")
                                arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                            #*****************************
                            # preparo el rasters de GDEH y GFESPDE, si existen dehesas y cambios en vegetacion # CAMBIOS del parametro
                            #**************************************************************************************

                            if Prodeh == "true":
                                arcpy.AddMessage("** Proceso bloque de Dehesa " + time.ctime())
                                fictime.write('Proceso bloque de Dehesa ' + time.ctime() + '\n')

                                if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\dehesa_" + codprov):
                                    arcpy.AddMessage("Inicio grid GDEH y GFESPDE ")
                                    fictime.write('Inicio grid GDEH y GFESPDE ' + '\n')

                                    # miro si intersecta con los cambios de vegetacion
                                    arcpy.MakeFeatureLayer_management("\\PROYE\\cambia_veg", "dehp_lyr")
                                    shp_dehp = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\dehesa_" + codprov
                                    shp_dehp2 = arcpy.SelectLayerByLocation_management ("dehp_lyr", "INTERSECT", shp_dehp,"60 Meters", "NEW_SELECTION")

                                    if int(arcpy.GetCount_management(shp_dehp2).getOutput(0)) > 0:
                                        arcpy.AddMessage("La dehesa intersecta con la nueva vegetacion ")
         
                                        #dehesa
                                        arcpy.AddMessage("genero dehesa de zona con cambio vege")
                                        temp_deh = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov
                                        gtemp_deh = Con(IsNull(Raster(temp_deh)),0,1)
                                        gtemp_deh.save("Dehe_temp")
                                        arcpy.BuildRasterAttributeTable_management("Dehe_temp", "Overwrite")
                                    
                                        # arbolado
                                        arcpy.AddMessage("genero clasi inicial arbolado")
                                        if arcpy.Exists("Arb_temp"):
                                            arcpy.AddMessage("ya existe")
                                        else:
                                            gtemp_arb = Con("GVEG_" + codprov, "1", "0", "VALUE = 3")
                                            gtemp_arb.save("Arb_temp")

                                        # Excepcion extremadura, madrid, andalucia - pixeles de arbolado en dehesa F= 100. No analiza zonas borde de dehesa
                                        #**********
                                        if codprov in ['06', '10', '28', '04', '11', '14', '18', '21', '23', '29', '41' ]:
                                            arcpy.AddMessage("Soy Extremadura, Madrid o Andalucia - arbolado todo a 100 en dehesas")
                                            
                                            #combinamos las capas necesarias
                                            gtemp = Combine(["Arb_temp", "Dehe_temp", "GVEG_" + codprov])
                                            gtemp.save("Combine_tmp6")

                                            arcpy.AddField_management("Combine_tmp6", "VegFin", "SHORT")
                                            arcpy.AddField_management("Combine_tmp6", "Fveg", "SHORT")

                                            arcpy.CalculateField_management("Combine_tmp6" ,"VegFin",'0', "PYTHON")
                                            arcpy.CalculateField_management("Combine_tmp6" ,"FVeg",'-1', "PYTHON")

                                            arcpy.MakeRasterLayer_management("Combine_tmp6", "lyrcomb6")
                                 
                                            # pixeles arbolado en dehesa - 34
                                            arcpy.AddMessage("34")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "NEW_SELECTION", "\"Arb_temp\" = 1 and \"Dehe_temp\" = 1")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'34', "PYTHON")
                                                arcpy.CalculateField_management("lyrcomb6" ,"FVeg",'100', "PYTHON") 
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION","") 

                                            # resto
                                            arcpy.AddMessage("resto")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "NEW_SELECTION", "\"Arb_temp\" = 0 and \"Dehe_temp\" = 1")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'!GVEG_' + codprov + '!', "PYTHON")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION", "")
                                            
                                            #  calculamos rasteres finales
                                            arcpy.AddMessage("saco rasters")
                                            gtemp = Lookup("Combine_tmp6","VegFin")
                                            gtemp1 = Con(gtemp,gtemp,"","Value > 0")
                                            gtemp1.save("GDEH_" + codprov )

                                            gtemp = Lookup("Combine_tmp6","FVeg")
                                            gtemp1 =Con(gtemp,gtemp,"","Value >= 0")
                                            gtemp1.save("GFESPDE_" + codprov)

                                            #limpio
                                            if arcpy.Exists("Combine_tmp6"):
                                                arcpy.Delete_management("Combine_tmp6")

                                        # Resto PROVINCIAS dehesas CM y CL - Analiza tanmaño y zonas de borde de la DEHESA
                                        #**********
                                        else:
                                            arcpy.AddMessage("Soy CasMan o CasLeon - analizo tamaño y borde de la dehesa")
                                                                               
                                            #genero mascaras de zonas que cambian
                                            arcpy.Buffer_analysis("dehp_lyr", "\\PROYE\\cambia_veg_b100", "100 Meters", "","","ALL")
                                            arcpy.PolygonToRaster_conversion("\\PROYE\\cambia_veg_b100", "OBJECTID", "gcambia_veg_b100", "MAXIMUM_COMBINED_AREA","NONE",5)

                                            arcpy.Buffer_analysis("dehp_lyr", "\\PROYE\\cambia_veg_b200", "200 Meters", "","","ALL")
                                            arcpy.PolygonToRaster_conversion("\\PROYE\\cambia_veg_b200", "OBJECTID", "gcambia_veg_b200", "MAXIMUM_COMBINED_AREA","NONE",5)
                                            arcpy.env.mask = "gcambia_veg_b200"  # mascara
                                                                        
                                            # matorral
                                            if arcpy.Exists("Mat_temp"): 
                                                arcpy.AddMessage ("ya existe")
                                            else:
                                                gtemp_mat = Con("GVEG_" + codprov, "1", "0", "VALUE = 2")
                                                gtemp_mat.save("Mat_temp")

                                            # suelo
                                            if arcpy.Exists("Suelo_temp"): 
                                                arcpy.AddMessage ("ya existe")
                                            else:
                                                gtemp_sue = Con("GVEG_" + codprov, "1", "0", "VALUE = 1")
                                                gtemp_sue.save("Suelo_temp")
                                            
                                            # Analisis de regiones con 1 pixel de arbolado - no entran en filtro de dehesa - menores de 500m 
                                            arcpy.AddMessage ("Dehesa- Analisis de regiones con 1 pixel de arbolado ")
                                            
                                            if arcpy.Exists("FStMat"): 
                                                arcpy.AddMessage ("ya existe")
                                            else:
                                                gtemp = FocalStatistics("Mat_temp", NbrIrregular(FFiltros),"SUM")
                                                gtemp.save("FStMat")

                                            if arcpy.Exists("FStSue"): 
                                                arcpy.AddMessage ("ya existe")
                                            else:
                                                gtemp = FocalStatistics("Suelo_temp", NbrIrregular(FFiltros),"SUM", "DATA")
                                                gtemp.save("FStSue")

                                            if arcpy.Exists("FStArb"): #cambia 01022023
                                                arcpy.AddMessage ("ya existe")
                                            else:
                                                gtemp = FocalStatistics("Arb_temp", NbrIrregular(FFiltros),"SUM", "DATA")
                                                gtemp.save("FStArb")

                                            gtemp = Combine(["Arb_temp", "FStArb"])
                                            gtemp.save("Combine_tmp1")

                                            gtemp = Con("Combine_tmp1",1,0, "\"Arb_temp\" = 1 AND \"FStArb\" = 1")
                                            gtemp.save("Arb_aislado") #pixeles aislados de arbolado !!
                                            gtemp = Con("Combine_tmp1",1,0,"\"Arb_temp\" = 1 AND \"FStArb\" > 1")
                                            gtemp.save("Arb_tmp1") #arbolado con sp mayor a 1 pixel
                                           
                                            # Analisis de arbolado no aislado y MENOR de 500m2  #cambia 01022023
                                            arcpy.AddMessage ("Dehesa- Analisis de arbolado no aislado y de menos de 500m2 ") 
                      
                                            gtemp = RegionGroup("Arb_tmp1", "FOUR", "WITHIN") 
                                            gtemp2 = Con (gtemp,"1","0", "\"LINK\" = 1 AND \"Count\" <= 20") 
                                            gtemp2.save("Arb_tmp2") 
                   
                                            # Analisis de arbolado no aislado y MENOS de 500m2 que NO contacta con matorral) #cambia 01022023
                                            arcpy.AddMessage ("Dehesa- Analisis de arbolado no aislado y de menos de 500m2 que NO contacta con matorral " ) 

                                            gtemp = RegionGroup("Arb_tmp2", "FOUR", "WITHIN") 
                                            gtemp.save("RegionT") 
                                            gtemp2 = Combine(["RegionT", "FStMat"])
                                            
                                            #saco los que contactan
                                            gtemp3 = arcpy.Frequency_analysis(gtemp2, "ArbMat_frq", "RegionT", "FStMat")
                                            arcpy.JoinField_management ("RegionT", "Value", gtemp3, "regionT")

                                            #saco los que no contactan
                                            gtemp = Con("RegionT","1","0", "\"LINK\" = 1 AND \"FStMat\" = 0")
                                            gtemp.save("Arb_tmp3")

                                            # Calculamos arbolado no aislado menor de 500m2 que no toca matorral en dehesa #cambia 01022023
                                            arcpy.AddMessage ("Dehesa- Calculamos arbolado no aislado menor de 500m2 que no toca matorral en dehesa " ) 
                                            
                                            gtemp = RegionGroup("Arb_tmp3", "FOUR", "WITHIN")
                                            gtemp.save("RegionG_Arb")
                                            gtemp2 = Combine(["RegionG_Arb", "Dehe_temp"])

                                            #saco celdas en dehesa
                                            arcpy.MakeTableView_management(gtemp2, "lyrComb")
                                            arcpy.SelectLayerByAttribute_management("lyrComb" , "NEW_SELECTION", "\"Dehe_temp\" = 1")
                                            arcpy.CopyRows_management("lyrComb", "Superf_dehesas")
                                            arcpy.AddField_management("Superf_dehesas", "CountDehesas", "DOUBLE") 
                                            arcpy.CalculateField_management("Superf_dehesas", "CountDehesas","!Count!", "PYTHON")
                                            arcpy.DeleteField_management("Superf_dehesas", "Count") 
                                                                       
                                            arcpy.JoinField_management ("RegionG_Arb", "Value", "Superf_dehesas", "RegionG_Arb")

                                            #calculo porcentaje
                                            arcpy.AddField_management("RegionG_Arb", "PorcenDehesas", "SHORT")
                                            arcpy.CalculateField_management("RegionG_Arb", "PorcenDehesas",'0', "PYTHON")

                                            arcpy.CalculateField_management("RegionG_Arb", "PorcenDehesas","(!CountDehesas! * 100)/ !Count!", "PYTHON")

                                            #saco lo que estan >50 en dehesa
                                            gtemp = Con("RegionG_Arb","34","0", "\"LINK\" = 1 AND \"PorcenDehesas\" > 50")
                                            gtemp.save("Arb_tmp4")
                                            
                                            # Calculamos raster final de dehesa y fespde
                                            arcpy.AddMessage ("Dehesa- Calculamos raster final de dehesa y fespde " )
                                            
                                            gtemp = Combine(["Arb_tmp4", "FStMat", "FStSue", "Dehe_temp", "GVEG_" + codprov, "Arb_aislado"])
                                            gtemp.save("Combine_tmp6")

                                            arcpy.AddField_management("Combine_tmp6", "VegFin", "SHORT")
                                            
                                            arcpy.CalculateField_management("Combine_tmp6" ,"VegFin",'0', "PYTHON")
                                            
                                            arcpy.MakeRasterLayer_management("Combine_tmp6", "lyrcomb6")
                                          
                                            arcpy.AddMessage("32")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "NEW_SELECTION", "\"Arb_tmp4\" = 34")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'32', "PYTHON")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION", "")

                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" ,"NEW_SELECTION", "\"VegFin\" = 0 and \"Arb_aislado\" = 1 and \"Dehe_temp\" = 1 and \"FStMat\" = 0 and \"FStSue\" >= 1")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'32', "PYTHON")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION", "")

                                            arcpy.AddMessage("33")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "NEW_SELECTION", "\"VegFin\" = 0 and \"GVEG_" + codprov + "\" = 3 and \"Dehe_temp\" = 1")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'33', "PYTHON")                                        
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION", "")

                                            arcpy.AddMessage("resto")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "NEW_SELECTION", "\"VegFin\" = 0  and \"Dehe_temp\" = 1")
                                            if int(arcpy.GetCount_management("lyrcomb6").getOutput(0)) > 0:
                                                arcpy.CalculateField_management("lyrcomb6" ,"VegFin",'!GVEG_' + codprov + '!', "PYTHON")
                                            arcpy.SelectLayerByAttribute_management("lyrcomb6" , "CLEAR_SELECTION", "")

                                            #calculamos rasteres finales                                    
                                            arcpy.AddMessage("dehesa-saco rasters")

                                            arcpy.env.mask = "gcambia_veg_b100"  # mascara para evitar efecto de borde
                                            
                                            gtemp = Lookup("Combine_tmp6","VegFin")
                                            gtemp_deh =Con(gtemp,gtemp,"","Value > 0")
                                            gtemp_deh.save("gtemp_deh" )

                                            # metemos cambios en las provinciales
                                            arcpy.env.mask = prov_ras   # mascara

                                            gtemp =Con(IsNull(gtemp_deh),Raster(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov), gtemp_deh)
                                            gtemp.save("GDEH_" + codprov  )

                                            gtemp = Reclassify("GDEH_" + codprov, "Value", RemapValue([[32,100],[33, 50]]),"NODATA")
                                            gtemp.save("GFESPDE_" + codprov)

                                        #limpiamos
                                        if arcpy.Exists("Arb_temp"):
                                                    arcpy.Delete_management("Arb_temp")
                                        if arcpy.Exists("Arb_aislado"):
                                                    arcpy.Delete_management("Arb_aislado")
                                        if arcpy.Exists("Arb_tmp1"):
                                                    arcpy.Delete_management("Arb_tmp1")
                                        if arcpy.Exists("Arb_tmp2"):
                                                    arcpy.Delete_management("Arb_tmp2")
                                        if arcpy.Exists("Arb_tmp3"):
                                                    arcpy.Delete_management("Arb_tmp3")
                                        if arcpy.Exists("Arb_tmp4"):
                                                    arcpy.Delete_management("Arb_tmp4")
                                        if arcpy.Exists("ArbMat_frq"):
                                                    arcpy.Delete_management("ArbMat_frq")
                                        if arcpy.Exists("Combine_tmp1"):
                                                    arcpy.Delete_management("Combine_tmp1")
                                        if arcpy.Exists("Combine_tmp5"):
                                                    arcpy.Delete_management("Combine_tmp5")
                                        #if arcpy.Exists("Combine_tmp6"):
                                                    #arcpy.Delete_management("Combine_tmp6")
                                        if arcpy.Exists("Dehe_temp"):
                                                    arcpy.Delete_management("Dehe_temp")
                                        if arcpy.Exists("FStArb"):
                                                    arcpy.Delete_management("FStArb")

                                        if arcpy.Exists("RegionG_Arb"):
                                                    arcpy.Delete_management("RegionG_Arb")
                                        if arcpy.Exists("RegionT"):
                                                    arcpy.Delete_management("RegionT")
                                          
                                        if arcpy.Exists("Superf_dehesas"):
                                                    arcpy.Delete_management("Superf_dehesas")

                                        # sustituyo en dirFin
                                        arcpy.AddMessage("Sustituyo en DirFin")
                                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov):
                                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov + "_M" + str(anio + codMes) )
                                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov)
                                        
                                        arcpy.CopyRaster_management("GDEH_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GDEH_" + codprov)

                                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov):
                                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov + "_M" + str(anio + codMes) )
                                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov)
                                        
                                        arcpy.CopyRaster_management("GFESPDE_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov)                  
                                                                            #relleno control_cambios
                                        fec = strftime("%d/%m/%Y",gmtime())
                                        arcpy.AddMessage(fec)
                                        arcpy.CalculateField_management("cc_lyr","GDEH","\"" + fec + "\"","PYTHON")
                                        arcpy.CalculateField_management("cc_lyr","GFESPDE","\"" + fec + "\"","PYTHON")
                                        arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")
                          
                                    else:
                                        arcpy.AddMessage("No intersecta la dehesa con la nueva vegetacion - No cambia la dehesa")
                                    #limpio
                                    if arcpy.Exists("dehe_ini"):
                                        arcpy.Delete_management("dehe_ini")
                             
                                else:
                                    arcpy.AddMessage("No existe dehesa en la provincia ")
                                    fictime.write('No existe dehesa en la provincia ' + '\n')
                                        
                            #limpio
                            if arcpy.Exists("Suelo_temp"):
                                    arcpy.Delete_management("Suelo_temp")
                            if arcpy.Exists("FStMat"):
                                    arcpy.Delete_management("FStMat")
                            if arcpy.Exists("FStSue"):
                                    arcpy.Delete_management("FStSue")
                                        
                            if arcpy.Exists("GVegAR"):
                                    arcpy.Delete_management("GVegAR")
                            if arcpy.Exists("GVegMA"):
                                    arcpy.Delete_management("GVegMA")
                            if arcpy.Exists("GVegSU"):
                                    arcpy.Delete_management("GVegSU")
                            if arcpy.Exists("GVegED"):
                                    arcpy.Delete_management("GVegED")
                            if arcpy.Exists("GVegAG"):
                                    arcpy.Delete_management("GVegAG")
                                        
                            if arcpy.Exists("gtemp_vegarb"):
                                    arcpy.Delete_management("gtemp_vegarb")
                            if arcpy.Exists("gtemp_vegmat"):
                                    arcpy.Delete_management("gtemp_vegmat")
                            if arcpy.Exists("gtemp_vegsue"):
                                    arcpy.Delete_management("gtemp_vegsue")
                            if arcpy.Exists("gtemp_vegedi"):
                                    arcpy.Delete_management("gtemp_vegedi")
                            if arcpy.Exists("gtemp_vegagu"):
                                    arcpy.Delete_management("gtemp_vegagu")
                            if arcpy.Exists("Mat_temp"):
                                    arcpy.Delete_management("Mat_temp")
             
                            #if arcpy.Exists("GVEGP_" + codprov):
                                   #arcpy.Delete_management("GVEGP_" + codprov)
                            #if arcpy.Exists("GVEG_" + codprov):
                                    #arcpy.Delete_management("GVEG_" + codprov)
                            if arcpy.Exists("GVEG_OLD"):
                                    arcpy.Delete_management("GVEG_OLD")                        
                                    
                            if arcpy.Exists(dirTrab + "\\PROYE\\pf_veg"):
                                    arcpy.Delete_management(dirTrab + "\\PROYE\\pf_veg")
                        else:
                            arcpy.AddMessage("Hay fichero de cambios de Vegetacion pero NO cambia")
                            
            else:
                arcpy.AddMessage("No hay fichero de cambios de Vegetacion")

            #*****************************
            # preparo el vectorial de factor especie si cambios
            #**************************************************************************************
            cambiaesp = 0
            
            if arcpy.Exists(dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\FactEsp.shp"):
                arcpy.AddMessage("Inicio vectorial FEspCA ")
                fictime.write('Inicio vectorial FEspCA ' + '\n')
              
                shp_fespca = dirPrin + "\\datos_ori\\M" + anio + codMes + "\\prov" + codprov + "\\FactEsp.shp"
                shp_espcap = arcpy.FeatureClassToFeatureClass_conversion(shp_fespca,dirTrab + "\\PROYE","pf_espca" ) # por si distinta proyeccion
                arcpy.AddField_management("\\PROYE\\pf_espca", "PROVINCIA", "LONG")
                arcpy.CalculateField_management("\\PROYE\\pf_espca", "PROVINCIA","!PROV!", "PYTHON")

                arcpy.MakeFeatureLayer_management(shp_espcap,"lyrFEsp")
                arcpy.SelectLayerByAttribute_management("lyrFEsp" , "NEW_SELECTION", "\"FE_ARB\" <> -1 or  \"FE_MAT\" <> -1 or \"FE_SUE\" <> -1")
                arcpy.AddMessage("Recintos con cambios en especie: " + arcpy.GetCount_management("lyrFEsp").getOutput(0))          
                if int(arcpy.GetCount_management("lyrFEsp").getOutput(0)) > 0: # se genera solo si vienen recintos con algo <> -1
                    cambiaesp = 1               

                    if ProespCA == "true":
                        arcpy.AddMessage("** Proceso bloque 1 de EspecieCA " + time.ctime())
                        fictime.write('Proceso bloque 1 de EspecieCA ' + time.ctime() + '\n')
 
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov): 
                            arcpy.AddMessage("hay especie CA previa en la provincia") 
                            arcpy.Update_analysis(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov, "lyrFEsp", "\\PROYE\\FEspCA_" + codprov, "#", 0.001) 
                            arcpy.RepairGeometry_management("\\PROYE\\FEspCA_" + codprov)
                
                            #calcula mascara de especie CCAA
                            arcpy.PolygonToRaster_conversion("lyrFEsp", "PROV" , "gtempmasc", "CELL_CENTER","NONE",5) 
                            gtemp1 = Con(Raster("gtempmasc") >= 0,1)
                            gtemp1.save("gtempmasc2")
                            arcpy.MosaicToNewRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\gesp_" + codprov + ";gtempmasc2",dirTrab, "GESP_" + codprov,"","","",1,"LAST")
                            arcpy.BuildRasterAttributeTable_management("GESP_" + codprov, "Overwrite")
              
                        else: 
                            arcpy.AddMessage("Especie CA nueva en la provincia") 
                            arcpy.Copy_management("lyrFEsp", "\\PROYE\\FEspCA_" + codprov) 
        
                            #calcula mascara de especie CCAA
                            arcpy.PolygonToRaster_conversion("lyrFEsp", "PROV" , "gtempmasc", "CELL_CENTER","NONE",5) 
                            gtemp1 = Con(Raster("gtempmasc") >= 0,1)
                            gtemp1.save("GESP_" + codprov)
                            arcpy.BuildRasterAttributeTable_management("GESP_" + codprov, "Overwrite")

                        # sustituyo en dirFin
                        arcpy.AddMessage("Sustituyo en DirFin")
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov):
                            arcpy.Copy_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov)
                        
                        arcpy.Copy_management(dirTrab + "\\PROYE\\FEspCA_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov)

                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov):
                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov)
                        
                        arcpy.CopyRaster_management("GESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov)

                        # cargo en CAMBIOS_Mxx - 
                        arcpy.AddMessage("Cargo en CambiosFesp")
                        arcpy.Dissolve_management("lyrFEsp", "\\PROYE\\cambia_fesp",["PROV", "MUN"], "", "SINGLE_PART","DISSOLVE_LINES")
        
                        arcpy.AddField_management("\\PROYE\\cambia_fesp", "TIPO_ESP", "TEXT", "", "", 3)
                        arcpy.AddField_management("\\PROYE\\cambia_fesp", "MES_ESP", "TEXT", "", "", 4)
        
                        arcpy.CalculateField_management("\\PROYE\\cambia_fesp", "TIPO_ESP","'ESP'", "PYTHON")
                        arcpy.CalculateField_management("\\PROYE\\cambia_fesp", "MES_ESP","\"" + anio + codMes + "\"", "PYTHON")
  
        
                        if arcpy.Exists(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosFesp_M" + anio + codMes + ".shp"):
                            arcpy.Append_management(["\\PROYE\\cambia_fesp"],dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosFesp_M" + anio + codMes + ".shp", "NO_TEST")
                            arcpy.CalculateField_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\CambiosFesp_M" + anio + codMes + ".shp", "Shape_Area","!shape.Area!", "PYTHON")
                        else:
                            arcpy.env.outputCoordinateSystem = arcpy.Describe(dirFin + "\\prov28\\prov28.gdb\\GLIMITE_28").spatialReference # proyecciopn obliga a huso30
                            arcpy.FeatureClassToFeatureClass_conversion("\\PROYE\\cambia_fesp",  dirPrin + "\\PROYE\\M" + anio + codMes, "CambiosFesp_M" + anio + codMes + ".shp")
                            arcpy.env.outputCoordinateSystem = arcpy.Describe(prov_ras).spatialReference #proyeccion de la provincia

                        #relleno control_cambios
                        fec = strftime("%d/%m/%Y",gmtime())
                        arcpy.AddMessage(fec)
                        arcpy.CalculateField_management("cc_lyr","GESP","\"" + fec + "\"","PYTHON")
                        arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                        #limpio
                        if arcpy.Exists("gtempmasc"):
                            arcpy.Delete_management("gtempmasc")
                        if arcpy.Exists("gtempmasc2"):
                            arcpy.Delete_management("gtempmasc2")
                if arcpy.Exists("\\PROYE\\pf_espca"):
                    arcpy.Delete_management("\\PROYE\\pf_espca")
                            
            else:
                arcpy.AddMessage("No hay fichero de cambios de Factor Especie CA")

            #*****************************
            # preparo rasters GFESPES, GFESP GFVEGESP si cambios
            #**************************************************************************************
            
            arcpy.AddMessage ("cambiaveg= " + str(cambiaveg) + " - cambiaesp= " + str(cambiaesp)) 
            if cambiaveg == 1 or cambiaesp == 1:
                arcpy.AddMessage("Inicio raster GFESPES ")
                fictime.write('Inicio raster GFESPES' + '\n')
                existeesp = 0

                if ProespCA == "true":
                    arcpy.AddMessage("** Proceso bloque 2 de EspecieCA " + time.ctime())
                    fictime.write('Proceso bloque 2 de EspecieCA ' + time.ctime() + '\n')

                    # mira si existe especie de CA
                    if arcpy.Exists("\\PROYE\\FEspCA_" + codprov): 
                        arcpy.AddMessage("FEspCA cambia o nuevo")
                        arcpy.MakeFeatureLayer_management("\\PROYE\\FEspCA_" + codprov,"lyrFEsp")
                        arcpy.env.mask = "GESP_" + codprov  # mascara
                        existeesp = 1
               
                    else:
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov): 
                            arcpy.AddMessage("FEspCA No cambia pero existe en la provincia de antes")
                            #arcpy.FeatureClassToFeatureClass_conversion(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov,dirTrab + "\\PROYE","PROYE\\FEspCA_NEW") 
                            arcpy.MakeFeatureLayer_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\FEspCA_" + codprov,"lyrFEsp")
                            arcpy.env.mask = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GESP_" + codprov # mascara
                            existeesp = 1
                        else:
                            arcpy.AddMessage("No FEspecie: ni antes, ni nuevo")

                    if existeesp == 1: 
                        #genero los 3 rasters de factor especie
                        arcpy.AddMessage("genero los 3 rasters de f especie CA")
                        if arcpy.Exists("GVEG_" + codprov):
                            ras2 = Raster("GVEG_" + codprov)
                        else:
                            ras2 = Raster(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GVEG_" + codprov)
                        entrada = ""
                                                    
                        # f_arb
                        arcpy.AddMessage("arbolado")
                        arcpy.SelectLayerByAttribute_management("lyrFEsp" , "NEW_SELECTION", "\"FE_ARB\" >= 0")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrFEsp").getOutput(0))
                        if int(arcpy.GetCount_management("lyrFEsp").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrFEsp", "FE_ARB" , "GFESPAR_temp", "CELL_CENTER","NONE",5)
                            ras1 = Raster("GFESPAR_temp")
                            gtemp1 = Con(((ras1 >= 0) & (ras2 == 3)),ras1)
                            gtemp1.save("gtemp_fvegar")
                            entrada = entrada + ";gtemp_fvegar"

                        # f_mat
                        arcpy.AddMessage("matorral")
                        arcpy.SelectLayerByAttribute_management("lyrFEsp" , "NEW_SELECTION", "\"FE_MAT\" >= 0")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrFEsp").getOutput(0))
                        if int(arcpy.GetCount_management("lyrFEsp").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrFEsp", "FE_MAT", "GFESPMA_temp", "CELL_CENTER","NONE",5)
                            ras1 = Raster("GFESPMA_temp")
                            gtemp2 = Con(((ras1 >= 0) & (ras2 == 2)),ras1)
                            gtemp2.save("gtemp_fvegmat")
                            entrada = entrada + ";gtemp_fvegmat"

                        # f_sue
                        arcpy.AddMessage("suelo")
                        arcpy.SelectLayerByAttribute_management("lyrFEsp" , "NEW_SELECTION", "\"FE_SUE\" >= 0")
                        arcpy.AddMessage(arcpy.GetCount_management("lyrFEsp").getOutput(0))
                        if int(arcpy.GetCount_management("lyrFEsp").getOutput(0)) > 0:
                            arcpy.PolygonToRaster_conversion("lyrFEsp", "FE_SUE", "GFESPSU_temp", "CELL_CENTER","NONE",5)
                            ras1 = Raster("GFESPSU_temp")
                            gtemp3 = Con(((ras1 >= 0) & (ras2 == 1)),ras1)
                            gtemp3.save("gtemp_fvegsue")
                            entrada = entrada + ";gtemp_fvegsue"

                        arcpy.SelectLayerByAttribute_management("lyrFEsp" , "CLEAR_SELECTION", "")

                        #genero el nuevo factor vegetacion
                        arcpy.AddMessage("Genero GFESPES ")
                        if entrada <> "": 
                            entrada = entrada[1:] 
                            arcpy.AddMessage(entrada)
            
                            arcpy.MosaicToNewRaster_management(entrada, dirTrab,"GFESPES_" + codprov, "","8_BIT_UNSIGNED", "", "1", "FIRST","FIRST")
                            arcpy.BuildRasterAttributeTable_management("GFESPES_" + codprov, "Overwrite")

                            arcpy.env.mask = prov_ras   # estrituyomascara

                            # sustituyo en dirFin
                            arcpy.AddMessage("Sustituyo en DirFin")
                            if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPES_" + codprov):
                                arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPES_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPES_" + codprov + "_M" + str(anio + codMes) )
                                arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPES_" + codprov)
                            
                            arcpy.CopyRaster_management("GFESPES_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\GFESPES_" + codprov)

                            #relleno control_cambios
                            fec = strftime("%d/%m/%Y",gmtime())
                            arcpy.AddMessage(fec)
                            arcpy.CalculateField_management("cc_lyr","GFESPES","\"" + fec + "\"","PYTHON")
                            arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")
                          
                        arcpy.env.mask = prov_ras   # estrituyomascara

                        #limpio
                        if arcpy.Exists("GFESPAR_temp"):
                            arcpy.Delete_management("GFESPAR_temp")
                        if arcpy.Exists("GFESPMA_temp"):
                            arcpy.Delete_management("GFESPMA_temp")
                        if arcpy.Exists("GFESPSU_temp"):
                            arcpy.Delete_management("GFESPSU_temp")
                        if arcpy.Exists("gtemp_fvegar"):
                            arcpy.Delete_management("gtemp_fvegar")
                        if arcpy.Exists("gtemp_fvegmat"):
                            arcpy.Delete_management("gtemp_fvegmat")
                        if arcpy.Exists("gtemp_fvegsue"):
                            arcpy.Delete_management("gtemp_fvegsue")
        
                    arcpy.env.mask = prov_ras   # restituyo mascara
                
                # prepara rasters de factor especie FINAL(dehesa+especieCA) -si hay cambio en vege y/o esp
                #*******************************************************

                if Proesp == "true":
                    arcpy.AddMessage("** Proceso bloque de Especie Total (deh+espCA) " + time.ctime())
                    fictime.write('Proceso bloque de Especie Total (deh+espCA) ' + time.ctime() + '\n')
                   
                    arcpy.AddMessage("Inicio grid GFESP (dehesa+especie CA)")
                    fictime.write('Inicio grid GFESP (dehesa+especie CA) ' + '\n')

                    if arcpy.Exists("GFESPDE_" + codprov):
                        arcpy.AddMessage("Existe dehesa nueva")
                        gtemp1 = "GFESPDE_" + codprov
                    
                        if arcpy.Exists("GFESPES_" + codprov):
                            arcpy.AddMessage("Existe especie nueva")
                            gtemp2 = "GFESPES_" + codprov

                            arcpy.MosaicToNewRaster_management([gtemp2, gtemp1], dirTrab,"GFESP_" + codprov,"","", "", "1", "FIRST","FIRST")
                            arcpy.BuildRasterAttributeTable_management("GFESP_" + codprov, "Overwrite")
                        else:
                            arcpy.AddMessage("No Existe especie nueva")
                            arcpy.CopyRaster_management(gtemp1,"GFESP_" + codprov)
                    else:
                        arcpy.AddMessage("NO Existe dehesa nueva")
                        if arcpy.Exists( dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov):
                            arcpy.AddMessage("pero si existe dehesa de antes")
                            gtemp1 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESPDE_" + codprov

                            if arcpy.Exists("GFESPES_" + codprov):
                                arcpy.AddMessage("Existe especie nueva")
                                gtemp2 = "GFESPES_" + codprov
        
                                arcpy.MosaicToNewRaster_management([gtemp2, gtemp1], dirTrab,"GFESP_" + codprov,"","", "", "1", "FIRST","FIRST")
                                arcpy.BuildRasterAttributeTable_management("GFESP_" + codprov, "Overwrite")
                        else:
                            arcpy.AddMessage("NO existe dehesa de antes")                               
                            if arcpy.Exists("GFESPES_" + codprov):
                                arcpy.AddMessage("Existe especie nueva")
                                gtemp2 = "GFESPES_" + codprov
                                arcpy.CopyRaster_management(gtemp2,"GFESP_" + codprov)

                    # sustituyo en dirFin
                    arcpy.AddMessage("Sustituyo en DirFin")
                    if arcpy.Exists("GFESP_" + codprov):
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov):
                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov)
                            
                        arcpy.CopyRaster_management("GFESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov)

                        #relleno control_cambios
                        fec = strftime("%d/%m/%Y",gmtime())
                        arcpy.AddMessage(fec)
                        arcpy.CalculateField_management("cc_lyr","GFESP","\"" + fec + "\"","PYTHON")
                        arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

                # prepara rasters de factor vegetacion con especie - si hay cambio en vege y/o esp
                #*******************************************************

                if Provegesp == "true":
                    arcpy.AddMessage("** Proceso bloque de Vegetación con especie " + time.ctime())
                    fictime.write('Proceso bloque de Vegetación con especie ' + time.ctime() + '\n')

                    arcpy.AddMessage("Inicio grid GFVEGESP ")
                    fictime.write('Inicio grid GFVEGESP ' + '\n')

                    if arcpy.Exists("GFVEG_" + codprov):
                        arcpy.AddMessage("Existe cambio de vegetacion")
                        gtemp1 = "GFVEG_" + codprov
                        if arcpy.Exists("GFESP_" + codprov):
                            arcpy.AddMessage("Existe cambio de Fespecie")
                            gtemp2 = "GFESP_" + codprov

                            #arcpy.MosaicToNewRaster_management([gtemp2, gtemp1], dirTrab,"GFVEGESP_" + codprov,"","", "", "1", "FIRST","FIRST")
                            gtemp = Con(IsNull(Raster(gtemp2)),Raster(gtemp1), Raster(gtemp2))
                            gtemp.save("GFVEGESP_" + codprov)
                            arcpy.BuildRasterAttributeTable_management("GFVEGESP_" + codprov, "Overwrite")

                        else:
                            arcpy.AddMessage("No Existe cambio de Fespecie") 
                            if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov): #cambia 20241214
                                arcpy.AddMessage("Existe Fespecie de antes") #cambia 20241214
                                gtemp2 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFESP_" + codprov  #cambia 20241214
                                 
                                gtemp = Con(IsNull(Raster(gtemp2)),Raster(gtemp1), Raster(gtemp2)) #cambia 20241214
                                gtemp.save("GFVEGESP_" + codprov) #cambia 20241214
                                arcpy.BuildRasterAttributeTable_management("GFVEGESP_" + codprov, "Overwrite") #cambia 20241214
                            else:
                                arcpy.AddMessage("No Existe Fespecie de antes")
                                arcpy.CopyRaster_management("GFVEG_" + codprov, "GFVEGESP_" + codprov )
                                arcpy.BuildRasterAttributeTable_management("GFVEGESP_" + codprov, "Overwrite")

                    else:
                        arcpy.AddMessage("No cambio de vegetacion")
                        if arcpy.Exists("GFESP_" + codprov):
                            arcpy.AddMessage("Existe cambio de Fespecie")
                            gtemp1 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEG_" + codprov
                            gtemp2 = "GFESP_" + codprov

                            #arcpy.MosaicToNewRaster_management([gtemp2, gtemp1], dirTrab,"GFVEGESP_" + codprov,"","", "", "1", "FIRST","FIRST")
                            gtemp = Con(IsNull(Raster(gtemp2)),Raster(gtemp1), Raster(gtemp2))
                            gtemp.save("GFVEGESP_" + codprov)
                            arcpy.BuildRasterAttributeTable_management("GFVEGESP_" + codprov, "Overwrite")

                    # sustituyo en dirFin
                    arcpy.AddMessage("Sustituyo en DirFin")
                    if arcpy.Exists("GFVEGESP_" + codprov):
                        if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov):
                            arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov + "_M" + str(anio + codMes) )
                            arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov)
                            
                        arcpy.CopyRaster_management("GFVEGESP_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov)

                        #relleno control_cambios
                        fec = strftime("%d/%m/%Y",gmtime())
                        arcpy.AddMessage(fec)
                        arcpy.CalculateField_management("cc_lyr","GFVEGES","\"" + fec + "\"","PYTHON")
                        arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")

            else:
                arcpy.AddMessage("No hay cambios ni en vegetación, ni en Factor Especie CA")
            
            #**************************************************************
            # prepara rasters de CA
            #*******************************************************

            if Proca == "true":
                arcpy.AddMessage("** Proceso bloque de CA " + time.ctime())
                fictime.write('Proceso bloque de CA ' + time.ctime() + '\n')
                
                arcpy.AddMessage("Inicio grid GCA ")
                fictime.write('Inicio grid GCA ' + '\n')
                cambiatot = 0

                # incendios
                if cambiainc != 0:
                #if arcpy.Exists("GFINC_" + codprov):
                    gtemp1 = "GFINC_" + codprov
                    cambiatot = cambiatot + 1
                else:
                    gtemp1 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFINC_" + codprov
                arcpy.AddMessage(gtemp1)

                # pte
                gtemp2 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFPTE_" + codprov
                arcpy.AddMessage(gtemp2)

                # suelo
                if arcpy.Exists("GFSUE_" + codprov):
                    gtemp3 = "GFSUE_" + codprov
                    cambiatot = cambiatot + 1
                else:
                    gtemp3 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFSUE_" + codprov
                arcpy.AddMessage(gtemp3)

                # vegetacion
                if arcpy.Exists("GFVEGESP_" + codprov):
                    gtemp4 = "GFVEGESP_" + codprov
                    cambiatot = cambiatot + 1
                else:
                    gtemp4 = dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GFVEGESP_" + codprov
                arcpy.AddMessage(gtemp4)

                # calculo
                if cambiatot != 0:
                    
                    gtemp = Combine([Raster(gtemp2), Raster(gtemp3), Raster(gtemp4), Raster(gtemp1)])
                    gtemp.save("GTOTAL_" + codprov)
                    arcpy.AddField_management("gtotal_" + codprov,"CA","LONG")
                    arcpy.MakeRasterLayer_management("gtotal_" + str(codprov), "gcalyr")    
                    arcpy.CalculateField_management("gcalyr","CA","!GFPTE_" + codprov + "! * !GFSUE_" + codprov + "! * !GFVEGESP_" + codprov + "! * !GFINC_" + codprov + "! " , "PYTHON")
              
                    gtemp = Lookup("GTOTAL_" + codprov,"CA")
                    gtemp.save("GCA_" + codprov)
                    
                    #gtemp = Raster(gtemp1) * Raster(gtemp2) * Raster(gtemp3) * Raster(gtemp4)
                    #gtemp.save("GCA_" + codprov)
                    arcpy.BuildRasterAttributeTable_management("GCA_" + codprov, "Overwrite")


                    # sustituyo en dirFin
                    arcpy.AddMessage("Sustituyo en DirFin")
                    if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GTOTAL_" + codprov):
                        arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GTOTAL_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GTOTAL_" + codprov + "_M" + str(anio + codMes) )
                        arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GTOTAL_" + codprov)
                                
                    arcpy.CopyRaster_management("GTOTAL_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GTOTAL_" + codprov)
                    
                    if arcpy.Exists(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GCA_" + codprov):
                        arcpy.CopyRaster_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GCA_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GCA_" + codprov + "_M" + str(anio + codMes) )
                        arcpy.Delete_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GCA_" + codprov)
                                
                    arcpy.CopyRaster_management("GCA_" + codprov, dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\GCA_" + codprov)

                    #relleno control_cambios
                    fec = strftime("%d/%m/%Y",gmtime())
                    arcpy.AddMessage(fec)
                    arcpy.CalculateField_management("cc_lyr","GCA","\"" + fec + "\"","PYTHON")
                    arcpy.CalculateField_management("cc_lyr","FICH_CONTR","'CambiosTot_M"+ anio + codMes + "'", "PYTHON")
            
            #**************************************************************
            # prepara GDB limpia
            #*******************************************************

            if ProGDB == "true":
                arcpy.AddMessage("** Proceso bloque de preparar GDB limpia " + time.ctime())
                fictime.write('Proceso bloque de preparar GDB limpia ' + time.ctime() + '\n')
                dirLimp2 = dirLimp + "\\M" + anio + codMes

                arcpy.Copy_management(dirFin + "\\prov" + codprov + "\\prov" + codprov + ".gdb" ,dirLimp2 + "\\prov" + codprov + "\\prov" + codprov + ".gdb")

                #limpio vectoriales
                arcpy.AddMessage("Inicio limpia vectoriales")
                arcpy.env.workspace = dirLimp2 + "\\prov" + codprov + "\\prov" + codprov + ".gdb"
                fctot = arcpy.ListFeatureClasses("","","PROYE")
                for fc in fctot:
                    fcfin = fc[len(fc)-3:]
                    if fcfin != "_" + codprov:
                        arcpy.AddMessage(fc)
                        arcpy.Delete_management(dirLimp2 + "\\prov" + codprov + "\\prov" + codprov + ".gdb\\PROYE\\" + fc)

                #limpio rasters
                arcpy.AddMessage("Inicio limpia rasters")
                fctot = arcpy.ListRasters()
                for fc in fctot:
                    fcfin = fc[len(fc)-3:]
                    if fcfin != "_" + codprov:
                        arcpy.AddMessage(fc)
                        arcpy.Delete_management(fc)
                        
                #restauro 
                arcpy.env.workspace = dirPrin + "\\PROYE\\M" + anio + codMes + "\\prov" + codprov + "\\prov" + codprov + ".gdb"

                
            arcpy.AddMessage("Provincia terminada a las "  + time.ctime())
            arcpy.AddMessage("*************************")
            fictime.write('Provincia terminada a las ' + time.ctime() + '\n')
            fictime.write('*********************************' + '\n')
        fictime.close()

# hago fichero de union de cambios
#*******************************************
if ProFin == "true":
       
    arcpy.AddMessage("Proceso bloque Generación de fichero final de cambios " + time.ctime())
    fictime = open(dirPrin + "\\PROYE\\M" + anio + codMes + "\log_timeF10.txt","a")
    fictime.write('Proceso bloque Generación de fichero final de cambios ' + time.ctime() + '\n')

    arcpy.ClearEnvironment("extent")
    arcpy.env.workspace = dirPrin + "\\PROYE\\M" + anio + codMes
    entrada = ""
    
    if arcpy.Exists("CambiosInc_M" + anio + codMes + ".shp"):
        arcpy.MakeFeatureLayer_management("CambiosInc_M" + anio + codMes + ".shp","inc_lyr")
        arcpy.SelectLayerByAttribute_management("inc_lyr", "NEW_SELECTION", "PROV > 0 or PROV_1 > 0")
        entrada = ";inc_lyr"
    if arcpy.Exists("CambiosSue_M" + anio + codMes + ".shp"):
        arcpy.MakeFeatureLayer_management("CambiosSue_M" + anio + codMes + ".shp","sue_lyr")
        arcpy.SelectLayerByAttribute_management("sue_lyr", "NEW_SELECTION", "PROV > 0 ")
        entrada = entrada + ";sue_lyr"
    if arcpy.Exists("CambiosVeg_M" + anio + codMes + ".shp"):
        arcpy.MakeFeatureLayer_management("CambiosVeg_M" + anio + codMes + ".shp","veg_lyr")
        arcpy.SelectLayerByAttribute_management("veg_lyr", "NEW_SELECTION", "PROV > 0 ")
        entrada = entrada + ";veg_lyr"
    if arcpy.Exists("CambiosFesp_M" + anio + codMes + ".shp"):
        arcpy.MakeFeatureLayer_management("CambiosFesp_M" + anio + codMes + ".shp","fesp_lyr")
        arcpy.SelectLayerByAttribute_management("fesp_lyr", "NEW_SELECTION", "PROV > 0 ")
        entrada = entrada + ";fesp_lyr"
        
    if entrada <> "":
        entrada = entrada[1:]    
        arcpy.AddMessage(entrada)
        fictime.write(entrada + '\n')

        arcpy.Union_analysis (entrada, "tempTot.shp", "", 0.001)
        arcpy.MultipartToSinglepart_management("tempTot.shp","tempTots.shp")
        arcpy.CalculateField_management("tempTots.shp", "Shape_Area","!shape.Area!", "PYTHON")

        #cargo el municipio
        arcpy.Identity_analysis("tempTots.shp", dirFin + "\\espana\\espana.gdb\PROYE_30\\ESP_cache_2026_TM_h30", "tempTot2.shp","#","0.001")
        arcpy.MultipartToSinglepart_management("tempTot2.shp","tempTot2s.shp")
        arcpy.CalculateField_management("tempTot2s.shp", "Shape_Area","!shape.Area!", "PYTHON")
        
        arcpy.MakeFeatureLayer_management("tempTot2s.shp","tot_lyr")
        # arcpy.SelectLayerByAttribute_management("tot_lyr", "NEW_SELECTION", "PROVINCIA <> 0")

##        arcpy.AddField_management("tempTots.shp","PROVINCIA","LONG")
##        #calculo PROVINCIA
##        arcpy.CalculateField_management("tot_lyr","PROVINCIA",'!PROV!', "PYTHON")
##        if arcpy.ListFields("tot_lyr", "PROV_1"):
##            arcpy.SelectLayerByAttribute_management("tot_lyr", "NEW_SELECTION", "PROV = 0 AND PROV_1 <> 0")
##            if int(arcpy.GetCount_management("tot_lyr").getOutput(0)) > 0:
##                arcpy.CalculateField_management("tot_lyr","PROV",'!PROV_1!', "PYTHON")
##                arcpy.CalculateField_management("tot_lyr","MUN",'!MUN_1!', "PYTHON")
##        if arcpy.ListFields("tot_lyr", "PROV_12"):
##            arcpy.SelectLayerByAttribute_management("tot_lyr", "NEW_SELECTION", "PROV = 0 AND PROV_12 <> 0")
##            if int(arcpy.GetCount_management("tot_lyr").getOutput(0)) > 0:
##                arcpy.CalculateField_management("tot_lyr","PROV",'!PROV_12!', "PYTHON")
##                arcpy.CalculateField_management("tot_lyr","MUN",'!MUN_12!', "PYTHON")
##        if arcpy.ListFields("tot_lyr", "PROV_12_13"):
##            arcpy.SelectLayerByAttribute_management("tot_lyr", "NEW_SELECTION", "PROV = 0 AND PROV_12_13 <> 0")
##            if int(arcpy.GetCount_management("tot_lyr").getOutput(0)) > 0:
##                arcpy.CalculateField_management("tot_lyr","PROV",'!PROV_12_13!', "PYTHON")
##                arcpy.CalculateField_management("tot_lyr","MUN",'!MUN_12_13!', "PYTHON")
##        if arcpy.ListFields("tot_lyr", "PROV_12_14"):
##            arcpy.SelectLayerByAttribute_management("tot_lyr", "NEW_SELECTION", "PROV = 0 AND PROV_12_14 <> 0")
##            if int(arcpy.GetCount_management("tot_lyr").getOutput(0)) > 0:
##                arcpy.CalculateField_management("tot_lyr","PROV",'!PROV_12_14!', "PYTHON")
##                arcpy.CalculateField_management("tot_lyr","MUN",'!MUN_12_14!', "PYTHON")
##        arcpy.SelectLayerByAttribute_management("tot_lyr", "CLEAR_SELECTION") 

        #limpio campos
        entrada = "PROVINCIA; MUNICIPIO; PROMUN "
        if arcpy.ListFields("tot_lyr", "TIPO_INC"):
            entrada = entrada + "; TIPO_INC; MES_INC"
        if arcpy.ListFields("tot_lyr", "TIPO_INC_1"):
            entrada = entrada + "; TIPO_INC_1; MES_INC_1"
        if arcpy.ListFields("tot_lyr", "TIPO_SUE"):
            entrada = entrada + ";TIPO_SUE; MES_SUE"
        if arcpy.ListFields("tot_lyr", "TIPO_VEG"):
            entrada = entrada + ";TIPO_VEG; MES_VEG"
        if arcpy.ListFields("tot_lyr", "TIPO_ESP"):
            entrada = entrada + ";TIPO_ESP; MES_ESP"

        arcpy.AddMessage("entrada de disolve: " + entrada)
        arcpy.Dissolve_management("tot_lyr", "CambiosTot_M"+ anio + codMes + ".shp", "\"" + entrada + "\"", "", "SINGLE_PART","DISSOLVE_LINES")
        arcpy.Dissolve_management("tempTot2s.shp", dirSem + "\\inf_general\\lim_controlcambCAP.gdb\\ETRS89_H30\\ActualizaRas_M"+ anio + codMes + "_30", "\"" + entrada + "\"", "", "SINGLE_PART","DISSOLVE_LINES")
        arcpy.SelectLayerByAttribute_management("tot_lyr", "CLEAR_SELECTION") 
        
        #limpio
        if arcpy.Exists("tempTots.shp"):
            arcpy.Delete_management("tempTots.shp")
        if arcpy.Exists("tempTot.shp"):
            arcpy.Delete_management("tempTot.shp")
        if arcpy.Exists("tempTot2.shp"):
            arcpy.Delete_management("tempTot2.shp")

    #calculo control de cambios
    arcpy.MakeTableView_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\Temp_CC.dbf", "cc_lyr")  
    arcpy.SelectLayerByAttribute_management("cc_lyr", "NEW_SELECTION", "\"FICH_CONTR\" <> ''")
    if int(arcpy.GetCount_management("cc_lyr").getOutput(0)) > 0:
        arcpy.CopyRows_management("cc_lyr", dirPrin + "\\PROYE\\M" + anio + codMes + "\\ControlCamb_M" + anio + codMes+ ".dbf")
        #arcpy.Delete_management(dirPrin + "\\PROYE\\M" + anio + codMes + "\\Temp_cc.dbf")


    fictime.close()

fictime = open(dirPrin + "\\PROYE\\M" + anio + codMes + "\log_timeF10.txt","a")  
fictime.write('TERMIN? TODO a las ' + time.ctime() + '\n')
fictime.write('*****************************************\n')
fictime.close()
arcpy.AddMessage("TERMIN? TODO a las " + time.ctime())
arcpy.AddMessage("??Acuerdate de revisar los ficheros de salida !!" )









