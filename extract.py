import pystache
import shutil
import tempfile
import pprint
import numpy as np
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.system
import ifcopenshell.util.shape_builder
import webbrowser
import os
from math import degrees

# f = ifcopenshell.open("/home/dion/basix.ifc")


def extract_basix(f):
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
        land_title = ifcopenshell.util.element.get_pset(site, pset_name, "LandTitleID") or ""
        return "SP" if land_title.startswith("SP") else "DP"

    def get_lot_section_plan():
        pset_name = "Pset_LandRegistration"
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

    def basix_system(alternative_supply):
        results = []
        presets = ["TOWNWATER", "RETICULATEDALTERNATIVE"]
        for e in f.by_type("IfcDistributionSystem"):
            if ifcopenshell.util.element.get_predefined_type(e) != "WATERSUPPLY":
                continue
            if not ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "WaterSupplyType") not in presets:
                continue
            if alternative_supply in ifcopenshell.util.element.get_pset(e, "bSA_BASIX", "AlternativeSupplyFor") or []:
                results.append(e)
        return results

    def indoor_outdoor_pool():
        for e in f.by_type("IfcSanitaryTerminalType"):
            if ifcopenshell.util.element.get_predefined_type(e) == "BATH" and ifcopenshell.util.element.get_pset(
                e, "Pset_SanitaryTerminalTypeBath", "BathType"
            ) == ["POOL"]:
                if space := ifcopenshell.util.element.get_container(e, ifc_class="IfcSpace"):
                    if (
                        is_external := ifcopenshell.util.element.get_pset(space, "Pset_SpaceCommon", "IsExternal")
                    ) is not None:
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
                    data["area"] += (
                        ifcopenshell.util.element.get_pset(wall, "Qto_WallBaseQuantities", "NetSideArea") or 0
                    )
                results.append(data)
        return results

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
                    data["area"] += (
                        ifcopenshell.util.element.get_pset(wall, "Qto_WallBaseQuantities", "NetSideArea") or 0
                    )
                results.append(data)
        return results

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
                    "roof_space_ventilation": ifcopenshell.util.element.get_pset(
                        e, "bSA_BASIX", "RoofSpaceVentilation"
                    ),
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

    def insulation_requirements():
        results = {}
        for ifc_class in ["IfcRoof", "IfcWall", "IfcCovering", "IfcSlab"]:
            for element in f.by_type(ifc_class):
                pset_name = "Pset_{}Common".format(ifc_class[3:])
                u_value = ifcopenshell.util.element.get_pset(element, pset_name, "ThermalTransmittance")
                results.setdefault(u_value, []).append(element)
        return results

    def bedroom_ceiling_fans():
        for e in f.by_type("IfcSpace"):
            if ifcopenshell.util.element.get_predefined_type(e) != "BEDROOM":
                continue
            has_fan = False
            for se in ifcopenshell.util.element.get_decomposition(e):
                if (
                    se.is_a("IfcElectricAppliance")
                    and "fan" in ifcopenshell.util.element.get_predefined_type(e).lower()
                ):
                    has_fan = True
                    break
            if not has_fan:
                return False
        return True

    def habitable_ceiling_fans():
        name = "Daytime Habitable Space"
        for zone in f.by_type("IfcZone"):
            if zone.Name != name:
                continue
            for e in ifcopenshell.util.system.get_system_elements(zone):
                if not e.is_a("IfcSpace"):
                    continue
                has_fan = False
                for se in ifcopenshell.util.element.get_decomposition(e):
                    if (
                        se.is_a("IfcElectricAppliance")
                        and "fan" in ifcopenshell.util.element.get_predefined_type(e).lower()
                    ):
                        has_fan = True
                        break
                if not has_fan:
                    return False
        return True

    def windows_doors():
        results = []
        for ifc_class in ["IfcWindow", "IfcDoor"]:
            for element in f.by_type(ifc_class):
                matrix = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
                y_axis = matrix[:, 1][:2]
                angle = degrees(ifcopenshell.util.shape_builder.np_angle_signed(y_axis, np.array((1.0, 0.0))))
                # Note this is project north not true north
                if angle >= -22.5 and angle < 22.5:
                    orientation = "EAST"
                elif angle >= 22.5 and angle < 67.5:
                    orientation = "NORTHEAST"
                elif angle >= 67.5 and angle < 112.5:
                    orientation = "NORTH"
                elif angle >= 112.5 and angle < 157.5:
                    orientation = "NORTHWEST"
                elif angle >= 157.5:
                    orientation = "WEST"
                elif angle >= -67.5 and angle < -22.5:
                    orientation = "SOUTHEAST"
                elif angle >= -112.5 and angle < -67.5:
                    orientation = "SOUTH"
                elif angle >= -157.5 and angle < -112.5:
                    orientation = "SOUTHWEST"
                elif angle < -157.5:
                    orientation = "WEST"
                frame = "composite"
                material = ifcopenshell.util.element.get_material(element, should_skip_usage=True)
                mapping = {"aluminium": "aluminium", "wood": "timber", "plastic": "upvc", "steel": "steel"}
                if material and material.is_a("IfcConstituentSet"):
                    for constituent in material.MaterialConstituents:
                        if constituent.Name != "Lining":
                            continue
                        category = (
                            getattr(constituent.Material, "Category", None) or constituent.Material.Name or ""
                        ).lower()
                        for k, v in mapping.items():
                            if k in category:
                                frame = v
                                break

                operation = None
                if ifc_class == "IfcDoor":
                    operation_type = None
                    if relating_type := ifcopenshell.util.element.get_type(element):
                        operation_type = relating_type.OperationType
                        if operation_type == "USERDEFINED":
                            operation_type = relating_type.UserDefinedOperationType
                    if not operation_type:
                        operation_type = element.OperationType
                        if operation_type == "USERDEFINED":
                            operation_type = element.UserDefinedOperationType
                    for kw in ["SWING", "FOLD", "SLIDING", "BIFOLD", "TRIFOLD", "STACKER", "FRENCH"]:
                        if kw in operation_type.upper():
                            operation = kw
                elif ifc_class == "IfcWindow":
                    operation_type = (
                        ifcopenshell.util.element.get_pset(element, "Pset_WindowPanelProperties", "OperationType") or ""
                    )
                    if operation_type == "USERDEFINED":
                        operation_type = (
                            ifcopenshell.util.element.get_pset(
                                element, "Pset_WindowPanelProperties", "UserDefinedOperationType"
                            )
                            or ""
                        )
                    for k, v in {
                        "TOPHUNG": "AWNING",
                        "SIDEHUNG": "CASEMENT",
                        "SLIDINGVERTICAL": "DOUBLEHUNG",
                        "FIXEDCASEMENT": "FIXED",
                        "LOUVRE": "LOUVRE",
                        "TILT": "TILT",
                        "SLIDINGHORIZONTAL": "SLIDING",
                        "BIFOLD": "BIFOLD",
                        "TRIFOLD": "BIFOLD",
                        "STACKER": "STACKER",
                    }.items():
                        if k in operation_type.upper():
                            operation = v

                data = {
                    "global_id": element.GlobalId,
                    "name": element.Name,
                    "orientation": orientation,
                    "height": ifcopenshell.util.element.get_pset(
                        element, f"Qto_{ifc_class[3:]}BaseQuantities", "Height"
                    )
                    or 0.0,
                    "width": ifcopenshell.util.element.get_pset(element, f"Qto_{ifc_class[3:]}BaseQuantities", "Width")
                    or 0.0,
                    "window_or_door": ifc_class,
                    "is_skylight": ifcopenshell.util.element.get_predefined_type(element) in ("SKYLIGHT", "LIGHTDOME"),
                    "frame": frame,
                    "glass": ifcopenshell.util.element.get_pset(element, "Pset_DoorWindowGlazingType", "GlassLayers")
                    or 1,
                    "operation": operation,
                    "uvalue": ifcopenshell.util.element.get_pset(
                        element, f"Pset_{ifc_class[3:]}Common", "ThermalTransmittance"
                    ),
                    "shgc": ifcopenshell.util.element.get_pset(
                        element, "Pset_DoorWindowGlazingType", "SolarHeatGainTransmittance"
                    ),
                    # Should be a property of the spatial zone
                    "floor_type": ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "FloorType"),
                    # Should be a property of the space container
                    "space_function": ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "SpaceFunction"),
                    # Should be a property of the adjacent or rel connects covering
                    "floor_covering": ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "FloorCovering"),
                }
                results.append(data)
        return results

    def hot_water_system_type():
        for element in f.by_type("IfcDistributionSystem"):
            if ifcopenshell.util.element.get_predefined_type(element) != "DOMESTICHOTWATER":
                continue
            if result := ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "HotWaterSystemType"):
                return result

    def system_type(system_type, room_type):
        if f.schema == "IFC4X3":
            for element in f.by_type("IfcDistributionSystem"):
                for rel in element.ReferencedInStructures:
                    space = rel.RelatingStructure
                    if space.is_a("IfcSpace") and ifcopenshell.util.element.get_predefined_type(space) == room_type:
                        if result := ifcopenshell.util.element.get_pset(element, "bSA_BASIX", system_type):
                            return result
            return
        for element in f.by_type("IfcDistributionSystem"):
            for rel in element.ServicesBuildings:
                for space in rel.RelatedBuildings:
                    if space.is_a("IfcSpace") and ifcopenshell.util.element.get_predefined_type(space) == room_type:
                        if result := ifcopenshell.util.element.get_pset(element, "bSA_BASIX", system_type):
                            return result

    def kitchen_natural_light():
        for element in f.by_type("IfcWindow"):
            if space := ifcopenshell.util.element.get_container(element, ifc_class="IfcSpace"):
                if ifcopenshell.util.element.get_predefined_type(space) == "KITCHEN":
                    return True
            for space in ifcopenshell.util.element.get_referenced_structures(element):
                if space.is_a("IfcSpace") and ifcopenshell.util.element.get_predefined_type(space) == "KITCHEN":
                    return True
        return False

    def total_bathroom_natural_light():
        spaces = set()
        for element in f.by_type("IfcWindow"):
            if space := ifcopenshell.util.element.get_container(element, ifc_class="IfcSpace"):
                if ifcopenshell.util.element.get_predefined_type(space) in ["BATHROOM", "TOILET"]:
                    spaces.add(space)
            for space in ifcopenshell.util.element.get_referenced_structures(element):
                if space.is_a("IfcSpace") and ifcopenshell.util.element.get_predefined_type(space) in [
                    "BATHROOM",
                    "TOILET",
                ]:
                    spaces.add(space)
        return len(spaces)

    def artificial_lighting():
        total = 0
        total_efficient = 0
        for element in f.by_type("IfcLightFixture"):
            total += 1
            if ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "LampType") in [
                "COMPACTFLUORESCENT",
                "FLUORESCENT",
                "LED",
            ]:
                total_efficient += 1
        if total == 0:
            return False
        return total_efficient / total >= 0.8

    def bath_heating_system(bath_type):
        for system in f.by_type("IfcDistributionSystem"):
            for element in ifcopenshell.util.system.get_system_elements(system):
                if (
                    element.is_a("IfcSanitaryTerminalType")
                    and ifcopenshell.util.element.get_predefined_type(element) == "BATH"
                    and ifcopenshell.util.element.get_pset(element, "Pset_SanitaryTerminalTypeBath", "BathType")
                    == [bath_type]
                ):
                    if result := ifcopenshell.util.element.get_pset(system, "bSA_BASIX", "PoolHeatingSystemType"):
                        return result

    def bath_pump(bath_type, prop):
        for element in f.by_type("IfcSanitaryTerminalType"):
            if ifcopenshell.util.element.get_predefined_type(element) != "BATH" or ifcopenshell.util.element.get_pset(
                element, "Pset_SanitaryTerminalTypeBath", "BathType"
            ) != [bath_type]:
                continue
            for system in ifcopenshell.util.system.get_element_systems(element):
                for pump in ifcopenshell.util.system.get_system_elements(system):
                    if pump.is_a("IfcPump") and (r := ifcopenshell.util.element.get_pset(system, "bSA_BASIX", prop)):
                        return r

    def pv_output():
        results = []
        for element in f.by_type("IfcDistributionSystem"):
            if ifcopenshell.util.element.get_predefined_type(element) == "POWERGENERATION":
                if r := ifcopenshell.util.element.get_pset(system, "bSA_BASIX", "RatedElectricalOutput"):
                    results.append(r)
        return results

    def cooktop_oven_type():
        elements = f.by_type("IfcBurner")
        elements += f.by_type("IfcElectricAppliance")
        for element in elements:
            if r := ifcopenshell.util.element.get_pset(element, "bSA_BASIX", "CooktopOvenType"):
                return r

    def clothesline(is_external):
        for element in f.by_type("IfcFurniture"):
            if ifcopenshell.util.element.get_predefined_type(element) == "CLOTHESLINE":
                if space := ifcopenshell.util.element.get_container(element, ifc_class="IfcSpace"):
                    if ifcopenshell.util.element.get_pset(space, "Pset_SpaceCommon", "IsExternal") == is_external:
                        return True
        return False

    # Step 1
    data = {
        "project_name": f.by_type("IfcProject")[0].LongName or "",
        "plan_type": get_plan_type(),
        "www_is_dp": get_plan_type() == "DP",
        "project_address": get_project_address(),
        "lot_section_plan": get_lot_section_plan(),
        "project_type": get_project_type(),
        "www_is_dhd": get_project_type() == "Dwelling house (detached)",
        "www_is_dha": get_project_type() == "Dwelling house (attached)",
        "www_is_daeb": get_project_type() == "Dwelling above existing building",
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
            "garden_and_lawn_alternative": basix_system("GARDENLAWN"),
            "toilet_alternative": basix_system("TOILET"),
            "laundry_alternative": basix_system("LAUNDRY"),
            "hot_water_alternative": basix_system("HOTWATER"),
            "drinking_alternative": basix_system("DRINKING"),
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
    data["www_showerhead_water_rating"] = [
        {"rating": x, "is_selected": data["showerhead_water_rating"] == x} for x in (1, 2, 3, 4, 5, 6)
    ]
    data["www_toilet_water_rating"] = [
        {"rating": x, "is_selected": data["toilet_water_rating"] == x} for x in (1, 2, 3, 4, 5, 6)
    ]
    data["www_kitchen_water_rating"] = [
        {"rating": x, "is_selected": data["kitchen_water_rating"] == x} for x in (1, 2, 3, 4, 5, 6)
    ]
    data["www_bathroom_water_rating"] = [
        {"rating": x, "is_selected": data["bathroom_water_rating"] == x} for x in (1, 2, 3, 4, 5, 6)
    ]

    # Step 3
    data.update(
        {
            "floor_details": floor_details(),
            "external_wall_details": external_wall_details(),
            "internal_wall_details": internal_wall_details(),
            "ceiling_roof_details": ceiling_roof_details(),
            "insulation_requirements": insulation_requirements(),
            "bedroom_ceiling_fans": bedroom_ceiling_fans(),
            "habitable_ceiling_fans": habitable_ceiling_fans(),
            "windows_doors": windows_doors(),
        }
    )

    # Step 4
    data.update(
        {
            "hot_water_system_type": hot_water_system_type(),
            "cooling_system_type_living_room": system_type("CoolingSystemType", "LIVINGROOM"),
            "cooling_system_type_bedroom": system_type("CoolingSystemType", "BEDROOM"),
            "heating_system_type_living_room": system_type("HeatingSystemType", "LIVINGROOM"),
            "heating_system_type_bedroom": system_type("HeatingSystemType", "BEDROOM"),
            "exhaust_system_type_bathroom": system_type("ExhaustSystemType", "BATHROOM"),
            "exhaust_system_control_bathroom": system_type("ExhaustSystemControl", "BATHROOM"),
            "exhaust_system_type_kitchen": system_type("ExhaustSystemType", "KITCHEN"),
            "exhaust_system_control_kitchen": system_type("ExhaustSystemControl", "KITCHEN"),
            "exhaust_system_type_laundry": system_type("ExhaustSystemType", "LAUNDRY"),
            "kitchen_natural_light": kitchen_natural_light(),
            "total_bathroom_natural_light": total_bathroom_natural_light(),
            "artificial_lighting": artificial_lighting(),
            "pool_heating_system": bath_heating_system("POOL"),
            "pool_pump_timer_control": bath_pump("POOL", "IsPumpTimerControlled"),
            "pool_pump_speed": bath_pump("POOL", "PumpSpeedType"),
            "pool_pump_star_rating": bath_pump("POOL", "PumpStarRating"),
            "spa_heating_system": bath_heating_system("SPA"),
            "spa_pump_timer_control": bath_pump("SPA", "IsPumpTimerControlled"),
            "pv_output": pv_output(),
            "cooktop_oven_type": cooktop_oven_type(),
            "outdoor_clothesline": clothesline(True),
            "indoor_clothesline": clothesline(False),
        }
    )

    pprint.pprint(data)
    cwd = os.path.dirname(os.path.realpath(__file__))
    tmpdirname = tempfile.mkdtemp()
    shutil.copyfile(os.path.join(cwd, "PublicSansRegular.ttf"), os.path.join(tmpdirname, "PublicSansRegular.ttf"))
    print(tmpdirname)
    with open(os.path.join(cwd, "index.html"), "r") as template:
        mustache = template.read()
        for page in ("11", "12", "13", "14", "21", "22", "33", "36"):
            with open(os.path.join(tmpdirname, f"page-{page}.html"), "w") as out:
                for otherpage in ("11", "12", "13", "14", "21", "22", "33", "36"):
                    data[f"is_page_{otherpage}"] = False
                for otherpage in ("1", "2", "3"):
                    data[f"is_section_{otherpage}"] = False
                data[f"is_page_{page}"] = True
                data[f"is_section_{page[0]}"] = True
                html = pystache.render(mustache, data)
                out.write(html)
    index = os.path.join(tmpdirname, "page-11.html")
    webbrowser.open("file://" + index)
    return data
