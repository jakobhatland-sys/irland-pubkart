import osmnx as ox
gdf = ox.features_from_place("Ireland", tags={"amenity": "pub"})
gdf["geometry"] = gdf.geometry.centroid   # flater -> punkter
gdf.to_file("puber.gpkg")
