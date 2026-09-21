# -*- coding: utf-8 -*-

# **********************************
# Programa: calcula el raster de MDT , rellenando con 2014 si se le indica
# Salida: GMDT_prov y GPTE_prov
#
# Fecha : mayo-2021 (Modificado 2026)
# Autor: bvm / Optimizado con gestión de RAM y prevención de bloqueos (.lock)
#
# ************************************
#%% Inicializa

import arcpy
from arcpy.sa import *
import os
import time

def ejecutar_pipeline():
# =========================================================================
# >>> CONFIGURACIÓN DE PARÁMETROS PARA DESARROLLO (VS CODE vs TOOLBOX)
# =========================================================================
    if not arcpy.GetParameterAsText(0) or "jupyter" in arcpy.GetParameterAsText(0).lower():
        arcpy.AddMessage("--- EJECUTANDO MODO DESARROLLO EN VS CODE ---")
        dirPrin     = r"D:\Pastos\CAP2023_Lidar3\RASTERS_CSP"           
        ficOri      = r"D:\Pastos\CAP2023_Lidar3\PENDIENTES\TIFF\MDT05_Prov_5.tif"
        fcRecorta   = r"" 
        dirOld      = r"Z:\INF_MASACTUAL\RASTERS_CAP"
        fcProvOld   = r"\\172.17.11.141\pastos\INF_MASACTUAL\inf_general\lim_controlcambCAP.gdb\ETRS89_H30\LIMPROV2025_30"
        totProvp    = "03"                            
    else:
        dirPrin     = arcpy.GetParameterAsText(0)
        ficOri      = arcpy.GetParameterAsText(1)
        fcRecorta   = arcpy.GetParameterAsText(2)
        dirOld      = r"" if arcpy.GetParameterAsText(3) == "" else arcpy.GetParameterAsText(3)
        fcProvOld   = arcpy.GetParameterAsText(4)
        totProvp    = arcpy.GetParameterAsText(5)

    totProv = totProvp.split(";")
    print("Provincias cargadas en memoria:", totProv)
    # =========================================================================

    # Para que machaque si existen
    arcpy.env.overwriteOutput = True

    #Procesamiento en paralelo (varios nucleos)
    arcpy.env.parallelProcessingFactor = "75%"

    # Cojo la licencia de Spatial
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
        arcpy.AddMessage(f"{time.ctime()} - Licencia 'Spatial Analyst' disponible")
    else:
        arcpy.AddError("Licencia 'Spatial Analyst' no disponible. Abortando.")
        raise SystemExit

    # inicio bucle de provincias elegidas
    try:
        for codProv in totProv:

            # Configuro directorios y entornos seguros usando os.path.join
            gdb_trabajo = os.path.join(dirPrin, f"prov{codProv}", f"prov{codProv}.gdb")
            log_path = os.path.join(dirPrin, f"prov{codProv}", "log_timeF11.txt")

            if not arcpy.Exists(gdb_trabajo):
                arcpy.AddError(f"No existe la gdb {gdb_trabajo}. No se puede procesar la provincia {codProv}")
                fictime.write(f"{time.ctime()} - No existe la gdb {gdb_trabajo}. No se puede procesar la provincia {codProv}\n")
                print(f"No se puede procesar la provincia {codProv}. No existe la gdb de trabajo.")
                continue
            
            arcpy.env.workspace = gdb_trabajo

            # MEJORA: Abrimos el log de manera segura asegurando su cierre automático al terminar la provincia
            with open(log_path, "a") as fictime:
                fictime.write('*******************************\n')
                arcpy.AddMessage(f"{time.ctime()} - Inicio del procesamiento de la provincia: {codProv}")
                fictime.write(f"{time.ctime()} - Inicio la provincia {codProv}\n")

                # Pasa a raster de GDB el MDT
                arcpy.AddMessage(f"{time.ctime()} - Generando GMDT intermedio... ")
                fictime.write(f"{time.ctime()} - Generando GMDT intermedio...\n")

                gtemp = Float(ficOri)
                gtemp.save("GMDT_ini_" + codProv)
                del gtemp # Liberamos RAM

                # Defino la proyeccion
                prov_vec = "GLIMITE_B210_" + codProv
                dsc = arcpy.Describe(prov_vec)
                coord_sys = dsc.spatialReference

                arcpy.DefineProjection_management("GMDT_ini_" + codProv, coord_sys)

                # Configuro entornos con buffer ajustados a la máscara
                arcpy.env.outputCoordinateSystem = coord_sys 
                arcpy.env.extent = prov_vec  
                arcpy.env.snapRaster = prov_vec  
                arcpy.env.mask = prov_vec   
                arcpy.env.cellSize = prov_vec   

                # Meto informacion del Lidar2 si existe FC limite de recorte
                if fcRecorta:
                    arcpy.AddMessage("****************** ")
                    arcpy.AddMessage(f"{time.ctime()} - Meto informacion Lidar2 ")
                    fictime.write(f"{time.ctime()} - Meto informacion Lidar2 \n")

                    arcpy.AddMessage(f"{time.ctime()} - calculo hojas afectadas")
                    fictime.write(f"{time.ctime()} - calculo hojas afectadas \n")
                    
                    # MEJORA: Mandamos las tablas geográficas intermedias a la memoria RAM virtual (memory)
                    out_identity = "memory\\mmdt_l2_" + codProv
                    out_frequency = "memory\\mdt_l2_frq"
                    
                    if arcpy.Exists(out_identity): arcpy.Delete_management(out_identity)
                    if arcpy.Exists(out_frequency): arcpy.Delete_management(out_frequency)

                    arcpy.Identity_analysis(fcRecorta, fcProvOld, out_identity, "ALL", "0.001")
                    arcpy.Frequency_analysis(out_identity, out_frequency, ["PROVINCIA"])

                    # MEJORA CLAVE: Nuevo Data Access Cursor protegido que evita bloqueos de la GDB
                    with arcpy.da.SearchCursor(out_frequency, ["PROVINCIA"]) as cur:
                        for row in cur:
                            nL2Prov = row[0]
                            arcpy.AddMessage(f"Hoja: {nL2Prov}")
                            fictime.write(f"Hoja: {nL2Prov}\n")

                            Raster1 = os.path.join(dirOld, f"prov{nL2Prov}")
                            gtemp = ExtractByMask(Raster1, fcRecorta)

                            arcpy.AddMessage("Hago mosaico")
                            arcpy.Mosaic_management(gtemp, "GMDT_ini_" + codProv, "FIRST")
                            del gtemp # Liberamos RAM

                    # Limpieza explícita de la memoria intermedia de esta sección
                    arcpy.Delete_management("memory\\")

                # Genero raster ajustado a limite
                arcpy.AddMessage(f"{time.ctime()} - Generando GMDT final... ")
                fictime.write(f"{time.ctime()} - Generando GMDT final... \n")

                if arcpy.Exists("GMDT_" + codProv):
                    arcpy.AddMessage(f"{time.ctime()} - Ya existe GMDT_{codProv}. Se sobreescribirá el GMDT generado...")
                    fictime.write(f"{time.ctime()} -  Ya existe GMDT_{codProv}. Se sobreescribirá el GMDT generado.... \n")

                gtemp = Con(IsNull("GMDT_ini_" + codProv), 0, "GMDT_ini_" + codProv)
                gtemp.save("GMDT_" + codProv)
                del gtemp # Liberamos RAM

                # =========================================================================
                # >>> GENERACIÓN Y COMPROBACIÓN DE HUECOS (OPTIMIZADO ANTI-BLOQUEOS)
                # =========================================================================
                arcpy.AddMessage(f"{time.ctime()} - Generando raster de comprobacion de huecos... ")
                fictime.write(f"{time.ctime()} - Generando raster de comprobacion de huecos\n")

                if arcpy.Exists("gcompru_mdt"):
                    arcpy.Delete_management("gcompru_mdt")
                    
                gtemp = Con(IsNull("GMDT_ini_" + codProv), 0, 1)
                gtemp.save("gcompru_mdt")
                del gtemp # Fin del bloqueo de gcompru_mdt

                # Rutas en memoria virtual
                temp_poly = "memory\\temp_poly"
                temp_line = "memory\\temp_line"
                temp_point = "memory\\temp_point"
                out_compru = "PROYE/compru_mdt_" + codProv

                if arcpy.Exists(out_compru):
                    arcpy.Delete_management(out_compru)

                try:
                    arcpy.RasterToPolygon_conversion("gcompru_mdt", temp_poly, "NO_SIMPLIFY", "VALUE")
                    arcpy.FeatureToLine_management(temp_poly, temp_line, "0.001 Meters", "ATTRIBUTES")
                    arcpy.FeatureToPoint_management(temp_poly, temp_point, "INSIDE")
                    arcpy.FeatureToPolygon_management(temp_line, out_compru, "0.001 Meters", "", temp_point)

                except Exception as e:
                    arcpy.AddMessage(f"{time.ctime()} - Se ha producido un error al proceder a la conversión vectorial: {str(e)}")
                    fictime.write(f"{time.ctime()} - Se ha producido un error al proceder a la conversión vectorial: {str(e)}\n")

                finally:
                       
                    if arcpy.Exists("GMDT_ini_" + codProv):
                        arcpy.Delete_management("GMDT_ini_" + codProv) 

                # Fuerza a ArcGIS a vaciar la caché al acabar la provincia
                arcpy.ClearWorkspaceCache_management(gdb_trabajo)
                fictime.write(f"{time.ctime()} - La provincia {codProv} se ha procesado completamente con éxito\n")
                arcpy.AddMessage(f"{time.ctime()} - La provincia {codProv} se ha procesado completamente con éxito.")
                arcpy.AddMessage("¡¡Acuerdate de revisar los huecos rellenado a 0 - compru_mdt!!")
                fictime.write('*****************************************\n')

                print("Procesamiento finalizado con éxito.")

    finally:
        arcpy.Delete_management("memory\\")

        # Devolvemos la licencia al terminar el script completo
        arcpy.CheckInExtension("Spatial")

#%% Ejecución estructurada
if __name__ == "__main__":
    ejecutar_pipeline()



# %%
