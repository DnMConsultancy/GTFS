import io
import zipfile
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import random
import streamlit as st

def load_gtfs(zip_bytes):
    """
    Lees alle .txt bestanden (GTFS-bestanden) uit de zip en laad ze in een dictionary
    waarbij de sleutel de bestandsnaam is en de waarde een pandas DataFrame.
    """
    data = {}
    with zipfile.ZipFile(zip_bytes, 'r') as z:
        for file in z.namelist():
            if file.endswith('.txt'):
                with z.open(file) as f:
                    data[file] = pd.read_csv(f)
    return data

def visualize_gtfs(data):
    """
    Maak een interactieve kaart met stops als markers (geclusterd) en routes (via shapes) als lijnen.
    """
    stops = data.get("stops.txt")
    shapes = data.get("shapes.txt")
    
    if stops is None:
        st.error("stops.txt niet gevonden in de GTFS-feed.")
        return None
    
    # Bepaal het middelpunt van de kaart op basis van de gemiddelde latitude en longitude
    avg_lat = stops['stop_lat'].mean()
    avg_lon = stops['stop_lon'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8)
    
    # Voeg een MarkerCluster toe voor de stops
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in stops.iterrows():
        folium.Marker(
            location=[row['stop_lat'], row['stop_lon']],
            popup=row.get('stop_name', 'Naam onbekend')
        ).add_to(marker_cluster)
    
    # Teken routes als polyline als shapes aanwezig zijn
    if shapes is not None:
        for shape_id, group in shapes.groupby('shape_id'):
            group_sorted = group.sort_values(by='shape_pt_sequence')
            coords = list(zip(group_sorted['shape_pt_lat'], group_sorted['shape_pt_lon']))
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            folium.PolyLine(coords, color=color, weight=2.5, opacity=1).add_to(m)
    
    return m

def add_virtual_stop(data, new_stop):
    """
    Voeg een nieuwe virtuele halte toe aan de GTFS feed.
    new_stop is een dictionary met de volgende keys:
    stop_id, stop_code, stop_name, stop_lat, stop_lon, location_type,
    parent_station, stop_timezone, wheelchair_boarding, platform_code.
    """
    stops = data.get("stops.txt")
    if stops is None:
        st.error("stops.txt niet gevonden in de feed.")
        return data
    
    # Converteer de nieuwe halte naar een DataFrame
    new_stop_df = pd.DataFrame([new_stop])
    # Voeg de nieuwe halte toe; eventueel ontbrekende kolommen worden toegevoegd
    stops = pd.concat([stops, new_stop_df], ignore_index=True)
    data["stops.txt"] = stops
    st.success("Virtuele halte is toegevoegd!")
    return data

def export_gtfs(data):
    """
    Exporteer alle DataFrames in de data-dictionary naar een nieuw zip-bestand.
    Elk bestand wordt opgeslagen als CSV (met header, geen index).
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as z:
        for filename, df in data.items():
            csv_data = df.to_csv(index=False)
            z.writestr(filename, csv_data)
    buffer.seek(0)
    return buffer

def main():
    st.title("GLIMBLE - GTFS Feed Editor")
    
    # Stap 1: GTFS feed inlezen via een zip bestand
    uploaded_file = st.file_uploader("Upload een GTFS zip bestand", type=["zip"])
    if uploaded_file is not None:
        zip_bytes = io.BytesIO(uploaded_file.read())
        data = load_gtfs(zip_bytes)
        st.session_state['gtfs_data'] = data
        st.success("GTFS feed succesvol ingelezen!")
        
        # Stap 2: Visualisatie van de huidige GTFS feed
        st.header("Visualisatie van de GTFS feed")
        map_obj = visualize_gtfs(data)
        if map_obj:
            # Render de folium kaart in streamlit
            st.components.v1.html(map_obj._repr_html_(), height=600)
        
        # Stap 3: Interactief een virtuele stop toevoegen
        st.header("Virtuele halte toevoegen")
        with st.form("add_stop_form"):
            stop_id = st.text_input("Stop ID")
            stop_code = st.text_input("Stop Code")
            stop_name = st.text_input("Stop Name")
            stop_lat = st.number_input("Stop Latitude", format="%.6f")
            stop_lon = st.number_input("Stop Longitude", format="%.6f")
            location_type = st.text_input("Location Type")
            parent_station = st.text_input("Parent Station")
            stop_timezone = st.text_input("Stop Timezone")
            wheelchair_boarding = st.text_input("Wheelchair Boarding")
            platform_code = st.text_input("Platform Code")
            submitted = st.form_submit_button("Virtuele halte toevoegen")
            
            if submitted:
                new_stop = {
                    'stop_id': stop_id,
                    'stop_code': stop_code,
                    'stop_name': stop_name,
                    'stop_lat': stop_lat,
                    'stop_lon': stop_lon,
                    'location_type': location_type,
                    'parent_station': parent_station,
                    'stop_timezone': stop_timezone,
                    'wheelchair_boarding': wheelchair_boarding,
                    'platform_code': platform_code
                }
                st.session_state['gtfs_data'] = add_virtual_stop(st.session_state['gtfs_data'], new_stop)
                
                # Toon de bijgewerkte kaart
                st.header("Bijgewerkte visualisatie")
                updated_map = visualize_gtfs(st.session_state['gtfs_data'])
                if updated_map:
                    st.components.v1.html(updated_map._repr_html_(), height=600)
        
        # Stap 4: Exporteren van de aangepaste GTFS feed
        st.header("Exporteer GTFS Feed")
        if st.button("Genereer en download nieuwe GTFS zip"):
            export_buffer = export_gtfs(st.session_state['gtfs_data'])
            st.download_button(
                label="Download aangepaste GTFS feed",
                data=export_buffer,
                file_name="new_gtfs_feed.zip",
                mime="application/zip"
            )

if __name__ == "__main__":
    main()