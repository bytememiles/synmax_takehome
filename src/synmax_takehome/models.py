from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WellRecord(BaseModel):
    """One row of `api_well_data` (take-home PDF column names)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    Operator: str | None = None
    Status: str | None = None
    Well_Type: str | None = Field(None, alias="Well Type")
    Work_Type: str | None = Field(None, alias="Work Type")
    Directional_Status: str | None = Field(None, alias="Directional Status")
    Multi_Lateral: str | None = Field(None, alias="Multi-Lateral")
    Mineral_Owner: str | None = Field(None, alias="Mineral Owner")
    Surface_Owner: str | None = Field(None, alias="Surface Owner")
    Surface_Location: str | None = Field(None, alias="Surface Location")
    GL_Elevation: str | None = Field(None, alias="GL Elevation")
    KB_Elevation: str | None = Field(None, alias="KB Elevation")
    DF_Elevation: str | None = Field(None, alias="DF Elevation")
    Single_Multiple_Completion: str | None = Field(
        None, alias="Single/Multiple Completion"
    )
    Potash_Waiver: str | None = Field(None, alias="Potash Waiver")
    Spud_Date: str | None = Field(None, alias="Spud Date")
    Last_Inspection: str | None = Field(None, alias="Last Inspection")
    TVD: str | None = None
    API: str
    Latitude: str | None = None
    Longitude: str | None = None
    CRS: str | None = None

    def to_db_row(self) -> dict[str, str | None]:
        return {
            "Operator": self.Operator,
            "Status": self.Status,
            "Well Type": self.Well_Type,
            "Work Type": self.Work_Type,
            "Directional Status": self.Directional_Status,
            "Multi-Lateral": self.Multi_Lateral,
            "Mineral Owner": self.Mineral_Owner,
            "Surface Owner": self.Surface_Owner,
            "Surface Location": self.Surface_Location,
            "GL Elevation": self.GL_Elevation,
            "KB Elevation": self.KB_Elevation,
            "DF Elevation": self.DF_Elevation,
            "Single/Multiple Completion": self.Single_Multiple_Completion,
            "Potash Waiver": self.Potash_Waiver,
            "Spud Date": self.Spud_Date,
            "Last Inspection": self.Last_Inspection,
            "TVD": self.TVD,
            "API": self.API,
            "Latitude": self.Latitude,
            "Longitude": self.Longitude,
            "CRS": self.CRS,
        }

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "WellRecord":
        return cls.model_validate(
            {
                "Operator": row.get("Operator"),
                "Status": row.get("Status"),
                "Well Type": row.get("Well Type"),
                "Work Type": row.get("Work Type"),
                "Directional Status": row.get("Directional Status"),
                "Multi-Lateral": row.get("Multi-Lateral"),
                "Mineral Owner": row.get("Mineral Owner"),
                "Surface Owner": row.get("Surface Owner"),
                "Surface Location": row.get("Surface Location"),
                "GL Elevation": row.get("GL Elevation"),
                "KB Elevation": row.get("KB Elevation"),
                "DF Elevation": row.get("DF Elevation"),
                "Single/Multiple Completion": row.get("Single/Multiple Completion"),
                "Potash Waiver": row.get("Potash Waiver"),
                "Spud Date": row.get("Spud Date"),
                "Last Inspection": row.get("Last Inspection"),
                "TVD": row.get("TVD"),
                "API": row["API"],
                "Latitude": row.get("Latitude"),
                "Longitude": row.get("Longitude"),
                "CRS": row.get("CRS"),
            }
        )
