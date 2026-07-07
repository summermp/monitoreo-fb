import json
import pandas as pd
import streamlit as st
from apify_client import ApifyClient
from datetime import datetime
import time

st.set_page_config(
    page_title="Facebook Comments",
    page_icon="💬",
    initial_sidebar_state="expanded",
    layout="wide"
)

# Secrets
client = ApifyClient(st.secrets["APIFY_API_TOKEN"])
actor_id = st.secrets["APIFY_ACTOR_COMMENTS_ID"]
face_post_url = st.secrets["LAST_FACE_POST"]

# Inicializar estado de sesión
if 'comments_data' not in st.session_state:
    st.session_state.comments_data = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""

def format_fecha(fecha_str):
    """Formatear fecha de ISO a dd/mm/yy hh:mm:ss"""
    try:
        dt = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%y %H:%M:%S')
    except:
        return fecha_str

def reordenar_columnas(df):
    """Función para reordenar las columnas del DataFrame"""
    # Definir el orden deseado de las columnas
    orden_columnas = [
        "Foto",
        "Url user",
        "Usuario",
        "Comentario",
        "Fecha",
        "Likes",
        "Título publicación",
        "Link"
    ]
    
    # Obtener las columnas que existen en el DataFrame
    columnas_existentes = [col for col in orden_columnas if col in df.columns]
    
    # Obtener las columnas que no están en el orden definido
    columnas_restantes = [col for col in df.columns if col not in orden_columnas]
    
    # Combinar: primero las columnas en orden, luego las que sobran
    nuevo_orden = columnas_existentes + columnas_restantes
    
    return df[nuevo_orden]

def fetch_comments():
    """Función para obtener comentarios de Apify"""
    st.session_state.is_loading = True
    
    run_input = {
        "startUrls": [{"url": face_post_url}],
        "resultsLimit": 100,
        "includeNestedComments": True,
        "viewOption": "RANKED_UNFILTERED",
        "onlyCommentsNewerThan": "2026-06-01",
    }
    
    try:
        with st.spinner("🔄 Obteniendo comentarios de Facebook..."):
            run = client.actor(actor_id).call(run_input=run_input)
            items = list(client.dataset(run.default_dataset_id).iterate_items())
        
        # Guardar en JSON (cache)
        with open("comments.json", "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
        
        # Procesar datos
        df = pd.DataFrame(items)
        
        # Eliminar columnas innecesarias
        eliminar_cols = ["facebookUrl", "commentId", "id", "feedbackId", "profileId", 
                        "facebookId", "threadingDepth", "pageAdLibrary", "likesCount", "inputUrl", "attachments"]
        df = df.drop(columns=eliminar_cols, errors="ignore")
        
        # Formatear fecha
        if 'date' in df.columns:
            df['date'] = df['date'].apply(format_fecha)
        
        # Renombrar columnas
        df.rename(
            columns={
                "commentUrl": "Link",
                "text": "Comentario",
                "date": "Fecha",
                "profileName": "Usuario",
                "profilePicture": "Foto",
                "profileUrl": "Url user",
                "postTitle": "Título publicación",
            },
            inplace=True
        )
        
        # Reordenar columnas
        df = reordenar_columnas(df)
        
        # Guardar en session state
        st.session_state.comments_data = df
        st.session_state.last_update = datetime.now().strftime('%d/%m/%y %H:%M:%S')
        st.session_state.is_loading = False
        
        st.success(f"✅ {len(df)} comentarios cargados exitosamente!")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Error al obtener comentarios: {str(e)}")
        st.session_state.is_loading = False

def load_from_cache(post_url):
    """Cargar datos desde el archivo JSON cache"""
    try:
        with open("comments.json", "r", encoding="utf-8") as f:
            items = json.load(f)
        
        df = pd.DataFrame(items)

        primer_url = df["facebookUrl"].iloc[0]

        if post_url == primer_url:
            print(post_url)
            print(primer_url)
            # Eliminar columnas innecesarias
            eliminar_cols = ["facebookUrl", "commentId", "id", "feedbackId", "profileId", 
                            "facebookId", "threadingDepth", "pageAdLibrary", "likesCount", "inputUrl", "attachments"]
            df = df.drop(columns=eliminar_cols, errors="ignore")
            
            # Formatear fecha
            if 'date' in df.columns:
                df['date'] = df['date'].apply(format_fecha)
            
            # Renombrar columnas
            df.rename(
                columns={
                    "commentUrl": "Link",
                    "text": "Comentario",
                    "date": "Fecha",
                    "profileName": "Usuario",
                    "profilePicture": "Foto",
                    "profileUrl": "Url user",
                    "postTitle": "Título publicación",
                },
                inplace=True
            )
            
            # Reordenar columnas
            df = reordenar_columnas(df)
            
            st.session_state.comments_data = df
            st.session_state.last_update = "Cargado datos desde archivo local"

            col1, col2, col3 = st.columns([2, 2, 2])

            with col1:
                st.write("")

            with col2:
                st.write("")
                # if st.button("🔄 Obtener comentarios", use_container_width=True, disabled=st.session_state.is_loading):
                    # fetch_comments()  # Descomentado para que funcione
                    # pass

            with col3:
                st.write("")

            # Mostrar información de caché
            if st.session_state.last_update:
                st.text(f"📅 Última actualización: {st.session_state.last_update}")
                # pass

            # Intentar cargar desde caché si no hay datos
            if st.session_state.comments_data is None:
                if load_from_cache():
                    pass
                    # st.info("📁 Datos cargados desde caché local")  # Descomentado para mostrar mensaje

            # Si hay datos, mostrar el buscador y la tabla
            if st.session_state.comments_data is not None:
                df = st.session_state.comments_data.copy()
                
                # Crear columnas para el search input y botón limpiar
                cols1, cols2, cols3 = st.columns([2, 4, 2])
                
                with cols1:
                    st.write("")
                
                with cols2:
                    search_term = st.text_input(
                        "Buscar usuario",
                        key="search_term_input",  # Cambiado el key para evitar conflictos
                        placeholder="Escribe el nombre del usuario... (dejar vacío para mostrar todos)",
                        label_visibility="collapsed"
                    )
                    st.session_state.search_term = search_term
                
                with cols3:
                    st.write("")

                # Aplicar filtro según el término de búsqueda
                if st.session_state.search_term and st.session_state.search_term.strip():
                    # Filtrar por usuario (búsqueda parcial, insensible a mayúsculas)
                    df_filtered = df[df['Usuario'].str.contains(st.session_state.search_term, case=False, na=False)]
                    st.write(f"Mostrando {len(df_filtered)} resultado(s) para **'{st.session_state.search_term}'**")  # Descomentado
                else:
                    # Mostrar todos los datos
                    df_filtered = df
                    st.text(f"Mostrando {len(df_filtered)} comentarios")  # Descomentado
                
                # Configurar columnas de Streamlit
                column_config = {}
                
                for col in df_filtered.columns:
                    if df_filtered[col].dropna().empty:
                        continue
                    
                    sample = df_filtered[col].dropna().astype(str)
                    
                    # Verificar si la columna contiene URLs
                    if not sample.empty and sample.str.startswith(("http://", "https://")).all():
                        if col == "Foto":
                            column_config[col] = st.column_config.ImageColumn(
                                label=col,
                                help="Foto de perfil"
                            )
                        else:
                            column_config[col] = st.column_config.LinkColumn(
                                label=col,
                                display_text="Abrir"
                            )
                
                # Mostrar dataframe
                st.dataframe(
                    df_filtered,
                    width="stretch",
                    hide_index=True,
                    column_config=column_config
                )

            else:
                st.warning("⚠️ No hay datos disponibles. Haz clic en 'Obtener comentarios' para cargarlos.")
                
                # Botón de carga inicial más visible
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🚀 Cargar comentarios", use_container_width=True, type="primary"):
                        # fetch_comments()  # Descomentado para que funcione
                        pass

            return True
        else:
            st.write('No se encontraron datos para esta publicacion')
    except:
        return False

#Codigo para posts
df_posts = pd.read_csv("2026-07-06T16-13_export POSTS.csv")
del_col = ['postId','facebookUrl', 'pageName', 'timestamp', 'user', 'topReactionsCount','reactionLikeCount','reactionLoveCount','reactionHahaCount', 'collaborators','feedbackId', 'paidPartnership', 'topComments','topLevelUrl', 'facebookId', 'pageAdLibrary', 'inputUrl', 'timeCreated', 'timestampCreated','textReferences','reactionCareCount', 'media','viewsCount', 'videoPostViewCount', 'liveViewerCount','reactionWowCount', 'sharedPost']
# Eliminar columnas
df_posts = df_posts.drop(columns=del_col)

# Renombrar columnas
df_posts = df_posts.rename(columns={'time':'Fecha','text':'Publicación','comments': 'Comentarios', 'shares': 'Compartido', 'isVideo':'Video'})

# Convertir time a formato dd/mm/yy hh:mm:ss
df_posts['Fecha'] = pd.to_datetime(df_posts['Fecha']).dt.strftime('%d/%m/%y %H:%M:%S')

# Configurar columna url como LinkColumn
column_config = {
    "url": st.column_config.LinkColumn("URL", display_text="Abrir", width=30)
}

df_posts["Fecha"] = pd.to_datetime(
    df_posts["Fecha"],
    format="%d/%m/%y %H:%M:%S"
)

# Selector de fecha
# fecha = st.date_input("Filtrar por fecha")
# st.write(fecha)

# df_filtrado = df_posts[
#     df_posts["Fecha"].dt.normalize() == pd.Timestamp(fecha)
# ]

post_to_show = ''
event = st.dataframe(df_posts, column_config=column_config, width='stretch', selection_mode = 'single-row', on_select="rerun")
# event = st.dataframe(df_filtrado, column_config=column_config, width='stretch', selection_mode = 'single-row', on_select="rerun")
 
if event.selection.rows:
    indice = event.selection.rows[0]
    post_to_show = df_posts.iloc[indice]["url"]
    load_from_cache(post_to_show)
    post_to_show = ''
