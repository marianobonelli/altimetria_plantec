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
from helper import translate, api_call_logo, api_call_fields

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

##################### API Lotes #####################

# Función para realizar la llamada a la API y cachear la respuesta
@st.cache_data
def get_fields(user_info, url, access_key_id):
    df = api_call_fields(user_info, url, access_key_id)
    return df

# Llamar a la función get_fields_table que está cacheada
filtered_df = get_fields(user_info, url, access_key_id)

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
############################################################################

############################################################################
# Mapa
############################################################################

# Organizar los widgets en dos columnas
col1, col2 = st.columns([3,1])

# Columna 1: Markdowns
with col1:
    st.markdown('')
    st.markdown('')
    st.markdown(f"<b>{translate('map_by_field', lang)} </b>", unsafe_allow_html=True)

st.markdown('Lote de interés: Divisa Fernando')

# Crear mapa
m = folium.Map(location=[gdf_poly.geometry.centroid.y.mean(), gdf_poly.geometry.centroid.x.mean()], zoom_start=14)

# Generar una paleta de colores
colors = list(mcolors.TABLEAU_COLORS.values())  # Usar una paleta predefinida de matplotlib, o elegir otra
color_dict = {name: colors[i % len(colors)] for i, name in enumerate(gdf_poly['field_name'].unique())}

# Preparar los datos para los grupos de características, respetando el orden
feature_groups = {name: FeatureGroup(name=str(name)) for name in gdf_poly['field_name'].unique()}

for idx, row in gdf_poly.iterrows():
    # Personalizar el contenido del tooltip
    tooltip_content = (
        f"<span style='font-family:Roboto;'>"
        f"{translate('field', lang)}: {row['field_name']}<br>"
        f"{translate('crop', lang)}: {row['crop']}<br>"
        f"{translate('hybrid_variety', lang)}: {row['hybrid']}<br>"
        f"{translate('seeding_date', lang)}: {row['crop_date']}<br>"
        f"{translate('hectares', lang)}: {row['hectares']}<br>"
        "</span>"
    )

    # Asignar un color basado en 'field_name'
    color = color_dict[row['field_name']]

    folium.GeoJson(
        row.geometry,
        style_function=lambda feature, color=color: {
            "color": color,  # Color del borde
            "fillColor": color,  # Color de relleno
            "weight": 2,
            "fillOpacity": 0.6
        },
        tooltip=tooltip_content
    ).add_to(feature_groups[row['field_name']])

# Agregar los grupos de características al mapa en el orden correcto
for name in gdf_poly['field_name'].unique():
    feature_groups[name].add_to(m)

# Agrega la capa de teselas de Esri World Imagery y el control de capas
tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
attr = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
folium.TileLayer(tiles, attr=attr, name='Esri World Imagery', show=True).add_to(m)
LayerControl(collapsed=True).add_to(m)

# Mostrar el mapa en Streamlit
st_folium(m, use_container_width=True)
