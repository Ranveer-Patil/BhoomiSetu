"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { Check, FileText, MapPin } from "lucide-react";
import { demoParcels } from "@/lib/demo-data";

const ParcelMap = dynamic(() => import("./parcel-map"), {
  ssr: false,
  loading: () => <div className="mapLoading">Loading parcel preview…</div>,
});
export function LandingPreview() {
  const [selected, setSelected] = useState(demoParcels[0]);
  return (
    <div className="productPreview">
      <div className="previewBar">
        <span>
          <MapPin size={15} /> Parcel intelligence
        </span>
        <span className="previewTag">Synthetic preview</span>
      </div>
      <ParcelMap
        parcels={demoParcels}
        scrollWheelZoom={false}
        onSelect={(id) =>
          setSelected(
            demoParcels.find((parcel) => parcel.case_id === id) ?? selected,
          )
        }
      />
      <div className="previewRecord">
        <span className="recordIcon">
          <FileText size={22} />
        </span>
        <div>
          <small>Selected survey</small>
          <strong>{selected.survey_number}</strong>
        </div>
        <div>
          <small>Area</small>
          <strong>{selected.area_hectares.toFixed(2)} ha</strong>
        </div>
        <span className="previewVerified">
          <Check size={14} /> Mapped
        </span>
      </div>
      <p className="previewCaption">
        Illustrative parcel boundaries on an OpenStreetMap basemap.
      </p>
    </div>
  );
}
