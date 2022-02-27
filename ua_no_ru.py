import time
import csv

import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer

def main():
    for file in ['szpitale_unified.csv', 'community_centre.csv']:
        with open(file, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            row_index = 0

            overpass_query = """
            [out:xml][timeout:2500];
    (
    node(1);
    );
    out body;
    >;
    out skel qt;
    """
            overpass_query_prefix = """[out:xml][timeout:2500];
    ("""
            overpass_query_suffix = """);
    out body;
    >;
    out skel qt;"""
            overpass_query = overpass_query_prefix

            for row in spamreader:
                if row_index == 0:
                    if row[0] != "id":
                        print(file, "id expected", row[0], "arrived")
                        raise
                    if row[1] != "name":
                        print(file, "name expected", row[1], "arrived")
                        raise
                    if row[2] != "name:uk":
                        print(file, "name:uk expected", row[3], "arrived")
                        raise
                else:
                    osm_element_type = row[0].split("/")[0]
                    osm_element_id = row[0].split("/")[1]
                    name = row[1]
                    name_ru = row[2].strip()
                    name_uk = row[3].strip()
                    overpass_query += osm_element_type + "(" + osm_element_id + ");\n"
                row_index += 1
            overpass_query += overpass_query_suffix
            print(overpass_query)

        changeset = build_changeset(False, "dodawanie nazw ukraińskich i rosyjskich (edycje osób które zgodziły się na dystrybucje ich pracy ale edytowały listę nazw a nie bezpośrednio w edytorze OSM)", "https://forum.openstreetmap.org/viewtopic.php?id=75019", "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/name_translation_proxy_ukraine_refugee_crisis")
        with open(file, newline='') as csvfile:
            print("aaa")
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            row_index = 0
            for row in spamreader:
                if row_index == 0:
                    if row[0] != "id":
                        raise
                    if row[1] != "name":
                        raise
                    if row[2] != "name:uk":
                        raise
                else:
                    osm_element_type = row[0].split("/")[0]
                    osm_element_id = row[0].split("/")[1]
                    name = row[1]
                    name_uk = row[2].strip()
                    #print("-------------------")
                    #print(name_uk)
                    #print("-------------------")
                    element = osm_bot_abstraction_layer.get_data(osm_element_id, osm_element_type)
                    #print(element)
                    #print(element["tag"])
                    tags = element["tag"]
                    #print(osm_element_type)
                    if "name" not in tags:
                        print("NAME MISSING!")
                        continue
                    if name != tags["name"]:
                        print("NAME MISMATCH!")
                        print("Translated:")
                        print(name)
                        print()
                        print("in OSM:")
                        print(tags["name"])
                        print()
                        print()
                        print()
                        print()
                        continue
                    if "name:uk" in tags and name_uk != tags["name:uk"]:
                        print("NAME MISMATCH! name:uk")
                        print(name_uk, "vs", tags["name:uk"])
                        continue
                    useful_edit = False
                    if "name:uk" in tags and element["tag"]["name:uk"].strip() == "":
                        useful_edit = True
                        del element["tag"]["name:uk"]
                        print("cleaning empty name! Sorry!")

                    if ("name:uk" not in tags or element["tag"]["name:uk"] != name_uk) and name_uk.strip() != "":
                        element["tag"]["name:uk"] = name_uk
                        useful_edit = True
                    
                    if useful_edit == False:
                        continue

                    osm_bot_abstraction_layer.update_element(changeset, osm_element_type, element)
                    continue
                row_index += 1
        try:
            changeset.ChangesetClose()
        except osmapi.ApiError as e:
            if is_exception_about_already_closed_changeset(e):
                pass
            else:
                raise e



def build_changeset(is_in_manual_mode, changeset_comment, discussion_url, osm_wiki_documentation_page):
    automatic_status = osm_bot_abstraction_layer.manually_reviewed_description()
    if is_in_manual_mode == False:
        automatic_status = osm_bot_abstraction_layer.fully_automated_description()
    comment = changeset_comment
    source = None
    api = osm_bot_abstraction_layer.get_correct_api(automatic_status, discussion_url)
    affected_objects_description = ""
    builder = osm_bot_abstraction_layer.ChangesetBuilder(affected_objects_description, comment, automatic_status, discussion_url, osm_wiki_documentation_page, source)
    builder.create_changeset(api)
    return api

main()