
import streamlit as st
import pandas as pd
import zipfile

def main():
    st.title("Interactieve GTFS Feed Inlezer")
    st.write("Upload een GTFS .zip bestand om de inhoud te verkennen.")

    # Upload widget voor .zip bestanden
    uploaded_file = st.file_uploader("Kies een GTFS .zip bestand", type=["zip"])

    if uploaded_file is not None:
        try:
            # Open de geüploade zipfile
            with zipfile.ZipFile(uploaded_file) as z:
                file_names = z.namelist()
                st.success("GTFS feed succesvol ingelezen!")
                st.write("Bestanden in de feed:")
                st.write(file_names)

                # --- Bestaande functionaliteit voor een willekeurig bestand ---
                file_choice = st.selectbox("Kies een bestand om te bekijken", file_names)
                if file_choice:
                    with z.open(file_choice) as f:
                        try:
                            df = pd.read_csv(f)
                            
                            # Verwerking voor calendar_dates.txt
                            if file_choice == "calendar_dates.txt" and 'date' in df.columns:
                                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                                st.info("De 'date' kolom is geformatteerd naar datetime objecten.")
                            
                            # Verwerking voor feed_info.txt
                            if file_choice == "feed_info.txt":
                                if 'feed_start_date' in df.columns:
                                    df['feed_start_date'] = pd.to_datetime(df['feed_start_date'], format='%Y%m%d')
                                if 'feed_end_date' in df.columns:
                                    df['feed_end_date'] = pd.to_datetime(df['feed_end_date'], format='%Y%m%d')
                                st.info("De kolommen 'feed_start_date' en 'feed_end_date' zijn geformatteerd naar datetime objecten.")

                            st.write(f"Voorbeeld van '{file_choice}':")
                            st.dataframe(df.head())
                        except Exception as e:
                            st.error(f"Fout bij het inlezen van '{file_choice}': {e}")

                st.markdown("---")
                st.header("Nieuwe Stop Toevoegen aan een Route")

                # Controleer of de vereiste bestanden aanwezig zijn
                required_files = ["routes.txt", "trips.txt", "stop_times.txt", "stops.txt"]
                missing_files = [f for f in required_files if f not in file_names]
                if missing_files:
                    st.error(f"De volgende vereiste bestanden ontbreken in de GTFS-feed: {', '.join(missing_files)}")
                else:
                    # Lees de vereiste bestanden in als DataFrames
                    with z.open("routes.txt") as f:
                        df_routes = pd.read_csv(f)
                    with z.open("trips.txt") as f:
                        df_trips = pd.read_csv(f)
                    with z.open("stop_times.txt") as f:
                        df_stop_times = pd.read_csv(f)
                    with z.open("stops.txt") as f:
                        df_stops = pd.read_csv(f)

                    # --- Stap 1: Route selectie ---
                    unique_route_ids = sorted(df_routes['route_id'].unique())
                    selected_route = st.selectbox("Selecteer een route_id", unique_route_ids)
                    if selected_route:
                        # Filter routes.txt en trips.txt op de geselecteerde route_id
                        filtered_routes = df_routes[df_routes['route_id'] == selected_route]
                        filtered_trips = df_trips[df_trips['route_id'] == selected_route]
                        
                        st.subheader("Routes voor de geselecteerde route_id")
                        st.dataframe(filtered_routes)
                        
                        st.subheader("Trips voor de geselecteerde route_id")
                        st.dataframe(filtered_trips)

                        # --- Stap 2: Trip selectie ---
                        unique_trip_ids = sorted(filtered_trips['trip_id'].unique())
                        selected_trip = st.selectbox("Selecteer een trip_id", unique_trip_ids)
                        if selected_trip:
                            # Filter stop_times.txt voor de geselecteerde trip_id
                            filtered_stop_times = df_stop_times[df_stop_times['trip_id'] == selected_trip]
                            st.subheader("Stop Times voor de geselecteerde trip_id")
                            st.dataframe(filtered_stop_times)

                            # --- Stap 3: Toon bijbehorende stops ---
                            # Zorg dat stop_id in beide DataFrames hetzelfde type is (string)
                            df_stops['stop_id'] = df_stops['stop_id'].astype(str)
                            filtered_stop_times['stop_id'] = filtered_stop_times['stop_id'].astype(str)
                            
                            # Haal de unieke stop_id's op en filter stops.txt
                            stop_ids = filtered_stop_times['stop_id'].unique()
                            filtered_stops = df_stops[df_stops['stop_id'].isin(stop_ids)]
                            st.subheader("Stops behorende bij de geselecteerde trip_id")
                            st.dataframe(filtered_stops)

                            # --- Extra: Interactief een nieuwe stop toevoegen ---
                            st.markdown("### Voeg een nieuwe stop toe")
                            new_stop_id   = st.text_input("Nieuwe stop ID")
                            new_stop_name = st.text_input("Nieuwe stop naam")
                            new_stop_lat  = st.text_input("Nieuwe stop latitude")
                            new_stop_lon  = st.text_input("Nieuwe stop longitude")
                            
                            # Selecteer de bestaande stop na welke de nieuwe stop moet worden ingevoegd
                            insertion_stop = st.selectbox(
                                "Selecteer de stop na welke de nieuwe stop moet worden ingevoegd",
                                filtered_stops['stop_id']
                            )
                            
                            if st.button("Nieuwe stop toevoegen"):
                                if not (new_stop_id and new_stop_name and new_stop_lat and new_stop_lon):
                                    st.error("Vul alle nieuwe stopgegevens in.")
                                else:
                                    # Hier kun je de logica toevoegen om de nieuwe stop in de data te verwerken.
                                    # Voor demonstratiedoeleinden voegen we de nieuwe stop toe aan de gefilterde stops DataFrame.
                                    new_stop = {
                                        "stop_id": new_stop_id,
                                        "stop_name": new_stop_name,
                                        "stop_lat": new_stop_lat,
                                        "stop_lon": new_stop_lon
                                    }
                                    # Voeg de nieuwe stop toe aan de bestaande DataFrame
                                    updated_stops = filtered_stops.append(new_stop, ignore_index=True)
                                    st.success(f"Nieuwe stop toegevoegd na stop {insertion_stop}!")
                                    st.dataframe(updated_stops)

        except zipfile.BadZipFile:
            st.error("Het geüploade bestand is geen geldig zipbestand.")

if __name__ == '__main__':
    main()
