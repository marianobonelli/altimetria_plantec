# Importar bibliotecas para manipulación de datos
import geopandas as gpd
import json  # Biblioteca estándar para manipulación de JSON

# Importar bibliotecas para visualización
import folium
from folium import FeatureGroup, LayerControl
import matplotlib.colors as mcolors  # Agregado para manejo de colores

# Importar bibliotecas para manejo de geometrías
from shapely.geometry import shape  # Para manejar geometrías

# Importar bibliotecas para manejo de imágenes
from PIL import Image

# Importar bibliotecas para integración web y Streamlit
import streamlit as st
from streamlit_folium import st_folium

# Importar módulos o paquetes locales
from helper import translate, api_call_logo, api_call_fields, domains_areas_by_user, seasons, farms

import folium
import numpy as np
import rasterio as rio
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

#########################################################################################################################
# Page Config y estilo
#########################################################################################################################

st.set_page_config(
    page_title="Altimetría",
    page_icon=Image.open("assets/favicon geoagro nuevo-13.png"),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://geoagro1.atlassian.net/servicedesk/customer/portal/5',
        'Report a bug': "https://geoagro1.atlassian.net/servicedesk/customer/portal/5",
        'About': "Powered by GeoAgro"
    }
)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

###################   User info   ##################

user_info = {'email': "mbonelli@geoagro.com", 'language': 'es', 'env': 'prod', 'domainId': 1, 'areaId': 11553, 'workspaceId': 1757, 'seasonId': 2588, 'farmId': 13510}

##################### API Logo Marca Blanca #####################

if user_info['env'] == 'prod':
    url = st.secrets["url_prod"]
    access_key_id = st.secrets["API_key_prod"]
    
elif user_info['env'] == 'test':
    url = st.secrets["url_test"]
    access_key_id = st.secrets["API_key_test"]   

default_logo='assets/GeoAgro_principal.png'

@st.cache_data
def get_logo(user_info, url, access_key_id, default_logo_path):
    logo_image = api_call_logo(user_info, url, access_key_id, default_logo_path)
    return logo_image

logo_image = get_logo(user_info, url, access_key_id, default_logo_path=default_logo)

st.session_state['logo_image'] = logo_image

##################### USER INFO #####################

language = user_info['language']
email = user_info['email']
env = user_info['env']
st.session_state['env'] = env

##################### LANGUAGE  #####################

c_1, c_2, c_3 = st.columns([1.5, 4.5, 1], gap="small")

with c_1:
    st.image(logo_image)

with c_3:   
    try:
        langs = ['es', 'en', 'pt']
        if language is not None:
            lang = st.selectbox(translate("language", language), label_visibility="hidden", options=langs, index=langs.index(language))
        else:  # from public link
            lang = st.selectbox(translate("es", language), label_visibility="hidden", options=langs)
        
        st.session_state['lang'] = lang
    except Exception as exception:
        lang = "es"
        st.session_state['lang'] = lang
        pass

##################### Titulo / solicitado por  #####################

# st.subheader(translate("dashboards",lang), anchor=False)
st.markdown(f'{translate("requested_by",lang)}<a style="color:blue;font-size:18px;">{""+email+""}</a> | <a style="color:blue;font-size:16px;" target="_self" href="/"> {translate("logout",lang)}</a>', unsafe_allow_html=True)
st.markdown('')
st.markdown('')

with st.sidebar:
    ############################################################################
    # DOMAIN
    ############################################################################

    hay_algun_establecimiento_seleccionado=False

    # Función para realizar la llamada a la API y cachear la respuesta
    @st.cache_data
    def get_domains_areas_by_user(user_info, access_key_id, url):
        api_call = domains_areas_by_user(user_info['email'], access_key_id, url)
        return api_call
    
    # Obtener la información de dominio
    dominios_api = get_domains_areas_by_user(user_info, access_key_id, url)

    # Filtrar y ordenar los dominios
    dominios_filtrados_ordenados = sorted([dominio for dominio in dominios_api if not dominio['deleted']], key=lambda dominio: dominio['name'])

    # Intentar encontrar el índice del dominio predeterminado en user_info
    default_domain_index = next((index for index, dominio in enumerate(dominios_filtrados_ordenados) if dominio['id'] == user_info['domainId']), None)

    # Selector de dominio en Streamlit
    dominio_seleccionado_nombre = st.selectbox(translate("domain",lang), [dominio['name'] for dominio in dominios_filtrados_ordenados], index=default_domain_index)
    dominio_seleccionado = next((dominio for dominio in dominios_filtrados_ordenados if dominio['name'] == dominio_seleccionado_nombre), None)

    ############################################################################
    # AREA
    ############################################################################

    if dominio_seleccionado:
        # Obtener áreas del dominio seleccionado y filtrarlas
        areas_seleccionadas = dominio_seleccionado['areas']
        areas_filtradas_ordenadas = sorted([area for area in areas_seleccionadas if not area['deleted']], key=lambda area: area['name'])

        # Intentar encontrar el índice del área predeterminada en user_info
        default_area_index = next((index for index, area in enumerate(areas_filtradas_ordenadas) if area['id'] == user_info['areaId']), None)

        # Selector de área en Streamlit
        area_seleccionada_nombre = st.selectbox(translate("area",lang), [area['name'] for area in areas_filtradas_ordenadas], index=default_area_index)
        area_seleccionada = next((area for area in areas_filtradas_ordenadas if area['name'] == area_seleccionada_nombre), None)

        ############################################################################
        # WORWSPACE
        ############################################################################

        if area_seleccionada:
            # Obtener workspaces del área seleccionada y filtrarlos
            workspaces_seleccionados = area_seleccionada['workspaces']
            workspaces_filtrados_ordenados = sorted([workspace for workspace in workspaces_seleccionados if not workspace['deleted']], key=lambda workspace: workspace['name'])

            # Intentar encontrar el índice del workspace predeterminado en user_info
            default_workspace_index = next((index for index, workspace in enumerate(workspaces_filtrados_ordenados) if workspace['id'] == user_info['workspaceId']), None)

            # Selector de workspace en Streamlit
            workspace_seleccionado_nombre = st.selectbox(translate("workspace",lang), [workspace['name'] for workspace in workspaces_filtrados_ordenados], index=default_workspace_index)
            workspace_seleccionado = next((workspace for workspace in workspaces_filtrados_ordenados if workspace['name'] == workspace_seleccionado_nombre), None)

            ############################################################################
            # Season
            ############################################################################

            # Función para realizar la llamada a la API y cachear la respuesta
            @st.cache_data
            def get_seasons(workspaceId, access_key_id, url):
                api_call = seasons(workspaceId, access_key_id, url)
                return api_call
            
            # Si se seleccionó un workspace, obtener las temporadas para ese workspace
            if workspace_seleccionado:
                # Realizar la llamada a la API para obtener las temporadas del workspace seleccionado
                seasons_data = get_seasons(workspace_seleccionado['id'], access_key_id, url)

                # Filtrar y ordenar las temporadas que no están eliminadas
                seasons_filtradas_ordenadas = sorted([season for season in seasons_data if not season['deleted']], key=lambda season: season['name'])

                # Intentar encontrar el índice de la temporada predeterminada en user_info
                default_season_index = next((index for index, season in enumerate(seasons_filtradas_ordenadas) if season['id'] == user_info['seasonId']), None)

                # Selector de temporada en Streamlit
                season_seleccionada_nombre = st.selectbox(translate("season",lang), [season['name'] for season in seasons_filtradas_ordenadas], index=default_season_index)
                season_seleccionada = next((season for season in seasons_filtradas_ordenadas if season['name'] == season_seleccionada_nombre), None)

                ############################################################################
                # Farm
                ############################################################################

                # Función para realizar la llamada a la API y cachear la respuesta
                @st.cache_data
                def get_farms(workspaceId, seasonId, access_key_id, url):
                    api_call = farms(workspaceId, seasonId, access_key_id, url)
                    return api_call

                # Si se seleccionó una temporada, obtener las granjas para esa temporada y workspace
                if season_seleccionada:
                    # Realizar la llamada a la API para obtener las granjas del workspace y la temporada seleccionados
                    farms_data = get_farms(workspace_seleccionado['id'], season_seleccionada['id'], access_key_id, url)

                    # Filtrar y ordenar las granjas que no están eliminadas
                    farms_filtradas_ordenadas = sorted([farm for farm in farms_data if not farm['deleted']], key=lambda farm: farm['name'])

                    # Intentar encontrar el índice de la granja predeterminada en user_info
                    default_farm_index = next((index for index, farm in enumerate(farms_filtradas_ordenadas) if farm['id'] == user_info['farmId']), None)

                    farm_seleccionada_nombre = st.selectbox(translate("farm",lang), [farm['name'] for farm in farms_filtradas_ordenadas], index=default_farm_index)
                    farm_seleccionada = next((farm for farm in farms_filtradas_ordenadas if farm['name'] == farm_seleccionada_nombre), None)

                    if farm_seleccionada:
                        hay_algun_establecimiento_seleccionado=True
                    
    ############################################################################
    # Powered by GeoAgro Picture
    ############################################################################

    st.markdown(
        """
        <style>
            div [data-testid=stImage]{
                bottom:0;
                display: flex;
                margin-bottom:10px;
            }
        </style>
        """, unsafe_allow_html=True
        )
        
    
    cI1,cI2,cI3=st.columns([1,4,1], gap="small")
    with cI1:
        pass
    with cI2:
        image = Image.open('assets/Powered by GeoAgro-01.png')
        new_image = image.resize((220, 35))
        st.image(new_image)
    with cI3:
        pass

############################################################################

if hay_algun_establecimiento_seleccionado == True:

    ##################### API Lotes #####################

    # Función para realizar la llamada a la API y cachear la respuesta
    @st.cache_data
    def get_fields(seasonId, farmId, lang, url, access_key_id):
        df = api_call_fields(seasonId, farmId, lang, url, access_key_id)
        return df

    # Llamar a la función get_fields_table que está cacheada
    filtered_df = get_fields(season_seleccionada['id'], farm_seleccionada['id'], lang, url, access_key_id)

    # Convertir la columna 'geometry' de GeoJSON a geometrías de Shapely
    def geojson_to_geometry(geojson_str):
        if geojson_str is not None:
            geojson = json.loads(geojson_str)
            return shape(geojson)
        return None

    filtered_df['geometry'] = filtered_df['geometry'].apply(geojson_to_geometry)

    # Eliminar la columna 'geometry' de GeoJSON ya que ya no es necesaria
    filtered_df = filtered_df.drop('geometryWKB', axis=1, errors='ignore')  # Usamos errors='ignore' para evitar errores si la columna no existe

    # Convertir el DataFrame de Pandas a un GeoDataFrame de GeoPandas
    gdf_poly = gpd.GeoDataFrame(filtered_df, geometry='geometry')

    # Nombres de columnas originales y sus nuevos nombres
    renombrar_columnas = {
        "crop_name": "crop",
        "hybrid_name": "hybrid",
        "has": "hectares",
        "name": "field_name"
    }

    # Filtrar y mantener solo las columnas que necesitan ser renombradas
    columnas_para_renombrar = {orig: nuevo for orig, nuevo in renombrar_columnas.items() if orig in gdf_poly.columns}

    # Renombrar columnas del GeoDataFrame
    gdf_poly = gdf_poly.rename(columns=columnas_para_renombrar)

    ############################################################################

    ############################################################################
    # Mapa
    ############################################################################

    # Organizar los widgets en dos columnas
    col1, col2 = st.columns([3,1])

    # Columna 1: Markdowns
    with col1:
        st.markdown(f"<b>{translate('map_by_field', lang)} </b>", unsafe_allow_html=True)

    # Suponiendo que 'gdf' es tu GeoDataFrame
    total_bounds = gdf_poly.total_bounds  # Retorna algo como (min_x, min_y, max_x, max_y)

    # Calcula el centro de la caja delimitadora
    centro_x = (total_bounds[0] + total_bounds[2]) / 2
    centro_y = (total_bounds[1] + total_bounds[3]) / 2

    # Crear mapa
    m = folium.Map(location=[centro_y, centro_x], zoom_start=13)

    # Crear un grupo de características para la "Capa de lotes"
    capa_de_lotes = FeatureGroup(name="Capa de lotes")

    # Elegir un color único para todas las geometrías
    color = "#3388ff"  # Puedes cambiar este color según prefieras

    for idx, row in gdf_poly.iterrows():
        # Personalizar el contenido del tooltip
        tooltip_content = (
            f"<span style='font-family:Roboto;'>"
            f"Campo: {row['field_name']}<br>"
            f"Cultivo: {row['crop']}<br>"
            f"Variedad/Híbrido: {row['hybrid']}<br>"
            f"Fecha de siembra: {row['crop_date']}<br>"
            f"Hectáreas: {row['hectares']}<br>"
            "</span>"
        )

        # Agregar la geometría al grupo de características con el color único
        folium.GeoJson(
            row.geometry,
            style_function=lambda feature, color=color: {
                "color": 'black',#color,  # Color del borde
                # "fillColor": color,  # Color de relleno
                "weight": 2,
                "fillOpacity": 0
            },
            tooltip=tooltip_content
        ).add_to(capa_de_lotes)

    # Agregar el grupo de características "Capa de lotes" al mapa
    capa_de_lotes.add_to(m)

    # Load the DEM raster file
    infile = "raster_test/dem_completo.tif"

    with rio.open(infile) as src:
        boundary = src.bounds
        img = src.read(1)  # Read the first band
        nodata = src.nodata

    # Replace nodata values with NaN for visualization
    img = np.where(img == nodata, np.nan, img)

    # Define 'RdYlGn' colormap
    colormap = LinearSegmentedColormap.from_list("terrain", plt.cm.terrain(np.linspace(0, 1, 256)))

    def normalize(value):
        """Normalize raster values to (0, 1) for colormap."""
        vmin = np.nanmin(img)
        vmax = np.nanmax(img)
        return (value - vmin) / (vmax - vmin)

    def color_mapper(value):
        """Map normalized value to RGBA color."""
        if np.isnan(value):
            return (0, 0, 0, 0)  # Transparent for NaN values
        return colormap(normalize(value))

    # Add the raster as an image overlay on the Folium map
    folium.raster_layers.ImageOverlay(
        image=img,
        name='DEM',
        opacity=1,
        interactive=True,
        bounds=[[boundary.bottom, boundary.left], [boundary.top, boundary.right]],
        colormap=color_mapper,  # Use the RdYlGn color mapper function
    ).add_to(m)

    from branca.colormap import LinearColormap

    # Define la paleta de colores manualmente (puedes ajustar estos colores según tu preferencia)
    terrain_colors = ['#333399', '#0e7ee4', '#00bc94', '#55dd77', '#c5f38d', '#e4dc8a', '#aa926b', '#8d6d66', '#c5b5b1', '#ffffff']

    # Calcular valores mínimos y máximos para la barra de colores
    vmin, vmax = np.nanmin(img), np.nanmax(img)

    # Definir y agregar la barra de colores al mapa usando la lista de colores definida
    colorbar = LinearColormap(colors=terrain_colors, vmin=vmin, vmax=vmax)
    m.add_child(colorbar)

    # Agrega la capa de teselas de Esri World Imagery y el control de capas
    tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    attr = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    folium.TileLayer(tiles, attr=attr, name='Esri World Imagery', show=True).add_to(m)
    LayerControl(collapsed=True).add_to(m)

    # Mostrar el mapa en Streamlit
    st_folium(m, use_container_width=True)

else:
    st.write('Debe seleccionar un farm para continuar')


############################################################################
# Mapa
############################################################################

# import os
# import leafmap.foliumap as leafmap
# import leafmap.colormaps as cm
# import streamlit as st

# m = leafmap.Map(
#     location=[gdf_poly.geometry.centroid.y.mean(), gdf_poly.geometry.centroid.x.mean()], 
#     zoom_start=14,
#     draw_control=False,
#     measure_control=False,
#     # fullscreen_control=False,
#     attribution_control=True,
# )

# m.add_gdf(gdf_poly, layer_name="Lotes")

# dem = 'dem_completo.tif'
# m.add_raster(dem, colormap="terrain", layer_name="DEM")

# m.to_streamlit()
    
############################################################################
    
