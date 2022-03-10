import time
import csv

import osm_bot_abstraction_layer.osm_bot_abstraction_layer as osm_bot_abstraction_layer
import osmapi

def is_imprecise_ukrainian_name(name_uk, name):
    if name_uk in ["шкільний комплекс", "професійна школа"]:
        return True
    if name_uk == "Загальноосвітній ліцей" and name.lower() != "liceum ogólnokształcące":
        return True
    if name_uk == "Початкова школа" and name.lower() != "szkoła podstawowa":
        return True
    return False

def main(make_edits):
    report_of_problems = ""
    for file in ["szkoły.csv", 'wioski_przygraniczne.csv', 'urzędy_wojewódzkie.csv', 'miasta.csv']: #'lotniska.csv']: #'krew.csv', 'szpitale.csv', 'pks.csv', 'community_centre.csv', 'miasta.csv']: # 'social_facility_second.csv' 'stacje_kolejowe.csv
        report_of_problems += "\n------\n" + file + "\n"
        changeset = None
        show_overpass_query(file)

        names_uk = []
        names_ru = []
        with open(file, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            row_index = 0
            for row in spamreader:
                if row_index == 0:
                    matcher = build_id_to_index_number(row)
                else:
                    name_uk = None
                    name_ru = None
                    name = row[matcher.get("name")]
                    if matcher.get("name:uk") != None:
                        name_uk = row[matcher.get("name:uk")].replace(" (місто)", "") # drop "(city) explanation"
                    if matcher.get("name:ru") != None:
                        name_ru = row[matcher.get("name:ru")].replace(" (Польша)", "") # drop "(city) explanation"
                    if name_ru in names_ru and name_ru != None:
                        print("REPEATING", name_ru)
                    if name_uk in names_uk and name_uk != None:
                        if is_imprecise_ukrainian_name(name_uk, name) == False:
                            print("REPEATING", name_uk, "FOR", name)
                    if name_ru != None:
                        names_ru.append(name_ru)
                    if name_uk != None:
                        names_uk.append(name_uk)
                row_index += 1
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
                        name_ru = row[matcher.get("name:ru")].replace(" (Польша)", "") # drop "(city) explanation"
                    name_uk = None
                    if matcher.get("name:uk") != None:
                        name_uk = row[matcher.get("name:uk")].replace(" (місто)", "") # drop "(city) explanation"
                    if name_uk in ["Сувчина" # https://www.openstreetmap.org/node/31948375
                        "Стубно", # https://www.openstreetmap.org/node/31948515 
                        "Клецко", # https://www.openstreetmap.org/node/563338229
                        ]:
                        name_uk = None
                    
                    if is_imprecise_ukrainian_name(name_uk, name):
                        error = "SKIPPING IMPRECISE NAME ( " + link + " )!\n"
                        if name_uk != None:
                            error += "Provided Ukrainian name:\n" + name_uk.strip() + "\n"
                        else:
                            error += "No provided Ukrainian name"
                        if name_ru:
                            error += "Provided Russian name:\n" + name_ru.strip() + "\n"
                        else:
                            error += "No provided Russian name"
                        report_of_problems += error
                        print(error + "\n")
                        name_uk = None
                    element = osm_bot_abstraction_layer.get_data(osm_element_id, osm_element_type)
                    if element == None:
                        error = "NO ELEMENT AT ALL ( " + link + " )!\n"
                        report_of_problems += error
                        print(error + "\n")
                        skip_edit = True
                        continue # no need to check anything else
                    if "tag" not in element:
                        error = "NO TAGS AT ALL ( " + link + " )!\n"
                        report_of_problems += error
                        print(error + "\n")
                        skip_edit = True
                        continue # no need to check anything else
                    tags = element["tag"]

                    skip_edit = False
                    link = "https://www.openstreetmap.org/" + osm_element_type + "/" + osm_element_id
                    if "name" not in tags:
                        error = "NAME MISSING ( " + link + " )!\n"
                        if name_uk != None:
                            error += "Provided Ukrainian name:\n" + name_uk.strip() + "\n"
                        else:
                            error += "No provided Ukrainian name"
                        if name_ru:
                            error += "Provided Russian name:\n" + name_ru.strip() + "\n"
                        else:
                            error += "No provided Russian name"
                        report_of_problems += error
                        print(error + "\n")
                        skip_edit = True
                    elif name != tags["name"]:
                        expanded_name = tags["name"]
                        if "RCKiK" in tags["name"]:
                            expanded_name = expanded_name.replace("RCKiK", "Regionalne Centrum Krwiodawstwa i Krwiolecznictwa")
                            expanded_name = expanded_name.replace("TO", "Oddział Terenowy")
                            expanded_name = expanded_name.replace("OT", "Oddział Terenowy")
                        if "WCKiK" in tags["name"]:
                            expanded_name = expanded_name.replace("WCKiK", "Wojskowe Centrum Krwiodawstwa i Krwiolecznictwa")

                        if name != expanded_name:
                            error = "NAME MISMATCH ( " + link + " )!\n"
                            error += "Being translated:\n" + name + "\n"
                            error += "In OSM:\n" + tags["name"] + "\n"
                            error += "expanded_name:\n" + expanded_name + "\n"
                            if name_uk != None:
                                error += "Provided Ukrainian name:\n" + name_uk.strip() + "\n"
                            else:
                                error += "No provided Ukrainian name"
                            if name_ru:
                                error += "Provided Russian name:\n" + name_ru.strip() + "\n"
                            else:
                                error += "No provided Russian name"

                            report_of_problems += error
                            print(error + "\n")
                            skip_edit = True
                    if name_uk != None:
                        if "name:uk" in tags and name_uk.strip() != tags["name:uk"].strip():
                            error = "UKRAINIAN NAME MISMATCH ( " + link + " )!\n"
                            error += "Provided:\n" + name_uk.strip() + "\n"
                            error += "In OSM:\n" + tags["name:uk"].strip() + "\n"
                            error += "Translated:\n" + tags["name"] + "\n"
                            if name_uk != None:
                                error += "Provided Ukrainian name:\n" + name_uk.strip() + "\n"
                            else:
                                error += "No provided Ukrainian name"
                            if name_ru:
                                error += "Provided Russian name:\n" + name_ru.strip() + "\n"
                            else:
                                error += "No provided Russian name"

                            report_of_problems += error
                            print(error + "\n")
                            skip_edit = True
                    if name_ru != None:
                        if "name:ru" in tags and name_ru.strip() != tags["name:ru"].strip():
                            error = "RUSSIAN NAME MISMATCH ( " + link + " )!\n"
                            error += "Provided:\n" + name_ru.strip() + "\n"
                            error += "In OSM:\n" + tags["name:ru"].strip() + "\n"
                            error += "Translated:\n" + tags["name"] + "\n"
                            if name_uk != None:
                                error += "Provided Ukrainian name:\n" + name_uk.strip() + "\n"
                            else:
                                error += "No provided Ukrainian name"
                            if name_ru:
                                error += "Provided Russian name:\n" + name_ru.strip() + "\n"
                            else:
                                error += "No provided Russian name"

                            report_of_problems += error
                            print(error + "\n")
                            skip_edit = True

                    if make_edits == False or skip_edit:
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
                        if ("name:ru" not in tags or element["tag"]["name:ru"] != name_ru.strip()):
                            element["tag"]["name:ru"] = name_ru.strip()
                            useful_edit = True
                    if name_uk != None and name_uk.strip() != "":
                        if ("name:uk" not in tags or element["tag"]["name:uk"] != name_uk.strip()):
                            element["tag"]["name:uk"] = name_uk.strip()
                            useful_edit = True

                    if useful_edit == False:
                        continue

                    if changeset == None:
                        description = "dodawanie nazw ukraińskich i rosyjskich (edycje osób które zgodziły się na dystrybucje ich pracy ale edytowały listę nazw a nie bezpośrednio w edytorze OSM)"
                        description += " - " + file.replace("_", " ").replace(".csv", "")
                        changeset = build_changeset(False, description, "https://forum.openstreetmap.org/viewtopic.php?id=75019", "https://wiki.openstreetmap.org/wiki/Mechanical_Edits/Mateusz_Konieczny_-_bot_account/name_translation_proxy_ukraine_refugee_crisis")
                    osm_bot_abstraction_layer.update_element(changeset, osm_element_type, element)
                row_index += 1
        try:
            if make_edits and changeset != None:
                changeset.ChangesetClose()
        except osmapi.ApiError as e:
            if is_exception_about_already_closed_changeset(e):
                pass
            else:
                raise e
    print(report_of_problems)

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

def overpass_query_builder(query_data_rows):
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

main(make_edits=True)