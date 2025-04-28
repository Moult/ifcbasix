import ifctester
import ifctester.ids
import ifcopenshell
from ifctester import ids, reporter

file_location = "/Volumes/cqrData 2024/Master/NSW/NSW Building Code Checker/SBE Model/B&L House/"
ifc_file_name = "2023-250106-BaL-V3s_AC28 24Apr2025_1357.ifc"
ifc_file_path = f"{file_location}{ifc_file_name}"

specs = ifctester.ids.Ids(
    title="BASIX",
    copyright="Awesome Team",
    version="1.0.0",
    description="These requirements are required by BASIX",
    author="john.mitchell@cqr.net.au",
    date="2025-01-01",
    purpose="Minimum Requirements",
)


def add_spec(code, name, description=None):
    spec = ifctester.ids.Specification(
        name=f"{code} {name}", ifcVersion=["IFC2X3", "IFC4", "IFC4X3_ADD2"], identifier="{code}"
    )
    specs.specifications.append(spec)
    return spec


def add_property(spec, pset, name, data_type, value=None):
    spec.requirements.append(ifctester.ids.Property(propertySet=pset, baseName=name, dataType=data_type, value=value))


spec = add_spec("1.2", "Project Name")
spec.applicability.append(ifctester.ids.Entity(name="IFCPROJECT"))
spec.requirements.append(ifctester.ids.Attribute(name="LongName"))

spec = add_spec("1.2", "Plan Type", "NSW Plan type shall be provided to uniquely identify the land Title")
spec.applicability.append(ifctester.ids.Entity(name="IFCSITE"))
restriction = ifctester.ids.Restriction(options={"pattern": "(SP|DP).+"})
add_property(spec, "Pset_LandRegistration", "LandTitleID", "IFCIDENTIFIER", restriction)

spec = add_spec(
    "1.2", "Property Address", "Address information shall be provided to uniquely identify the project location"
)
spec.applicability.append(ifctester.ids.Entity(name="IFCSITE"))
add_property(spec, "Pset_Address", "Town", "IFCLABEL")
add_property(spec, "Pset_Address", "PostalCode", "IFCLABEL")
add_property(spec, "Pset_Address", "Region", "IFCLABEL")
add_property(spec, "Pset_Address", "Country", "IFCLABEL")

spec = add_spec("1.2", "Lot / Section / Plan", "NSW Plan data shall identify Lot and Section numbers")
spec.applicability.append(ifctester.ids.Entity(name="IFCSITE"))
add_property(spec, "bSA_Site", "LotNumber", "IFCIDENTIFIER")
add_property(spec, "bSA_Site", "SectionNumber", "IFCIDENTIFIER")

spec = add_spec("1.3", "Project Type", "Specify your project type")
spec.applicability.append(ifctester.ids.Entity(name="IFCBUILDING"))
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": ["Dwelling house (detached)", "Dwelling house (attached)", "Dwelling above existing building"]
    }
)
add_property(spec, "bSA_BASIX", "ProjectType", "IFCLABEL", restriction)

spec = add_spec("1.3", "Number of Bedrooms", "Bedrooms should be modeled as a space")
spec.set_usage("required")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPACE", predefinedType="BEDROOM"))

spec = add_spec("1.3", "Is Secondary Dwelling")
spec.applicability.append(ifctester.ids.Entity(name="IFCBUILDING"))
add_property(spec, "bSA_BASIX", "IsSecondaryDwelling", "IFCBOOLEAN")

spec = add_spec("1.4", "Site Area")
spec.applicability.append(ifctester.ids.Entity(name="IFCSITE"))
add_property(spec, "Qto_SiteBaseQuantities", "GrossArea", "IFCAREAMEASURE")

spec = add_spec("1.4", "Roof Area")
spec.applicability.append(ifctester.ids.Entity(name="IFCROOF"))
add_property(spec, "Qto_RoofBaseQuantities", "ProjectedArea", "IFCAREAMEASURE")

spec = add_spec("1.4", "Number of Storeys", "blah blah include habitable blah")
spec.set_usage("required")
spec.applicability.append(ifctester.ids.Entity(name="IFCBUILDINGSTOREY"))

spec = add_spec("1.4", "Space Areas", "All spaces must have a gross floor area for measurement")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPACE"))
add_property(spec, "Qto_SpaceBaseQuantities", "GrossFloorArea", "IFCAREAMEASURE")

spec = add_spec("1.4", "Zoned Floor Areas", "blah blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCZONE"))
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": [
            "Conditioned Floor Area",
            "Unconditioned Floor Area",
            "Garage Floor Area",
            "Mezzanine Floor Area",
        ]
    }
)
spec.applicability.append(ifctester.ids.Attribute(name="Name", value=restriction))

spec = add_spec("1.4", "Has Swimming Pool and / or Spa", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSANITARYTERMINALTYPE", predefinedType="BATH"))
restriction = ifctester.ids.Restriction(options={"enumeration": ["POOL", "SPA"]})
spec.applicability.append(
    ifctester.ids.Property(
        propertySet="Pset_SanitaryTerminalTypeBath", baseName="BathType", dataType="IFCLABEL", value=restriction
    )
)

# spec = ifctester.ids.Specification(
#     name="Step 2. Water Details",
#     instructions="2.1.1 Garden and Lawn",
#     description="Specify the total area of garden and lawn (m2)",
# )
# specs.specifications.append(spec)
# spec.applicability.append(ifctester.ids.Entity(name="IFCZONE"))
# spec.requirements.append(
#     ifctester.ids.Property(
#         propertySet="total_zone_area",
#         baseName="Garden and Lawn Area",
#         dataType="IfcAreaMeasure",
#     )
# )
#
# spec = ifctester.ids.Specification(
#     name="Step 2. cont...",
#     instructions="2.1.2 Indigenous and Low Water Planting",
#     description="Enter the area (m?) of indigenous or low water use species",
# )
# specs.specifications.append(spec)
# spec.applicability.append(ifctester.ids.Entity(name="IFCZONE"))
# spec.requirements.append(
#     ifctester.ids.Property(
#         propertySet="total_zone_area",
#         baseName="Indigenous and Low Water Planting Area",
#         dataType="IfcAreaMeasure",
#     )
# )
#
# spec = ifctester.ids.Specification(
#     name="Step 2. Fixtures",
#     instructions="2.2.1 Water rating of all showerheads",
#     description="Enter water rating (WELS) of all showerheads",
# )


specs.to_xml("basix.ids")
