import pystache
import pprint
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.system

f = ifcopenshell.open("/home/dion/basix.ifc")

site = None
for element in f.by_type("IfcSite"):
    site = element
    break

building = None
for element in f.by_type("IfcBuilding"):
    building = element
    break


def get_project_address():
    result = []
    if pset := ifcopenshell.util.element.get_pset(site, "Pset_Address"):
        for name in ["Town", "PostalCode", "Region", "Country"]:
            if value := pset.get(name):
                result.append(value)
    return ", ".join(result)


def get_plan_type():
    pset_name = "Pset_LandRegistration"
    if f.schema in ("IFC2X3", "IFC4"):
        pset_name = "e" + pset_name
    land_title = ifcopenshell.util.element.get_pset(site, pset_name, "LandTitleID") or ""
    return "SP" if land_title.startswith("SP") else "DP"


def get_lot_section_plan():
    pset_name = "Pset_LandRegistration"
    if f.schema in ("IFC2X3", "IFC4"):
        pset_name = "e" + pset_name
    plan = ifcopenshell.util.element.get_pset(site, pset_name, "LandTitleID") or "-"
    lot = ifcopenshell.util.element.get_pset(site, "bSA_Site", "LotNumber") or "-"
    section = ifcopenshell.util.element.get_pset(site, "bSA_Site", "SectionNumber") or "-"
    return f"{lot}/{section}/{plan}"


def get_project_type():
    return ifcopenshell.util.element.get_pset(building, "bSA_BASIX", "ProjectType") or ""


def get_total_bedrooms():
    return len([e for e in f.by_type("IfcSpace") if ifcopenshell.util.element.get_predefined_type(e) == "BEDROOM"])


def is_secondary_dwelling():
    return bool(ifcopenshell.util.element.get_pset(building, "bSA_BASIX", "IsSecondaryDwelling"))


def site_area():
    return ifcopenshell.util.element.get_pset(site, "Qto_SiteBaseQuantities", "GrossArea") or 0


def roof_area():
    return sum(
        (ifcopenshell.util.element.get_pset(e, "Qto_RoofBaseQuantities", "ProjectedArea") or 0)
        for e in f.by_type("IfcRoof")
    )


def total_storeys():
    return len(f.by_type("IfcBuildingStorey"))


def total_zone_area(name):
    total = 0
    for zone in f.by_type("IfcZone"):
        if zone.Name != name:
            continue
        for e in ifcopenshell.util.system.get_system_elements(zone):
            if not e.is_a("IfcSpace"):
                continue
            total += ifcopenshell.util.element.get_pset(e, "Qto_SpaceBaseQuantities", "GrossFloorArea") or 0
    return total


def conditioned_floor_area():
    return total_zone_area("Conditioned Floor Area")


def unconditioned_floor_area():
    return total_zone_area("Unconditioned Floor Area")


def garage_floor_area():
    return total_zone_area("Garage Floor Area")


def mezzanine_floor_area():
    return total_zone_area("Mezzanine Floor Area")


def has_swimming_pool():
    for e in f.by_type("IfcSanitaryTerminalType"):
        if (
            ifcopenshell.util.element.get_predefined_type(e) == "BATH"
            and ifcopenshell.util.element.get_pset(e, "Pset_SanitaryTerminalTypeBath", "BathType") == "POOL"
        ):
            return True
    return False


def has_outdoor_spa():
    for e in f.by_type("IfcSanitaryTerminal"):
        if (
            ifcopenshell.util.element.get_predefined_type(e) == "BATH"
            and ifcopenshell.util.element.get_pset(e, "Pset_SanitaryTerminalTypeBath", "BathType") == ["SPA"]
            and not ifcopenshell.util.element.get_container(e, ifc_class="IfcBuilding")
        ):
            return True
    return False



data = {
    "project_address": get_project_address(),
    "project_name": f.by_type("IfcProject")[0].LongName or "",
    "plan_type": get_plan_type(),
    "lot_section_plan": get_lot_section_plan(),
    "project_type": get_project_type(),
    "total_bedrooms": get_total_bedrooms(),
    "is_secondary_dwelling": is_secondary_dwelling(),
    "site_area": site_area(),
    "roof_area": roof_area(),
    "total_storeys": total_storeys(),
    "conditioned_floor_area": conditioned_floor_area(),
    "unconditioned_floor_area": unconditioned_floor_area(),
    "garage_floor_area": garage_floor_area(),
    "mezzanine_floor_area": mezzanine_floor_area(),
    "has_swimming_pool": has_swimming_pool(),
    "has_outdoor_spa": has_outdoor_spa(),
}
pprint.pprint(data)

with open("results.mustache", "r") as template:
    with open("results.html", "w") as out:
        html = pystache.render(template.read(), data)
        print(html)
        out.write(html)
