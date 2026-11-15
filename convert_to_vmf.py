import json
import os

def make_box_solid(solid_id, min_x, min_y, min_z, max_x, max_y, max_z, mat):
    s = f"""\tsolid
\t{{
\t\t"id" "{solid_id}"
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+1}"
\t\t\t"plane" "({min_x} {min_y} {max_z}) ({min_x} {max_y} {max_z}) ({max_x} {max_y} {max_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[1 0 0 0] 0.25"
\t\t\t"vaxis" "[0 -1 0 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+2}"
\t\t\t"plane" "({min_x} {max_y} {min_z}) ({min_x} {min_y} {min_z}) ({max_x} {min_y} {min_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[1 0 0 0] 0.25"
\t\t\t"vaxis" "[0 -1 0 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+3}"
\t\t\t"plane" "({min_x} {min_y} {min_z}) ({min_x} {min_y} {max_z}) ({max_x} {min_y} {max_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[1 0 0 0] 0.25"
\t\t\t"vaxis" "[0 0 -1 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+4}"
\t\t\t"plane" "({max_x} {max_y} {min_z}) ({max_x} {max_y} {max_z}) ({min_x} {max_y} {max_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[-1 0 0 0] 0.25"
\t\t\t"vaxis" "[0 0 -1 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+5}"
\t\t\t"plane" "({min_x} {max_y} {min_z}) ({min_x} {max_y} {max_z}) ({min_x} {min_y} {max_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[0 1 0 0] 0.25"
\t\t\t"vaxis" "[0 0 -1 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\tside
\t\t{{
\t\t\t"id" "{solid_id*10+6}"
\t\t\t"plane" "({max_x} {min_y} {min_z}) ({max_x} {min_y} {max_z}) ({max_x} {max_y} {max_z})"
\t\t\t"material" "{mat}"
\t\t\t"uaxis" "[0 -1 0 0] 0.25"
\t\t\t"vaxis" "[0 0 -1 0] 0.25"
\t\t\t"rotation" "0"
\t\t\t"lightmapscale" "16"
\t\t\t"smoothing_groups" "0"
\t\t}}
\t\t"editor"
\t\t{{
\t\t\t"color" "0 180 255"
\t\t\t"visgroupshown" "1"
\t\t\t"visgroupautoshown" "1"
\t\t}}
\t}}"""
    return s

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    custom_maps_path = os.path.join(root, "custom_maps.json")
    with open(custom_maps_path, "r", encoding="utf-8") as f:
        custom_maps = json.load(f)

    m_data = custom_maps["MainCity2"]
    grid = m_data["grid"]
    rows = len(grid)
    cols = len(grid[0])
    tile_sz = 256

    solids = []
    solid_id = 1

    # Base ground plane
    floor = make_box_solid(solid_id, 0, 0, -32, cols * tile_sz, rows * tile_sz, 0, "CONCRETE/CONCRETEFLOOR014A")
    solids.append(floor)
    solid_id += 1

    mat_map = {
        1: ("BUILDING_TEMPLATE/BUILDING_TEMPLATE011G", 1024),
        2: ("BUILDING_TEMPLATE/BUILDING_TEMPLATE011C", 1536),
        3: ("BUILDING_TEMPLATE/BUILDING_TEMPLATE005B", 768),
        4: ("BRICK/BRICKWALL014A", 512),
        5: ("BUILDING_TEMPLATE/BUILDING_TEMPLATE002B", 1280),
        6: ("METAL/METALDOOR018A", 256),
        7: ("NATURE/WATER_CANAL_CHEAP", 64),
    }

    for r in range(rows):
        for c in range(cols):
            val = grid[r][c]
            if val in mat_map:
                mat, h = mat_map[val]
                x1 = c * tile_sz
                y1 = r * tile_sz
                x2 = (c + 1) * tile_sz
                y2 = (r + 1) * tile_sz
                z1 = 0 if val != 7 else -64
                z2 = h if val != 7 else 0
                solids.append(make_box_solid(solid_id, x1, y1, z1, x2, y2, z2, mat))
                solid_id += 1

    solids_str = "\n".join(solids)
    vmf_content = f"""versioninfo
{{
\t"editorversion" "400"
\t"editorbuild" "8864"
\t"mapversion" "1"
\t"formatversion" "100"
\t"prefab" "0"
}}
viewsettings
{{
\t"bShow3DGrid" "1"
\t"nGridSpacing" "64"
\t"bShowGrid" "1"
}}
world
{{
\t"id" "1"
\t"mapversion" "1"
\t"classname" "worldspawn"
\t"skyname" "sky_c17_01"
\t"maxpropscreenwidth" "-1"
\t"detailvbsp" "detail.vbsp"
\t"detailmaterial" "detail/detailsprites"
{solids_str}
}}
entity
{{
\t"id" "9901"
\t"classname" "info_player_start"
\t"angles" "0 90 0"
\t"origin" "{12 * tile_sz} {12 * tile_sz} 32"
}}
entity
{{
\t"id" "9902"
\t"classname" "light_environment"
\t"_ambient" "150 180 200 20"
\t"_light" "255 240 210 200"
\t"angles" "0 45 0"
\t"pitch" "-45"
\t"origin" "{12 * tile_sz} {12 * tile_sz} 512"
}}
entity
{{
\t"id" "9903"
\t"classname" "env_sun"
\t"angles" "0 45 0"
\t"pitch" "-45"
\t"size" "16"
\t"sun_color" "255 240 210"
\t"origin" "{12 * tile_sz} {12 * tile_sz} 576"
}}
"""
    out_dir = os.path.join(root, "source_engine", "maps")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "MainCity2.vmf")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(vmf_content)

    print(f"Successfully generated {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")

if __name__ == "__main__":
    main()

