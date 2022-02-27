import time
import csv

import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer

def main():
    for file in ['szpitale.csv', 'pks.csv', 'krew.csv', 'community_centre.csv', 'miasta.csv']: #['miasta_unified.csv']:
        show_overpass_query(file)
        changeset = build_changeset(False, "dodawanie nazw ukraińskich i rosyjskich (edycje osób które zgodziły się na dystrybucje ich pracy ale edytowały listę nazw a nie bezpośrednio w edytorze OSM)", "https://forum.openstreetmap.org/viewtopic.php?id=75019", "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/name_translation_proxy_ukraine_refugee_crisis")
        with open(file, newline='') as csvfile:
            print("aaa")
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            row_index = 0
            matcher = None
            for row in spamreader:
                if row_index == 0:
                    matcher = build_id_to_index_number(row)
                else:
                    osm_element_type = row[matcher["id"]].split("/")[0]
                    osm_element_id = row[matcher["id"]].split("/")[1]
                    name = row[matcher["name"]]
                    name_ru = None
                    if matcher.get("name:ru") != None:
                        name_ru = row[matcher.get("name:ru")]
                    name_uk = None
                    if matcher.get("name:uk") != None:
                        name_uk = row[matcher.get("name:uk")]
                    element = osm_bot_abstraction_layer.get_data(osm_element_id, osm_element_type)
                    tags = element["tag"]
                    if "name" not in tags:
                        print("NAME MISSING!")
                        print("https://www.openstreetmap.org/" + osm_element_type + "/" + osm_element_id)
                        continue
                    if name != tags["name"]:
                        print("https://www.openstreetmap.org/" + osm_element_type + "/" + osm_element_id)
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
                    if name_uk != None:
                        if "name:uk" in tags and name_uk != tags["name:uk"]:
                            print("NAME MISMATCH! name:uk")
                            print(name_uk, "vs", tags["name:uk"])
                            continue
                    if name_ru != None:
                        if "name:ru" in tags and name_ru != tags["name:ru"]:
                            print("NAME MISMATCH! name:ru")
                            print(name_ru, "vs", tags["name:ru"])
                            continue

                    useful_edit = False

                    # may be not needed anymore?
                    if "name:ru" in tags and element["tag"]["name:ru"].strip() == "":
                        useful_edit = True
                        del element["tag"]["name:ru"]
                        print("cleaning empty name! Sorry!")
                    if "name:uk" in tags and element["tag"]["name:uk"].strip() == "":
                        useful_edit = True
                        del element["tag"]["name:uk"]
                        print("cleaning empty name! Sorry!")

                    if name_ru != None and name_ru.strip() != "":
                        if ("name:ru" not in tags or element["tag"]["name:ru"] != name_ru):
                            element["tag"]["name:ru"] = name_ru
                            useful_edit = True
                    if name_uk != None and name_uk.strip() != "":
                        if ("name:uk" not in tags or element["tag"]["name:uk"] != name_uk):
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

def build_id_to_index_number(header_row_array):
    matcher = {}
    for index, column in enumerate(header_row_array):
        if column in ["id", "@id"]:
            matcher["id"] = index
        elif column in "name":
            matcher["name"] = index
        elif column in "name:ru":
            matcher["name:ru"] = index
        elif column in "name:uk":
            matcher["name:uk"] = index
    if "id" not in matcher:
        raise "id missing in header"
    if "name" not in matcher:
        raise "name missing in header"
    if "name:ru" not in matcher and "name:uk" not in matcher:
        raise "neither name:ru nor name:uk present in header"
    if "name:uk" not in matcher:
        raise "name:uk missing in header"
    return matcher

def show_overpass_query(file):
    with open(file, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        row_index = 0

        query_data_rows = ""

        matcher = None
        for row in spamreader:
            if row_index == 0:
                matcher = build_id_to_index_number(row)
            else:
                osm_element_type = row[0].split("/")[0]
                osm_element_id = row[0].split("/")[1]
                query_data_rows += osm_element_type + "(" + osm_element_id + ");\n"
            row_index += 1
        print(overpass_query_builder(query_data_rows))

def overpass_query(query_data_rows):
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
    return overpass_query_prefix + query_data_rows + overpass_query_suffix


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