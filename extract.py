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


def has_swimming_pool():
    for e in f.by_type("IfcSanitaryTerminalType"):
        if ifcopenshell.util.element.get_predefined_type(e) == "BATH" and ifcopenshell.util.element.get_pset(
            e, "Pset_SanitaryTerminalTypeBath", "BathType"
        ) == ["POOL"]:
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


def water_rating(ifc_class, predefined_type):
    result = 10
    for e in f.by_type(ifc_class):
        if ifcopenshell.util.element.get_predefined_type(e) != predefined_type:
            continue
        # Note: ratings may change, it may be better to instead fetch the underyling "litres per unit usage"
        if not (rating := ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "WELSRating")):
            return 0
        result = min(result, rating)
    return result


def installing_tank(predefined_type):
    for e in f.by_type("IfcTank"):
        if not [
            s
            for s in ifcopenshell.util.system.get_element_systems(e)
            if ifcopenshell.util.element.get_predefined_type(s) == predefined_type
        ]:
            continue
        return True
    return False


def greywater_treatment():
    results = []
    for e in f.by_type("IfcDistributionSystem"):
        if ifcopenshell.util.element.get_predefined_type(e) == "WASTEWATER":
            if [x for x in ifcopenshell.util.system.get_system_elements(e) if x.is_a("IfcFlowTreatmentDevice")]:
                results.append(e)
    return results


def system(predefined_type):
    results = []
    for e in f.by_type("IfcDistributionSystem"):
        if ifcopenshell.util.element.get_predefined_type(e) == predefined_type:
            results.append(e)
    return results


def basix_system(predefined_type):
    results = []
    presets = ["TOWNWATER", "RETICULATEDALTERNATIVE"]
    for e in f.by_type("IfcDistributionSystem"):
        if ifcopenshell.util.element.get_predefined_type(e) != predefined_type:
            continue
        if not ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "WaterSupplyType") not in presets:
            continue
        results.append(e)
    return results


def indoor_outdoor_pool():
    for e in f.by_type("IfcSanitaryTerminalType"):
        if ifcopenshell.util.element.get_predefined_type(e) == "BATH" and ifcopenshell.util.element.get_pset(
            e, "Pset_SanitaryTerminalTypeBath", "BathType"
        ) == ["POOL"]:
            if space := ifcopenshell.util.element.get_container(e, ifc_class="IfcSpace"):
                if is_external := ifcopenshell.util.element.get_pset(space, "Pset_SpaceCommon", "IsExternal"):
                    return bool(is_external)
    return None


def bath_pset(bath_type, name, default):
    for e in f.by_type("IfcSanitaryTerminalType"):
        if ifcopenshell.util.element.get_predefined_type(e) == "BATH" and ifcopenshell.util.element.get_pset(
            e, "Pset_SanitaryTerminalTypeBath", "BathType"
        ) == [bath_type]:
            return ifcopenshell.util.element.get_pset(e, "bSA_BASIX", name) or default
    return None


def floor_details():
    results = []
    for e in f.by_type("IfcSpatialZone"):
        if ifcopenshell.util.element.get_predefined_type(e) != "THERMAL":
            continue
        if not (floor_type := ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "FloorType")):
            continue
        results.append(
            {
                "floor_type": floor_type,
                "floor_area": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "FloorArea"),
                "form_of_construction": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "FormOfConstruction"),
                "frame": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Frame"),
                "subfloor_insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "SubfloorInsulation"),
                "floor_insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "FloorInsulation"),
                "reflective_foil": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "ReflectiveFoil"),
                "subfloor_wall_insulation": ifcopenshell.util.element.get_pset(
                    e, "bSA_BASIX", "SubfloorWallInsulation"
                ),
                "heating_system": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "HeatingSystem"),
                "additional_insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "AdditionalInsulation"),
                # Garage
                "low_emissions": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "LowEmissions"),
                "slab_type": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "SlabType"),
                "insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Insulation"),
            }
        )
    return results


def external_wall_details():
    results = []
    for e in f.by_type("IfcWallType"):
        if ifcopenshell.util.element.get_pset(e, "Pset_WallCommon", "IsExternal") is True:
            data = {
                "name": e.Name,
                "description": e.Description,
                "construction_type": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "ConstructionType"),
                "area": 0.0,
                "frame": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Frame"),
                "low_emissions": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "LowEmissions"),
                "insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Insulation"),
                "reflective_foil": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "ReflectiveFoil"),
                "wall_colour": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "WallColour"),
            }
            for wall in ifcopenshell.util.element.get_types(e):
                data["area"] += ifcopenshell.util.element.get_pset(e, "Qto_WallBaseQuantities", "NetSideArea")
            results.append(data)


def internal_wall_details():
    results = []
    for e in f.by_type("IfcWallType"):
        if ifcopenshell.util.element.get_pset(e, "Pset_WallCommon", "IsExternal") is False:
            data = {
                "name": e.Name,
                "description": e.Description,
                "construction_type": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "ConstructionType"),
                "area": 0.0,
                "frame": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Frame"),
                "insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Insulation"),
            }
            for wall in ifcopenshell.util.element.get_types(e):
                data["area"] += ifcopenshell.util.element.get_pset(e, "Qto_WallBaseQuantities", "NetSideArea")
            results.append(data)


def ceiling_roof_details():
    results = []
    for e in f.by_type("IfcSpatialZone"):
        if ifcopenshell.util.element.get_predefined_type(e) != "THERMAL":
            continue
        if not (ceiling_roof_type := ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "CeilingRoofType")):
            continue
        results.append(
            {
                "ceiling_roof_type": ceiling_roof_type,
                "roof_area": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "RoofArea"),
                "construction_type": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "ConstructionType"),
                "frame": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "Frame"),
                "roof_space_ventilation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "roof_space_ventilation"),
                "roof_colour": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "RoofColour"),
                "ceiling_insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "CeilingInsulation"),
                "roof_insulation": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "RoofInsulation"),
                "insulation_location": ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "InsulationLocation"),
                "ceiling_area_uninsulated": ifcopenshell.util.element.get_pset(
                    e, "bSA_BASIX", "CeilingAreaUninsulated"
                ),
            }
        )
    return results


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
    "conditioned_floor_area": total_zone_area("Conditioned Floor Area"),
    "unconditioned_floor_area": total_zone_area("Unconditioned Floor Area"),
    "garage_floor_area": total_zone_area("Garage Floor Area"),
    "mezzanine_floor_area": total_zone_area("Mezzanine Floor Area"),
    "has_swimming_pool": has_swimming_pool(),
    "has_outdoor_spa": has_outdoor_spa(),
}

# Step 2
data.update(
    {
        "garden_lawn_area": total_zone_area("Garden and Lawn Area"),
        "indigenous_low_water_area": total_zone_area("Indigenous and Low Water Planting Area"),
        "showerhead_water_rating": water_rating("IfcSanitaryTerminal", "SHOWER"),
        "toilet_water_rating": water_rating("IfcSanitaryTerminal", "TOILETPAN"),
        "kitchen_water_rating": water_rating("IfcSanitaryTerminal", "SINK"),
        "bathroom_water_rating": water_rating("IfcSanitaryTerminal", "WASHHANDBASIN"),
        "installing_rainwater_tank": installing_tank("RAINWATER"),
        "installing_stormwater_tank": installing_tank("STORMWATER"),
        "reticulated_alternative_water_supply": system("WATERSUPPLY"),
        "greywater_treatment": greywater_treatment(),
        "greywater_diversion": system("WASTEWATER"),
        "private_dam": None,
        "hot_water_system": system("DOMESTICHOTWATER"),
        "reticulated_alternative_water_supply_connection": system("WATERSUPPLY"),
        "garden_and_lawn_alternative": basix_system("WATERSUPPLY"),
        "toilet_alternative": basix_system("WATERSUPPLY"),
        "laundry_alternative": basix_system("WATERSUPPLY"),
        "hot_water_alternative": basix_system("WATERSUPPLY"),
        "drinking_alternative": basix_system("WATERSUPPLY"),
        # If has pool / spa
        "indoor_outdoor_pool": indoor_outdoor_pool(),
        "pool_volume": bath_pset("POOL", "PoolVolume", 0.0),
        "pool_cover": bath_pset("POOL", "PoolCover", None),
        "pool_shaded": bath_pset("POOL", "PoolShaded", None),
        "spa_volume": bath_pset("SPA", "SpaVolume", 0.0),
        "spa_cover": bath_pset("SPA", "SpaCover", None),
        "spa_shaded": bath_pset("SPA", "SpaShaded", None),
    }
)

# Step 3
data.update(
    {
        "floor_details": floor_details(),
        "external_wall_details": external_wall_details(),
        "internal_wall_details": internal_wall_details(),
        "ceiling_roof_details": ceiling_roof_details(),
    }
)


pprint.pprint(data)

with open("results.mustache", "r") as template:
    with open("results.html", "w") as out:
        html = pystache.render(template.read(), data)
        print(html)
        out.write(html)
