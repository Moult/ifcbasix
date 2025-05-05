import ifctester
import ifctester.ids
import ifcopenshell
from ifctester import ids, reporter


specs = ifctester.ids.Ids(
    title="BASIX",
    copyright="Awesome Team",
    version="1.0.12",
    description="These requirements are required by BASIX",
    author="john.mitchell@cqr.net.au",
    date="2025-05-05",
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

spec = add_spec("1.4", "Zoned Floor Areas", "Provide area of Conditioned, Unconditioned, Garage and Mezzanine rooms")
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

spec = add_spec("2.1", "Garden and Planting Zones", "Gardens and Lawns must have a total zone area for measurement")
spec.applicability.append(ifctester.ids.Entity(name="IFCZONE"))
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": [
            "Garden and Lawn Area",
            "Indigenous and Low Water Planting Area",
        ]
    }
)
spec.applicability.append(ifctester.ids.Attribute(name="Name", value=restriction))

spec = add_spec("2.2", "Fixture Water Rating", "Water taps must have a WELS rating")
spec.applicability.append(ifctester.ids.Entity(name="IfcSanitaryTerminal"))
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": [
            "SHOWER",
            "TOILETPAN",
            "SINK",
            "WASHHANDBASIN",
        ]
    }
)
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value=restriction))
add_property(spec, "bSA_BASIX", "WELSRating", "IFCINTEGER")

spec = add_spec("2.3", "Water systems", "You may have a rainwater or stormwater water system")
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": [
            "RAINWATER",
            "STORMWATER",
        ]
    }
)
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value=restriction))

spec = add_spec("2.3", "Tank", "Do you have a tank that is part of a rainwater or stormwater system?")
spec.applicability.append(ifctester.ids.Entity(name="IfcTank"))
spec.applicability.append(ifctester.ids.PartOf(name="IfcDistributionSystem"))

spec = add_spec("2.3", "Alternative water supply", "You may have an alternative water supply system")
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value="WATERSUPPLY"))

spec = add_spec("2.3", "Greywater systems", "You may have a greywater treatment or diversion system")
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value="WASTEWATER"))

spec = add_spec("2.3", "Greywater treatment", "Are you treating greywater?")
restriction = ifctester.ids.Restriction(
    options={
        "enumeration": [
            "IFCFILTER",
            "IFCINTERCEPTOR",
        ]
    }
)
spec.applicability.append(ifctester.ids.Entity(name=restriction))
spec.applicability.append(ifctester.ids.PartOf(name="IfcDistributionSystem"))

spec = add_spec("2.3", "Hot water systems", "You may have a hot water recirculation / diversion system")
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value="DOMESTICHOTWATER"))


spec = add_spec("2.4", "Reticulated alternative recycled water", "Specify alternative recycled water scheme")
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value="WATERSUPPLY"))

spec = add_spec(
    "2.4",
    "Reticulated alternative recycled water",
    "You may have a town water or reticulated alternative water supply, which may be used as an alternative supply for different purposes",
)
spec.applicability.append(ifctester.ids.Entity(name="IfcDistributionSystem"))
spec.applicability.append(ifctester.ids.Attribute(name="PredefinedType", value="WATERSUPPLY"))
restriction = ifctester.ids.Restriction(options={"enumeration": ["TOWNWATER", "RETICULATEDALTERNATIVE"]})
add_property(spec, "bSA_BASIX", "WaterSupplyType", "IFCLABEL", restriction)
restriction = ifctester.ids.Restriction(
    options={"enumeration": ["GARDENLAWN", "TOILET", "LAUNDRY", "HOTWATER", "DRINKING"]}
)
add_property(spec, "bSA_BASIX", "AlternativeSupplyFor", "IFCLABEL", restriction)


spec = add_spec("2.5", "Space indoors / outdoors", "All spaces must be identified whether they are indoors or outdoors")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPACE"))
add_property(spec, "Pset_SpaceCommon", "IsExternal", "IFCBOOLEAN")

spec = add_spec("2.5", "Pools must be in a space", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSANITARYTERMINALTYPE", predefinedType="BATH"))
p = ifctester.ids.Property(
    propertySet="Pset_SanitaryTerminalTypeBath", baseName="BathType", dataType="IFCLABEL", value="POOL"
)
spec.applicability.append(p)
spec.requirements.append(ifctester.ids.PartOf(name="IfcSpace"))

spec = add_spec("2.5", "Pool data", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSANITARYTERMINALTYPE", predefinedType="BATH"))
p = ifctester.ids.Property(
    propertySet="Pset_SanitaryTerminalTypeBath", baseName="BathType", dataType="IFCLABEL", value="POOL"
)
spec.applicability.append(p)
add_property(spec, "bSA_BASIX", "PoolVolume", "IFCVOLUMEMEASURE")
add_property(spec, "bSA_BASIX", "PoolCover", "IFCBOOLEAN")
add_property(spec, "bSA_BASIX", "PoolShaded", "IFCBOOLEAN")


spec = add_spec("2.5", "Spa data", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSANITARYTERMINALTYPE", predefinedType="BATH"))
pool_prop = ifctester.ids.Property(
    propertySet="Pset_SanitaryTerminalTypeBath", baseName="BathType", dataType="IFCLABEL", value="SPA"
)
spec.applicability.append(pool_prop)
add_property(spec, "bSA_BASIX", "SpaVolume", "IFCVOLUMEMEASURE")
add_property(spec, "bSA_BASIX", "SpaCover", "IFCBOOLEAN")
add_property(spec, "bSA_BASIX", "SpaCover", "IFCBOOLEAN")


spec = add_spec("3", "Floor Details", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPATIALZONE", predefinedType="THERMAL"))
spec.applicability.append(ifctester.ids.Property(propertySet="bSA_BASIX", baseName="FloorType", dataType="IFCLABEL"))
restriction = ifctester.ids.Restriction(
    options={"enumeration": ["CONCRETESLABONGROUND", "SUSPENDEDFLOORABOVEENCLOSEDSUBFLOOR", "SUSPENDEDFLOORABOVEOPENSUBFLOOR", "FIRSTFLOOR", "SUSPENDEDFLOORABOVEGARAGE"]}
)
add_property(spec, "bSA_BASIX", "FloorType", "IFCLABEL", value=restriction)
add_property(spec, "bSA_BASIX", "FloorArea", "IFCAREAMEASURE")
add_property(spec, "bSA_BASIX", "FormOfConstruction", "IFCLABEL")
add_property(spec, "bSA_BASIX", "SubfloorInsulation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "FloorInsulation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "ReflectiveFoil", "IFCBOOLEAN")
add_property(spec, "bSA_BASIX", "SubfloorWallInsulation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "HeatingSystem", "IFCBOOLEAN")
add_property(spec, "bSA_BASIX", "AdditionalInsulation", "IFCBOOLEAN")

spec = add_spec("3", "Floor Details (Garage)", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPATIALZONE", predefinedType="THERMAL"))
spec.applicability.append(ifctester.ids.Property(propertySet="bSA_BASIX", baseName="FloorType", dataType="IFCLABEL", value="SUSPENDEDFLOORABOVEGARAGE"))
add_property(spec, "bSA_BASIX", "LowEmissions", "IFCLABEL")
add_property(spec, "bSA_BASIX", "SlabType", "IFCLABEL")
add_property(spec, "bSA_BASIX", "Insulation", "IFCLABEL")

spec = add_spec("3", "External Wall Identification", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCWALLTYPE"))
add_property(spec, "Pset_WallCommon", "IsExternal", "IFCBOOLEAN")

spec = add_spec("3", "Wall Details", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCWALLTYPE"))
spec.requirements.append(ifctester.ids.Attribute(name="Name", instructions="... describe what to put in here"))
spec.requirements.append(ifctester.ids.Attribute(name="Description", instructions="... describe"))
add_property(spec, "bSA_BASIX", "ConstructionType", "IFCLABEL")
add_property(spec, "bSA_BASIX", "Frame", "IFCLABEL")
add_property(spec, "bSA_BASIX", "Insulation", "IFCLABEL")

spec = add_spec("3", "External Wall Details", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCWALLTYPE"))
spec.applicability.append(ifctester.ids.Property(propertySet="Pset_WallCommon", baseName="IsExternal", dataType="IFCBOOLEAN", value="TRUE"))
add_property(spec, "bSA_BASIX", "LowEmissions", "IFCLABEL")
add_property(spec, "bSA_BASIX", "ReflectiveFoil", "IFCBOOLEAN")
add_property(spec, "bSA_BASIX", "WallColour", "IFCLABEL")

spec = add_spec("3", "Wall Area", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCWALL"))
add_property(spec, "Qto_WallBaseQuantities", "NetSideArea", "IFCAREAMEASURE")


spec = add_spec("3", "Ceiling / Roof Details", "blah")
spec.applicability.append(ifctester.ids.Entity(name="IFCSPATIALZONE", predefinedType="THERMAL"))
spec.applicability.append(ifctester.ids.Property(propertySet="bSA_BASIX", baseName="CeilingRoofType", dataType="IFCLABEL"))
restriction = ifctester.ids.Restriction(
    options={"enumeration": ["FLATCEILINGPITCHEDROOF", "RAKEDCEILINGPITCHEDROOF", "FLATCEILINGROOF"]}
)
add_property(spec, "bSA_BASIX", "CeilingRoofType", "IFCLABEL", value=restriction)
add_property(spec, "bSA_BASIX", "RoofArea", "IFCAREAMEASURE")
add_property(spec, "bSA_BASIX", "ConstructionType", "IFCLABEL")
add_property(spec, "bSA_BASIX", "Frame", "IFCLABEL")
add_property(spec, "bSA_BASIX", "RoofSpaceVentilation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "RoofColour", "IFCLABEL")
add_property(spec, "bSA_BASIX", "CeilingInsulation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "RoofInsulation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "InsulationLocation", "IFCLABEL")
add_property(spec, "bSA_BASIX", "CeilingAreaUninsulated", "IFCLABEL")


spec = add_spec("3", "Insulation requirements", "blah")
restriction = ifctester.ids.Restriction(options={"enumeration": ["IFCROOF", "IFCWALL", "IFCCOVERING", "IFCSLAB"]})
spec.applicability.append(ifctester.ids.Entity(name=restriction))
restriction = ifctester.ids.Restriction(options={"enumeration": ["Pset_RoofCommon", "Pset_WallCommon", "Pset_CoveringCommon", "Pset_SlabCommon"]})
spec.requirements.append(ifctester.ids.Property(propertySet=restriction, baseName="ThermalTransmittance", dataType="IFCTHERMALTRANSMITTANCEMEASURE"))


spec = add_spec("3", "Fans", "You got fans?")
restriction = ifctester.ids.Restriction(options={"pattern": ".*FAN.*"})
spec.applicability.append(ifctester.ids.Entity(name="IfcElectricAppliance", predefinedType=restriction))
spec.applicability.append(ifctester.ids.PartOf(name="IfcSpace"))


spec = add_spec("3", "Zoned Habitable Areas", "You must identify habitable areas")
spec.applicability.append(ifctester.ids.Entity(name="IFCZONE"))
spec.applicability.append(ifctester.ids.Attribute(name="Name", value="Daytime Habitable Space"))

spec = add_spec("3", "Door Window Materials", "Doors and windows must define the lining material")
restriction = ifctester.ids.Restriction(options={"enumeration": ["IFCDOOR", "IFCWINDOW"]})
spec.applicability.append(ifctester.ids.Entity(name=restriction))
spec.applicability.append(ifctester.ids.Material(value="Lining"))
restriction = ifctester.ids.Restriction(options={"enumeration": ["aluminium", "wood", "plastic", "steel", "composite"]})
spec.requirements.append(ifctester.ids.Material(value=restriction))


spec = add_spec("3", "Door Operation", "")
spec.applicability.append(ifctester.ids.Entity(name="IFCDOOR"))
restriction = ifctester.ids.Restriction(options={"pattern": ".*(SWING|FOLD|SLIDING|USERDEFINED).*"})
spec.requirements.append(ifctester.ids.Attribute(name="OperationType", value=restriction))

spec = add_spec("3", "Door User defined Operation", "")
spec.applicability.append(ifctester.ids.Entity(name="IFCDOOR"))
spec.applicability.append(ifctester.ids.Attribute(name="OperationType", value="USERDEFINED"))
restriction = ifctester.ids.Restriction(options={"pattern": ".*(BIFOLD|TRIFOLD|STACKER|FRENCH).*"})
spec.requirements.append(ifctester.ids.Attribute(name="UserDefinedOperationType", value=restriction))


spec = add_spec("3", "Window Operation", "")
spec.applicability.append(ifctester.ids.Entity(name="IFCWINDOW"))
restriction = ifctester.ids.Restriction(options={"pattern": ".*(HUNG|SLIDING|FIXED|TILT|USERDEFINED).*"})
add_property(spec, "Pset_WindowPanelProperties", "OperationType", "IFCLABEL", restriction)

spec = add_spec("3", "Window User defined Operation", "")
spec.applicability.append(ifctester.ids.Entity(name="IFCWINDOW"))
spec.applicability.append(
    ifctester.ids.Property(
        propertySet="Pset_WindowPanelProperties", baseName="OperationType", dataType="IFCLABEL", value="USERDEFINED"
    )
)
restriction = ifctester.ids.Restriction(options={"pattern": ".*(LOUVRE|BIFOLD|TRIFOLD|STACKER).*"})
add_property(spec, "Pset_WindowPanelProperties", "UserDefinedOperationType", "IFCLABEL", restriction)


spec = add_spec("3", "Window Skylights", "")
spec.applicability.append(ifctester.ids.Entity(name="IFCWINDOW"))
spec.requirements.append(ifctester.ids.Entity(name="IFCWINDOW", predefinedType=restriction))
restriction = ifctester.ids.Restriction(options={"enumeration": ["LIGHTDOME", "SKYLIGHT", "WINDOW"]})

spec = add_spec("3", "Window / Door Data", "")
restriction = ifctester.ids.Restriction(options={"enumeration": ["IFCDOOR", "IFCWINDOW"]})
spec.applicability.append(ifctester.ids.Entity(name=restriction))
restriction = ifctester.ids.Restriction(options={"enumeration": ["Qto_DoorBaseQuantities", "Qto_WindowBaseQuantities"]})
add_property(spec, restriction, "Height", "IFCLENGTHMEASURE")
add_property(spec, restriction, "Width", "IFCLENGTHMEASURE")
add_property(spec, "Pset_DoorWindowGlazingType", "GlassLayers", "IFCCOUNTMEASURE")
restriction = ifctester.ids.Restriction(options={"enumeration": ["Pset_DoorCommon", "Pset_WindowCommon"]})
spec.requirements.append(ifctester.ids.Property(propertySet=restriction, baseName="ThermalTransmittance", dataType="IFCTHERMALTRANSMITTANCEMEASURE"))
add_property(spec, "Pset_DoorWindowGlazingType", "SolarHeatGainTransmittance", "IFCNORMALISEDRATIOMEASURE")
add_property(spec, "bSA_BASIX", "FloorType", "IFCLABEL")
add_property(spec, "bSA_BASIX", "SpaceFunction", "IFCLABEL")
add_property(spec, "bSA_BASIX", "FloorCovering", "IFCLABEL")


specs.to_xml("basix.ids")
